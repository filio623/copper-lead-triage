import re

from backend.app.models.analysis import RuleScoreResult
from backend.app.models.lead import NormalizedLead


PLACEHOLDER_VALUES = {"", "--", "unknown", "n/a", "none", "null", "tbd", "test"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# These are deliberately lightweight first-pass heuristics derived from the
# Phase 0 manual review rubric. They should be tuned as more leads are labeled.
POSITIVE_FIT_KEYWORDS = (
    "event",
    "events",
    "wedding",
    "weddings",
    "bridal",
    "photo",
    "photography",
    "fashion",
    "wardrobe",
    "marketing",
    "brand",
    "branding",
    "promotion",
    "promotions",
    "agency",
    "production",
    "productions",
    "venue",
    "hospitality",
    "conference",
    "expo",
    "trade show",
    "tradeshow",
    "show",
    "media",
    "display",
    "events manager",
    "event manager",
    "event planning",
)

NEGATIVE_FIT_KEYWORDS = (
    "math",
    "mathematics",
    "foundation repair",
    "plumbing",
)

LOCAL_CITY_KEYWORDS = {
    "los angeles",
    "hollywood",
    "west hollywood",
    "burbank",
    "pasadena",
    "long beach",
    "santa monica",
    "culver city",
    "beverly hills",
    "glendale",
    "torrance",
    "anaheim",
    "irvine",
    "newport beach",
    "malibu",
}


def _clean_text(value: str | None = None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if cleaned.casefold() in PLACEHOLDER_VALUES:
        return None

    return cleaned


def _normalized_values(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized = []
    for value in values:
        cleaned = _clean_text(value)
        if cleaned is not None:
            normalized.append(cleaned)
    return normalized


def has_name(lead: NormalizedLead) -> bool:
    return _clean_text(lead.full_name) is not None


def has_company(lead: NormalizedLead) -> bool:
    return _clean_text(lead.company_name) is not None


def has_title(lead: NormalizedLead) -> bool:
    return _clean_text(lead.title) is not None


def has_usable_email(lead: NormalizedLead) -> bool:
    email = _clean_text(lead.primary_email)
    if email is None:
        return False
    return bool(EMAIL_PATTERN.match(email))


def has_usable_phone(lead: NormalizedLead) -> bool:
    for phone in _normalized_values(lead.phone_numbers):
        digits = "".join(char for char in phone if char.isdigit())
        if len(digits) >= 7:
            return True
    return False


def has_website(lead: NormalizedLead) -> bool:
    return bool(_normalized_values(lead.websites))


def has_city(lead: NormalizedLead) -> bool:
    return _clean_text(lead.city) is not None


def score_completeness(lead: NormalizedLead) -> int:
    score = 0
    if has_name(lead):
        score += 20
    if has_company(lead):
        score += 20
    if has_title(lead):
        score += 10
    if has_usable_email(lead):
        score += 20
    if has_usable_phone(lead):
        score += 15
    if has_website(lead):
        score += 10
    if has_city(lead):
        score += 5
    return score


def score_contactability(lead: NormalizedLead) -> int:
    score = 0
    if has_usable_email(lead):
        score += 60
    if has_usable_phone(lead):
        score += 30
    if has_website(lead):
        score += 10
    return score


def _fit_text(lead: NormalizedLead) -> str:
    parts = [
        _clean_text(lead.company_name),
        _clean_text(lead.title),
        _clean_text(lead.full_name),
        _clean_text(lead.source),
    ]
    parts.extend(_normalized_values(lead.websites))
    return " ".join(part for part in parts if part).casefold()


def _keyword_matches(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def score_business_fit(lead: NormalizedLead) -> tuple[int, list[str], list[str]]:
    text = _fit_text(lead)
    positive_matches = _keyword_matches(text, POSITIVE_FIT_KEYWORDS)
    negative_matches = _keyword_matches(text, NEGATIVE_FIT_KEYWORDS)

    strengths: list[str] = []
    warnings: list[str] = []

    if negative_matches:
        warnings.append(
            f"Lead contains low-fit keyword signals: {', '.join(sorted(set(negative_matches)))}."
        )
        return 20, strengths, warnings

    if len(positive_matches) >= 2:
        strengths.append(
            f"Lead contains strong fit keywords: {', '.join(sorted(set(positive_matches[:3])))}."
        )
        return 80, strengths, warnings

    if positive_matches:
        strengths.append(f"Lead contains a plausible fit keyword: {positive_matches[0]}.")
        return 65, strengths, warnings

    if has_company(lead) or has_title(lead):
        warnings.append("Lead has enough identity data to review, but fit is still unclear.")
        return 45, strengths, warnings

    warnings.append("Lead does not contain enough business context to estimate fit confidently.")
    return 30, strengths, warnings


def score_geography(lead: NormalizedLead) -> tuple[int, list[str], list[str]]:
    city = _clean_text(lead.city)
    if city is None:
        return 40, [], ["City is missing, so geography fit is unknown."]

    city_key = city.casefold()
    if city_key in LOCAL_CITY_KEYWORDS:
        return 75, [f"Lead is in or near the core Southern California service area ({city})."], []

    return 55, [], [f"Lead is outside the core local-city list or location fit is uncertain ({city})."]


def _build_strengths(lead: NormalizedLead) -> list[str]:
    strengths: list[str] = []
    if has_name(lead):
        strengths.append("Lead has a usable contact name.")
    if has_company(lead):
        strengths.append("Lead has a company name.")
    if has_usable_email(lead):
        strengths.append("Lead has a usable email address.")
    if has_usable_phone(lead):
        strengths.append("Lead has a usable phone number.")
    if has_website(lead):
        strengths.append("Lead has a website for additional context.")
    return strengths


def _build_warnings(lead: NormalizedLead) -> list[str]:
    warnings: list[str] = []
    if not has_name(lead):
        warnings.append("Lead is missing a usable contact name.")
    if not has_company(lead):
        warnings.append("Lead is missing a company name.")
    if not has_usable_email(lead) and not has_usable_phone(lead):
        warnings.append("Lead does not have a direct usable contact method.")
    if not has_website(lead):
        warnings.append("Lead does not have a website for added context.")
    return warnings


def _build_disqualifiers(
    completeness_score: int,
    contactability_score: int,
    business_fit_score: int,
) -> list[str]:
    disqualifiers: list[str] = []

    if contactability_score == 0 and completeness_score < 35:
        disqualifiers.append("Lead is too incomplete to contact or assess confidently.")

    if business_fit_score <= 20:
        disqualifiers.append("Lead appears to be a weak fit for Step and Repeat LA.")

    return disqualifiers


def _determine_action(
    completeness_score: int,
    contactability_score: int,
    business_fit_score: int,
    disqualifiers: list[str],
) -> str:
    if disqualifiers and contactability_score == 0:
        return "reject"

    if business_fit_score <= 20 and contactability_score <= 40:
        return "reject"

    if completeness_score >= 60 and contactability_score >= 60 and business_fit_score >= 65:
        return "pursue"

    if business_fit_score >= 55 and (completeness_score < 60 or contactability_score < 60):
        return "research"

    if business_fit_score >= 45 and contactability_score >= 60 and completeness_score >= 50:
        return "research"

    return "hold"


def _is_research_worthy(
    recommended_rule_action: str,
    completeness_score: int,
    contactability_score: int,
    business_fit_score: int,
) -> bool:
    if recommended_rule_action == "research":
        return True

    return business_fit_score >= 65 and (completeness_score < 60 or contactability_score < 60)


def _build_rule_reasons(
    action: str,
    disqualifiers: list[str],
    strengths: list[str],
    warnings: list[str],
) -> list[str]:
    if action == "pursue":
        reasons = ["Lead is contactable now and shows plausible business fit."]
    elif action == "research":
        reasons = ["Lead shows potential, but more context is needed before outreach."]
    elif action == "hold":
        reasons = ["Lead is not strong enough to prioritize now, but not weak enough to reject."]
    else:
        reasons = ["Lead is too sparse or too weak a fit to prioritize."]

    reasons.extend(disqualifiers[:2])
    reasons.extend(strengths[:2])
    reasons.extend(warnings[:2])

    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def score_lead(lead: NormalizedLead) -> RuleScoreResult:
    completeness_score = score_completeness(lead)
    contactability_score = score_contactability(lead)

    business_fit_score, fit_strengths, fit_warnings = score_business_fit(lead)
    geography_score, geography_strengths, geography_warnings = score_geography(lead)

    strengths = _build_strengths(lead) + fit_strengths + geography_strengths
    warnings = _build_warnings(lead) + fit_warnings + geography_warnings
    disqualifiers = _build_disqualifiers(
        completeness_score=completeness_score,
        contactability_score=contactability_score,
        business_fit_score=business_fit_score,
    )

    recommended_rule_action = _determine_action(
        completeness_score=completeness_score,
        contactability_score=contactability_score,
        business_fit_score=business_fit_score,
        disqualifiers=disqualifiers,
    )

    research_worthy = _is_research_worthy(
        recommended_rule_action=recommended_rule_action,
        completeness_score=completeness_score,
        contactability_score=contactability_score,
        business_fit_score=business_fit_score,
    )
    eligible_for_enrichment = research_worthy and business_fit_score >= 55 and not disqualifiers
    rule_reasons = _build_rule_reasons(
        action=recommended_rule_action,
        disqualifiers=disqualifiers,
        strengths=strengths,
        warnings=warnings,
    )

    return RuleScoreResult(
        completeness_score=completeness_score,
        contactability_score=contactability_score,
        business_fit_score=business_fit_score,
        geography_score=geography_score,
        research_worthy=research_worthy,
        disqualifiers=disqualifiers,
        strengths=strengths,
        warnings=warnings,
        eligible_for_enrichment=eligible_for_enrichment,
        recommended_rule_action=recommended_rule_action,
        rule_reasons=rule_reasons,
    )


def should_send_to_llm(rule_score: RuleScoreResult) -> bool:
    return rule_score.recommended_rule_action in {"pursue", "research"}

if __name__ == "__main__":
    from backend.app.services.normalize import return_normalized_leads
    from pprint import pprint
    
    leads = return_normalized_leads(page_number=5, page_size=6, pages=1)
    for lead in leads:
        score = score_lead(lead)
        send = should_send_to_llm(score)
        print("*************Lead Analysis:***********")
        pprint(lead.model_dump())
        print("*************Rule Score:**************")
        pprint(score.model_dump())
        print("*************Should Send to LLM:************")
        print(f"Should I send to the LLM? : {send}")
        print("*" * 20)