"""Shared fixtures and configuration for pytest."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.types import Config, FrontMatter, MarkdownFile


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return Config(
        wordpress_url="https://example.com",
        username="testuser",
        password="testpass",
        auth_method="application_passwords",
        default_status="draft",
        default_author="admin",
        concurrency=4,
        retry_attempts=3,
        retry_delay=1.0,
        upload_media=True,
        media_max_size_mb=10
    )


@pytest.fixture
def sample_front_matter():
    """Create a sample front matter object."""
    return FrontMatter(
        title="Test Post Title",
        slug="test-post-slug",
        type="blog",
        subtitle="Test subtitle",
        description="Test description",
        date_published="2025-01-15T10:00:00Z",
        date_updated="2025-01-16T14:30:00Z",
        featured_image="./images/test.jpg",
        authors=["John Doe", "jane@example.com"],
        status="publish",
        featured=True,
        tags=["test", "sample"],
        categories=["Technology"],
        initiatives=["Innovation"],
        external_id="test-external-id"
    )


@pytest.fixture
def sample_event_front_matter():
    """Create a sample event front matter."""
    return FrontMatter(
        title="Test Event",
        slug="test-event",
        type="event",
        start_date="2025-10-01",
        end_date="2025-10-15",
        location_name="Test Venue",
        location_address="123 Test Street",
        host=["Test Organization"],
        registration_url="https://example.com/register"
    )


@pytest.fixture
def sample_podcast_front_matter():
    """Create a sample podcast front matter."""
    return FrontMatter(
        title="Episode 1: Test Episode",
        slug="episode-1",
        type="podcast",
        episode_number=1,
        audio_url="https://example.com/audio.mp3",
        duration="00:45:30",
        guests=["Guest One", "Guest Two"],
        show="Test Podcast Series"
    )


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2
- List item 3

Here's a link to [[Another Page]] and [[custom-slug|Custom Display Text]].

![Test Image](./images/test.jpg)

```python
def hello():
    print("Hello World")
```

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
"""


@pytest.fixture
def temp_markdown_file(tmp_path, sample_markdown_content):
    """Create a temporary markdown file for testing."""
    file_path = tmp_path / "test_post.md"
    content = """---
title: Test Post
slug: test-post
type: blog
tags:
  - test
  - sample
categories:
  - Technology
---

""" + sample_markdown_content
    
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def temp_markdown_dir(tmp_path):
    """Create a temporary directory structure with markdown files."""
    # Create directory structure
    (tmp_path / "blog").mkdir()
    (tmp_path / "events").mkdir()
    (tmp_path / "podcasts").mkdir()
    (tmp_path / "pages").mkdir()
    
    # Create blog post
    blog_content = """---
title: Blog Post
slug: blog-post
type: blog
---

Blog content here.
"""
    (tmp_path / "blog" / "post1.md").write_text(blog_content, encoding='utf-8')
    
    # Create event
    event_content = """---
title: Test Event
slug: test-event
type: event
start_date: 2025-10-01
end_date: 2025-10-02
---

Event description.
"""
    (tmp_path / "events" / "event1.md").write_text(event_content, encoding='utf-8')
    
    # Create podcast
    podcast_content = """---
title: Episode 1
slug: episode-1
type: podcast
episode_number: 1
audio_url: https://example.com/episode1.mp3
---

Episode notes.
"""
    (tmp_path / "podcasts" / "episode1.md").write_text(podcast_content, encoding='utf-8')
    
    # Create page
    page_content = """---
title: About Page
slug: about
type: page
---

About us content.
"""
    (tmp_path / "pages" / "about.md").write_text(page_content, encoding='utf-8')
    
    return str(tmp_path)


@pytest.fixture
def mock_wordpress_client():
    """Create a mock WordPress client for testing."""
    client = MagicMock()
    client.test_connection.return_value = True
    client.find_post_by_slug.return_value = None
    client.find_post_by_meta.return_value = None
    client.create_post.return_value = {"id": 123, "slug": "test-post"}
    client.update_post.return_value = {"id": 123, "slug": "test-post"}
    client.find_user_by_email.return_value = 1
    client.find_user_by_name.return_value = 1
    client.get_or_create_taxonomy_term.return_value = 10
    return client


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library for API testing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "name": "Test"}
    mock_response.raise_for_status = MagicMock()
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    
    mock_requests = MagicMock()
    mock_requests.Session.return_value = mock_session
    
    monkeypatch.setattr("src.wordpress_client.requests", mock_requests)
    return mock_requests