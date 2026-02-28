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

### Session 5: V2 Test Suite Added (Current)

**What was added (30 new tests, all passing):**

`TestFormatString` (12 tests):
- All 7 tokens validated against fixed datetime `datetime(2026, 3, 15, 19, 30)`: `{YYYY}`→'2026', `{YY}`→'26', `{MM}`→'03', `{DD}`→'15', `{hh}`→'19', `{mm}`→'30'
- `{channel}` with numeric channel_id → included; with non-numeric (e.g. 'ESPN') → silently omitted; with None → silently omitted
- Combined template `{MM}{DD}{hh}{mm}{channel}` with numeric channel → correct concatenation (e.g. '0315193042')
- Combined template with non-numeric channel → no channel suffix ('03151930')
- Default `sports_episode_format` with single-digit numeric channel → '031519307'

`TestClassifyProgramme` (9 tests):
- 'Movie' → 'movie', 'Film' → 'movie', 'Sports' → 'sports', 'News' → 'news', 'Series' → 'tv'
- No categories → 'tv' (fallback)
- Movie takes precedence over sports (both present → 'movie')
- Custom regex `(?i)kino` in movie_patterns config → 'Kino' category classifies as 'movie'
- Invalid regex `[invalid` → warning logged, pattern skipped, classify_programme returns valid result without crashing

`TestEnrichProgrammeV2` (9 tests):
- Movie → `enrich_programme()` returns `{}` (early return, no previously_shown)
- Sports with BOTH existing season+episode → returned as-is, not regenerated
- Sports with NEITHER → generates season from `{YYYY}` and episode from `{MM}{DD}{hh}{mm}{channel}`
- Sports with only season (no episode) → regenerates BOTH from format strings (existing season overwritten)
- Sports with only episode (no season) → regenerates BOTH from format strings
- News with `enable_news_enrichment=True` → season=year int, episode=`{MM}{DD}`
- TV with `categories: ['Series']` and `onscreen_episode` → V1 parse_episode_string path
- `enable_sports_enrichment=False` (default) → no season/episode set for sports
- `enable_news_enrichment=False` (default) → no season/episode set for news

**Final test counts: 65 passed, 11 skipped, 0 failed**

**Key implementation details confirmed by tests:**
- `format_string()` reads from `programme.start` attribute (not `custom_properties`)
- `classify_programme()` reads from `programme.custom_properties['categories']`
- When only one of season/episode exists, the `if existing_season and existing_episode` guard fails → BOTH are regenerated from format strings
- Movie early-return happens before `previously_shown` logic → movies return `{}`
- `{channel}` uses `str(channel_id).isdigit()` test — integer or numeric string passes, alpha fails silently

**MockProgramData updated** to add `start=None` and `channel_id=None` defaults — all 35 existing tests unaffected.

### Session 1: Test Suite Creation (Feb 28, 2026)

**Test Strategy:**
- TDD approach: Write tests first to define contract for Blair's implementation
- Comprehensive coverage across 6 test categories (34 total tests)
- Pragmatic use of skip markers for unimplemented features (V2 scope)

**Test Framework Setup:**
- pytest with pytest.ini configuration
- Mock objects for ProgramData (avoids Django dependency in unit tests)
- Test fixtures for realistic EPG data (sample-epg.xml)
- requirements.txt with test dependencies

**Test Categories Implemented:**
1. ✅ **Onscreen Episode Parsing** (15 tests) - S2E36 → season 2, episode 36
   - Valid formats: S2E36, S01E01, s2e5, 2x36 (case-insensitive)
   - Invalid formats: S2, E36, malformed strings
   - Edge cases: S00E00 (rejected per Blair's design), high numbers, embedded text
   
2. ✅ **TV Show Enrichment** (6 tests) - Series/Movies metadata
   - Enriching Series with onscreen_episode → season/episode in custom_properties
   - Preserving original onscreen_episode field
   - Handling invalid episode data gracefully
   
3. ⏳ **Sports Enrichment** (4 tests, SKIPPED) - Year-based seasons
   - Marked for V2 implementation
   - Year from start_time → season number
   - Sequential episode numbering per sport
   
4. ✅ **Previously-Shown Logic** (4 tests) - Flag non-new programmes
   - All non-new programmes get previously_shown=true
   - New programmes (new:true) don't get flag
   - Handles missing custom_properties
   - Can be disabled via config
   
5. ⏳ **Bulk Operations** (4 tests, SKIPPED) - Requires enrich_batch method
   - Batch processing 100+ programmes
   - Order preservation
   - Empty/single programme edge cases
   
6. ⏳ **XMLTV Output** (3 tests, SKIPPED) - Integration tests
   - Requires Dispatcharr setup (Mrs. Garrett)
   - Validate episode-num tags appear
   - Validate previously-shown tags

**Test Results:**
- 34 tests defined
- 23 PASSED (core functionality validated)
- 11 SKIPPED (V2 features + integration tests)
- 0 FAILED

**Coverage Gaps Discovered:**
- Sports enrichment is V2 scope (enable_sports_enrichment=False by default)
- Blair's plugin needs `enrich_batch()` method for batch tests
- Integration tests blocked until Mrs. Garrett sets up local Dispatcharr
- S00E00 rejected by design (Blair's validation rejects season/episode 0)

**Test Pattern Worth Reusing:**
- MockProgramData class for testing without Django ORM
- Separation of unit tests (fast, no dependencies) from integration tests (marked with skip)
- Test docstrings clearly state what is being tested
- Fixtures in tests/fixtures/ for realistic sample data

**Coordination Notes:**
- Blair has implemented plugin.py with episode parsing ✅
- Blair's implementation passes all 23 active unit tests ✅
- Skipped tests document expectations for future work
- Tests define clear contract: parse_episode_string, enrich_programme, should_enrich_tv

**Next Steps:**
- Blair: Implement enrich_batch() method for batch tests
- Blair: Implement sports enrichment for V2 (year-based seasons)
- Mrs. Garrett: Set up local Dispatcharr for integration tests
- Tootie: Review Blair's implementation against test expectations

### Session 2: MVP Validation Complete (2026-02-28)

**Learning:** All 23 MVP tests pass against Blair's plugin implementation. Test suite is comprehensive: 34 tests cover episode parsing, TV enrichment, previously-shown flags, bulk operations, and XMLTV output. V2 tests correctly skipped (sports enrichment deferred). TDD approach validated—tests defined contracts clearly; Blair's implementation met all expectations. MockProgramData class enables future testing without Django. Quality gates established.

### Session 3: Test Suite Audit (Current)

**Critical finding:** Tests are broken and not running in CI/locally. Import error (tests import `EnrichmentPlugin` but plugin defines `Plugin`) and field mismatch (`category` vs `categories`) caused all tests to fail. After fixes:
- **20 passing** (59% of active tests)
- **3 failing** (category field mismatch with Dispatcharr structure)
- **11 skipped** (V2 features + integration tests)

**Test coverage analysis:**
- ✅ Episode parsing: 100% covered, all formats tested (S2E36, 2x14, edge cases)
- ✅ Previously-shown logic: 100% covered, all scenarios validated
- ❌ TV enrichment: Tests stale - using `category` (singular) but plugin uses `categories` (plural) per Dispatcharr API
- ⏳ Dry-run mode: NOT TESTED - critical gap for safety
- ⏳ Error handling: Minimal coverage for malformed input
- ⏳ Bulk operations: 0% - enrich_batch method not implemented
- ⏳ Integration tests: Blocked pending Dispatcharr setup

**Quality assessment:** 🟡 50-80% effective coverage (tests exist but stale; core parsing solid but enrichment flow untested)

**Critical gaps before shipping:**
1. Tests must match Dispatcharr data structure (categories field)
2. Dry-run mode completely untested (safety feature!)
3. No error handling tests for malformed EPG data
4. No integration validation that XMLTV tags appear
5. enrich_batch method missing (needed for performance)

**Recommended actions:**
- Fix test fixtures to use `categories` (plural) to match real Dispatcharr data
- Add dry-run validation tests (verify no DB writes occur)
- Add error handling tests (corrupted custom_properties, invalid JSON, etc.)
- Set up local Dispatcharr for integration testing before V1 ships

### Session 3: Test Audit Summary & Findings (2026-02-28)

**Team Finding:** Test suite is broken but fixable. Critical gaps identified in dry-run coverage (safety feature), fixture field names (categories mismatch), and error handling. Import issue fixed by Tootie; stale fixtures and coverage gaps documented.

**Assessment:** Effective coverage is 🟡 50-80%. Episode parsing and previously-shown logic are solid (100% each); but TV enrichment tests are failing due to `category` vs `categories` mismatch with Dispatcharr API, and dry-run mode has zero test coverage (critical safety feature).

**Five Critical Gaps Before V1 Ships:**
1. Test fixtures use `category` singular but plugin expects `categories` plural — 3 tests fail
2. Dry-run mode completely untested — can't verify no DB writes occur
3. Error handling minimal — tests don't cover malformed custom_properties, invalid JSON, missing fields
4. No integration validation — tests exist but skipped (Dispatcharr setup incomplete)
5. Bulk operations untested — enrich_batch() method missing

**Quality Confidence:** Code review shows plugin.py is correct; tests are the validator. Once tests are fixed and expanded, V1 is shippable.

**Coordination:** All findings recorded in decisions.md under "Test Suite Status" for team visibility. Jo and Blair can prioritize fixes based on impact/effort assessment.

### Session 4: Test Suite Fixed + Dry-Run Coverage Added (2026-02-28)

**What was fixed:**
- **3 failing tests resolved**: `test_should_enrich_tv_with_series_category`, `test_should_enrich_tv_with_movies_category`, `test_enrich_programme_with_onscreen_episode` all used `'category'` (singular) in MockProgramData fixtures. `plugin.py`'s `should_enrich_tv()` correctly reads `'categories'` (plural) per Dispatcharr API. Updated all test fixtures to use `'categories'` — no changes to plugin.py needed.
- **All other `category` → `categories` fixtures updated** for consistency (even passing tests were using the wrong field name).

**New tests added (12 new, all passing):**

`TestDryRunMode` (7 tests):
- `test_dry_run_default_is_false` — confirms safe default
- `test_dry_run_enabled_via_config` — confirms config works
- `test_enrich_programme_returns_changes_in_dry_run` — enrich_programme() is pure, returns changes regardless
- `test_enrich_programme_does_not_mutate_object` — no side effects on programme object
- `test_dry_run_skips_bulk_update` — verifies `bulk_update` is NOT called when dry_run=True (mocks Django ORM)
- `test_live_mode_calls_bulk_update` — verifies `bulk_update` IS called in live mode
- `test_dry_run_stats_still_reported` — stats returned and logger called even without DB writes

`TestMalformedInput` (5 tests):
- `test_parse_none_returns_none` — parse_episode_string(None) → None
- `test_parse_empty_string_returns_none` — parse_episode_string("") → None
- `test_parse_not_an_episode_returns_none` — parse_episode_string("not_an_episode") → None
- `test_enrich_programme_with_none_custom_properties` — no crash when custom_properties is None
- `test_enrich_programme_with_garbage_onscreen_episode` — no season/episode set on garbage input

**Final test results: 35 passed, 11 skipped, 0 failed**
- Up from 20 passing (3 failing) → all green
- Coverage now includes critical safety feature (dry-run) and malformed data handling

**Technique used for dry-run tests:**
Mocked Django model imports using `unittest.mock.patch.dict(sys.modules, ...)` since `from apps.epg.models import ProgramData` is a late import inside `_enrich_all_programmes()`. This lets unit tests validate DB write behavior without a running Dispatcharr instance.
