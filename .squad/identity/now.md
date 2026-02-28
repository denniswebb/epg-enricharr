---
updated_at: 2026-02-28T22:16:56Z
focus_area: V3 sports title grouping architecture — pending Dennis approval
active_issues: []
---

# What We're Focused On

## Active Focus
**V3 sports title grouping — Jo's architecture decision pending user approval**

## Critical Decisions Waiting

**Dennis must approve:** Modify `programme.title` directly in plugin (scope expansion: enrichment → transformation). Jo's decision document includes 3-phase implementation spec and fallback options if rejected.

## Immediate Next Actions (in order)

1. **Dennis approval/rejection** — Review Jo's architecture decision (merged into decisions.md, Session 8 entry). Two paths:
   - **APPROVE:** Blair executes Phase 0–3 (subtitle field check, title splitting, model mutations, settings)
   - **REJECT:** Blair executes fallback plan (metadata-only enrichment + feature request to Dispatcharr)

2. **Blair Phase 0 (independent)** — Can proceed regardless of Phase 1–3 approval:
   - Verify `ProgramData` model has `subtitle` field
   - Check if Dispatcharr's XMLTV code maps `programme.subtitle` → `<sub-title>`
   - If both yes: document for future enhancement

3. **Session continuation** — Awaiting Dennis to review decision in decisions.md and provide go/no-go before Blair implements Phase 1–3

## Completed in Session 8

✅ Blair: XMLTV field mapping research complete — Findings: `sub_title` not mapped, `show_title`/`series_title` don't exist, no custom_properties hook for title override  
✅ Jo: V3 sports grouping architecture decision finalized — Option A (modify title) with full spec and fallback plan  
✅ Scribe: Decisions merged, logs written, inbox cleaned, blair history updated  

## Known V3 Candidates (Future Planning)

- Sports title grouping (core V3 — **IN PROGRESS, pending approval**)
- Better EPG descriptions for sports (future)
- Sequential episode numbering for sports (future)
- Multi-language episode string parsing (future)
- External API enrichment (V3 goal): TheSportsDB, TVDB

## Current State

- v2.0.2 live, 73 tests passing, live-verified
- V3 research complete, architecture decision ready for user sign-off
- Phase 0 ready to start; Phase 1–3 blocked on approval

## Process Notes

- Session memory captured in this file; fetch for next session context
- Conversational planning style: findings presented, then discuss with Dennis
- Definition of "done": deployed + real-world tested (not unit tests alone)
