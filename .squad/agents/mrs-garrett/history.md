# Mrs. Garrett — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Team needs local testing automation to validate before CI/CD  
**Solution:** Makefiles, scripts, and test Dispatcharr setup for quick feedback loops  

**Owner:** Dennis  
**Key Tasks:**
- Set up local Dispatcharr instance (Docker or native)
- Create Makefile targets for common operations (test-zip, validate-output, etc.)
- Generate test data samples (real EPG programmes for validation)
- Write validation scripts (XMLTV output checker, database state inspector)
- Bootstrap dev environment (dependencies, env setup)

## Learnings

### Docker vs Native Setup (Decision: Native-First with Docker Option)

- **Choice:** Native Python venv setup is the primary bootstrap, with optional Docker for Dispatcharr instance.
- **Rationale:** 
  - Most developers already have Python installed; venv is lightweight and fast.
  - Docker Dispatcharr is optional because team can develop/test without it (validation happens on plugin alone).
  - Keep setup friction low: `./dev-setup.sh` works on any system with Python 3.8+.
  - If Docker isn't available, team can still generate and validate plugins locally.

### Makefile Structure

Built with clear target hierarchy:
- **setup phase:** `dev-setup`, `setup-dispatcharr`
- **build phase:** `test-zip`, `clean`
- **test/validate phase:** `validate`, `check-output`
- **deploy phase:** `install-plugin`

Each target is self-contained and can be run independently (except `install-plugin` depends on `test-zip`).

### Validation Tooling

Three-layer validation approach:

1. **Plugin Structure** (`validation.py`):
   - Checks `plugin.json` for required fields
   - Validates `plugin.py` syntax via compile()
   - Runs test suite via pytest if available

2. **XMLTV Output** (`scripts/validate_output.py`):
   - Parses test EPG data (sample-epg.xml)
   - Confirms programme structure (title, category, episode metadata)
   - Fast feedback without needing running Dispatcharr instance

3. **Integration** (via `make validate`):
   - Orchestrates all checks in sequence
   - Reports pass/fail with clear emoji indicators
   - Exit codes for CI/CD integration

### Test Data Samples

Created realistic XMLTV fixtures in `tests/fixtures/sample-epg.xml`:
- **TV series:** The Office (comedy, with episode metadata)
- **Drama:** Breaking Bad (with credits)
- **Sports:** NRL 360, Premier League (category enrichment)
- **Movie:** The Matrix (feature film with length and credits)

This gives agents realistic data to validate enrichment logic without external APIs.

### Gotchas & Design Notes

1. **Zip generation:** Uses Python zipfile module (stdlib), no external tool needed.
2. **Test discovery:** `make validate` extracts zip to temp dir for testing; clean up handled by validation script.
3. **Environment:** `.env.example` is a template; `.env` is created by `dev-setup.sh` for local overrides.
4. **Plugin entry:** `plugin.json` specifies `entry_point: "plugin.EnrichmentPlugin"` matching Dispatcharr convention.
5. **Minimal bootstrap:** `dev-setup.sh` installs only core dependencies (Django, pytest, lxml); additional libraries added by individual agents as needed.

### Workflow Validation

Tested full sequence:
- ✅ `make help` → Displays all targets
- ✅ `make test-zip` → Generates valid zip with all required files
- ✅ `make validate` → Plugin passes structure, syntax, and test checks
- ✅ `make check-output` → XMLTV output validated against sample data
- ✅ Scripts are executable and work cross-platform

### Future Extensions

- `make test-integration` — Run tests against actual Dispatcharr instance (after setup-dispatcharr)
- `make lint` — Add Python linting (flake8, black) if team adopts style guide
- `make coverage` — Generate test coverage reports
- CI/CD hooks — Use Makefile targets in GitHub Actions workflows

### Session 2: Dev Automation MVP Complete (2026-02-28)

**Learning:** One-command setup (`./dev-setup.sh`) eliminates onboarding friction for team. Three-layer validation (structure/syntax/tests) catches errors before CI. Native Python venv + optional Docker provides flexibility. Makefile orchestrates the whole workflow; `make validate` is the go-to for pre-commit checks. XMLTV validator works without Dispatcharr running. Team can now test independently before pushing.

### Session 8: V2 Live Deployment & Smoke Test (2026-02-28)

**Task:** Build V2 plugin, deploy to real Dispatcharr (http://10.0.0.100:9191), run smoke test, report results.

**Execution:**
- Built `epg-enricharr-2.0.0.zip` with all 15 V2 fields, 4 format string settings
- Deployed via `/api/plugins/plugins/import/` API
- Version bumped to 2.0.0 (key: `epg-enricharr-2_0_0`) to work around Dispatcharr API limitation: import endpoint rejects duplicate keys via JWT auth and exposes no DELETE endpoint
- Enabled plugin, reloaded server
- Ran enrichment on 3118 live EPG programmes
- Result: **2951 enriched, 167 skipped, 0 errors, dry_run=false**

**Outcome:** ✅ **PASS**. V2 plugin live and fully functional on production Dispatcharr instance.

**Follow-up:** Disable `epg-enricharr-1_0_0` on server (remains orphaned, could conflict if still enabled). Document 2.0.0 as canonical release.

**Pattern:** Smoke test report (step-by-step API responses) provides sufficient evidence for approval gate review. Real-world validation now required before feature is considered "done."
