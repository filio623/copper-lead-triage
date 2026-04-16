from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.analysis import LeadAnalysisRecord
from backend.app.models.db import (
    LeadAnalysisORM,
    LeadSnapshotORM,
    LeadSnapshotRecord,
    StoredLeadAnalysis,
    dumps_json,
    generate_id,
    lead_analysis_orm_to_model,
    lead_analysis_to_stored_record,
    lead_snapshot_orm_to_model,
    serialize_datetime,
    utc_now,
)


class AnalysesRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_snapshot(
        self,
        copper_lead_id: int,
        raw_payload: dict[str, Any],
        snapshot_id: Optional[str] = None,
    ) -> LeadSnapshotRecord:
        # Saving raw snapshots separately preserves the original Copper payload
        # that later normalization and analysis were derived from.
        record = LeadSnapshotORM(
            id=snapshot_id or generate_id(),
            copper_lead_id=copper_lead_id,
            raw_payload_json=dumps_json(raw_payload),
            fetched_at=serialize_datetime(utc_now()) or "",
        )
        self.session.add(record)
        self.session.commit()
        return lead_snapshot_orm_to_model(record)

    def save_analysis(
        self,
        lead_analysis: LeadAnalysisRecord,
        analysis_id: Optional[str] = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_prompt_version: str | None = None,
    ) -> StoredLeadAnalysis:
        # This converts the service-layer object into a stored record and then
        # writes the SQLAlchemy row that backs it.
        stored = lead_analysis_to_stored_record(
            analysis_id=analysis_id or generate_id(),
            lead_analysis=lead_analysis,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_prompt_version=llm_prompt_version,
        )
        row = LeadAnalysisORM(
            id=stored.analysis_id,
            copper_lead_id=stored.copper_lead_id,
            batch_run_id=stored.batch_run_id,
            raw_snapshot_id=stored.raw_snapshot_id,
            normalized_json=dumps_json(stored.normalized_lead.model_dump(mode="json")),
            rule_score_json=dumps_json(stored.rule_score.model_dump(mode="json")),
            enrichment_json=dumps_json(stored.enrichment_result.model_dump(mode="json"))
            if stored.enrichment_result is not None
            else None,
            llm_output_json=dumps_json(stored.llm_analysis.model_dump(mode="json"))
            if stored.llm_analysis is not None
            else None,
            llm_provider=stored.llm_provider,
            llm_model=stored.llm_model,
            llm_prompt_version=stored.llm_prompt_version,
            review_status=stored.review_status,
            processed_at=serialize_datetime(stored.processed_at) or "",
            updated_at=serialize_datetime(stored.updated_at) or "",
        )
        self.session.add(row)
        self.session.commit()
        return lead_analysis_orm_to_model(row)

    def get_latest_analysis(self, copper_lead_id: int) -> StoredLeadAnalysis | None:
        # This gives callers the latest saved analysis for a lead without
        # exposing any ORM-specific details above the repository layer.
        row = self.session.scalar(
            select(LeadAnalysisORM)
            .where(LeadAnalysisORM.copper_lead_id == copper_lead_id)
            .order_by(LeadAnalysisORM.processed_at.desc(), LeadAnalysisORM.id.desc())
            .limit(1)
        )
        if row is None:
            return None
        return lead_analysis_orm_to_model(row)

    def list_analyses_for_run(self, batch_run_id: str) -> list[StoredLeadAnalysis]:
        rows = self.session.scalars(
            select(LeadAnalysisORM)
            .where(LeadAnalysisORM.batch_run_id == batch_run_id)
            .order_by(LeadAnalysisORM.processed_at.asc(), LeadAnalysisORM.id.asc())
        ).all()
        return [lead_analysis_orm_to_model(row) for row in rows]

    def update_review_status(self, analysis_id: str, review_status: str) -> None:
        # The review repository stores history, while this method keeps the
        # current effective status updated on the main analysis row.
        row = self.session.get(LeadAnalysisORM, analysis_id)
        if row is None:
            raise ValueError(f"Analysis {analysis_id} does not exist.")

        row.review_status = review_status
        row.updated_at = serialize_datetime(utc_now()) or ""
        self.session.commit()
