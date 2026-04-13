# Lead Scoring & Triage Engine — App Architecture

**Created:** 2026-04-09
**Modified:** 2026-04-12
**Version:** 2.1

**Project:** Step and Repeat LA — AI CRM Applications

---

## Overview

The first product to build is a backend-first lead analysis system for the Copper lead database. It is intended to help an operator review a large backlog of leads, understand which ones are worth attention, and generate usable outreach drafts without automatically taking action in Copper.

This document replaces the earlier SDK-first framing with a narrower v1:

- Bulk cleanup first
- Operator-admin workflow first
- Score and draft first
- Human review before outbound action
- Backend processing before Copper UI

The long-term product can still grow into a Copper embedded app and later into daily operational tooling, but the initial version should be a review and recommendation system.

---

## Current Implementation Checkpoint

As of 2026-04-12, the backend work has reached an early local-script checkpoint.

Implemented now:

- `backend/app/services/normalize.py` fetches Copper leads with the search API, validates them into `LeadSnapshot`, and returns `NormalizedLead` objects
- `backend/app/services/scoring.py` applies a simple deterministic gate before any model call
- the current deterministic gate is intentionally narrow: send a lead to the LLM only if it has basic identity data plus at least one usable contact method
- `backend/app/services/scoring.py` also contains the first `PydanticAI` triage agent using typed `LLMAnalysisResult` output
- the current agent uses `deps_type` plus `RunContext` to inject the normalized lead and deterministic gate summary into dynamic instructions
- the local scoring script can now be run manually to test one or more leads through the fetch -> normalize -> gate -> LLM path

Not implemented yet:

- enrichment tools and external research
- persistence of lead analyses or run history
- orchestration in `pipeline.py`
- FastAPI endpoints
- review queue UI

This means the current project state is best understood as an interactive local triage prototype, not yet a full backend service.

---

## Product Scope

### V1 Goal

Turn a large raw lead database into a reviewable queue of:

- contactable leads
- prioritized recommendations
- explainable scores
- editable outreach drafts

### V1 Success Metrics

- Produce a ranked set of leads that are realistically contactable
- Generate outreach drafts that a human can actually use
- Increase the number of legitimate sales opportunities created from the existing lead backlog

### V1 Non-Goals

- No autonomous outreach
- No automatic Copper write-back without operator approval
- No embedded Copper UI required to prove value
- No real-time webhook flow required in the first implementation

---

## Working Assumptions

- The first real user is the operator/admin building and reviewing the system
- The eventual audience can expand to sales staff and other Copper users
- Human review is required before any outbound use or CRM mutation
- Explainability is a first-class requirement
- The model layer should remain provider-agnostic
- `PydanticAI` is the preferred harness for structured LLM interactions

---

## System Shape

The first system should be a lead analysis engine with a thin API wrapper, not an API-centric application.

```text
Copper API
  -> Copper client
  -> normalization layer
  -> rules engine
  -> optional enrichment adapter
  -> LLM analysis layer
  -> persistence
  -> review queue
  -> FastAPI wrapper
```

The core unit of work is:

1. fetch one lead
2. normalize and clean it
3. run deterministic checks
4. decide whether enrichment is worth doing
5. generate a structured recommendation and draft
6. store the full evidence trail

---

## Core Backend Components

| Component | Responsibility | Why it exists |
|---|---|---|
| `config` | Load env vars, thresholds, feature flags, provider settings | Keep runtime settings in one place |
| `copper_client` | Read leads and supporting Copper data | Separate Copper API details from business logic |
| `models` | Internal typed schemas for lead data and analysis results | Keep the pipeline predictable and testable |
| `normalize` | Clean raw Copper payloads into a stable internal shape | Copper payloads and custom fields should not leak everywhere |
| `scoring` | Deterministic completeness and contactability rules | Cheap, explainable filtering before LLM usage |
| `enrichment` | Optional web lookup adapter for company/context research | Make Tavily or Serper swappable rather than hardcoded |
| `llm_analysis` | Structured recommendation and draft generation | Keep provider-specific prompting behind one interface |
| `storage` | Persist lead snapshots, scores, evidence, and review decisions | Support re-runs, auditing, and learning |
| `pipeline` | Orchestrate the per-lead workflow | Central place for business flow |
| `batch_runner` | Process samples and bulk runs safely | Bulk-first is the main v1 operating mode |
| `api` | FastAPI endpoints over the pipeline | Expose backend services without holding business logic |
| `evaluation` | Compare system outputs to human judgment | Critical for learning and tuning |

---

## External Services

### Copper

Copper is the source of truth for lead data and, later, the target for approved write-back.

### Enrichment Providers

The enrichment layer is optional in v1 and should be introduced only after deterministic scoring is working.

- `Tavily`: an AI-oriented search/research API that returns ranked results and extracted content suitable for downstream reasoning
- `Serper`: a structured Google Search API that returns search results, news, maps, and related SERP data

The architecture should treat both as adapters behind a common interface, for example:

```python
class EnrichmentProvider(Protocol):
    async def enrich_company(self, company_name: str, city: str | None) -> EnrichmentResult:
        ...
```

### LLM Layer

Use `PydanticAI` as the harness for typed outputs and provider flexibility. The application should depend on an internal analysis interface, not directly on a single model vendor.

---

## Recommended Internal Data Models

The first version should define these internal objects before building the API surface:

- `LeadSnapshot`
- `NormalizedLead`
- `RuleScoreResult`
- `EnrichmentResult`
- `LLMAnalysisResult`
- `LeadAnalysisRecord`
- `BatchRun`
- `ReviewDecision`

These objects matter more than the API routes at the start. If they are clean, the rest of the system gets easier.

---

## Per-Lead Processing Flow

### Step 1 — Fetch

Pull the raw lead from Copper, plus any supporting metadata needed to interpret custom fields.

### Step 2 — Normalize

Convert the raw Copper payload into a clean internal representation.

Normalization should handle:

- blank strings
- placeholder names such as `--`
- email presence and status
- phone normalization
- timestamps
- flattened custom field values
- source attribution normalization

### Step 3 — Deterministic Scoring

Run cheap, explainable rules before any enrichment or LLM call.

The first scoring layer should answer:

- Is this lead contactable?
- Does it have enough data to justify enrichment?
- Does it have obvious disqualifiers?
- Why did it receive this score?

Suggested outputs:

- `completeness_score`
- `contactability_score`
- `disqualifiers`
- `eligible_for_enrichment`
- `recommended_rule_action`
- `rule_reasons`

### Step 4 — Optional Enrichment

Only enrich leads that clear the deterministic threshold.

The enrichment step should gather evidence, not final decisions. For example:

- whether the company appears active
- whether the company is event-related
- whether the company looks like a fit for Step and Repeat LA
- supporting snippets or URLs

### Step 5 — LLM Analysis

Pass the normalized lead plus enrichment evidence into a structured LLM call.

The LLM should produce:

- priority / tier recommendation
- industry fit
- short reasoning summary
- outreach draft
- confidence or caution notes

The LLM should not be trusted as the only source of truth for obvious rules such as missing email, missing name, or immediate disqualification.

### Step 6 — Persist

Store:

- raw source snapshot
- normalized fields
- deterministic scoring output
- enrichment evidence
- LLM output
- model metadata
- timestamps
- review state

### Step 7 — Human Review

Show the analysis in a review queue before any write-back or outbound use.

---

## Persistence Model

SQLite is sufficient for v1 and supports the learning workflow well.

The first schema should store more than one flattened score row. It should preserve the evidence trail.

Recommended tables:

| Table | Purpose |
|---|---|
| `batch_runs` | Track sample runs and bulk runs |
| `lead_snapshots` | Store raw Copper payloads captured at processing time |
| `lead_analyses` | Store normalized data, rules output, enrichment, LLM output, and status |
| `review_decisions` | Store operator actions and notes |

Suggested fields for `lead_analyses`:

- `copper_lead_id`
- `batch_run_id`
- `raw_snapshot_id`
- `normalized_json`
- `completeness_score`
- `contactability_score`
- `rule_action`
- `rule_reasons_json`
- `enrichment_json`
- `llm_provider`
- `llm_model`
- `llm_prompt_version`
- `llm_output_json`
- `review_status`
- `processed_at`
- `updated_at`

---

## API Layer

FastAPI should be a thin service wrapper added after the local pipeline works.

Recommended early endpoints:

```text
POST   /runs/sample            # run a small evaluation batch
POST   /runs/bulk              # start a bulk analysis run
GET    /runs/{id}              # run status and counters
POST   /leads/score            # analyze one lead by ID
GET    /leads/{id}/analysis    # fetch the latest stored analysis
POST   /reviews/{id}           # approve, reject, or annotate a result
```

Avoid Copper write-back endpoints in the first implementation unless they are explicitly manual and operator-triggered.

---

## Suggested Folder Layout

```text
backend/
  app/
    api/
    core/
      config.py
      logging.py
    clients/
      copper.py
      enrichment.py
      llm.py
    models/
      lead.py
      analysis.py
      db.py
    services/
      normalize.py
      scoring.py
      pipeline.py
      batch.py
      evaluation.py
    repositories/
      analyses.py
      runs.py
    main.py
  scripts/
    run_sample.py
    run_bulk.py
```

---

## Build Order

### Phase 0 — Evaluation Setup

Before productizing anything, create a small manual evaluation set.

- Pull 50 to 100 leads
- Review them manually
- Decide what "good lead" means for this business
- Define what counts as a usable outreach draft

### Phase 1 — Local Single-Lead Pipeline

Build a local script first, not an API.

- `config`
- `models`
- Copper read client
- normalization
- deterministic scoring
- SQLite persistence
- sample runner script

Checkpoint on 2026-04-12:

- `config`, `models`, normalization, and first-pass deterministic gating are in place
- the local sample runner currently lives in `backend/app/services/scoring.py`
- SQLite persistence is not implemented yet

Milestone:

Given a small batch of Copper leads, the system can produce a stored analysis and a readable explanation for each lead.

### Phase 2 — Batch Processing

Add bulk-friendly run tracking.

- resumable runs
- duplicate avoidance
- progress counters
- failure logging
- review queue generation

### Phase 3 — LLM Layer

Once the deterministic layer is stable:

- add `PydanticAI`
- add structured recommendation output
- add outreach drafting
- store prompt and model metadata

Checkpoint on 2026-04-12:

- `PydanticAI` has been added for local lead triage
- structured `LLMAnalysisResult` output is wired into the current prototype
- prompt structure now combines stable instructions with dependency-driven runtime lead context
- outreach drafting exists in the schema and prompt, but still needs qualitative review and tuning
- prompt/version/model metadata storage is not implemented yet

### Phase 4 — FastAPI Wrapper

Add the API only after the service layer works locally.

### Phase 5 — Review UI

Build a lightweight review app before any Copper embedded UI.

### Phase 6 — Copper UI and Approved Write-Back

Only after the review workflow is stable should the project add:

- Copper embedded app support
- approved write-back to custom fields
- optional opportunity conversion helpers
- real-time webhook processing

---

## Key Design Decisions

### Why backend-first instead of Copper UI first?

The hard problems are data shape, scoring quality, enrichment usefulness, and draft quality. Those should be debugged without also fighting SDK and iframe concerns.

### Why rules before LLM?

Rules are cheap, fast, and explainable. They also create a stable baseline you can compare the LLM against.

### Why avoid full automation in v1?

This project is both a product effort and a learning exercise. Human review keeps the risk low and makes it easier to understand where the system is right or wrong.

### Why not use `pandas` as the primary processing layer?

`pandas` is useful for offline analysis, exploration, and reporting. It is usually the wrong center of gravity for a row-by-row application pipeline. The core processing path should use typed models and normal Python functions.

### Why provider-agnostic LLM architecture?

The business logic should survive model changes. `PydanticAI` is a good fit because it supports structured outputs while keeping the system from depending too directly on one vendor.

---

## Current Notes

- Live CRM verification on 2026-04-09 confirmed `65,650` leads, `2,077` opportunities, and `0` open opportunities
- The earlier framing that all leads were untouched since 2019–2020 is no longer strictly true; at least one lead was modified on 2026-04-09
- The CRM verification document is the current factual reference for counts and verification methods

---

## Changelog

| Version | Date       | Description |
|---------|------------|-------------|
| 2.1     | 2026-04-12 | Added an implementation checkpoint describing the current normalize -> gate -> PydanticAI triage prototype status |
| 2.0     | 2026-04-10 | Reframed the project around a backend-first, operator-reviewed v1 and added a concrete component framework |
| 1.0     | 2026-04-09 | Initial creation |
