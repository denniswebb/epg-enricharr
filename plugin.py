"""
EPG Enricharr Plugin
Enriches EPG data to improve Plex DVR recognition
"""

import re
import json
import os
import logging
from typing import Optional, Tuple, Dict, Any


logger = logging.getLogger(__name__)

def _read_manifest_version() -> str:
    manifest = os.path.join(os.path.dirname(__file__), 'plugin.json')
    try:
        with open(manifest) as f:
            return json.load(f).get('version', '0.0.0')
    except Exception:
        return '0.0.0'


class Plugin:
    """Dispatcharr plugin to enrich EPG custom_properties with season/episode metadata."""
    
    name = "EPG Enricharr"
    version = _read_manifest_version()
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
        # Dispatcharr passes settings as comma-separated strings from the UI
        tv_cats = self.config.get('tv_categories', 'Movies,Series,Sports')
        self.tv_categories = [c.strip() for c in tv_cats.split(',')] if isinstance(tv_cats, str) else list(tv_cats or [])
        sports_cats = self.config.get('sports_categories', '')
        self.sports_categories = [c.strip() for c in sports_cats.split(',') if c.strip()] if isinstance(sports_cats, str) else list(sports_cats or [])
        self.auto_mark_previously_shown = self.config.get('auto_mark_previously_shown', True)
        self.dry_run_mode = self.config.get('dry_run_mode', False)
        self.enable_news_enrichment = self.config.get('enable_news_enrichment', False)
        self.sports_season_format = self.config.get('sports_season_format', '{YYYY}')
        self.sports_episode_format = self.config.get('sports_episode_format', '{MM}{DD}{hh}{mm}{channel}')
        self.news_season_format = self.config.get('news_season_format', '{YYYY}')
        self.news_episode_format = self.config.get('news_episode_format', '{MM}{DD}')
        self.enable_sports_title_grouping = self.config.get('enable_sports_title_grouping', False)

        def _parse_patterns(pattern_str, defaults):
            raw = self.config.get(pattern_str, defaults)
            parts = [p.strip() for p in raw.split(',') if p.strip()]
            compiled = []
            for p in parts:
                try:
                    compiled.append(re.compile(p))
                except re.error:
                    logger.warning(f"Invalid regex pattern skipped: {p!r}")
            return compiled

        self.movie_patterns = _parse_patterns('movie_patterns', '(?i)movie,(?i)film,(?i)cinema')
        self.sports_patterns = _parse_patterns('sports_patterns', '(?i)sport,(?i)football,(?i)soccer,(?i)basketball,(?i)baseball,(?i)hockey,(?i)tennis,(?i)golf,(?i)racing,(?i)boxing,(?i)wrestling,(?i)mma,(?i)ufc')
        self.news_patterns = _parse_patterns('news_patterns', '(?i)news,(?i)weather,(?i)report')
        
        # Parse sports title patterns for V3 title grouping
        sports_title_raw = self.config.get('sports_title_patterns', [])
        if isinstance(sports_title_raw, str):
            sports_title_parts = [p.strip() for p in sports_title_raw.split(',') if p.strip()]
        else:
            sports_title_parts = list(sports_title_raw or [])
        self.sports_title_patterns = []
        for p in sports_title_parts:
            try:
                self.sports_title_patterns.append(re.compile(p))
            except re.error:
                logger.warning(f"Invalid sports title regex pattern skipped: {p!r}")
    
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
    
    def format_string(self, template: str, programme) -> str:
        """
        Resolve format tokens against EPG programme data.
        
        Tokens: {YYYY} {YY} {MM} {DD} {hh} {mm} {channel}
        Channel token is omitted silently if channel ID is non-numeric.
        """
        start = getattr(programme, 'start', None) or getattr(programme, 'start_time', None)
        result = template

        if start is not None:
            result = result.replace('{YYYY}', start.strftime('%Y'))
            result = result.replace('{YY}', start.strftime('%y'))
            result = result.replace('{MM}', start.strftime('%m'))
            result = result.replace('{DD}', start.strftime('%d'))
            result = result.replace('{hh}', start.strftime('%H'))
            result = result.replace('{mm}', start.strftime('%M'))
        else:
            for token in ('{YYYY}', '{YY}', '{MM}', '{DD}', '{hh}', '{mm}'):
                result = result.replace(token, '')

        if '{channel}' in result:
            channel_id = getattr(programme, 'channel_id', None)
            if channel_id is None:
                try:
                    channel_id = getattr(programme.channel, 'channel_id', None)
                except AttributeError:
                    pass
            if channel_id is not None and str(channel_id).isdigit():
                result = result.replace('{channel}', str(channel_id))
            else:
                result = result.replace('{channel}', '')

        return result

    def classify_programme(self, programme) -> str:
        """
        Classify a programme as 'movie', 'sports', 'news', or 'tv'.
        
        Classification uses configured regex patterns applied to categories and title.
        Precedence: movie → sports → news → tv (default fallback).
        """
        custom_props = programme.custom_properties or {}
        categories = custom_props.get('categories', [])
        cat_text = ' '.join(categories) if isinstance(categories, list) else str(categories)
        title = getattr(programme, 'title', '') or ''
        match_text = cat_text + ' ' + title

        for pattern in self.movie_patterns:
            if pattern.search(match_text):
                return 'movie'
        for pattern in self.sports_patterns:
            if pattern.search(match_text):
                return 'sports'
        for pattern in self.news_patterns:
            if pattern.search(match_text):
                return 'news'
        return 'tv'

    def _extract_sports_title_and_subtitle(self, title: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract sport name and match description from title using regex patterns.
        
        Args:
            title: Programme title
            
        Returns:
            Tuple of (sport_name, subtitle) where:
            - sport_name: Captured group 1 (sport/event name), or None if no match
            - subtitle: Captured group 2 (description), or None if missing
            
            If no pattern matches, returns (None, None) — caller uses full title as-is.
        """
        if not title:
            return None, None
        
        # Iterate patterns in order; first match wins
        for pattern in self.sports_title_patterns:
            try:
                match = pattern.search(title)
                if match:
                    # Extract group 1 (required) and group 2 (optional)
                    sport_name = match.group(1) if match.lastindex >= 1 else None
                    subtitle = match.group(2) if match.lastindex >= 2 else None
                    
                    # Guard: reject empty strings
                    if sport_name and sport_name.strip():
                        return sport_name.strip(), subtitle.strip() if subtitle else None
            except (IndexError, re.error):
                continue
        
        # No pattern matched
        return None, None

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
        categories = custom_props.get('categories', [])
        
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

        content_type = self.classify_programme(programme_data)

        # Movies → skip enrichment entirely
        if content_type == 'movie':
            return {}

        # V3: Sports title grouping (applies to sports content, independent of enrichment)
        if content_type == 'sports' and self.enable_sports_title_grouping and self.sports_title_patterns:
            original_title = getattr(programme_data, 'title', '') or ''
            sport_name, subtitle = self._extract_sports_title_and_subtitle(original_title)
            
            if sport_name:
                # Grouping succeeded: update title to sport name
                changes['_title'] = sport_name
                
                # Store original title for reference
                changes['original_title'] = original_title
                
                # If subtitle was extracted, store it in custom property
                if subtitle:
                    changes['title_subtitle'] = subtitle

        # Sports enrichment
        if content_type == 'sports' and self.enable_sports_enrichment:
            existing_season = custom_props.get('season')
            existing_episode = custom_props.get('episode')
            if existing_season and existing_episode:
                changes['season'] = existing_season
                changes['episode'] = existing_episode
                if not custom_props.get('onscreen_episode'):
                    changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
            else:
                try:
                    changes['season'] = int(self.format_string(self.sports_season_format, programme_data))
                except (ValueError, TypeError):
                    pass
                changes['episode'] = self.format_string(self.sports_episode_format, programme_data)
                if 'season' in changes:
                    changes['onscreen_episode'] = f"S{changes['season']}E{changes['episode']}"
                else:
                    changes['onscreen_episode'] = changes['episode']

        # News enrichment
        elif content_type == 'news' and self.enable_news_enrichment:
            existing_season = custom_props.get('season')
            existing_episode = custom_props.get('episode')
            if existing_season and existing_episode:
                changes['season'] = existing_season
                changes['episode'] = existing_episode
                if not custom_props.get('onscreen_episode'):
                    changes['onscreen_episode'] = f"S{existing_season}E{existing_episode}"
            else:
                try:
                    changes['season'] = int(self.format_string(self.news_season_format, programme_data))
                except (ValueError, TypeError):
                    pass
                changes['episode'] = self.format_string(self.news_episode_format, programme_data)
                if 'season' in changes:
                    changes['onscreen_episode'] = f"S{changes['season']}E{changes['episode']}"
                else:
                    changes['onscreen_episode'] = changes['episode']

        # TV show enrichment: Parse onscreen_episode
        elif content_type == 'tv' and self.should_enrich_tv(programme_data):
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

        # Apply settings from Dispatcharr context (plugin is instantiated without config at load time)
        settings = context.get('settings', {})
        if settings:
            self.__init__(config=settings)
        
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
        title_changed = False
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
                    # Extract _title before updating custom_properties (if present)
                    title_change = changes.pop('_title', None)
                    
                    # Apply changes to custom_properties
                    programme.custom_properties = programme.custom_properties or {}
                    programme.custom_properties.update(changes)
                    
                    # Apply title mutation if present
                    if title_change is not None:
                        programme.title = title_change
                        title_changed = True
                    
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
                # Build update_fields list dynamically
                update_fields = ['custom_properties']
                if title_changed:
                    update_fields.append('title')
                
                ProgramData.objects.bulk_update(
                    programmes_to_update,
                    update_fields,
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
