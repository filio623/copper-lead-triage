"""Build a more representative lead-review sample from Copper.

This script is meant for Phase 0 manual review. It pulls leads from evenly
spaced pages across the full lead backlog, assigns a simple data-shape bucket
to each lead, and then writes a balanced sample for human review.

Outputs:
- `phase0_review_sample.json`
- `phase0_review_sample.csv`
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.config import get_settings


API_URL = "https://api.copper.com/developer_api/v1/leads/search"
PAGE_SIZE = 200
DEFAULT_SAMPLE_SIZE = 60
DEFAULT_TARGET_PAGES = 12
DEFAULT_JSON_OUTPUT = "phase0_review_sample.json"
DEFAULT_CSV_OUTPUT = "phase0_review_sample.csv"
PLACEHOLDER_VALUES = {"", "--", "unknown", "n/a", "none", "null", "tbd", "test"}


@dataclass(frozen=True)
class LeadFeatures:
    has_name: bool
    has_company: bool
    has_email: bool
    has_phone: bool
    has_website: bool
    interaction_count: int


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if cleaned.casefold() in PLACEHOLDER_VALUES:
        return None

    return cleaned


def _has_email(lead: dict[str, Any]) -> bool:
    email = lead.get("email") or {}
    return _clean_text(email.get("email")) is not None


def _has_phone(lead: dict[str, Any]) -> bool:
    for phone in lead.get("phone_numbers") or []:
        digits = "".join(char for char in str(phone.get("number") or "") if char.isdigit())
        if len(digits) >= 7:
            return True
    return False


def _has_website(lead: dict[str, Any]) -> bool:
    for website in lead.get("websites") or []:
        if _clean_text(website.get("url")) is not None:
            return True
    return False


def extract_features(lead: dict[str, Any]) -> LeadFeatures:
    return LeadFeatures(
        has_name=_clean_text(lead.get("name")) is not None,
        has_company=_clean_text(lead.get("company_name")) is not None,
        has_email=_has_email(lead),
        has_phone=_has_phone(lead),
        has_website=_has_website(lead),
        interaction_count=int(lead.get("interaction_count") or 0),
    )


def classify_bucket(lead: dict[str, Any]) -> str:
    features = extract_features(lead)

    if (features.has_email or features.has_phone) and (features.has_name or features.has_company):
        if features.has_website:
            return "contactable_with_context"
        return "contactable_basic"

    if features.has_company and features.has_website:
        return "researchable_company"

    if features.has_name and not (features.has_email or features.has_phone or features.has_website):
        return "person_sparse"

    if features.has_company and not (features.has_email or features.has_phone):
        return "company_sparse"

    return "very_sparse"


def build_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "X-PW-AccessToken": settings.copper_api_key.get_secret_value(),
        "X-PW-Application": "developer_api",
        "X-PW-UserEmail": settings.copper_email,
        "Content-Type": "application/json",
    }


def fetch_page(client: httpx.Client, page_number: int, headers: dict[str, str]) -> list[dict[str, Any]]:
    payload = {
        "page_size": PAGE_SIZE,
        "page_number": page_number,
        "sort_by": "date_modified",
        "sort_direction": "desc",
    }
    response = client.post(API_URL, headers=headers, json=payload)

    if response.status_code == 422:
        # Some Copper environments appear to accept pagination fields as query
        # params for this endpoint even though the documented approach is JSON.
        response = client.post(API_URL, headers=headers, params=payload)

    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def discover_total_pages(client: httpx.Client, headers: dict[str, str]) -> int:
    page_number = 1

    while True:
        data = fetch_page(client, page_number, headers)
        if not data:
            return page_number - 1
        if len(data) < PAGE_SIZE:
            return page_number
        page_number += 1


def choose_page_numbers(total_pages: int, target_pages: int) -> list[int]:
    if total_pages <= 0:
        return []

    if total_pages <= target_pages:
        return list(range(1, total_pages + 1))

    chosen = {1, total_pages}
    for index in range(target_pages):
        page = 1 + round(index * (total_pages - 1) / max(target_pages - 1, 1))
        chosen.add(page)

    return sorted(chosen)


def gather_candidates(
    client: httpx.Client,
    headers: dict[str, str],
    page_numbers: list[int],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    for page_number in page_numbers:
        page = fetch_page(client, page_number, headers)
        for lead in page:
            lead_id = lead.get("id")
            if not isinstance(lead_id, int) or lead_id in seen_ids:
                continue
            seen_ids.add(lead_id)
            candidates.append(lead)

    return candidates


def choose_balanced_sample(
    candidates: list[dict[str, Any]],
    sample_size: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    bucketed: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for lead in candidates:
        bucketed[classify_bucket(lead)].append(lead)

    for bucket in bucketed.values():
        rng.shuffle(bucket)

    buckets = sorted(bucketed)
    if not buckets:
        return []

    selected: list[dict[str, Any]] = []
    used_ids: set[int] = set()

    while len(selected) < sample_size:
        progress_made = False
        for bucket_name in buckets:
            bucket = bucketed[bucket_name]
            while bucket:
                lead = bucket.pop()
                lead_id = lead["id"]
                if lead_id in used_ids:
                    continue
                used_ids.add(lead_id)
                selected.append(lead)
                progress_made = True
                break
            if len(selected) >= sample_size:
                break

        if not progress_made:
            break

    return selected


def _format_timestamp(value: Any) -> str | None:
    if value is None:
        return None

    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def build_review_row(lead: dict[str, Any]) -> dict[str, Any]:
    features = extract_features(lead)
    bucket = classify_bucket(lead)
    email = (lead.get("email") or {}).get("email")
    phones = [phone.get("number") for phone in lead.get("phone_numbers") or [] if phone.get("number")]
    websites = [website.get("url") for website in lead.get("websites") or [] if website.get("url")]

    return {
        "id": lead.get("id"),
        "bucket": bucket,
        "name": lead.get("name"),
        "company_name": lead.get("company_name"),
        "title": lead.get("title"),
        "details": lead.get("details"),
        "status": lead.get("status"),
        "interaction_count": features.interaction_count,
        "has_name": features.has_name,
        "has_company": features.has_company,
        "has_email": features.has_email,
        "has_phone": features.has_phone,
        "has_website": features.has_website,
        "email": email,
        "phone_numbers": phones,
        "websites": websites,
        "city": (lead.get("address") or {}).get("city"),
        "customer_source_id": lead.get("customer_source_id"),
        "date_created": _format_timestamp(lead.get("date_created")),
        "date_modified": _format_timestamp(lead.get("date_modified")),
        "date_last_contacted": _format_timestamp(lead.get("date_last_contacted")),
        "review_lead_quality": "",
        "review_completeness": "",
        "review_contactability": "",
        "review_business_fit": "",
        "review_recommended_action": "",
        "review_notes": "",
    }


def write_json(path: Path, sample_rows: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    payload = {
        "metadata": metadata,
        "leads": sample_rows,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, sample_rows: list[dict[str, Any]]) -> None:
    if not sample_rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(sample_rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a balanced Phase 0 review sample from Copper leads.")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE, help="Number of leads to export.")
    parser.add_argument(
        "--target-pages",
        type=int,
        default=DEFAULT_TARGET_PAGES,
        help="How many evenly spaced pages to sample from across the backlog.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling.",
    )
    parser.add_argument(
        "--json-output",
        default=DEFAULT_JSON_OUTPUT,
        help="Path for the JSON review export.",
    )
    parser.add_argument(
        "--csv-output",
        default=DEFAULT_CSV_OUTPUT,
        help="Path for the CSV review export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    headers = build_headers()

    with httpx.Client(timeout=30.0) as client:
        total_pages = discover_total_pages(client, headers)
        page_numbers = choose_page_numbers(total_pages=total_pages, target_pages=args.target_pages)
        candidates = gather_candidates(client, headers, page_numbers)
        sample = choose_balanced_sample(candidates, sample_size=args.sample_size, seed=args.seed)

    sample_rows = [build_review_row(lead) for lead in sample]
    metadata = {
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sample_size": len(sample_rows),
        "target_pages": args.target_pages,
        "page_size": PAGE_SIZE,
        "discovered_total_pages": total_pages,
        "sampled_pages": page_numbers,
        "seed": args.seed,
    }

    json_output = Path(args.json_output)
    csv_output = Path(args.csv_output)
    write_json(json_output, sample_rows, metadata)
    write_csv(csv_output, sample_rows)

    print(f"Discovered total pages: {total_pages}")
    print(f"Sampled pages: {page_numbers}")
    print(f"Candidate pool size: {len(candidates)}")
    print(f"Wrote {len(sample_rows)} leads to {json_output}")
    print(f"Wrote {len(sample_rows)} leads to {csv_output}")


if __name__ == "__main__":
    main()
