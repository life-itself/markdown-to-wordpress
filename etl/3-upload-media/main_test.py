#!/usr/bin/env python3
"""Tests for media uploader using real sample data."""

import pytest
import json
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import MediaUploader


class TestMediaUploader:
    """Test suite for media uploader."""
    
    @pytest.fixture
    def mock_uploader(self):
        """Create uploader with mocked API calls."""
        project_root = Path(__file__).parent.parent.parent
        input_dir = project_root / "sample-data"
        output_dir = project_root / "test-output"
        rename_dict_path = project_root / "etl/0-image-processing/test-output/image_rename_dict.json"
        
        output_dir.mkdir(exist_ok=True)
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'WORDPRESS_SITE_DOMAIN': 'test.wordpress.com',
            'WORDPRESS_OAUTH_TOKEN': 'test-token',
            'RETRY_DELAY': '100'
        }):
            uploader = MediaUploader(input_dir, output_dir, rename_dict_path)
            
        return uploader, input_dir, output_dir
    
    def test_initialization(self, mock_uploader):
        """Test uploader initialization."""
        uploader, _, _ = mock_uploader
        
        assert uploader.site_domain == 'test.wordpress.com'
        assert uploader.oauth_token == 'test-token'
        assert uploader.api_base == 'https://public-api.wordpress.com/wp/v2/sites/test.wordpress.com'
    
    def test_get_file_hash(self, mock_uploader):
        """Test file hash calculation."""
        uploader, input_dir, _ = mock_uploader
        
        # Create a temporary test file
        test_file = input_dir / 'test_hash.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('test content')
        
        try:
            hash1 = uploader.get_file_hash(test_file)
            hash2 = uploader.get_file_hash(test_file)
            
            assert hash1 == hash2  # Same file should have same hash
            assert len(hash1) == 32  # MD5 hash length
        finally:
            if test_file.exists():
                test_file.unlink()
    
    @patch('requests.get')
    def test_test_connection(self, mock_get, mock_uploader):
        """Test API connection test."""
        uploader, _, _ = mock_uploader
        
        # Mock successful response
        mock_get.return_value.status_code = 200
        assert uploader.test_connection() == True
        
        # Mock failed response
        mock_get.return_value.status_code = 401
        assert uploader.test_connection() == False
    
    @patch('requests.get')
    def test_check_existing_media(self, mock_get, mock_uploader):
        """Test checking for existing media."""
        uploader, _, _ = mock_uploader
        
        # Mock response with existing media
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'slug': 'test-image', 'title': {'rendered': 'test-image'}}
        ]
        mock_get.return_value = mock_response
        
        result = uploader.check_existing_media('test-image.jpg')
        assert result is not None
        assert result['id'] == 1
    
    @patch('requests.post')
    @patch('requests.get')
    def test_upload_image_mock(self, mock_get, mock_post, mock_uploader):
        """Test image upload with mocked API."""
        uploader, input_dir, _ = mock_uploader
        
        # Create a test image file
        test_image = input_dir / 'assets/images/test-upload.jpg'
        test_image.parent.mkdir(parents=True, exist_ok=True)
        test_image.write_bytes(b'fake image data')
        
        try:
            # Mock no existing media
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = []
            
            # Mock successful upload
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                'id': 123,
                'source_url': 'https://test.com/image.jpg',
                'slug': 'test-upload'
            }
            
            result = uploader.upload_image(test_image, 'test-upload.jpg')
            
            assert result is not None
            assert result['id'] == 123
            assert mock_post.called
            
        finally:
            if test_image.exists():
                test_image.unlink()
    
    def test_process_with_rename_dict(self, mock_uploader):
        """Test processing with rename dictionary."""
        uploader, input_dir, output_dir = mock_uploader
        
        # Mock the upload process to avoid actual API calls
        with patch.object(uploader, 'test_connection', return_value=True), \
             patch.object(uploader, 'upload_image', return_value={'id': 1, 'source_url': 'test.jpg', 'slug': 'test'}):
            
            # Should load rename dictionary from fixture setup
            if uploader.rename_dict:
                outputs = uploader.process_images()
                
                assert 'media_upload_map.json' in outputs
                # Check if output file was created
                output_file = output_dir / 'media_upload_map.json'
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                        assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])