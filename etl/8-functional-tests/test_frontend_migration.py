#!/usr/bin/env python3
"""
Frontend functional tests for migration quality.
Tests access actual WordPress frontend pages (not API).
"""

import requests
import re
from bs4 import BeautifulSoup

# Test configuration
WORDPRESS_SITE = "https://app-67d6f672c1ac1810207db362.closte.com"
API_BASE = f"{WORDPRESS_SITE}/?rest_route=/wp/v2"


def get_post_urls():
    """Get actual post URLs from WordPress API."""
    response = requests.get(f"{API_BASE}/posts&per_page=10")
    if response.status_code != 200:
        return []

    posts = response.json()
    return [{
        'slug': p['slug'],
        'url': p['link'],
        'title': p['title']['rendered']
    } for p in posts if p.get('link')]


def fetch_frontend_page(post_url):
    """Fetch actual frontend HTML page."""
    response = requests.get(post_url, timeout=30)
    if response.status_code == 200:
        return response.text
    return None


def test_post_has_title():
    """Test that migrated posts have titles."""
    posts = get_post_urls()
    assert len(posts) > 0, "No posts found to test"

    for post in posts[:3]:  # Test first 3 posts
        html = fetch_frontend_page(post['url'])
        assert html is not None, f"Could not fetch page at {post['url']}"

        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')

        assert title_tag is not None, f"No title tag found for {post['slug']}"
        # Title should contain the post title or site title
        assert len(title_tag.text.strip()) > 0, f"Empty title for {post['slug']}"


def test_post_has_content():
    """Test that migrated posts have substantial content."""
    posts = get_post_urls()
    assert len(posts) > 0, "No posts found to test"

    for post in posts[:3]:
        html = fetch_frontend_page(post['url'])
        assert html is not None, f"Could not fetch page at {post['url']}"

        soup = BeautifulSoup(html, 'html.parser')

        # Find main content area (common WordPress selectors)
        content = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=re.compile(r'content|post|entry', re.I))
        )

        assert content is not None, f"No content area found for {post['slug']}"

        text = content.get_text()
        assert len(text) > 100, f"Content too short for {post['slug']}: {len(text)} chars"


def test_no_raw_markdown():
    """Test that markdown is converted to HTML, not raw text."""
    posts = get_post_urls()
    assert len(posts) > 0, "No posts found to test"

    for post in posts[:5]:
        html = fetch_frontend_page(post['url'])
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')
        content = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=re.compile(r'content|post|entry', re.I))
        )

        if content:
            text = content.get_text()

            # Check for common raw markdown patterns
            assert not re.search(r'^#{1,6}\s+\w', text, re.M), \
                f"Raw markdown headers found in {post['slug']}"
            assert not ('[[' in text and ']]' in text), \
                f"Wiki-style links found in {post['slug']}"


def test_proper_html_structure():
    """Test that content has proper HTML structure."""
    posts = get_post_urls()
    assert len(posts) > 0, "No posts found to test"

    for post in posts[:3]:
        html = fetch_frontend_page(post['url'])
        assert html is not None, f"Could not fetch page at {post['url']}"

        soup = BeautifulSoup(html, 'html.parser')

        # Check for basic HTML structure
        assert soup.find('html'), f"No html tag in {post['slug']}"
        assert soup.find('body'), f"No body tag in {post['slug']}"

        # Check for content elements
        content = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=re.compile(r'content|post|entry', re.I))
        )

        assert content is not None, f"No content area in {post['slug']}"

        # Should have paragraphs
        paragraphs = content.find_all('p')
        assert len(paragraphs) > 0, f"No paragraphs found in {post['slug']}"