# Tootie — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** EPG enrichment must be validated against real data; quality gates prevent regressions  
**Solution:** Comprehensive tests for parsing, database updates, and output validation  

**Owner:** Dennis  
**Key Test Scenarios:**
- Onscreen episode parsing: S2E36, S9E93, S01E01, etc.
- Sports numbering: year-based season, game ordinals
- Edge cases: missing episode data, malformed strings, duplicate programmes
- Bulk updates: efficiency, transactional safety, no data loss
- XMLTV output: episode-num tags generated correctly

## Learnings

(To be populated as Tootie develops test suite.)
