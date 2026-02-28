# Team Decisions

## Session 1: Team Formation

- **Universe:** Facts of Life (character-driven naming with functional resonance)
- **Team Size:** 8 agents (6 cast + Scribe + Ralph)
- **Casting:** Determined by universe fit, not role descriptions
- **Self-Validation:** All agents validate own work locally/in CI before handoff
- **Local-First Approach:** Mrs. Garrett provides dev tooling; Mr. Belvedere owns pipelines

## Session 2: Scope & Milestone Decisions

### 2026-02-27T21:50: Scope Decision — MVP Definition

**Decision:** MVP ships with TV show enrichment only. Sports enrichment is V2.

**Rationale:** TV shows (parsing S2E36 → season/episode) solve 80% of Plex DVR issues and have clearer success criteria. Sports (year-based seasons, ordinal numbering) require domain knowledge for each sport and complex validation. Shipping TV enrichment fast unblocks users immediately.

**Impact:** Blair focuses on TV parsing first. Tootie tests TV-only scenarios. Sports settings can be stubbed (disabled by default) for future work.

---

### 2026-02-27T21:50: Scope Decision — Plugin Settings Defaults

**Decision:** Default configuration:
- `enable_tv_enrichment: true` 
- `enable_sports_enrichment: false` (MVP ships disabled)
- `tv_categories: ["Movies", "Series", "Sports"]` (broad match initially)
- `sports_categories: []` (V2)
- `auto_mark_previously_shown: true` (prevents false "New" flags)
- `dry_run_mode: false` (production-ready by default)

**Rationale:** Safe, broad defaults that work for most users without configuration. TV categories cast wide net initially (we can refine later). Auto-marking previously-shown prevents Plex recording duplicates. Dry-run false means plugin is active on install.

**Impact:** Blair implements these defaults in plugin.json. Natalie documents override options.

---

### 2026-02-27T21:50: Scope Decision — Test Strategy

**Decision:** Three-layer testing:
1. **Unit tests** (Blair/Tootie): Test parsing logic in isolation (onscreen_episode → season/episode, previously-shown detection)
2. **Integration tests** (Mrs. Garrett): Plugin loads in local Dispatcharr, processes test ProgramData fixtures
3. **Manual validation** (Dennis): Install zip on real Dispatcharr, verify XMLTV output includes `<episode-num system="xmltv_ns">`

**Rationale:** Unit tests catch logic bugs fast. Integration tests prove plugin system compatibility. Manual validation confirms Plex actually recognizes the output. All three layers are needed for production confidence.

**Impact:** Tootie writes pytest unit tests alongside Blair's code. Mrs. Garrett sets up local Dispatcharr container + test data loader. Dennis runs final smoke test before release.

---

### 2026-02-27T21:50: Scope Decision — Out of Scope

**Decision:** The following are explicitly OUT:
- DVR recording filenames (Plex handles this)
- Plex metadata agents (we only enrich XMLTV)
- Retroactive enrichment of old ProgramData (plugin only processes new EPG refreshes)
- Custom category mapping UI (text config only)
- Multi-language support (English-only for MVP)

**Rationale:** Each of these requires integration with systems we don't own or scope creep into UX territory. The plugin solves one problem well: enriching custom_properties when EPG data arrives.

**Impact:** Natalie documents these non-goals in README. Blair can reject feature requests outside this scope.

---

### 2026-02-27T21:50: Quality Bar for "Done"

**Plugin is shippable when:**

1. ✅ **Functional:**
   - Parses S2E36, S01E05, 2x14 formats → season/episode integers
   - Sets `previously_shown: true` for non-new content
   - Updates ProgramData.custom_properties in bulk (Django .update())
   - Logs enrichment stats (X programs enriched, Y skipped)

2. ✅ **Tested:**
   - Unit tests: 80%+ coverage on parsing logic
   - Integration test: Plugin loads in Dispatcharr, processes fixture data
   - Manual test: Dennis confirms Plex recognizes enriched shows

3. ✅ **Documented:**
   - README explains what it does, how to install, how to configure
   - plugin.json has setting descriptions
   - Code has docstrings for parsing functions

4. ✅ **Packaged:**
   - Zip artifact with plugin.json + plugin.py
   - GitHub Actions releases on git tag push
   - Installation instructions in README

5. ✅ **Safe:**
   - Dry-run mode works (logs without writes)
   - No destructive updates (only adds keys to custom_properties)
   - Graceful failure if onscreen_episode is malformed

**Not required for V1:**
- Sports enrichment
- Performance optimization beyond basic bulk updates
- Admin UI for settings
- Localization

---

**Approved by:** Jo  
**Date:** 2026-02-27  
**Status:** ACTIVE — Team can proceed

### 2026-02-27T21:50: User directive — mise for dev automation

**By:** Dennis (user)  
**What:** Prefer `mise` for managing scripts and local dev environment  
**Why:** User preference — mise is the tool of choice for this project  
**Impact:** Mrs. Garrett and Mr. Belvedere should use mise for Makefile/task runner, env management, script orchestration

---

## Session 3: V1 Quality Assessment

### 2026-02-28T17:33:02Z: V1 Status — Critical Blocking Items Identified

**By:** Jo (Lead)

**Finding:** Project is 85% complete. Core implementation is sound and original vision remains perfectly in focus. Three critical gaps prevent release: (1) test import bug blocks all test execution, (2) CI/CD workflows are TODO stubs, (3) safety features untested.

**Verdict:** 🟡 NOT SHIPPABLE until blockers resolved. Estimated 2-3 hours to unblock.

**Blocking Items:**
1. Import mismatch: tests import `EnrichmentPlugin` but plugin.py defines `Plugin` — prevents test suite execution
2. CI/CD gaps: squad-ci.yml and squad-release.yml are skeleton files; pytest not configured for automated testing
3. Safety validation: Dry-run mode has zero test coverage; error handling for malformed data is minimal

**Quality Bar Assessment:**
- ✅ Functional: Complete. Parsing handles S2E36/S01E05/2x14, previously_shown works, bulk updates use Django ORM efficiently.
- ❌ Tested: Blocked. 0 tests can execute due to import bug.
- ✅ Documented: Complete. README comprehensive (354 lines), plugin.json settings described, code docstrings present.
- ❌ Packaged: Partial. Zip structure correct but CI/CD workflows unimplemented.
- 🟡 Safe: Partial. Code review shows correct implementation but unvalidated without tests.

**Original Vision:** ✅ Perfectly aligned. No scope creep detected.

**Recommended Path:**
1. Fix test import (5 min), run suite
2. Configure CI workflows for pytest (30 min)
3. Manual smoke test by Dennis on real Dispatcharr (15 min)
4. All three blocking items resolved → V1 shippable

**Full Report:** `.squad/decisions/inbox/jo-v1-status-gaps.md`

---

### 2026-02-28T17:33:02Z: Test Suite Status — Critical Gaps & Coverage Reality

**By:** Tootie (Tester)

**Finding:** Test suite appears to be 59% passing (20/34 tests) but is providing false confidence due to stale fixtures and import issues. Effective coverage is 🟡 50-80%.

**Current State:**
- ✅ 20 passing tests (59% of 34)
- ❌ 3 failing tests (stale fixtures don't match plugin implementation)
- ⏳ 11 skipped tests (V2 features + integration tests)

**Critical Gaps (Must Fix Before V1 Ships):**

1. **Test Fixtures Use Wrong Field Names** (HIGH) — Tests use `category` (singular) but plugin expects `categories` (plural) per Dispatcharr API. Three core enrichment tests fail because they validate wrong data structure. Fix: Update MockProgramData fixtures.

2. **Dry-Run Mode Completely Untested** (CRITICAL) — Safety feature with zero coverage. Can't verify plugin doesn't write to database when dry_run=true. Critical risk for production debugging. Fix: Add tests for dry-run behavior, stats logging, and changes dict output.

3. **Error Handling for Malformed Data Minimal** (MEDIUM) — Tests cover None and invalid episode strings only. Missing tests for corrupted custom_properties, missing required fields, large datasets, transaction failures. Risk: Plugin could crash in production. Fix: Expand error handling tests.

4. **No Integration Validation** (HIGH) — 3 integration tests skipped. Can't verify XMLTV output contains `<episode-num>` tags. Risk: Works in unit tests but fails in real Dispatcharr. Fix: Mrs. Garrett sets up local Dispatcharr.

5. **Bulk Operations Untested** (MEDIUM) — 4 bulk operation tests skipped due to missing `enrich_batch()` method. Can't validate performance with 100+ programmes. Fix: Decision needed (ship without, or implement).

**Coverage by Feature:**
- ✅ Episode Parsing: 100% (S2E36, 2x14, edge cases covered)
- ✅ Previously-Shown Logic: 100%
- ❌ TV Enrichment: 0% (fixture mismatch)
- ❌ Dry-Run Mode: 0%
- 🟡 Error Handling: 30%
- ✅ Config Defaults: 100%

**Root Cause:** Tests weren't maintained as plugin evolved. Import error prevented anyone from noticing failures.

**Next Steps:**
1. Fix import issue (DONE by Tootie)
2. Fix test fixtures to use `categories` plural
3. Add dry-run mode tests
4. Expand error handling tests
5. Set up integration tests

**Full Report:** `.squad/decisions/inbox/tootie-test-gaps.md`

---

### 2026-02-28T17:33:02Z: Documentation Assessment — Production-Ready

**By:** Natalie (Docs)

**Finding:** All 5 V1 criteria met. Documentation is complete, comprehensive, and production-ready. No gaps identified.

**Assessment:**
- ✅ README.md: Comprehensive (354 lines), covers architecture, installation, configuration, troubleshooting
- ✅ plugin.json: All setting descriptions present
- ✅ Code docstrings: All parsing functions documented
- ✅ Test documentation: Clear docstrings on test cases

**Verdict:** Documentation exceeds expectations. No V1 blockers in this area.

---

### 2026-02-28T17:33:02Z: Plugin API Automation Directives

**By:** Dennis (User)

**What:** Enable plugin via API and reload plugin system via API to support full automation pipeline.

**Directive 1 — Plugin Enable:** POST to `/api/plugins/plugins/{plugin-id}/enabled/` with payload `{"enabled":true}`. Requires Authorization bearer token and proper headers. Impact: Mrs. Garrett to add `enable-plugin` task to mise.

**Directive 2 — Plugin Reload:** POST to `/api/plugins/plugins/reload/` with Authorization bearer token. Triggers system-wide plugin reload (separate from individual enable). Impact: Mrs. Garrett to add `reload-plugins` task to mise.

**Rationale:** Automating deployment pipeline. Future runs can enable/reload plugins without manual UI interaction.

**Endpoints:**
- Enable: `http://{DISPATCHARR_HOST}/api/plugins/plugins/epg-enricharr-1_0_0/enabled/`
- Reload: `POST http://{DISPATCHARR_HOST}/api/plugins/plugins/reload/`

---

### 2026-02-28T17:39:42Z: Test Suite Fixed — Category Field & Coverage Expansion

**By:** Tootie (Tester)  

**Status:** ✅ RESOLVED — 35 passing, 0 failing, 11 skipped. Coverage ~85%.

**What was fixed:**
1. **Test fixture field name:** All MockProgramData fixtures updated from `'category'` (singular) to `'categories'` (plural) to match real Dispatcharr API behavior. Confirmed by Blair against upstream source (`apps/epg/tasks.py` line 1861+).
2. **Dry-run mode coverage:** Added 7 tests validating that dry_run_mode=true prevents database writes, returns changes dict without mutations, and still reports stats. This critical safety feature had 0% coverage.
3. **Malformed input handling:** Added 5 tests for None/empty/garbage inputs to ensure plugin never crashes on bad EPG data.

**Impact:** Test-related V1 blocker resolved. Plugin code (`plugin.py` line 87) was correct all along — issue was in test fixtures only.

**Effective coverage:** Improved from 50-80% to ~85%. All core features now validated. Bulk operations and integration tests remain skipped (V2/setup dependencies).

---

### 2026-02-28T17:39:42Z: Field Name Verification — Dispatcharr API Alignment

**By:** Blair (Backend)  

**Finding:** Confirmed `categories` (plural) is the correct field name in Dispatcharr's custom_properties structure. XMLTV has singular `<category>` XML tags, but Dispatcharr's `extract_custom_properties()` collects them into a list under the plural key `categories`.

**Plugin status:** `plugin.py` line 87 (`custom_props.get('categories', [])`) is **CORRECT** and matches real Dispatcharr behavior. No code changes needed.

**V2 deferred features:** `enrich_batch()` method is referenced only in skipped tests. Safe to leave unimplemented for V2.

---

## Session 4: V2 Design Finalization

### 2026-02-28T18:54Z: User directive — numeric channel only

**By:** Dennis (via Copilot)

**What:** The `{channel}` token in episode format strings must only be used when the channel ID is numeric. If the channel ID is non-numeric (e.g., "ESPN"), silently omit it from the generated episode string.

**Why:** User request — captured for team memory

---

### 2026-02-28T18:54Z: User directive — simplified enrichment fallback chain

**By:** Dennis (via Copilot)

**What:** The enrichment logic follows a simple two-step rule:
  1. If EPG data already provides both season AND episode → use them as-is. No generation.
  2. If the programme is NOT a movie AND season/episode are missing → generate using format string templates.
  No middle steps (no external lookups, no partial-match logic). Keep it simple.

**Why:** User request — captured for team memory

---

### 2026-02-28T21:00Z: V2 Design Direction — Approved

**By:** Jo (Lead), Dennis (Owner)

**Status:** ✅ APPROVED — Ready for implementation

This session finalizes V2 design for sports/news enrichment. Key artifacts:

1. **V2 Scope Discussion** — Problem statement, proposed approaches, trade-offs. Verdict: Regex-based content routing with format string templates. No external APIs for V2; defer to V3.

2. **V2 Token System Design** — Complete technical spec. Vocabulary: 7 core tokens (YYYY, YY, MM, DD, hh, mm, channel) + 3 optional. Settings: 4 new format string fields per strategy (sports_season_format, sports_episode_format, news_season_format, news_episode_format). Fallback chain: TV parses episodes; Sports/News generate from templates. Validation: load-time check + runtime graceful failure.

**Key Decisions:**
- Per-strategy format strings (4 settings), not global
- Numeric channel requirement; silently omit non-numeric IDs
- Simplified fallback: no middle steps, no external lookups
- Compatible with V1 TV enrichment; content classification abstraction needed

**Implementation Readiness:** Spec complete. Blair can code directly. Tests needed for token resolution, validation, graceful failures.

**Impact:** V2 scope locked. Ready for sprint planning and implementation.

**Approved by:** Dennis, Jo  
**Date:** 2026-02-28  
**Status:** ACTIVE — Ready for development

---

## Session 5: onscreen_episode Season Prefix Fix

### 2026-02-28T19:45Z: Decision — onscreen_episode Format for Generated Sports/News Episodes

**By:** Blair (Backend Dev)  
**Status:** ACTIVE

**Decision:** When `enrich_programme()` generates season+episode from format templates (the `else` branch for sports and news), it MUST also write `onscreen_episode` so the season is visible in Dispatcharr's display.

**Format:** `S{season}E{episode}` — e.g. `S2026E0315193042`

- Season is the integer value from the format string (no zero-padding).
- Episode is the raw format string output (string).
- If season conversion to int failed (try/except silently skipped), write `onscreen_episode` as the episode string alone.
- Do NOT write `onscreen_episode` in the `if existing_season and existing_episode` branch (EPG already has it).

**Rationale:** The V1 TV path preserves `onscreen_episode` from EPG because Dispatcharr uses it for display. Without `onscreen_episode` in the sports/news generated path, the season (e.g. 2026) was never visible to users — only the raw episode string appeared. The `S{season}E{episode}` format matches Plex DVR S/E notation and is consistent with how V1 stores TV episodes.

**Scope:** Only the `else` branches in `enrich_programme()` (sports and news). No change to the `if existing_season and existing_episode` path. No change to TV enrichment.

---

### 2026-02-28T20:15Z: Diagnosis — onscreen Episode-Num Missing Season Prefix

**By:** Blair (Backend Dev)  
**Triggered by:** Dennis showing live EPG output with `E03011800` instead of `S2026E03011800`

**Symptom:**
```xml
<episode-num system="onscreen">E03011800</episode-num>
<episode-num system="xmltv_ns">2025.3011799.</episode-num>
```

Season IS present in `xmltv_ns` (2025 = 2026−1, zero-indexed). Season is NOT in `onscreen`.

**Root Cause:** The fix only runs in the `else` (first-time generation) path. The **`if existing_season and existing_episode` branch** (lines 199–201 for sports, 217–219 for news) copies season+episode but **never sets `onscreen_episode`**. Programmes enriched before the onscreen_episode fix was applied and later re-run with existing season+episode get stuck in the `if` branch and never reach the `else` where `onscreen_episode` is generated.

**Recommended Action:** Patch lines 199–201 and 217–219 in `plugin.py`. Add:
```python
if not custom_props.get('onscreen_episode'):
    changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
```

The guard prevents overwriting a legitimately set onscreen string.

---

### 2026-02-28T20:45Z: Code Review — onscreen_episode Season Prefix Fix

**By:** Jo (Tech Lead)  
**Status:** ✅ APPROVED

**Verdict:** Fix is correct, surgical, and tests cover the critical paths.

**Key Findings:**
- Generated path writes onscreen_episode ✅ (lines 202–211 sports, 220–229 news)
- Existing EPG branch untouched ✅ (lines 199–201 sports, 217–219 news)
- TV path untouched ✅ (lines 231–244)
- Format consistent with Plex DVR ✅ (`S{season}E{episode}`)
- Tests exercise key behaviors ✅ (all 4 pass, full suite 67 passed / 11 skipped)

**Non-Blocking Gaps (Note for Future):**
- No `test_news_existing_epg_preserves_onscreen_episode` — implicit coverage by code symmetry, but worth adding
- Weak assertion in `test_sports_season_format_failure_writes_episode_no_crash` — should assert `onscreen_episode` IS present, not just permissively check

**All Gate Criteria Met:** Fix correct, targeted, existing/TV paths untouched, format consistent, tests pass.

---

### 2026-02-28T20:58Z: Smoke Test Report — onscreen_episode Season Fix (v2.0.1)

**By:** Mrs. Garrett (Deploy Manager)  
**Date:** 2026-02-28  
**Plugin version deployed:** 2.0.1  

**Deploy Result:** ✅ Enabled, reloaded, 3,105 programmes enriched, 0 errors

| Metric | Value |
|--------|-------|
| Total programmes | 3,118 |
| **Enriched** | **3,105** |
| Skipped | 13 |
| **Errors** | **0** |

**Status at time:** Stats identical to prior V2 run — confirms no regression. 0 errors means code executed without exceptions.

**Note:** This smoke test used metrics as proxy (0 errors) without directly verifying the `onscreen_episode` field value. See v2.0.2 smoke test for proper database verification.

---

### 2026-02-28T21:10Z: Smoke Test Gap Analysis — onscreen_episode Season Fix

**By:** Mrs. Garrett (Deploy Manager)  
**Finding:** v2.0.1 smoke test was incomplete. Used statistics as proxy without verifying the actual `onscreen_episode` field format.

**Root Cause:** Dispatcharr REST API does not expose `custom_properties`. Rather than defer, accepted 0-error count as proof. Statistics cannot prove a data format fix works — only the actual data can.

**Recommended Procedure for Future:** Query live database after deployment to inspect `onscreen_episode` field. Pull 5 programmes from enriched batch. Verify season prefix present in all samples. Only mark PASS if data verified.

---

### 2026-02-28T21:25Z: v2.0.2 Deploy Smoke Test — Proper Database Verification

**By:** Mrs. Garrett (Deploy Manager)  
**Date:** 2026-02-28  
**Status:** ✅ PASS — onscreen_episode season prefix VERIFIED

**Deploy:** Deployed epg-enricharr v2.0.2. Enrichment ran: 3,105 programmes enriched, 0 errors.

**Database Verification (PostgreSQL):**
```sql
SELECT COUNT(*) as total_with_onscreen,
       COUNT(CASE WHEN custom_properties->>'onscreen_episode' LIKE 'S%' THEN 1 END) as has_season_prefix
FROM epg_programdata
WHERE custom_properties->>'onscreen_episode' IS NOT NULL;

Result: 1786 total, 1786 with season prefix (100%)
```

**Sample Data:**
```json
{
  "season": 2026,
  "episode": "02271930",
  "onscreen_episode": "S2026E02271930",
  "previously_shown": true
}
```

**Verdict:** ✅ PASS — ALL 1786 records show `S2026E...` format. 0 bare episodes. Fix is confirmed working in production.

---

## Session 6: Test Gap Closure

### 2026-02-28T21:41:14Z: Test Gap Closure — Two Tests Filled

**By:** Tootie (Test Engineer)  
**Status:** ✅ RESOLVED

**What Changed:**
1. **New test added:** `test_news_existing_epg_preserves_onscreen_episode` — Establishes that news programmes with existing `season + episode + onscreen_episode` do NOT get `onscreen_episode` overwritten. Mirrors the sports parity test.
2. **Existing test strengthened:** `test_sports_season_format_failure_writes_episode_no_crash` — Changed from permissive `if 'onscreen_episode' in changes: assert changes['onscreen_episode']` to unconditional `assert 'onscreen_episode' in changes` + `assert changes['onscreen_episode'] == '03151930'`.

**Key Behavioural Fact Confirmed:** When `sports_season_format` produces a non-int-convertible value (e.g. `'{hh}:{mm}'` → `'19:30'`), the plugin's else-branch always writes `onscreen_episode = episode` (episode-only fallback, no `S{season}E` prefix). This is now contractually tested.

**Test Results:** No code changes to `plugin.py`. Tests only. All 73 tests pass (11 skipped unchanged).

---

### 2026-02-28T21:41:14Z: Test Gap Review — Tootie's Closure Approved

**By:** Jo (Tech Lead)  
**Status:** ✅ APPROVED

**Verdict:** Both tests are correct, specific, and production-ready. No further changes required.

**Review Findings:**
- `test_news_existing_epg_preserves_onscreen_episode`: Correctly mirrors sports version. Assertion pattern correct.
- `test_sports_season_format_failure_writes_episode_no_crash`: Strengthened to unconditional, specific assertions. Value `'03151930'` correctly derived.
- All 17 `TestEnrichProgrammeV2` tests pass (17/17)
- Full suite: 73 passed / 0 failed / 11 skipped

**Gate Criteria Met:** Tests match gap scenarios, assertions specific, no regressions, ready for production.
