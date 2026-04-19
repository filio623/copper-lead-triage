import asyncio

from sqlalchemy import select

from backend.app.models.analysis import LLMAnalysisResult
from backend.app.models.db import LeadSnapshotORM, build_sqlite_url, create_database_engine, create_session_factory, initialize_database
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.services import pipeline
from backend.app.services.pipeline import PipelineDeps, process_normalized_lead, process_raw_lead


def build_pipeline_deps(tmp_path) -> tuple[PipelineDeps, object]:
    # This helper gives each test its own isolated SQLite database and session
    # so pipeline persistence behavior can be asserted without cross-test state.
    engine = create_database_engine(build_sqlite_url(tmp_path / "pipeline.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()
    deps = PipelineDeps(analyses_repository=AnalysesRepository(session))
    return deps, session


def build_hold_lead() -> NormalizedLead:
    # This lead shape should fall below triage so the pipeline can be tested
    # for the "rules only, no LLM" branch.
    return NormalizedLead(
        copper_lead_id=301,
        full_name="Riley Build",
        company_name="Riley Construction Group",
        title="Office Manager",
        primary_email=None,
        phone_numbers=["555-0100"],
        websites=None,
        city=None,
        source="referral",
    )


def build_research_lead() -> NormalizedLead:
    # This lead shape should clear triage gating so the pipeline can be tested
    # for the branch that attaches `llm_analysis` before saving.
    return NormalizedLead(
        copper_lead_id=302,
        full_name="Jordan Eventson",
        company_name="Premier Event Productions",
        title="Event Manager",
        primary_email="jordan@premierevents.com",
        phone_numbers=["310-555-1111"],
        websites=["https://premierevents.com"],
        city="Los Angeles",
        source="tradeshow",
    )


def build_raw_lead() -> dict:
    # This fixture mirrors the Copper payload shape enough for `validate_lead`
    # and `normalize_lead` to exercise the raw-input path cleanly.
    return {
        "id": 401,
        "name": "Taylor Eventson",
        "company_name": "Backstage Event Group",
        "title": "Producer",
        "customer_source_id": 99,
        "email": {"email": "taylor@backstageevents.com"},
        "phone_numbers": [{"number": "323-555-1212"}],
        "websites": [{"url": "https://backstageevents.com"}],
        "address": {"city": "Los Angeles"},
    }


def test_process_normalized_lead_saves_rules_only_when_triage_is_skipped(tmp_path, monkeypatch) -> None:
    deps, _session = build_pipeline_deps(tmp_path)
    lead = build_hold_lead()

    # This guard makes the test fail loudly if the pipeline unexpectedly tries
    # to call the LLM branch for a lead that should be skipped.
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("Triage should not run for this lead.")

    monkeypatch.setattr(pipeline, "analyze_triage_input", fail_if_called)

    stored = asyncio.run(process_normalized_lead(lead, deps))

    assert stored.copper_lead_id == lead.copper_lead_id
    assert stored.llm_analysis is None
    assert stored.rule_score.recommended_rule_action in {"hold", "reject"}


def test_process_normalized_lead_saves_llm_analysis_when_triage_runs(tmp_path, monkeypatch) -> None:
    deps, _session = build_pipeline_deps(tmp_path)
    lead = build_research_lead()

    # This stub replaces the live model call so the test can focus only on
    # whether the pipeline wires triage output back into the saved analysis.
    async def fake_analyze_triage_input(triage_input):
        return LLMAnalysisResult(
            priority_tier="high",
            industry_fit="strong",
            reasoning_summary=f"Stub analysis for lead {triage_input.normalized_lead.copper_lead_id}.",
            confidence=0.88,
            caution_notes=["Needs human review before outreach."],
            outreach_subject="Backdrop support for upcoming events",
            outreach_body="Would love to learn more about your upcoming event needs.",
            personalization_basis=["Event production company", "Los Angeles location"],
            draft_warnings=["Draft is still generic."],
            usable_without_rewrite=False,
        )

    monkeypatch.setattr(pipeline, "analyze_triage_input", fake_analyze_triage_input)

    stored = asyncio.run(process_normalized_lead(lead, deps))

    assert stored.copper_lead_id == lead.copper_lead_id
    assert stored.llm_analysis is not None
    assert stored.llm_analysis.priority_tier == "high"
    assert stored.rule_score.recommended_rule_action in {"pursue", "research"}


def test_process_raw_lead_saves_snapshot_and_analysis(tmp_path, monkeypatch) -> None:
    deps, session = build_pipeline_deps(tmp_path)
    raw_lead = build_raw_lead()

    # This stub avoids a live network model call while still letting the raw
    # pipeline path exercise validation, normalization, snapshot saving, and
    # final analysis persistence.
    async def fake_analyze_triage_input(triage_input):
        return LLMAnalysisResult(
            priority_tier="medium",
            industry_fit="moderate",
            reasoning_summary="Raw lead path stub analysis.",
            confidence=0.74,
            caution_notes=["Still needs operator review."],
            outreach_subject="Event branding support",
            outreach_body="Wanted to introduce Step and Repeat LA.",
            personalization_basis=["Event-related company"],
            draft_warnings=["Needs more personalization."],
            usable_without_rewrite=False,
        )

    monkeypatch.setattr(pipeline, "analyze_triage_input", fake_analyze_triage_input)

    stored = asyncio.run(process_raw_lead(raw_lead, deps))
    snapshot_row = session.scalar(
        select(LeadSnapshotORM).where(LeadSnapshotORM.id == stored.raw_snapshot_id)
    )

    assert stored.copper_lead_id == raw_lead["id"]
    assert stored.raw_snapshot_id is not None
    assert snapshot_row is not None
    assert snapshot_row.copper_lead_id == raw_lead["id"]
