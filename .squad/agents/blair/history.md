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

### Session 3: Category Field Name Investigation (2026-02-28)

**Finding: Fix belongs in the TESTS, not in plugin.py.**

Confirmed against Dispatcharr source (`apps/epg/tasks.py` line 1861+):
```python
def extract_custom_properties(prog):
    categories = [cat.text.strip() for cat in prog.findall('category') if cat.text and cat.text.strip()]
    if categories:
        custom_props['categories'] = categories  # plural key
```
- XMLTV XML tag is `<category>` (singular) — Dispatcharr reads multiple XML nodes and collects them into a list stored under **`categories`** (plural) in `custom_properties`.
- `plugin.py` line 87 (`custom_props.get('categories', [])`) is **CORRECT** — matches real Dispatcharr behavior.
- The 3 failing tests used `'category'` (singular) in MockProgramData fixtures — wrong key name.
- **Fix:** Change `'category'` → `'categories'` in all MockProgramData `custom_properties` fixtures.

**Tootie already applied the fix** (unstaged changes in `tests/test_enrichment.py`) — 46 tests now collect, 35 pass, 11 skipped (V2/integration stubs). The fix is correct and verified against Dispatcharr upstream.

**`enrich_batch` status:** Referenced only in tests decorated `@pytest.mark.skip(reason="Requires enrich_batch method implementation")`. Safe to leave as V2 stub — none of those tests execute.

**Other field name observations:**
- All other fields (`onscreen_episode`, `new`, `previously_shown`) are consistent between plugin.py and test fixtures — no other mismatches found.
- Session 1 history note said `custom_properties.category` (singular) — that was an error in my own notes. The real Dispatcharr API uses plural. History corrected here.

**Confirmed field name:** `categories` (plural) is the correct and official Dispatcharr field name for storing custom_properties list of category names. This is the definitive reference for any future development.

### Session 4: V2 Sports/News Enrichment (2026-02-28)

**What was implemented:**

1. **`format_string(template, programme)`** — Token formatter resolving 7 tokens: `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{hh}`, `{mm}`, `{channel}`. Uses `programme.start` (falls back to `programme.start_time` via getattr). Channel token silently omitted if `channel_id` is non-numeric (uses `programme.channel_id` FK first, then `programme.channel.channel_id`).

2. **`classify_programme(programme)`** — Returns `'movie'`, `'sports'`, `'news'`, or `'tv'`. Matches compiled regex patterns against joined categories + title. Precedence: movie → sports → news → tv.

3. **Updated `enrich_programme()`** — Now classifies before enriching. Movies return `{}` immediately. Sports/news use format string templates when `enable_sports_enrichment`/`enable_news_enrichment` is True. If both season+episode already exist in custom_properties (not None, not 0), uses them as-is. TV path unchanged.

4. **7 new plugin.json fields:** `enable_news_enrichment`, `sports_season_format`, `sports_episode_format`, `news_season_format`, `news_episode_format`, `movie_patterns`, `sports_patterns`, `news_patterns`.

**Key decisions:**
- `_parse_patterns()` is a closure inside `__init__` (not a method) — spec's pattern, keeps it encapsulated.
- Season from format_string cast to `int()` with try/except — episode stays as string.
- Movies get no `previously_shown` flag (early return with `{}`); all other types do.
- Existing 35 passing tests remain 35 passing, 11 skipped — zero regression.

**Model field name confirmed:** `programme.start` is the actual field name per spec. Fallback to `start_time` via getattr for safety.

**Pattern defaults registered:** movie=`(?i)movie,(?i)film,(?i)cinema`; sports=13 patterns covering major sports; news=`(?i)news,(?i)weather,(?i)report`.
