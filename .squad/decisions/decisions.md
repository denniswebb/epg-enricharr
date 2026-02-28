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
