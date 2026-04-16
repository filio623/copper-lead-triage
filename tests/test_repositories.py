from datetime import UTC, datetime

from backend.app.models.analysis import (
    LLMAnalysisResult,
    LeadAnalysisRecord,
    RuleScoreResult,
)
from sqlalchemy import text

from backend.app.models.db import build_sqlite_url, create_database_engine, create_session_factory, initialize_database
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.reviews import ReviewsRepository
from backend.app.repositories.runs import RunsRepository


def build_sample_analysis_record(
    *,
    copper_lead_id: int = 101,
    batch_run_id: str | None = None,
    raw_snapshot_id: str | None = None,
) -> LeadAnalysisRecord:
    # This fixture keeps the repository tests focused on persistence behavior
    # instead of repeating the same lead and analysis setup in every test.
    return LeadAnalysisRecord(
        copper_lead_id=copper_lead_id,
        batch_run_id=batch_run_id,
        raw_snapshot_id=raw_snapshot_id,
        normalized_lead=NormalizedLead(
            copper_lead_id=copper_lead_id,
            full_name="Jordan Eventson",
            company_name="Premier Event Productions",
            title="Event Manager",
            primary_email="jordan@premierevents.com",
            phone_numbers=["310-555-1111"],
            websites=["https://premierevents.com"],
            city="Los Angeles",
            source="tradeshow",
        ),
        rule_score=RuleScoreResult(
            completeness_score=80,
            contactability_score=90,
            business_fit_score=80,
            geography_score=75,
            research_worthy=True,
            strengths=["Lead has a usable email address."],
            warnings=["Lead may need more context before outreach."],
            eligible_for_enrichment=True,
            recommended_rule_action="research",
            rule_reasons=["Lead shows potential, but more context is needed before outreach."],
        ),
        llm_analysis=LLMAnalysisResult(
            priority_tier="high",
            industry_fit="strong",
            reasoning_summary="Strong event-focused lead with solid contactability.",
            confidence=0.82,
            caution_notes=["Needs a little more context before drafting a final outreach email."],
            outreach_subject="Backdrop support for upcoming events",
            outreach_body="Would love to learn more about your event needs.",
            personalization_basis=["Event production company", "Los Angeles location"],
            draft_warnings=["Draft is generic and may need company-specific details."],
            usable_without_rewrite=False,
        ),
        processed_at=datetime(2026, 4, 15, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 15, 12, 5, tzinfo=UTC),
    )


def test_initialize_database_creates_tables(tmp_path) -> None:
    database_url = build_sqlite_url(tmp_path / "test.sqlite3")
    engine = create_database_engine(database_url)
    initialize_database(engine)

    with engine.connect() as connection:
        rows = connection.execute(text("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """)).fetchall()
    table_names = {row._mapping["name"] for row in rows}

    assert "batch_runs" in table_names
    assert "lead_snapshots" in table_names
    assert "lead_analyses" in table_names
    assert "review_decisions" in table_names


def test_runs_repository_round_trip(tmp_path) -> None:
    engine = create_database_engine(build_sqlite_url(tmp_path / "runs.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()
    repository = RunsRepository(session)

    run = repository.create_run(run_type="sample", total_leads=25)
    updated = repository.update_run(
        run.run_id,
        status="completed",
        processed_count=25,
        success_count=22,
        failure_count=3,
        completed_at=datetime(2026, 4, 15, 13, 0, tzinfo=UTC),
    )
    loaded = repository.get_run(run.run_id)

    assert loaded is not None
    assert loaded.run_type == "sample"
    assert loaded.status == "completed"
    assert loaded.processed_count == 25
    assert loaded.completed_at == updated.completed_at


def test_analyses_repository_round_trip(tmp_path) -> None:
    engine = create_database_engine(build_sqlite_url(tmp_path / "analyses.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()

    runs_repository = RunsRepository(session)
    analyses_repository = AnalysesRepository(session)

    run = runs_repository.create_run(run_type="sample", total_leads=1)
    snapshot = analyses_repository.save_snapshot(
        copper_lead_id=101,
        raw_payload={"id": 101, "name": "Jordan Eventson", "company_name": "Premier Event Productions"},
    )
    record = build_sample_analysis_record(
        copper_lead_id=101,
        batch_run_id=run.run_id,
        raw_snapshot_id=snapshot.snapshot_id,
    )

    stored = analyses_repository.save_analysis(
        record,
        llm_provider="openai",
        llm_model="gpt-5.4-nano",
        llm_prompt_version="v1",
    )
    loaded = analyses_repository.get_latest_analysis(101)

    assert loaded is not None
    assert loaded.analysis_id == stored.analysis_id
    assert loaded.batch_run_id == run.run_id
    assert loaded.raw_snapshot_id == snapshot.snapshot_id
    assert loaded.normalized_lead.company_name == "Premier Event Productions"
    assert loaded.llm_analysis is not None
    assert loaded.llm_analysis.priority_tier == "high"
    assert loaded.llm_provider == "openai"
    assert loaded.llm_prompt_version == "v1"
    assert loaded.processed_at == datetime(2026, 4, 15, 12, 0, tzinfo=UTC)


def test_list_analyses_for_run_returns_all_matching_rows(tmp_path) -> None:
    engine = create_database_engine(build_sqlite_url(tmp_path / "run_analyses.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()

    runs_repository = RunsRepository(session)
    analyses_repository = AnalysesRepository(session)

    run = runs_repository.create_run(run_type="bulk", total_leads=2)

    first = build_sample_analysis_record(copper_lead_id=201, batch_run_id=run.run_id)
    second = build_sample_analysis_record(copper_lead_id=202, batch_run_id=run.run_id)

    analyses_repository.save_analysis(first)
    analyses_repository.save_analysis(second)

    analyses = analyses_repository.list_analyses_for_run(run.run_id)

    assert len(analyses) == 2
    assert {analysis.copper_lead_id for analysis in analyses} == {201, 202}


def test_reviews_repository_saves_history_and_updates_status(tmp_path) -> None:
    engine = create_database_engine(build_sqlite_url(tmp_path / "reviews.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()

    analyses_repository = AnalysesRepository(session)
    reviews_repository = ReviewsRepository(session)

    stored = analyses_repository.save_analysis(build_sample_analysis_record())
    review = reviews_repository.create_review_decision(
        analysis_id=stored.analysis_id,
        decision="approved",
        notes="Looks ready for follow-up.",
    )
    history = reviews_repository.get_review_history(stored.analysis_id)
    reloaded = analyses_repository.get_latest_analysis(stored.copper_lead_id)

    assert review.analysis_id == stored.analysis_id
    assert len(history) == 1
    assert history[0].decision == "approved"
    assert history[0].notes == "Looks ready for follow-up."
    assert reloaded is not None
    assert reloaded.review_status == "approved"
