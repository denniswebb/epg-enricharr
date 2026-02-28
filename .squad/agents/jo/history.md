# Jo — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Plex DVR doesn't recognize TV shows or sports from IPTV EPG — missing xmltv_ns episode numbering  
**Solution:** Plugin enriches ProgramData.custom_properties in the database with missing metadata  

**Team:** 8 members (6 cast + Scribe + Ralph)  
**Owner:** Dennis (user running the squad)  

## Learnings

### Session 1: Initial Scope Decisions (2025-02-27)

**Scope Clarifications:**
- User requirements were complete and well-defined — rare but appreciated
- MVP scoping: TV enrichment alone solves 80% of problem; sports adds complexity without proportional value
- Data flow was pre-validated by user (import → custom_properties → output generator) — no guesswork needed

**Patterns Noticed:**
- Three-layer test strategy (unit/integration/manual) maps cleanly to team roles: Tootie (unit), Mrs. Garrett (integration), Dennis (manual)
- "Previously shown" flag is critical but easy to overlook — prevents false "New" recordings in Plex
- Plugin settings defaults should be production-ready (dry_run: false), not dev-mode (dry_run: true)

**Architectural Insights:**
- Dispatcharr plugin system gives direct Django model access — simple, powerful, no API layer
- Bulk updates via Django .update() are essential for performance (EPG refresh = thousands of programs)
- Output generator already checks for season/episode keys — our job is purely data enrichment, not format changes

**Team Dynamics:**
- Decisions recorded before work starts = team can parallelize without blocking on me
- Mrs. Garrett's local Dispatcharr setup is critical path — integration tests need it
- Blair can reject scope creep using documented out-of-scope list

### Session 2: Orchestration & Decision Finalization (2026-02-28)

**Learning:** Clear scope decisions delivered to inbox; team executed in parallel without rework. All four agents (Blair, Tootie, Mrs. Garrett, me) completed first batch: plugin implemented, tests passing, local dev automation ready. Scope boundaries (no sports, no UI, no retroactive enrichment) prevented team from overbuilding. Next work batch can start immediately from here.

### Session 3: V1 Quality Bar Assessment (2026-02-28)

**Critical Finding:** Test suite has import mismatch. Tests import `EnrichmentPlugin` but plugin.py defines `Plugin`. This is a blocking bug—tests cannot run. Blair and Tootie's work is otherwise solid, but this name mismatch invalidates the "tests passing" claim from Session 2.

**Architecture is Sound:** Plugin code is production-quality—parsing logic, bulk operations, dry-run mode, category filtering all implemented correctly. Original intention (enrich IPTV EPG for Plex DVR) is perfectly in focus.

**Gaps Against Quality Bar:**
1. **TESTED:** Import bug blocks all tests; 80%+ coverage claim unverifiable until fixed
2. **PACKAGED:** CI/CD workflows exist but are TODO skeletons—no builds, no tests, no releases
3. **Safe/Functional:** Code looks correct but cannot be validated without working tests

**What's Actually Done:** README (excellent), plugin.json (complete), plugin.py (solid implementation), mise.toml (good automation), test suite (well-designed but broken import).

**Shippable Blockers:** Fix test import, configure CI to run tests, add GitHub release automation. Estimated 2-3 hours of focused work to cross V1 finish line.

### Session 4: V2 Scope Discussion — Expanding Beyond TV (2025-02-28)

**Context:** Dennis proposed expanding plugin to handle sports (AFL/NRL), news, and other non-scripted content. Wants everything DVR'd to have season/episode structure.

**Architectural Decisions:**

1. **Sports episode ID model:** Dennis proposed `MMDDHHmm + channel`. Analysis: solid foundation but needs refinement. Recommended `YYYYMMDDHHMM` with optional channel suffix. Key insight: channel numbers can change in IPTV, so they shouldn't be primary key — only collision tiebreaker.

2. **Regex-based routing:** Approved as V2 scope. Right abstraction level — extends existing category filtering. Risk: regex fragility requires good defaults and dry-run preview. Settings may need JSON encoding in text field (plugin.json limitation).

3. **External data sources:** Deferred to V3. High complexity-to-value ratio for a plugin that runs on EPG refresh. Latency and reliability risks outweigh marginal metadata quality gains. V2 should work entirely offline.

4. **News/daily model:** Year-as-season + MMDD-as-episode is correct. Well-understood pattern that matches Plex's "daily" episode ordering.

5. **Architecture abstraction:** Current `enrich_programme()` needs strategy pattern. Proposed: `classify_content()` → `get_enrichment_strategy()` → `strategy.enrich()`. Keeps strategies testable in isolation, allows composition.

**V2 Scope (unit of work):**
- Regex-based content routing (local only)
- Sports strategy: year + MMDDHHMM
- Daily strategy: year + MMDD
- JSON-based content rules in settings
- Dry-run rule preview
- Backwards compatible with existing tv_categories

**Deferred to V3:**
- External API integrations (sports databases)
- Per-sport customization
- Rich metadata (team info, logos)
- Admin UI for rules
- Community rule packs

**Key Insight:** V2 value proposition is "organized DVR for everything" — season/episode presence matters more than metadata quality. Quality enrichment (round numbers, team names) is V3 polish.

### Session 5: V2 Token System Design (2025-02-28)

**Context:** Dennis requested Dispatcharr-style template tokens for configurable season/episode generation. User wants flexibility like `{YYYY}` vs `{YY}` for seasons, `{MMDDhhmm}{channel}` vs `{YYMMDDhhmm}` for episodes.

**Key Design Decisions:**

1. **Token vocabulary:** 7 core tokens (`{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{hh}`, `{mm}`, `{channel}`) + 3 optional. Excluded title/subtitle/sport tokens — those require parsing, not direct extraction. V2 tokens must be deterministic and fast.

2. **Per-strategy settings:** Each content type (sports, news) gets own format strings. 4 new settings total. Worth the complexity — sports needs timestamp precision + channel, news needs simpler date-only format.

3. **Fallback chain:** TV content continues parse-only (V1 behavior). Sports/News generate from templates. No middle step with external lookups — that's V3 scope.

4. **Validation strategy:** Validate format strings at load time (catch typos early). Runtime errors log warning and skip that programme — never crash bulk enrichment.

5. **Channel edge case:** Empty channel is valid (template produces usable result). Non-numeric channels log warning but don't block. Trust user's template.

**Architectural Insight:** Template system is pure string replacement followed by int conversion. No DSL, no conditionals, no expressions. Simplicity is the feature — users can understand `{MMDDhhmm}` without documentation.

**Plugin.json Limitation:** Only `text` and `boolean` types supported. Format strings work fine as text fields with good description strings explaining tokens.

**Spec delivered:** `.squad/decisions/inbox/jo-v2-token-system-design.md` — Blair can implement directly without further design discussion.

### Session 6: V2 Implementation Review (2025-07-22)

**Context:** Blair implemented 4 V2 features (format_string, classify_programme, enrichment routing, plugin.json settings). Tootie wrote 30 V2 tests across 3 test classes.

**Review Outcome:** ✅ APPROVED. All 5 review criteria passed. 65 tests passing, 0 failures.

**Key Observations:**
1. Token system is clean — pure string replacement, no DSL complexity. All 7 tokens resolve correctly.
2. Content classification with regex patterns is well-implemented — graceful invalid regex handling, correct precedence order.
3. Enrichment routing respects the "both exist → use as-is, missing → generate" rule from Dennis's directive.
4. V1 TV path (parse_episode_string) completely preserved — no regressions.
5. Feature flags (enable_sports_enrichment, enable_news_enrichment) properly gate their respective code paths.

**Minor gaps noted (non-blocking):** format_string with None start untested, start_time attribute fallback untested, nested channel.channel_id fallback untested. All are low-risk edge cases with correct code but no test coverage.

**Pattern confirmed:** Spec-first workflow continues to pay off. Clear decisions.md spec → implementation matches → tests validate → review is fast. No design ambiguity surfaced during review.

### Session 7: V2 Live Approval Gate (2026-02-28)

**Context:** Mrs. Garrett completed V2 deployment and smoke test against real Dispatcharr (http://10.0.0.100:9191). Reviewed full report against new "done = deployed + tested" standard.

**Verdict:** ✅ APPROVED — V2 is live and functional.

**All 9 checklist items passed:**
- All 4 V2 features deployed and confirmed (format_string, classify_programme, 15 fields, live enrichment run)
- Plugin deployed to real server, enabled, loaded (trusted=true post-reload)
- Enrichment ran on 3118 live EPG programmes: 2951 enriched, 167 skipped, 0 errors, dry_run=false

**One platform gap (non-blocking):** custom_properties not exposed in Dispatcharr REST API — enrichment correctness inferred from zero-error stats rather than direct field inspection. Accepted as platform limitation.

**Version bump decision:** 2.0.0 / key `epg-enricharr-2_0_0` is acceptable. Old `1_0_0` key remains on server — follow-up required to disable it and prevent dual-plugin conflicts. Team should standardise on 2_0_0 going forward.

**Pattern confirmed:** "Done = deployed + tested" standard worked cleanly. Smoke test report format (step-by-step with API responses) gives enough evidence to approve without being present during the run.

### Session 8: onscreen_episode Fix Review — Sports/News Generated Path (2026-02-28)

**Context:** Blair added `onscreen_episode` to the sports/news generated path (else branch) in `enrich_programme()`. Tootie added 4 targeted tests. Reviewed per Dennis's request.

**Verdict:** ✅ APPROVED

**What passed:**
1. `onscreen_episode` only written in generated path (else branch) — existing EPG path untouched
2. TV path untouched
3. Format `S{year}E{episode}` is correct Plex DVR notation; season-failure fallback (episode-only) is correct
4. All 4 new tests pass; full suite 67 pass / 2 pre-existing failures (unrelated version assertions) / 11 skipped

**Non-blocking gaps noted:**
- No `test_news_existing_epg_preserves_onscreen_episode` (news existing-EPG path not explicitly tested; symmetric code makes it low risk)
- `test_sports_season_format_failure_writes_episode_no_crash` has a permissive `if 'onscreen_episode' in changes:` guard — should assert presence unconditionally since the code always writes it in that path

**Pattern:** Blair's spec-first decision (`.squad/decisions/inbox/blair-onscreen-episode-season.md`) precisely matched the implementation — no ambiguity, fast review.
