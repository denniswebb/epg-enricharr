# Session Log: Test Gaps Filled — News Preserve Test + Stronger Season Failure Assertion

**Date:** 2026-02-28T21:41:14Z  
**Summary:** Tootie filled two gaps flagged in Jo's Session 8 code review. News parity test added; sports failure assertion strengthened. All 17 V2 tests pass.

## Changes

1. **New test:** `test_news_existing_epg_preserves_onscreen_episode` — Verifies news programmes with existing season/episode/onscreen_episode are not overwritten.
2. **Strengthened test:** `test_sports_season_format_failure_writes_episode_no_crash` — Changed from permissive guard to unconditional specific assertions on `onscreen_episode` value.

## Results

- **Test count:** 73 total (17 V2 + 56 V1/utilities)
- **Pass rate:** 100% (73/73, 11 skipped)
- **Regressions:** 0

## Ready for Merge

Tests are production-ready. No code changes to `plugin.py` required.
