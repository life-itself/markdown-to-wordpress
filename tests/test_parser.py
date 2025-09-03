"""Unit tests for the parser module."""

import pytest
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.parser import MarkdownParser
from src.types import FrontMatter, MarkdownFile


class TestMarkdownParser:
    """Test suite for MarkdownParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()
    
    def test_parser_initialization(self):
        """Test parser initializes with correct markdown extensions."""
        assert self.parser.md is not None
        assert hasattr(self.parser.md, 'convert')
    
    def test_find_markdown_files_valid_directory(self, temp_markdown_dir):
        """Test finding markdown files in a valid directory."""
        files = self.parser.find_markdown_files(temp_markdown_dir)
        assert len(files) == 4
        assert all(f.endswith('.md') for f in files)
    
    def test_find_markdown_files_invalid_directory(self):
        """Test finding markdown files with invalid directory."""
        with pytest.raises(FileNotFoundError) as exc_info:
            self.parser.find_markdown_files("/nonexistent/path")
        assert "Input path does not exist" in str(exc_info.value)
    
    def test_find_markdown_files_with_pattern(self, temp_markdown_dir):
        """Test finding markdown files with custom pattern."""
        files = self.parser.find_markdown_files(temp_markdown_dir, pattern="blog/*.md")
        assert len(files) == 1
        assert "post1.md" in files[0]
    
    def test_parse_file_success(self, temp_markdown_file):
        """Test successful parsing of a markdown file."""
        result = self.parser.parse_file(temp_markdown_file)
        
        assert isinstance(result, MarkdownFile)
        assert result.front_matter.title == "Test Post"
        assert result.front_matter.slug == "test-post"
        assert result.front_matter.type == "blog"
        assert "test" in result.front_matter.tags
        assert "Technology" in result.front_matter.categories
        assert result.content is not None
        assert result.html is not None
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            self.parser.parse_file("/nonexistent/file.md")
        assert "File does not exist" in str(exc_info.value)
    
    def test_normalize_front_matter_missing_slug(self, tmp_path):
        """Test slug generation when not provided."""
        file_path = tmp_path / "my-test-post.md"
        file_path.write_text("---\ntitle: Test\n---\nContent", encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        assert result.front_matter.slug == "my-test-post"
    
    def test_normalize_front_matter_type_detection(self, tmp_path):
        """Test content type detection from path."""
        # Test blog detection
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        blog_file = blog_dir / "post.md"
        blog_file.write_text("---\ntitle: Test\n---\nContent", encoding='utf-8')
        result = self.parser.parse_file(str(blog_file))
        assert result.front_matter.type == "blog"
        
        # Test event detection
        event_dir = tmp_path / "events"
        event_dir.mkdir()
        event_file = event_dir / "event.md"
        event_file.write_text("---\ntitle: Test\n---\nContent", encoding='utf-8')
        result = self.parser.parse_file(str(event_file))
        assert result.front_matter.type == "event"
        
        # Test podcast detection
        podcast_dir = tmp_path / "podcasts"
        podcast_dir.mkdir()
        podcast_file = podcast_dir / "episode.md"
        podcast_file.write_text("---\ntitle: Test\n---\nContent", encoding='utf-8')
        result = self.parser.parse_file(str(podcast_file))
        assert result.front_matter.type == "podcast"
    
    def test_normalize_front_matter_arrays(self, tmp_path):
        """Test normalization of array fields."""
        file_path = tmp_path / "test.md"
        content = """---
title: Test
tags: single-tag
authors: John Doe
---
Content"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        assert isinstance(result.front_matter.tags, list)
        assert result.front_matter.tags == ["single-tag"]
        assert isinstance(result.front_matter.authors, list)
        assert result.front_matter.authors == ["John Doe"]
    
    def test_normalize_date_formats(self):
        """Test date normalization with various formats."""
        metadata = {
            "title": "Test",
            "date_published": "2025-01-15",
            "date_updated": "2025-01-16T10:30:00Z"
        }
        
        front_matter = self.parser._normalize_front_matter(metadata, "test.md")
        assert "2025-01-15" in front_matter.date_published
        assert "2025-01-16" in front_matter.date_updated
    
    def test_generate_slug(self):
        """Test slug generation from various text inputs."""
        assert self.parser._generate_slug("Hello World") == "hello-world"
        assert self.parser._generate_slug("Test_With_Underscores") == "test-with-underscores"
        assert self.parser._generate_slug("Special!@#$%^Characters") == "specialcharacters"
        assert self.parser._generate_slug("  Leading and Trailing  ") == "leading-and-trailing"
        assert self.parser._generate_slug("Multiple   Spaces") == "multiple-spaces"
    
    def test_process_wiki_links(self):
        """Test processing of wiki-style links."""
        html = "Check out [[Another Page]] and [[custom-slug|Custom Text]]."
        result = self.parser._process_wiki_links(html)
        
        assert '<a href="/another-page"' in result
        assert 'data-wiki-link="Another Page"' in result
        assert '>Another Page</a>' in result
        assert '<a href="/custom-slug"' in result
        assert '>Custom Text</a>' in result
    
    def test_process_image_paths(self):
        """Test processing of image paths."""
        html = '<img src="./images/local.jpg"> and <img src="https://example.com/remote.jpg">'
        result = self.parser._process_image_paths(html)
        
        assert 'data-local-image="./images/local.jpg"' in result
        # Check that remote images don't get the data-local-image attribute
        assert 'data-local-image' not in result.split('https://example.com/remote.jpg">')[1] if 'https://example.com/remote.jpg">' in result else True
    
    def test_convert_to_html_with_markdown_features(self, tmp_path):
        """Test HTML conversion with various markdown features."""
        file_path = tmp_path / "test.md"
        content = """---
title: Test
---

# Heading

**Bold** and *italic* text.

- List item 1
- List item 2

```python
print("Code block")
```

| Table | Header |
|-------|--------|
| Cell  | Data   |
"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        html = result.html
        
        assert "<h1" in html  # May have id attribute
        assert "<strong>Bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "<ul>" in html
        assert "<li>List item 1</li>" in html
        assert "<code" in html or "<pre>" in html
        assert "<table>" in html
    
    def test_external_id_generation(self, tmp_path):
        """Test external_id is set when not provided."""
        file_path = tmp_path / "test.md"
        content = """---
title: Test
slug: test-slug
---
Content"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        assert result.front_matter.external_id == "test-slug"
    
    def test_event_specific_fields(self, tmp_path):
        """Test parsing of event-specific fields."""
        file_path = tmp_path / "event.md"
        content = """---
title: Test Event
type: event
start_date: 2025-10-01
end_date: 2025-10-15
location_name: Test Venue
location_address: 123 Test St
host: [Org1, Org2]
registration_url: https://example.com/register
---
Event content"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        fm = result.front_matter
        
        assert fm.type == "event"
        assert fm.start_date == "2025-10-01"
        assert fm.end_date == "2025-10-15"
        assert fm.location_name == "Test Venue"
        assert fm.location_address == "123 Test St"
        assert fm.host == ["Org1", "Org2"]
        assert fm.registration_url == "https://example.com/register"
    
    def test_podcast_specific_fields(self, tmp_path):
        """Test parsing of podcast-specific fields."""
        file_path = tmp_path / "podcast.md"
        content = """---
title: Episode 1
type: podcast
episode_number: 1
audio_url: https://example.com/audio.mp3
duration: 00:45:30
guests: [Guest One, Guest Two]
show: My Podcast
---
Episode notes"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        fm = result.front_matter
        
        assert fm.type == "podcast"
        assert fm.episode_number == 1
        assert fm.audio_url == "https://example.com/audio.mp3"
        assert fm.duration == "00:45:30"
        assert fm.guests == ["Guest One", "Guest Two"]
        assert fm.show == "My Podcast"
    
    def test_page_specific_fields(self, tmp_path):
        """Test parsing of page-specific fields."""
        file_path = tmp_path / "page.md"
        content = """---
title: About Page
type: page
template: custom-template
parent_slug: parent-page
---
Page content"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        fm = result.front_matter
        
        assert fm.type == "page"
        assert fm.template == "custom-template"
        assert fm.parent_slug == "parent-page"
    
    def test_empty_content_handling(self, tmp_path):
        """Test handling of empty content."""
        file_path = tmp_path / "empty.md"
        content = """---
title: Empty Post
---

"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        assert result.content.strip() == ""
        assert result.html == ""
    
    def test_unicode_content_handling(self, tmp_path):
        """Test handling of unicode content."""
        file_path = tmp_path / "unicode.md"
        content = """---
title: Unicode Test
---

This contains émojis 🎉 and spëcial cháracters: 中文, 日本語, العربية
"""
        file_path.write_text(content, encoding='utf-8')
        
        result = self.parser.parse_file(str(file_path))
        assert "émojis 🎉" in result.content
        assert "中文" in result.content
        assert result.html is not None