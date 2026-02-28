# EPG Enricharr

Dispatcharr plugin to enrich EPG data for improved Plex DVR recognition.

## Features

- Normalizes programme titles for better matching
- Enriches season/episode metadata
- Improves sports event recognition
- Validates and cleans XMLTV output

## Installation

1. Download the latest plugin zip from releases
2. Extract to your Dispatcharr plugins directory
3. Restart Dispatcharr
4. Configure through the admin interface

## Development

See [docs/SETUP.md](docs/SETUP.md) for local development instructions.

### Quick Start

```bash
make help          # See all available targets
make dev-setup     # Install dependencies
make test-zip      # Generate plugin
make validate       # Run validation
```

## Testing

Run validation:
```bash
make validate
```

Generate plugin zip:
```bash
make test-zip
```

## License

MIT License - see LICENSE file
