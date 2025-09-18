#!/usr/bin/env python3
"""
Bulk publish all draft posts to make them live.
"""

import json
import requests
import os
import base64
import time
from pathlib import Path
from dotenv import load_dotenv

def setup_wordpress_client():
    """Setup WordPress API client."""
    load_dotenv()

    site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
    username = os.getenv('WORDPRESS_USERNAME')
    app_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')

    if not all([site_domain, username, app_password]):
        raise ValueError("Missing WordPress credentials in .env file")

    credentials = f'{username}:{app_password}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }

    return site_domain, headers

def bulk_publish_posts():
    """Publish all draft posts from the migration."""
    print("Starting bulk publication of migrated content...")

    # Setup
    site_domain, headers = setup_wordpress_client()

    # Load creation results to get all post IDs
    results_file = Path('etl/5-create-content/full-migration-output/content_creation_results.json')
    with open(results_file, 'r', encoding='utf-8') as f:
        creation_results = json.load(f)

    print(f"Found {len(creation_results)} posts to publish")

    success_count = 0
    failed_count = 0
    failed_posts = []

    print("Publishing posts...")
    print("Progress: ", end="", flush=True)

    for i, post in enumerate(creation_results):
        try:
            post_id = post['wordpress_id']
            title = post['title']

            # Update post status to 'publish'
            update_data = {'status': 'publish'}
            update_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}'

            response = requests.post(update_url, headers=headers, json=update_data)

            if response.status_code in [200, 201]:
                success_count += 1
                print("+", end="", flush=True)
            else:
                failed_count += 1
                failed_posts.append({
                    'id': post_id,
                    'title': title,
                    'error': f"HTTP {response.status_code}: {response.text[:100]}"
                })
                print("-", end="", flush=True)

            # Progress indicator every 50 posts
            if (i + 1) % 50 == 0:
                print(f" [{i+1}/{len(creation_results)}]", end="", flush=True)

            # Rate limiting - pause every 10 requests
            if (i + 1) % 10 == 0:
                time.sleep(1)

        except Exception as e:
            failed_count += 1
            failed_posts.append({
                'id': post.get('wordpress_id', 'Unknown'),
                'title': post.get('title', 'Unknown'),
                'error': str(e)
            })
            print("x", end="", flush=True)

    print(f"\n\nBulk publication completed!")
    print("="*50)
    print(f"Successfully published: {success_count}/{len(creation_results)} ({success_count/len(creation_results)*100:.1f}%)")
    print(f"Failed: {failed_count}")

    if failed_posts:
        print(f"\nFailed posts:")
        for failed in failed_posts[:5]:  # Show first 5 failures
            print(f"  - {failed['title']} (ID: {failed['id']}): {failed['error']}")
        if len(failed_posts) > 5:
            print(f"  ... and {len(failed_posts) - 5} more")

        # Save failed posts for reference
        failed_file = Path('bulk_publish_failures.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_posts, f, indent=2, ensure_ascii=False)
        print(f"\nFull error details saved to: {failed_file}")

    print(f"\n+ All posts are now LIVE on WordPress!")
    print(f"Visit your site: https://{site_domain}")
    print(f"WordPress admin: https://{site_domain}/wp-admin/edit.php")

    return success_count, failed_count

if __name__ == '__main__':
    try:
        success, failed = bulk_publish_posts()
        exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"Publication failed: {e}")
        exit(1)