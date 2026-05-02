from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import get_db_session
from backend.app.main import app
from backend.app.models.analysis import LeadAnalysisRecord, RuleScoreResult
from backend.app.models.db import (
    build_sqlite_url,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.models.lead import NormalizedLead
from backend.app.repositories.analyses import AnalysesRepository


def build_sample_analysis_record(copper_lead_id: int = 901) -> LeadAnalysisRecord:
    # Keep this fixture small because the API test only needs a saved analysis
    # to prove the route reads existing data without running the pipeline.
    return LeadAnalysisRecord(
        copper_lead_id=copper_lead_id,
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
        processed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 20, 12, 5, tzinfo=UTC),
    )


@pytest.fixture
def api_context(tmp_path) -> Generator[tuple[TestClient, AnalysesRepository], None, None]:
    # Route tests should use a temporary database so they never read from or
    # write to the real local app database.
    engine = create_database_engine(build_sqlite_url(tmp_path / "api_leads.sqlite3"))
    initialize_database(engine)
    session_factory = create_session_factory(engine=engine)
    seed_session = session_factory()
    analyses_repository = AnalysesRepository(seed_session)

    def override_get_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        yield TestClient(app), analyses_repository
    finally:
        app.dependency_overrides.clear()
        seed_session.close()
        engine.dispose()


def test_get_latest_lead_analysis_returns_saved_analysis(api_context) -> None:
    client, analyses_repository = api_context
    stored = analyses_repository.save_analysis(build_sample_analysis_record(copper_lead_id=901))

    response = client.get("/leads/901/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == stored.analysis_id
    assert body["copper_lead_id"] == 901
    assert body["normalized_lead"]["company_name"] == "Premier Event Productions"
    assert body["rule_score"]["recommended_rule_action"] == "research"


def test_get_latest_lead_analysis_for_missing_lead_returns_404(api_context) -> None:
    client, _analyses_repository = api_context

    response = client.get("/leads/999999/analysis")

    assert response.status_code == 404
    assert response.json()["detail"] == "No analysis for Copper lead 999999"
