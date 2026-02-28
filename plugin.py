"""
EPG Enricharr Plugin
Enriches EPG data to improve Plex DVR recognition
"""

import re
import logging
from typing import Optional, Tuple, Dict, Any


logger = logging.getLogger(__name__)


class Plugin:
    """Dispatcharr plugin to enrich EPG custom_properties with season/episode metadata."""
    
    name = "EPG Enricharr"
    version = "1.0.0"
    description = "Enrich EPG data for Plex DVR recognition"
    
    # Episode format patterns
    EPISODE_PATTERNS = [
        re.compile(r'[Ss](\d+)[Ee](\d+)'),      # S2E36, s02e05
        re.compile(r'(\d+)[xX](\d+)'),           # 2x36, 02x05
    ]
    
    def __init__(self, config=None):
        """Initialize plugin with optional configuration."""
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.enable_tv_enrichment = self.config.get('enable_tv_enrichment', True)
        self.enable_sports_enrichment = self.config.get('enable_sports_enrichment', False)
        self.tv_categories = self.config.get('tv_categories', ['Movies', 'Series', 'Sports'])
        self.sports_categories = self.config.get('sports_categories', [])
        self.auto_mark_previously_shown = self.config.get('auto_mark_previously_shown', True)
        self.dry_run_mode = self.config.get('dry_run_mode', False)
    
    def parse_episode_string(self, episode_str: str) -> Optional[Tuple[int, int]]:
        """
        Parse onscreen episode string to extract season and episode numbers.
        
        Supported formats:
        - S2E36, s02e05 (standard format)
        - 2x36, 02x05 (alternative format)
        
        Args:
            episode_str: Episode string to parse (e.g., "S2E36")
        
        Returns:
            Tuple of (season, episode) as 1-based integers, or None if parsing fails
        """
        if not episode_str or not isinstance(episode_str, str):
            return None
        
        episode_str = episode_str.strip()
        
        for pattern in self.EPISODE_PATTERNS:
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
    
    def should_enrich_tv(self, programme_data) -> bool:
        """
        Determine if a programme should receive TV enrichment.
        
        Args:
            programme_data: ProgramData object with custom_properties
        
        Returns:
            True if programme should be enriched
        """
        if not self.enable_tv_enrichment:
            return False
        
        custom_props = programme_data.custom_properties or {}
        categories = custom_props.get('category', [])
        
        # Check if any category matches TV categories
        if isinstance(categories, list):
            for cat in categories:
                if any(tv_cat.lower() in cat.lower() for tv_cat in self.tv_categories):
                    return True
        
        return False
    
    def enrich_programme(self, programme_data) -> Dict[str, Any]:
        """
        Enrich a single programme's custom_properties.
        
        Args:
            programme_data: ProgramData object
        
        Returns:
            Dictionary of changes made to custom_properties
        """
        changes = {}
        custom_props = programme_data.custom_properties or {}
        
        # TV show enrichment: Parse onscreen_episode
        if self.should_enrich_tv(programme_data):
            onscreen_episode = custom_props.get('onscreen_episode')
            
            if onscreen_episode:
                parsed = self.parse_episode_string(onscreen_episode)
                if parsed:
                    season, episode = parsed
                    changes['season'] = season
                    changes['episode'] = episode
                    
                    # Preserve original onscreen_episode
                    if 'onscreen_episode' not in custom_props:
                        changes['onscreen_episode'] = onscreen_episode
        
        # Previously-shown flag: Mark if not explicitly new
        if self.auto_mark_previously_shown:
            is_new = custom_props.get('new', False)
            if not is_new:
                changes['previously_shown'] = True
        
        return changes
    
    def run(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run plugin action (Dispatcharr plugin API).
        
        Args:
            action: Action ID to run
            params: Parameters for the action
            context: Execution context (logger, settings, etc.)
        
        Returns:
            Result dictionary with status and metrics
        """
        logger.info(f"🔥 EPG-Enricharr.run() called with action='{action}'")
        
        if not self.enabled:
            logger.info("Plugin disabled, skipping")
            return {
                'status': 'skipped',
                'message': 'Plugin is disabled'
            }
        
        if action in ('enrich_all', 'enrich_on_epg_refresh'):
            logger.info(f"Running enrichment for action '{action}'...")
            return self._enrich_all_programmes(context)
        
        logger.warning(f"Unknown action: {action}")
        return {
            'status': 'error',
            'message': f'Unknown action: {action}'
        }
    
    def _enrich_all_programmes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich all programmes in the database.
        
        Args:
            context: Execution context with logger and settings
        
        Returns:
            Result with enrichment statistics
        """
        log = context.get('logger', logger)
        log.info("🎯 Starting EPG enrichment...")
        
        try:
            # Import Django models (late import to avoid issues in tests)
            from apps.epg.models import ProgramData
        except ImportError:
            log.warning("Could not import ProgramData model - running outside Dispatcharr?")
            return {
                'status': 'error',
                'message': 'Django models not available'
            }
        
        programmes_to_update = []
        stats = {
            'total': 0,
            'enriched': 0,
            'skipped': 0,
            'errors': 0,
        }
        
        # Query all programmes (consider filtering by date range for performance)
        queryset = ProgramData.objects.select_related('epg').all()
        stats['total'] = queryset.count()
        
        for programme in queryset:
            try:
                changes = self.enrich_programme(programme)
                
                if changes:
                    # Apply changes to custom_properties
                    programme.custom_properties = programme.custom_properties or {}
                    programme.custom_properties.update(changes)
                    
                    if not self.dry_run_mode:
                        programmes_to_update.append(programme)
                    
                    stats['enriched'] += 1
                    log.debug(f"Enriched: {programme.title} - {changes}")
                else:
                    stats['skipped'] += 1
            
            except Exception as e:
                stats['errors'] += 1
                log.error(f"Error enriching programme {programme.id}: {e}")
        
        # Bulk update in database
        if not self.dry_run_mode and programmes_to_update:
            try:
                ProgramData.objects.bulk_update(
                    programmes_to_update,
                    ['custom_properties'],
                    batch_size=1000
                )
                log.info(f"Bulk updated {len(programmes_to_update)} programmes")
            except Exception as e:
                log.error(f"Bulk update failed: {e}")
                return {
                    'status': 'error',
                    'message': f'Bulk update failed: {e}',
                    'stats': stats
                }
        
        log.info(f"✅ Enrichment complete: {stats}")
        
        return {
            'status': 'ok',
            'stats': stats,
            'dry_run': self.dry_run_mode
        }
    
    def get_metadata(self):
        """Return plugin metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description
        }


# Module-level initialization for Dispatcharr plugin loader
def get_plugin(config=None):
    """Factory function for plugin instantiation."""
    return Plugin(config)
