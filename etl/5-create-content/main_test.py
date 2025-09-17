#!/usr/bin/env python3
"""Tests for WordPress content creator using prepared content."""

import pytest
import json
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ContentCreator


class TestContentCreator:
    """Test suite for WordPress content creation."""

    @pytest.fixture
    def mock_creator(self):
        """Create content creator with mocked API calls."""
        project_root = Path(__file__).parent.parent.parent
        input_dir = project_root / "sample-data"
        output_dir = project_root / "test-output"

        output_dir.mkdir(exist_ok=True)

        # Mock environment variables
        with patch.dict(os.environ, {
            'WORDPRESS_SITE_DOMAIN': 'test.wordpress.com',
            'WORDPRESS_OAUTH_TOKEN': 'test-token',
            'RETRY_DELAY': '100'
        }):
            # Create sample prepared content
            sample_content = [
                {
                    'title': 'Test Blog Post',
                    'slug': 'test-blog-post',
                    'content': '<h1>Test Content</h1><p>This is a test post.</p>',
                    'excerpt': 'This is a test excerpt',
                    'type': 'post',
                    'status': 'draft',
                    'date': '2023-01-01T10:00:00',
                    'categories': ['test', 'blog'],
                    'tags': ['sample', 'testing'],
                    'featured_image': 'test-feature.jpg',
                    'meta': {
                        '_source_file': 'test.md'
                    }
                },
                {
                    'title': 'Test Page',
                    'slug': 'test-page',
                    'content': '<h1>Test Page Content</h1>',
                    'type': 'page',
                    'status': 'publish'
                }
            ]

            # Create temporary content file
            content_file = output_dir / 'test_prepared_content.json'
            with open(content_file, 'w') as f:
                json.dump(sample_content, f)

            # Create sample media map
            media_map = {
                'assets/images/test-image.jpg': {
                    'wordpress_id': 123,
                    'new_filename': 'test-feature.jpg',
                    'wordpress_url': 'https://test.com/wp-content/uploads/test-feature.jpg'
                }
            }

            media_map_file = output_dir / 'test_media_map.json'
            with open(media_map_file, 'w') as f:
                json.dump(media_map, f)

            creator = ContentCreator(
                input_dir,
                output_dir,
                content_file,
                media_map_file
            )

        return creator, input_dir, output_dir

    def test_initialization(self, mock_creator):
        """Test creator initialization."""
        creator, _, _ = mock_creator

        assert creator.site_domain == 'test.wordpress.com'
        assert creator.oauth_token == 'test-token'
        assert len(creator.prepared_content) == 2
        assert len(creator.media_map) == 1

    @patch('requests.get')
    def test_test_connection(self, mock_get, mock_creator):
        """Test API connection."""
        creator, _, _ = mock_creator

        # Mock successful connection
        mock_get.return_value.status_code = 200
        assert creator.test_connection() == True

        # Mock failed connection
        mock_get.return_value.status_code = 401
        assert creator.test_connection() == False

    def test_get_endpoint(self, mock_creator):
        """Test endpoint mapping."""
        creator, _, _ = mock_creator

        assert creator._get_endpoint('post') == 'posts'
        assert creator._get_endpoint('page') == 'pages'
        assert creator._get_endpoint('event') == 'events'
        assert creator._get_endpoint('podcast') == 'podcasts'
        assert creator._get_endpoint('unknown') == 'posts'  # fallback

    def test_get_featured_media_id(self, mock_creator):
        """Test media ID lookup."""
        creator, _, _ = mock_creator

        # Should find media ID by new filename
        media_id = creator._get_featured_media_id('test-feature.jpg')
        assert media_id == 123

        # Should return None for non-existent image
        media_id = creator._get_featured_media_id('non-existent.jpg')
        assert media_id is None

    @patch('requests.get')
    def test_check_existing_post(self, mock_get, mock_creator):
        """Test checking for existing posts."""
        creator, _, _ = mock_creator

        # Mock existing post found
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 456, 'slug': 'test-post'}]
        mock_get.return_value = mock_response

        result = creator.check_existing_post('test-post')
        assert result is not None
        assert result['id'] == 456

        # Mock no existing post
        mock_response.json.return_value = []
        result = creator.check_existing_post('non-existent-post')
        assert result is None

    @patch('requests.post')
    @patch('requests.get')
    def test_prepare_categories(self, mock_get, mock_post, mock_creator):
        """Test category creation and lookup."""
        creator, _, _ = mock_creator

        # Mock existing category
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'id': 1, 'name': 'Test'}
        ]

        # Mock new category creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'id': 2, 'name': 'Blog'}

        category_ids = creator._prepare_categories(['test', 'blog'])

        # Should return IDs for both categories
        assert len(category_ids) == 2
        assert 1 in category_ids  # existing category

    @patch('requests.post')
    @patch('requests.get')
    def test_create_or_update_post_create(self, mock_get, mock_post, mock_creator):
        """Test creating a new post."""
        creator, _, _ = mock_creator

        # Mock no existing post
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []

        # Mock successful post creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'id': 789,
            'title': {'rendered': 'Test Post'},
            'link': 'https://test.com/test-post'
        }

        post_data = {
            'title': 'Test Post',
            'slug': 'test-post',
            'content': 'Test content',
            'type': 'post'
        }

        result = creator.create_or_update_post(post_data)

        assert result is not None
        assert result['id'] == 789
        assert mock_post.called

    @patch('requests.post')
    @patch('requests.get')
    def test_create_or_update_post_update(self, mock_get, mock_post, mock_creator):
        """Test updating an existing post."""
        creator, _, _ = mock_creator

        # Mock existing post found
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'id': 999, 'slug': 'existing-post'}
        ]

        # Mock successful post update
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'id': 999,
            'title': {'rendered': 'Updated Post'},
            'link': 'https://test.com/existing-post'
        }

        post_data = {
            'title': 'Updated Post',
            'slug': 'existing-post',
            'content': 'Updated content',
            'type': 'post'
        }

        result = creator.create_or_update_post(post_data)

        assert result is not None
        assert result['id'] == 999

    def test_process_content_mock(self, mock_creator):
        """Test the complete content processing pipeline with mocks."""
        creator, _, output_dir = mock_creator

        # Mock all the API calls
        with patch.object(creator, 'test_connection', return_value=True), \
             patch.object(creator, 'create_or_update_post') as mock_create:

            # Mock successful creation
            mock_create.side_effect = [
                {'id': 1, 'title': {'rendered': 'Test Blog Post'}, 'link': 'https://test.com/test-blog-post'},
                {'id': 2, 'title': {'rendered': 'Test Page'}, 'link': 'https://test.com/test-page'}
            ]

            results = creator.process_content()

            # Check results
            assert results['summary']['total'] == 2
            assert results['summary']['created'] == 2
            assert results['summary']['failed'] == 0

            # Check output file was created
            output_file = output_dir / 'migration_results.json'
            assert output_file.exists()

            # Verify the content
            with open(output_file, 'r') as f:
                saved_results = json.load(f)
                assert saved_results['summary']['created'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])