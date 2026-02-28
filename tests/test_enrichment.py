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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
