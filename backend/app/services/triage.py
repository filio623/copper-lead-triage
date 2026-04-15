import asyncio
from dataclasses import dataclass
import re
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

from pydantic_ai import Agent, RunContext
from backend.app.models.analysis import TriageInput, LLMAnalysisResult
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider
from backend.app.core.config import get_settings



"""TODO build guide for the primary PydanticAI triage task.

Purpose:
- interpret a normalized lead plus evidence
- return structured triage output without owning deterministic validation

Suggested responsibilities:
- build the triage task input
- define the triage agent
- run the task and validate the structured output
- attach prompt version and model metadata for persistence

Implementation checklist:
- decide what the agent should receive from rules and enrichment
- define how prompt instructions are composed
- keep one primary per-lead triage task for v1
- separate later tasks such as draft critique into their own modules if needed

Questions to answer while implementing:
- what information should be passed as dependencies versus prompt text?
- what output fields are required for a useful human review queue?
"""


@dataclass
class TriageDeps:
    lead: TriageInput
    gate_reason: str

instructions = "Your job is to take the attached data and provide an analysis of what you think of it"


provider = gateway_provider("openai", api_key=get_settings().pydantic_ai_gateway_api_key.get_secret_value())
model = OpenAIChatModel("gpt-5.4-nano", provider=provider)

triage_agent = Agent(model=model, instructions=instructions, deps_type=TriageDeps, output_type=LLMAnalysisResult)










if __name__ == "__main__":
    from pprint import pprint
    from backend.app.services.normalize import return_normalized_leads
    from backend.app.services.rules import score_lead, should_send_to_llm

    leads = return_normalized_leads(page_number=5, page_size=7, pages=1)

    leads_to_send = []

    for lead in leads:
        score = score_lead(lead)
        send = should_send_to_llm(score)
        if send:
            leads_to_send.append(lead.copper_lead_id)

    # This guard makes the local test harness fail with a clear message instead
    # of crashing with an index error when the sampled page has too few leads.
    if len(leads_to_send) < 2:
        raise ValueError("Need at least two triage-eligible leads in this sample page to run the local triage test.")

    # This keeps your current selection logic, but makes it explicit that we
    # are choosing one already-gated lead for a proof-of-concept agent run.
    first_lead = next((lead for lead in leads if lead.copper_lead_id == leads_to_send[1]), None)

    # This guard makes it obvious if the selected lead id cannot be found back
    # in the normalized list before we try to build the triage input object.
    if first_lead is None:
        raise ValueError("Could not find the selected lead in the normalized lead list.")

    # This is the structured triage input that bundles the normalized lead with
    # its deterministic rule score so the model can use both together.
    triage_input = TriageInput(
        normalized_lead=first_lead,
        rule_score=score_lead(first_lead),
    )

    # This keeps your deps wrapper and gives the Agent the exact dependency
    # shape it expects because the agent was declared with `deps_type=TriageDeps`.
    triage_deps = TriageDeps(
        lead=triage_input,
        gate_reason="Lead has a strong business fit and is contactable, but has some minor completeness issues that may be easily resolved with enrichment. Worth getting LLM insights to determine if it's worth pursuing."
    )

    # This prompt is where we manually inject the actual lead data for now.
    # It is not the final architecture, but it works for a rough POC because
    # your current agent instructions do not yet automatically include `deps`.
    user_prompt = f"""
Please analyze this lead for Step and Repeat LA and return structured output.

Use the deterministic rules as context, but do not just repeat them.
Focus on:
- priority_tier
- industry_fit
- reasoning_summary
- confidence
- caution_notes
- outreach_subject
- outreach_body
- personalization_basis
- draft_warnings
- usable_without_rewrite

Gate summary:
{triage_deps.gate_reason}

Triage input:
{triage_input.model_dump_json(indent=2)}
"""
    print(leads_to_send)

    # This optional debug print lets you inspect the exact structured payload
    # that you are sending into the proof-of-concept agent run.
    # print(triage_input.model_dump_json(indent=2))

    # This now passes the correct deps object and a prompt that actually
    # contains the lead and rule data the model needs to do the task.
    response = triage_agent.run_sync(user_prompt=user_prompt, deps=triage_deps)

    print("*************LLM Analysis Result:***********")
    print(response.output.model_dump_json(indent=2))



