"""TODO build guide for the primary PydanticAI triage task.

Purpose:
- interpret a normalized lead plus evidence
- return structured triage output without owning deterministic validation

Suggested responsibilities:
- build the triage task input
- define the triage agent
- run the task and validate the structured output
- attach prompt version and model metadata for persistence

Implementation checklist:
- decide what the agent should receive from rules and enrichment
- define how prompt instructions are composed
- keep one primary per-lead triage task for v1
- separate later tasks such as draft critique into their own modules if needed

Questions to answer while implementing:
- what information should be passed as dependencies versus prompt text?
- what output fields are required for a useful human review queue?
"""
