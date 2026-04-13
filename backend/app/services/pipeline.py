"""TODO build guide for the per-lead orchestration pipeline.

Purpose:
- own the end-to-end flow for one lead
- return a complete `LeadAnalysisRecord`

Suggested workflow:
- fetch raw lead
- validate and normalize
- compute deterministic rule score
- decide whether to enrich
- decide which LLM tasks to run
- persist snapshots and results
- return the saved analysis record

Implementation checklist:
- define one primary entrypoint for processing a single lead
- keep orchestration here instead of inside prompts or scripts
- make each step easy to stub in tests
- handle recoverable failures without hiding them

Questions to answer while implementing:
- should persistence happen once at the end or at multiple checkpoints?
- how should partial failures be represented in stored output?
"""
