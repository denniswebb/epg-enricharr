---
name: "episode-parsing"
description: "Parse TV episode strings (S2E36, 2x14) into season/episode integers"
domain: "data-parsing, regex, tv-metadata"
confidence: "high"
source: "earned (epg-enricharr MVP implementation)"
---

## Context

When enriching EPG data for Plex DVR, episode strings come in multiple formats:
- Standard: `S2E36`, `S01E05`, `s10e99` (case-insensitive)
- Alternative: `2x36`, `01x05`, `10X99` (x or X separator)

These need to be parsed into 1-based integer pairs: `(season, episode)`

## Patterns

**Regex-based parsing with validation:**

```python
import re
from typing import Optional, Tuple

EPISODE_PATTERNS = [
    re.compile(r'[Ss](\d+)[Ee](\d+)'),      # S2E36, s02e05
    re.compile(r'(\d+)[xX](\d+)'),           # 2x36, 02x05
]

def parse_episode_string(episode_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse onscreen episode string to extract season and episode numbers.
    
    Returns:
        Tuple of (season, episode) as 1-based integers, or None if parsing fails
    """
    if not episode_str or not isinstance(episode_str, str):
        return None
    
    episode_str = episode_str.strip()
    
    for pattern in EPISODE_PATTERNS:
        match = pattern.search(episode_str)
        if match:
            try:
                season = int(match.group(1))
                episode = int(match.group(2))
                if season > 0 and episode > 0:
                    return (season, episode)
            except (ValueError, IndexError):
                continue
    
    return None
```

**Key design choices:**
- Use `.search()` not `.match()` — handles embedded strings ("Title - S2E36 - Description")
- Iterate patterns in order — more specific first
- Validate integers > 0 — reject S0E0 edge cases
- Return None for invalid input — makes error handling explicit
- Strip whitespace before parsing

## Examples

**Valid inputs:**
```python
parse_episode_string("S2E36")           # (2, 36)
parse_episode_string("S01E05")          # (1, 5)
parse_episode_string("s10e99")          # (10, 99)
parse_episode_string("2x36")            # (2, 36)
parse_episode_string("10X99")           # (10, 99)
parse_episode_string("Title - S2E36")   # (2, 36) — embedded
```

**Invalid inputs (return None):**
```python
parse_episode_string("")                # None
parse_episode_string(None)              # None
parse_episode_string("Episode 5")       # None
parse_episode_string("S0E0")            # None — zeros rejected
parse_episode_string("invalid")         # None
```

**Testing strategy:**
```python
def test_parse_episode_standard_format():
    assert parse_episode_string("S2E36") == (2, 36)
    assert parse_episode_string("S01E05") == (1, 5)

def test_parse_episode_x_format():
    assert parse_episode_string("2x36") == (2, 36)
    assert parse_episode_string("01x05") == (1, 5)

def test_parse_episode_invalid_formats():
    assert parse_episode_string("") is None
    assert parse_episode_string(None) is None
    assert parse_episode_string("S0E0") is None
```

## Anti-Patterns

❌ **Don't use `.match()` — misses embedded strings:**
```python
pattern.match("Title - S2E36")  # Fails — match requires start of string
```

❌ **Don't skip zero validation — breaks Plex:**
```python
season = int(match.group(1))  # Could be 0
# Should validate: if season > 0 and episode > 0
```

❌ **Don't raise exceptions on invalid input — breaks bulk processing:**
```python
return int(match.group(1)), int(match.group(2))  # ValueError on bad data
# Should: return None and let caller handle gracefully
```

❌ **Don't assume format — always try multiple patterns:**
```python
# Bad: Only supports one format
match = re.match(r'S(\d+)E(\d+)', episode_str)

# Good: Try multiple formats in order
for pattern in EPISODE_PATTERNS:
    match = pattern.search(episode_str)
    if match:
        # ...
```

## Related Skills

- **bulk-django-updates**: Use with Django's `bulk_update()` for efficient database writes
- **jsonfield-enrichment**: Store parsed season/episode in JSONField custom_properties
