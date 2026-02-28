# Decision: onscreen_episode Format for Generated Sports/News Episodes

**By:** Blair (Backend Dev)  
**Date:** Session 5  
**Status:** ACTIVE

## Decision

When `enrich_programme()` generates season+episode from format templates (the `else` branch for sports and news), it MUST also write `onscreen_episode` so the season is visible in Dispatcharr's display.

**Format:** `S{season}E{episode}` — e.g. `S2026E0315193042`

- Season is the integer value from the format string (no zero-padding).
- Episode is the raw format string output (string).
- If season conversion to int failed (try/except silently skipped), write `onscreen_episode` as the episode string alone.
- Do NOT write `onscreen_episode` in the `if existing_season and existing_episode` branch (EPG already has it).

## Rationale

The V1 TV path preserves `onscreen_episode` from EPG because Dispatcharr uses it for display. Without `onscreen_episode` in the sports/news generated path, the season (e.g. 2026) was never visible to users — only the raw episode string appeared. The `S{season}E{episode}` format matches Plex DVR S/E notation and is consistent with how V1 stores TV episodes.

## Scope

- Only the `else` branches in `enrich_programme()` (sports and news).
- No change to the `if existing_season and existing_episode` path.
- No change to TV enrichment.
