from backend.app.models.analysis import RuleScoreResult, TriageInput
from backend.app.models.lead import NormalizedLead
from backend.app.services.triage import (
    TRIAGE_PROMPT_VERSION,
    build_gate_reason,
    build_triage_deps,
    build_triage_prompt,
    get_triage_service_metadata,
    should_run_triage,
)


def build_sample_triage_input(action: str = "research") -> TriageInput:
    # This helper keeps the test fixtures small and focused on the triage
    # contract instead of repeating the same lead setup in every test.
    return TriageInput(
        normalized_lead=NormalizedLead(
            copper_lead_id=101,
            full_name="Jordan Eventson",
            company_name="Premier Event Productions",
            title="Event Manager",
            primary_email="jordan@premierevents.com",
            phone_numbers=["310-555-1111"],
            websites=["https://premierevents.com"],
            city="Los Angeles",
            source="tradeshow",
        ),
        rule_score=RuleScoreResult(
            completeness_score=80,
            contactability_score=90,
            business_fit_score=80,
            geography_score=75,
            research_worthy=True,
            strengths=["Lead has a usable email address."],
            warnings=["Lead may need a little more context before outreach."],
            eligible_for_enrichment=True,
            recommended_rule_action=action,
            rule_reasons=[
                "Lead shows potential, but more context is needed before outreach.",
                "Lead has a usable email address.",
            ],
        ),
    )


def test_should_run_triage_for_research_lead() -> None:
    triage_input = build_sample_triage_input(action="research")
    assert should_run_triage(triage_input) is True


def test_should_not_run_triage_for_hold_lead() -> None:
    triage_input = build_sample_triage_input(action="hold")
    assert should_run_triage(triage_input) is False


def test_build_gate_reason_uses_rule_context() -> None:
    triage_input = build_sample_triage_input(action="pursue")
    gate_reason = build_gate_reason(triage_input)

    assert "pursue" in gate_reason
    assert "Primary reasons:" in gate_reason


def test_build_triage_deps_contains_input_and_gate_reason() -> None:
    triage_input = build_sample_triage_input()
    triage_deps = build_triage_deps(triage_input)

    assert triage_deps.lead == triage_input
    assert triage_deps.gate_reason


def test_build_triage_prompt_contains_serialized_input() -> None:
    triage_input = build_sample_triage_input()
    prompt = build_triage_prompt(triage_input)

    assert "Premier Event Productions" in prompt
    assert "recommended_rule_action" in prompt
    assert "priority_tier" in prompt


def test_get_triage_service_metadata_contains_prompt_version() -> None:
    metadata = get_triage_service_metadata()

    assert metadata["prompt_version"] == TRIAGE_PROMPT_VERSION
    assert metadata["provider"] == "openai"
    assert metadata["model"]
