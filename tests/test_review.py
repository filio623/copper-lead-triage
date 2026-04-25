from datetime import UTC, datetime

from backend.app.models.analysis import (
    LLMAnalysisResult,
    LeadAnalysisRecord,
    RuleScoreResult,
)
from backend.app.models.db import (
    StoredLeadAnalysis,
    build_sqlite_url,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.reviews import ReviewsRepository
from backend.app.repositories.runs import RunsRepository
from backend.app.services.review import (
    ReviewDeps,
    build_review_row,
    get_batch_review_rows,
    get_review_history,
    record_review_decision,
)


def build_review_deps(tmp_path) -> tuple[ReviewDeps, AnalysesRepository, RunsRepository]:
    # Each review test gets an isolated SQLite database so saved review status
    # and review history cannot leak across tests.
    engine = create_database_engine(build_sqlite_url(tmp_path / "review.sqlite3"))
    initialize_database(engine)
    session = create_session_factory(engine=engine)()
    analyses_repository = AnalysesRepository(session)
    reviews_repository = ReviewsRepository(session)
    runs_repository = RunsRepository(session)
    deps = ReviewDeps(
        analyses_repository=analyses_repository,
        reviews_repository=reviews_repository,
    )
    return deps, analyses_repository, runs_repository


def build_sample_analysis_record(
    *,
    copper_lead_id: int = 701,
    batch_run_id: str | None = None,
    include_llm_analysis: bool = True,
) -> LeadAnalysisRecord:
    # This fixture keeps the review service tests focused on review behavior,
    # not on the earlier pipeline/rules/triage stages.
    llm_analysis = None
    if include_llm_analysis:
        llm_analysis = LLMAnalysisResult(
            priority_tier="high",
            industry_fit="strong",
            reasoning_summary="Strong event lead with usable contact data.",
            confidence=0.84,
            caution_notes=["Human should verify event timing before outreach."],
            outreach_subject="Event backdrop support",
            outreach_body="Wanted to introduce Step and Repeat LA.",
            personalization_basis=["Event production company"],
            draft_warnings=["Draft needs final review."],
            usable_without_rewrite=False,
        )

    return LeadAnalysisRecord(
        copper_lead_id=copper_lead_id,
        batch_run_id=batch_run_id,
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
        llm_analysis=llm_analysis,
        processed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 20, 12, 5, tzinfo=UTC),
    )


def test_build_review_row_handles_analysis_without_llm() -> None:
    record = build_sample_analysis_record(include_llm_analysis=False)
    stored = StoredLeadAnalysis(
        analysis_id="analysis-1",
        copper_lead_id=record.copper_lead_id,
        batch_run_id=record.batch_run_id,
        raw_snapshot_id=record.raw_snapshot_id,
        normalized_lead=record.normalized_lead,
        rule_score=record.rule_score,
        enrichment_result=record.enrichment_result,
        llm_analysis=record.llm_analysis,
        review_status=record.review_status,
        processed_at=record.processed_at,
        updated_at=record.updated_at,
    )

    row = build_review_row(stored)

    assert row["analysis_id"] == "analysis-1"
    assert row["copper_lead_id"] == 701
    assert row["company_name"] == "Premier Event Productions"
    assert row["person_name"] == "Jordan Eventson"
    assert row["rule_action"] == "research"
    assert row["priority_tier"] is None
    assert row["industry_fit"] is None


def test_get_batch_review_rows_returns_rows_for_saved_run(tmp_path) -> None:
    deps, analyses_repository, runs_repository = build_review_deps(tmp_path)
    run = runs_repository.create_run(run_type="sample", total_leads=2)

    analyses_repository.save_analysis(
        build_sample_analysis_record(copper_lead_id=702, batch_run_id=run.run_id)
    )
    analyses_repository.save_analysis(
        build_sample_analysis_record(copper_lead_id=703, batch_run_id=run.run_id)
    )

    rows = get_batch_review_rows(run.run_id, deps)

    assert len(rows) == 2
    assert {row["copper_lead_id"] for row in rows} == {702, 703}
    assert all(row["batch_run_id"] == run.run_id for row in rows)


def test_record_review_decision_updates_status_and_history(tmp_path) -> None:
    deps, analyses_repository, _runs_repository = build_review_deps(tmp_path)
    stored = analyses_repository.save_analysis(build_sample_analysis_record())

    decision = record_review_decision(
        analysis_id=stored.analysis_id,
        decision="approved",
        deps=deps,
        notes="Looks ready for follow-up.",
    )
    history = get_review_history(stored.analysis_id, deps)
    reloaded = analyses_repository.get_latest_analysis(stored.copper_lead_id)

    assert decision.analysis_id == stored.analysis_id
    assert decision.decision == "approved"
    assert len(history) == 1
    assert history[0].notes == "Looks ready for follow-up."
    assert reloaded is not None
    assert reloaded.review_status == "approved"
