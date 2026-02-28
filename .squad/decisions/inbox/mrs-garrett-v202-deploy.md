# v2.0.2 Deploy Smoke Test — Mrs. Garrett
**Date:** 2026-08-29  
**Requested by:** Dennis  
**Status:** ✅ PASS — onscreen_episode season prefix VERIFIED

---

## Summary

Deployed epg-enricharr v2.0.2 (Blair's `onscreen_episode` season-prefix fix) to production Dispatcharr at http://10.0.0.100:9191. This is a re-deploy of the same fix that v2.0.1 failed to prove — this time with actual database verification of the field value, not just stat counts.

---

## Step-by-Step Execution

### 1. Auth Check
- Token from `.env` tested: `GET /api/plugins/plugins/` → HTTP 200
- Token valid, no refresh needed

### 2. Version Bump
- `plugin.json` version: `2.0.1` → `2.0.2`

### 3. Build
```
mise run test-zip
✅ Plugin zip created: epg-enricharr-2.0.2.zip
```

### 4. Deploy (Import)
```
POST /api/plugins/plugins/import/  (multipart file upload)
Response: {"success": true, "plugin": {"key": "epg-enricharr", "version": "2.0.2", ...}}
```
Note: Dispatcharr assigned key `epg-enricharr` (no version suffix — new behavior as of Dispatcharr 0.19.0).

### 5. Enable Plugin
```
POST /api/plugins/plugins/epg-enricharr/enabled/  {"enabled": true}
Response: {"success": true, "enabled": true, "trusted": true, "loaded": true}
```

### 6. Disable old v2.0.1
```
POST /api/plugins/plugins/epg-enricharr-2_0_1/enabled/  {"enabled": false}
Response: {"success": true, "enabled": false}
```

### 7. Set Enrichment Flags
```
POST /api/plugins/plugins/epg-enricharr/settings/
{"settings": {"enable_sports_enrichment": true, "enable_news_enrichment": true}}
Response: {"success": true, "settings": {"enable_sports_enrichment": true, "enable_news_enrichment": true}}
```

**Verified via plugin list:**
- `enable_sports_enrichment`: true ✅
- `enable_news_enrichment`: true ✅
- `enabled`: true ✅
- `loaded`: true ✅

### 8. Reload Plugins
```
POST /api/plugins/plugins/reload/
Response: {"success": true, "count": 4}
```

### 9. Run Enrichment
```
POST /api/plugins/plugins/epg-enricharr/run/  {"action": "enrich_on_epg_refresh"}
Response: {
  "success": true,
  "result": {
    "status": "ok",
    "stats": {"total": 3118, "enriched": 3105, "skipped": 13, "errors": 0},
    "dry_run": false
  }
}
```

---

## ✅ ACTUAL VERIFICATION — Database Query

**Method:** SSH into Unraid host → `docker exec Dispatcharr psql -U dispatch -d dispatcharr`

**Table:** `public.epg_programdata`, column: `custom_properties` (jsonb)

### Sample Rows (sports + news)

```
title                                                          | onscreen_episode
---------------------------------------------------------------|------------------
Friday Night Football : Wolverhampton Wanderers v Aston Villa  | S2026E02271930
Sky Sports Tennis in HD on 508 from February 24               | S2026E02272200
Sky Sports News                                                | S2026E02280045
Sky Sports News                                                | S2026E02280100
HSBC Women's World Championship LPGA Golf : Day 3             | S2026E02280130
Sky Sports Breakfast                                           | S2026E02280700
Gillette Labs Soccer Saturday                                  | S2026E02281000
```

Full `custom_properties` example:
```json
{
  "season": 2026,
  "episode": "02271930",
  "onscreen_episode": "S2026E02271930",
  "previously_shown": true
}
```

### Format Verification
```sql
SELECT
  COUNT(*) as total_with_onscreen,
  COUNT(CASE WHEN custom_properties->>'onscreen_episode' LIKE 'S%' THEN 1 END) as has_season_prefix,
  COUNT(CASE WHEN custom_properties->>'onscreen_episode' NOT LIKE 'S%' THEN 1 END) as bare_episode
FROM epg_programdata
WHERE custom_properties->>'onscreen_episode' IS NOT NULL;

 total_with_onscreen | has_season_prefix | bare_episode
---------------------+-------------------+--------------
                1786 |              1786 |            0
```

**1786/1786 records with `S{year}E{episode}` format. 0 bare episodes.**

---

## Verdict

| Check | Result |
|-------|--------|
| Plugin loaded | ✅ trusted, loaded |
| Sports enrichment enabled | ✅ true |
| News enrichment enabled | ✅ true |
| Enrichment ran | ✅ 3105 enriched, 0 errors |
| `onscreen_episode` format | ✅ ALL 1786 are `S2026E...` |
| Bare `E...` format remaining | ✅ 0 |

## ✅ PASS — Blair's fix is confirmed working in production.

The `onscreen_episode` field now correctly writes `S2026E{MMDDHHII}` for sports and news programmes. The previous smoke test (v2.0.1) declared PASS without verifying this field; that failure mode cannot recur — this report contains actual sampled database output.
