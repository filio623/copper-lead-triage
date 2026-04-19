from dataclasses import dataclass, field
from typing import Any, Optional

from backend.app.models.db import BatchRun, StoredLeadAnalysis
from backend.app.repositories.runs import RunsRepository
from backend.app.services.pipeline import (
    PipelineDeps,
    process_normalized_lead,
    process_raw_lead,
)
from backend.app.models.lead import NormalizedLead


@dataclass
class BatchDeps:
    runs_repository: RunsRepository
    pipeline_deps: PipelineDeps


@dataclass
class BatchFailure:
    lead_index: int
    copper_lead_id: Optional[int] = None
    error_message: str = ""


@dataclass
class BatchProcessResult:
    run: BatchRun
    analyses: list[StoredLeadAnalysis] = field(default_factory=list)
    failures: list[BatchFailure] = field(default_factory=list)
    duplicate_lead_ids: list[int] = field(default_factory=list)


def _update_run_progress(
    deps: BatchDeps,
    run_id: str,
    success_count: int,
    failure_count: int,
) -> BatchRun:
    # This keeps batch-run counter updates in one place so both raw and
    # normalized processing paths report progress consistently.
    return deps.runs_repository.update_run(
        run_id,
        status="running",
        processed_count=success_count + failure_count,
        success_count=success_count,
        failure_count=failure_count,
    )


async def process_raw_batch(
    raw_leads: list[dict[str, Any]],
    deps: BatchDeps,
    run_type: str = "sample",
) -> BatchProcessResult:
    # This is the main Phase 6 raw-lead batch path. It creates a batch run,
    # processes unique leads one by one through the per-lead pipeline, and
    # records failures without stopping the whole run.
    run = deps.runs_repository.create_run(run_type=run_type, total_leads=len(raw_leads), status="running")

    analyses: list[StoredLeadAnalysis] = []
    failures: list[BatchFailure] = []
    duplicate_lead_ids: list[int] = []
    seen_lead_ids: set[int] = set()

    for index, raw_lead in enumerate(raw_leads):
        lead_id = raw_lead.get("id")
        if isinstance(lead_id, int) and lead_id in seen_lead_ids:
            duplicate_lead_ids.append(lead_id)
            continue
        if isinstance(lead_id, int):
            seen_lead_ids.add(lead_id)

        try:
            analysis = await process_raw_lead(
                raw_lead=raw_lead,
                deps=deps.pipeline_deps,
                batch_run_id=run.run_id,
            )
            analyses.append(analysis)
        except Exception as exc:
            failures.append(
                BatchFailure(
                    lead_index=index,
                    copper_lead_id=lead_id if isinstance(lead_id, int) else None,
                    error_message=str(exc),
                )
            )

        run = _update_run_progress(
            deps=deps,
            run_id=run.run_id,
            success_count=len(analyses),
            failure_count=len(failures),
        )

    run = deps.runs_repository.update_run(
        run.run_id,
        status="completed",
        processed_count=len(analyses) + len(failures),
        success_count=len(analyses),
        failure_count=len(failures),
    )
    return BatchProcessResult(
        run=run,
        analyses=analyses,
        failures=failures,
        duplicate_lead_ids=duplicate_lead_ids,
    )


async def process_normalized_batch(
    normalized_leads: list[NormalizedLead],
    deps: BatchDeps,
    run_type: str = "sample",
) -> BatchProcessResult:
    # This normalized path is useful for local testing and scripted runs where
    # the lead normalization step has already happened upstream.
    run = deps.runs_repository.create_run(run_type=run_type, total_leads=len(normalized_leads), status="running")

    analyses: list[StoredLeadAnalysis] = []
    failures: list[BatchFailure] = []
    duplicate_lead_ids: list[int] = []
    seen_lead_ids: set[int] = set()

    for index, normalized_lead in enumerate(normalized_leads):
        lead_id = normalized_lead.copper_lead_id
        if lead_id in seen_lead_ids:
            duplicate_lead_ids.append(lead_id)
            continue
        seen_lead_ids.add(lead_id)

        try:
            analysis = await process_normalized_lead(
                normalized_lead=normalized_lead,
                deps=deps.pipeline_deps,
                batch_run_id=run.run_id,
            )
            analyses.append(analysis)
        except Exception as exc:
            failures.append(
                BatchFailure(
                    lead_index=index,
                    copper_lead_id=lead_id,
                    error_message=str(exc),
                )
            )

        run = _update_run_progress(
            deps=deps,
            run_id=run.run_id,
            success_count=len(analyses),
            failure_count=len(failures),
        )

    run = deps.runs_repository.update_run(
        run.run_id,
        status="completed",
        processed_count=len(analyses) + len(failures),
        success_count=len(analyses),
        failure_count=len(failures),
    )
    return BatchProcessResult(
        run=run,
        analyses=analyses,
        failures=failures,
        duplicate_lead_ids=duplicate_lead_ids,
    )
