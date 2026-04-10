# Copper CRM Findings — Verification Document
**Business:** Step and Repeat LA (stepandrepeatla.com)
**CRM:** Copper (api.copper.com/developer_api/v1)
**Auth user:** codi@stepandrepeatla.com
**Original analysis date:** April 8–9, 2026

This document lists every factual claim made in the CRM assessment PDF, the expected value, and the exact Copper API call an agent should make to verify it. All endpoints use POST with JSON body unless noted.

---

## HOW TO AUTHENTICATE

All requests require these three headers:
```
X-PW-AccessToken: <COPPER_API_KEY>
X-PW-Application: developer_api
X-PW-UserEmail: codi@stepandrepeatla.com
Content-Type: application/json
```

---

## SECTION 1 — DATABASE TOTALS

### 1.1 Total People (Contacts)
- **Claimed value:** 38,229
- **Endpoint:** `POST /people/search`
- **Body:** `{"page_size": 1, "page_number": 1}`
- **How to verify:** Paginate through all pages with `page_size: 200`, count total records until empty response. Expected total: 38,229.

### 1.2 Total Companies
- **Claimed value:** 17,237
- **Endpoint:** `POST /companies/search`
- **Body:** `{"page_size": 1, "page_number": 1}`
- **How to verify:** Paginate with `page_size: 200`, count all records. Expected total: 17,237.

### 1.3 Total Leads
- **Claimed value:** 65,650
- **Endpoint:** `POST /leads/search`
- **Body:** `{"page_size": 200, "page_number": 1, "sort_by": "date_modified", "sort_direction": "desc"}`
- **How to verify:** Paginate through all pages (expect ~328 pages × 200 = 65,650). IMPORTANT: send params as JSON body, not URL query params.

### 1.4 Total Opportunities
- **Claimed value:** 2,077
- **Endpoint:** `POST /opportunities/search`
- **Body:** `{"page_size": 200, "page_number": 1}`
- **How to verify:** Paginate and count. Expected total: 2,077.

### 1.5 Won Revenue
- **Claimed value:** $1,177,866
- **Endpoint:** `POST /opportunities/search`
- **Body:** `{"page_size": 200, "page_number": 1}`
- **How to verify:** Pull all opportunities, filter where `status == "Won"`, sum the `monetary_value` field. Expected sum: $1,177,866.

---

## SECTION 2 — PIPELINE & OPPORTUNITY STATUS

### 2.1 Zero Open Opportunities
- **Claimed value:** 0 open opportunities
- **Endpoint:** `POST /opportunities/search`
- **Body:** `{"page_size": 200, "page_number": 1}`
- **How to verify:** Pull all opportunities, filter where `status == "Open"`. Expected count: 0.

### 2.2 Opportunity Status Breakdown
- **Claimed values:**

| Status | Count | Total Value |
|--------|-------|-------------|
| Won | 1,084 | $1,177,866 |
| Lost | 585 | $802,561 |
| Abandoned | 408 | $540,442 |
| Open | 0 | $0 |

- **Endpoint:** `POST /opportunities/search`
- **Body:** `{"page_size": 200, "page_number": 1}`
- **How to verify:** Pull all 2,077 opportunities, group by `status` string field (`"Won"`, `"Lost"`, `"Abandoned"`, `"Open"`), count and sum `monetary_value` per group.
- **Note:** `status` is a string in the response body, not an integer.

### 2.3 Funnel Conversion by Stage (Won vs Lost)
- **Claimed values:**

| Stage Name | Won | Lost | Win Rate |
|------------|-----|------|----------|
| Initial Contact | 155 | 299 | 34% |
| Quote Sent | 159 | 130 | 55% |
| Finalizing Details | 139 | 85 | 62% |
| Payment Needed | 631 | 71 | 90% |

- **Endpoint:** `POST /opportunities/search` + `GET /pipelines`
- **How to verify:**
  1. `GET /pipelines` — find pipeline ID for "Sales Board" (expected ID: 623012), get stage IDs and names.
  2. Pull all opportunities, filter where `status` is `"Won"` or `"Lost"`.
  3. Group by `pipeline_stage_id`, resolve stage names from pipeline lookup.
  4. Count Won and Lost per stage, calculate win rate as `won / (won + lost)`.

### 2.4 Average and Median Deal Size (Won)
- **Claimed values:** Average $1,089 | Median $691 | Min $23 | Max $27,006
- **Endpoint:** `POST /opportunities/search`
- **How to verify:** Pull all won opportunities, extract `monetary_value`, compute mean, median, min, max.

### 2.5 Lost Deal Average vs Won Deal Average
- **Claimed value:** Lost deals average $1,374 — 26% higher than won deals ($1,089)
- **How to verify:** Compute average `monetary_value` for Lost status vs Won status separately.

### 2.6 Loss Reasons Breakdown
- **Claimed values:**

| Reason | Count | % |
|--------|-------|---|
| Not Specified | 318 | 54% |
| Price | 107 | 18% |
| Event Cancelled | 44 | 8% |
| Other | 34 | 6% |
| Not Enough Time | 31 | 5% |
| Competitor | 28 | 5% |
| Couldn't Find Product | 23 | 4% |

- **Endpoint:** `GET /loss_reasons` then `POST /opportunities/search`
- **How to verify:**
  1. `GET /loss_reasons` — build lookup map of loss_reason_id → name.
  2. Pull all lost opportunities, extract `loss_reason_id`, group and count.
  3. `None` or null loss_reason_id = "Not Specified".

---

## SECTION 3 — LEAD DATABASE

### 3.1 Total Leads (confirmed)
- **Claimed value:** 65,650
- **How to verify:** See 1.3 above.

### 3.2 All Leads in "New" Status
- **Claimed value:** 100% of leads are in "New" status, 0 converted
- **Endpoint:** `POST /leads/search`
- **How to verify:** Pull all leads, check `status` field on each record. Expected: every record returns `status: "New"`. No records with any other status value.

### 3.3 Leads Never Contacted
- **Claimed value:** 36,554 leads (56%) have no Date Last Contacted
- **Endpoint:** `POST /leads/search`
- **How to verify:** Pull all leads, count records where `date_last_contacted` is `null` or `None`. Expected: 36,554.

### 3.4 Lead Date Range
- **Claimed values:**
  - Date Created range: July 9, 2019 → November 10, 2025
  - Date Modified range: March 2, 2020 → April 9, 2026
  - Date Last Contacted range: August 8, 2019 → April 9, 2026 (on records that have it)
- **Endpoint:** `POST /leads/search`
- **How to verify:** Pull all leads, find min and max of `date_created`, `date_modified`, and `date_last_contacted` fields. All values are Unix timestamps (seconds since epoch).

### 3.5 Leads Created by Year
- **Claimed values:**

| Year | Leads |
|------|-------|
| 2019 | 34,677 |
| 2020 | 9,517 |
| 2021 | 437 |
| 2022 | 12,890 |
| 2023 | 4,000 |
| 2025 | 4,129 |

- **How to verify:** Pull all leads, convert `date_created` Unix timestamp to year, group and count by year.

### 3.6 Lead Data Quality — Bad/No Email
- **Claimed value:** ~81% of leads have bad or no email (~53,000 leads)
- **How to verify:** Pull all leads, check `email` array field. Count records where email array is empty OR where Communication Status custom field (ID: 341521) includes the "Bad Email" or "No Email" option ID.

### 3.7 Lead Data Quality — No Name
- **Claimed value:** ~74% of leads have no name (~48,600 leads)
- **How to verify:** Pull all leads, count records where `name` field is null, empty, or equals `"--"`.

### 3.8 Top Lead Sources
- **Claimed values:** Purchased/Acquired Lists 53% | Mailing/Postcard 18% | Tradeshow 12%
- **Endpoint:** `GET /customer_sources` then `POST /leads/search`
- **How to verify:**
  1. `GET /customer_sources` — build lookup map of source_id → name.
  2. Pull all leads, extract `customer_source_id`, group and count.
  3. Calculate percentage of total.

---

## SECTION 4 — PRODUCT PERFORMANCE

### 4.1 Product Win Rates
- **Claimed values:**

| Product | Win Rate | Avg Won Deal | Won Revenue |
|---------|----------|--------------|-------------|
| Retractables | 91% | $1,010 | $40,399 |
| Rentals | 78% | $684 | $71,861 |
| Stands & Carpet | 72% | $860 | $181,422 |
| Fabric Stretch Displays | 69% | $1,362 | $260,182 |
| Media Walls | 65% | $2,840 | $133,504 |
| Step and Repeats | 64% | $991 | $379,617 |
| Hedge Products | 33% | $1,637 | $83,540 |
| Pool Floats | 31% | $1,122 | $38,157 |

- **Endpoint:** `GET /custom_field_definitions` then `POST /opportunities/search`
- **How to verify:**
  1. `GET /custom_field_definitions` — find field named "Products" (expected ID: 339317). It is a MultiSelect field. Get the option_id → option_name map from its `options` array.
  2. Pull all opportunities, extract custom field 339317 value (it is an array of option IDs).
  3. For each product option, count Won and Lost opportunities that include that option ID.
  4. Calculate win rate = won / (won + lost), avg won deal = sum(won monetary_value) / count(won).
  5. Note: one opportunity can include multiple product option IDs.

### 4.2 Media Walls Average Deal
- **Claimed value:** $2,840 avg won deal — highest of all products
- **How to verify:** As above, filter won opportunities containing Media Walls option ID, compute average monetary_value.

---

## SECTION 5 — REPEAT CUSTOMERS

### 5.1 Companies with Multiple Deals
- **Claimed values:** 245 companies with 2+ deals | 79 companies with 3+ deals
- **Endpoint:** `POST /opportunities/search` then `GET /companies/{id}`
- **How to verify:**
  1. Pull all opportunities, group by `company_id`.
  2. Count how many company_ids appear 2+ times and 3+ times.
  3. Resolve company names via `GET /companies/{id}` for the top entries.

### 5.2 Top Repeat Buyers
- **Claimed values:**

| Company | Total Deals | Won | Revenue |
|---------|-------------|-----|---------|
| The Vibe Agency | 14 | 13 | $50,584 |
| SO Events | 19 | 12 | $30,637 |
| Sequoia Productions | 12 | 7 | $25,348 |
| Cardone Training Technologies | 7 | 6 | $13,790 |
| Revolucion Marketing | 8 | 5 | $10,293 |
| Alpinestars | 6 | 6 | $8,576 |
| CBS | 7 | 6 | $5,737 |

- **How to verify:** Group opportunities by `company_id`, sort by count descending, resolve top company names via `GET /companies/{id}`, tally Won count and sum Won `monetary_value`.

### 5.3 New/Repeat Field Unused
- **Claimed value:** New/Repeat custom field is empty on virtually every record
- **How to verify:** `GET /custom_field_definitions` — find field named "New/Repeat" (expected ID: 730946). Pull all opportunities, check custom field 730946 value. Expected: null or empty on nearly all records.

---

## SECTION 6 — PIPELINES

### 6.1 Three Pipelines Exist
- **Endpoint:** `GET /pipelines`
- **Claimed values:**
  - Sales Board (ID: 623012) — 4 stages
  - Business Development (ID: 623013) — 4 stages
  - Projects (ID: 1113335) — 8 stages

### 6.2 Sales Board Stage Win Probabilities
| Stage | Win Probability |
|-------|----------------|
| Initial Contact | 10% |
| Quote Sent | 20% |
| Finalizing Details | 70% |
| Payment Needed | 90% |

- **How to verify:** `GET /pipelines`, find Sales Board pipeline, inspect `stages` array for each stage's `win_probability`.

---

## SECTION 7 — REVENUE IMPACT ESTIMATES

These are calculated projections, not raw API values. Verify by confirming the underlying inputs:

| Estimate | Input to Verify | API Source |
|----------|----------------|------------|
| $75K faster quoting | Avg won deal $1,089, 34%→55% funnel lift | Opportunities |
| $283K lead activation | 13,000 viable leads × 2% conv × $1,089 | Leads + Opportunities |
| $37K repeat reactivation | 245 repeat companies × 10% × $1,500 | Opportunities grouped by company |
| $25K loss recovery | 585 lost deals × $802,561 total | Opportunities (Lost) |
| $30K upsell | Step-and-repeat → Media Wall avg delta | Opportunities by product |
| **$450K–$500K total** | Sum of above | — |

---

## PAGINATION NOTES FOR AGENT

- Max `page_size` is 200 per request.
- Paginate by incrementing `page_number` starting at 1.
- Stop when response returns an empty array `[]`.
- All date fields are Unix timestamps (seconds since epoch). Use `datetime.fromtimestamp(ts)` to convert.
- `status` on opportunities is a string: `"Won"`, `"Lost"`, `"Abandoned"`, `"Open"` — not an integer.
- Custom field values are in the `custom_fields` array as objects: `{"custom_field_definition_id": <id>, "value": <value>}`. MultiSelect values are arrays of option IDs.
- Send all search params as JSON body (`json=payload`), not URL query params.

---

## QUICK VERIFICATION CHECKLIST

```
[ ] Total leads = 65,650
[ ] Total contacts = 38,229
[ ] Total companies = 17,237
[ ] Total opportunities = 2,077
[ ] Open opportunities = 0
[ ] Won deals = 1,084 / $1,177,866
[ ] Lost deals = 585 / $802,561
[ ] Abandoned = 408 / $540,442
[ ] All 65,650 leads in "New" status
[ ] 36,554 leads with null date_last_contacted
[ ] Lead date_created range: Jul 2019 – Nov 2025
[ ] 245 companies with 2+ deals
[ ] Media Walls avg won deal = $2,840 (highest product)
[ ] Retractables win rate = 91% (highest win rate)
[ ] New/Repeat field (ID: 730946) empty on nearly all records
[ ] Loss reason missing on 318 of 585 lost deals (54%)
```
