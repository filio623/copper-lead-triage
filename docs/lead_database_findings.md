# Lead Database Findings — Step and Repeat LA (Copper CRM)

**Created:** 2026-04-09
**Modified:** 2026-04-09
**Version:** 1.0

---

## Corrected Lead Count

The original CRM analysis reported **19,800 leads**. A subsequent full paginated pull of the Copper API returned the accurate figure:

**Total Leads: 65,650**

The original script used a hardcoded page cap (`range(1, 100)`) which stopped at 99 pages × 200 records = 19,800. The actual database contains 328 pages of leads at 200 per page.

---

## Date Range of Lead Activity

After fixing the pagination script and sorting by `date_modified` descending, the results showed:

| Field | Unix Timestamp | Human Date |
|---|---|---|
| Most recently modified (first result) | 1583182037 | March 2, 2020 |
| Least recently modified (last result) | 1565129733 | August 7, 2019 |

**Key finding:** Every single one of the 65,650 leads has been completely untouched since March 2020 at the latest. The most recently modified lead is over 5 years old. Because none have been modified since import, `date_modified` is effectively the same as `date_created` — meaning all of these leads were imported in a roughly 7-month window between **August 2019 and March 2020**.

---

## What This Tells Us

### 1. These are all bulk-imported lists
This date range aligns exactly with the lead sources identified in the original analysis — purchased mailing lists, tradeshow attendee lists, and postcard campaign contacts. They were imported as batch uploads in late 2019 through early 2020 and never worked.

### 2. Not a single lead has been touched in 5+ years
`date_modified` = `date_created` across the board. Zero engagement, zero outreach, zero conversion attempts on any of the 65,650 records.

### 3. Data quality is likely worse than originally estimated
The original analysis (on 19,800 leads) found:
- **81%** bad or no email
- **74%** no name on record

Extrapolated to 65,650 leads:
- ~53,000 leads with bad/no email
- ~48,600 leads with no name

### 4. The pipeline between purchased lists and actual outreach never existed
The business invested in list acquisition (Postcard Mania, Debbie's Book/LA411, Databridge, USA Data, etc.) and tradeshow attendance, but no system was ever built to convert that investment into active outreach. The leads sat and aged.

---

## Revised Impact Estimate

With 65,650 total leads instead of 19,800, the opportunity is larger — but the data quality challenge is also larger. A conservative estimate:

- ~20% of leads have enough data to be worth enriching = **~13,000 viable leads**
- 2% conversion on viable leads at $1,089 avg deal = **~$283,000 in potential pipeline**

This is up significantly from the original ~$109K estimate based on 5,000 viable leads from the 19,800 count.

---

## Script Bug Log

The following bugs were identified and corrected in the original pagination script:

**Bug 1 — Started at page 2**
```python
# Wrong
page = 2

# Correct
page = 1
```

**Bug 2 — Sent pagination params as URL query params instead of JSON body**
```python
# Wrong — sends as ?page_size=200&page_number=1 in the URL
response = httpx.post(url, headers=headers, params=params)

# Correct — sends as JSON in the request body
response = httpx.post(url, headers=headers, json=params)
```

---

## Corrected Script

```python
from dotenv import load_dotenv
import os
import httpx
import time
from datetime import datetime

load_dotenv()

COPPER_API = os.getenv("COPPER_API")
EMAIL = "codi@stepandrepeatla.com"

headers = {
    "X-PW-AccessToken": COPPER_API,
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": EMAIL,
    "Content-Type": "application/json",
}

all_count = 0
page = 1  # Start at page 1
first_date = None
last_date = None
start_time = time.time()

while True:
    payload = {
        "page_size": 200,
        "page_number": page,
        "sort_by": "date_modified",
        "sort_direction": "desc"
    }

    response = httpx.post(
        "https://api.copper.com/developer_api/v1/leads/search",
        headers=headers,
        json=payload  # JSON body, not URL params
    )

    leads = response.json()
    count = len(leads)
    all_count += count

    if page == 1 and leads:
        first_date = leads[0].get("date_modified")
    if leads:
        last_date = leads[-1].get("date_modified")

    print(f"Page {page}: {count} leads | Total: {all_count}")

    if count < 200:
        break

    page += 1

elapsed = time.time() - start_time
print(f"\nTotal leads: {all_count}")
if first_date:
    print(f"Most recently modified: {datetime.fromtimestamp(first_date)}")
if last_date:
    print(f"Least recently modified: {datetime.fromtimestamp(last_date)}")
print(f"Execution time: {elapsed:.2f} seconds")
```

---

## Changelog

| Version | Date       | Description                  |
|---------|------------|------------------------------|
| 1.0     | 2026-04-09 | Initial creation             |
