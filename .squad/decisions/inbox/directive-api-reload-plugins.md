### 2026-02-28T04:34:49Z: Plugin reload endpoint for future automation

**By:** Dennis (via Copilot)

**What:** Reload/refresh the plugin system via API. POST to `/api/plugins/plugins/reload/` with Authorization bearer token. Triggers plugin system to reload all plugins (useful after config changes or when waiting for event-triggered actions).

**Why:** Automate full deployment pipeline including plugin refresh. This is separate from individual plugin enable — it's a system-wide reload.

**Impact:** Mrs. Garrett to add `reload-plugins` task to mise that calls this endpoint. Endpoint: `POST http://{DISPATCHARR_HOST}/api/plugins/plugins/reload/`
