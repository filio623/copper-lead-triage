from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from backend.app.services.batch import BatchDeps, process_raw_batch
from backend.app.api.deps import get_batch_deps, get_runs_repository
from backend.app.models.db import BatchRun
from backend.app.repositories.runs import RunsRepository
from backend.app.services.normalize import get_leads


router = APIRouter(prefix="/runs", tags=["runs"])

class RunBatchRequest(BaseModel):
    page_size: int = 5
    page_number: int = 1

async def run_copper_batch(*, request: RunBatchRequest, run_type: str, deps: BatchDeps) -> dict[str, Any]:
    raw_leads = get_leads(page_size=request.page_size, page_number=request.page_number)
    if not raw_leads:
        raise HTTPException(status_code=404, detail="No leads found for the given page parameters.")
    
    result = await process_raw_batch(raw_leads=raw_leads, deps=deps, run_type=run_type)

    return {
        "run": result.run,
        "failure_count": len(result.failures),
        "duplicate_lead_ids": result.duplicate_lead_ids,
    }

@router.get("/{run_id}")
def get_run(
    run_id: str,
    runs_repository: RunsRepository = Depends(get_runs_repository),
) -> BatchRun:
    run = runs_repository.get_run(run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} does not exist.")
    return run

@router.post("/sample")
async def create_sample_run(request: RunBatchRequest, deps: BatchDeps = Depends(get_batch_deps)) -> dict[str, Any]:
    return await run_copper_batch(request=request, run_type="sample", deps=deps)

@router.post("/bulk")
async def create_bulk_run(request: RunBatchRequest, deps: BatchDeps = Depends(get_batch_deps)) -> dict[str, Any]:
    return await run_copper_batch(request=request, run_type="bulk", deps=deps)
