# EPG Enricharr

**EPG Enricharr** is a Dispatcharr plugin that enriches electronic program guide (EPG) data to improve how Plex DVR recognizes and organizes TV shows, sports, and news programmes. It parses episode information, generates season/episode metadata from date/time tokens, and groups sports titles for proper Plex series organization.

**Current Version:** 3.0.0

## The Problem

**Plex DVR doesn't recognize TV shows from IPTV EPGs** because:
- IPTV EPG data lacks XML TV episode number tags (`<episode-num system="xmltv_ns">`)
- Without these tags, Plex marks **everything as "New"** instead of recognizing series/episodes
- Sports broadcasts have descriptive titles ("AFL : Fremantle v Adelaide") that prevent Plex from grouping matches under a single series
- This causes duplicate recordings and prevents proper show tracking

**EPG Enricharr solves this** by:
1. **V1 — TV Enrichment:** Parsing onscreen episode strings (e.g., "S2E36") into season/episode numbers
2. **V2 — Sports & News Enrichment:** Generating season/episode from date/time tokens using configurable format strings
3. **V3 — Sports Title Grouping:** Splitting sports titles with regex patterns so Plex groups all matches under one series
4. Storing enriched metadata in Dispatcharr's database for XMLTV output
5. Enabling Plex DVR to recognize shows and episodes correctly

## How It Works

### Architecture

```
IPTV EPG (programme data)
       ↓
   Content Classification (movie / sports / news / tv)
       ↓
   EPG Enricharr (enrich_programme)
       ├── TV path: parse "S2E36" → season=2, episode=36
       ├── Sports path: generate from format string → S2026E03151930
       ├── News path: generate from format string → S2026E0315
       ├── Movie path: skip (no enrichment)
       └── Sports title grouping: "AFL : Fremantle v Adelaide" → title="AFL"
       ↓
Dispatcharr Database (custom_properties: {season, episode, original_title, ...})
       ↓
XMLTV Generator (reads custom_properties)
       ↓
Plex DVR (recognizes series, seasons, episodes)
```

## Features

### V1: TV Show Enrichment
- Parses episode strings like `S2E36`, `S01E05`, `2x36` into season/episode integers
- Stores values in `ProgramData.custom_properties`
- Marks programmes as `previously_shown` (prevents false "New" labels in Plex)
- Supports embedded strings ("Title - S2E36 - Description")

### V2: Sports & News Enrichment
- **Format string system** with 7 tokens: `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{hh}`, `{mm}`, `{channel}`
- **Content classification** routes programmes to the correct enrichment strategy
- **Pattern-based detection** using configurable regex for movies, sports, and news
- **Precedence order:** Movie (skip) → Sports → News → TV
- **Fallback chain:** Use existing EPG season/episode if present, generate from format string if missing

### V3: Sports Title Grouping
- **Regex-based title extraction** with configurable capture groups
- Group 1 = series name (e.g., "AFL"), Group 2 = match description (optional)
- Original title preserved in `custom_properties.original_title` for recovery
- First-match-wins pattern evaluation (ordered list, stops at first success)
- Independent feature flag — works with or without sports enrichment

**Example:**
```
Input title:  "AFL : Fremantle v Adelaide"
Output title: "AFL"                          (used by Plex for grouping)
Preserved:    original_title = "AFL : Fremantle v Adelaide"
              title_subtitle = "Fremantle v Adelaide"
```

## Installation

### Prerequisites
- **Dispatcharr** version 1.0.0 or higher
- **Python** 3.8 or later (included with Dispatcharr)

### Steps

#### Docker Installation
If you're running Dispatcharr in Docker, add a volume mount to your `docker-compose.yml`:

```yaml
services:
  dispatcharr:
    image: opendataint/dispatcharr:latest
    volumes:
      # ... existing volumes ...
      - ./plugins:/app/data/plugins
    # ... rest of config ...
```

Then extract the plugin zip into your local `./plugins` directory.

#### Native/Manual Installation
1. **Download** the latest `epg-enricharr-3.0.0.zip` from [GitHub Releases](https://github.com/denniswebb/epg-enricharr/releases)
2. **Extract** to your Dispatcharr plugins directory:
   ```bash
   unzip epg-enricharr-3.0.0.zip -d /path/to/dispatcharr/plugins/
   ```
   (Typically: `/app/data/plugins/` in Docker, or wherever you installed Dispatcharr locally)
3. **Restart** Dispatcharr:
   ```bash
   docker restart dispatcharr
   # OR
   systemctl restart dispatcharr  # if using systemd
   ```
4. **Verify** the plugin loaded:
   - Go to Dispatcharr **Settings** → **Plugins**
   - You should see "EPG Enricharr" listed with status "Active"

### Post-Installation

Once installed, the plugin **automatically enriches EPG data** when you import EPG sources. No additional setup required. However, you can customize behavior through settings (see **Configuration** below).

## Configuration

All settings are optional. Defaults are production-ready for most users.

### Settings Fields

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| **Enable plugin** | Boolean | `true` | Master switch to enable/disable the entire plugin |
| **Enable TV enrichment** | Boolean | `true` | Parse episode strings (S2E36) and add season/episode metadata |
| **Enable sports enrichment** | Boolean | `false` | Year-based season numbering and date-based episodes for sports |
| **Enable news enrichment** | Boolean | `false` | Year-based season and date-based episode numbering for news |
| **Enable sports title grouping** | Boolean | `false` | Split sports titles using regex patterns for Plex grouping (V3) |
| **TV categories** | Text | `Movies,Series,Sports` | Categories to apply TV enrichment (comma-separated) |
| **Sports categories** | Text | *(empty)* | Categories for sports enrichment (comma-separated) |
| **Auto-mark previously shown** | Boolean | `true` | Mark non-new programmes as `previously_shown` |
| **Dry run mode** | Boolean | `false` | Log changes without writing to database |
| **Sports season format** | Text | `{YYYY}` | Format string for sports season number |
| **Sports episode format** | Text | `{MM}{DD}{hh}{mm}{channel}` | Format string for sports episode number |
| **News season format** | Text | `{YYYY}` | Format string for news season number |
| **News episode format** | Text | `{MM}{DD}` | Format string for news episode number |
| **Movie detection patterns** | Text | `(?i)movie,(?i)film,...` | Regex patterns to identify movies (comma-separated) |
| **Sports detection patterns** | Text | `(?i)sport,(?i)football,...` | Regex patterns to identify sports (comma-separated) |
| **News detection patterns** | Text | `(?i)news,(?i)weather,...` | Regex patterns to identify news (comma-separated) |
| **Sports title patterns** | List | `[]` | Ordered regex patterns for title grouping (V3) |

### Configuration Examples

#### Example 1: Enable Sports Enrichment (V2)
Generate season/episode for sports based on air date and time:

```
Enable sports enrichment: true
Sports season format: {YYYY}
Sports episode format: {MM}{DD}{hh}{mm}
```

Result: A match airing 2026-03-15 at 19:30 → `S2026E03151930`

#### Example 2: Sports Title Grouping (V3)
Group all AFL and NRL matches under their sport name:

```
Enable sports title grouping: true
Sports title patterns:
  - "^(AFL).*:\\s*(.+)$"
  - "^(NRL).*:\\s*(.+)$"
  - "^(A-League).*:\\s*(.+)$"
```

Results:
- "AFL : Fremantle v Adelaide" → title="AFL", subtitle="Fremantle v Adelaide"
- "NRL Premiership : Broncos v Storm" → title="NRL", subtitle="Broncos v Storm"

#### Example 3: News Enrichment
Simple date-based episodes for news programmes:

```
Enable news enrichment: true
News season format: {YYYY}
News episode format: {MM}{DD}
```

Result: News airing 2026-03-15 → `S2026E0315`

#### Example 4: Strict Category Matching
If you only want to enrich "Series" (not "Movies" or "Sports"):

```
TV categories: Series
```

#### Example 5: Testing Changes (Dry Run)
Before applying enrichment to your database:

1. Enable **Dry run mode** → `true`
2. Trigger enrichment (see below)
3. Check logs for what *would* change
4. Disable **Dry run mode** and re-run when ready

## Usage

### Automatic Enrichment

The plugin **automatically enriches EPG data** when Dispatcharr imports a new EPG source. No action needed—just use Dispatcharr normally.

### Manual Enrichment (Trigger)

To manually trigger enrichment on all existing programmes:

1. Go to Dispatcharr **Settings** → **Plugins**
2. Find "EPG Enricharr"
3. Click **"Enrich All EPG"** button
4. Check the logs for enrichment results

## Example: Before and After

### V1: TV Show Enrichment

**Input:** Programme with `onscreen_episode: "S45E12345"`

**After enrichment:**
```json
{
  "season": 45,
  "episode": 12345,
  "onscreen_episode": "S45E12345",
  "previously_shown": true
}
```

### V2: Sports Enrichment

**Input:** Sports programme airing 2026-03-15 at 19:30

**After enrichment (with default format strings):**
```json
{
  "season": 2026,
  "episode": "03151930",
  "onscreen_episode": "S2026E03151930",
  "previously_shown": true
}
```

### V3: Sports Title Grouping

**Input:** `title = "AFL : Fremantle v Adelaide"`

**After enrichment (with pattern `^(AFL).*:\s*(.+)$`):**
```json
{
  "title": "AFL",
  "original_title": "AFL : Fremantle v Adelaide",
  "title_subtitle": "Fremantle v Adelaide",
  "season": 2026,
  "episode": "03151930"
}
```

Plex now groups all AFL matches under the "AFL" series.

## Supported Formats

### TV Episode Parsing (V1)

- **Standard:** `S2E36`, `S01E05`, `s02e05` (case-insensitive)
- **Numeric:** `2x36`, `02x05`, `2X36` (case-insensitive)
- **Embedded:** `Title - S2E36 - Description` (parsed from longer text)

### Format String Tokens (V2)

| Token | Description | Example |
|-------|-------------|---------|
| `{YYYY}` | 4-digit year | 2026 |
| `{YY}` | 2-digit year | 26 |
| `{MM}` | Month (01-12) | 03 |
| `{DD}` | Day (01-31) | 15 |
| `{hh}` | Hour (00-23) | 19 |
| `{mm}` | Minute (00-59) | 30 |
| `{channel}` | Channel ID (numeric only) | 42 |

### Title Grouping Patterns (V3)

Patterns use Python regex with capture groups:
- **Group 1** (required): Series name for Plex grouping
- **Group 2** (optional): Match description / subtitle

Example patterns:
```
^(AFL).*:\s*(.+)$          — "AFL : Fremantle v Adelaide"
^(NRL).*:\s*(.+)$          — "NRL Premiership : Broncos v Storm"
^(A-League)\s*:\s*(.+)$    — "A-League : Sydney FC v Melbourne"
```

### Not Supported (Logged as Skipped)

- Season/episode 0 (e.g., `S00E00` — reserved for specials)
- Malformed strings (e.g., `S2`, `E36`, `Season 2`)
- Text-only formats (e.g., "Season 2 Episode 36")

When parsing fails, the programme is logged and skipped—no errors occur.

## Troubleshooting

### Plugin Not Loading

**Symptom:** Plugin doesn't appear in Dispatcharr **Settings** → **Plugins**

**Solutions:**
1. **Check file permissions:** Ensure plugin directory is readable by Dispatcharr process
   ```bash
   ls -la /app/data/plugins/
   # Should show epg-enricharr files with readable permissions
   ```
2. **Restart Dispatcharr:** Changes to the plugins directory require restart
   ```bash
   docker restart dispatcharr
   ```
3. **Check logs:** Look for errors in Dispatcharr logs
   ```bash
   docker logs dispatcharr | grep -i enricharr
   ```

### Episodes Not Showing in Plex

**Symptom:** Plex still marks everything as "New" despite enrichment

**Solutions:**
1. **Verify enrichment ran:**
   - Enable **Dry run mode** and manually trigger **"Enrich All EPG"**
   - Check Dispatcharr logs for enrichment stats
   - Confirm "enriched" count > 0

2. **Check XMLTV output:**
   - Locate your Dispatcharr XMLTV file (usually `xmltv.xml`)
   - Look for `<episode-num>` tags in enriched programmes
   - If missing, enrichment didn't run or wasn't written to database

3. **Verify category matching:**
   - Check your IPTV EPG categories
   - Ensure they're listed in **TV categories** setting
   - Try adding broader categories like `"Series,Movies,Sports"`

4. **Re-import EPG in Plex:**
   - In Plex, go to **Settings** → **Live TV & DVR** → **EPG source**
   - Toggle the EPG source off and on to force re-import
   - This reloads the XMLTV metadata

### Database Rollback (Undo Enrichment)

If enrichment caused issues, you can:

1. **Disable the plugin** (flip **Enable plugin** → `false`)
2. **Manually revert** (requires database access):
   ```bash
   # This is database-level work; contact Dispatcharr support for guidance
   ```

Alternatively, **restore from backup** if you made one before enrichment.

## Performance & Safety

### Database Operations
- **Bulk updates** via Django ORM (efficient for 1,000+ programmes)
- **Transactional:** All changes succeed or none do
- **Read-only enrichment:** Plugin only reads your EPG, doesn't modify source files

### Dry Run Mode
Use dry-run mode to safely preview changes:
1. Set **Dry run mode** → `true`
2. Manually trigger **"Enrich All EPG"**
3. Review logs—no database changes are written
4. Once confident, disable dry-run and re-run

### Resource Usage
- Negligible CPU overhead (episode parsing is fast regex)
- Database impact scales with programme count (1,000 programmes ≈ 1-2 seconds)

## Development & Testing

For developers extending or testing this plugin locally:

### Quick Start
```bash
./dev-setup.sh          # One-time setup
mise run test-zip       # Generate plugin zip
mise run validate       # Run test suite
mise run install-plugin # Install to local Dispatcharr
```

### Running Tests
```bash
pytest tests/test_enrichment.py -v
```

Test suite: 85 passing, 11 skipped (V2 integration stubs).

### Viewing Test Output
```bash
mise run check-output   # Print XMLTV output from test data
```

See [docs/SETUP.md](docs/SETUP.md) for detailed local development instructions.

## Roadmap

### Completed
- V1: TV show enrichment (parsing, previously-shown)
- V2: Sports & news enrichment (format strings, content classification)
- V3: Sports title grouping (regex patterns, original title preservation)

### Planned (V4+)
- External API enrichment (TheSportsDB, TVDB) for richer metadata
- Sequential episode numbering for sports (track game order within season)
- Multi-language episode string parsing
- Admin UI for pattern management (visual regex builder)
- Community pattern packs (shared rule repository)
- CI/CD pipeline (GitHub Actions for test/release automation)

### Out of Scope (By Design)
- DVR recording filenames (Plex manages this)
- Plex metadata agents (plugin only enriches XMLTV)
- Retroactive enrichment of old ProgramData

## License

MIT License — see [LICENSE](LICENSE) file.

## Support & Feedback

- **Issues:** [GitHub Issues](https://github.com/denniswebb/epg-enricharr/issues)
- **Documentation:** [Full docs](docs/)
- **Discussions:** [GitHub Discussions](https://github.com/denniswebb/epg-enricharr/discussions)

---

**Made by** [Dennis Webb](https://github.com/denniswebb) and contributors.
**Inspired by** the Dispatcharr community's need for better Plex DVR recognition.
