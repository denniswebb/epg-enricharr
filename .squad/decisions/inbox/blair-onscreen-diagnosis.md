# Blair Diagnosis: onscreen Episode-Num Missing Season Prefix

**Date:** 2026-03-01  
**Author:** Blair (Backend Dev)  
**Triggered by:** Dennis showing live EPG output with `E03011800` instead of `S2026E03011800`

---

## Symptom

```xml
<episode-num system="onscreen">E03011800</episode-num>
<episode-num system="xmltv_ns">2025.3011799.</episode-num>
```

Season IS present in `xmltv_ns` (2025 = 2026−1, zero-indexed). Season is NOT in `onscreen`.

---

## Q1: Does the fix exist in plugin.py?

**YES** — The `onscreen_episode = f"S{season}E{episode}"` fix exists at lines 208–211 (sports) and 226–229 (news). BUT it only exists in the **`else` branch** (new generation path).

---

## Q2: Does Dispatcharr use `onscreen_episode` for the onscreen XML tag?

**YES** — Confirmed in `apps/output/views.py` (Dispatcharr/Dispatcharr repo):

```python
if "onscreen_episode" in custom_data:
    program_xml.append(f'    <episode-num system="onscreen">{html.escape(custom_data["onscreen_episode"])}</episode-num>')
elif "episode" in custom_data:
    program_xml.append(f'    <episode-num system="onscreen">E{custom_data["episode"]}</episode-num>')
```

- If `onscreen_episode` key exists → output verbatim (this is what we want: `S2026E03011800`)
- Else if `episode` key exists → prepend `E` with **no season** (this is what we're seeing: `E03011800`)

The real EPG output confirms the fallback (`elif episode`) was used, meaning `onscreen_episode` is **absent** from `custom_properties`.

---

## Root Cause: The Dead Zone in the `if existing` Branch

The fix only runs in the `else` (first-time generation) path. The **`if existing_season and existing_episode` branch** (lines 199–201 for sports, 217–219 for news) copies season+episode but **never sets `onscreen_episode`**:

```python
if existing_season and existing_episode:
    changes['season'] = existing_season
    changes['episode'] = existing_episode
    # ← NO onscreen_episode here! ← THE BUG
```

**Scenario that produces the bug:**
1. Programme first enriched by V2 code **before** the onscreen_episode fix was applied
2. `season=2026` and `episode="03011800"` written to DB — no `onscreen_episode`
3. Fix deployed; plugin re-runs
4. Programme now has `existing_season=2026` AND `existing_episode="03011800"` → truthy → takes the `if existing` branch
5. `else` branch with `onscreen_episode` assignment is **never reached**
6. Programme is permanently stuck with no `onscreen_episode`

`xmltv_ns` uses integer math on `season` and `episode` directly — that's why it works fine. `onscreen` requires the separate `onscreen_episode` key.

---

## Q3: What field SHOULD we be setting?

`custom_properties['onscreen_episode']` IS the correct field. Dispatcharr reads it directly and outputs it verbatim in `<episode-num system="onscreen">`. The field name and format (`S{season}E{episode}`) are correct.

---

## Q4: What needs to change?

The `if existing_season and existing_episode` branches in both sports and news must also synthesize `onscreen_episode` **when it is missing**:

### Sports branch (lines 199–201):
```python
# BEFORE (broken):
if existing_season and existing_episode:
    changes['season'] = existing_season
    changes['episode'] = existing_episode

# AFTER (fixed):
if existing_season and existing_episode:
    changes['season'] = existing_season
    changes['episode'] = existing_episode
    if not custom_props.get('onscreen_episode'):
        changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
```

### News branch (lines 217–219): same change.

The `if not custom_props.get('onscreen_episode')` guard prevents overwriting a legitimately set onscreen string (e.g. from an EPG source that provides its own display label).

---

## Summary Table

| Question | Answer |
|---|---|
| Fix exists in plugin.py? | Yes — but only in `else` (new generation) branch |
| Dispatcharr uses `onscreen_episode` for onscreen XML tag? | Yes — verbatim |
| What field to set? | `onscreen_episode` (already correct) |
| What's broken? | `if existing_season and existing_episode` branch never sets it |
| Affected programmes | Any programme enriched V2-style before the onscreen fix was applied |

---

## Recommended Action

Assign to Blair: patch lines 199–201 and 217–219 in `plugin.py`. Two-line addition per branch. Tests should cover the "re-enrichment of existing season+episode programme missing onscreen_episode" path.
