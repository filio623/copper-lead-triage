# Phase 0 Review Rubric

**Created:** 2026-04-13
**Modified:** 2026-04-13
**Version:** 1.1

**Status:** Active working rubric
**Source Sample:** [phase0_review_sample.csv](/Users/jamesfilios/Software_Projects/copper-lead-triage/phase0_review_sample.csv)

---

## Purpose

This document captures the first-pass manual review rubric derived from the Phase 0 lead sample review. It is intended to turn manual judgment into a repeatable scoring framework that can later be implemented in deterministic rules and compared against LLM output.

This is a working rubric, not a final policy. It should be refined as more leads are reviewed.

---

## Review Sample Basis

As of 2026-04-13, the rubric below is based on 48 manually labeled leads from the Phase 0 review sample.

Observed action distribution:

- `research`: 19
- `hold`: 12
- `reject`: 9
- `pursue`: 8

High-level observations from the labeled sample:

- `pursue` leads tended to have both usable contact information and enough context to understand why the lead might matter
- `research` leads often showed possible event, wedding, photo, fashion, or related fit, but lacked enough certainty or completeness for immediate outreach
- `hold` leads were usually incomplete, low-confidence, or lower-priority, but not obviously worthless
- `reject` leads were typically both sparse and a poor business fit

---

## Recommended Action Labels

### `pursue`

Use `pursue` when the lead appears actionable now and has a plausible business fit for Step and Repeat LA.

Typical signals:

- usable contact information is present
- enough context exists to understand the business or role
- the company or person appears event-related or plausibly relevant to backdrops, step and repeats, media walls, or related products
- there is enough confidence to justify outreach without requiring major additional research first

Typical notes from the sample:

- good data available
- contacted recently
- event management company
- weddings are great for backdrops
- lots of contact points

### `research`

Use `research` when the lead may be promising, but more information is needed before deciding whether to pursue.

Typical signals:

- some business-fit signal is present, but the lead is not complete enough to act on confidently
- direct contactability is weak or incomplete
- outside research could materially change the decision
- the industry, event, or company type suggests possible relevance

Typical notes from the sample:

- need to get website and email to find more data
- worth researching
- good for backdrops but needs more research
- potential for step and repeat product sales
- worth getting more information

### `hold`

Use `hold` when the lead is weak, incomplete, low-priority, or uncertain, but not clearly bad enough to reject.

Typical signals:

- sparse contact or company information
- lower-probability fit
- geography may reduce urgency or likelihood
- there is not enough evidence to reject, but also not enough reason to spend research time immediately

Typical notes from the sample:

- little data available
- may research later
- lower chance of business
- hold for future
- low probability of sales

### `reject`

Use `reject` when the lead is both too weak and too unlikely to matter.

Typical signals:

- almost no usable information
- no contact points
- poor business fit
- little realistic opportunity even if more time were spent

Typical notes from the sample:

- almost no data here
- mostly empty lead
- no contact
- not a good fit for this business
- little opportunity here

---

## Preliminary Scoring Dimensions

The review notes suggest that the first deterministic scoring layer should include at least these dimensions:

- `completeness`
  how much useful lead information is present

- `contactability`
  whether there is a realistic path to contact the lead

- `business_fit`
  whether the lead appears relevant to Step and Repeat LA offerings

- `geography_or_serviceability`
  whether location affects urgency or practical value without acting as an automatic disqualifier

- `research_worthiness`
  whether additional research could materially improve the decision

- `recommended_action`
  the synthesized outcome: `pursue`, `research`, `hold`, or `reject`

---

## Early Rule Implications

The labeled sample suggests these first-pass heuristics:

- a lead should rarely be `pursue` without both usable contact information and contextual business fit
- sparse person-only leads are strong candidates for `hold` or `reject`
- missing information does not always mean `reject`; if the lead appears plausibly relevant, it often falls into `research`
- poor business fit plus weak data is a strong `reject` pattern
- out-of-region geography can reduce priority, but it is not a hard reject by itself

These are not yet final scoring rules. They are the initial design inputs for `backend/app/services/rules.py`.

---

## Current Implementation Status

As of 2026-04-13:

- this rubric has been translated into a first-pass `RuleScoreResult` shape
- the initial deterministic scoring logic has been implemented in `backend/app/services/rules.py`
- the current implementation should be treated as a baseline, not a finished policy

## Next Steps

1. Compare deterministic rule outcomes against future manual reviews and LLM outputs.
2. Revisit the keyword lists, thresholds, and action-mapping logic after more labeled leads are reviewed.
3. Expand the rubric when outreach-draft quality criteria become clearer.
4. Use later evaluation loops to tune the rules without losing explainability.

---

## Changelog

| Version | Date       | Description |
|---------|------------|-------------|
| 1.1     | 2026-04-13 | Noted that the first-pass rubric has now been implemented in the initial deterministic rules layer |
| 1.0     | 2026-04-13 | Created the first-pass manual review rubric from the Phase 0 labeled sample |
