"""TODO build guide for enrichment providers.

Purpose:
- define the adapter boundary for optional outside research
- keep provider-specific logic separate from scoring and triage

Implementation checklist:
- define an enrichment provider interface or protocol
- decide what normalized inputs enrichment receives
- define what evidence should be returned in `EnrichmentResult`
- implement provider selection through config
- add error handling and rate-limit behavior

Possible later providers:
- Tavily
- Serper
- a no-op provider for local development and testing

Questions to answer while implementing:
- what evidence is actually useful for triage?
- when should enrichment be skipped even if available?
"""
