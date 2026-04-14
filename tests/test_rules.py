from backend.app.models.lead import NormalizedLead
from backend.app.services.rules import score_lead, should_send_to_llm


def test_pursue_for_contactable_event_lead() -> None:
    lead = NormalizedLead(
        copper_lead_id=1,
        full_name="Jordan Eventson",
        company_name="Premier Event Productions",
        title="Event Manager",
        primary_email="jordan@premierevents.com",
        phone_numbers=["310-555-1111"],
        websites=["https://premierevents.com"],
        city="Los Angeles",
    )

    result = score_lead(lead)

    assert result.recommended_rule_action == "pursue"
    assert result.completeness_score >= 60
    assert result.contactability_score >= 60
    assert result.business_fit_score >= 65
    assert not result.research_worthy
    assert should_send_to_llm(result) is True


def test_research_for_promising_but_incomplete_lead() -> None:
    lead = NormalizedLead(
        copper_lead_id=2,
        full_name="Taylor Bride",
        company_name="",
        title="Wedding Planner",
        primary_email=None,
        phone_numbers=None,
        websites=["https://taylorweddings.example"],
        city="San Diego",
    )

    result = score_lead(lead)

    assert result.recommended_rule_action == "research"
    assert result.research_worthy is True
    assert result.eligible_for_enrichment is True
    assert result.business_fit_score >= 55
    assert result.contactability_score < 60


def test_hold_for_weak_but_not_rejected_lead() -> None:
    lead = NormalizedLead(
        copper_lead_id=3,
        full_name="Riley Build",
        company_name="Riley Construction Group",
        title="Office Manager",
        primary_email=None,
        phone_numbers=["555-0100"],
        websites=None,
        city=None,
    )

    result = score_lead(lead)

    assert result.recommended_rule_action == "hold"
    assert "Lead has a usable phone number." in result.strengths
    assert should_send_to_llm(result) is False


def test_reject_for_sparse_and_low_fit_lead() -> None:
    lead = NormalizedLead(
        copper_lead_id=4,
        full_name="--",
        company_name="Foundation Repair Math Center",
        title=None,
        primary_email=None,
        phone_numbers=None,
        websites=None,
        city=None,
    )

    result = score_lead(lead)

    assert result.recommended_rule_action == "reject"
    assert result.disqualifiers
    assert result.business_fit_score <= 20
    assert should_send_to_llm(result) is False
