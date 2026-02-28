# EPG Enricharr

**EPG Enricharr** is a Dispatcharr plugin that enriches electronic program guide (EPG) data to improve how Plex DVR recognizes and organizes TV shows. It parses episode information from your IPTV EPG and stores season/episode numbers in Dispatcharr's database, enabling Plex to correctly identify series and episodes in your recordings.

## The Problem

**Plex DVR doesn't recognize TV shows from IPTV EPGs** because:
- IPTV EPG data lacks XML TV episode number tags (`<episode-num system="xmltv_ns">`)
- Without these tags, Plex marks **everything as "New"** instead of recognizing series/episodes
- This causes duplicate recordings and prevents proper show tracking
- You end up with broken episode metadata in your library

**EPG Enricharr solves this** by:
1. Reading onscreen episode strings from your IPTV EPG (e.g., "S2E36")
2. Parsing season and episode numbers
3. Storing them in Dispatcharr's custom properties database
4. Allowing Dispatcharr's XMLTV generator to output proper episode-num tags
5. Enabling Plex DVR to recognize shows and episodes correctly

## How It Works

### Architecture

```
IPTV EPG (onscreen_episode: "S2E36")
       ↓
   EPG Enricharr (plugin.enrich_programme)
       ↓
Dispatcharr Database (custom_properties: {season: 2, episode: 36})
       ↓
XMLTV Generator (reads custom_properties)
       ↓
XMLTV Output (<episode-num system="xmltv_ns">1 1 1</episode-num>)
       ↓
Plex DVR (recognizes as Season 2, Episode 36)
```

**What the plugin does:**
- **Listens** to `epg_refresh` events after EPG import
- **Parses** episode strings like "S2E36" or "2x36" into season/episode integers
- **Stores** these values in `ProgramData.custom_properties`
- **Preserves** the original onscreen_episode for reference
- **Marks** programmes as previously-shown (prevents false "New" labels)
- **Updates** the database via bulk operation (efficient and transactional)

**What it does NOT do:**
- Modify your EPG source data
- Change how Plex records files
- Manage metadata agents or scanning
- Require any configuration in Plex itself

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
1. **Download** the latest `epg-enricharr-1.0.0.zip` from [GitHub Releases](https://github.com/denniswebb/epg-enricharr/releases)
2. **Extract** to your Dispatcharr plugins directory:
   ```bash
   unzip epg-enricharr-1.0.0.zip -d /path/to/dispatcharr/plugins/
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
| **Enable sports enrichment** | Boolean | `false` | ⏳ Coming in V2: Year-based season numbering for sports |
| **TV categories** | Text (comma-separated) | `Movies,Series,Sports` | Programme categories to enrich (case-insensitive partial match) |
| **Sports categories** | Text (comma-separated) | *(empty)* | ⏳ V2 feature: Categories for sports enrichment |
| **Auto-mark previously shown** | Boolean | `true` | Mark non-new programmes as `previously_shown` (prevents false "New" labels) |
| **Dry run mode** | Boolean | `false` | Log changes without writing to database (useful for testing) |

### Configuration Examples

#### Example 1: Strict Category Matching
If you only want to enrich "Series" (not "Movies" or "Sports"):

```
TV categories: Series
```

#### Example 2: Testing Changes (Dry Run)
Before applying enrichment to your database:

1. Enable **Dry run mode** → `true`
2. Trigger enrichment (see below)
3. Check logs for what *would* change
4. Disable **Dry run mode** and re-run when ready

#### Example 3: Custom Category List
If your IPTV EPG uses non-standard categories like "TVShows" or "Drama":

```
TV categories: TVShows,Drama,Series,Episode
```

The plugin does **partial, case-insensitive matching**, so "Drama Series" will match "Drama" in this list.

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

### Input: IPTV EPG Programme

```xml
<programme start="202602280900" stop="202602281000" channel="bbc1.uk">
  <title>Coronation Street</title>
  <desc>British soap opera</desc>
  <category>Series</category>
  <onscreen_episode>S45E12345</onscreen_episode>
</programme>
```

### Dispatcharr Custom Properties (Before Enrichment)
```json
{
  "title": "Coronation Street",
  "category": ["Series"],
  "onscreen_episode": "S45E12345"
}
```

### Dispatcharr Custom Properties (After Enrichment)
```json
{
  "title": "Coronation Street",
  "category": ["Series"],
  "onscreen_episode": "S45E12345",
  "season": 45,
  "episode": 12345,
  "previously_shown": true
}
```

### XMLTV Output (Generated by Dispatcharr)
```xml
<programme start="202602280900" stop="202602281000" channel="bbc1.uk">
  <title>Coronation Street</title>
  <desc>British soap opera</desc>
  <category>Series</category>
  <episode-num system="xmltv_ns">44 12344 .</episode-num>
  <previously-shown />
</programme>
```

### Plex DVR Result
✅ **Recognizes as:**
- Series: Coronation Street
- Season: 45
- Episode: 12345
- Status: Previously Shown (no duplicate recording)

## Supported Formats

The plugin recognizes these onscreen episode formats:

- **Standard:** `S2E36`, `S01E05`, `s02e05` (case-insensitive)
- **Numeric:** `2x36`, `02x05`, `2X36` (case-insensitive)
- **Embedded:** `Title - S2E36 - Description` (parsed from longer text)

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

5. **Check for duplicate recordings:**
   - If Plex still records the same episode twice, first enrich, then clear Plex's EPG cache
   - Set a future recording to test

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
make test-zip           # Generate plugin zip
make validate           # Run test suite
make install-plugin     # Install to local Dispatcharr
```

### Running Tests
```bash
pytest tests/test_enrichment.py -v
```

### Viewing Test Output
```bash
make check-output       # Print XMLTV output from test data
```

See [docs/SETUP.md](docs/SETUP.md) for detailed local development instructions.

## Roadmap (V2 and Beyond)

**Planned Features:**
- 🎬 Sports enrichment: Year-based seasons + sequential episode numbering
- 🌍 Multi-language support (episode string parsing)
- ⚙️ Admin UI for category mapping
- 📊 Enrichment statistics dashboard

**Out of Scope (By Design):**
- DVR recording filenames (Plex manages this)
- Plex metadata agents (plugin only enriches XMLTV)
- Retroactive enrichment of old ProgramData
- Multi-language support in V1

## License

MIT License — see [LICENSE](LICENSE) file.

## Support & Feedback

- **Issues:** [GitHub Issues](https://github.com/denniswebb/epg-enricharr/issues)
- **Documentation:** [Full docs](docs/)
- **Discussions:** [GitHub Discussions](https://github.com/denniswebb/epg-enricharr/discussions)

---

**Made by** [Dennis Webb](https://github.com/denniswebb) and contributors.  
**Inspired by** the Dispatcharr community's need for better Plex DVR recognition.  
**Maintained with ❤️** for cord-cutters everywhere.
