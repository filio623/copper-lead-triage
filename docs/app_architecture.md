# Lead Scoring & Triage Engine — App Architecture

**Created:** 2026-04-09
**Modified:** 2026-04-09
**Version:** 1.0

**Project:** Step and Repeat LA — AI CRM Applications

---

## Overview

The Lead Scoring & Triage Engine is the first AI application to build. It addresses the single largest missed opportunity in the Copper CRM: **65,650 leads sitting completely untouched since 2019–2020**, with no system to work them.

The goal is an AI-powered pipeline that:
1. Pulls leads from Copper
2. Scores them on data completeness
3. Enriches viable ones with web research
4. Classifies them by industry fit and priority tier
5. Generates personalized outreach drafts for top prospects
6. Writes results back to Copper

---

## Two Modes

The app needs to support two distinct operating contexts:

| Mode | Description | Trigger |
|---|---|---|
| **Bulk** | Process all 65,650 existing leads as a cleanup job | Manual / scheduled |
| **Real-time** | Score new leads as they come in | Copper webhook |

Build bulk first. Get the logic right, validate output quality, then add real-time.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  COPPER CRM                         │
│  Leads DB ──► Webhooks ──► Embedded App (sidebar)  │
└────────┬──────────────────────────┬─────────────────┘
         │ REST API                 │ Webhook events
         ▼                         ▼
┌─────────────────────────────────────────────────────┐
│               FASTAPI BACKEND                       │
│                                                     │
│  /leads/bulk   ──► Background Job Queue             │
│  /leads/score  ──► Scoring Pipeline                 │
│  /leads/{id}   ──► Result Lookup                    │
│  /leads/action ──► Write back to Copper             │
└────────┬────────────────┬────────────────────────────┘
         │                │
         ▼                ▼
┌──────────────┐  ┌──────────────────────────────────┐
│  DATABASE    │  │        AI PIPELINE               │
│  (SQLite →   │  │                                  │
│  PostgreSQL) │  │  1. Data completeness score       │
│              │  │  2. Web enrichment (Tavily/Serper)│
│  - lead_id   │  │  3. LLM classification (Claude)  │
│  - score     │  │  4. Outreach draft generation    │
│  - tier      │  └──────────────────────────────────┘
│  - reasoning │
│  - enrichment│
│  - action    │
└──────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Frontend** | React + Copper Embedded App SDK | Sidebar panel inside Copper UI |
| **Backend** | Python + FastAPI | REST API, async support |
| **AI / LLM** | Anthropic Claude API | Structured JSON output via tool use |
| **Web Enrichment** | Tavily API or Serper API | Company research & validation |
| **Database** | SQLite (dev) → PostgreSQL (prod) | Store scores, avoid re-processing |
| **Background Jobs** | asyncio tasks (dev) → Celery + Redis (prod) | Bulk processing queue |
| **Copper Integration** | Copper REST API v1 | Read leads, write scores back |

---

## Backend: FastAPI Endpoints

```
POST   /leads/bulk              # Kick off bulk processing job
GET    /leads/bulk/status       # Check job progress
POST   /leads/score             # Score a single lead (by ID or object)
GET    /leads/{id}/result       # Get stored result for a lead
POST   /leads/{id}/action       # Apply action back to Copper
GET    /leads/queue             # View pending/processed queue
```

---

## The AI Pipeline (Per Lead)

Each lead goes through this pipeline in sequence:

### Step 1 — Pull Lead from Copper
```python
GET /leads/{id}
```
Fields we care about: name, company, email, phone, `date_created`, `customer_source_id`, custom fields (communication_status, how_did_this_come_in, products, new_repeat)

### Step 2 — Data Completeness Score (Rules-Based, No AI)
Fast, cheap pre-filter before any LLM calls.

| Field Present | Points |
|---|---|
| Has email (and not flagged bad) | +2 |
| Has name (not '--' or blank) | +2 |
| Has company name | +2 |
| Has phone | +1 |
| Has source attribution | +1 |

**Score 0–2 → Archive immediately.** No point enriching leads with no data.
**Score 3–4 → Enrich and classify.**
**Score 5–8 → High priority, fast-track to LLM.**

### Step 3 — Web Enrichment (For Score 3+ Leads)
Use Tavily or Serper to research the company name.

Questions to answer:
- Is this company still active?
- What industry are they in?
- Do they do events? (production company, venue, event planner, corporate, wedding)
- Company size / type?

```python
search_query = f"{lead.company} {lead.city} events"
results = tavily.search(search_query, max_results=3)
```

### Step 4 — LLM Classification (Claude)
Pass the lead data + enrichment results to Claude with a structured output prompt.

**Input to LLM:**
```
Lead name: {name}
Company: {company}
Email: {email} (status: {email_status})
Source: {source}
Enrichment: {web_research_summary}
Historical context: Step and Repeat LA sells event backdrops, displays,
and rentals. Best customers are event planners, production companies,
corporate event teams, wedding planners, venues, and entertainment industry.
```

**Expected JSON output (via tool use):**
```json
{
  "score": 72,
  "tier": "pursue",
  "industry_fit": "high",
  "reasoning": "Active event production company in LA area. High likelihood of needing branded displays.",
  "suggested_action": "pursue",
  "outreach_draft": "Hi [Name], I noticed [Company] does..."
}
```

Use Claude's tool use / structured output to guarantee valid JSON every time.

### Step 5 — Store Result
Write to local database. Never re-process a lead that already has a result unless forced.

### Step 6 — Write Back to Copper (Optional / On Approval)
Update custom fields on the lead in Copper:
- Score (numeric custom field)
- Tier (dropdown: Pursue / Enrich / Archive)
- AI reasoning (text field)

Or convert top-tier leads directly to Opportunities.

---

## Frontend: Copper Embedded App

Copper's SDK lets you build a sidebar panel that renders inside the Copper UI when viewing a Lead record. The panel gets the current lead's ID via a JS bridge.

**What the sidebar shows:**
- AI Score (0–100 with color coding)
- Tier badge (Pursue / Enrich / Archive)
- Industry fit rating
- AI reasoning summary
- Outreach draft (editable, copy-to-clipboard)
- Action buttons: Approve & Convert | Archive | Re-score

**Tech:** React app embedded as an iframe. Communicates with your FastAPI backend. Auth via API key in headers.

---

## Database Schema

```sql
CREATE TABLE lead_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    copper_lead_id  TEXT UNIQUE NOT NULL,
    completeness    INTEGER,
    ai_score        INTEGER,
    tier            TEXT,         -- 'pursue' | 'enrich' | 'archive'
    industry_fit    TEXT,         -- 'high' | 'medium' | 'low'
    reasoning       TEXT,
    outreach_draft  TEXT,
    enrichment_data JSON,
    action_taken    TEXT,         -- 'converted' | 'archived' | 'pending'
    processed_at    DATETIME,
    updated_at      DATETIME
);
```

---

## Recommended Build Order

### Phase 1 — Backend Pipeline (Week 1)
Build and validate the core scoring logic as a standalone Python script first. No API, no frontend. Just run it against a sample of 50–100 leads and check the output quality manually.

- [ ] Copper lead fetch function
- [ ] Data completeness scorer
- [ ] Tavily/Serper enrichment call
- [ ] Claude structured output prompt
- [ ] SQLite storage
- [ ] Batch runner script

### Phase 2 — FastAPI Wrapper (Week 2)
Wrap the pipeline in FastAPI endpoints. Add background job support for bulk processing.

- [ ] `POST /leads/score` endpoint
- [ ] `POST /leads/bulk` with async background task
- [ ] `GET /leads/{id}/result`
- [ ] `POST /leads/{id}/action` → write back to Copper

### Phase 3 — Copper Embedded App (Week 3)
Build the React sidebar. Hook it up to the FastAPI backend.

- [ ] Copper SDK setup and embedding
- [ ] Score display component
- [ ] Outreach draft display + copy button
- [ ] Action buttons (approve, archive, re-score)

### Phase 4 — Bulk Run & Review UI (Week 4)
Build a simple dashboard to monitor the bulk job and review AI recommendations before applying them.

- [ ] Progress view (X of 65,650 processed)
- [ ] Review queue (top pursue leads)
- [ ] Bulk approve / bulk archive actions

---

## Key Design Decisions

**Why start with rules-based scoring before the LLM?**
LLM calls cost money and take time. Filtering out zero-data leads with a simple completeness check first means you only spend AI budget on leads worth evaluating. Estimated 30–40% of leads (those with score 0–2) can be archived without any LLM call.

**Why SQLite first?**
Faster to get started. You can always migrate to PostgreSQL later. For a 65,650 lead database with simple queries, SQLite is more than sufficient.

**Why build backend before the Copper frontend?**
You'll debug the scoring logic, the enrichment calls, and the prompt quality while running a simple script. Adding the SDK and iframe layer before the core logic works means you're fighting two unknowns at once.

**Why Claude for the LLM?**
Tool use / structured output makes it easy to get reliable JSON back. The industry classification and outreach drafting tasks are well within Claude's strengths. Use `claude-haiku-4-5` for speed and cost on bulk processing; `claude-sonnet-4-6` for quality on high-priority leads.

---

## Estimated Revenue Impact (Revised)

Based on corrected lead count of 65,650:

| Assumption | Value |
|---|---|
| Leads with enough data to enrich (~20%) | ~13,000 |
| Leads classified as high-fit after enrichment (~30%) | ~3,900 |
| Conversion rate (2%) | ~78 new deals |
| Average deal size | $1,089 |
| **Estimated new pipeline** | **~$85,000 – $283,000** |

Conservative to optimistic range depending on data quality and follow-through on outreach.

---

## Changelog

| Version | Date       | Description                  |
|---------|------------|------------------------------|
| 1.0     | 2026-04-09 | Initial creation             |
