from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.app.models.lead import NormalizedLead


RuleAction = Literal["pursue", "review", "hold", "reject"]
PriorityTier = Literal["high", "medium", "low", "disqualify"]
IndustryFit = Literal["strong", "moderate", "weak", "unknown"]
ReviewStatus = Literal["pending", "approved", "rejected", "edited"]


class RuleScoreResult(BaseModel):
    completeness_score: int = 0
    contactability_score: int = 0
    disqualifiers: list[str] = Field(default_factory=list)
    eligible_for_enrichment: bool = False
    recommended_rule_action: RuleAction = "review"
    rule_reasons: list[str] = Field(default_factory=list)


class EnrichmentResult(BaseModel):
    company_active: Optional[bool] = None
    event_related: Optional[bool] = None
    fit_for_step_and_repeat_la: Optional[bool] = None
    summary: Optional[str] = None
    fit_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    searched_at: Optional[datetime] = None


class LLMAnalysisResult(BaseModel):
    priority_tier: PriorityTier = "medium"
    industry_fit: IndustryFit = "unknown"
    reasoning_summary: Optional[str] = None
    confidence: Optional[float] = None
    caution_notes: list[str] = Field(default_factory=list)
    outreach_subject: Optional[str] = None
    outreach_body: Optional[str] = None
    personalization_basis: list[str] = Field(default_factory=list)
    draft_warnings: list[str] = Field(default_factory=list)
    usable_without_rewrite: bool = False


class LeadAnalysisRecord(BaseModel):
    copper_lead_id: int
    batch_run_id: Optional[str] = None
    raw_snapshot_id: Optional[str] = None
    normalized_lead: NormalizedLead
    rule_score: RuleScoreResult
    enrichment_result: Optional[EnrichmentResult] = None
    llm_analysis: Optional[LLMAnalysisResult] = None
    review_status: ReviewStatus = "pending"
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
