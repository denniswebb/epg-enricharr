# Work Routing

## Primary Routing Table

| Task Type | Assignee | Notes |
|-----------|----------|-------|
| Architecture, scope, decisions | Jo (Lead) | Sync approval gate for major decisions |
| Plugin logic, enrichment code | Blair (Backend) | Standard: full context, decisions, history |
| Tests, validation, quality gates | Tootie (Tester) | Standard: reviewer role — can reject work |
| Documentation, guides, comments | Natalie (Docs) | Lightweight or Standard per scope |
| Local dev automation, test zips | Mrs. Garrett (DevOps Local) | Background: parallel with implementation |
| CI/CD, releases, distribution | Mr. Belvedere (DevOps CI/CD) | Background: activated post-implementation |
| Session logging, decision merging | Scribe | Background: always last in any fan-out |
| Work queue monitoring | Ralph | On-demand: "Ralph, go" to activate loop |

## Decision Gates

**Architecture / Scope Decisions** → Jo (sync) → Team approval before proceeding  
**Code Review / Quality** → Tootie (sync if rejecting) → Blocker for merge  
**Release / Distribution** → Mr. Belvedere (async) → Autonomous, reports outcomes

## Anticipatory Spawning

- Backend work → spawn Tootie (test cases) + Mrs. Garrett (local zip gen) in parallel
- Test completion → assess coverage, spawn follow-up if gaps found
- Implementation done → spawn Mr. Belvedere for CI/CD pipeline validation
- Any work batch → always spawn Scribe (background, last)
