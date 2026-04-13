"""TODO build guide for lead analysis persistence.

Purpose:
- save and load normalized analyses and related metadata

Implementation checklist:
- insert lead analysis rows
- fetch latest analysis by Copper lead id
- fetch analyses for a batch run
- update review status if that belongs here

Questions to answer while implementing:
- should raw snapshots be written through this repository or separately?
- how much denormalized summary data should be stored for easy querying?
"""
