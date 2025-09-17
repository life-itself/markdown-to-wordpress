#!/usr/bin/env python3
"""
Step 5: Create Content
Creates WordPress posts/pages from prepared content with proper metadata and media.
"""

import os
import json
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import time


class ContentCreator:
    """Creates WordPress content from prepared JSON data."""

    def __init__(self, input_dir: Path, output_dir: Path,
                 content_file: Optional[Path] = None,
                 media_map_file: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load environment variables
        load_dotenv()

        # Configure WordPress connection
        self.site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
        self.oauth_token = os.getenv('WORDPRESS_OAUTH_TOKEN')

        if not self.site_domain or not self.oauth_token:
            raise ValueError("Missing WordPress credentials in .env file")

        # WordPress.com API endpoint
        self.api_base = f"https://public-api.wordpress.com/wp/v2/sites/{self.site_domain}"

        # Set up headers
        self.headers = {
            'Authorization': f'Bearer {self.oauth_token}',
            'Content-Type': 'application/json'
        }

        # Load prepared content
        self.prepared_content = []
        if content_file and content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                self.prepared_content = json.load(f)

        # Load media map
        self.media_map = {}
        if media_map_file and media_map_file.exists():
            with open(media_map_file, 'r', encoding='utf-8') as f:
                self.media_map = json.load(f)

        # Track created content
        self.created_posts = []
        self.updated_posts = []
        self.failed_posts = []

    def test_connection(self) -> bool:
        """Test WordPress API connection."""
        try:
            response = requests.get(
                f"{self.api_base}/posts",
                headers=self.headers,
                params={'per_page': 1}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def check_existing_post(self, slug: str, post_type: str = 'post') -> Optional[Dict]:
        """Check if a post with this slug already exists."""
        endpoint = f"{self.api_base}/{self._get_endpoint(post_type)}"

        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={'slug': slug, 'per_page': 1}
            )

            if response.status_code == 200:
                posts = response.json()
                if posts and len(posts) > 0:
                    return posts[0]

            return None

        except Exception as e:
            print(f"Error checking existing post: {e}")
            return None

    def _get_endpoint(self, post_type: str) -> str:
        """Get the WordPress API endpoint for a post type."""
        endpoints = {
            'post': 'posts',
            'page': 'pages',
            'event': 'events',  # Custom post type
            'podcast': 'podcasts'  # Custom post type
        }
        return endpoints.get(post_type, 'posts')

    def _get_featured_media_id(self, image_filename: str) -> Optional[int]:
        """Get WordPress media ID from the upload map."""
        if not image_filename or not self.media_map:
            return None

        # Look for the image in the media map
        for original_path, media_info in self.media_map.items():
            if media_info.get('new_filename') == image_filename:
                return media_info.get('wordpress_id')
            # Also check if it matches the original filename
            if original_path.endswith(image_filename):
                return media_info.get('wordpress_id')

        return None

    def _prepare_categories(self, categories: List[str]) -> List[int]:
        """Ensure categories exist and return their IDs."""
        category_ids = []

        for category_name in categories:
            # Check if category exists
            response = requests.get(
                f"{self.api_base}/categories",
                headers=self.headers,
                params={'search': category_name, 'per_page': 100}
            )

            if response.status_code == 200:
                existing_cats = response.json()
                # Look for exact match
                for cat in existing_cats:
                    if cat['name'].lower() == category_name.lower():
                        category_ids.append(cat['id'])
                        break
                else:
                    # Create new category
                    create_response = requests.post(
                        f"{self.api_base}/categories",
                        headers=self.headers,
                        json={'name': category_name}
                    )
                    if create_response.status_code in [200, 201]:
                        new_cat = create_response.json()
                        category_ids.append(new_cat['id'])

        return category_ids

    def _prepare_tags(self, tags: List[str]) -> List[int]:
        """Ensure tags exist and return their IDs."""
        tag_ids = []

        for tag_name in tags:
            # Check if tag exists
            response = requests.get(
                f"{self.api_base}/tags",
                headers=self.headers,
                params={'search': tag_name, 'per_page': 100}
            )

            if response.status_code == 200:
                existing_tags = response.json()
                # Look for exact match
                for tag in existing_tags:
                    if tag['name'].lower() == tag_name.lower():
                        tag_ids.append(tag['id'])
                        break
                else:
                    # Create new tag
                    create_response = requests.post(
                        f"{self.api_base}/tags",
                        headers=self.headers,
                        json={'name': tag_name}
                    )
                    if create_response.status_code in [200, 201]:
                        new_tag = create_response.json()
                        tag_ids.append(new_tag['id'])

        return tag_ids

    def create_or_update_post(self, post_data: Dict) -> Optional[Dict]:
        """Create or update a WordPress post."""
        post_type = post_data.get('type', 'post')
        slug = post_data.get('slug')

        # Check if post exists
        existing_post = None
        if slug:
            existing_post = self.check_existing_post(slug, post_type)

        # Prepare WordPress data
        wp_data = {
            'title': post_data.get('title', ''),
            'content': post_data.get('content', ''),
            'excerpt': post_data.get('excerpt', ''),
            'slug': slug,
            'status': post_data.get('status', 'draft')
        }

        # Add date if provided (convert to proper WordPress format)
        if post_data.get('date'):
            # WordPress expects ISO 8601 format
            date_str = post_data['date']
            if isinstance(date_str, str):
                # If it's already a string, try to parse and reformat
                try:
                    from datetime import datetime
                    if date_str and date_str != 'None':
                        # Handle different date formats
                        if 'T' in date_str:
                            # Already has time component
                            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            # Date only, add time component
                            dt = datetime.fromisoformat(date_str + 'T10:00:00')
                        wp_data['date'] = dt.isoformat()
                except Exception as e:
                    # If parsing fails, skip the date
                    print(f"    Warning: Could not parse date '{date_str}': {e}, skipping")

        # Add featured image if available
        featured_image = post_data.get('featured_image')
        if featured_image:
            media_id = self._get_featured_media_id(featured_image)
            if media_id:
                wp_data['featured_media'] = media_id

        # Add categories if post type supports them
        if post_type == 'post' and post_data.get('categories'):
            category_ids = self._prepare_categories(post_data['categories'])
            if category_ids:
                wp_data['categories'] = category_ids

        # Add tags if post type supports them
        if post_type in ['post', 'page'] and post_data.get('tags'):
            tag_ids = self._prepare_tags(post_data['tags'])
            if tag_ids:
                wp_data['tags'] = tag_ids

        # Add custom meta fields
        if post_data.get('meta'):
            wp_data['meta'] = post_data['meta']

        # Determine endpoint
        endpoint = f"{self.api_base}/{self._get_endpoint(post_type)}"

        try:
            if existing_post:
                # Update existing post
                response = requests.post(
                    f"{endpoint}/{existing_post['id']}",
                    headers=self.headers,
                    json=wp_data
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  ~ Updated: {post_data.get('title')} (ID: {result['id']})")
                    return result
                else:
                    error_msg = f"Failed to update: {response.status_code} - {response.text}"
                    print(f"  x {error_msg}")
                    return None
            else:
                # Create new post
                response = requests.post(
                    endpoint,
                    headers=self.headers,
                    json=wp_data
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  + Created: {post_data.get('title')} (ID: {result['id']})")
                    return result
                else:
                    error_msg = f"Failed to create: {response.status_code} - {response.text}"
                    print(f"  x {error_msg}")
                    return None

        except Exception as e:
            print(f"  x Exception: {e}")
            return None

    def process_content(self) -> Dict:
        """Process all prepared content and create WordPress posts."""
        print("Starting content creation...")

        # Test connection first
        if not self.test_connection():
            raise ConnectionError("Failed to connect to WordPress API")

        print(f"Connected to {self.site_domain}")
        print(f"Processing {len(self.prepared_content)} items")

        for i, post_data in enumerate(self.prepared_content, 1):
            print(f"\n[{i}/{len(self.prepared_content)}] Processing: {post_data.get('title', 'Untitled')}")

            result = self.create_or_update_post(post_data)

            if result:
                if 'Updated' in str(result.get('message', '')):
                    self.updated_posts.append({
                        'wordpress_id': result['id'],
                        'title': post_data.get('title'),
                        'slug': post_data.get('slug'),
                        'type': post_data.get('type'),
                        'url': result.get('link')
                    })
                else:
                    self.created_posts.append({
                        'wordpress_id': result['id'],
                        'title': post_data.get('title'),
                        'slug': post_data.get('slug'),
                        'type': post_data.get('type'),
                        'url': result.get('link')
                    })
            else:
                self.failed_posts.append({
                    'title': post_data.get('title'),
                    'slug': post_data.get('slug'),
                    'type': post_data.get('type'),
                    'error': 'Creation/Update failed'
                })

            # Rate limiting
            time.sleep(float(os.getenv('RETRY_DELAY', 1000)) / 1000)

        # Save results
        results = {
            'created': self.created_posts,
            'updated': self.updated_posts,
            'failed': self.failed_posts,
            'summary': {
                'total': len(self.prepared_content),
                'created': len(self.created_posts),
                'updated': len(self.updated_posts),
                'failed': len(self.failed_posts)
            }
        }

        output_file = self.output_dir / 'migration_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\nSAVED: {output_file}")

        # Print summary
        print(f"\nSummary:")
        print(f"   Total processed: {len(self.prepared_content)}")
        print(f"   Created: {len(self.created_posts)}")
        print(f"   Updated: {len(self.updated_posts)}")
        print(f"   Failed: {len(self.failed_posts)}")

        return results


def main():
    parser = argparse.ArgumentParser(description='Create WordPress content')
    parser.add_argument('--input-dir', default='../../sample-data',
                       help='Input directory (not used directly but for consistency)')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for results')
    parser.add_argument('--content-file', required=True,
                       help='Path to prepared content JSON from Step 1')
    parser.add_argument('--media-map',
                       help='Path to media upload map from Step 3')

    args = parser.parse_args()

    creator = ContentCreator(
        Path(args.input_dir),
        Path(args.output_dir),
        Path(args.content_file) if args.content_file else None,
        Path(args.media_map) if args.media_map else None
    )

    creator.process_content()


if __name__ == '__main__':
    main()