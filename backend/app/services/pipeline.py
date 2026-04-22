from dataclasses import dataclass

from backend.app.services.normalize import validate_lead, normalize_lead
from backend.app.services.rules import score_lead, should_send_to_llm
from backend.app.services.triage import analyze_triage_input
from backend.app.repositories.analyses import AnalysesRepository
from backend.app.models.analysis import RuleScoreResult, LeadAnalysisRecord, TriageInput
from backend.app.models.lead import NormalizedLead
from backend.app.models.db import StoredLeadAnalysis


@dataclass
class PipelineDeps:
    analyses_repository: AnalysesRepository


def build_lead_analysis_record(
      normalized_lead: NormalizedLead,
      rule_score: RuleScoreResult,
      batch_run_id: str | None = None,
      raw_snapshot_id: str | None = None) -> LeadAnalysisRecord:
    return LeadAnalysisRecord(
        copper_lead_id=normalized_lead.copper_lead_id,
        batch_run_id=batch_run_id,
        raw_snapshot_id=raw_snapshot_id,
        normalized_lead=normalized_lead,
        rule_score=rule_score,
        llm_analysis=None,
    )


def build_triage_input(record: LeadAnalysisRecord) -> TriageInput:
    return TriageInput(
        normalized_lead=record.normalized_lead,
        rule_score=record.rule_score,
        enrichment_result=record.enrichment_result,
    )


async def process_normalized_lead(
        normalized_lead: NormalizedLead,
        deps: PipelineDeps,
        batch_run_id: str | None = None,
        raw_snapshot_id: str | None = None) -> StoredLeadAnalysis:

    score = score_lead(normalized_lead)

    lead_record = build_lead_analysis_record(
        normalized_lead=normalized_lead,
        rule_score=score,
        batch_run_id=batch_run_id,
        raw_snapshot_id=raw_snapshot_id,
    )
    triage_input = build_triage_input(lead_record)

    if should_send_to_llm(score):
        lead_record.llm_analysis = await analyze_triage_input(triage_input)

    stored_analysis = deps.analyses_repository.save_analysis(lead_record)
    return stored_analysis


async def process_raw_lead(
      raw_lead: dict,
      deps: PipelineDeps,
      batch_run_id: str | None = None,
  ) -> StoredLeadAnalysis:
    lead = validate_lead(raw_lead)
    normalized_lead = normalize_lead(lead)
    snapshot = deps.analyses_repository.save_snapshot(
        copper_lead_id=lead.id,
        raw_payload=raw_lead,
    )
    analysis = await process_normalized_lead(
        normalized_lead=normalized_lead,
        deps=deps,
        batch_run_id=batch_run_id,
        raw_snapshot_id=snapshot.snapshot_id,
    )
    return analysis

if __name__ == "__main__":
    import asyncio
    from backend.app.models.db import create_database_engine, create_session_factory, initialize_database
    from backend.app.repositories.analyses import AnalysesRepository
    from backend.app.services.normalize import get_leads
    from pprint import pprint

    engine = create_database_engine()
    initialize_database(engine)
    session_factory = create_session_factory(engine=engine)
    session = session_factory()

    deps = PipelineDeps(
        analyses_repository=AnalysesRepository(session)
    )

    try:
        raw_leads = get_leads(page_size=1, page_number=1)
        if not raw_leads:
            raise ValueError("No leads returned")
    except Exception as e:
        print(f"Exception: {e}")
    

    result = asyncio.run(process_raw_lead(raw_leads[0], deps))

    pprint(result.model_dump())


    
