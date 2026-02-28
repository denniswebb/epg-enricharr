# Smoke Test Gap: onscreen_episode Season Fix (v2.0.1)

**Date:** 2026-02-28 (Post-Failure Investigation)  
**Agent:** Mrs. Garrett (Deploy Manager)  
**Issue:** v2.0.1 deployed and smoke tested, but the onscreen_episode season prefix fix was NOT actually verified in the EPG XML output.

---

## What Was Actually Tested

**Metrics only:**
- Enrichment API response: 3,105 programmes enriched, 13 skipped, 0 errors
- Statistics delta compared to prior V2 run: identical (no regression detected)
- Plugin load status via REST API: `trusted=true, loaded=true`

**What was NOT tested:**
- The actual EPG XML output from a programme's `custom_properties` field
- No direct inspection of the `onscreen_episode` field to verify `S{season}E{episode}` format
- No sample programme pulled from Dispatcharr and examined for the season prefix

---

## The Justification Used at the Time

From history.md, v2.0.1 smoke test:

> `custom_properties` are not exposed via REST API, so direct field inspection is not possible. The 0-error result with 3,105 enriched programmes is the canonical verification method.

**Honest assessment:** This was a cop-out. The lack of REST API exposure does NOT mean the field cannot be verified. It means I accepted a statistical proxy (`0 errors` + `enriched count`) as sufficient proof, when it is NOT sufficient for a data mutation fix.

---

## Why This Failed

1. **No proof that the fix executed:** 0 errors means "no exceptions," not "the format string worked as intended."
2. **No proof the format was applied:** Stats alone cannot distinguish between:
   - Code path A executes correctly: `S2026E03011800`
   - Code path B executes, but format fails silently: `E03011800` (season omitted)
   - Both result in 3,105 enriched programmes with 0 errors
3. **No sample validation:** One actual EPG programme with the season prefix in hand would have caught the regression immediately.

---

## What a Proper Smoke Test Should Include

### 1. Pull a Sample Programme from the Live EPG

After deployment and enrichment run:
```bash
# Get a sports or news programme from the enriched set
curl -s "http://10.0.0.100:9191/api/epg/programs/?category=Sports&limit=1" \
  -H "Authorization: Bearer $DISPATCHARR_TOKEN" | jq .
```

Extract the programme ID, then:

### 2. Query Dispatcharr's Plugin Management API

Dispatcharr may expose programme custom_properties via:
- `GET /api/epg/programs/{id}/` (check if custom_properties is in the response)
- `GET /api/plugins/plugins/epg-enricharr-2_0_1/status/` (check if plugin exposes enrichment results)
- Direct database query: SSHinto the Unraid host and query Dispatcharr's SQLite/Postgres DB:
  ```bash
  sqlite3 /path/to/dispatcharr/db.sqlite3 "SELECT custom_properties FROM epg_programme WHERE id=12345;"
  ```

### 3. Validate the Season Prefix in the XML

Once custom_properties is retrieved, parse it:
```python
import json
props = json.loads(custom_properties)
onscreen_episode = props.get("onscreen_episode")
# Should be: S2026E03011800 (or similar S{season}E{episode})
# NOT: E03011800 (season missing)
assert onscreen_episode.startswith("S"), f"Missing season prefix: {onscreen_episode}"
```

### 4. Spot-Check Multiple Programmes

Pull at least 3–5 sports and news programmes to ensure:
- Season is present in every `onscreen_episode`
- Format is consistent
- No edge cases (e.g., format string with bad syntax that silently fails)

---

## Proposed Procedure for Future Onscreen_episode Fixes

**Before deployment:**
1. Build the zip, deploy to staging Dispatcharr (or test instance)
2. Run a small enrichment job (10–20 programmes)
3. Query one sample programme directly (via DB or API)
4. Print its `onscreen_episode` field and verify it matches the expected format
5. Only then deploy to production

**After production deployment:**
1. Run the full enrichment job
2. Query 5 programmes (sports, news, mixed) from the enriched batch
3. Log their IDs and `onscreen_episode` values in the smoke test report
4. Include sample output: `"onscreen_episode": "S2026E03151930"` 
5. Mark as ✅ PASS only if all samples show the season prefix

---

## Root Cause

Dispatcharr's REST API does not expose `custom_properties` in list or detail endpoints. Rather than defer or escalate, I accepted statistics as a proxy. **Statistics cannot prove a data format fix works**. Only the actual data can.

This is the key lesson: **Verify the data, not the stats.**

---

## What Needs to Happen Now

1. Query the live Dispatcharr database or logs to inspect what `onscreen_episode` actually contains in a sports/news programme
2. If the fix is truly broken (season missing), roll back v2.0.1 or redeploy with the corrected code
3. Run a proper smoke test per the procedure above before re-deploying
4. Update this decision and history.md with the outcome

