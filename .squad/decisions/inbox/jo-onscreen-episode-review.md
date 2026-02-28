# Review: Blair's onscreen_episode Fix for Sports/News Generated Path

**By:** Jo (Tech Lead)  
**Date:** Session 8  
**Status:** ✅ APPROVED

## Verdict

**APPROVE** — Fix is correct, surgical, and tests cover the critical paths.

## Review Findings

### 1. Generated path writes onscreen_episode ✅
Lines 202-211 (sports) and 220-229 (news): `onscreen_episode` is written only in the `else` branch when both `existing_season` and `existing_episode` are absent. Correct.

### 2. Existing EPG branch untouched ✅
Lines 199-201 (sports) and 217-219 (news): `if existing_season and existing_episode` branch sets only `changes['season']` and `changes['episode']`. No `onscreen_episode` written. Correct.

### 3. TV path untouched ✅
Lines 231-244: TV enrichment unchanged. No regressions.

### 4. Format consistent with Plex DVR ✅
`f"S{changes['season']}E{changes['episode']}"` → e.g. `S2026E0315193042`.
Matches Plex DVR xmltv_ns S/E notation. Season-failure fallback writes episode-only string (no crash). Correct.

### 5. Tootie's tests ✅ (with caveats — see below)
- `test_sports_generated_path_writes_onscreen_episode`: Confirms onscreen_episode present and contains '2026'. Uses fixed datetime (2026-03-15 19:30), no live-date dependency. ✅
- `test_news_generated_path_writes_onscreen_episode`: Same pattern for news path. ✅
- `test_sports_existing_epg_preserves_onscreen_episode`: Verifies season/episode preserved from EPG; confirms onscreen_episode not regenerated. Assertion (`changes.get('onscreen_episode', existing_onscreen) == existing_onscreen`) is slightly loose — passes whether onscreen_episode absent OR equal to existing — but correctly validates the no-regeneration requirement. ✅
- `test_sports_season_format_failure_writes_episode_no_crash`: Confirms no crash and episode written when season int conversion fails. ✅

All 4 pass. Full suite: 67 passed / 2 pre-existing failures (version assertion mismatch, unrelated) / 11 skipped.

## Non-Blocking Gaps (Note for Future)

1. **No `test_news_existing_epg_preserves_onscreen_episode`**: The news existing-EPG branch is structurally identical to sports and is implicitly covered by code symmetry, but no explicit test exercises it. Low risk; worth adding in a follow-up.

2. **Weak assertion in `test_sports_season_format_failure_writes_episode_no_crash`**: Uses `if 'onscreen_episode' in changes:` (permissive — passes if absent). The code always writes `onscreen_episode` in the no-season path (line 211), so the test should assert it IS present. This is a test quality gap, not a code bug — the code is correct.

## All Gate Criteria Met

- Fix is correct and targeted ✅
- Existing EPG branch not touched ✅
- TV path not touched ✅
- Plex DVR format consistent ✅
- Tests exercise key behaviors ✅
