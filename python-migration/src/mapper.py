"""Content mapper to convert markdown files to WordPress format."""

from typing import Dict, Any, List, Optional
from .types import MarkdownFile, WordPressPost, Config
from .wordpress_client import WordPressClient


class ContentMapper:
    """Maps markdown content to WordPress post format."""
    
    def __init__(self, config: Config, wp_client: WordPressClient):
        self.config = config
        self.wp_client = wp_client
    
    def map_to_wordpress(self, md_file: MarkdownFile) -> Dict[str, Any]:
        """Convert a markdown file to WordPress post data."""
        fm = md_file.front_matter
        
        # Basic post data
        post_data = {
            "title": fm.title,
            "content": md_file.html or md_file.content,
            "slug": fm.slug,
            "status": fm.status or self.config.default_status,
            "excerpt": fm.subtitle or fm.description or "",
        }
        
        # Handle dates
        if fm.date_published:
            post_data["date"] = fm.date_published
        if fm.date_updated:
            post_data["modified"] = fm.date_updated
        
        # Handle author
        if fm.authors and len(fm.authors) > 0:
            author_id = self._resolve_author(fm.authors[0])
            if author_id:
                post_data["author"] = author_id
        
        # Handle taxonomies
        if fm.tags:
            tag_ids = self._resolve_taxonomy_terms("tags", fm.tags)
            if tag_ids:
                post_data["tags"] = tag_ids
        
        if fm.categories:
            cat_ids = self._resolve_taxonomy_terms("categories", fm.categories)
            if cat_ids:
                post_data["categories"] = cat_ids
        
        # Handle meta fields
        meta = {}
        
        # Always set external ID for idempotency
        meta["_external_id"] = fm.external_id or fm.slug
        
        # Type-specific meta
        if fm.type == "event":
            if fm.start_date:
                meta["start_date"] = fm.start_date
            if fm.end_date:
                meta["end_date"] = fm.end_date
            if fm.location_name:
                meta["location_name"] = fm.location_name
            if fm.location_address:
                meta["location_address"] = fm.location_address
            if fm.registration_url:
                meta["registration_url"] = fm.registration_url
            if fm.host:
                meta["host"] = fm.host if isinstance(fm.host, str) else ", ".join(fm.host)
        
        elif fm.type == "podcast":
            if fm.episode_number:
                meta["episode_number"] = fm.episode_number
            if fm.audio_url:
                meta["audio_url"] = fm.audio_url
            if fm.duration:
                meta["duration"] = fm.duration
            if fm.guests:
                meta["guests"] = ", ".join(fm.guests)
            if fm.show:
                meta["show"] = fm.show
        
        elif fm.type == "blog" and fm.featured is not None:
            meta["featured"] = fm.featured
        
        if meta:
            post_data["meta"] = meta
        
        return post_data
    
    def _resolve_author(self, author: str) -> Optional[int]:
        """Resolve author name/email to WordPress user ID."""
        # Try email first
        if "@" in author:
            user_id = self.wp_client.find_user_by_email(author)
            if user_id:
                return user_id
        
        # Try display name
        user_id = self.wp_client.find_user_by_name(author)
        if user_id:
            return user_id
        
        # Use default author
        return self.wp_client.find_user_by_name(self.config.default_author)
    
    def _resolve_taxonomy_terms(self, taxonomy: str, terms: List[str]) -> List[int]:
        """Resolve taxonomy term names to IDs."""
        term_ids = []
        
        for term in terms:
            term_id = self.wp_client.get_or_create_taxonomy_term(taxonomy, term)
            if term_id:
                term_ids.append(term_id)
        
        return term_ids
    
    def get_post_type(self, content_type: str) -> str:
        """Get WordPress post type for content type."""
        type_mapping = {
            "blog": "posts",
            "news": "posts", 
            "page": "pages",
            "event": "event",  # Assumes custom post type
            "podcast": "podcast"  # Assumes custom post type
        }
        
        return type_mapping.get(content_type, "posts")