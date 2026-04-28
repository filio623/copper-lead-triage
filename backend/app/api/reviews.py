from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_review_deps
from backend.app.services.review import ReviewDeps, get_batch_review_rows, record_review_decision, get_review_history
from backend.app.models.analysis import ReviewStatus
from backend.app.models.db import ReviewDecision


router = APIRouter(prefix="/reviews", tags=["reviews"])

class ReviewDecisionRequest(BaseModel):
    decision: ReviewStatus
    notes: str | None = None


@router.get("/runs/{batch_run_id}")
def list_review_rows(
    batch_run_id: str,
    deps: ReviewDeps = Depends(get_review_deps),
) -> list[dict[str, Any]]:
    # Routes should stay thin: FastAPI handles HTTP/dependency wiring, while
    # the review service owns the actual review-row business shape.
    return get_batch_review_rows(batch_run_id, deps)
 

@router.post("/{analysis_id}")
def record_decision(analysis_id: str, request: ReviewDecisionRequest, deps: ReviewDeps = Depends(get_review_deps)) -> ReviewDecision:
    try:
        return record_review_decision(
            analysis_id=analysis_id,
            decision=request.decision,
            notes=request.notes,
            deps=deps,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{analysis_id}/history")
def get_review_decision_history(analysis_id: str, deps: ReviewDeps = Depends(get_review_deps)) -> list[ReviewDecision]:
    try:
        return get_review_history(analysis_id=analysis_id, deps=deps)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error