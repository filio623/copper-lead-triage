from dataclasses import dataclass
from typing import Any

from backend.app.models.db import ReviewDecision, StoredLeadAnalysis
from backend.app.repositories.reviews import ReviewsRepository
from backend.app.repositories.analyses import AnalysesRepository



@dataclass
class ReviewDeps:
    analyses_repository: AnalysesRepository
    reviews_respository: ReviewsRepository


def build_review_row(analysis: StoredLeadAnalysis) -> dict[str, Any]:
    return {
        "analysis_id": analysis.analysis_id,
        "copper_lead_id": analysis.copper_lead_id,
        "company_name": analysis.normalized_lead.company_name | None,
        "person_name": analysis.normalized_lead.full_name | None,
        "rule_action": analysis.rule_score.recommended_rule_action,
        "top_rule_reasons": analysis.rule_score.rule_reasons,
        "review_satus": analysis.review_status,
        "priority_tier": analysis.llm_analysis.priority_tier if analysis.llm_analysis else None,
        "industry_fit": analysis.llm_analysis.industry_fit if analysis.llm_analysis else None,
        "batch_run_id": analysis.batch_run_id,
    }

def get_batch_review_rows(batch_run_id: str, deps: ReviewDeps) ->list[dict[str, Any]]:
    pass

def record_review_decision(
        analysis_id: str,
        decision: str,
        deps: ReviewDeps,
        notes: str | None = None
) ->ReviewDecision:
    pass










"""TODO build guide for review workflow support.

Purpose:
- represent the human review step after scoring and triage
- keep review decisions separate from raw analysis generation

Implementation checklist:
- define review decision write paths
- define how pending analyses are listed or exported
- decide what reviewer notes should be stored
- support approve, reject, and edited outcomes

Questions to answer while implementing:
- what should the default review queue sort order be?
- what fields are most important for manual review?
"""



