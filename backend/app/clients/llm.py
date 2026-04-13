"""TODO build guide for model/provider setup.

Purpose:
- centralize model configuration and task-specific agent construction
- keep provider details out of service modules where possible

Implementation checklist:
- define how model names and API keys are loaded
- decide whether each task gets its own factory function
- capture prompt version, provider, and model metadata
- expose helpers used by `services/triage.py` and later LLM tasks
- decide how local development and testing should stub model calls

Questions to answer while implementing:
- what should be configurable at runtime versus hardcoded in code?
- should every task create its own agent or share some common helper layer?
"""
