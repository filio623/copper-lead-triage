"""TODO build guide for the FastAPI application entrypoint.

Purpose:
- create the FastAPI app only after the service layer works locally
- wire route modules without putting business logic here

Implementation checklist:
- create the FastAPI app instance
- register startup and shutdown hooks if needed
- include `api/leads.py`, `api/runs.py`, and `api/reviews.py`
- wire config, logging, and dependency helpers
- keep this file thin

Questions to answer while implementing:
- how should repositories be constructed and injected?
- should the database be initialized on startup or separately?
- what health or readiness endpoints are worth exposing?
"""
