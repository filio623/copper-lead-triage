"""Export saved lead analyses into a human-review file."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from backend.app.models.db import create_database_engine, create_session_factory, initialize_database
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.reviews import ReviewsRepository
from backend.app.services.review import ReviewDeps, get_batch_review_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export saved lead analyses for human review.")
    parser.add_argument("--batch-run-id", required=True, help="Batch run id to export.")
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Export format.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path for the review export.",
    )
    return parser.parse_args()


def serialize_cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return value


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: serialize_cell(value) for key, value in row.items()})


def write_json(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2, default=str)


def main() -> None:
    args = parse_args()

    # The script stays thin: database setup and file output live here, while
    # the review service owns the business shape of each review row.
    engine = create_database_engine()
    initialize_database(engine)
    session = create_session_factory(engine=engine)()
    deps = ReviewDeps(
        analyses_repository=AnalysesRepository(session),
        reviews_repository=ReviewsRepository(session),
    )

    rows = get_batch_review_rows(args.batch_run_id, deps)
    output_path = Path(args.output)

    if args.format == "csv":
        write_csv(rows, output_path)
    else:
        write_json(rows, output_path)

    print(f"Exported {len(rows)} review rows to {output_path}")


if __name__ == "__main__":
    main()
