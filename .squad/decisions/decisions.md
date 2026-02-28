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

### 2026-02-28T19: V2 sports/news enrichment approved

**By:** Blair (implementation), Tootie (testing), Jo (review)  
**What:** Implemented format_string() token formatter, classify_programme() content router, and enrich_programme() V2 logic with partial preservation for sports/news and configurable regex patterns. Added 9 new settings to plugin.json.  
**Format String Tokens:** `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{hh}`, `{mm}`, `{channel}` (non-numeric channels omitted silently)  
**Content Classification:** Movie → Sports → News → TV (default fallback), using regex patterns from plugin settings  
**Enrichment Logic:** Movies skip immediately, sports/news preserve existing season/episode when both present else regenerate from templates, TV uses V1 parse_episode_string path  
**Settings Added:** enable_news_enrichment (bool), sports_season_format, sports_episode_format, news_season_format, news_episode_format, movie_patterns, sports_patterns, news_patterns  
**Why:** Core V2 feature for dynamic enrichment based on programme type, with backward compatibility for V1 TV logic  
**Testing:** 30 new tests, 65 passing, 0 failed, 11 skipped  
**Verdict:** ✅ Approved by Jo, ready to merge
