"""TODO build guide for deterministic lead scoring.

Purpose:
- replace the current boolean gate with a full `RuleScoreResult`
- keep explainable logic outside the LLM

Suggested responsibilities:
- score completeness
- score contactability
- identify obvious disqualifiers
- recommend a next rule action
- emit human-readable rule reasons

Implementation checklist:
- decide what fields contribute to completeness
- decide what fields contribute to contactability
- define hard disqualifiers versus soft warnings
- map rule outcomes to `pursue`, `review`, `hold`, or `reject`
- keep helper functions small and easy to test

Questions to answer while implementing:
- should lead quality and lead completeness be separate scores?
- what minimum score should trigger enrichment?
- what minimum score should allow LLM triage?
"""
