import time
from pprint import pprint
import httpx
from typing import Dict, List

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


def get_leads_page(page_size: int = 1, page_number: int = 1, headers: Dict[str, str] = headers) -> List[Dict]:
    try:
        data = {
            "page_size": page_size,
            "page_number": page_number,
            "sort_by": "date_modified",
            "sort_direction": "desc"
        }
        # Copper Search API expects search parameters in the JSON body for POST requests
        response = httpx.post("https://api.copper.com/developer_api/v1/leads/search", headers=headers, json=data)

        if response.status_code == 200:
            raw_data = response.json()
            return raw_data if isinstance(raw_data, list) else []
        else:
            print(f"Failed to fetch leads. Status code: {response.status_code}, Response: {response.text}")
            return []

    except httpx.HTTPError as e:
        print(f"An error occurred while fetching leads: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


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

def return_normalized_leads(page_number: int = 1, page_size: int = 1, pages: int = 1, get_all: bool = False) -> List[NormalizedLead]:
    normalized_leads = []
    current_page = page_number
    
    if get_all:
        while True:
            leads_data = get_leads_page(page_number=current_page, page_size=page_size)
            if not leads_data:
                break
            
            for lead_dict in leads_data:
                validated_lead = validate_lead(lead_dict)
                normalized_lead = normalize_lead(validated_lead)
                normalized_leads.append(normalized_lead)
            
            current_page += 1
    else:
        for _ in range(pages):
            leads_data = get_leads_page(page_number=current_page, page_size=page_size)
            if not leads_data:
                break
                
            for lead_dict in leads_data:
                validated_lead = validate_lead(lead_dict)
                normalized_lead = normalize_lead(validated_lead)
                normalized_leads.append(normalized_lead)
            
            current_page += 1
            
    return normalized_leads


if __name__ == "__main__":
    # Test with a single page of 5 leads
    leads = return_normalized_leads(page_number=1, page_size=5, pages=1)
    for lead in leads:
        pprint(lead)