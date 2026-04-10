import time
from pprint import pprint
import httpx
from typing import Dict

from backend.app.core.config import get_settings
from backend.app.models.lead import LeadSnapshot, NormalizedLead

settings = get_settings()

COPPER_API = settings.copper_api_key.get_secret_value()
EMAIL = settings.copper_email

all_count = 0
page = 1

headers = {
    "X-PW-AccessToken": COPPER_API,
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": EMAIL,
    "Content-Type": "application/json",
}

params = {
    "page_size": 200,
    "page_number": page,
    "sort_by": "date_modified",
    "sort_direction": "desc"
    }

start_time = time.time()
end_time = None

first_date = None
last_date = None


def get_lead(page_size:int = 1, page_number:int = 1, headers: Dict[str, str] = None) -> Dict:
    try:
        params = {
            "page_size": page_size,
            "page_number": page_number,
            "sort_by": "date_modified",
            "sort_direction": "desc"
        }
        response = httpx.post("https://api.copper.com/developer_api/v1/leads/search", headers=headers, params=params)

        if response.status_code == 200:
            raw_data = response.json()
            
            return raw_data[0] if raw_data else None
        else:
            print(f"Failed to fetch leads. Status code: {response.status_code}, Response: {response.text}")
            return None

    except httpx.HTTPError as e:
        print(f"An error occurred while fetching leads: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def validate_lead(lead_data: Dict) -> LeadSnapshot:
    validated = LeadSnapshot.model_validate(lead_data)
    return validated

def normalize_lead(lead_snapshot: LeadSnapshot) -> NormalizedLead:
    normalized = NormalizedLead(
        copper_lead_id=lead_snapshot.id,
        full_name=lead_snapshot.name,
        company_name=lead_snapshot.company_name,
        title=lead_snapshot.title,
        primary_email=lead_snapshot.email.email if lead_snapshot.email else None,
        phone_numbers=[phone.number for phone in lead_snapshot.phone_numbers] if lead_snapshot.phone_numbers else None,
        websites=[website.url for website in lead_snapshot.websites] if lead_snapshot.websites else None,
        city=lead_snapshot.address.city if lead_snapshot.address else None,
        source=str(lead_snapshot.customer_source_id) if lead_snapshot.customer_source_id else None
    )
    return normalized

if __name__ == "__main__":
    page_number = 1
    while page_number < 5:
        snapshot = get_lead(page_size=1, page_number=page_number, headers=headers)
        validated_lead = validate_lead(snapshot)
        normalized_lead = normalize_lead(validated_lead)
        pprint(normalized_lead)
        page_number += 1