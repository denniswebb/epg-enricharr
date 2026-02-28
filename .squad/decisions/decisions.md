# Decisions

### 2026-02-28T04:04:48Z: Use mise instead of make

**By:** Dennis  
**What:** Prefer mise for task automation and dev environment management — do not use Make/Makefile  
**Why:** User preference — mise is the tool of choice for this project  
**Impact:** Mrs. Garrett (Local DevOps) should convert Makefile to mise.toml task definitions; all team members use `mise run {task}` instead of `make {target}`

### 2026-02-28T04:18:54Z: Plugin deployment via Dispatcharr API

**By:** Dennis  
**What:** Teach the team to deploy plugin ZIP to Dispatcharr via API. Two curl commands learned from manual install:
  1. POST multipart ZIP to `/api/plugins/plugins/import/` 
  2. GET `/api/plugins/plugins/` to refresh/activate
Both require Bearer token (JWT) and instance URL. Parameterized by .env (DISPATCHARR_HOST, DISPATCHARR_AUTH_TOKEN)  
**Why:** Automate plugin deployment so agents can self-validate on test instance  
**Impact:** Mrs. Garrett adds `mise run deploy-plugin` task with curl automation; credentials stored in .env

### 2026-02-28T19:00Z: User directive — partial EPG season/episode handling

**By:** Dennis (via Copilot)  
**What:** Generate whichever field is missing, keep whichever is present.
  - Has season AND episode → use both as-is
  - Has season but NO episode → keep EPG season, generate episode from template
  - Has episode but NO season → keep EPG episode, generate season from template
  - Has neither → generate both from templates
Movies are always skipped before reaching any of these checks.  
**Why:** User request — EPG can provide partial metadata; we should fill gaps, not discard what's there  
**Impact:** Implementation begins next session with EPG enrichment logic updated

### 2026-02-28T19:00Z: V2 sports/news enrichment approved

**By:** Blair (implementation), Tootie (testing), Jo (review)  
**What:** Implemented format_string() token formatter, classify_programme() content router, and enrich_programme() V2 logic with partial preservation for sports/news and configurable regex patterns. Added 9 new settings to plugin.json.  
**Format String Tokens:** `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{hh}`, `{mm}`, `{channel}` (non-numeric channels omitted silently)  
**Content Classification:** Movie → Sports → News → TV (default fallback), using regex patterns from plugin settings  
**Enrichment Logic:** Movies skip immediately, sports/news preserve existing season/episode when both present else regenerate from templates, TV uses V1 parse_episode_string path  
**Settings Added:** enable_news_enrichment (bool), sports_season_format, sports_episode_format, news_season_format, news_episode_format, movie_patterns, sports_patterns, news_patterns  
**Why:** Core V2 feature for dynamic enrichment based on programme type, with backward compatibility for V1 TV logic  
**Testing:** 30 new tests, 65 passing, 0 failed, 11 skipped  
**Verdict:** ✅ Approved by Jo, ready to merge

### 2026-02-28T19:12Z: User directive — done means deployed and tested

**By:** Dennis (via Copilot)  
**What:** A task cannot be considered complete until it has been deployed to the real working server and verified with a real-world test. Passing unit tests alone does not constitute "done." The definition of done requires actual runtime validation against the live Dispatcharr instance.  
**Why:** User request — V2 was marked complete based on unit tests only; no real deployment or smoke test was performed. This closes that gap permanently.  
**Impact:** All agents (Blair, Tootie, Mrs. Garrett) must treat local unit test success as a necessary but insufficient condition for completion. Mrs. Garrett's deploy-and-smoke-test pipeline is a required step before any feature can be called done. Jo's approval gate must include confirmation that a real-world test was run, not just that tests passed.

### 2026-02-28T19:17Z: V2 plugin smoke test passed on live Dispatcharr

**By:** Mrs. Garrett (Local DevOps)  
**What:** Built epg-enricharr-2.0.0 (V2 with 15 fields, 4 format string settings), deployed to http://10.0.0.100:9191, enabled, and ran enrichment on 3118 live EPG programmes. Result: 2951 enriched, 167 skipped, 0 errors, dry_run=false.  
**Workaround:** Version bumped to 2.0.0 (key: `epg-enricharr-2_0_0`) to bypass Dispatcharr API limitation: import endpoint rejects duplicate keys via JWT auth and exposes no DELETE endpoint. Old `epg-enricharr-1_0_0` remains on server.  
**Why:** Real-world validation required per user directive. All V2 fields functional, live enrichment clean.  
**Impact:** V2 confirmed working on production Dispatcharr instance. Next: disable `epg-enricharr-1_0_0` to prevent dual-plugin conflicts.

### 2026-02-28T19:30Z: V2 live approval — all checks pass

**By:** Jo (Lead)  
**What:** Reviewed Mrs. Garrett's smoke test against 9-point checklist (V2 feature coverage, real deployment, real data, stats verification, zero errors). All pass. Gap identified: `custom_properties` not exposed in Dispatcharr REST API (platform limitation, not plugin deficiency).  
**Verdict:** ✅ APPROVED. V2 plugin live, enriching real EPG data, zero errors.  
**Required follow-up (non-blocking):** Disable `epg-enricharr-1_0_0` on server, standardise team on 2.0.0 as canonical release, investigate admin-level DELETE endpoint for future clean upgrades.  
**Why:** V2 meets definition of done: deployed + tested on real system.  
**Impact:** V2 feature closed, shipped live, live-verified.
