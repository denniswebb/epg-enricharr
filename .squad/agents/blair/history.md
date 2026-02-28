# Blair — History

## Project Context (Day 1)

**Project:** epg-enricharr — Dispatcharr plugin to enrich EPG data for Plex DVR recognition  
**Stack:** Python, Django, Dispatcharr plugin system  
**Problem:** Missing episode metadata in custom_properties for XMLTV output  
**Solution:** Enrich custom_properties with season/episode numbers, previously_shown flags, etc.  

**Owner:** Dennis  
**Key References:**
- Dispatcharr plugin docs: https://github.com/Dispatcharr/Dispatcharr/blob/main/Plugins.md
- Dispatcharr EPG models: apps/epg/models.py
- XMLTV output generator: apps/output/views.py (lines 1698-1726 for episode-num)
- EPG import parser: apps/epg/tasks.py (line 1861+ for extract_custom_properties)

## Learnings

(To be populated as Blair implements the plugin.)
