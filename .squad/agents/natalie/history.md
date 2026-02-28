# Natalie — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Users need clear docs to understand and install the plugin  
**Solution:** Comprehensive README, setting descriptions, and architecture guide  

**Owner:** Dennis  
**Key Topics:**
- What the plugin does: enriches EPG data for Plex DVR
- Why: Plex needs xmltv_ns episode numbers, previously_shown flags, etc.
- How to install: plugin.json manifest, placement in /app/data/plugins/
- Settings: enable/disable by type, categories list, dry-run mode
- Examples: real EPG data transformations, before/after

## Learnings

### Session 1: Comprehensive README Documentation (2026-02-27)

**What was documented:**
- Complete README.md rewrite covering all 9 deliverables from the charter
- 353 lines of clear, user-focused documentation
- Emphasis on problem statement first (why users need this) before features

**Key patterns & decisions:**

1. **Architecture diagram first:** Visual flow (IPTV EPG → Plugin → DB → XMLTV → Plex) helps users understand what plugin does without diving into code.

2. **Problem-to-solution arc:** Lead with "What's broken in Plex?" then "How EPG Enricharr fixes it" builds context and authority. Users understand *why* before *how*.

3. **Installation branching:** Docker vs. Native — users typically run one or the other, so separate sections reduce cognitive load.

4. **Configuration table format:** Markdown table with Type, Default, Description for each setting is scannable and reference-friendly. Audience doesn't read top-to-bottom.

5. **Real examples over abstractions:**
   - Before/After XML + JSON shows actual transformations
   - "S2E36" format examples with case variants
   - Dry-run troubleshooting step-by-step

6. **Troubleshooting flow:** Symptom → Solutions (multiple). Users often try first one that doesn't work; giving alternatives reduces support tickets.

7. **Honesty about V2:** "⏳ Coming in V2" labels on sports settings set expectations. Users appreciate transparency about what *isn't* ready.

8. **Voice & tone:** 
   - Second person ("you") for action steps
   - Active voice ("The plugin parses" not "Parsing is done")
   - Emoji sparingly (✅, ⏳, ❤️) for visual breaks in dense text
   - Technical accuracy without jargon (explain "xmltv_ns" once, then reference)

9. **Scope boundaries explicitly listed:** "Out of Scope" and "Does NOT do" sections save time for users reading docs to understand integration points.

10. **Dry-run as safety valve:** Highlighting dry-run mode in multiple places (configuration, troubleshooting, development) as the "test without committing" feature.

**Reusable patterns for future docs:**
- Problem statement → Solution → How it works → Install → Configure → Use → Troubleshoot → Roadmap
- Always include "Before/After" examples for transformative tools
- Configuration should be a table (scannable)
- Troubleshooting should be Symptom → Multiple Solutions format
- Roadmap with status emojis (✅, ⏳, ❌) manages expectations
