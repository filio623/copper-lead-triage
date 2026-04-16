# Lead Triage Engine — Build Plan

**Created:** 2026-04-13
**Modified:** 2026-04-15
**Version:** 1.5

**Status:** Active working plan
**Related Docs:** [app_architecture.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/app_architecture.md), [crm_findings_for_verification.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/crm_findings_for_verification.md), [phase0_review_rubric.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/phase0_review_rubric.md)

---

## Purpose

This document is the step-by-step build guide for the backend-first lead triage app. It is meant to track the implementation order, define deliverables, and point to the target files that should be filled in.

Use this document as the working checklist while building. Use the architecture document for product direction and design decisions.

---

## Current Starting Point

Already in place:

- Copper lead fetch exists
- lead validation and first-pass normalization exist
- a local deterministic gate exists
- a first `PydanticAI` triage prototype exists
- a first `TriageInput` model now exists for the planned triage service contract

Not in place yet:

- durable rule scoring output
- enrichment adapters
- orchestration pipeline
- API routes
- review workflow

### Phase 0 Progress Note

As of 2026-04-13, a first-pass review rubric has been created from 48 manually labeled leads in the Phase 0 sample. That rubric should now be used as the reference for the first deterministic scoring implementation.

As of 2026-04-13, the representative review-sample builder script also exists at `backend/scripts/build_review_sample.py`.

---

## Build Principles

- Keep the current prototype usable while migrating toward the target structure
- Prefer typed internal models over ad hoc dictionaries
- Keep deterministic rules outside the LLM
- Keep one primary per-lead triage agent as the default architecture
- Add future LLM tasks as separate typed modules, not one giant prompt
- Store evidence and reasoning so outputs can be reviewed and tuned later

---

## Phase Plan

### Phase 0 — Evaluation Rubric

Goal:
Define what the system is actually trying to optimize before building more automation.

Deliverables:

- a manual sample set of 50 to 100 leads
- a lightweight review rubric for lead quality, completeness, contactability, and business fit
- a definition of what counts as a usable outreach draft

Target files:

- [docs/build_plan.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/build_plan.md)
- future evaluation notes or sample exports

Exit criteria:

- there is a shared definition of a good lead
- there is a shared definition of a good draft

Current status on 2026-04-13:

- a first-pass action rubric now exists in [phase0_review_rubric.md](/Users/jamesfilios/Software_Projects/copper-lead-triage/docs/phase0_review_rubric.md)
- the rubric is good enough to begin drafting the first deterministic rules
- the review-sample builder script exists and can regenerate the manual review set
- outreach-draft quality standards still need to be sharpened as more samples are reviewed

### Phase 1 — Data Contracts And Normalization Hardening

Goal:
Make the internal lead model strong enough to support rules, enrichment, and LLM tasks.

Deliverables:

- improve `NormalizedLead`
- preserve important Copper fields needed for scoring and research
- normalize placeholders, contact methods, timestamps, and relevant custom fields

Target files:

- [backend/app/models/lead.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/models/lead.py)
- [backend/app/services/normalize.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/normalize.py)
- [backend/app/clients/copper.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/clients/copper.py)

Exit criteria:

- the normalized model contains the fields needed by rules and triage
- normalization is deterministic and easy to test

### Phase 2 — Deterministic Rules

Goal:
Replace the current boolean gate with a real scoring layer.

Deliverables:

- full `RuleScoreResult`
- completeness scoring
- contactability scoring
- disqualifiers
- recommended next rule action
- human-readable rule reasons

Target files:

- [backend/app/services/rules.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/rules.py)
- [backend/app/models/analysis.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/models/analysis.py)
- [tests/test_rules.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/tests/test_rules.py)

Exit criteria:

- rule scoring works without the LLM
- you can explain every score from stored rule output

Current status on 2026-04-13:

- `backend/app/services/rules.py` now contains the first implemented deterministic scoring layer
- `backend/app/models/analysis.py` has been updated to support richer rule output
- `tests/test_rules.py` covers the initial scoring contract
- the next step is to replace the legacy boolean gate in `backend/app/services/scoring.py` with the new rule output or move triage into `triage.py`

Current status on 2026-04-14:

- `backend/app/models/analysis.py` now includes a first `TriageInput` model for the Phase 3 triage task contract
- `backend/app/services/triage.py` now has an early local proof-of-concept agent skeleton for per-lead triage experimentation
- the local triage harness now passes structured deps correctly and injects the serialized triage input into the prompt for testing
- `backend/app/clients/llm.py` is still a placeholder and should become the thin provider/model setup layer before triage is formalized further
- `tests/test_triage_contracts.py` is still a placeholder and should be the next place to lock the Phase 3 contract down

### Phase 3 — LLM Task Layer

Goal:
Formalize the first triage agent and leave room for future LLM tasks.

Deliverables:

- one primary per-lead triage agent
- typed task input and output contracts
- prompt versioning and model metadata strategy
- a clear split between triage and future tasks such as research summary or draft critique

Target files:

- [backend/app/services/triage.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/triage.py)
- [backend/app/clients/llm.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/clients/llm.py)
- [tests/test_triage_contracts.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/tests/test_triage_contracts.py)

Exit criteria:

- the agent only handles judgment and drafting tasks
- deterministic validity checks remain outside the agent

Near-term implementation notes on 2026-04-14:

- keep the first agent focused on triage judgment and optional drafting, not online research
- treat enrichment as a later separate task instead of folding web research into the first triage agent
- move from the current local proof-of-concept harness to a reusable service entrypoint in `backend/app/services/triage.py`
- add contract tests for input shaping, structured output validation, and triage gating behavior before moving on to pipeline orchestration

Current status on 2026-04-15:

- `backend/app/services/triage.py` now exposes a reusable triage service entrypoint around the agent task
- `backend/app/clients/llm.py` now contains the thin model factory for the triage task
- `tests/test_triage_contracts.py` now covers triage gating, prompt building, deps shaping, and service metadata

### Phase 4 — Persistence

Goal:
Store raw inputs, analysis outputs, run metadata, and review state.

Deliverables:

- SQLAlchemy-backed SQLite schema
- repository layer
- database initialization path
- saved lead analyses and batch runs

Target files:

- [backend/app/models/db.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/models/db.py)
- [backend/app/repositories/analyses.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/repositories/analyses.py)
- [backend/app/repositories/runs.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/repositories/runs.py)
- [backend/app/repositories/reviews.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/repositories/reviews.py)
- [tests/test_repositories.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/tests/test_repositories.py)

Exit criteria:

- a lead analysis can be saved and loaded
- a batch run can be tracked over time

Current status on 2026-04-15:

- `backend/app/models/db.py` now defines the initial SQLAlchemy ORM models, engine/session helpers, and typed persistence models
- `backend/app/repositories/analyses.py` now saves lead snapshots and lead analyses and can fetch the latest stored analysis
- `backend/app/repositories/runs.py` now creates, updates, and fetches batch runs
- `backend/app/repositories/reviews.py` now stores review history and mirrors the effective review status back onto the saved analysis row
- `tests/test_repositories.py` now covers schema creation, run persistence, analysis persistence, review persistence, and JSON/timestamp round-tripping
- the next step after persistence is to wire these pieces together in `backend/app/services/pipeline.py`

### Phase 5 — Per-Lead Pipeline

Goal:
Move the app from loose helper functions to one orchestrated workflow.

Deliverables:

- fetch
- normalize
- rule score
- optional enrichment
- optional LLM tasks
- persistence
- one returned `LeadAnalysisRecord`

Target files:

- [backend/app/services/pipeline.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/pipeline.py)
- [tests/test_pipeline.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/tests/test_pipeline.py)

Exit criteria:

- one lead can be processed end-to-end through a single service entrypoint

### Phase 6 — Batch Runs

Goal:
Process many leads safely and review the output later.

Deliverables:

- sample run support
- bulk run support
- progress counters
- duplicate avoidance
- failure logging

Target files:

- [backend/app/services/batch.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/batch.py)
- [backend/scripts/run_sample.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/scripts/run_sample.py)
- [backend/scripts/run_bulk.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/scripts/run_bulk.py)

Exit criteria:

- a sample batch can be run and saved
- failures are visible without stopping the whole run

### Phase 7 — Review Workflow

Goal:
Make results easy for a human to inspect, annotate, approve, or reject.

Deliverables:

- review decision model
- review service
- export or summary workflow for manual inspection

Target files:

- [backend/app/services/review.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/services/review.py)
- [backend/scripts/review_export.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/scripts/review_export.py)

Exit criteria:

- a human can review saved analyses and record a decision

### Phase 8 — API Layer

Goal:
Expose the existing service layer through a thin FastAPI interface.

Deliverables:

- app startup
- route modules for runs, leads, and reviews
- dependency setup for repositories and services

Target files:

- [backend/app/main.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/main.py)
- [backend/app/api/leads.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/api/leads.py)
- [backend/app/api/runs.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/api/runs.py)
- [backend/app/api/reviews.py](/Users/jamesfilios/Software_Projects/copper-lead-triage/backend/app/api/reviews.py)

Exit criteria:

- the API is only a wrapper around already-working services

---

## Recommended Implementation Order

1. Define the evaluation rubric.
2. Harden `NormalizedLead`.
3. Build `rules.py`.
4. Build the SQLite schema and repositories.
5. Build `triage.py`.
6. Build `pipeline.py`.
7. Build `run_sample.py`.
8. Build `batch.py` and `run_bulk.py`.
9. Build review support.
10. Add FastAPI last.

---

## Tracking Checklist

- [ ] Phase 0 complete
- [ ] Phase 1 complete
- [ ] Phase 2 complete
- [ ] Phase 3 complete
- [ ] Phase 4 complete
- [ ] Phase 5 complete
- [ ] Phase 6 complete
- [ ] Phase 7 complete
- [ ] Phase 8 complete

---

## Changelog

| Version | Date       | Description |
|---------|------------|-------------|
| 1.5     | 2026-04-15 | Switched the new Phase 4 persistence layer from raw `sqlite3` to SQLAlchemy while keeping SQLite as the initial backing database |
| 1.4     | 2026-04-15 | Recorded the reusable Phase 3 triage service milestone and the first implemented SQLite persistence layer for Phase 4 |
| 1.3     | 2026-04-14 | Recorded the Phase 3 triage-task start, the new `TriageInput` contract, and the early local triage proof-of-concept status |
| 1.2     | 2026-04-13 | Recorded the review-sample builder and the first implemented deterministic rules milestone |
| 1.1     | 2026-04-13 | Added the first-pass Phase 0 rubric as an input to the build plan and noted current Phase 0 progress |
| 1.0     | 2026-04-13 | Initial build-plan document created |
