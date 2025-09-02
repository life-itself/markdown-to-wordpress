"""WordPress API client for content migration."""

import requests
import time
from typing import Dict, Any, Optional, List
from requests.auth import HTTPBasicAuth
import logging

from .types import WordPressPost, Config

logger = logging.getLogger(__name__)


class WordPressClient:
    """WordPress REST API client."""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.wordpress_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication
        if config.auth_method == "application_passwords":
            self.session.auth = HTTPBasicAuth(config.username, config.password)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'markdown-to-wordpress/1.0.0',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Test connection to WordPress API."""
        try:
            response = self.session.get(f"{self.base_url}/wp-json/wp/v2/users/me")
            response.raise_for_status()
            
            user_data = response.json()
            logger.info(f"Connected to WordPress as: {user_data.get('name', 'Unknown')}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"WordPress connection failed: {e}")
            return False
    
    def find_post_by_slug(self, slug: str, post_type: str = "posts") -> Optional[Dict[str, Any]]:
        """Find a post by slug."""
        try:
            response = self.session.get(
                f"{self.base_url}/wp-json/wp/v2/{post_type}",
                params={"slug": slug, "per_page": 1}
            )
            response.raise_for_status()
            
            posts = response.json()
            return posts[0] if posts else None
            
        except requests.RequestException as e:
            logger.debug(f"Post not found by slug '{slug}': {e}")
            return None
    
    def find_post_by_meta(self, meta_key: str, meta_value: str, post_type: str = "posts") -> Optional[Dict[str, Any]]:
        """Find a post by meta field."""
        try:
            response = self.session.get(
                f"{self.base_url}/wp-json/wp/v2/{post_type}",
                params={
                    "meta_key": meta_key,
                    "meta_value": meta_value,
                    "per_page": 1
                }
            )
            response.raise_for_status()
            
            posts = response.json()
            return posts[0] if posts else None
            
        except requests.RequestException as e:
            logger.debug(f"Post not found by meta {meta_key}={meta_value}: {e}")
            return None
    
    def create_post(self, post_data: Dict[str, Any], post_type: str = "posts") -> Dict[str, Any]:
        """Create a new post."""
        try:
            # Add rate limiting
            time.sleep(self.config.retry_delay / 4)  # Basic rate limiting
            
            response = self.session.post(
                f"{self.base_url}/wp-json/wp/v2/{post_type}",
                json=post_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created post: {post_data.get('slug')} (ID: {result.get('id')})")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to create post {post_data.get('slug', 'unknown')}: {e}")
            raise
    
    def update_post(self, post_id: int, post_data: Dict[str, Any], post_type: str = "posts") -> Dict[str, Any]:
        """Update an existing post."""
        try:
            # Add rate limiting
            time.sleep(self.config.retry_delay / 4)  # Basic rate limiting
            
            response = self.session.post(
                f"{self.base_url}/wp-json/wp/v2/{post_type}/{post_id}",
                json=post_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Updated post: {post_data.get('slug')} (ID: {post_id})")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to update post {post_id}: {e}")
            raise
    
    def get_or_create_taxonomy_term(self, taxonomy: str, term_name: str) -> Optional[int]:
        """Get taxonomy term ID or create if it doesn't exist."""
        try:
            # First, try to find existing term
            response = self.session.get(
                f"{self.base_url}/wp-json/wp/v2/{taxonomy}",
                params={"search": term_name, "per_page": 100}
            )
            response.raise_for_status()
            
            terms = response.json()
            
            # Look for exact match
            for term in terms:
                if term.get('name', '').lower() == term_name.lower():
                    return term['id']
            
            # Create new term if not found
            return self._create_taxonomy_term(taxonomy, term_name)
            
        except requests.RequestException as e:
            logger.error(f"Failed to get taxonomy term {taxonomy}/{term_name}: {e}")
            return None
    
    def _create_taxonomy_term(self, taxonomy: str, term_name: str) -> Optional[int]:
        """Create a new taxonomy term."""
        try:
            term_data = {
                "name": term_name,
                "slug": self._generate_slug(term_name)
            }
            
            response = self.session.post(
                f"{self.base_url}/wp-json/wp/v2/{taxonomy}",
                json=term_data
            )
            
            if response.status_code == 409:  # Conflict - term exists
                # Try to get existing term
                return self.get_or_create_taxonomy_term(taxonomy, term_name)
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created taxonomy term: {taxonomy}/{term_name} (ID: {result.get('id')})")
            return result['id']
            
        except requests.RequestException as e:
            logger.error(f"Failed to create taxonomy term {taxonomy}/{term_name}: {e}")
            return None
    
    def find_user_by_email(self, email: str) -> Optional[int]:
        """Find user ID by email."""
        try:
            response = self.session.get(
                f"{self.base_url}/wp-json/wp/v2/users",
                params={"search": email, "per_page": 100}
            )
            response.raise_for_status()
            
            users = response.json()
            for user in users:
                if user.get('email', '').lower() == email.lower():
                    return user['id']
            
            return None
            
        except requests.RequestException as e:
            logger.debug(f"User not found by email {email}: {e}")
            return None
    
    def find_user_by_name(self, name: str) -> Optional[int]:
        """Find user ID by display name."""
        try:
            response = self.session.get(
                f"{self.base_url}/wp-json/wp/v2/users",
                params={"search": name, "per_page": 100}
            )
            response.raise_for_status()
            
            users = response.json()
            for user in users:
                if user.get('name', '').lower() == name.lower():
                    return user['id']
            
            return None
            
        except requests.RequestException as e:
            logger.debug(f"User not found by name {name}: {e}")
            return None
    
    def _generate_slug(self, text: str) -> str:
        """Generate URL-friendly slug."""
        import re
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')