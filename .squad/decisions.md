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
