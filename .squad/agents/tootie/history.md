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
