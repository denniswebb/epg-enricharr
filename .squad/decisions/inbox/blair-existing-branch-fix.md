# Blair — Existing Branch onscreen_episode Fix

**Date:** 2026-03-01  
**Author:** Blair (Backend Dev)  
**Status:** Applied ✅

## Problem

The `if existing_season and existing_episode` branches in `enrich_programme()` for both sports and news copied `season` and `episode` into `changes` but never set `onscreen_episode`. Programmes enriched before Session 5's `else`-branch fix had `season`+`episode` in `custom_properties` but no `onscreen_episode`. On re-run they hit the `if existing` branch and never reached the `else` where `onscreen_episode` is generated — permanently stuck producing `E{episode}` (no season prefix) from Dispatcharr's fallback.

## Fix

Added to both the sports and news `if existing_season and existing_episode` branches in `plugin.py`:

```python
if existing_season and existing_episode:
    changes['season'] = existing_season
    changes['episode'] = existing_episode
    if not custom_props.get('onscreen_episode'):
        changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
```

The `if not custom_props.get('onscreen_episode')` guard preserves any correctly-set value from a prior run — only fills the gap when absent.

## Test Result

67 pass, 11 skipped, 2 pre-existing failures (version string `2.0.0` vs `2.0.1`, unrelated). Zero regression.

## Files Changed

- `plugin.py` — sports `if existing` branch (line ~199) and news `if existing` branch (line ~217)
