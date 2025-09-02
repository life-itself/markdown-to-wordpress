"""Type definitions for the migration tool."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


@dataclass
class FrontMatter:
    """Represents markdown front matter data."""
    title: str
    slug: Optional[str] = None
    type: Optional[str] = None  # blog, event, podcast, page
    subtitle: Optional[str] = None
    description: Optional[str] = None
    date_published: Optional[str] = None
    date_updated: Optional[str] = None
    featured_image: Optional[str] = None
    authors: Optional[List[str]] = None
    status: Optional[str] = None  # draft, publish, private
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    initiatives: Optional[List[str]] = None
    external_id: Optional[str] = None
    
    # Event specific
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    host: Optional[Union[str, List[str]]] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    registration_url: Optional[str] = None
    
    # Podcast specific
    episode_number: Optional[int] = None
    audio_url: Optional[str] = None
    duration: Optional[str] = None
    guests: Optional[List[str]] = None
    show: Optional[str] = None
    
    # Page specific
    template: Optional[str] = None
    parent_slug: Optional[str] = None


@dataclass
class MarkdownFile:
    """Represents a parsed markdown file."""
    path: str
    front_matter: FrontMatter
    content: str
    html: Optional[str] = None


@dataclass
class WordPressPost:
    """Represents a WordPress post/page."""
    title: str
    content: str
    slug: str
    status: str = "draft"
    excerpt: Optional[str] = None
    date: Optional[str] = None
    date_gmt: Optional[str] = None
    modified: Optional[str] = None
    modified_gmt: Optional[str] = None
    author: Optional[int] = None
    featured_media: Optional[int] = None
    categories: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class Config:
    """Configuration for WordPress connection and migration."""
    wordpress_url: str
    username: str
    password: str
    auth_method: str = "application_passwords"
    default_status: str = "draft"
    default_author: str = "admin"
    concurrency: int = 4
    retry_attempts: int = 3
    retry_delay: float = 1.0
    upload_media: bool = True
    media_max_size_mb: int = 10


@dataclass
class MigrationResult:
    """Result of a single file migration."""
    source_path: str
    action: str  # created, updated, skipped, error
    wp_id: Optional[int] = None
    wp_slug: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None