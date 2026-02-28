# EPG Enricharr Squad

## Project Context

**Owner:** Dennis  
**Project:** epg-enricharr  
**Stack:** Python, Django (Dispatcharr plugin)  
**Goal:** Enrich IPTV EPG data in Dispatcharr to enable Plex DVR recognition of TV shows and sports programmes.

## Members

| Name | Role | Focus | Badge |
|------|------|-------|-------|
| Jo | Lead | Scope, decisions, code review | 🏗️ |
| Blair | Backend Dev | Plugin core logic, enrichment algorithms | 🔧 |
| Tootie | Tester | Validation, test automation, quality gates | 🧪 |
| Natalie | Docs | README, setup guides, field descriptions | 📝 |
| Mrs. Garrett | DevOps (Local) | Local testing, plugin zip generation, dev tooling | ⚙️ |
| Mr. Belvedere | DevOps (CI/CD) | GitHub Actions, releases, artifact distribution | ⚙️ |
| Scribe | Session Logger | Memory, decisions, logs | 📋 |
| Ralph | Work Monitor | Work queue, backlog tracking | 🔄 |

## Design Principles

- **Self-validating:** All agents validate their work without manual intervention once pipelines are in place.
- **Local-first:** Agents test locally before pushing (zip validation, plugin installation to test Dispatcharr instance).
- **CI/CD-driven:** Release pipeline automates artifact generation and distribution.
