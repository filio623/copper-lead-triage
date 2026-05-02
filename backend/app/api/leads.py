from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_analyses_repository
from backend.app.models.db import StoredLeadAnalysis
from backend.app.repositories.analyses import AnalysesRepository


router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/{copper_lead_id}/analysis")
def get_latest_lead_analysis(
    copper_lead_id: int,
    analyses_repository: AnalysesRepository = Depends(get_analyses_repository),
) -> StoredLeadAnalysis:
    analysis = analyses_repository.get_latest_analysis(copper_lead_id)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis for Copper lead {copper_lead_id}",
        )
    return analysis
