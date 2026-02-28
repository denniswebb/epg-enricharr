# Test Suite Documentation

## Overview

This test suite validates the EPG enrichment plugin functionality. Tests are written using pytest and cover:

1. **Onscreen episode parsing** - Parsing S2E36 format into season/episode numbers
2. **TV show enrichment** - Adding season/episode metadata to Series/Movies
3. **Sports enrichment** - Year-based seasons and sequential episode numbering
4. **Previously-shown flags** - Marking non-new programmes
5. **Bulk operations** - Efficient batch updates
6. **XMLTV output** - Integration tests with Dispatcharr (requires setup)

## Test Structure

```
tests/
├── test_enrichment.py        # Main test suite
├── fixtures/
│   └── sample-epg.xml         # Sample EPG data for testing
└── README.md                  # This file
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test class
```bash
pytest tests/test_enrichment.py::TestOnscreenEpisodeParsing
```

### Run specific test
```bash
pytest tests/test_enrichment.py::TestOnscreenEpisodeParsing::test_parse_valid_standard_format
```

### Skip integration tests (require Dispatcharr)
```bash
pytest tests/ -m "not integration"
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=plugin --cov-report=html
```

## Test Categories

### Unit Tests
Tests that run independently without external dependencies:
- `TestOnscreenEpisodeParsing` - Episode string parsing
- `TestParsingEdgeCases` - Edge cases and invalid inputs
- `TestPreviouslyShownLogic` - Previously-shown flag logic
- `TestEnrichmentPlugin` - Basic plugin functionality

### Integration Tests (require Dispatcharr)
Tests marked with `@pytest.mark.skip(reason="Requires Dispatcharr integration")`:
- `TestIntegration::test_xmltv_episode_num_tag` - XMLTV output validation
- `TestIntegration::test_xmltv_previously_shown_tag` - Previously-shown tag
- `TestIntegration::test_xmltv_sports_numbering` - Sports numbering in XMLTV

These will be enabled once Mrs. Garrett sets up local Dispatcharr instance.

### Batch Tests
Tests that validate bulk operations:
- `TestBulkOperations::test_enrich_batch_100_programmes` - 100 programme batch
- `TestBulkOperations::test_enrich_batch_preserves_order` - Order preservation

### Sports Tests
Tests for sports-specific enrichment:
- `TestSportsEnrichment::test_sports_season_from_year` - Year-based seasons
- `TestSportsEnrichment::test_sports_sequential_episodes_batch` - Sequential numbering
- `TestSportsEnrichment::test_sports_separate_sequences_per_sport` - Separate sequences

## Test Data

### Fixtures
- `sample_tv_programme` - TV series with S2E5 episode data
- `sample_sports_programme` - Soccer match in 2026
- `sample_show_programme` - Talk show without episode data
- `sample_new_programme` - Programme marked as new

### Sample EPG Data
`fixtures/sample-epg.xml` contains realistic EPG data:
- The Office (S2E20)
- Breaking Bad (S3E12)
- NRL 360 (Sports)
- Premier League (Sports)
- The Matrix (Movie)

## Coverage Goals

Target: >80% coverage of core enrichment logic

Key areas to cover:
- ✅ Episode parsing (all formats, edge cases)
- ✅ TV show enrichment (Series, Movies)
- ✅ Sports enrichment (year-based, sequential)
- ✅ Previously-shown logic
- ✅ Bulk operations
- ⏳ XMLTV output validation (requires Dispatcharr)

## Adding New Tests

1. Create test function with descriptive name: `test_<feature>_<scenario>`
2. Add docstring explaining what is tested
3. Use fixtures for test data when possible
4. Assert expected behavior clearly
5. Mark integration tests with `@pytest.mark.skip()` if they require Dispatcharr

Example:
```python
def test_parse_episode_special_format(self):
    """Test parsing special episode format."""
    from plugin import parse_onscreen_episode
    
    season, episode = parse_onscreen_episode('S00E01')
    assert season == 0
    assert episode == 1
```

## CI Integration

Tests will be run automatically via GitHub Actions (Mr. Belvedere):
- On every pull request
- On every commit to main branch
- Integration tests run only when Dispatcharr is available

## Notes

- Blair is implementing `plugin.py` to pass these tests (TDD approach)
- Tests define the contract between enrichment logic and expected behavior
- Integration tests are placeholders until Mrs. Garrett completes Dispatcharr setup
- All test names should be descriptive enough to understand what is being tested

## Contact

**Test Engineer:** Tootie  
**Implementation:** Blair  
**Local Environment:** Mrs. Garrett  
**CI/CD:** Mr. Belvedere
