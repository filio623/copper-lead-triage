import asyncio

from backend.app.models.analysis import RuleScoreResult
from backend.app.models.db import StoredLeadAnalysis, build_sqlite_url, create_database_engine, create_session_factory, initialize_database
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.runs import RunsRepository
from backend.app.services import batch
from backend.app.services.batch import BatchDeps, process_normalized_batch, process_raw_batch
from backend.app.services.pipeline import PipelineDeps


def build_batch_deps(tmp_path) -> BatchDeps:
    # This helper gives each test an isolated database plus the run and
    # analysis repositories that the batch layer depends on.
    engine = create_database_engine(build_sqlite_url(tmp_path / "batch.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()
    return BatchDeps(
        runs_repository=RunsRepository(session),
        pipeline_deps=PipelineDeps(
            analyses_repository=AnalysesRepository(session),
        ),
    )


def build_stored_analysis(copper_lead_id: int, batch_run_id: str | None = None) -> StoredLeadAnalysis:
    # This keeps the tests focused on batch orchestration rather than the
    # details of full per-lead pipeline output generation.
    return StoredLeadAnalysis(
        analysis_id=f"analysis-{copper_lead_id}",
        copper_lead_id=copper_lead_id,
        batch_run_id=batch_run_id,
        normalized_lead=NormalizedLead(copper_lead_id=copper_lead_id),
        rule_score=RuleScoreResult(recommended_rule_action="hold"),
    )


def test_process_raw_batch_tracks_successes_failures_and_duplicates(tmp_path, monkeypatch) -> None:
    deps = build_batch_deps(tmp_path)
    raw_leads = [
        {"id": 1, "name": "Lead One"},
        {"id": 2, "name": "Lead Two"},
        {"id": 2, "name": "Lead Two Duplicate"},
        {"id": 3, "name": "Lead Three"},
    ]

    # This stub lets the batch test focus on run tracking and duplicate
    # handling rather than executing the full pipeline and live triage path.
    async def fake_process_raw_lead(raw_lead, deps, batch_run_id=None):
        if raw_lead["id"] == 3:
            raise ValueError("Bad lead payload")
        return build_stored_analysis(raw_lead["id"], batch_run_id=batch_run_id)

    monkeypatch.setattr(batch, "process_raw_lead", fake_process_raw_lead)

    result = asyncio.run(process_raw_batch(raw_leads, deps, run_type="sample"))

    assert result.run.run_type == "sample"
    assert result.run.status == "completed"
    assert result.run.success_count == 2
    assert result.run.failure_count == 1
    assert result.run.processed_count == 3
    assert result.duplicate_lead_ids == [2]
    assert [analysis.copper_lead_id for analysis in result.analyses] == [1, 2]
    assert result.failures[0].copper_lead_id == 3


def test_process_normalized_batch_keeps_going_after_failure(tmp_path, monkeypatch) -> None:
    deps = build_batch_deps(tmp_path)
    normalized_leads = [
        NormalizedLead(copper_lead_id=10, full_name="Lead Ten"),
        NormalizedLead(copper_lead_id=11, full_name="Lead Eleven"),
    ]

    # This stub verifies that one failed lead does not prevent later leads
    # from being processed through the batch loop.
    async def fake_process_normalized_lead(normalized_lead, deps, batch_run_id=None, raw_snapshot_id=None):
        if normalized_lead.copper_lead_id == 10:
            raise ValueError("Scoring failed")
        return build_stored_analysis(normalized_lead.copper_lead_id, batch_run_id=batch_run_id)

    monkeypatch.setattr(batch, "process_normalized_lead", fake_process_normalized_lead)

    result = asyncio.run(process_normalized_batch(normalized_leads, deps, run_type="bulk"))

    assert result.run.run_type == "bulk"
    assert result.run.status == "completed"
    assert result.run.success_count == 1
    assert result.run.failure_count == 1
    assert result.run.processed_count == 2
    assert len(result.analyses) == 1
    assert result.analyses[0].copper_lead_id == 11
    assert result.failures[0].copper_lead_id == 10
