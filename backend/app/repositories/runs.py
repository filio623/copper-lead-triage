from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.db import (
    BatchRun,
    BatchRunORM,
    RunStatus,
    RunType,
    batch_run_orm_to_model,
    generate_id,
    serialize_datetime,
    utc_now,
)


class RunsRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(
        self,
        run_type: RunType,
        total_leads: int = 0,
        status: RunStatus = "pending",
        run_id: str | None = None,
    ) -> BatchRun:
        # Creating a batch run first gives later pipeline code a stable parent
        # record to attach per-lead analyses to.
        now = utc_now()
        row = BatchRunORM(
            id=run_id or generate_id(),
            run_type=run_type,
            status=status,
            total_leads=total_leads,
            processed_count=0,
            success_count=0,
            failure_count=0,
            started_at=serialize_datetime(now) or "",
            completed_at=None,
            created_at=serialize_datetime(now) or "",
            updated_at=serialize_datetime(now) or "",
        )
        self.session.add(row)
        self.session.commit()
        return batch_run_orm_to_model(row)

    def get_run(self, run_id: str) -> BatchRun | None:
        row = self.session.get(BatchRunORM, run_id)
        if row is None:
            return None
        return batch_run_orm_to_model(row)

    def list_runs(self, limit: int = 50) -> list[BatchRun]:
        rows = self.session.scalars(
            select(BatchRunORM)
            .order_by(BatchRunORM.created_at.desc(), BatchRunORM.id.desc())
            .limit(limit)
        ).all()
        return [batch_run_orm_to_model(row) for row in rows]

    def update_run(
        self,
        run_id: str,
        *,
        status: RunStatus | None = None,
        total_leads: int | None = None,
        processed_count: int | None = None,
        success_count: int | None = None,
        failure_count: int | None = None,
        completed_at: datetime | None = None,
    ) -> BatchRun:
        # This supports simple progress updates without pushing SQL decisions
        # into the batch service layer.
        row = self.session.get(BatchRunORM, run_id)
        if row is None:
            raise ValueError(f"Run {run_id} does not exist.")

        row.status = status or row.status
        row.total_leads = total_leads if total_leads is not None else row.total_leads
        row.processed_count = processed_count if processed_count is not None else row.processed_count
        row.success_count = success_count if success_count is not None else row.success_count
        row.failure_count = failure_count if failure_count is not None else row.failure_count
        row.completed_at = serialize_datetime(completed_at) if completed_at is not None else row.completed_at
        row.updated_at = serialize_datetime(utc_now()) or ""

        self.session.commit()
        return batch_run_orm_to_model(row)
