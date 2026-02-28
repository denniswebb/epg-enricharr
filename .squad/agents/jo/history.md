# Jo — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Plex DVR doesn't recognize TV shows or sports from IPTV EPG — missing xmltv_ns episode numbering  
**Solution:** Plugin enriches ProgramData.custom_properties in the database with missing metadata  

**Team:** 8 members (6 cast + Scribe + Ralph)  
**Owner:** Dennis (user running the squad)  

## Learnings

### Session 1: Initial Scope Decisions (2025-02-27)

**Scope Clarifications:**
- User requirements were complete and well-defined — rare but appreciated
- MVP scoping: TV enrichment alone solves 80% of problem; sports adds complexity without proportional value
- Data flow was pre-validated by user (import → custom_properties → output generator) — no guesswork needed

**Patterns Noticed:**
- Three-layer test strategy (unit/integration/manual) maps cleanly to team roles: Tootie (unit), Mrs. Garrett (integration), Dennis (manual)
- "Previously shown" flag is critical but easy to overlook — prevents false "New" recordings in Plex
- Plugin settings defaults should be production-ready (dry_run: false), not dev-mode (dry_run: true)

**Architectural Insights:**
- Dispatcharr plugin system gives direct Django model access — simple, powerful, no API layer
- Bulk updates via Django .update() are essential for performance (EPG refresh = thousands of programs)
- Output generator already checks for season/episode keys — our job is purely data enrichment, not format changes

**Team Dynamics:**
- Decisions recorded before work starts = team can parallelize without blocking on me
- Mrs. Garrett's local Dispatcharr setup is critical path — integration tests need it
- Blair can reject scope creep using documented out-of-scope list
