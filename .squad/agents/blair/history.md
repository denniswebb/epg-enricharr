# Blair — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Missing episode metadata in custom_properties for XMLTV output  
**Solution:** Enrich custom_properties with season/episode numbers, previously_shown flags, etc.  

**Owner:** Dennis  
**Key References:**
- Dispatcharr plugin docs: https://github.com/Dispatcharr/Dispatcharr/blob/main/Plugins.md
- Dispatcharr EPG models: apps/epg/models.py
- XMLTV output generator: apps/output/views.py (lines 1698-1726 for episode-num)
- EPG import parser: apps/epg/tasks.py (line 1861+ for extract_custom_properties)

## Learnings

### Session 1: Core Plugin Implementation (2025-02-27)

**Architecture decisions:**
- Plugin follows Dispatcharr pattern: `Plugin` class with `run()` method, `fields` for settings, `actions` for operations
- Configuration passed in `config` dict at init, with sensible defaults matching Jo's scope decisions
- Bulk updates using Django's `bulk_update()` with 1000 batch size for efficiency

**Episode parsing approach:**
- Used regex patterns to handle multiple formats: `S##E##`, `s##e##`, `##x##`, `##X##`
- Patterns are case-insensitive and work with zero-padded numbers (S01E05, 2x36)
- Returns 1-based integers (season, episode) tuple or None for invalid input
- Validation: season > 0 and episode > 0 to avoid S0E0 edge cases

**Django patterns discovered:**
- `ProgramData.custom_properties` is JSONField — can update in-place, then bulk_update the objects
- `select_related('epg')` reduces query count when iterating programmes
- Late import of Django models (`from apps.epg.models import ProgramData`) allows testing outside Dispatcharr

**Category filtering:**
- Check if `custom_properties.category` (list) contains any TV-related strings
- Case-insensitive matching: "Series", "series", "SERIES" all match
- Default categories: Movies, Series, Sports (broad net per Jo's decision)

**Previously-shown logic:**
- If `custom_properties.get('new')` is not True, set `previously_shown: true`
- Prevents Plex from treating every airing as a new recording opportunity
- Respects explicit "new" flag from EPG providers

**Error handling:**
- Try/except around each programme enrichment to avoid batch failures
- Log errors and increment error counter
- Gracefully skip programmes with malformed data

**Dry-run mode:**
- Compute changes but skip bulk_update when `dry_run_mode: true`
- Return enrichment stats showing what would have been changed
- Useful for testing configuration before applying to production data

**Testing strategy:**
- MockProgramData class simulates Django model for unit tests (no database required)
- 15 test cases cover: parsing edge cases, category filtering, enrichment logic, config defaults
- All tests pass — parsing logic is solid, ready for Tootie's integration tests

**Key gotcha:**
- plugin.json `fields` must have `id`, `type`, `label`, `description`, `default` — missing any breaks Dispatcharr UI
- `tv_categories` stored as comma-separated text (not array) — need to split in code if plugin system doesn't handle lists

**What's working:**
- ✅ Parses S2E36, S01E05, 2x14 formats correctly
- ✅ Updates custom_properties with season/episode integers
- ✅ Marks previously_shown for non-new content
- ✅ Bulk updates efficiently (1000 batch size)
- ✅ Respects enable/disable flags
- ✅ Dry-run mode for safe testing
- ✅ 15 unit tests passing
- ✅ Plugin zip validates successfully

**Still needed:**
- Integration test with real Dispatcharr instance (Mrs. Garrett's task)
- Manual validation that XMLTV output includes episode-num (Dennis's smoke test)
- Documentation updates (Natalie's task)

**V2 scope (sports enrichment):**
- Year-based season numbering: `season = programme.start_time.year`
- Sequential episode ordinals within sport+season
- Requires sport-specific logic (different for Soccer vs Rugby vs NBA)
- Settings stubbed but disabled by default

**Parallel work note:**
- Tootie has written additional test classes (TestSportsEnrichment, TestBulkOperations, TestIntegration) in parallel
- These tests expect V2 features (sports) and APIs (enrich_batch) not in MVP scope
- Core MVP tests (TestEnrichmentPlugin) all pass: 15/15 ✅
- Failed tests are expected — they're testing unimplemented V2 features per Jo's scope decision
- Integration tests are skipped (waiting for Mrs. Garrett's Dispatcharr env)

### Session 2: Production Readiness (2026-02-28)

**Learning:** Plugin is MVP-complete: 15/15 core tests pass, dry-run mode works, bulk operations optimized. Extended test suite (34 total tests) validates roadmap; V2 features (sports enrichment) correctly deferred. Episode parsing logic is solid and handles all documented formats. Plugin ready for Dispatcharr installation and manual validation.
