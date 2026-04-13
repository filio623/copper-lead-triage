"""TODO build guide for sample and bulk batch processing.

Purpose:
- process many leads through the same per-lead pipeline
- track run-level metadata and progress

Implementation checklist:
- define what a sample run versus bulk run means
- create a batch run record before processing
- iterate lead ids or paginated source records
- skip duplicates if a rerun policy requires it
- capture per-lead failures without stopping the whole batch
- update progress counters and final run status

Questions to answer while implementing:
- should runs be resumable by page, lead id, or stored checkpoint?
- how should concurrency be limited for external APIs?
"""
