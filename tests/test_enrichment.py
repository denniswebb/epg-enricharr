"""
Test suite for epg-enricharr plugin
"""

import pytest
from plugin import EnrichmentPlugin


class MockProgramData:
    """Mock ProgramData object for testing."""
    
    def __init__(self, title="Test Programme", custom_properties=None):
        self.id = 1
        self.title = title
        self.custom_properties = custom_properties or {}


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
            custom_properties={'category': ['Series', 'Drama']}
        )
        assert self.plugin.should_enrich_tv(programme) is True
    
    def test_should_enrich_tv_with_movies_category(self):
        """Test TV enrichment with Movies category."""
        programme = MockProgramData(
            custom_properties={'category': ['Movies']}
        )
        assert self.plugin.should_enrich_tv(programme) is True
    
    def test_should_not_enrich_tv_without_matching_category(self):
        """Test that programmes without matching categories are not enriched."""
        programme = MockProgramData(
            custom_properties={'category': ['News', 'Documentary']}
        )
        assert self.plugin.should_enrich_tv(programme) is False
    
    def test_should_not_enrich_tv_when_disabled(self):
        """Test that TV enrichment respects enabled flag."""
        plugin = EnrichmentPlugin({'enable_tv_enrichment': False})
        programme = MockProgramData(
            custom_properties={'category': ['Series']}
        )
        assert plugin.should_enrich_tv(programme) is False
    
    def test_enrich_programme_with_onscreen_episode(self):
        """Test enriching a programme with onscreen_episode."""
        programme = MockProgramData(
            custom_properties={
                'category': ['Series'],
                'onscreen_episode': 'S2E36'
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['season'] == 2
        assert changes['episode'] == 36
    
    def test_enrich_programme_previously_shown_non_new(self):
        """Test that non-new programmes are marked as previously_shown."""
        programme = MockProgramData(
            custom_properties={'category': ['Series']}
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['previously_shown'] is True
    
    def test_enrich_programme_no_previously_shown_for_new(self):
        """Test that new programmes are not marked as previously_shown."""
        programme = MockProgramData(
            custom_properties={
                'category': ['Series'],
                'new': True
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert 'previously_shown' not in changes
    
    def test_enrich_programme_no_changes_without_data(self):
        """Test that programmes without enrichable data return no changes."""
        programme = MockProgramData(
            custom_properties={'category': ['News']}
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
    
    def test_sports_season_from_year(self):
        """Test that sports season is derived from start_time year."""
        from datetime import datetime
        
        programme = MockProgramData(
            custom_properties={
                'category': ['Soccer'],
                'start_time': datetime(2026, 2, 28, 15, 0, 0)
            }
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes.get('season') == 2026
    
    def test_sports_sequential_episodes_batch(self):
        """Test sequential episode numbering for sports in batch."""
        from datetime import datetime
        
        programmes = [
            MockProgramData(
                custom_properties={
                    'category': ['Soccer'],
                    'start_time': datetime(2026, 2, 28, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'category': ['Soccer'],
                    'start_time': datetime(2026, 3, 1, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'category': ['Soccer'],
                    'start_time': datetime(2026, 3, 2, 15, 0, 0)
                }
            )
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        # Episodes should be sequential: 1, 2, 3
        assert results[0].get('episode') == 1
        assert results[1].get('episode') == 2
        assert results[2].get('episode') == 3
    
    def test_sports_separate_sequences_per_sport(self):
        """Test that different sports maintain separate episode sequences."""
        from datetime import datetime
        
        programmes = [
            MockProgramData(
                custom_properties={
                    'category': ['Soccer'],
                    'start_time': datetime(2026, 2, 28, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'category': ['Soccer'],
                    'start_time': datetime(2026, 3, 1, 15, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'category': ['Rugby league'],
                    'start_time': datetime(2026, 2, 28, 17, 0, 0)
                }
            ),
            MockProgramData(
                custom_properties={
                    'category': ['Rugby league'],
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
    
    def test_sports_all_recognized_categories(self):
        """Test that all sports categories are recognized."""
        from datetime import datetime
        
        sports_categories = ['Sports', 'Soccer', 'Rugby league', 'Cricket', 'Baseball', 'Hockey']
        
        for category in sports_categories:
            programme = MockProgramData(
                custom_properties={
                    'category': [category],
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
        """Test parsing S00E00 (special episodes)."""
        season, episode = self.plugin.parse_episode_string('S00E00')
        assert season == 0
        assert episode == 0
    
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
            custom_properties={'category': ['Series']}
        )
        
        changes = self.plugin.enrich_programme(programme)
        
        assert changes['previously_shown'] is True
    
    def test_new_programme_no_previously_shown(self):
        """Test new programme does not get previously_shown flag."""
        programme = MockProgramData(
            custom_properties={
                'category': ['Series'],
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
            custom_properties={'category': ['Series']}
        )
        
        changes = plugin.enrich_programme(programme)
        
        assert 'previously_shown' not in changes


class TestBulkOperations:
    """Test bulk enrichment operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = EnrichmentPlugin()
    
    def test_enrich_batch_100_programmes(self):
        """Test enriching 100 programmes in batch."""
        programmes = [
            MockProgramData(
                custom_properties={
                    'category': ['Series'],
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
    
    def test_enrich_batch_preserves_order(self):
        """Test that batch enrichment preserves programme order."""
        programmes = [
            MockProgramData(custom_properties={'category': ['Series']}),
            MockProgramData(custom_properties={'category': ['Movies']}),
            MockProgramData(custom_properties={'category': ['Series']}),
        ]
        
        results = self.plugin.enrich_batch(programmes)
        
        assert len(results) == 3
        # Order should be preserved
    
    def test_enrich_batch_empty_list(self):
        """Test enriching empty batch."""
        results = self.plugin.enrich_batch([])
        
        assert results == []
    
    def test_enrich_batch_single_programme(self):
        """Test enriching batch with single programme."""
        programmes = [
            MockProgramData(
                custom_properties={
                    'category': ['Series'],
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
