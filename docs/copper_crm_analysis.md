# [ARCHIVED] Copper CRM Analysis: Step and Repeat LA

**Created:** 2026-04-09
**Modified:** 2026-04-10
**Version:** 2.0
**Archived:** 2026-04-10

**CRM:** Copper (api.copper.com/developer_api/v1)
**Business:** Step and Repeat LA (stepandrepeatla.com)
**Primary User:** codi@stepandrepeatla.com

---

## Archive Note

This document is retained as the original narrative CRM analysis, but it is no longer the active source of truth.

It has been archived because several headline values in this document are stale, most notably the original `19,800` lead count. Use [crm_findings_for_verification.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/crm_findings_for_verification.md) for current verification guidance and [app_architecture.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/app_architecture.md) for the current build direction.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Business](#the-business)
3. [CRM Data Overview](#crm-data-overview)
4. [Pipeline & Opportunity Analysis](#pipeline--opportunity-analysis)
5. [Lead Database Analysis](#lead-database-analysis)
6. [People & Company Analysis](#people--company-analysis)
7. [Product Performance](#product-performance)
8. [Sales Rep Performance](#sales-rep-performance)
9. [Loss Analysis](#loss-analysis)
10. [Repeat Customer Analysis](#repeat-customer-analysis)
11. [Data Quality Assessment](#data-quality-assessment)
12. [AI Opportunity Recommendations](#ai-opportunity-recommendations)
13. [Technical Appendix: API Methodology](#technical-appendix-api-methodology)

---

## Executive Summary

Step and Repeat LA has a Copper CRM instance containing **38,229 contacts, 17,237 companies, 19,800 leads, and 2,077 opportunities** worth over $2.5M in total pipeline value. The business has won 1,084 deals totaling $1.18M.

**The core finding:** Copper is functioning as an intake archive and closed-order ledger, not as an active sales pipeline. There are **zero open opportunities** in the system. The lead database is massive but largely unworked — all 19,800 leads remain in "New" status with significant data quality issues (81% have bad/no email, 74% have no name). Meanwhile, won deal data is relatively well-maintained, and repeat customers represent the single largest revenue source.

This creates a clear AI opportunity: the gap between raw intake and closed deals is where automation can have massive impact — specifically in lead triage, enrichment, auto-qualification, and quote generation.

---

## The Business

Step and Repeat LA is a Los Angeles-based manufacturer and retailer of custom backdrops, displays, and event equipment. They serve the event industry with:

**Core Products:**
- Step and repeat backdrops (red carpet style)
- Fabric stretch displays (FSDs)
- Media walls
- Hedge walls and hedge products
- Pool floats (custom branded)
- Retractable banners
- Stands, carpet, and stanchions

**Services:**
- Custom design and fabrication
- Rentals (equipment for events)
- Installation and delivery (LA area)
- Rush orders
- Nationwide shipping

**Target Customers:**
- Event planners and production companies
- Hollywood/entertainment industry
- Corporate clients needing branded displays
- Wedding planners and venues
- Nonprofits and charities
- Schools and universities

**Key Business Characteristics:**
- Event-driven demand with hard deadlines
- Mix of one-time buyers and high-value repeat accounts
- Seasonal cycles (award season, holiday parties, corporate event Q4 rush)
- Custom orders alongside standard catalog products
- Rush orders are common and command premium pricing

**Team (Copper Users):**
| Name | Email | Role |
|------|-------|------|
| Codi-Rose Filios | codi@stepandrepeatla.com | Primary user |
| Marie | marie@stepandrepeatla.com | |
| Marie C | events@stepandrepeatla.com | Events |
| Manon | manon@stepandrepeatla.com | Sales |
| Yesenia | yesenia@stepandrepeatla.com | Sales |
| Fredy | fredy@stepandrepeatla.com | Sales |
| Emiliano | emiliano@stepandrepeatla.com | |
| Step and Repeat LA | services@stepandrepeatla.com | General inbox |

---

## CRM Data Overview

### Database Totals

| Entity | Count |
|--------|-------|
| People (Contacts) | 38,229 |
| Companies | 17,237 |
| Leads | 19,800 |
| Opportunities | 2,077 |
| Projects | 31 |
| Tasks | 200+ |

### Contact Type Breakdown (People)

| Type | Count | % |
|------|-------|---|
| Potential Customer | 21,696 | 56.7% |
| Uncategorized | 9,534 | 24.9% |
| Current Customer | 6,649 | 17.4% |
| Top Customer | 313 | 0.8% |
| Cold Customer | 23 | 0.1% |
| Vendor/Resource | 14 | <0.1% |

### How People Came In (Contact Channels)

| Channel | Count |
|---------|-------|
| Emailed | 10,106 |
| Web Form | 2,159 |
| Live Chat | 1,979 |
| Catch That Lead | 1,903 |
| Other | 1,616 |
| Web Order | 1,030 |
| Called | 562 |

### Year Ordered (Tagged on People)

| Year | Count |
|------|-------|
| 2023 | 39 |
| 2024 | 652 |
| 2025 | 345 |
| 2026 | 219 |

*Note: Only 1,255 of 6,649 Current Customers have a Year Ordered tag — significant under-tagging.*

---

## Pipeline & Opportunity Analysis

### Pipeline Architecture

The Copper instance has **three pipelines**:

**1. Sales Board (ID: 623012)** — Primary revenue pipeline
| Stage | Win Probability |
|-------|----------------|
| Initial Contact | 10% |
| Quote Sent | 20% |
| Finalizing Details | 70% |
| Payment Needed | 90% |

**2. Business Development (ID: 623013)** — Partnership/B2B pipeline
| Stage | Win Probability |
|-------|----------------|
| First Meeting | 10% |
| Partner Meeting | 25% |
| Negotiation | 50% |
| Term Sheet | 75% |

**3. Projects (ID: 1113335)** — Production/fulfillment tracking
| Stage | Win Probability |
|-------|----------------|
| To Be Designed | - |
| Final Approval | - |
| To Print | - |
| To Fabricate | - |
| Assembly | - |
| Shipping | - |
| Pick up | - |
| Install/Delivery | - |

### Opportunity Status Breakdown

| Status | Count | Total Value | Avg Deal |
|--------|-------|-------------|----------|
| **Won** | 1,084 | $1,177,866 | $1,089 |
| **Lost** | 585 | $802,561 | $1,374 |
| **Abandoned** | 408 | $540,442 | $1,326 |
| **Open** | **0** | $0 | - |
| **Total** | **2,077** | **$2,520,869** | |

**Critical finding:** There are zero open opportunities. The pipeline is being used purely as a historical record, not as an active sales management tool.

### Won Deal Statistics

| Metric | Value |
|--------|-------|
| Total won deals | 1,084 |
| Total won revenue | $1,177,866 |
| Average deal size | $1,089 |
| Median deal size | $691 |
| Minimum | $23 |
| Maximum | $27,006 |

### Won Deal Value Distribution

| Range | Deals | Revenue |
|-------|-------|---------|
| $0 - $100 | 49 | $3,549 |
| $100 - $250 | 139 | $23,041 |
| $250 - $500 | 210 | $80,002 |
| $500 - $1,000 | 317 | $230,850 |
| $1,000 - $2,500 | 290 | $438,232 |
| $2,500 - $5,000 | 54 | $180,550 |
| $5,000 - $10,000 | 16 | $104,707 |
| $10,000+ | 7 | $116,935 |

The sweet spot is **$250 - $2,500** (817 deals, 75% of all wins, $749K revenue). But the $5,000+ segment (23 deals) accounts for $221K — high-value deals worth pursuing deliberately.

### Funnel Conversion by Stage (Won vs Lost only)

| Stage | Won | Lost | Win Rate |
|-------|-----|------|----------|
| Initial Contact | 155 | 299 | **34%** |
| Quote Sent | 159 | 130 | **55%** |
| Finalizing Details | 139 | 85 | **62%** |
| Payment Needed | 631 | 71 | **90%** |

**The biggest leak is at Initial Contact** — only 34% of deals that sit at this stage end up won. The jump to 55% at Quote Sent shows that getting a quote out fast is the single most important conversion lever.

### Deals by Year Created

| Year | Total | Won | Win Rate | Revenue |
|------|-------|-----|----------|---------|
| 2019 | 1,282 | 664 | 52% | $663,481 |
| 2020 | 770 | 402 | 52% | $455,713 |
| 2021 | 9 | 2 | 22% | $1,776 |
| 2023 | 1 | 1 | 100% | $20,000 |
| 2025 | 3 | 3 | 100% | $7,080 |
| 2026 | 12 | 12 | 100% | $29,816 |

The massive drop after 2020 suggests the team stopped creating opportunities in Copper for a period and is only recently starting to use it again (2025-2026 deals are all won, suggesting they're being recorded after the fact).

### Recent Won Deals (2025-2026)

| Date | Value | Name | Rep |
|------|-------|------|-----|
| 2026-02-09 | $16,353 | Montecito Village Travel & Your Travel Center | Yesenia |
| 2026-02-09 | $2,766 | FERZAN&SONS, LLC. | - |
| 2026-02-09 | $381 | Amelia G. | Manon |
| 2026-02-06 | $3,683 | PMC | Manon |
| 2026-02-06 | $1,867 | Kristina Rodgers | - |
| 2026-02-06 | $1,537 | Damian C. King | - |
| 2026-02-06 | $1,329 | Elwood Clothing | - |
| 2026-02-06 | $712 | Otonomus Hotel | Fredy |
| 2026-02-06 | $563 | Kira Sano | - |
| 2026-02-06 | $439 | Westbrooks Management | Manon |
| 2026-01-30 | $93 | Samantha Jackson Web Order | Yesenia |
| 2026-01-30 | $93 | Kristyn Harris | Yesenia |
| 2025-11-17 | $5,921 | Warners Bro - Marcus - MW | - |
| 2025-11-17 | $1,008 | Ina - Faraday Future - Stanchions | - |
| 2025-08-18 | $151 | Vane Lazo Banner | - |

---

## Lead Database Analysis

### Summary

| Metric | Value |
|--------|-------|
| Total leads | 19,800 |
| Status: New | 19,800 (100%) |
| Status: Converted | 0 |

**Every single lead is in "New" status.** None have been formally converted to opportunities through the Copper lead conversion workflow.

### Lead Sources

| Source | Count | % |
|--------|-------|---|
| Purchased/Acquired List | 10,476 | 52.9% |
| Mailing/Postcard | 3,569 | 18.0% |
| Tradeshow | 2,435 | 12.3% |
| None/Unspecified | 2,331 | 11.8% |
| Catch That Lead | 504 | 2.5% |
| Internet/Website/Online | 237 | 1.2% |
| Unknown/Other | 121 | 0.6% |
| Google | 119 | 0.6% |
| Referral | 4 | <0.1% |
| Another Website | 2 | <0.1% |
| Chambers/Associations | 2 | <0.1% |

### How Customers Heard About Us (Top 25 — Free Text Field)

| Value | Count |
|-------|-------|
| Postcard Mania List | 3,569 |
| Postcard Mania Event Planners | 1,954 |
| Postcard Mania Purchased Mailing List | 1,752 |
| Debbie's Book/LA411 | 1,540 |
| USA Data Purchased Address List | 1,367 |
| Databridge General Purchased List | 1,052 |
| Wedding MBA 2021 List | 548 |
| Salons Purchased List | 459 |
| Event Planners Purchased List | 417 |
| Photo Booth Acquired List | 415 |
| NAB Tradeshow | 367 |
| Bizbash Database | 333 |
| Charity Purchased List | 248 |
| Nightclub Purchased List | 227 |
| TSE Booth | 202 |
| PostcardMania List | 177 |
| Wedding MBA Booth | 149 |
| Progress Bay List - Education | 139 |
| Acquired List - info on web directory | 139 |
| Wedding MBA | 119 |
| Marie's Event People List | 119 |
| Photo Booth List Acquired Via Elance | 118 |
| Largest Mixer Booth | 114 |
| Wedding Bridal Tradeshow | 111 |
| services@stepandrepeat EMAIL | 101 |

The lead database is predominantly purchased/acquired lists and tradeshow attendee lists, not organic inbound leads.

### Lead Communication Status (Data Quality)

| Status | Count | % of All Leads |
|--------|-------|----------------|
| Good Mailing Address | 17,520 | 88.5% |
| Bad Email / No Email | 16,091 | **81.3%** |
| No Name | 14,721 | **74.3%** |
| No Mailing Address | 1,957 | 9.9% |
| Return to Sender | 292 | 1.5% |
| Do not mail | 73 | 0.4% |
| Do not call | 62 | 0.3% |
| Out of Country | 58 | 0.3% |
| No longer with company | 50 | 0.3% |
| Contact Rarely | 10 | 0.1% |

*Note: A single lead can have multiple communication statuses. The data shows that while most leads have good mailing addresses, the vast majority lack usable email or even a name — reflecting the purchased-list origin of most leads.*

### Additional Lead Quality Issues (from Codex Analysis)

- 177 leads use the placeholder name `'--'`
- Duplicate leads exist by exact email address
- 494 of the 600 most recent leads were created in March 2025, suggesting bulk import rather than organic flow
- The newest lead observed was created November 10, 2025
- Products field empty on ~97% of leads
- "How did this come in?" empty on ~90% of leads
- "New/Repeat" empty on 100% of leads
- No monetary value on any leads

---

## People & Company Analysis

### People Database: 38,229 Total

The people database is significantly larger than the leads database and includes both customer contacts and non-customer entries (UPS, QuickBooks, Mail Subsystem bounce addresses — data hygiene issue).

Notable patterns in recent contacts:
- Many new contacts being created in 2026 with assignee changes (active sales motion)
- "How did customer hear about us?" field often set to "Unkown" (typo) or "Auto-Zapped" (indicating automated entry from Zapier or similar)
- "Repeat" appearing as a value in the "How did customer hear about us?" field on some Current Customers

### Company Database: 17,237 Total

Large database but analysis of company-level data was limited. Cross-referencing with opportunities showed 1,238 unique companies with at least one deal.

---

## Product Performance

### Products Custom Field (MultiSelect, ID: 339317)

| Product | Total Deals | Won | Lost | Win Rate | Won Revenue | Avg Won Deal |
|---------|-------------|-----|------|----------|-------------|--------------|
| Step and Repeats | 755 | 383 | 213 | **64%** | $379,617 | $991 |
| Fabric Stretch Displays | 360 | 191 | 86 | **69%** | $260,182 | $1,362 |
| Stands and Carpet | 352 | 211 | 83 | **72%** | $181,422 | $860 |
| Hedge Products | 217 | 51 | 102 | **33%** | $83,540 | $1,637 |
| General/Other | 164 | 125 | 24 | **84%** | $104,425 | $836 |
| Rentals | 158 | 105 | 30 | **78%** | $71,861 | $684 |
| Pool Floats | 149 | 34 | 74 | **31%** | $38,157 | $1,122 |
| Media Walls | 96 | 47 | 25 | **65%** | $133,504 | **$2,840** |
| Retractables | 59 | 40 | 4 | **91%** | $40,399 | $1,010 |

### Key Product Insights

**Best performers:**
- **Retractables** (91% win rate) — Almost automatic sales. Consider promoting more aggressively.
- **General/Other** (84% win rate) — Catch-all category; high conversion.
- **Rentals** (78% win rate) — Reliable, recurring revenue stream.

**Highest value:**
- **Media Walls** ($2,840 avg won deal) — 3x the average deal. The premium product line.
- **Hedge Products** ($1,637 avg) — High value but losing 2/3 of deals.
- **Fabric Stretch Displays** ($1,362 avg) — Strong volume AND value.

**Problem products:**
- **Pool Floats** (31% win rate) — Losing 2 out of 3 deals. Worth investigating why.
- **Hedge Products** (33% win rate) — Same pattern. Are these priced too high? Too much competition? Wrong audience?

**Upsell opportunity:**
- **Media Walls** are the highest-value product at $2,840 avg but only 96 total deals. Step-and-repeat buyers ($991 avg) could be upsold to media walls for appropriate events.
- **Stands and Carpet** are natural add-ons to step-and-repeats and hedge walls.

---

## Sales Rep Performance

### Sales Rep Custom Field (MultiSelect, ID: 698990)

| Rep | Total Deals | Won | Win Rate | Won Revenue |
|-----|-------------|-----|----------|-------------|
| Yesenia | 3 | 3 | 100% | $16,539 |
| Manon | 3 | 3 | 100% | $4,503 |
| Fredy | 1 | 1 | 100% | $712 |
| Codi | 0 | 0 | - | $0 |
| Keila | 0 | 0 | - | $0 |
| Nakia | 0 | 0 | - | $0 |

*Note: The Sales Rep field was only recently added (based on the low fill rate) and is only populated on recent 2025-2026 deals. The vast majority of historical deals (2,070 out of 2,077) have no rep assigned. This field is not useful for historical analysis but will become valuable going forward.*

---

## Loss Analysis

### 585 Lost Deals — $802,561 in Lost Value

Average lost deal ($1,374) is **26% higher** than average won deal ($1,089). The business is disproportionately losing larger deals.

### Loss Reasons

| Reason | Count | % |
|--------|-------|---|
| **Not specified** | 318 | **54%** |
| Price | 107 | 18% |
| Event Cancelled | 44 | 8% |
| Other | 34 | 6% |
| Not enough time | 31 | 5% |
| Competitor | 28 | 5% |
| Couldn't find what they were looking for | 23 | 4% |

### Loss Analysis Insights

1. **54% of losses have no reason recorded** — This is a major process gap. Without loss reasons, it's impossible to systematically improve.

2. **Price is the #1 stated reason** (107 deals) — But 18% isn't devastating. It suggests pricing is competitive for most, but there's a segment being priced out.

3. **"Not enough time" (31 deals)** — These are the most tragic losses: the customer WANTED to buy but the timeline didn't work. Faster quoting and response could recover some of these.

4. **"Event Cancelled" (44 deals)** — External factor, not addressable by sales process. But these contacts should be flagged for follow-up on future events.

5. **"Competitor" (28 deals)** — Relatively low. The business isn't losing heavily to competitors on product — they're losing on process (speed, price response, follow-up).

---

## Repeat Customer Analysis

### Company-Level Repeat Purchase Patterns

| Metric | Value |
|--------|-------|
| Companies with at least 1 deal | 1,238 |
| Companies with 2+ deals | 245 (20%) |
| Companies with 3+ deals | 79 (6%) |
| Companies with 5+ deals | 27 (2%) |

### Top 10 Repeat Buyers

| Company | Total Deals | Won | Won Revenue |
|---------|-------------|-----|-------------|
| SO Events | 19 | 12 | $30,637 |
| The Vibe Agency | 14 | 13 | $50,584 |
| Sequoia Productions | 12 | 7 | $25,348 |
| Continental Color Craft | 11 | 9 | $3,680 |
| Revolucion Marketing | 8 | 5 | $10,293 |
| EMPIRE | 7 | 6 | $8,621 |
| Cardone Training Technologies | 7 | 6 | $13,790 |
| CBS | 7 | 6 | $5,737 |
| The Special Event Company | 6 | 3 | $3,326 |
| Alpinestars | 6 | 6 | $8,576 |

### Repeat Customer Insights

- **The Vibe Agency** is the most valuable repeat customer: 14 deals, 13 won, $50,584 in revenue.
- "Repeat" is the #1 customer source on won deals (128 of the last 400 won deals per Codex analysis).
- Despite this, the **New/Repeat custom field is empty on virtually every record** — the team isn't systematically tracking repeat business.
- 392 deals (19%) have no company associated, meaning repeat purchase patterns can't be identified for those customers.

---

## Data Quality Assessment

### What's Working

| Area | Status |
|------|--------|
| Pipeline structure | Well-designed stages that match the business |
| Custom field design | Thoughtful fields (Products, Event Date, How did they hear, Sales Rep, New/Repeat) |
| Won deal data | Products filled on ~88% of recent wins; Event Date on ~63% |
| Monetary values | Present on most opportunities |
| Activity types | Rich custom types (Phone Call, Meeting, Text Message, Form Letter, Gift Card, Love Letter, Thank You Card) |

### What's Broken

| Issue | Impact | Scale |
|-------|--------|-------|
| All 19,800 leads stuck in "New" | No lead conversion workflow | 100% of leads |
| Zero open opportunities | No active pipeline management | Total |
| 81% of leads have bad/no email | Can't email the lead database | 16,091 leads |
| 74% of leads have no name | Can't personalize outreach | 14,721 leads |
| 177 leads named `'--'` | Junk placeholder data | 177 leads |
| Duplicate leads by email | Inflated counts, confused outreach | Unknown extent |
| New/Repeat field unused | Can't track repeat revenue | ~100% empty |
| Sales Rep field barely used | Can't analyze rep performance historically | <1% filled |
| Loss reason not recorded | Can't learn from losses | 54% of lost deals |
| Source attribution missing on leads | Can't measure marketing ROI | 12% have no source |
| 19% of deals have no company | Can't track account-level patterns | 392 deals |
| Projects/Tasks appear legacy | Stale data from 2019-2021 | 31 projects, all open since 2020 |
| Non-customer contacts in People | UPS, QuickBooks, Mail Subsystem mixed in | Unknown count |

---

## AI Opportunity Recommendations

### Tier 1: Highest Impact, Build First

#### 1. Inquiry-to-Quote-Draft Workflow (Recommended First Build)

**The Problem:** The biggest funnel leak is at Initial Contact (34% win rate). Deals that get a quote sent win at 55%. The #1 controllable loss reason is speed — "not enough time" kills deals, and slow quoting loses to competitors.

**The Solution:** An AI agent that takes an incoming inquiry (email, web form, chat) and:
1. Parses it into structured fields (customer name, company, event date, product type, size, quantity)
2. Classifies the product category (Step and Repeat, FSD, Media Wall, etc.)
3. Infers the intake channel (Emailed, Web Form, Live Chat, Called)
4. Checks for existing customer/company in Copper (repeat buyer detection)
5. Estimates a quote range based on historical won deals for similar products
6. Generates a quote draft with product recommendations and add-on suggestions
7. Creates or updates the Lead/Person/Company and creates an open Opportunity in Copper

**Why First:** This directly addresses the zero-open-pipeline problem and the Initial Contact conversion leak. It also builds the foundation (Copper API write operations, LLM integration) that every subsequent workflow needs.

**Data Available:** 1,082 won deals with monetary values and product classifications provide strong training data for quote estimation.

#### 2. Lead Enrichment, Scoring & Triage

**The Problem:** 19,800 leads sitting in "New" with terrible data quality. But ~5,000+ have names and company info that could be enriched.

**The Solution:** An AI agent that:
1. Scores all 19,800 leads on data completeness (has email? has name? has company? has phone?)
2. For viable leads: enriches with web search (is the company still active? are they in events?)
3. Classifies by industry fit (event planner, venue, production company, corporate, wedding = high fit)
4. Detects and flags duplicates by email/name/company
5. Recommends: Pursue (with personalized draft), Archive (junk/unworkable), or Enrich (needs more data)
6. Generates personalized outreach for the "Pursue" tier

**Estimated impact:** Even 2% conversion on 5,000 viable leads at $1,089 avg deal = ~$109K new pipeline.

#### 3. Repeat Customer Reactivation Engine

**The Problem:** Repeat is the #1 source on won deals, but there's no system to proactively re-engage past buyers. 245 companies have bought 2+ times — many likely have annual events.

**The Solution:** An AI agent that:
1. Identifies all companies/people with past won opportunities
2. Analyzes purchase timing (do they buy annually? seasonally? around specific events?)
3. Cross-references with event dates to predict when they'll need product again
4. Generates personalized re-engagement outreach: "Last year you ordered a 10x8 step and repeat for your holiday gala — should we start planning this year's?"
5. Flags when a known repeat customer appears as a new lead or starts a new opportunity

**Estimated impact:** If 10% of the 245 repeat companies can be reactivated with a $1,500 avg deal = ~$37K.

### Tier 2: Strong ROI, Build After Foundation

#### 4. Loss Pattern Analyzer & Win-Back Campaign

**The Problem:** $802K in lost deals, 54% with no recorded reason, and lost deals average 26% higher value than won deals.

**The Solution:**
- Analyze activity history on all 585 lost deals to infer loss reasons where none are recorded
- Identify patterns: which products lose most? which stages? which time-of-year?
- For "Price" losses: generate re-engagement when promotions or package deals are available
- For "Event Cancelled" losses: monitor for future events from the same contacts
- For "Not enough time" losses: flag as process improvement examples

#### 5. Attribution Repair & Marketing Intelligence

**The Problem:** Can't measure marketing ROI when source attribution is missing on most leads and many deals.

**The Solution:**
- Backfill source/channel from raw inquiry context, tags, and "How did customer hear" free text
- Build a source-to-revenue attribution model: which channels actually produce won deals?
- Already known from won deals: Repeat > Unknown > Google > Internet/Website > LiveChat
- Feed insights into marketing budget decisions

#### 6. Daily Pipeline & Sales Briefing

**The Problem:** No one is looking at Copper daily for pipeline management (evidenced by zero open opportunities).

**The Solution:**
- Daily automated briefing (email or Slack) summarizing: new inquiries, deals needing follow-up, stale leads, approaching event dates, overdue tasks
- Weekly summary of win/loss patterns, product trends, rep performance
- Natural language — no need to log into Copper

### Tier 3: Transformative, Build When Foundation is Solid

#### 7. AI Sales Assistant (Conversational CRM Interface)

Natural language interface over Copper: "What opportunities do we have this month?", "Show me all event planners from the Wedding MBA list", "What's the status of the CBS order?"

#### 8. Smart Upsell & Cross-Sell Engine

When a customer orders one product, recommend complementary products based on historical purchase patterns. Media Wall buyers often also need stands/carpet. Step-and-repeat buyers can be upsold to FSDs for larger events.

#### 9. Auto-Quote PDF Generator

Full branded quote/proposal generation based on Copper opportunity data and historical pricing, delivered as a PDF ready to send.

---

## Technical Appendix: API Methodology

### Authentication & Connection

**Base URL:** `https://api.copper.com/developer_api/v1`

**Authentication Method:** API key + user email in custom headers.

```python
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

COPPER_API_KEY = os.getenv("COPPER_API_KEY")
COPPER_BASE_URL = "https://api.copper.com/developer_api/v1"
USER_EMAIL = "codi@stepandrepeatla.com"

headers = {
    "X-PW-AccessToken": COPPER_API_KEY,
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": USER_EMAIL,
    "Content-Type": "application/json",
}
```

The API key is stored in a `.env` file and loaded via `python-dotenv`. All requests require three custom headers: the access token, application identifier, and the user email associated with the Copper account.

### Endpoints Used

#### 1. Metadata & Configuration Endpoints (GET requests)

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/pipelines` | Retrieve all pipeline definitions with stages and win probabilities | GET |
| `/custom_field_definitions` | Get all custom field definitions, data types, and dropdown options | GET |
| `/customer_sources` | List all lead/customer source categories | GET |
| `/loss_reasons` | List all opportunity loss reason categories | GET |
| `/contact_types` | List all contact type categories | GET |
| `/activity_types` | List all activity types (user and system categories) | GET |
| `/users` | List all Copper users in the account | GET |

These GET endpoints require no request body and return the full list of configuration data. They were called first to build lookup maps (ID -> name) used to decode the numeric IDs in entity records.

**Example:**
```python
r = requests.get(f'{COPPER_BASE_URL}/pipelines', headers=headers)
pipelines = r.json()
```

#### 2. Search Endpoints (POST requests with pagination)

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/opportunities/search` | Search and filter all opportunities | POST |
| `/leads/search` | Search and filter all leads | POST |
| `/people/search` | Search and filter all people/contacts | POST |
| `/companies/search` | Search and filter all companies | POST |
| `/projects/search` | Search and filter all projects | POST |
| `/tasks/search` | Search and filter all tasks | POST |
| `/activities/search` | Search and filter all activities | POST |

All search endpoints use POST with a JSON body containing filter criteria, pagination, and sorting parameters.

**Pagination strategy:** The API returns a maximum of 200 records per page. To retrieve complete datasets, we iterated through pages until an empty response was received:

```python
all_opps = []
for page in range(1, 50):
    r = requests.post(
        f'{COPPER_BASE_URL}/opportunities/search',
        headers=headers,
        json={
            'page_size': 200,
            'page_number': page,
            'sort_by': 'date_modified',
            'sort_direction': 'desc'
        }
    )
    data = r.json()
    if not data:
        break
    all_opps.extend(data)
```

**Key pagination parameters:**
- `page_size`: Max 200 records per page
- `page_number`: 1-indexed page number
- `sort_by`: Field to sort on (e.g., `date_modified`, `date_created`, `name`)
- `sort_direction`: `asc` or `desc`

**API limit:** Search endpoints return a maximum of 100,000 records total.

#### 3. Individual Entity Endpoints (GET by ID)

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/companies/{id}` | Fetch a single company by ID | GET |

Used to resolve company names for the top repeat buyers, since opportunity records only contain `company_id` (not the name).

```python
r = requests.get(f'{COPPER_BASE_URL}/companies/{company_id}', headers=headers)
company = r.json()
print(company.get('name'))
```

### Analysis Strategy

#### Phase 1: Schema Discovery
1. Fetched all metadata endpoints to understand the data model
2. Built lookup maps: pipeline stages, custom field definitions (with dropdown options), customer sources, loss reasons, contact types, activity types
3. This was essential because Copper stores most classifications as numeric IDs that need to be resolved

**Key custom fields discovered:**
| ID | Name | Type | Purpose |
|----|------|------|---------|
| 339317 | Products | MultiSelect | Product categories on deals |
| 339673 | How did customer hear about us? | String | Free-text attribution |
| 340085 | Event Date | Date | Event date on opportunities |
| 340960 | How did this come in? | MultiSelect | Intake channel |
| 341521 | Communication Status | MultiSelect | Contact data quality flags |
| 395689 | Event Type | String | Type of event |
| 671742 | Year Ordered | MultiSelect | Year tags on people |
| 698990 | Sales Rep | MultiSelect | Assigned sales rep |
| 730946 | New/Repeat | Dropdown | New vs repeat customer |

#### Phase 2: Complete Data Pull
1. Paginated through all opportunities (2,077 total across 11 pages)
2. Paginated through all leads (19,800 total across 99 pages)
3. Paginated through all people (38,229 total across 192 pages)
4. Paginated through all companies (17,237 total)
5. Fetched all projects (31) and sampled tasks (200)
6. Sampled recent activities (50)

#### Phase 3: Aggregation & Pattern Analysis

**Opportunity analysis pipeline:**
1. Status breakdown (discovered status is a string, not integer — `'Won'`, `'Lost'`, `'Abandoned'`, not `0`, `1`, `2`)
2. Pipeline stage distribution with value aggregation
3. Product extraction from custom field 339317 (MultiSelect — value is an array of option IDs)
4. Cross-tabulation: product x status for win rates
5. Channel extraction from custom field 340960
6. Sales rep extraction from custom field 698990
7. Temporal analysis: deals grouped by year of creation
8. Value distribution bucketing
9. Funnel analysis: win rate at each pipeline stage

**Lead analysis pipeline:**
1. Total count via full pagination
2. Customer source aggregation
3. "How did customer hear" free-text field aggregation (counter on raw values)
4. Communication status extraction from custom field 341521 (reveals data quality)

**Repeat buyer analysis:**
1. Grouped all opportunities by `company_id`
2. Filtered for companies with 2+ deals
3. Sorted by deal count
4. Resolved company names via individual GET requests to `/companies/{id}`
5. Calculated per-company win rate and revenue

**Key technical notes:**
- The `status` field on opportunities is a **string** (`'Won'`, `'Lost'`, `'Abandoned'`, `'Open'`), not an integer. The Copper docs suggest integer status_ids for search filters, but the response body contains the string.
- Custom fields are returned as an array of objects with `custom_field_definition_id` and `value`. For MultiSelect fields, `value` is an array of option IDs. For Dropdown fields, `value` is a single option ID. For String/Date fields, `value` is the raw value.
- Date fields are Unix timestamps (seconds since epoch).
- The Projects pipeline (ID: 1113335) uses the `/projects/search` endpoint, not `/opportunities/search`, despite being defined as a pipeline.
- Activity search revealed mostly system-generated activities (Assignee Changes) in recent data, with user activities (notes, calls) being less frequent.

### Rate Limits & Constraints

- **API rate limits:** Not explicitly documented in our testing, but Copper generally allows generous API usage for developer integrations.
- **Webhook limits:** 600 notifications/minute, 1,800 per 10-minute window, max 100 subscriptions.
- **Search result cap:** 100,000 records maximum per search query.
- **Page size max:** 200 records per page.
- **Recommended approach for large datasets:** Paginate with `page_size: 200` and iterate until empty response. For the leads database (19,800 records), this required 99 API calls.

### Reproducibility

To reproduce this analysis:

1. Ensure `copper.py` exists with valid API credentials in `.env`
2. Install dependencies: `pip install requests python-dotenv`
3. Run metadata discovery first (GET endpoints) to build lookup maps
4. Run search endpoints with full pagination for each entity type
5. Aggregate using Python `collections.Counter` and `defaultdict`
6. Cross-reference custom field values against the lookup maps from step 3

All data was pulled live from the Copper API on April 8, 2026. Results will vary as data changes.

---

## Changelog

| Version | Date       | Description                  |
|---------|------------|------------------------------|
| 2.0     | 2026-04-10 | Archived the document and redirected readers to the current verification and architecture docs |
| 1.0     | 2026-04-09 | Initial creation             |
