"""
Test suite for epg-enricharr plugin.

NOTES:
- Some tests reference methods not yet implemented in plugin.py (e.g., enrich_batch)
- Blair should implement these to pass all tests
- Integration tests are marked with @pytest.mark.skip() until Dispatcharr is set up
- Sports enrichment tests require enable_sports_enrichment=True and implementation

Test coverage:
- ✅ Episode parsing (S2E36 → season 2, episode 36)
- ✅ TV show enrichment (Series/Movies)
- ⏳ Sports enrichment (needs implementation)
- ✅ Previously-shown flags
- ⏳ Bulk operations (needs enrich_batch method)
- ⏳ XMLTV output (integration tests)
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from plugin import Plugin as EnrichmentPlugin


class MockProgramData:
    """Mock ProgramData object for testing."""
    
    def __init__(self, title="Test Programme", custom_properties=None, start=None, channel_id=None):
        self.id = 1
        self.title = title
        self.custom_properties = custom_properties or {}
        self.start = start
        self.channel_id = channel_id


class TestEnrichmentPlugin:
    """Test cases for the enrichment plugin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin()
    
    def test_plugin_initialization(self):
        """Test that plugin initializes correctly."""
        assert self.plugin is not None
        assert self.plugin.version == "1.0.0"
    
    def test_plugin_metadata(self):
        """Test that plugin returns proper metadata."""
        metadata = self.plugin.get_metadata()
        assert metadata["name"] == "EPG Enricharr"
        assert metadata["version"] == "1.0.0"
        assert "description" in metadata
    
    def test_parse_episode_standard_format(self):
        """Test parsing S##E## format."""
        assert self.plugin.parse_episode_string("S2E36") == (2, 36)
        assert self.plugin.parse_episode_string("S01E05") == (1, 5)
        assert self.plugin.parse_episode_string("s10e99") == (10, 99)
    
    def test_parse_episode_x_format(self):
        """Test parsing ##x## format."""
        assert self.plugin.parse_episode_string("2x36") == (2, 36)
        assert self.plugin.parse_episode_string("01x05") == (1, 5)
        assert self.plugin.parse_episode_string("10X99") == (10, 99)
    
    def test_parse_episode_invalid_formats(self):
        """Test that invalid formats return None."""
        assert self.plugin.parse_episode_string("") is None
        assert self.plugin.parse_episode_string(None) is None
        assert self.plugin.parse_episode_string("Episode 5") is None
        assert self.plugin.parse_episode_string("S0E0") is None
        assert self.plugin.parse_episode_string("invalid") is None
    
    def test_parse_episode_embedded_in_text(self):
        """Test parsing episode strings embedded in longer text."""
        assert self.plugin.parse_episode_string("Title - S2E36 - Description") == (2, 36)
        assert self.plugin.parse_episode_string("2x36: Episode Title") == (2, 36)
    
    def test_should_enrich_tv_with_series_category(self):
        """Test TV enrichment filtering by category."""
        programme = MockProgramData(
            custom_properties={'categories': ['Series', 'Drama']}
        )
        assert self.plugin.should_enrich_tv(programme) is True
    
    def test_should_enrich_tv_with_movies_category(self):
        """Test TV enrichment with Movies category."""
        programme = MockProgramData(
            custom_properties={'categories': ['Movies']}
        )
        assert self.plugin.should_enrich_tv(programme) is True
    
    def test_should_not_enrich_tv_without_matching_category(self):
        """Test that programmes without matching categories are not enriched."""
        programme = MockProgramData(
            custom_properties={'categories': ['News', 'Documentary']}
        )
        assert self.plugin.should_enrich_tv(programme) is False
    
    def test_should_not_enrich_tv_when_disabled(self):
        """Test that TV enrichment respects enabled flag."""
        plugin = EnrichmentPlugin({'enable_tv_enrichment': False})
        programme = MockProgramData(
            custom_properties={'categories': ['Series']}
        )
        assert plugin.should_enrich_tv(programme) is False
    
    def test_enrich_programme_with_onscreen_episode(self):
        """Test enriching a programme with onscreen_episode."""
        programme = MockProgramData(
            custom_properties={
                'categories': ['Series'],
                'onscreen_episode': 'S2E36'
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['season'] == 2
        assert changes['episode'] == 36
    
    def test_enrich_programme_previously_shown_non_new(self):
        """Test that non-new programmes are marked as previously_shown."""
        programme = MockProgramData(
            custom_properties={'categories': ['Series']}
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['previously_shown'] is True
    
    def test_enrich_programme_no_previously_shown_for_new(self):
        """Test that new programmes are not marked as previously_shown."""
        programme = MockProgramData(
            custom_properties={
                'categories': ['Series'],
                'new': True
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert 'previously_shown' not in changes
    
    def test_enrich_programme_no_changes_without_data(self):
        """Test that programmes without enrichable data return no changes."""
        programme = MockProgramData(
            custom_properties={'categories': ['News']}
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        # Should still mark previously_shown if not new
        assert changes.get('previously_shown') is True
    
    def test_config_defaults(self):
        """Test that default configuration values are set correctly."""
        plugin = EnrichmentPlugin()
        
        assert plugin.enabled is True
        assert plugin.enable_tv_enrichment is True
        assert plugin.enable_sports_enrichment is False
        assert plugin.auto_mark_previously_shown is True
        assert plugin.dry_run_mode is False
        assert 'Series' in plugin.tv_categories


class TestSportsEnrichment:
    """Test sports programme enrichment with year-based seasons."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin({'enable_sports_enrichment': True})
    
    @pytest.mark.skip(reason="Sports enrichment not yet implemented in V1")
    def test_sports_season_from_year(self):
        """Test that sports season is derived from start_time year."""
        from datetime import datetime
        
        programme = MockProgramData(
            custom_properties={
                'categories': ['Soccer'],
                'start_time': datetime(2026, 2, 28, 15, 0, 0)
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes.get('season') == 2026
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_sports_sequential_episodes_batch(self):
        """Test sequential episode numbering for sports in batch."""
        from datetime import datetime
        
        programmes = [
            MockProgramData(
                custom_properties={
                    'categories': ['Soccer'],
                    'start_time': datetime(2026, 2, 28, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'categories': ['Soccer'],
                    'start_time': datetime(2026, 3, 1, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'categories': ['Soccer'],
                    'start_time': datetime(2026, 3, 2, 15, 0, 0)
                }
            )
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        # Episodes should be sequential: 1, 2, 3
        assert results[0].get('episode') == 1
        assert results[1].get('episode') == 2
        assert results[2].get('episode') == 3
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_sports_separate_sequences_per_sport(self):
        """Test that different sports maintain separate episode sequences."""
        from datetime import datetime
        
        programmes = [
            MockProgramData(
                custom_properties={
                    'categories': ['Soccer'],
                    'start_time': datetime(2026, 2, 28, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'categories': ['Soccer'],
                    'start_time': datetime(2026, 3, 1, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'categories': ['Rugby league'],
                    'start_time': datetime(2026, 2, 28, 17, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'categories': ['Rugby league'],
                    'start_time': datetime(2026, 3, 1, 17, 0, 0)
                }
            )
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        # Soccer: E1, E2
        assert results[0].get('episode') == 1
        assert results[1].get('episode') == 2
        
        # Rugby: E1, E2 (separate sequence)
        assert results[2].get('episode') == 1
        assert results[3].get('episode') == 2
    
    @pytest.mark.skip(reason="Sports enrichment not yet implemented in V1")
    def test_sports_all_recognized_categories(self):
        """Test that all sports categories are recognized."""
        from datetime import datetime
        
        sports_categories = ['Sports', 'Soccer', 'Rugby league', 'Cricket', 'Baseball', 'Hockey']
        
        for category in sports_categories:
            programme = MockProgramData(
                custom_properties={
                    'categories': [category],
                    'start_time': datetime(2026, 2, 28, 15, 0, 0)
                }
            )
            
            changes = self.plugin.enrich_programme(programme)
            
            # Should have year-based season
            assert changes.get('season') == 2026, f"Failed for category: {category}"


class TestParsingEdgeCases:
    """Test edge cases in episode parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin()
    
    def test_parse_s00e00(self):
        """Test parsing S00E00 (special episodes - should return None per Blair's design)."""
        # Blair's implementation rejects season 0 and episode 0
        # This is reasonable since XMLTV numbering starts at 1
        result = self.plugin.parse_episode_string('S00E00')
        assert result is None
    
    def test_parse_high_season_numbers(self):
        """Test parsing very high season numbers."""
        season, episode = self.plugin.parse_episode_string('S99E93')
        assert season == 99
        assert episode == 93
    
    def test_parse_high_episode_numbers(self):
        """Test parsing very high episode numbers."""
        season, episode = self.plugin.parse_episode_string('S9E999')
        assert season == 9
        assert episode == 999
    
    def test_parse_invalid_formats(self):
        """Test various invalid formats return None."""
        invalid_formats = [
            'S2',           # Season only
            'E36',          # Episode only
            'S2E',          # Missing episode number
            'SE36',         # Missing season number
            'E10E20',       # Malformed
            '2-36',         # Wrong separator
            'Season 2',     # Text format
            '',             # Empty string
        ]
        
        for fmt in invalid_formats:
            result = self.plugin.parse_episode_string(fmt)
            assert result is None, f"Expected None for format: {fmt}"


class TestPreviouslyShownLogic:
    """Test previously-shown flag logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin()
    
    def test_non_new_programme_gets_previously_shown(self):
        """Test non-new programme gets previously_shown flag."""
        programme = MockProgramData(
            custom_properties={'categories': ['Series']}
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['previously_shown'] is True
    
    def test_new_programme_no_previously_shown(self):
        """Test new programme does not get previously_shown flag."""
        programme = MockProgramData(
            custom_properties={
                'categories': ['Series'],
                'new': True
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert 'previously_shown' not in changes
    
    def test_programme_without_custom_properties(self):
        """Test programme without custom_properties gets previously_shown."""
        programme = MockProgramData()
        programme.custom_properties = None
        
        changes = self.plugin.enrich_programme(programme)
        
        # Should handle missing custom_properties gracefully
        assert changes.get('previously_shown') is True
    
    def test_previously_shown_can_be_disabled(self):
        """Test that previously_shown logic can be disabled."""
        plugin = EnrichmentPlugin({'auto_mark_previously_shown': False})
        
        programme = MockProgramData(
            custom_properties={'categories': ['Series']}
        )
        
        changes = plugin.enrich_programme(programme)
        
        assert 'previously_shown' not in changes


class TestDryRunMode:
    """Test dry-run mode — verifies plugin never writes to the DB when dry_run_mode=True."""

    def setup_method(self):
        self.plugin = EnrichmentPlugin()

    def test_dry_run_default_is_false(self):
        """dry_run_mode defaults to False (plugin is active on install)."""
        assert self.plugin.dry_run_mode is False

    def test_dry_run_enabled_via_config(self):
        """dry_run_mode can be enabled via config dict."""
        plugin = EnrichmentPlugin({'dry_run_mode': True})
        assert plugin.dry_run_mode is True

    def test_enrich_programme_returns_changes_in_dry_run(self):
        """enrich_programme() is pure — it still returns changes dict in dry-run mode."""
        plugin = EnrichmentPlugin({'dry_run_mode': True})
        programme = MockProgramData(
            custom_properties={'categories': ['Series'], 'onscreen_episode': 'S2E36'}
        )
        changes = plugin.enrich_programme(programme)
        assert changes['season'] == 2
        assert changes['episode'] == 36

    def test_enrich_programme_does_not_mutate_object(self):
        """enrich_programme() must not write to the programme object (DB write happens in _enrich_all)."""
        plugin = EnrichmentPlugin({'dry_run_mode': True})
        programme = MockProgramData(
            custom_properties={'categories': ['Series'], 'onscreen_episode': 'S2E36'}
        )
        original = dict(programme.custom_properties)
        plugin.enrich_programme(programme)
        assert programme.custom_properties == original

    def _make_mock_context(self, programmes):
        """Helper: build a mock ProgramData queryset and context dict."""
        mock_qs = MagicMock()
        mock_qs.count.return_value = len(programmes)
        mock_qs.__iter__ = lambda self: iter(programmes)
        mock_pd = MagicMock()
        mock_pd.objects.select_related.return_value.all.return_value = mock_qs
        mock_epg_models = MagicMock()
        mock_epg_models.ProgramData = mock_pd
        return mock_pd, mock_epg_models, {'logger': MagicMock()}

    def test_dry_run_skips_bulk_update(self):
        """In dry-run mode, ProgramData.objects.bulk_update must NOT be called."""
        plugin = EnrichmentPlugin({'dry_run_mode': True})
        mock_programme = MagicMock()
        mock_programme.custom_properties = {'categories': ['Series'], 'onscreen_episode': 'S2E36'}
        mock_programme.title = 'Test Show'
        mock_programme.id = 1

        mock_pd, mock_epg_models, context = self._make_mock_context([mock_programme])

        with patch.dict(sys.modules, {
            'apps': MagicMock(), 'apps.epg': MagicMock(), 'apps.epg.models': mock_epg_models
        }):
            result = plugin._enrich_all_programmes(context)

        mock_pd.objects.bulk_update.assert_not_called()
        assert result['dry_run'] is True
        assert result['stats']['enriched'] >= 1

    def test_live_mode_calls_bulk_update(self):
        """In live mode (dry_run=False), bulk_update IS called when there are changes."""
        plugin = EnrichmentPlugin({'dry_run_mode': False})
        mock_programme = MagicMock()
        mock_programme.custom_properties = {'categories': ['Series'], 'onscreen_episode': 'S2E36'}
        mock_programme.title = 'Test Show'
        mock_programme.id = 1

        mock_pd, mock_epg_models, context = self._make_mock_context([mock_programme])

        with patch.dict(sys.modules, {
            'apps': MagicMock(), 'apps.epg': MagicMock(), 'apps.epg.models': mock_epg_models
        }):
            result = plugin._enrich_all_programmes(context)

        mock_pd.objects.bulk_update.assert_called_once()
        assert result['dry_run'] is False

    def test_dry_run_stats_still_reported(self):
        """Dry-run mode must still compute and return enrichment stats (log without writing)."""
        plugin = EnrichmentPlugin({'dry_run_mode': True})
        mock_programme = MagicMock()
        mock_programme.custom_properties = {'categories': ['Series'], 'onscreen_episode': 'S3E12'}
        mock_programme.title = 'Test Show'
        mock_programme.id = 1

        mock_pd, mock_epg_models, context = self._make_mock_context([mock_programme])
        mock_logger = MagicMock()
        context['logger'] = mock_logger

        with patch.dict(sys.modules, {
            'apps': MagicMock(), 'apps.epg': MagicMock(), 'apps.epg.models': mock_epg_models
        }):
            result = plugin._enrich_all_programmes(context)

        assert 'stats' in result
        assert result['stats']['total'] == 1
        assert result['stats']['enriched'] == 1
        mock_logger.info.assert_called()  # stats must be logged even in dry-run


class TestMalformedInput:
    """Tests for malformed / edge-case input that must not crash the plugin."""

    def setup_method(self):
        self.plugin = EnrichmentPlugin()

    def test_parse_none_returns_none(self):
        assert self.plugin.parse_episode_string(None) is None

    def test_parse_empty_string_returns_none(self):
        assert self.plugin.parse_episode_string("") is None

    def test_parse_not_an_episode_returns_none(self):
        assert self.plugin.parse_episode_string("not_an_episode") is None

    def test_enrich_programme_with_none_custom_properties(self):
        """enrich_programme must not crash when custom_properties is None."""
        programme = MockProgramData()
        programme.custom_properties = None
        result = self.plugin.enrich_programme(programme)
        assert isinstance(result, dict)

    def test_enrich_programme_with_garbage_onscreen_episode(self):
        """enrich_programme must not crash and must not set season/episode on garbage input."""
        programme = MockProgramData(
            custom_properties={'categories': ['Series'], 'onscreen_episode': '!!!GARBAGE!!!'}
        )
        result = self.plugin.enrich_programme(programme)
        assert 'season' not in result
        assert 'episode' not in result


class TestBulkOperations:
    """Test bulk enrichment operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin()
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_enrich_batch_100_programmes(self):
        """Test enriching 100 programmes in batch."""
        programmes = [
            MockProgramData(
                custom_properties={
                    'categories': ['Series'],
                    'onscreen_episode': f'S1E{i}'
                }
            )
            for i in range(1, 101)
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        assert len(results) == 100
        # Verify all have season/episode enriched
        for i, result in enumerate(results):
            assert result.get('season') == 1
            assert result.get('episode') == i + 1
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_enrich_batch_preserves_order(self):
        """Test that batch enrichment preserves programme order."""
        programmes = [
            MockProgramData(custom_properties={'categories': ['Series']}),
            MockProgramData(custom_properties={'categories': ['Movies']}),
            MockProgramData(custom_properties={'categories': ['Series']}),
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        assert len(results) == 3
        # Order should be preserved
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_enrich_batch_empty_list(self):
        """Test enriching empty batch."""
        results = self.plugin.enrich_batch([])
        
        assert results == []
    
    @pytest.mark.skip(reason="Requires enrich_batch method implementation")
    def test_enrich_batch_single_programme(self):
        """Test enriching batch with single programme."""
        programmes = [
            MockProgramData(
                custom_properties={
                    'categories': ['Series'],
                    'onscreen_episode': 'S2E5'
                }
            )
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        assert len(results) == 1
        assert results[0].get('season') == 2
        assert results[0].get('episode') == 5


class TestIntegration:
    """Integration tests (to be run with Dispatcharr)."""
    
    @pytest.mark.skip(reason="Requires Dispatcharr integration")
    def test_xmltv_episode_num_tag(self):
        """Test XMLTV output contains episode-num tag."""
        # This test requires actual Dispatcharr instance
        # Will be implemented once Mrs. Garrett sets up local environment
        pass
    
    @pytest.mark.skip(reason="Requires Dispatcharr integration")
    def test_xmltv_previously_shown_tag(self):
        """Test XMLTV output contains previously-shown tag."""
        # This test requires actual Dispatcharr instance
        pass
    
    @pytest.mark.skip(reason="Requires Dispatcharr integration")
    def test_xmltv_sports_numbering(self):
        """Test XMLTV output for sports uses year-based season."""
        # This test requires actual Dispatcharr instance
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# =============================================================================
# V2 Tests — format_string, classify_programme, enrich_programme routing
# =============================================================================

class TestFormatString:
    """Test format_string() token resolution against programme datetime and channel."""

    def setup_method(self):
        from datetime import datetime
        self.plugin = EnrichmentPlugin()
        self.dt = datetime(2026, 3, 15, 19, 30)

    def _prog(self, channel_id=None):
        return MockProgramData(start=self.dt, channel_id=channel_id)

    def test_YYYY_token(self):
        assert self.plugin.format_string('{YYYY}', self._prog()) == '2026'

    def test_YY_token(self):
        assert self.plugin.format_string('{YY}', self._prog()) == '26'

    def test_MM_token(self):
        assert self.plugin.format_string('{MM}', self._prog()) == '03'

    def test_DD_token(self):
        assert self.plugin.format_string('{DD}', self._prog()) == '15'

    def test_hh_token(self):
        assert self.plugin.format_string('{hh}', self._prog()) == '19'

    def test_mm_token(self):
        assert self.plugin.format_string('{mm}', self._prog()) == '30'

    def test_channel_numeric_included(self):
        assert self.plugin.format_string('{channel}', self._prog(channel_id='42')) == '42'

    def test_channel_non_numeric_omitted(self):
        assert self.plugin.format_string('{channel}', self._prog(channel_id='ESPN')) == ''

    def test_channel_none_omitted(self):
        assert self.plugin.format_string('{channel}', self._prog(channel_id=None)) == ''

    def test_combined_template_numeric_channel(self):
        p = self._prog(channel_id='42')
        assert self.plugin.format_string('{MM}{DD}{hh}{mm}{channel}', p) == '0315193042'

    def test_combined_template_non_numeric_channel(self):
        p = self._prog(channel_id='ESPN')
        assert self.plugin.format_string('{MM}{DD}{hh}{mm}{channel}', p) == '03151930'

    def test_default_sports_episode_format_numeric_channel(self):
        """Default sports episode format with numeric channel produces MM+DD+hh+mm+channel."""
        plugin = EnrichmentPlugin({'enable_sports_enrichment': True})
        p = self._prog(channel_id='7')
        result = plugin.format_string(plugin.sports_episode_format, p)
        assert result == '031519307'


class TestClassifyProgramme:
    """Test classify_programme() content-type routing and precedence."""

    def setup_method(self):
        self.plugin = EnrichmentPlugin()

    def test_movie_category(self):
        p = MockProgramData(custom_properties={'categories': ['Movie']})
        assert self.plugin.classify_programme(p) == 'movie'

    def test_film_category(self):
        p = MockProgramData(custom_properties={'categories': ['Film']})
        assert self.plugin.classify_programme(p) == 'movie'

    def test_sports_category(self):
        p = MockProgramData(custom_properties={'categories': ['Sports']})
        assert self.plugin.classify_programme(p) == 'sports'

    def test_news_category(self):
        p = MockProgramData(custom_properties={'categories': ['News']})
        assert self.plugin.classify_programme(p) == 'news'

    def test_series_category_fallback_to_tv(self):
        p = MockProgramData(custom_properties={'categories': ['Series']})
        assert self.plugin.classify_programme(p) == 'tv'

    def test_no_categories_fallback_to_tv(self):
        p = MockProgramData(custom_properties={})
        assert self.plugin.classify_programme(p) == 'tv'

    def test_movie_takes_precedence_over_sports(self):
        p = MockProgramData(custom_properties={'categories': ['Movie', 'Sports']})
        assert self.plugin.classify_programme(p) == 'movie'

    def test_custom_kino_pattern_classifies_as_movie(self):
        plugin = EnrichmentPlugin({'movie_patterns': '(?i)kino'})
        p = MockProgramData(custom_properties={'categories': ['Kino']})
        assert plugin.classify_programme(p) == 'movie'

    def test_invalid_regex_pattern_skipped_no_crash(self):
        """Invalid regex is logged as a warning and skipped; classify_programme must not raise."""
        plugin = EnrichmentPlugin({'movie_patterns': '[invalid'})
        p = MockProgramData(custom_properties={'categories': ['News']})
        result = plugin.classify_programme(p)
        assert result == 'news'


class TestEnrichProgrammeV2:
    """Test V2 enrichment decision logic: movies skip, sports/news generate, TV uses V1 path."""

    def setup_method(self):
        from datetime import datetime
        self.dt = datetime(2026, 3, 15, 19, 30)
        self.sports_plugin = EnrichmentPlugin({'enable_sports_enrichment': True})
        self.news_plugin = EnrichmentPlugin({'enable_news_enrichment': True})
        self.default_plugin = EnrichmentPlugin()

    def _sports_prog(self, channel_id='42', extra_props=None):
        props = {'categories': ['Sports']}
        if extra_props:
            props.update(extra_props)
        return MockProgramData(custom_properties=props, start=self.dt, channel_id=channel_id)

    def test_movie_programme_returns_empty(self):
        """Movies are skipped entirely — no previously_shown, no season/episode."""
        p = MockProgramData(custom_properties={'categories': ['Movie']})
        assert self.sports_plugin.enrich_programme(p) == {}

    def test_sports_both_existing_values_preserved(self):
        """When both season and episode exist in custom_properties, they are returned as-is."""
        p = self._sports_prog(extra_props={'season': 2025, 'episode': '01011500'})
        changes = self.sports_plugin.enrich_programme(p)
        assert changes['season'] == 2025
        assert changes['episode'] == '01011500'

    def test_sports_neither_generates_both(self):
        """No existing season/episode → both generated from format strings."""
        p = self._sports_prog(channel_id='42')
        changes = self.sports_plugin.enrich_programme(p)
        assert changes['season'] == 2026
        assert changes['episode'] == '0315193042'

    def test_sports_only_season_present_regenerates_from_format(self):
        """Only season present (no episode) → both regenerated from format strings."""
        p = self._sports_prog(channel_id=None, extra_props={'season': 2025})
        changes = self.sports_plugin.enrich_programme(p)
        assert changes['season'] == 2026
        assert changes['episode'] == '03151930'

    def test_sports_only_episode_present_generates_season(self):
        """Only episode present (no season) → both regenerated from format strings."""
        p = self._sports_prog(channel_id=None, extra_props={'episode': '01011500'})
        changes = self.sports_plugin.enrich_programme(p)
        assert changes['season'] == 2026
        assert 'episode' in changes

    def test_news_programme_enriched_with_news_format(self):
        """News programme with enable_news_enrichment=True gets season and episode."""
        p = MockProgramData(custom_properties={'categories': ['News']}, start=self.dt)
        changes = self.news_plugin.enrich_programme(p)
        assert changes['season'] == 2026
        assert changes['episode'] == '0315'

    def test_tv_programme_uses_v1_episode_parsing(self):
        """TV programme routes to parse_episode_string V1 path."""
        p = MockProgramData(
            custom_properties={'categories': ['Series'], 'onscreen_episode': 'S3E07'}
        )
        changes = self.default_plugin.enrich_programme(p)
        assert changes['season'] == 3
        assert changes['episode'] == 7

    def test_sports_enrichment_disabled_skips_season_episode(self):
        """enable_sports_enrichment=False (default) → season/episode not set for sports."""
        p = MockProgramData(
            custom_properties={'categories': ['Sports']},
            start=self.dt,
            channel_id='42'
        )
        changes = self.default_plugin.enrich_programme(p)
        assert 'season' not in changes
        assert 'episode' not in changes

    def test_news_enrichment_disabled_skips_season_episode(self):
        """enable_news_enrichment=False (default) → season/episode not set for news."""
        p = MockProgramData(
            custom_properties={'categories': ['News']},
            start=self.dt
        )
        changes = self.default_plugin.enrich_programme(p)
        assert 'season' not in changes
        assert 'episode' not in changes
