import argparse
import asyncio
from pprint import pprint

from backend.app.models.db import create_database_engine, create_session_factory, initialize_database
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.runs import RunsRepository
from backend.app.services.batch import BatchDeps, process_raw_batch
from backend.app.services.normalize import get_leads
from backend.app.services.pipeline import PipelineDeps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a larger bulk lead batch through the triage pipeline.")
    parser.add_argument("--page-size", type=int, default=50, help="How many leads to fetch for the bulk batch.")
    parser.add_argument("--page-number", type=int, default=1, help="Which Copper search page to fetch.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # This uses the same repository and dependency wiring as the sample script,
    # but is intended for larger runs so the `run_type` is stored as `bulk`.
    engine = create_database_engine()
    initialize_database(engine)
    session_factory = create_session_factory(engine=engine)
    session = session_factory()

    batch_deps = BatchDeps(
        runs_repository=RunsRepository(session),
        pipeline_deps=PipelineDeps(
            analyses_repository=AnalysesRepository(session),
        ),
    )

    raw_leads = get_leads(page_size=args.page_size, page_number=args.page_number)
    if not raw_leads:
        raise ValueError("No leads returned for the requested bulk run.")

    result = await process_raw_batch(raw_leads, batch_deps, run_type="bulk")

    print("Bulk batch run summary")
    print("----------------------")
    pprint(
        {
            "run_id": result.run.run_id,
            "run_type": result.run.run_type,
            "status": result.run.status,
            "total_leads": result.run.total_leads,
            "processed_count": result.run.processed_count,
            "success_count": result.run.success_count,
            "failure_count": result.run.failure_count,
            "duplicate_lead_ids": result.duplicate_lead_ids,
        }
    )

    if result.failures:
        print("\nFailures")
        print("--------")
        for failure in result.failures:
            pprint(failure)


if __name__ == "__main__":
    asyncio.run(main())
