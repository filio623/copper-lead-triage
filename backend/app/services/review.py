from dataclasses import dataclass
from typing import Any

from backend.app.models.analysis import ReviewStatus
from backend.app.models.db import ReviewDecision, StoredLeadAnalysis
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.reviews import ReviewsRepository


@dataclass
class ReviewDeps:
    analyses_repository: AnalysesRepository
    reviews_repository: ReviewsRepository


def build_review_row(analysis: StoredLeadAnalysis) -> dict[str, Any]:
    return {
        "analysis_id": analysis.analysis_id,
        "copper_lead_id": analysis.copper_lead_id,
        "company_name": analysis.normalized_lead.company_name,
        "person_name": analysis.normalized_lead.full_name,
        "rule_action": analysis.rule_score.recommended_rule_action,
        "top_rule_reasons": analysis.rule_score.rule_reasons,
        "review_status": analysis.review_status,
        "priority_tier": analysis.llm_analysis.priority_tier if analysis.llm_analysis else None,
        "industry_fit": analysis.llm_analysis.industry_fit if analysis.llm_analysis else None,
        "batch_run_id": analysis.batch_run_id,
    }


def get_batch_review_rows(batch_run_id: str, deps: ReviewDeps) -> list[dict[str, Any]]:
    analyses = deps.analyses_repository.list_analyses_for_run(batch_run_id)
    review_rows = []
    for analysis in analyses:
        review_rows.append(build_review_row(analysis))
    return review_rows


def record_review_decision(
    analysis_id: str,
    decision: ReviewStatus,
    deps: ReviewDeps,
    notes: str | None = None,
) -> ReviewDecision:
    return deps.reviews_repository.create_review_decision(
        analysis_id=analysis_id,
        decision=decision,
        notes=notes,
    )


def get_review_history(analysis_id: str, deps: ReviewDeps) -> list[ReviewDecision]:
    return deps.reviews_repository.get_review_history(analysis_id=analysis_id)
