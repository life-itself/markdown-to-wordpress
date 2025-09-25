#!/usr/bin/env python3
"""
Step 3: Upload Media
Uploads images to WordPress Media Library using the REST API.
"""

import os
import json
import argparse
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import time
import mimetypes


class MediaUploader:
    """Uploads media files to WordPress."""
    
    def __init__(self, input_dir: Path, output_dir: Path, rename_dict_path: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Configure WordPress connection
        self.site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.app_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')

        if not self.site_domain or not self.username or not self.app_password:
            raise ValueError("Missing WordPress credentials in .env file")

        # Self-hosted WordPress API endpoint
        self.api_base = f"https://{self.site_domain}/?rest_route=/wp/v2"

        # Set up Basic Auth headers
        import base64
        credentials = f'{self.username}:{self.app_password}'
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
        }
        
        # Load rename dictionary
        self.rename_dict = {}
        if rename_dict_path and rename_dict_path.exists():
            with open(rename_dict_path, 'r') as f:
                self.rename_dict = json.load(f)
        
        # Track uploaded media
        self.upload_map = {}  # original_path -> wordpress_media_data
        self.upload_errors = []
    
    def test_connection(self) -> bool:
        """Test WordPress API connection."""
        try:
            response = requests.get(
                f"{self.api_base}/media",
                headers=self.headers,
                params={'per_page': 1}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for deduplication."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_existing_media(self, filename: str) -> Optional[Dict]:
        """Check if media with this filename already exists in WordPress."""
        try:
            response = requests.get(
                f"{self.api_base}/media",
                headers=self.headers,
                params={
                    'search': filename,
                    'per_page': 100
                }
            )
            
            if response.status_code == 200:
                media_items = response.json()
                # Look for exact filename match
                for item in media_items:
                    if item.get('slug') == Path(filename).stem:
                        return item
                    # Also check title
                    if item.get('title', {}).get('rendered') == Path(filename).stem:
                        return item
            
            return None
            
        except Exception as e:
            print(f"Error checking existing media: {e}")
            return None
    
    def upload_image(self, image_path: Path, new_filename: Optional[str] = None) -> Optional[Dict]:
        """Upload a single image to WordPress Media Library."""
        if not image_path.exists():
            print(f"  ✗ Image not found: {image_path}")
            return None
        
        # Use new filename if provided
        filename = new_filename if new_filename else image_path.name
        
        # Check if already uploaded
        existing = self.check_existing_media(filename)
        if existing:
            print(f"  ~ Already exists: {filename} (ID: {existing['id']})")
            return existing
        
        try:
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(image_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Read file
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            # Prepare multipart upload
            files = {
                'file': (filename, file_data, mime_type)
            }
            
            # Upload to WordPress
            response = requests.post(
                f"{self.api_base}/media",
                headers=self.headers,
                files=files
            )
            
            if response.status_code in [200, 201]:
                media_data = response.json()
                print(f"  + Uploaded: {filename} (ID: {media_data['id']})")
                return media_data
            else:
                error_msg = f"Failed to upload {filename}: {response.status_code} - {response.text}"
                print(f"  x {error_msg}")
                self.upload_errors.append({
                    'file': str(image_path),
                    'error': error_msg
                })
                return None
                
        except Exception as e:
            error_msg = f"Exception uploading {image_path}: {e}"
            print(f"  x {error_msg}")
            self.upload_errors.append({
                'file': str(image_path),
                'error': str(e)
            })
            return None
    
    def process_images(self) -> Dict:
        """Process and upload all images based on rename dictionary."""
        print("Starting media upload...")
        
        # Test connection first
        if not self.test_connection():
            raise ConnectionError("Failed to connect to WordPress API")
        
        print(f"Connected to {self.site_domain}")
        
        if not self.rename_dict:
            print("No rename dictionary provided, looking for images to upload...")
            # Find all images in input directory
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
            for root, dirs, files in os.walk(self.input_dir):
                for file in files:
                    if Path(file).suffix.lower() in image_extensions:
                        img_path = Path(root) / file
                        rel_path = img_path.relative_to(self.input_dir)
                        self.rename_dict[str(rel_path)] = file
        
        total_images = len(self.rename_dict)
        print(f"Found {total_images} images to upload")
        
        uploaded_count = 0
        skipped_count = 0
        
        # Upload each image
        for old_path, new_filename in self.rename_dict.items():
            # Construct full path
            full_path = self.input_dir / old_path
            
            if not full_path.exists():
                # Try with forward slashes
                full_path = self.input_dir / old_path.replace('\\', '/')
            
            if full_path.exists():
                print(f"\nProcessing: {old_path} -> {new_filename}")
                media_data = self.upload_image(full_path, new_filename)
                
                if media_data:
                    self.upload_map[old_path] = {
                        'wordpress_id': media_data['id'],
                        'wordpress_url': media_data['source_url'],
                        'wordpress_slug': media_data['slug'],
                        'original_path': str(old_path),
                        'new_filename': new_filename
                    }
                    
                    if 'Already exists' in str(media_data.get('message', '')):
                        skipped_count += 1
                    else:
                        uploaded_count += 1
                
                # Rate limiting
                time.sleep(float(os.getenv('RETRY_DELAY', 1000)) / 1000)
            else:
                print(f"  x File not found: {full_path}")
                self.upload_errors.append({
                    'file': str(old_path),
                    'error': 'File not found'
                })
        
        # Save upload map
        output_file = self.output_dir / 'media_upload_map.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.upload_map, f, indent=2)
        print(f"\nSAVED: {output_file}")
        
        # Save errors if any
        if self.upload_errors:
            error_file = self.output_dir / 'upload_errors.json'
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({'errors': self.upload_errors}, f, indent=2)
            print(f"SAVED: {error_file}")
        
        print(f"\nSummary:")
        print(f"   Uploaded: {uploaded_count} new images")
        print(f"   Reused: {skipped_count} existing images")
        print(f"   Errors: {len(self.upload_errors)}")
        
        return {
            'media_upload_map.json': self.upload_map,
            'upload_errors.json': {'errors': self.upload_errors} if self.upload_errors else {}
        }


def main():
    parser = argparse.ArgumentParser(description='Upload media to WordPress')
    parser.add_argument('--input-dir', default='../../sample-data',
                       help='Input directory containing images')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for upload map')
    parser.add_argument('--rename-dict',
                       help='Path to rename dictionary from step 0')
    
    args = parser.parse_args()
    
    uploader = MediaUploader(
        Path(args.input_dir),
        Path(args.output_dir),
        Path(args.rename_dict) if args.rename_dict else None
    )
    
    uploader.process_images()


if __name__ == '__main__':
    main()