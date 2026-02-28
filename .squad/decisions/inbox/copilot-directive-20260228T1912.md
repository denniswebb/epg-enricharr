### 2026-02-28T19:12Z: User directive — done means deployed and tested

**By:** Dennis (via Copilot)
**What:** A task cannot be considered complete until it has been deployed to the real working server and verified with a real-world test. Passing unit tests alone does not constitute "done." The definition of done requires actual runtime validation against the live Dispatcharr instance.
**Why:** User request — V2 was marked complete based on unit tests only; no real deployment or smoke test was performed. This closes that gap permanently.
**Impact:** All agents (Blair, Tootie, Mrs. Garrett) must treat local unit test success as a necessary but insufficient condition for completion. Mrs. Garrett's deploy-and-smoke-test pipeline is a required step before any feature can be called done. Jo's approval gate must include confirmation that a real-world test was run, not just that tests passed.
