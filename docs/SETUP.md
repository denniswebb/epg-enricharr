# Local Development Setup

This guide walks through setting up a local development environment for epg-enricharr.

## Quick Start

```bash
# 1. Bootstrap development environment
./dev-setup.sh

# 2. Activate Python virtual environment
source venv/bin/activate

# 3. Build and validate plugin
mise run test-zip
mise run validate

# 4. Run tests
mise run check-output
```

## Prerequisites

- Python 3.8+
- pip / venv
- Docker (optional, for Dispatcharr instance)
- mise

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/denniswebb/epg-enricharr.git
cd epg-enricharr
```

### 2. Run Development Setup

```bash
chmod +x dev-setup.sh
./dev-setup.sh
```

This will:
- Create a Python virtual environment
- Install dependencies (Django, pytest, lxml, etc.)
- Create necessary directories
- Generate `.env` file

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 4. Generate Plugin Zip

```bash
mise run test-zip
```

Creates `epg-enricharr-3.0.0.zip` with:
- `plugin.json` — Plugin metadata
- `plugin.py` — Plugin code
- `tests/` — Test suite
- `README.md` — Documentation
- `LICENSE` — MIT license

### 5. Validate Plugin

```bash
mise run validate
```

Checks:
- ✅ plugin.json is valid JSON with required fields
- ✅ plugin.py syntax is correct
- ✅ Tests run successfully

### 6. (Optional) Set Up Local Dispatcharr

```bash
mise run setup-dispatcharr
```

This starts a Docker container with a basic Dispatcharr instance on `http://localhost:8000`.

```bash
# Install plugin to local instance
mise run install-plugin

# Verify enrichment output
mise run check-output
```

## Mise Tasks

| Task | Purpose |
|------|---------|
| `mise run help` | Show all available tasks |
| `mise run dev-setup` | Install dependencies |
| `mise run test-zip` | Generate plugin zip |
| `mise run validate` | Validate plugin structure |
| `mise run setup-dispatcharr` | Start local Dispatcharr (Docker) |
| `mise run install-plugin` | Install plugin to Dispatcharr |
| `mise run check-output` | Validate enriched output |
| `mise run clean` | Remove build artifacts |

## Configuration

Edit `.env` to customize:
- `DISPATCHARR_HOST` — Where Dispatcharr is running
- `DISPATCHARR_DB_PATH` — Database location
- `EPG_TEST_DATA_PATH` — Path to test EPG data
- `LOG_LEVEL` — Debug/Info/Warning/Error

## Test Data

Sample test data is in `tests/fixtures/sample-epg.xml`:
- TV show (The Office)
- Drama series (Breaking Bad)
- Sports (NRL, Premier League)
- Movie (The Matrix)

Use this for local validation before running CI/CD.

## Troubleshooting

### Python version error

```bash
# Ensure Python 3.8+ is installed
python3 --version

# Specify Python explicitly
python3.11 -m venv venv
```

### Virtual environment not activating

```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows (Git Bash):
source venv/Scripts/activate
```

### Docker not found

If Docker isn't installed, the `mise run setup-dispatcharr` task will fall back to native setup.
See Dispatcharr documentation for installation: https://github.com/Dispatcharr/Dispatcharr

### Tests not running

Ensure pytest is installed:
```bash
pip install pytest pytest-cov
```

## Next Steps

1. **Code changes:** Edit `plugin.py` to add enrichment logic
2. **Add tests:** Update `tests/test_enrichment.py` with test cases
3. **Validate locally:** Run `mise run validate` before committing
4. **Check output:** Use `mise run check-output` to verify enrichment

## Contributing

When adding new features:

1. Update `plugin.py` with enrichment logic
2. Add tests to `tests/test_enrichment.py`
3. Add sample data to `tests/fixtures/` if needed
4. Run `make validate` to ensure quality
5. Commit and open a pull request

## Questions?

See the main [README.md](../README.md) or open an issue on GitHub.
