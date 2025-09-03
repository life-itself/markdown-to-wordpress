"""Unit tests for the mapper module."""

import pytest
from unittest.mock import MagicMock, patch

from src.mapper import ContentMapper
from src.types import Config, MarkdownFile, FrontMatter


class TestContentMapper:
    """Test suite for ContentMapper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config(
            wordpress_url="https://example.com",
            username="testuser",
            password="testpass",
            default_status="draft",
            default_author="admin"
        )
        self.wp_client = MagicMock()
        self.mapper = ContentMapper(self.config, self.wp_client)
    
    def test_mapper_initialization(self):
        """Test mapper initializes with config and client."""
        assert self.mapper.config == self.config
        assert self.mapper.wp_client == self.wp_client
    
    def test_map_to_wordpress_basic_post(self, sample_front_matter):
        """Test mapping basic blog post to WordPress format."""
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=sample_front_matter,
            content="Test content",
            html="<p>Test content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        
        assert result["title"] == "Test Post Title"
        assert result["content"] == "<p>Test content</p>"
        assert result["slug"] == "test-post-slug"
        assert result["status"] == "publish"
        assert result["excerpt"] == "Test subtitle"
        assert result["date"] == "2025-01-15T10:00:00Z"
        assert result["modified"] == "2025-01-16T14:30:00Z"
    
    def test_map_to_wordpress_with_default_status(self):
        """Test using default status when not specified."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            status=None
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["status"] == "draft"
    
    def test_map_to_wordpress_author_resolution(self, sample_front_matter):
        """Test author resolution with email and name."""
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=sample_front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        # Test with name (first author is "John Doe")
        self.wp_client.find_user_by_email.return_value = None
        self.wp_client.find_user_by_name.return_value = 3
        result = self.mapper.map_to_wordpress(md_file)
        self.wp_client.find_user_by_name.assert_called_with("John Doe")
        assert result["author"] == 3
        
        # Test with email in authors list
        sample_front_matter.authors = ["jane@example.com"]
        md_file.front_matter = sample_front_matter
        self.wp_client.find_user_by_email.return_value = 5
        result = self.mapper.map_to_wordpress(md_file)
        self.wp_client.find_user_by_email.assert_called_with("jane@example.com")
        assert result["author"] == 5
        
        # Test fallback to default author
        sample_front_matter.authors = ["Unknown User"]
        md_file.front_matter = sample_front_matter
        self.wp_client.find_user_by_email.return_value = None
        self.wp_client.find_user_by_name.side_effect = [None, 1]  # First call returns None, second returns 1
        result = self.mapper.map_to_wordpress(md_file)
        assert result["author"] == 1
    
    def test_map_to_wordpress_taxonomies(self, sample_front_matter):
        """Test taxonomy mapping."""
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=sample_front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        self.wp_client.get_or_create_taxonomy_term.side_effect = [10, 11, 20, 30]
        
        result = self.mapper.map_to_wordpress(md_file)
        
        # Check tags were resolved
        assert result["tags"] == [10, 11]
        self.wp_client.get_or_create_taxonomy_term.assert_any_call("tags", "test")
        self.wp_client.get_or_create_taxonomy_term.assert_any_call("tags", "sample")
        
        # Check categories were resolved
        assert result["categories"] == [20]
        self.wp_client.get_or_create_taxonomy_term.assert_any_call("categories", "Technology")
    
    def test_map_to_wordpress_meta_fields(self, sample_front_matter):
        """Test meta field mapping."""
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=sample_front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        
        assert "meta" in result
        assert result["meta"]["_external_id"] == "test-external-id"
        assert result["meta"]["featured"] == True
    
    def test_map_to_wordpress_event_type(self, sample_event_front_matter):
        """Test mapping event-specific fields."""
        md_file = MarkdownFile(
            path="/test/event.md",
            front_matter=sample_event_front_matter,
            content="Event content",
            html="<p>Event content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        
        assert result["title"] == "Test Event"
        assert result["meta"]["start_date"] == "2025-10-01"
        assert result["meta"]["end_date"] == "2025-10-15"
        assert result["meta"]["location_name"] == "Test Venue"
        assert result["meta"]["location_address"] == "123 Test Street"
        assert result["meta"]["host"] == "Test Organization"
        assert result["meta"]["registration_url"] == "https://example.com/register"
    
    def test_map_to_wordpress_podcast_type(self, sample_podcast_front_matter):
        """Test mapping podcast-specific fields."""
        md_file = MarkdownFile(
            path="/test/podcast.md",
            front_matter=sample_podcast_front_matter,
            content="Episode notes",
            html="<p>Episode notes</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        
        assert result["title"] == "Episode 1: Test Episode"
        assert result["meta"]["episode_number"] == 1
        assert result["meta"]["audio_url"] == "https://example.com/audio.mp3"
        assert result["meta"]["duration"] == "00:45:30"
        assert result["meta"]["guests"] == "Guest One, Guest Two"
        assert result["meta"]["show"] == "Test Podcast Series"
    
    def test_map_to_wordpress_no_html(self):
        """Test mapping when HTML is not available."""
        front_matter = FrontMatter(
            title="Test",
            slug="test"
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Raw markdown content",
            html=None
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["content"] == "Raw markdown content"
    
    def test_map_to_wordpress_excerpt_fallback(self):
        """Test excerpt field fallback logic."""
        # Test with subtitle
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            subtitle="Subtitle text",
            description="Description text"
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["excerpt"] == "Subtitle text"
        
        # Test with description when no subtitle
        front_matter.subtitle = None
        md_file.front_matter = front_matter
        result = self.mapper.map_to_wordpress(md_file)
        assert result["excerpt"] == "Description text"
        
        # Test with empty string when neither exists
        front_matter.description = None
        md_file.front_matter = front_matter
        result = self.mapper.map_to_wordpress(md_file)
        assert result["excerpt"] == ""
    
    def test_resolve_author_with_no_authors(self):
        """Test author resolution when no authors provided."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            authors=None
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert "author" not in result
    
    def test_resolve_author_empty_list(self):
        """Test author resolution with empty authors list."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            authors=[]
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert "author" not in result
    
    def test_resolve_taxonomy_terms_empty(self):
        """Test taxonomy resolution with no terms."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            tags=None,
            categories=None
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert "tags" not in result
        assert "categories" not in result
    
    def test_resolve_taxonomy_terms_failure(self):
        """Test handling of taxonomy term resolution failure."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            tags=["tag1", "tag2"]
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        # Some terms succeed, some fail
        self.wp_client.get_or_create_taxonomy_term.side_effect = [10, None]
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["tags"] == [10]  # Only successful term included
    
    def test_get_post_type_mapping(self):
        """Test post type mapping for different content types."""
        assert self.mapper.get_post_type("blog") == "posts"
        assert self.mapper.get_post_type("news") == "posts"
        assert self.mapper.get_post_type("page") == "pages"
        assert self.mapper.get_post_type("event") == "event"
        assert self.mapper.get_post_type("podcast") == "podcast"
        assert self.mapper.get_post_type("unknown") == "posts"  # Default
        assert self.mapper.get_post_type(None) == "posts"  # Default
    
    def test_event_host_as_list(self):
        """Test event host field when provided as list."""
        front_matter = FrontMatter(
            title="Event",
            slug="event",
            type="event",
            host=["Org1", "Org2", "Org3"]
        )
        md_file = MarkdownFile(
            path="/test/event.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["meta"]["host"] == "Org1, Org2, Org3"
    
    def test_event_host_as_string(self):
        """Test event host field when provided as string."""
        front_matter = FrontMatter(
            title="Event",
            slug="event",
            type="event",
            host="Single Organization"
        )
        md_file = MarkdownFile(
            path="/test/event.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["meta"]["host"] == "Single Organization"
    
    def test_external_id_fallback(self):
        """Test external_id falls back to slug when not provided."""
        front_matter = FrontMatter(
            title="Test",
            slug="test-slug",
            external_id=None
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        assert result["meta"]["_external_id"] == "test-slug"
    
    def test_no_meta_for_non_featured_blog(self):
        """Test that non-featured blog posts don't get featured meta."""
        front_matter = FrontMatter(
            title="Test",
            slug="test",
            type="blog",
            featured=None
        )
        md_file = MarkdownFile(
            path="/test/path.md",
            front_matter=front_matter,
            content="Content",
            html="<p>Content</p>"
        )
        
        result = self.mapper.map_to_wordpress(md_file)
        # Should still have meta for external_id
        assert "_external_id" in result["meta"]
        assert "featured" not in result["meta"]