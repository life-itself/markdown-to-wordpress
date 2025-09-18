#!/usr/bin/env python3
"""
Duplicate detection and cleanup script.
Finds and removes duplicate posts and media.
"""

import json
import requests
import os
import base64
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

def setup_wordpress_client():
    """Setup WordPress API client."""
    load_dotenv()

    site_domain = os.getenv('WORDPRESS_SITE_DOMAIN')
    username = os.getenv('WORDPRESS_USERNAME')
    app_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')

    credentials = f'{username}:{app_password}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }

    return site_domain, headers

def get_all_posts(site_domain, headers):
    """Get all posts from WordPress (published and drafts)."""
    print("Fetching all WordPress posts...")

    all_posts = []
    page = 1
    per_page = 100

    while True:
        # Get published posts
        posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts&per_page={per_page}&page={page}&status=publish'
        response = requests.get(posts_url, headers=headers)

        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            all_posts.extend(posts)
            page += 1
        else:
            break

    # Also get draft posts
    page = 1
    while True:
        posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts&per_page={per_page}&page={page}&status=draft'
        response = requests.get(posts_url, headers=headers)

        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            all_posts.extend(posts)
            page += 1
        else:
            break

    print(f"Found {len(all_posts)} total posts")
    return all_posts

def get_all_media(site_domain, headers):
    """Get all media from WordPress."""
    print("Fetching all WordPress media...")

    all_media = []
    page = 1
    per_page = 100

    while True:
        media_url = f'https://{site_domain}/?rest_route=/wp/v2/media&per_page={per_page}&page={page}'
        response = requests.get(media_url, headers=headers)

        if response.status_code == 200:
            media = response.json()
            if not media:
                break
            all_media.extend(media)
            page += 1
        else:
            break

    print(f"Found {len(all_media)} total media items")
    return all_media

def find_duplicate_posts(all_posts):
    """Find duplicate posts based on title and slug."""
    print("\nAnalyzing duplicate posts...")

    duplicates = {
        'by_title': defaultdict(list),
        'by_slug': defaultdict(list),
        'by_content_hash': defaultdict(list)
    }

    for post in all_posts:
        title = post.get('title', {}).get('rendered', '').strip()
        slug = post.get('slug', '').strip()
        content = post.get('content', {}).get('rendered', '')
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        if title:
            duplicates['by_title'][title.lower()].append(post)
        if slug:
            duplicates['by_slug'][slug].append(post)
        if content:
            duplicates['by_content_hash'][content_hash].append(post)

    # Find actual duplicates (more than 1 post with same identifier)
    title_duplicates = {k: v for k, v in duplicates['by_title'].items() if len(v) > 1}
    slug_duplicates = {k: v for k, v in duplicates['by_slug'].items() if len(v) > 1}
    content_duplicates = {k: v for k, v in duplicates['by_content_hash'].items() if len(v) > 1}

    print(f"Duplicate posts by title: {len(title_duplicates)}")
    print(f"Duplicate posts by slug: {len(slug_duplicates)}")
    print(f"Duplicate posts by content: {len(content_duplicates)}")

    return {
        'title_duplicates': title_duplicates,
        'slug_duplicates': slug_duplicates,
        'content_duplicates': content_duplicates
    }

def find_duplicate_media(all_media):
    """Find duplicate media based on filename and file size."""
    print("\nAnalyzing duplicate media...")

    duplicates = {
        'by_filename': defaultdict(list),
        'by_title': defaultdict(list)
    }

    for media in all_media:
        filename = media.get('source_url', '').split('/')[-1] if media.get('source_url') else ''
        title = media.get('title', {}).get('rendered', '').strip()

        if filename:
            duplicates['by_filename'][filename.lower()].append(media)
        if title:
            duplicates['by_title'][title.lower()].append(media)

    # Find actual duplicates
    filename_duplicates = {k: v for k, v in duplicates['by_filename'].items() if len(v) > 1}
    title_duplicates = {k: v for k, v in duplicates['by_title'].items() if len(v) > 1}

    print(f"Duplicate media by filename: {len(filename_duplicates)}")
    print(f"Duplicate media by title: {len(title_duplicates)}")

    return {
        'filename_duplicates': filename_duplicates,
        'title_duplicates': title_duplicates
    }

def create_cleanup_plan(post_duplicates, media_duplicates):
    """Create a plan for cleaning up duplicates."""
    print("\nCreating cleanup plan...")

    cleanup_plan = {
        'posts_to_delete': [],
        'media_to_delete': [],
        'summary': {}
    }

    # For post duplicates, keep the one with the highest ID (most recent)
    for duplicate_type, duplicates in post_duplicates.items():
        for identifier, posts in duplicates.items():
            if len(posts) > 1:
                # Sort by ID and keep the highest (most recent)
                posts_sorted = sorted(posts, key=lambda x: x.get('id', 0), reverse=True)
                posts_to_keep = posts_sorted[0]
                posts_to_delete = posts_sorted[1:]

                for post in posts_to_delete:
                    cleanup_plan['posts_to_delete'].append({
                        'id': post.get('id'),
                        'title': post.get('title', {}).get('rendered', ''),
                        'slug': post.get('slug', ''),
                        'reason': f'Duplicate {duplicate_type}',
                        'duplicate_of': posts_to_keep.get('id')
                    })

    # For media duplicates, keep the one with the highest ID
    for duplicate_type, duplicates in media_duplicates.items():
        for identifier, media_items in duplicates.items():
            if len(media_items) > 1:
                media_sorted = sorted(media_items, key=lambda x: x.get('id', 0), reverse=True)
                media_to_keep = media_sorted[0]
                media_to_delete = media_sorted[1:]

                for media in media_to_delete:
                    cleanup_plan['media_to_delete'].append({
                        'id': media.get('id'),
                        'title': media.get('title', {}).get('rendered', ''),
                        'filename': media.get('source_url', '').split('/')[-1],
                        'reason': f'Duplicate {duplicate_type}',
                        'duplicate_of': media_to_keep.get('id')
                    })

    # Remove duplicates from the lists
    cleanup_plan['posts_to_delete'] = list({item['id']: item for item in cleanup_plan['posts_to_delete']}.values())
    cleanup_plan['media_to_delete'] = list({item['id']: item for item in cleanup_plan['media_to_delete']}.values())

    cleanup_plan['summary'] = {
        'duplicate_posts_to_delete': len(cleanup_plan['posts_to_delete']),
        'duplicate_media_to_delete': len(cleanup_plan['media_to_delete'])
    }

    print(f"Posts marked for deletion: {cleanup_plan['summary']['duplicate_posts_to_delete']}")
    print(f"Media marked for deletion: {cleanup_plan['summary']['duplicate_media_to_delete']}")

    return cleanup_plan

def execute_cleanup(cleanup_plan, site_domain, headers, dry_run=True):
    """Execute the cleanup plan."""
    print(f"\n{'DRY RUN - ' if dry_run else ''}Executing cleanup...")

    deleted_posts = 0
    deleted_media = 0
    errors = []

    # Delete duplicate posts
    for post in cleanup_plan['posts_to_delete']:
        try:
            post_id = post['id']
            print(f"{'[DRY RUN] ' if dry_run else ''}Deleting post: {post['title']} (ID: {post_id})")

            if not dry_run:
                delete_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}&force=true'
                response = requests.delete(delete_url, headers=headers)

                if response.status_code in [200, 410]:  # 410 is already deleted
                    deleted_posts += 1
                    print(f"  + Deleted successfully")
                else:
                    errors.append(f"Failed to delete post {post_id}: {response.status_code}")
                    print(f"  - Failed: {response.status_code}")
            else:
                deleted_posts += 1

        except Exception as e:
            errors.append(f"Error deleting post {post['id']}: {e}")

    # Delete duplicate media
    for media in cleanup_plan['media_to_delete']:
        try:
            media_id = media['id']
            print(f"{'[DRY RUN] ' if dry_run else ''}Deleting media: {media['filename']} (ID: {media_id})")

            if not dry_run:
                delete_url = f'https://{site_domain}/?rest_route=/wp/v2/media/{media_id}&force=true'
                response = requests.delete(delete_url, headers=headers)

                if response.status_code in [200, 410]:
                    deleted_media += 1
                    print(f"  + Deleted successfully")
                else:
                    errors.append(f"Failed to delete media {media_id}: {response.status_code}")
                    print(f"  - Failed: {response.status_code}")
            else:
                deleted_media += 1

        except Exception as e:
            errors.append(f"Error deleting media {media['id']}: {e}")

    print(f"\n{'DRY RUN ' if dry_run else ''}Cleanup Summary:")
    print(f"Posts deleted: {deleted_posts}")
    print(f"Media deleted: {deleted_media}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

    return deleted_posts, deleted_media, errors

def main():
    """Run duplicate detection and cleanup."""
    print("Starting duplicate detection and cleanup...")

    try:
        # Setup
        site_domain, headers = setup_wordpress_client()

        # Get all content
        all_posts = get_all_posts(site_domain, headers)
        all_media = get_all_media(site_domain, headers)

        # Find duplicates
        post_duplicates = find_duplicate_posts(all_posts)
        media_duplicates = find_duplicate_media(all_media)

        # Create cleanup plan
        cleanup_plan = create_cleanup_plan(post_duplicates, media_duplicates)

        # Save analysis results
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / 'duplicate_analysis.json', 'w', encoding='utf-8') as f:
            json.dump({
                'post_duplicates': post_duplicates,
                'media_duplicates': media_duplicates,
                'cleanup_plan': cleanup_plan
            }, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nAnalysis saved to: {output_dir / 'duplicate_analysis.json'}")

        # Ask for confirmation before actual deletion
        if cleanup_plan['summary']['duplicate_posts_to_delete'] > 0 or cleanup_plan['summary']['duplicate_media_to_delete'] > 0:
            print("\n" + "="*60)
            print("DUPLICATE CLEANUP PLAN")
            print("="*60)
            print(f"Posts to delete: {cleanup_plan['summary']['duplicate_posts_to_delete']}")
            print(f"Media to delete: {cleanup_plan['summary']['duplicate_media_to_delete']}")

            # First do a dry run
            print("\nRunning DRY RUN first...")
            execute_cleanup(cleanup_plan, site_domain, headers, dry_run=True)

            # Real execution
            print("\nExecuting ACTUAL cleanup...")
            execute_cleanup(cleanup_plan, site_domain, headers, dry_run=False)

        else:
            print("\n+ No duplicates found! Content is clean.")

        return True

    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)