import os
import httpx
import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

COPPER_API = os.getenv("COPPER_API")
EMAIL = "codi@stepandrepeatla.com"
BASE_URL = "https://api.copper.com/developer_api/v1"

headers = {
    "X-PW-AccessToken": COPPER_API,
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": EMAIL,
    "Content-Type": "application/json",
}

async def fetch_all(endpoint, payload_template=None):
    all_records = []
    page = 1
    if payload_template is None:
        payload_template = {}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            payload = payload_template.copy()
            payload["page_size"] = 200
            payload["page_number"] = page
            
            response = await client.post(f"{BASE_URL}/{endpoint}", headers=headers, json=payload)
            if response.status_code != 200:
                print(f"Error fetching {endpoint} page {page}: {response.status_code}")
                break
            data = response.json()
            if not data: break
            all_records.extend(data)
            if len(data) < 200: break
            page += 1
    return all_records

async def main():
    print("--- STARTING VERIFICATION PART 2 ---")
    
    # 1. Pipelines & Stages
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/pipelines", headers=headers)
        pipelines = resp.json()
        sales_board = next((p for p in pipelines if p['name'] == "Sales Board"), None)
        stage_map = {s['id']: s['name'] for s in sales_board['stages']} if sales_board else {}

    # 2. Loss Reasons
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/loss_reasons", headers=headers)
        loss_reasons = resp.json()
        loss_reason_map = {lr['id']: lr['name'] for lr in loss_reasons}

    # 3. Custom Field for Lead Quality (Communication Status)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/custom_field_definitions", headers=headers)
        custom_fields = resp.json()
        comm_status_cf = next((cf for cf in custom_fields if cf['name'] == "Communication Status"), None)
        bad_email_ids = []
        if comm_status_cf:
            bad_email_ids = [opt['id'] for opt in comm_status_cf['options'] if "Bad Email" in opt['name'] or "No Email" in opt['name']]

    # 4. Lead Sources
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/customer_sources", headers=headers)
        sources = resp.json()
        source_map = {s['id']: s['name'] for s in sources}

    # OPPORTUNITIES ANALYSIS
    print("\nAnalyzing Opportunities for Funnel and Loss Reasons...")
    opps = await fetch_all("opportunities/search")
    
    funnel = {} # stage_id -> {won: 0, lost: 0}
    loss_counts = {} # reason_id -> count
    company_won_stats = {} # company_id -> {won_count: 0, won_revenue: 0, total_count: 0}
    
    for o in opps:
        status = o.get("status")
        stage_id = o.get("pipeline_stage_id")
        
        if status in ["Won", "Lost"]:
            if stage_id not in funnel: funnel[stage_id] = {"won": 0, "lost": 0}
            if status == "Won": funnel[stage_id]["won"] += 1
            else: funnel[stage_id]["lost"] += 1
            
        if status == "Lost":
            lr_id = o.get("loss_reason_id")
            loss_counts[lr_id] = loss_counts.get(lr_id, 0) + 1

        cid = o.get("company_id")
        if cid:
            if cid not in company_won_stats: company_won_stats[cid] = {"won_count": 0, "won_revenue": 0, "total_count": 0}
            company_won_stats[cid]["total_count"] += 1
            if status == "Won":
                company_won_stats[cid]["won_count"] += 1
                company_won_stats[cid]["won_revenue"] += (o.get("monetary_value") or 0)

    print("\n[2.3] Funnel Conversion (Sales Board):")
    for stage_id, counts in funnel.items():
        name = stage_map.get(stage_id, f"Unknown({stage_id})")
        total = counts['won'] + counts['lost']
        rate = (counts['won'] / total * 100) if total > 0 else 0
        print(f"  {name}: Won {counts['won']}, Lost {counts['lost']}, Win Rate {rate:.1f}%")

    print("\n[2.6] Loss Reasons:")
    for lr_id, count in loss_counts.items():
        name = loss_reason_map.get(lr_id, "Not Specified") if lr_id else "Not Specified"
        print(f"  {name}: {count} ({count/status_counts_lost*100:.1f}%)" if 'status_counts_lost' in locals() else f"  {name}: {count}")
    # Wait, I need status_counts_lost. From previous run it was 585.
    
    print("\n[5.2] Top Repeat Buyers (Sample):")
    sorted_companies = sorted(company_won_stats.items(), key=lambda x: x[1]['total_count'], reverse=True)[:10]
    async with httpx.AsyncClient() as client:
        for cid, stats in sorted_companies:
            resp = await client.get(f"{BASE_URL}/companies/{cid}", headers=headers)
            cname = resp.json().get("name", "Unknown")
            print(f"  {cname}: Total {stats['total_count']}, Won {stats['won_count']}, Revenue ${stats['won_revenue']:,.2f}")

    # LEADS ANALYSIS
    print("\nAnalyzing Leads for Quality and Sources...")
    leads = await fetch_all("leads/search")
    
    bad_email_count = 0
    no_name_count = 0
    lead_sources = {}
    
    for l in leads:
        # Email Check
        emails = l.get("email")
        has_bad_email_cf = False
        if comm_status_cf:
            cf_val = next((f for f in l.get("custom_fields", []) if f['custom_field_definition_id'] == comm_status_cf['id']), None)
            if cf_val and cf_val['value'] in bad_email_ids:
                has_bad_email_cf = True
        
        if not emails or has_bad_email_cf:
            bad_email_count += 1
            
        # Name Check
        name = l.get("name")
        if not name or name in ["", "--", "Unknown"]:
            no_name_count += 1
            
        # Source
        sid = l.get("customer_source_id")
        lead_sources[sid] = lead_sources.get(sid, 0) + 1

    print(f"\n[3.6] Lead Quality - Bad/No Email: {bad_email_count} ({bad_email_count/len(leads)*100:.1f}%)")
    print(f"[3.7] Lead Quality - No Name: {no_name_count} ({no_name_count/len(leads)*100:.1f}%)")
    
    print("\n[3.8] Top Lead Sources:")
    sorted_sources = sorted(lead_sources.items(), key=lambda x: x[1], reverse=True)
    for sid, count in sorted_sources[:5]:
        name = source_map.get(sid, "Unknown")
        print(f"  {name}: {count} ({count/len(leads)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
