from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import get_db_session
from backend.app.main import app
from backend.app.models.analysis import LLMAnalysisResult, LeadAnalysisRecord, RuleScoreResult
from backend.app.models.db import (
    build_sqlite_url,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.runs import RunsRepository


def build_sample_analysis_record(
    *,
    copper_lead_id: int = 801,
    batch_run_id: str | None = None,
) -> LeadAnalysisRecord:
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
        llm_analysis=LLMAnalysisResult(
            priority_tier="high",
            industry_fit="strong",
            reasoning_summary="Strong event-focused lead with solid contactability.",
            confidence=0.82,
            caution_notes=["Needs a little more context before outreach."],
            outreach_subject="Backdrop support for upcoming events",
            outreach_body="Would love to learn more about your event needs.",
            personalization_basis=["Event production company", "Los Angeles location"],
            draft_warnings=["Draft is generic and may need company-specific details."],
            usable_without_rewrite=False,
        ),
        processed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 20, 12, 5, tzinfo=UTC),
    )


@pytest.fixture
def api_context(tmp_path) -> Generator[
    tuple[TestClient, AnalysesRepository, RunsRepository],
    None,
    None,
]:
    engine = create_database_engine(build_sqlite_url(tmp_path / "api_reviews.sqlite3"))
    initialize_database(engine)
    session_factory = create_session_factory(engine=engine)
    seed_session = session_factory()

    analyses_repository = AnalysesRepository(seed_session)
    runs_repository = RunsRepository(seed_session)

    def override_get_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        yield TestClient(app), analyses_repository, runs_repository
    finally:
        app.dependency_overrides.clear()
        seed_session.close()
        engine.dispose()


def test_health_returns_healthy(api_context) -> None:
    client, _analyses_repository, _runs_repository = api_context

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_review_rows_for_run_returns_saved_rows(api_context) -> None:
    client, analyses_repository, runs_repository = api_context
    run = runs_repository.create_run(run_type="sample", total_leads=2)

    analyses_repository.save_analysis(
        build_sample_analysis_record(copper_lead_id=802, batch_run_id=run.run_id)
    )
    analyses_repository.save_analysis(
        build_sample_analysis_record(copper_lead_id=803, batch_run_id=run.run_id)
    )

    response = client.get(f"/reviews/runs/{run.run_id}")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert {row["copper_lead_id"] for row in rows} == {802, 803}
    assert all(row["batch_run_id"] == run.run_id for row in rows)
    assert all(row["review_status"] == "pending" for row in rows)


def test_post_review_records_decision(api_context) -> None:
    client, analyses_repository, _runs_repository = api_context
    stored = analyses_repository.save_analysis(build_sample_analysis_record())

    response = client.post(
        f"/reviews/{stored.analysis_id}",
        json={"decision": "approved", "notes": "Looks ready for follow-up."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == stored.analysis_id
    assert body["decision"] == "approved"
    assert body["notes"] == "Looks ready for follow-up."

    reloaded = analyses_repository.get_analysis_by_id(stored.analysis_id)
    assert reloaded is not None
    assert reloaded.review_status == "approved"


def test_get_review_history_returns_saved_decisions(api_context) -> None:
    client, analyses_repository, _runs_repository = api_context
    stored = analyses_repository.save_analysis(build_sample_analysis_record())

    client.post(
        f"/reviews/{stored.analysis_id}",
        json={"decision": "approved", "notes": "Looks ready for follow-up."},
    )

    response = client.get(f"/reviews/{stored.analysis_id}/history")

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["analysis_id"] == stored.analysis_id
    assert history[0]["decision"] == "approved"
    assert history[0]["notes"] == "Looks ready for follow-up."


def test_post_review_for_missing_analysis_returns_404(api_context) -> None:
    client, _analyses_repository, _runs_repository = api_context

    response = client.post(
        "/reviews/missing-analysis-id",
        json={"decision": "approved", "notes": None},
    )

    assert response.status_code == 404
