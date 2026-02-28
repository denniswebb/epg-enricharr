### 2026-02-28T04:29:15Z: Plugin enable via API

**By:** Dennis (via Copilot)

**What:** Enable plugin via API instead of UI. POST to `/api/plugins/plugins/{plugin-id}/enabled/` with payload `{"enabled":true}`. Endpoint requires Authorization bearer token and proper headers.

**Why:** Automate full deployment pipeline. Future runs can enable plugin without manual UI interaction.

**Impact:** Mrs. Garrett to add `enable-plugin` task to mise. Endpoint: `http://{DISPATCHARR_HOST}/api/plugins/plugins/epg-enricharr-1_0_0/enabled/`
