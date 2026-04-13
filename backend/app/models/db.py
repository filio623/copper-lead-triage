"""TODO build guide for database schema and persistence models.

Purpose:
- define the SQLite schema and any database-facing models
- keep persistence structure aligned with `LeadAnalysisRecord` and batch tracking

Implementation checklist:
- define table creation or migration logic
- represent `batch_runs`, `lead_snapshots`, `lead_analyses`, and `review_decisions`
- choose how JSON fields will be stored and retrieved
- decide how timestamps are written and parsed
- decide whether schema setup lives here or in a repository helper

Questions to answer while implementing:
- do you want raw SQL, `sqlite3`, or a very light abstraction?
- how will prompt version and model metadata be stored?
- how will updates to review status be tracked?
"""
