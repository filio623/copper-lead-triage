import asyncio
from dataclasses import dataclass
import re
from pprint import pprint
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider

from backend.app.core.config import get_settings
from backend.app.models.analysis import LLMAnalysisResult
from backend.app.models.lead import NormalizedLead
from backend.app.services.normalize import return_normalized_leads




PLACEHOLDER_VALUES = {"", "--", "unknown", "n/a", "none", "null", "tbd", "test"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
settings = get_settings()


@dataclass
class TriageDeps:
    lead: NormalizedLead
    gate_reason: str


TRIAGE_INSTRUCTIONS = """
You are reviewing Copper CRM leads for Step and Repeat LA.

Your job is to analyze whether a lead looks worth pursuing based only on the provided record.

Important rules:
- Do not invent facts that are not present in the lead record.
- Treat missing data as missing data, not as a negative business signal unless it clearly limits actionability.
- Focus on business fit, actionability, and whether more research would materially help.
- Keep reasoning concise and grounded in the provided fields.
- If confidence is low, say so in the confidence field and caution notes.
- Return structured output that matches the requested schema.

Step and Repeat LA sells branded event backdrops, step and repeats, media walls, display products, and related event signage/services.
"""

triage_agent = Agent(
    OpenAIChatModel(
        "gpt-5.2",
        provider=gateway_provider(
            "openai",
            api_key=settings.pydantic_ai_gateway_api_key.get_secret_value(),
        ),
    ),
    output_type=LLMAnalysisResult,
    instructions=TRIAGE_INSTRUCTIONS,
    deps_type=TriageDeps,
)


@triage_agent.instructions
def add_triage_context(ctx: RunContext[TriageDeps]) -> str:
    return f"""Deterministic gate summary:
- {ctx.deps.gate_reason}

Lead data:
{ctx.deps.lead.model_dump_json(indent=2)}
"""


def _clean_text(value: str | None = None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _is_placeholder(value: str | None = None) -> bool:
    cleaned = _clean_text(value)
    if cleaned is None:
        return False

    return cleaned.casefold() in PLACEHOLDER_VALUES


def has_usable_email(lead: NormalizedLead) -> bool:
    email = _clean_text(lead.primary_email)
    if email is None or _is_placeholder(email):
        return False

    return bool(EMAIL_PATTERN.match(email))


def has_usable_phone(lead: NormalizedLead) -> bool:
    if not lead.phone_numbers:
        return False

    for phone in lead.phone_numbers:
        cleaned = _clean_text(phone)
        if cleaned is None or _is_placeholder(cleaned):
            continue

        digits = "".join(char for char in cleaned if char.isdigit())
        if len(digits) >= 7:
            return True

    return False


def has_basic_identity(lead: NormalizedLead) -> bool:
    full_name = _clean_text(lead.full_name)
    company_name = _clean_text(lead.company_name)

    if full_name and not _is_placeholder(full_name):
        return True
    if company_name and not _is_placeholder(company_name):
        return True
    if lead.websites:
        return True

    return False


def should_send_to_llm(lead: NormalizedLead) -> bool:
    return has_basic_identity(lead) and (has_usable_email(lead) or has_usable_phone(lead))


def gate_reason(lead: NormalizedLead) -> str:
    if should_send_to_llm(lead):
        return "Lead has basic identity information and at least one usable contact method."
    if has_basic_identity(lead):
        return "Lead has some identity information but no usable email or phone yet."
    return "Lead does not have enough usable identity information for LLM triage."


def get_leads_for_llm(page_number: int = 1, page_size: int = 5, pages: int = 1, get_all: bool = False) -> list[NormalizedLead]:
    leads = return_normalized_leads(
        page_number=page_number,
        page_size=page_size,
        pages=pages,
        get_all=get_all,
    )
    return [lead for lead in leads if should_send_to_llm(lead)]


def split_leads_by_gate(
    page_number: int = 1,
    page_size: int = 25,
    pages: int = 1,
    get_all: bool = False,
) -> tuple[list[NormalizedLead], list[NormalizedLead]]:
    leads = return_normalized_leads(
        page_number=page_number,
        page_size=page_size,
        pages=pages,
        get_all=get_all,
    )

    llm_ready = [lead for lead in leads if should_send_to_llm(lead)]
    not_ready = [lead for lead in leads if not should_send_to_llm(lead)]
    return llm_ready, not_ready


def build_triage_prompt() -> str:
    return """Analyze this sales lead for Step and Repeat LA.

Return a structured analysis of:
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
"""


async def analyze_lead_with_llm(lead: NormalizedLead) -> LLMAnalysisResult:
    if not should_send_to_llm(lead):
        raise ValueError("Lead did not pass the deterministic gate and should not be sent to the LLM.")

    result = await triage_agent.run(
        build_triage_prompt(),
        deps=TriageDeps(
            lead=lead,
            gate_reason=gate_reason(lead),
        ),
    )
    return result.output


async def analyze_leads_with_llm(leads: list[NormalizedLead]) -> list[tuple[NormalizedLead, LLMAnalysisResult]]:
    analyses = []
    for lead in leads:
        if not should_send_to_llm(lead):
            continue

        analyses.append((lead, await analyze_lead_with_llm(lead)))

    return analyses


async def get_and_analyze_leads(
    page_number: int = 1,
    page_size: int = 2,
    pages: int = 1,
    get_all: bool = False,
) -> list[tuple[NormalizedLead, LLMAnalysisResult]]:
    leads = get_leads_for_llm(
        page_number=page_number,
        page_size=page_size,
        pages=pages,
        get_all=get_all,
    )
    return await analyze_leads_with_llm(leads)


async def _main() -> None:
    analyzed_leads = await get_and_analyze_leads(page_number=89, page_size=3, pages=1)
    for lead, analysis in analyzed_leads:
        print(f"Lead: {lead.full_name} ({lead.company_name})")
        pprint(analysis.model_dump())
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(_main())
