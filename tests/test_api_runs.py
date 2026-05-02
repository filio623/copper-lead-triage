from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import get_db_session
from backend.app.main import app
from backend.app.models.db import (
    build_sqlite_url,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.repositories.runs import RunsRepository


@pytest.fixture
def api_context(tmp_path) -> Generator[tuple[TestClient, RunsRepository], None, None]:
    # The API tests should never touch the real local SQLite database. This
    # override makes FastAPI dependencies use an isolated temporary DB instead.
    engine = create_database_engine(build_sqlite_url(tmp_path / "api_runs.sqlite3"))
    initialize_database(engine)
    session_factory = create_session_factory(engine=engine)
    seed_session = session_factory()
    runs_repository = RunsRepository(seed_session)

    def override_get_db_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        yield TestClient(app), runs_repository
    finally:
        app.dependency_overrides.clear()
        seed_session.close()
        engine.dispose()


def test_get_run_returns_saved_run(api_context) -> None:
    client, runs_repository = api_context
    run = runs_repository.create_run(run_type="sample", total_leads=3)

    response = client.get(f"/runs/{run.run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run.run_id
    assert body["run_type"] == "sample"
    assert body["status"] == "pending"
    assert body["total_leads"] == 3
    assert body["processed_count"] == 0


def test_get_run_for_missing_run_returns_404(api_context) -> None:
    client, _runs_repository = api_context

    response = client.get("/runs/missing-run-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run missing-run-id does not exist."
