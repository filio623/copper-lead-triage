# Lead Scoring & Triage Engine — App Architecture

**Created:** 2026-04-09
**Modified:** 2026-04-27
**Version:** 2.9

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

As of 2026-04-27, the backend work has moved beyond the original local-script checkpoint and now has the first FastAPI service shell, but the API layer is still incomplete.

Implemented now:

- `backend/app/services/normalize.py` fetches Copper leads with the search API, validates them into `LeadSnapshot`, and returns `NormalizedLead` objects
- `backend/scripts/build_review_sample.py` creates a more representative Phase 0 review sample across the lead backlog
- a first-pass manual review rubric now exists in `docs/phase0_review_rubric.md`
- `backend/app/services/rules.py` now implements the first deterministic scoring layer and returns `RuleScoreResult`
- `backend/app/models/analysis.py` now includes the richer rule score fields needed by the rubric
- `backend/app/models/analysis.py` now includes a first `TriageInput` model for the planned Phase 3 triage task contract
- `tests/test_rules.py` covers the first-pass deterministic scoring contract
- `backend/app/services/scoring.py` still contains the first `PydanticAI` triage prototype using typed `LLMAnalysisResult` output
- `backend/app/services/triage.py` now contains the first reusable Phase 3 triage service boundary with a typed entrypoint and prompt/deps helpers
- `backend/app/clients/llm.py` now contains the thin triage model factory and basic model metadata helper
- `tests/test_triage_contracts.py` now covers triage gating, prompt construction, deps shaping, and service metadata
- `backend/app/models/db.py` now defines the initial SQLAlchemy ORM models, engine/session helpers, typed persistence models, and local database URL handling
- `backend/app/repositories/analyses.py`, `runs.py`, and `reviews.py` now implement the first persistence repositories
- `tests/test_repositories.py` now covers schema creation plus repository round-trips for runs, analyses, and reviews
- `backend/app/services/pipeline.py` now implements the first per-lead orchestration path across validation, normalization, rules, optional triage, and persistence
- `tests/test_pipeline.py` now covers the first end-to-end pipeline contracts for triage skipped, triage used, and raw lead snapshot + analysis persistence
- `backend/app/services/batch.py` now implements the first Phase 6 batch orchestration layer over the per-lead pipeline
- `backend/scripts/run_sample.py` and `backend/scripts/run_bulk.py` now run saved sample and bulk batches through the service layer
- `tests/test_batch.py` now covers duplicate handling, failure handling, and batch run counter updates
- `backend/app/services/review.py` now implements review-row shaping, review-decision recording, and review-history access
- `backend/scripts/review_export.py` now exports saved review rows for a batch run to CSV or JSON
- `tests/test_review.py` now covers review rows, review decisions, review history, and review-status updates
- `backend/app/main.py` now creates the FastAPI app, initializes the database during lifespan startup, stores a request session factory on `app.state`, disposes the engine on shutdown, and includes the review router
- `backend/app/api/deps.py` now provides request-scoped DB sessions, repository constructors, and service dependency construction for API routes
- `backend/app/api/reviews.py` now exposes the first API route, `GET /reviews/runs/{batch_run_id}`

Not implemented yet:

- enrichment tools and external research
- review queue UI
- complete FastAPI route coverage for runs, leads, review decisions, and review history
- API tests
- richer prompt/model metadata capture as the pipeline is tuned

This means the current project state is best understood as a usable backend workflow core plus the first API shell: normalization, rules, triage, persistence, per-lead orchestration, batch execution, review export, and first review API route now exist.

As of 2026-04-27, the recommended next step is to keep FastAPI thin by adding API tests and small route modules over already-working services before adding any new business behavior.

---

## Product Scope

### V1 Goal

Turn a large raw lead database into a reviewable queue of:

- contactable leads
- prioritized recommendations
- explainable scores
- editable outreach drafts

### Primary Job To Be Done

Help an operator work through the existing Copper lead backlog by answering four practical questions for each lead:

- Is this lead a plausible business target?
- Is this lead complete and contactable enough to act on now?
- Does this lead look relevant or timely enough to justify research or outreach?
- What is the recommended next action for a human reviewer?

### V1 Success Metrics

- Produce a ranked set of leads that are realistically contactable
- Generate outreach drafts that a human can actually use
- Increase the number of legitimate sales opportunities created from the existing lead backlog

### V1 Non-Goals

- No autonomous outreach
- No automatic Copper write-back without operator approval
- No embedded Copper UI required to prove value
- No real-time webhook flow required in the first implementation

### Expected Later Capabilities

The architecture should leave room for later additions that are useful but not required for the first working version:

- external research on a company, venue, or event
- suggested contacts when the source record is incomplete
- lead-completion suggestions based on evidence gathered outside Copper
- timeliness signals such as upcoming events, launches, or campaigns
- additional LLM tasks such as draft critique, rewrite, or research summarization

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
  -> LLM task layer
  -> persistence
  -> review queue
  -> FastAPI wrapper
```

The core unit of work is:

1. fetch one lead
2. normalize and clean it
3. run deterministic checks
4. decide whether enrichment is worth doing
5. run one or more LLM tasks as needed
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
| `llm_analysis` | Structured recommendation and later task-specific LLM modules | Keep provider-specific prompting behind one interface |
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

### Agent Strategy

The recommended architecture is:

- one primary per-lead triage agent in v1
- plain Python orchestration around that agent
- deterministic rules outside the agent
- optional enrichment outside the agent
- additional LLM tasks added as separate, narrowly-scoped modules rather than folded into one giant prompt

The first agent should focus on interpreting a normalized lead plus evidence and returning structured output for:

- fit assessment
- priority / tier recommendation
- reasoning summary
- caution notes
- suggested next action
- outreach draft

### Why Not Default To Multi-Agent Or Graphs?

Even if the long-term system becomes more capable, the default recommendation is still not to start with multi-agent orchestration or graph runtimes.

Reasons:

- the hardest problem right now is evaluation quality, not agent coordination
- debugging one pipeline is much easier than debugging multiple interacting agents
- cost and latency stay easier to control
- plain Python keeps the architecture clearer for learning and iteration
- `pydantic_graph` can be revisited later if the workflow becomes meaningfully stateful or branch-heavy

### When To Add More Agents Or Graph-Like Control Flow

The project should only move beyond the single-agent default once there is a concrete need such as:

- a dedicated research task that is materially different from triage
- a separate drafting or draft-critique step that benefits from isolation
- a reviewer or QA step that needs a different prompt contract
- branching workflows with retries, checkpoints, or resumable state transitions

Until those needs are real, treat the system as a modular single-agent pipeline rather than a multi-agent application.

### Designing For Additional LLM Tasks

The codebase should still be designed to support more than one LLM task over time. The clean pattern is:

- one module per task
- one typed input contract per task
- one typed output contract per task
- orchestration in `pipeline.py`, not inside the agent prompts themselves

Examples of later tasks that may be worth adding:

- company or event research summarization
- contact-discovery recommendation
- outreach draft generation
- outreach draft critique and rewrite
- human-note summarization

This means the architecture should be extensible without making multi-agent orchestration the foundation.

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

Pass the normalized lead plus enrichment evidence into one or more structured LLM tasks.

The first triage task should produce:

- priority / tier recommendation
- industry fit
- short reasoning summary
- outreach draft
- confidence or caution notes

The LLM should not be trusted as the only source of truth for obvious rules such as missing email, missing name, or immediate disqualification.

Later tasks may generate additional research summaries, draft revisions, or contact suggestions, but they should remain separate task modules with their own typed outputs.

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

Current API implementation status on 2026-04-27:

- `backend/app/main.py` owns the `FastAPI` instance and app lifespan
- `backend/app/api/deps.py` owns request-scoped sessions and service dependency construction
- `backend/app/api/reviews.py` owns review HTTP routes and currently exposes `GET /reviews/runs/{batch_run_id}`
- route handlers should remain thin adapters over service functions, not new homes for business logic

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
      rules.py
      triage.py
      enrichment.py
      pipeline.py
      batch.py
      evaluation.py
      review.py
    repositories/
      analyses.py
      runs.py
      reviews.py
    main.py
  scripts/
    run_sample.py
    run_bulk.py
    review_export.py
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
- keep the first implementation centered on one per-lead triage agent
- add new LLM tasks as separate modules only when they have a clear job and typed output
- avoid multi-agent orchestration until the workflow clearly needs branching, review, or specialized agent roles

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

### Why not start with multi-agent architecture if the system may grow later?

Because future complexity is not a reason to front-load present complexity. The safer path is to keep the workflow modular enough that additional LLM tasks or agents can be added later without forcing them into the first milestone.

---

## Current Notes

- Live CRM verification on 2026-04-09 confirmed `65,650` leads, `2,077` opportunities, and `0` open opportunities
- The earlier framing that all leads were untouched since 2019–2020 is no longer strictly true; at least one lead was modified on 2026-04-09
- The CRM verification document is the current factual reference for counts and verification methods

---

## Changelog

| Version | Date       | Description |
|---------|------------|-------------|
| 2.9     | 2026-04-27 | Recorded the completed review workflow service/export/tests and the first FastAPI lifespan/dependency/review-route implementation |
| 2.8     | 2026-04-19 | Recorded the first implemented Phase 6 batch services and runner scripts and moved the next milestone to review workflow support |
| 2.7     | 2026-04-18 | Recorded the first implemented per-lead pipeline and set the next milestone as Phase 6 batch processing over the new pipeline |
| 2.6     | 2026-04-15 | Switched the new Phase 4 persistence layer to SQLAlchemy while keeping SQLite as the initial local backing database |
| 2.5     | 2026-04-15 | Recorded the reusable triage service milestone and the first implemented SQLite persistence layer with repository tests |
| 2.4     | 2026-04-14 | Recorded the Phase 3 triage-task start, including the first `TriageInput` model and local triage proof-of-concept status |
| 2.3     | 2026-04-13 | Updated the implementation checkpoint to include representative sampling, the Phase 0 rubric, and the first deterministic `rules.py` layer |
| 2.2     | 2026-04-13 | Clarified the app job-to-be-done, documented the single-agent-first `PydanticAI` strategy, and added guidance for later LLM task expansion without defaulting to multi-agent orchestration |
| 2.1     | 2026-04-12 | Added an implementation checkpoint describing the current normalize -> gate -> PydanticAI triage prototype status |
| 2.0     | 2026-04-10 | Reframed the project around a backend-first, operator-reviewed v1 and added a concrete component framework |
| 1.0     | 2026-04-09 | Initial creation |
