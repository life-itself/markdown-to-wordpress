#!/usr/bin/env python3
"""
Batch content creation script for Step 5.
Creates all WordPress posts/pages from prepared content.
"""

import json
import requests
import os
import base64
import time
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


def create_all_content(content_file: Path, media_map_file: Path, output_dir: Path, batch_size: int = 10):
    """Create all WordPress posts/pages from prepared content."""

    # Load environment variables
    load_dotenv()

    # WordPress credentials
    site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
    username = os.getenv('WORDPRESS_USERNAME')
    app_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')

    if not all([site_domain, username, app_password]):
        raise ValueError("Missing WordPress credentials in .env file")

    # Set up Basic Auth
    credentials = f'{username}:{app_password}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }

    # WordPress API endpoints
    posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts'
    pages_url = f'https://{site_domain}/?rest_route=/wp/v2/pages'

    # Load prepared content
    print("Loading prepared content...")
    with open(content_file, 'r', encoding='utf-8') as f:
        all_content = json.load(f)

    # Load media map
    print("Loading media map...")
    with open(media_map_file, 'r', encoding='utf-8') as f:
        media_map = json.load(f)

    print(f"\n=== STARTING BATCH CONTENT CREATION ===")
    print(f"Total posts to create: {len(all_content)}")
    print(f"Batch size: {batch_size}")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    success_count = 0
    failed_count = 0
    results = []
    errors = []

    # Process all posts
    for i, post_data in enumerate(all_content):
        # Progress indicator
        if i % batch_size == 0:
            print(f"\n[{i+1}/{len(all_content)}] Processing batch...")

        title = post_data.get('title', 'Untitled')

        # Prepare WordPress post data
        wp_post = {
            'title': title,
            'content': post_data.get('content', ''),
            'excerpt': post_data.get('excerpt', ''),
            'slug': post_data.get('slug', ''),
            'status': 'draft',  # Always create as draft for safety
            'type': post_data.get('type', 'post')
        }

        # Add date if available
        if post_data.get('date'):
            date_str = post_data['date']
            if 'T' not in str(date_str):
                date_str = f"{date_str}T10:00:00"
            wp_post['date'] = date_str

        # Add featured image if available
        featured_media_id = None
        if post_data.get('featured_image'):
            for path, media_info in media_map.items():
                if post_data['featured_image'] in path:
                    featured_media_id = media_info['wordpress_id']
                    wp_post['featured_media'] = featured_media_id
                    break

        # Determine endpoint based on type
        endpoint = pages_url if post_data.get('type') == 'page' else posts_url

        # Create the post
        try:
            response = requests.post(endpoint, headers=headers, json=wp_post)

            if response.status_code in [200, 201]:
                result = response.json()
                success_count += 1

                # Store result
                results.append({
                    'title': title,
                    'slug': post_data.get('slug', ''),
                    'wordpress_id': result['id'],
                    'wordpress_url': result['link'],
                    'type': post_data.get('type', 'post'),
                    'featured_media': featured_media_id,
                    'source_file': post_data.get('meta', {}).get('_source_file', '')
                })

                # Progress indicator
                print("+", end="", flush=True)

            else:
                failed_count += 1
                errors.append({
                    'title': title,
                    'slug': post_data.get('slug', ''),
                    'status_code': response.status_code,
                    'error': response.text[:200]
                })
                print("-", end="", flush=True)

        except Exception as e:
            failed_count += 1
            errors.append({
                'title': title,
                'slug': post_data.get('slug', ''),
                'error': str(e)
            })
            print("x", end="", flush=True)

        # Rate limiting
        if i % 5 == 0 and i > 0:
            time.sleep(1)  # Pause every 5 posts

    # Save results
    print(f"\n\nSaving results...")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / 'content_creation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if errors:
        with open(output_dir / 'creation_errors.json', 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)

    # Final summary
    print("\n" + "=" * 50)
    print("=== BATCH CREATION COMPLETE ===")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successfully created: {success_count}/{len(all_content)} ({success_count/len(all_content)*100:.1f}%)")
    print(f"Failed: {failed_count}/{len(all_content)}")

    if success_count > 0:
        print(f"\nResults saved to: {output_dir / 'content_creation_results.json'}")
    if errors:
        print(f"Errors saved to: {output_dir / 'creation_errors.json'}")

    print("\n+ Migration completed! All posts created as drafts in WordPress.")
    print("Visit your WordPress admin to review and publish: ")
    print(f"https://{site_domain}/wp-admin/edit.php")

    return success_count, failed_count


def main():
    """Main entry point for batch content creation."""
    parser = argparse.ArgumentParser(description='Batch create WordPress content')
    parser.add_argument('--content-file', type=Path,
                        default=Path('../1-prepare-content/full-migration-output/prepared_content.json'),
                        help='Path to prepared content JSON file')
    parser.add_argument('--media-map', type=Path,
                        default=Path('../3-upload-media/full-migration-output/media_upload_map.json'),
                        help='Path to media upload map JSON file')
    parser.add_argument('--output-dir', type=Path, default=Path('./full-migration-output'),
                        help='Output directory for results')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of posts to process before showing progress')

    args = parser.parse_args()

    # Run batch creation
    try:
        success, failed = create_all_content(
            args.content_file,
            args.media_map,
            args.output_dir,
            args.batch_size
        )

        # Exit with error code if any failures
        if failed > 0:
            exit(1)

    except Exception as e:
        print(f"Error during batch creation: {e}")
        exit(1)


if __name__ == '__main__':
    main()