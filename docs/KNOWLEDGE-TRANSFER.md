# EPG-Enricharr: Knowledge Transfer

> Intended for incoming development team.

## Project Overview

**EPG-Enricharr** is a Dispatcharr plugin that enriches IPTV EPG data to enable Plex DVR recognition of TV shows, sports, and news programmes.

**The Problem:** Plex DVR needs `xmltv_ns` episode numbers (`<episode-num system="xmltv_ns">S02E36</episode-num>`) to recognize and organize shows. Many IPTV providers only supply generic programme titles without structured episode metadata. This plugin extracts or generates episode information from EPG data and writes it to the Dispatcharr database.

**Tech Stack:** Python 3.8+, Django ORM (via Dispatcharr plugin system), Dispatcharr 0.19.0+, Plex DVR integration via XMLTV.

**Data Flow:**
1. IPTV EPG imported to Dispatcharr as `ProgramData` records
2. Plugin processes each programme: extracts/generates episode metadata
3. Metadata stored in `ProgramData.custom_properties` (JSONField)
4. Dispatcharr XMLTV output generator reads custom_properties and populates `<episode-num>`, `<previously-shown>` tags
5. Plex DVR ingests XMLTV and recognizes series, organizes recordings

**Owner:** Dennis (user)  
**Current Version:** 3.0.0 (V3 sports title grouping implemented and tested)  
**Test Status:** 85 passing, 11 skipped (V2 integration stubs)

---

## Architecture & Design Decisions

### V1: TV Show Enrichment (MVP, COMPLETE)

**Scope Decision:** MVP ships with TV-only enrichment. TV shows solve 80% of use cases; sports/news are V2+ due to higher complexity and domain-specific rules.

**Episode Parsing (Core Algorithm)**
- Regex-based parser recognizing multiple formats: `S2E36`, `S01E05`, `s10e99`, `2x36`, `10X99`
- Returns 1-based integer tuple `(season, episode)` or None
- Validation: season > 0, episode > 0 (rejects S0E0 edge cases)
- Uses `.search()` not `.match()` to handle embedded strings ("Title - S2E36 - Description")
- **Key code:** `plugin.py` lines ~60-100

**Configuration Defaults**
- `enable_tv_enrichment: true` (enabled by default)
- `tv_categories: ["Movies", "Series", "Sports"]` (broad initial match)
- `enable_sports_enrichment: false` (V2, off by default)
- `enable_news_enrichment: false` (V2, off by default)
- `auto_mark_previously_shown: true` (prevents false "New" flags in Plex)
- `dry_run_mode: false` (production-ready, active on install)

**Previously-Shown Logic**
- Non-new content flagged with `previously_shown: true` in custom_properties
- Prevents Plex DVR from treating every airing as a new recording opportunity
- Logic: if `custom_properties.get('new')` is not True, set `previously_shown: true`

**Data Structure**
- Field name is `categories` (plural), not `category` (singular) — matches Dispatcharr API
- Type: list of strings from `<category>` XML elements
- Example: `custom_properties['categories'] = ['Series', 'Comedy']`

---

### V2: Sports & News Enrichment (IMPLEMENTED)

**Scope Decision:** For non-scripted content (sports, news) where episode parsing fails, generate season/episode from date/time tokens using configurable format strings.

**Format String System (7 Core Tokens)**
- `{YYYY}` — 4-digit year
- `{YY}` — 2-digit year
- `{MM}` — Month (01-12)
- `{DD}` — Day (01-31)
- `{hh}` — Hour (00-23)
- `{mm}` — Minute (00-59)
- `{channel}` — Channel ID (numeric only; non-numeric silently omitted)

**Example Templates**
- Sports: season = `{YYYY}`, episode = `{MMDDhhmm}` (e.g., S2026E03151930)
- News: season = `{YYYY}`, episode = `{MMDD}` (e.g., S2026E0315)

**Content Classification (Routing)**
- `classify_programme()` routes content to correct enrichment strategy
- Pattern matching: applied to joined `categories + title` fields
- Precedence order: Movie → Sports → News → TV
- Patterns configured in plugin.json with regex validation at init

**Enrichment Strategy (Fallback Chain)**
1. **Both season + episode exist in EPG** → use as-is, no generation
2. **Missing one or both** → generate from format string templates
3. **TV path** → use V1 episode parsing (no generation)
4. **Error handling** → invalid regex patterns logged, skipped, no crash

**onscreen_episode Field**
- XMLTV output reads `custom_properties['onscreen_episode']` for display title
- Dispatcharr falls back to `E{episode}` if `onscreen_episode` absent
- Format: `S{season}E{episode}` (e.g., `S2026E03151930`)
- **Critical:** Must write `onscreen_episode` in both generated AND existing-EPG branches

---

### V3: Sports Title Grouping (IMPLEMENTED)

**Problem:** Plex groups shows by XMLTV `<title>` value. Sports broadcasts have full descriptive titles ("AFL : Fremantle v Adelaide") that prevent grouping all matches under a single series.

**Solution:** Regex-based title extraction with configurable capture groups, enabled as opt-in feature.

**Pattern Format**
- Capture group 1: sport name (required) — e.g., "AFL"
- Capture group 2: match description (optional) — e.g., "Fremantle v Adelaide"
- First match wins (iterate patterns in order, stop at first success)
- Invalid regex patterns logged, skipped, no crash

**Example Configuration**
```json
{
  "enable_sports_title_grouping": true,
  "sports_title_patterns": [
    "^(AFL).*:\\s*(.+)$",
    "^(NRL).*:\\s*(.+)$",
    "^([A-Za-z\\s-]+)\\s*:\\s*\\1\\s*:\\s*(.+)$"
  ]
}
```

**Transformation**
- Input: `"AFL : Fremantle v Adelaide"`
- Output: 
  - `programme.title` → `"AFL"` (used by Plex for grouping)
  - `custom_properties.original_title` → `"AFL : Fremantle v Adelaide"` (preserved for recovery)
  - `custom_properties.title_subtitle` → `"Fremantle v Adelaide"` (match description)

**Architecture Pattern**
- Uses `_title` (leading underscore) convention in changes dict to signal model field mutation
- Separate from sports season/episode enrichment (independent feature flags)
- Conditional bulk_update fields: only includes 'title' if ANY programme needs mutation

**Edge Cases Handled**
- No pattern match → Title unchanged (passthrough)
- Feature disabled or patterns empty → No mutation
- Invalid regex → Logged and skipped, no crash
- Empty capture group → Rejected, tries next pattern
- Missing capture group 2 → Subtitle not set (optional)

---

## Current State & What Was Being Worked On

**Status:** V3 sports title grouping COMPLETE ✅ Ready for local testing with real EPG data

**Latest Work Session (2026-03-02):**
- Blair: Implemented regex pattern matching, `_extract_sports_title_and_subtitle()` method, bulk update optimization
- Tootie: Wrote 12 comprehensive tests (happy path, edge cases, regressions) — all passing
- Test Results: 85 passing, 11 skipped (V2 integration stubs), zero regressions

**Next Actions (in priority order)**
1. **Local Testing** — Deploy to test Dispatcharr, verify Plex grouping behavior with real EPG data
   - Test pattern matching against actual AFL/NRL titles
   - Verify original title recovery in custom_properties
   - Check Plex series grouping works as expected
   
2. **Documentation** — Update README with pattern examples (AFL, NRL, A-League)

3. **Version Bump** — Release as v3.0.0 (semantic versioning for V3 feature)

4. **Production Release** — Deploy to live environment

**Current Plugin Version:** 3.0.0 (V1 + V2 + V3, V3 awaiting deployment)  
**Known Production Baseline:** 
- 73 tests passing (V1 + V2)
- v2.0.2 deployed and verified
- Live enrichment run: 2951 programmes enriched, 167 skipped, 0 errors

---

## Key Technical Patterns & Learnings

### Episode Parsing (V1)

**Regex Pattern Strategy**
```python
EPISODE_PATTERNS = [
    re.compile(r'[Ss](\d+)[Ee](\d+)'),  # S2E36, s02e05
    re.compile(r'(\d+)[xX](\d+)'),       # 2x36, 02x05
]

def parse_episode_string(episode_str: str) -> Optional[Tuple[int, int]]:
    if not episode_str or not isinstance(episode_str, str):
        return None
    
    episode_str = episode_str.strip()
    
    for pattern in EPISODE_PATTERNS:
        match = pattern.search(episode_str)  # Use .search(), not .match()
        if match:
            try:
                season = int(match.group(1))
                episode = int(match.group(2))
                if season > 0 and episode > 0:  # Reject zeros
                    return (season, episode)
            except (ValueError, IndexError):
                continue
    
    return None
```

**Key Design Choices**
- Use `.search()` not `.match()` — handles embedded strings
- Iterate patterns in order — more specific first
- Validate season, episode > 0 — rejects S0E0 edge cases
- Return None for invalid input — explicit error handling
- Strip whitespace before parsing

**Anti-Patterns to Avoid**
- ❌ `.match()` — misses embedded episode strings
- ❌ Skip zero validation — breaks Plex DVR
- ❌ Raise exceptions on invalid input — breaks bulk processing
- ❌ Single format only — need multiple patterns

---

### Django Integration Patterns

**ProgramData Model & Custom Properties**
- `custom_properties` is a JSONField (JSONB in PostgreSQL)
- Directly mutable in Python: `prog.custom_properties['season'] = 2`
- Bulk updates efficient: `ProgramData.objects.bulk_update(programmes, batch_size=1000)`
- **Critical:** Use `select_related('epg')` to reduce query count when iterating

**Bulk Update Pattern**
```python
programmes_to_update = []
for prog in ProgramData.objects.select_related('epg'):
    changes = enrich_programme(prog)
    if changes:
        for key, value in changes.items():
            if key.startswith('_'):  # Model field
                setattr(prog, key[1:], value)
            else:  # custom_properties field
                prog.custom_properties[key] = value
        programmes_to_update.append(prog)

if programmes_to_update:
    update_fields = ['custom_properties']
    if any('_title' in p.custom_properties for p in programmes_to_update):
        update_fields.append('title')
    ProgramData.objects.bulk_update(programmes_to_update, update_fields, batch_size=1000)
```

**Field Naming Convention**
- Model fields: `_title`, `_subtitle` (leading underscore in changes dict)
- custom_properties fields: plain keys like `season`, `episode`, `original_title`
- Routes in `_enrich_all_programmes()`: `_` prefix stripped when writing to model field

**Late Model Import Pattern**
- Import models inside plugin methods, not at module level
- Allows testing plugin logic without full Django environment
- Example: `from apps.epg.models import ProgramData` inside `run()` method

---

### Content Classification & Routing

**Pattern Parsing & Validation (at init time)**
```python
def __init__(self, config=None):
    self.config = config or {}
    # Patterns compiled once at init, invalid ones logged and skipped
    self.movie_patterns = self._parse_patterns(
        self.config.get('movie_patterns', 'default_movie_patterns')
    )
```

**Classification Method**
```python
def classify_programme(programme):
    content = f"{' '.join(programme.custom_properties.get('categories', []))} {programme.title}".lower()
    for pattern in self.movie_patterns:
        if pattern.search(content):
            return 'movie'
    for pattern in self.sports_patterns:
        if pattern.search(content):
            return 'sports'
    # ... etc
    return 'tv'
```

**Key Learnings**
- Precedence matters: movie → sports → news → tv (specific to general)
- Join categories + title for pattern matching
- Case-insensitive matching (use `(?i)` in patterns)
- Invalid regex doesn't crash enrichment (pattern skipped, warned, continues)

---

### Data Verification Patterns

**Testing Strategy (Three Layers)**
1. **Unit tests** — Episode parsing, logic validation (no database)
2. **Integration tests** — Plugin loads in local Dispatcharr, processes test data
3. **Manual smoke test** — Real Dispatcharr instance, real EPG data

**Verification Failure Mode (Critical Lesson)**
- ❌ **Insufficient:** Check metric statistics (0 errors, X records enriched) — metrics can hide format bugs
- ✅ **Sufficient:** Query actual database for sample rows, verify field values in custom_properties
- Example: `SELECT custom_properties->>'onscreen_episode' FROM epg_programdata WHERE ... LIKE 'S%'` should be 100% formatted

**Mock Test Fixtures (MockProgramData)**
```python
class MockProgramData:
    def __init__(self, title='Test', categories=None, custom_properties=None):
        self.title = title
        self.custom_properties = custom_properties or {}
        self.start = datetime(2026, 3, 15, 19, 30)
        self.channel_id = 42
```

**Test Assertion Pattern for "Preserve" Tests**
```python
# Correct pattern — catches overwrites
assert programme.custom_properties.get('onscreen_episode', existing_value) == existing_value
```

---

### Dry-Run Mode Pattern

**Safety Feature for Configuration Testing**
- Feature flag: `dry_run_mode: true` skips database writes
- Returns enrichment stats dict showing what would have been changed
- Useful for validating configuration before applying to production

**Implementation**
```python
changes = {field: value for field, value in changes.items()}
if self.config.get('dry_run_mode'):
    # Skip bulk_update, return stats dict only
    return stats  # {'enriched': 123, 'skipped': 45, 'errors': 0}
else:
    ProgramData.objects.bulk_update(programmes, update_fields, batch_size=1000)
```

---

## Codebase Map

### Core Files

**`plugin.py` (Main Plugin Implementation)**
- `Plugin` class: Main entry point, matches Dispatcharr plugin system
- `fields` attribute: Plugin settings definitions (for Dispatcharr UI)
- `run()` method: Entry point called by Dispatcharr on EPG refresh
- `parse_episode_string(episode_str)` — Lines ~60-100: Regex-based parsing
- `classify_programme(programme)` — V2: Content type routing
- `format_string(template, programme)` — V2: Token resolution
- `enrich_programme(programme)` — Main enrichment logic (60+ lines)
  - TV path: Parse episode from onscreen_episode field
  - Sports path: Use existing or generate from format string
  - News path: Similar to sports with simpler format
  - V3 addition: Title grouping via `_extract_sports_title_and_subtitle()`
- `_extract_sports_title_and_subtitle(title)` — V3: Regex-based title extraction
- `_enrich_all_programmes()` — Bulk update orchestration

**`plugin.json` (Plugin Manifest & Settings)**
- `id`: "epg-enricharr"
- `version`: "3.0.0"
- `fields`: Array of plugin settings (enable/disable flags, format strings, patterns)
- **V1 fields:** `enable_tv_enrichment`, `tv_categories`, `auto_mark_previously_shown`, `dry_run_mode`
- **V2 fields:** `enable_sports_enrichment`, `enable_news_enrichment`, format string templates, category patterns
- **V3 fields:** `enable_sports_title_grouping`, `sports_title_patterns`

**`tests/test_enrichment.py` (Test Suite)**
- `MockProgramData` class: Fixture factory
- `TestEpisodeParsing` (15 tests) — V1 parsing validation
- `TestEnrichmentPlugin` (20 tests) — V1 enrichment logic
- `TestFormatString` (12 tests) — V2 token resolution
- `TestClassifyProgramme` (9 tests) — V2 content routing
- `TestEnrichProgrammeV2` (9 tests) — V2 enrichment paths
- `TestSportsTitleGrouping` (12 tests) — V3 title extraction
- **Status:** 85 passing, 11 skipped (integration stubs)

### Supporting Files

**`README.md`** — User documentation (installation, configuration, troubleshooting)
**`scripts/validate_output.py`** — Local XMLTV validation (no Dispatcharr needed)
**`validation.py`** — Plugin structure validator
**`mise.toml`** — Dev automation tasks
**`.env.example`** — Environment variables for local Dispatcharr access

---

## Outstanding Work / Known Issues

### Completed & Verified ✅
- V1 TV enrichment (MVP) — Live in production
- V2 sports/news enrichment — Live in production (v2.0.2)
- V3 sports title grouping — Implemented, tested, awaiting local validation

### In Progress 🔄
- **Local Testing:** Need to deploy V3 to Dennis's test Dispatcharr, verify Plex grouping works with real AFL/NRL/A-League EPG data
- **Documentation:** README needs V3 examples and pattern guide

### Future (V4+) 📋
- External API enrichment (TheSportsDB, TVDB) — V3+ scope
- Sequential episode numbering for sports (tracking game order within season)
- Multi-language episode string parsing
- Admin UI for pattern management
- Community pattern packs / shared rule repository

### Known Limitations
- Plugin can only modify `custom_properties` and model fields directly accessible in `_enrich_all_programmes()`
- Subtitle field (`sub_title`) cannot be populated via plugin (model field, not custom_properties)
- No Dispatcharr REST API access to custom_properties (must query database directly for verification)
- Pattern configuration requires regex knowledge from users (no UI builder)

---

## Recommendations for Incoming Team

### Development Workflow

1. **Local-First Testing**
   - Always run tests locally before pushing: `mise run test` or `pytest`
   - Use dry-run mode to validate configuration changes without database writes
   - Deploy to local Dispatcharr test instance to verify real XMLTV output

2. **Data Verification**
   - Don't trust metric statistics alone (0 errors, X enriched count)
   - Always sample actual database records to verify field values
   - Query Dispatcharr PostgreSQL directly: `docker exec Dispatcharr psql -U dispatch -d dispatcharr`

3. **Pattern & Regex Testing**
   - Test regex patterns with actual EPG data before committing
   - Use Python's `re.match()` interactively to validate captures
   - Remember: `.search()` vs `.match()` matters (search finds anywhere, match requires start of string)

4. **Bulk Operations**
   - Use batch_size=1000 for bulk_update (proven performance on 3000+ records)
   - Always use `select_related()` when iterating large datasets
   - Track actual error counts per-programme, don't rely on batch operation errors

### Architecture Decisions to Preserve

- **Three-layer testing:** Unit (fast, no deps) → Integration (local Dispatcharr) → Manual (real instance)
- **Dry-run mode:** Keep as first-line validation tool for any new enrichment feature
- **Feature flags:** Each major feature (TV, sports, news, title grouping) has its own enable flag
- **Late model imports:** Keep models imported inside plugin methods, not at module level
- **First-match-wins pattern matching:** Simpler than score-based ranking, matches user mental model
- **Custom properties JSON field:** Flexible, no schema migrations needed for new enrichment fields

### Common Gotchas to Avoid

1. **Field Names**
   - Use `categories` (plural), not `category` (singular)
   - Dispatcharr stores EPG category list under `categories` key in custom_properties

2. **Episode Parsing**
   - S0E0 is invalid (validated as season > 0, episode > 0)
   - Always handle malformed input gracefully (return None, don't raise)
   - `.search()` is correct for embedded episode strings

3. **Model Field Mutations**
   - Model fields in changes dict use `_` prefix convention (e.g., `_title`)
   - Must explicitly include model field names in bulk_update's `update_fields` list
   - Only conditional inclusion if ANY programme needs update (performance optimization)

4. **Dry-Run Mode**
   - Must work without database writes (no side effects)
   - Return stats dict showing what WOULD have been changed
   - Test both `dry_run=true` and `dry_run=false` scenarios

5. **Test Fixtures**
   - MockProgramData must include `start` datetime for sports path testing
   - Use fixed datetime `(2026, 3, 15, 19, 30)` to avoid test flakiness
   - Remember: categories is a list, not a string

### Adding New Features

**Template for V4+ enrichment strategies:**

1. Add feature flag to plugin.json (`enable_new_feature`)
2. Add pattern configuration to plugin.json (`new_feature_patterns`)
3. Update `classify_programme()` to recognize new content type
4. Add enrichment path in `enrich_programme()`:
   ```python
   elif content_type == 'new_feature' and self.config.get('enable_new_feature'):
       # enrichment logic
   ```
5. Update `_enrich_all_programmes()` to handle model field mutations if needed
6. Write test class with: happy path, edge cases, pattern validation, regressions
7. Test against real EPG data in local Dispatcharr before merging
8. Update README with examples and default patterns

### Code Review Checklist

- ✅ Tests pass locally (no failures, regression test coverage confirmed)
- ✅ Dry-run mode tested (works without database writes)
- ✅ Data verification done (sampled real database records, not just metrics)
- ✅ Backwards compatible (existing enrichment paths unaffected)
- ✅ Feature flag added (off by default for new features)
- ✅ Error handling graceful (invalid regex/data logged, doesn't crash)
- ✅ Pattern validation at init (not at runtime)
- ✅ Documentation updated (README with examples, docstrings in code)

---

## Quick Reference

**Plugin Entry Point:** `plugin.py` — `Plugin` class, `run()` method

**Key Methods:**
- `parse_episode_string(s)` — Regex parsing (S2E36 → (2, 36))
- `classify_programme(p)` — Detect content type (movie/sports/news/tv)
- `format_string(template, p)` — Token resolution ({YYYY}, {MM}, etc.)
- `enrich_programme(p)` — Main enrichment logic (returns changes dict)
- `_extract_sports_title_and_subtitle(title)` — Regex title extraction

**Configuration Keys:**
- `enable_tv_enrichment` (bool) — V1 TV parsing
- `enable_sports_enrichment` (bool) — V2 sports enrichment
- `enable_news_enrichment` (bool) — V2 news enrichment
- `enable_sports_title_grouping` (bool) — V3 title grouping
- `tv_categories` (list) — Categories to enrich
- `sports_title_patterns` (list) — Regex patterns for title splitting
- `dry_run_mode` (bool) — Test without database writes

**Custom Properties Keys Written by Plugin:**
- `season` (int) — Season number
- `episode` (str/int) — Episode number
- `onscreen_episode` (str) — Display format (S#E##)
- `previously_shown` (bool) — Non-new flag
- `original_title` (str) — Original title (V3 sports grouping)
- `title_subtitle` (str) — Match description (V3 sports grouping)

**Test Fixtures:**
- `MockProgramData` — Fake programme for unit tests

**Deployment:**
- `mis run test-zip` — Build plugin zip locally
- `mise run enable-plugin` — Deploy to test Dispatcharr
- `mise run reload-plugins` — Reload server
- Database check: `docker exec Dispatcharr psql -U dispatch -d dispatcharr`

---

## Session History Summary

**V1 (Feb 27–28):** Core TV enrichment implemented, tested, and verified. Import bug fixed, test suite enabled, 73 tests passing.

**V2 (Feb 28 – Mar 1):** Sports/news enrichment with format strings added. Classification routing, token resolution, fallback chains. Production deployed as v2.0.2. onscreen_episode edge cases fixed. 85 tests passing.

**V3 (Mar 1–2):** Sports title grouping architecture finalized (regex approach chosen). Implementation complete: pattern matching, title extraction, bulk update optimization. All 12 V3 tests passing. Ready for local validation.

---

*Last updated: 2026-03-02 (V3 implementation complete)*
