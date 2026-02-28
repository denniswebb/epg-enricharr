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

### 🔖 Core Context

**Key Implementation Patterns (Sessions 1–6):**

**V1 TV Parsing:**
- Episode parsing: regex patterns S##E##, s##e##, ##x##, case-insensitive, zero-padded
- Returns 1-based integers (season, episode) or None for invalid input
- Validation: season > 0, episode > 0 to avoid S0E0 edge cases
- Field name: `onscreen_episode` for display; auto-generated as `S{season}E{episode}`

**V2 Sports/News Enrichment:**
- Format string approach: {YYYY}, {YY}, {MM}, {DD}, {hh}, {mm}, {channel} tokens
- Numeric channel only: integer channel_id or numeric string; non-numeric silently omitted
- Fallback chain: If EPG has season+episode → use as-is. Else generate from templates.
- Onscreen episode: Always write `S{season}E{episode}` for display consistency
- Season int conversion failure → graceful fallback: write episode-only, no `S` prefix

**Django Integration:**
- `ProgramData.custom_properties` is JSONField — update in-place, bulk_update for efficiency
- `select_related('epg')` reduces query count
- Bulk operations: batch size 1000 for performance
- Late model import allows testing outside Dispatcharr

**Data Structure Lessons:**
- Field names: `categories` (plural, list) not `category` (singular)
- API structure: `channel_id`, `start` (datetime), `custom_properties` (jsonb)
- XMLTV output reads from custom_properties keys: season, episode, onscreen_episode, previously_shown
- Dispatcharr fallback logic: if onscreen_episode absent, uses `E{episode}` (no season) — this is why we must write onscreen_episode

**Bug-Fix Patterns:**
- Preserve-path gap: When programme has existing season+episode but missing onscreen_episode, regenerate it with guard: `if not custom_props.get('onscreen_episode')`
- Test fix patterns: Use preserve tests (`.get(key, default) == default`) to catch overwrites
- Verification: Always query actual database for format fixes; statistics (0-error counts) are insufficient

**Configuration Design:**
- Per-strategy format strings: sports_season_format, sports_episode_format, news_season_format, news_episode_format
- Feature flags: enable_tv_enrichment, enable_sports_enrichment, enable_news_enrichment
- Defaults: TV enabled, sports/news disabled (V1 ships with TV only)
- Dry-run mode: Prevents database writes, returns changes dict for inspection

**Current Status (End Session 6):** V1 shipped and verified. V2 implemented with format strings, classification, and regeneration logic. Production verification (v2.0.2) confirmed onscreen_episode format in database. Team patterns: spec-first design, test-driven validation, database verification for format fixes.

---

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

### Session 5: onscreen_episode Bug Fix for Sports/News (V2)

**Bug:** The V2 sports/news generated path wrote `season` and `episode` to `custom_properties` but never wrote `onscreen_episode`. The V1 TV path preserves `onscreen_episode` from the raw EPG string (e.g. "S1 E11 Guilty Witness") which Dispatcharr uses for display. Without `onscreen_episode`, the season was invisible in the displayed episode for sports/news.

**Investigation:**
- `enrich_programme()` lines 202-207 (sports else) and 216-221 (news else): generate season as int + episode as string from format templates, but set nothing for `onscreen_episode`.
- The `if existing_season and existing_episode` branch correctly re-uses EPG data as-is — that path doesn't need `onscreen_episode` because the EPG presumably already has it.
- decisions.md had no prior ruling on `onscreen_episode` format for generated episodes.

**Fix (2 `else` branches only):**
- Sports else (lines 208-211): After generating season+episode, write `onscreen_episode = f"S{season}E{episode}"` if season was successfully converted to int; otherwise just `episode` string alone.
- News else (lines 226-229): Same logic.
- No change to the `if existing_season and existing_episode` branch (EPG data path).
- No change to the TV path.

**Test result:** 63 pass, 11 skipped, 2 pre-existing failures (version string checks, unrelated).

**Format decision:** `S{season}E{episode}` — e.g. `S2026E0315193042`. Consistent with Plex DVR S/E notation. Season is the int value (no zero-padding). Episode is the raw format string output.

### Session 6: onscreen_episode Dead Zone — Diagnosis (2026-03-01)

**Bug reported:** Live EPG shows `<episode-num system="onscreen">E03011800</episode-num>` — missing season prefix. Expected: `S2026E03011800`.

**Investigation:**

1. **Fix IS in plugin.py** — lines 208–211 (sports) and 226–229 (news) correctly write `onscreen_episode = f"S{season}E{episode}"`.

2. **Dispatcharr confirmed** (`apps/output/views.py`): Reads `custom_data["onscreen_episode"]` verbatim for the onscreen XML tag. Falls back to `E{episode}` (no season) if `onscreen_episode` key is absent. This explains the symptom exactly.

3. **Root cause:** The fix only lives in the `else` branch (new generation). The `if existing_season and existing_episode` branch (lines 199–201 sports, 217–219 news) copies season+episode to `changes` but NEVER sets `onscreen_episode`. Programmes already enriched before the fix had season+episode but no `onscreen_episode`. On re-run, they hit the `if existing` branch and never reach the `else` where `onscreen_episode` is built. They are permanently stuck.

4. **xmltv_ns works** because Dispatcharr builds it directly from `season` and `episode` integer math — no `onscreen_episode` key required. That's why season appeared in xmltv_ns but not onscreen.

**Required fix:**
Add `if not custom_props.get('onscreen_episode'): changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"` to both `if existing_season and existing_episode` branches (sports and news).

**Diagnosis written to:** `.squad/decisions/inbox/blair-onscreen-diagnosis.md`

### Session 7: onscreen_episode `if existing` Branch Fix (2026-03-01)

**Fix applied:** Added `onscreen_episode` generation to both `if existing_season and existing_episode` branches (sports and news) in `enrich_programme()`.

**Pattern added to sports branch (was lines 199–201, now 199–203) and news branch (was lines 217–219, now 217–221):**
```python
if existing_season and existing_episode:
    changes['season'] = existing_season
    changes['episode'] = existing_episode
    if not custom_props.get('onscreen_episode'):
        changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
```

**Guard:** `if not custom_props.get('onscreen_episode')` prevents overwriting a correctly-set value from a prior run.

**Test result:** 67 pass, 11 skipped, 2 pre-existing failures (version string `2.0.0` vs `2.0.1`, unrelated to this fix). Zero regression.

**Decision file written to:** `.squad/decisions/inbox/blair-existing-branch-fix.md`

### Session 8: XMLTV Field Mapping Research (2026-03-01)

**Research Task:** Understand how Dispatcharr converts `custom_properties` to XMLTV output, specifically investigating: (1) `sub_title` field mapping, (2) `show_title`/`series_title` field support, (3) approach for "grouped show name" (sports use case).

**Key Findings:**

**XMLTV Field Mapping (Confirmed via prior sessions):**
- `onscreen_episode` → `<episode-num system="onscreen">` (reads verbatim from custom_properties)
- `season` + `episode` → `<episode-num system="xmltv_ns">` (Dispatcharr builds from integer math)
- `previously_shown` → `<previously-shown>` tag
- `categories` → `<category>` elements (plural list in custom_properties)

**Critical Discovery — No sub_title Support:**
- ❌ Dispatcharr does NOT map `custom_properties.sub_title` to XMLTV `<sub-title>` element
- Setting `sub_title` in enrichment has NO EFFECT on XMLTV output
- No custom_properties field feeds into the XMLTV `<sub-title>` element

**Title Field Limitation:**
- ❌ XMLTV `<title>` comes from EPG programme.title field, not custom_properties
- `show_title` and `series_title` custom_properties fields do NOT exist in Dispatcharr's XMLTV pipeline
- Plugin cannot override or supplement the primary title

**Sports Grouping Architecture Gap:**
- ⚠️ Plex DVR groups sports matches by XMLTV `<title>` value — all episodes with same title are grouped
- Current architecture has NO field in custom_properties that modifies the output title
- Achieving "AFL series" grouping separate from episode title ("Collingwood v Richmond") requires:
  - Either: Dispatcharr core change to manipulate programme.title before XMLTV generation (outside plugin scope)
  - Or: Plex-side metadata agent configuration (outside XMLTV scope)
  - Or: V3 research into custom XMLTV extensions Dispatcharr might support

**Recommendation:** Sports grouping is NOT achievable via current XMLTV/custom_properties enrichment layer. Requires architectural decision at V3 planning phase.

**Research artifacts written to:**
- `.squad/decisions/inbox/blair-xmltv-field-research.md` — Complete technical findings and recommendation

### Session 9: Subtitle Field Check (2026-03-01)

**Task:** Verify if Dispatcharr `ProgramData` model has a `subtitle` field and whether it maps to XMLTV `<sub-title>` for Plex support.

**Critical Findings:**

1. **Model Field Exists:** ✅ `sub_title` (underscore format) is a core field on `ProgramData` model.
2. **XMLTV Mapping Confirmed:** ✅ Dispatcharr writes `prog.sub_title` verbatim to `<sub-title>` element (lines 1677–1678 in views.py).
3. **Plugin Cannot Write It:** ❌ The subtitle comes from the model field, not from `custom_properties`. Plugin enrichment has no path to populate `prog.sub_title`.

**Architecture Implication:**

Jo's idea to write match descriptions to a subtitle field for Plex support is **NOT feasible via plugin enrichment**. Here's the blocker:
- Dispatcharr XMLTV generator reads from `prog.sub_title` (database field), not `custom_properties`
- Plugin can only modify `custom_properties` (JSONField) via `enrich_programme()`
- No bridge exists between custom_properties and the model's sub_title field
- To write subtitles, we'd need database-level field manipulation (outside plugin scope) or require Dispatcharr core to support subtitle population from custom_properties

**Recommendation:** If match descriptions are valuable for reference, store them in `custom_properties` for our own UI/logging use only. Plex XMLTV import will not see them because they won't appear in the XMLTV output.

**Decision file:** `.squad/decisions/inbox/blair-subtitle-field-check.md`

---

### Session 10: V3 Sports Grouping Research & Architecture Decision (2026-02-28)

**Synthesis of Blair's XMLTV research into Jo's architecture proposal.**

**Key Finding (from Blair's research):**
- Custom_properties enrichment alone **cannot** solve sports grouping problem
- Dispatcharr XMLTV reads `<title>` from programme.title (EPG source), not custom_properties
- No custom_properties field can override XMLTV output title
- Subtitle field exists in model but plugin has no path to populate it (model field, not custom_properties)

**Architecture Decision by Jo — Option A (Recommended):**
- Modify `programme.title` directly in plugin (feature-flagged, off by default)
- Original title preserved in `custom_properties.original_title` for recovery
- 85% sports titles follow "Sport : Description" format — colon split is reliable
- Same Django ORM mutation pattern as custom_properties enrichment

**Scope Expansion:** This crosses from enrichment into data transformation. Modifies raw EPG data. Requires explicit user approval.

**Trade-Offs:**
- ✅ Plex groups all AFL matches under "AFL" — solves the business problem
- ✅ Feature-flagged, off by default — safe opt-in
- ✅ Original title preserved — recovery possible
- ❌ Dispatcharr UI shows truncated title instead of full episode title
- ❌ Other Dispatcharr consumers see modified title
- ❌ Philosophical: not pure enrichment anymore

**Implementation Ready (Phase 0–3 spec documented):**
- Phase 0: Check if ProgramData has subtitle field, confirm XMLTV mapping
- Phase 1: Title splitting logic in enrich_programme()
- Phase 2: Model field mutation in bulk update pipeline
- Phase 3: plugin.json settings (enable_sports_title_grouping, sports_title_delimiter)

**Fallback Plan (if rejected):**
1. Option C: Write `custom_properties.sport_name` only (metadata, no XMLTV effect)
2. Option B: File Dispatcharr feature request for custom_properties title override support
3. Document the limitation in README

**Status:** PENDING DENNIS APPROVAL. Phase 0 can proceed independently. Blocks Phase 1–3 implementation.

**Research artifacts merged into decisions.md:** `.squad/decisions/inbox/blair-xmltv-field-research.md`, `.squad/decisions/inbox/jo-v3-sports-grouping-arch.md`
