---
updated_at: 2026-02-28T21:53:00Z
focus_area: V3 planning — sports title grouping in Plex
active_issues: []
---

# What We're Focused On

## Active Focus
**V3 planning — sports title grouping in Plex**

## Immediate Next Actions (in order)

1. **Blair: Research task** — Check Dispatcharr source `apps/output/views.py` (lines 1698-1726) for what `custom_properties` field controls XMLTV `<title>` vs `<sub-title>`. Does writing `sub_title` or `show_title` get picked up?

2. **Blair: Research task** — Pull real EPG title samples from live DB for AFL, NBA, NRL, Netball, SuperLeague. Are titles consistently "Sport: Team v Team" prefix-colon format or messy? DB access: `docker exec Dispatcharr psql -U dispatch -d dispatcharr` via SSH to 10.0.0.100. Table: `epg_programdata`, column: `custom_properties`.

3. **Jo: After Blair's research** — Decide approach for show title extraction: delimiter (split on ":") vs configurable per-sport regex vs hybrid.

4. **V3 feature planning conversation with Dennis** — He wants to discuss all V3 features, not just sports grouping. Make sure nothing gets dismissed undocumented.

## Known V3 Candidates (from decisions.md)

- Sports title grouping (core V3 — Plex groups all AFL matches under "AFL" etc.)
- Better EPG descriptions for sports (current ones are generic filler)
- Sequential episode numbering for sports (date-based is ugly in Plex)
- Multi-language episode string parsing
- Enrichment statistics dashboard
- Admin UI for category mapping
- External API lookups (TVDB/TMDB) — explicitly deferred

## Current State

- v2.0.2 live, 73 tests passing
- Decisions files consolidated

## Process Directive

Always update now.md at end of session with pending items so fresh sessions pick up automatically.
