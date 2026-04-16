import asyncio
from dataclasses import dataclass
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

from pydantic_ai import Agent, RunContext
from backend.app.models.analysis import TriageInput, LLMAnalysisResult
from backend.app.clients.llm import get_triage_model, get_triage_model_metadata
from backend.app.services.rules import should_send_to_llm


# This prompt version gives you a stable identifier for the first triage task.
# It will matter later when you start comparing prompt changes over time.
TRIAGE_PROMPT_VERSION = "v1"

# These are the persistent high-level instructions for the triage task.
# The goal is to keep the agent focused on judgment and drafting, not on
# re-checking deterministic rules or inventing facts that are not present.
TRIAGE_INSTRUCTIONS = """
You are reviewing Copper CRM leads for Step and Repeat LA.

Your job is to interpret the provided lead record and deterministic rule output.

Important rules:
- Do not invent facts that are not present in the provided input.
- Treat the rule score as context, not as the only source of truth.
- Focus on business fit, actionability, and whether the lead deserves human attention.
- Keep reasoning concise and grounded in the provided data.
- If data is missing, acknowledge the uncertainty instead of filling gaps with guesses.
- Return structured output that matches the requested schema.

Step and Repeat LA sells event backdrops, step and repeats, media walls, branded displays, and related event-signage products.
"""


@dataclass
class TriageDeps:
    lead: TriageInput
    gate_reason: str

# This keeps your simple module-level agent definition in place, but now the
# model wiring is pulled from the thin `clients/llm.py` helper.
triage_agent = Agent(
    model=get_triage_model(),
    instructions=TRIAGE_INSTRUCTIONS,
    deps_type=TriageDeps,
    output_type=LLMAnalysisResult,
)

# This instruction hook shows one clean use of `deps`: the agent gets a short,
# human-readable gate summary without you having to manually repeat it in the
# module-level instruction string every time.
@triage_agent.instructions
def add_triage_context(ctx: RunContext[TriageDeps]) -> str:
    return f"""Deterministic triage gate summary:
- {ctx.deps.gate_reason}

Prompt version:
- {TRIAGE_PROMPT_VERSION}
"""


def should_run_triage(triage_input: TriageInput) -> bool:
    # The rules layer owns the gating decision. This helper just makes the
    # triage service boundary explicit and easy to read from callers.
    return should_send_to_llm(triage_input.rule_score)


def build_gate_reason(triage_input: TriageInput) -> str:
    # This creates a compact summary from the deterministic rule result so the
    # model can quickly understand why the lead reached triage.
    rule_score = triage_input.rule_score
    action = rule_score.recommended_rule_action

    reason_parts = [f"Rules recommended '{action}'."]

    if rule_score.rule_reasons:
        reason_parts.append(f"Primary reasons: {' '.join(rule_score.rule_reasons[:2])}")

    if rule_score.disqualifiers:
        reason_parts.append(f"Disqualifiers noted: {' '.join(rule_score.disqualifiers[:2])}")

    return " ".join(reason_parts)


def build_triage_deps(triage_input: TriageInput) -> TriageDeps:
    # This keeps construction of the deps object in one place so the async
    # service function and the local demo harness use the same shape.
    return TriageDeps(
        lead=triage_input,
        gate_reason=build_gate_reason(triage_input),
    )


def build_triage_prompt(triage_input: TriageInput) -> str:
    # This is the task-specific prompt body. For now it directly includes the
    # serialized triage input because that is the simplest working way to let
    # the model see the normalized lead and rule output together.
    return f"""
Please analyze this lead for Step and Repeat LA and return structured output.

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

Use the deterministic rule output as context, but do not merely repeat it.
Do not invent missing facts. If the lead is weak or uncertain, say so clearly.

Triage input:
{triage_input.model_dump_json(indent=2)}
"""


async def analyze_triage_input(triage_input: TriageInput) -> LLMAnalysisResult:
    # This is the main async service entrypoint that later code in `pipeline.py`
    # should call once normalization and rules have already happened.
    if not should_run_triage(triage_input):
        raise ValueError(
            "Triage should only run for leads that passed the deterministic gate."
        )

    triage_deps = build_triage_deps(triage_input)
    user_prompt = build_triage_prompt(triage_input)
    result = await triage_agent.run(user_prompt=user_prompt, deps=triage_deps)
    return result.output


def analyze_triage_input_sync(triage_input: TriageInput) -> LLMAnalysisResult:
    # This sync wrapper is convenient for local experimentation and simple
    # scripts so you do not have to manage an event loop every time.
    return asyncio.run(analyze_triage_input(triage_input))


def get_triage_service_metadata() -> dict[str, str]:
    # This exposes minimal task metadata now so you can inspect which prompt
    # and model are being used even before persistence exists.
    metadata = get_triage_model_metadata()
    metadata["prompt_version"] = TRIAGE_PROMPT_VERSION
    return metadata










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

    # This now uses the shared helper so the local harness exercises the same
    # service logic that later callers will rely on.
    triage_deps = build_triage_deps(triage_input)
    print(leads_to_send)
    print(get_triage_service_metadata())

    # This optional debug print lets you inspect the exact structured payload
    # that you are sending into the proof-of-concept agent run.
    # print(triage_input.model_dump_json(indent=2))

    print("*************LLM Analysis Result:***********")
    pprint(triage_deps)
    print(analyze_triage_input_sync(triage_input).model_dump_json(indent=2))


