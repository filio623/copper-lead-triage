from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_review_deps
from backend.app.services.review import ReviewDeps, get_batch_review_rows


router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/runs/{batch_run_id}")
def list_review_rows(
    batch_run_id: str,
    deps: ReviewDeps = Depends(get_review_deps),
) -> list[dict[str, Any]]:
    # Routes should stay thin: FastAPI handles HTTP/dependency wiring, while
    # the review service owns the actual review-row business shape.
    return get_batch_review_rows(batch_run_id, deps)
