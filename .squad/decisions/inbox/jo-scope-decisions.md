# Jo — Scope Decisions

### 2025-02-27T21:50: Scope Decision — MVP Definition

**Decision:** MVP ships with TV show enrichment only. Sports enrichment is V2.

**Rationale:** TV shows (parsing S2E36 → season/episode) solve 80% of Plex DVR issues and have clearer success criteria. Sports (year-based seasons, ordinal numbering) require domain knowledge for each sport and complex validation. Shipping TV enrichment fast unblocks users immediately.

**Impact:** Blair focuses on TV parsing first. Tootie tests TV-only scenarios. Sports settings can be stubbed (disabled by default) for future work.

---

### 2025-02-27T21:50: Scope Decision — Plugin Settings Defaults

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

### 2025-02-27T21:50: Scope Decision — Test Strategy

**Decision:** Three-layer testing:
1. **Unit tests** (Blair/Tootie): Test parsing logic in isolation (onscreen_episode → season/episode, previously-shown detection)
2. **Integration tests** (Mrs. Garrett): Plugin loads in local Dispatcharr, processes test ProgramData fixtures
3. **Manual validation** (Dennis): Install zip on real Dispatcharr, verify XMLTV output includes `<episode-num system="xmltv_ns">`

**Rationale:** Unit tests catch logic bugs fast. Integration tests prove plugin system compatibility. Manual validation confirms Plex actually recognizes the output. All three layers are needed for production confidence.

**Impact:** Tootie writes pytest unit tests alongside Blair's code. Mrs. Garrett sets up local Dispatcharr container + test data loader. Dennis runs final smoke test before release.

---

### 2025-02-27T21:50: Scope Decision — Out of Scope

**Decision:** The following are explicitly OUT:
- DVR recording filenames (Plex handles this)
- Plex metadata agents (we only enrich XMLTV)
- Retroactive enrichment of old ProgramData (plugin only processes new EPG refreshes)
- Custom category mapping UI (text config only)
- Multi-language support (English-only for MVP)

**Rationale:** Each of these requires integration with systems we don't own or scope creep into UX territory. The plugin solves one problem well: enriching custom_properties when EPG data arrives.

**Impact:** Natalie documents these non-goals in README. Blair can reject feature requests outside this scope.

---

## Quality Bar for "Done"

### Plugin is shippable when:

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

### Not required for V1:
- Sports enrichment
- Performance optimization beyond basic bulk updates
- Admin UI for settings
- Localization

---

**Approved by:** Jo  
**Date:** 2025-02-27  
**Status:** ACTIVE — Team can proceed
