"""Unit tests for the WordPress client module."""

import pytest
import requests
from unittest.mock import MagicMock, patch, call
import time

from src.wordpress_client import WordPressClient
from src.types import Config


class TestWordPressClient:
    """Test suite for WordPressClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config(
            wordpress_url="https://example.com",
            username="testuser",
            password="testpass",
            auth_method="application_passwords",
            retry_delay=0.1  # Short delay for testing
        )
        
    @patch('src.wordpress_client.requests.Session')
    def test_client_initialization(self, mock_session_class):
        """Test client initialization with auth and headers."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        
        assert client.base_url == "https://example.com"
        mock_session_class.assert_called_once()
        
        # Check auth was set
        assert mock_session.auth is not None
        
        # Check headers were set
        mock_session.headers.update.assert_called_with({
            'User-Agent': 'markdown-to-wordpress/1.0.0',
            'Content-Type': 'application/json'
        })
    
    @patch('src.wordpress_client.requests.Session')
    def test_test_connection_success(self, mock_session_class):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Test User", "id": 1}
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.test_connection()
        
        assert result is True
        mock_session.get.assert_called_with("https://example.com/wp-json/wp/v2/users/me")
        mock_response.raise_for_status.assert_called_once()
    
    @patch('src.wordpress_client.requests.Session')
    def test_test_connection_failure(self, mock_session_class):
        """Test failed connection test."""
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Connection failed")
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.test_connection()
        
        assert result is False
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_post_by_slug_found(self, mock_session_class):
        """Test finding a post by slug when it exists."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 123, "slug": "test-post"}]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_post_by_slug("test-post", "posts")
        
        assert result == {"id": 123, "slug": "test-post"}
        mock_session.get.assert_called_with(
            "https://example.com/wp-json/wp/v2/posts",
            params={"slug": "test-post", "per_page": 1}
        )
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_post_by_slug_not_found(self, mock_session_class):
        """Test finding a post by slug when it doesn't exist."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_post_by_slug("nonexistent", "posts")
        
        assert result is None
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_post_by_meta(self, mock_session_class):
        """Test finding a post by meta field."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 456, "meta": {"_external_id": "test-id"}}]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_post_by_meta("_external_id", "test-id", "posts")
        
        assert result == {"id": 456, "meta": {"_external_id": "test-id"}}
        mock_session.get.assert_called_with(
            "https://example.com/wp-json/wp/v2/posts",
            params={
                "meta_key": "_external_id",
                "meta_value": "test-id",
                "per_page": 1
            }
        )
    
    @patch('src.wordpress_client.requests.Session')
    @patch('time.sleep')
    def test_create_post_success(self, mock_sleep, mock_session_class):
        """Test successful post creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 789, "slug": "new-post"}
        
        mock_session = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        post_data = {
            "title": "New Post",
            "slug": "new-post",
            "content": "Content"
        }
        
        result = client.create_post(post_data, "posts")
        
        assert result == {"id": 789, "slug": "new-post"}
        mock_session.post.assert_called_with(
            "https://example.com/wp-json/wp/v2/posts",
            json=post_data
        )
        mock_response.raise_for_status.assert_called_once()
        mock_sleep.assert_called_once()  # Rate limiting
    
    @patch('src.wordpress_client.requests.Session')
    def test_create_post_failure(self, mock_session_class):
        """Test post creation failure."""
        mock_session = MagicMock()
        mock_session.post.side_effect = requests.RequestException("Creation failed")
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        post_data = {"title": "Test"}
        
        with pytest.raises(requests.RequestException):
            client.create_post(post_data, "posts")
    
    @patch('src.wordpress_client.requests.Session')
    @patch('time.sleep')
    def test_update_post_success(self, mock_sleep, mock_session_class):
        """Test successful post update."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123, "slug": "updated-post"}
        
        mock_session = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        post_data = {
            "title": "Updated Post",
            "slug": "updated-post"
        }
        
        result = client.update_post(123, post_data, "posts")
        
        assert result == {"id": 123, "slug": "updated-post"}
        mock_session.post.assert_called_with(
            "https://example.com/wp-json/wp/v2/posts/123",
            json=post_data
        )
        mock_response.raise_for_status.assert_called_once()
        mock_sleep.assert_called_once()  # Rate limiting
    
    @patch('src.wordpress_client.requests.Session')
    def test_get_or_create_taxonomy_term_existing(self, mock_session_class):
        """Test getting existing taxonomy term."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 10, "name": "Technology"},
            {"id": 11, "name": "Tech"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.get_or_create_taxonomy_term("categories", "Technology")
        
        assert result == 10
        mock_session.get.assert_called_with(
            "https://example.com/wp-json/wp/v2/categories",
            params={"search": "Technology", "per_page": 100}
        )
    
    @patch('src.wordpress_client.requests.Session')
    def test_get_or_create_taxonomy_term_case_insensitive(self, mock_session_class):
        """Test taxonomy term matching is case-insensitive."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 10, "name": "TECHNOLOGY"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.get_or_create_taxonomy_term("categories", "technology")
        
        assert result == 10
    
    @patch('src.wordpress_client.requests.Session')
    def test_get_or_create_taxonomy_term_create_new(self, mock_session_class):
        """Test creating new taxonomy term when not found."""
        # First call returns empty (not found)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = []
        
        # Second call creates new term
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {"id": 20, "name": "New Term"}
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.get_or_create_taxonomy_term("tags", "New Term")
        
        assert result == 20
        mock_session.post.assert_called_with(
            "https://example.com/wp-json/wp/v2/tags",
            json={"name": "New Term", "slug": "new-term"}
        )
    
    @patch('src.wordpress_client.requests.Session')
    def test_create_taxonomy_term_conflict(self, mock_session_class):
        """Test handling of conflict when creating taxonomy term."""
        # First search returns empty
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = []
        
        # Create attempt returns 409 conflict
        mock_post_response = MagicMock()
        mock_post_response.status_code = 409
        
        # Second search finds the term
        mock_get_response2 = MagicMock()
        mock_get_response2.json.return_value = [{"id": 30, "name": "Existing"}]
        
        mock_session = MagicMock()
        mock_session.get.side_effect = [mock_get_response, mock_get_response2]
        mock_session.post.return_value = mock_post_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.get_or_create_taxonomy_term("tags", "Existing")
        
        assert result == 30
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_user_by_email_found(self, mock_session_class):
        """Test finding user by email."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 5, "email": "test@example.com"},
            {"id": 6, "email": "other@example.com"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_user_by_email("test@example.com")
        
        assert result == 5
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_user_by_email_case_insensitive(self, mock_session_class):
        """Test email matching is case-insensitive."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 5, "email": "TEST@EXAMPLE.COM"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_user_by_email("test@example.com")
        
        assert result == 5
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_user_by_email_not_found(self, mock_session_class):
        """Test user not found by email."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_user_by_name_found(self, mock_session_class):
        """Test finding user by display name."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 7, "name": "John Doe"},
            {"id": 8, "name": "Jane Smith"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_user_by_name("John Doe")
        
        assert result == 7
    
    @patch('src.wordpress_client.requests.Session')
    def test_find_user_by_name_case_insensitive(self, mock_session_class):
        """Test name matching is case-insensitive."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 7, "name": "JOHN DOE"}
        ]
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        result = client.find_user_by_name("john doe")
        
        assert result == 7
    
    def test_generate_slug(self):
        """Test slug generation."""
        client = WordPressClient(self.config)
        
        assert client._generate_slug("Hello World") == "hello-world"
        assert client._generate_slug("Test_With_Underscores") == "test-with-underscores"
        assert client._generate_slug("Special!@#$%^&*()Characters") == "specialcharacters"
        assert client._generate_slug("  Leading and Trailing  ") == "leading-and-trailing"
        assert client._generate_slug("Multiple   Spaces") == "multiple-spaces"
        assert client._generate_slug("CamelCaseText") == "camelcasetext"
    
    @patch('src.wordpress_client.requests.Session')
    def test_error_handling_in_api_calls(self, mock_session_class):
        """Test error handling in various API calls."""
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("API Error")
        mock_session.post.side_effect = requests.RequestException("API Error")
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(self.config)
        
        # Test find_post_by_slug error handling
        result = client.find_post_by_slug("test", "posts")
        assert result is None
        
        # Test find_post_by_meta error handling
        result = client.find_post_by_meta("key", "value", "posts")
        assert result is None
        
        # Test find_user_by_email error handling
        result = client.find_user_by_email("test@example.com")
        assert result is None
        
        # Test find_user_by_name error handling
        result = client.find_user_by_name("Test User")
        assert result is None
        
        # Test get_or_create_taxonomy_term error handling
        result = client.get_or_create_taxonomy_term("tags", "Test")
        assert result is None
    
    @patch('src.wordpress_client.requests.Session')
    def test_base_url_trailing_slash_removal(self, mock_session_class):
        """Test that trailing slashes are removed from base URL."""
        config = Config(
            wordpress_url="https://example.com/",
            username="testuser",
            password="testpass"
        )
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        client = WordPressClient(config)
        assert client.base_url == "https://example.com"