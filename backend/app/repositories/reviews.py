from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.analysis import ReviewStatus
from backend.app.models.db import (
    LeadAnalysisORM,
    ReviewDecision,
    ReviewDecisionORM,
    generate_id,
    review_decision_orm_to_model,
    serialize_datetime,
    utc_now,
)


class ReviewsRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_review_decision(
        self,
        analysis_id: str,
        decision: ReviewStatus,
        notes: str | None = None,
        review_id: str | None = None,
    ) -> ReviewDecision:
        # Review history is stored separately so the system can keep a real
        # audit trail of human decisions over time.
        analysis_row = self.session.get(LeadAnalysisORM, analysis_id)
        if analysis_row is None:
            raise ValueError(f"Analysis {analysis_id} does not exist.")

        row = ReviewDecisionORM(
            id=review_id or generate_id(),
            analysis_id=analysis_id,
            decision=decision,
            notes=notes,
            decided_at=serialize_datetime(utc_now()) or "",
        )
        self.session.add(row)

        # This mirrors the latest review state back onto the analysis row so
        # summary queries do not have to reconstruct it from history each time.
        analysis_row.review_status = decision
        analysis_row.updated_at = serialize_datetime(utc_now()) or ""

        self.session.commit()
        return review_decision_orm_to_model(row)

    def get_review_history(self, analysis_id: str) -> list[ReviewDecision]:
        rows = self.session.scalars(
            select(ReviewDecisionORM)
            .where(ReviewDecisionORM.analysis_id == analysis_id)
            .order_by(ReviewDecisionORM.decided_at.asc(), ReviewDecisionORM.id.asc())
        ).all()
        return [review_decision_orm_to_model(row) for row in rows]
