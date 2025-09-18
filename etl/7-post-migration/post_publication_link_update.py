#!/usr/bin/env python3
"""
Post-publication link update script.
Updates internal lifeitself.org links to WordPress URLs.
"""

import json
import requests
import os
import base64
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

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

def create_url_mapping():
    """Create mapping from old URLs to new WordPress URLs."""
    print("Creating URL mapping...")

    # Load creation results
    results_file = Path('etl/5-create-content/full-migration-output/content_creation_results.json')
    with open(results_file, 'r', encoding='utf-8') as f:
        creation_results = json.load(f)

    # Load prepared content for more detailed mapping
    content_file = Path('etl/1-prepare-content/full-migration-output/prepared_content.json')
    with open(content_file, 'r', encoding='utf-8') as f:
        prepared_content = json.load(f)

    # Create slug to content mapping
    slug_to_content = {p['slug']: p for p in prepared_content}

    # Build URL mapping dictionary
    url_mapping = {}

    for post in creation_results:
        slug = post.get('slug', '')
        wordpress_url = post.get('wordpress_url', '')
        source_file = post.get('source_file', '')

        if not slug or not wordpress_url:
            continue

        content_meta = slug_to_content.get(slug, {})

        # Map various URL patterns
        base_patterns = [
            f"https://lifeitself.org/{slug}",
            f"https://lifeitself.org/{slug}/",
            f"/{slug}",
            f"/{slug}/"
        ]

        # Add date-based patterns for blog posts
        if 'blog/' in source_file or post.get('type') == 'post':
            date = content_meta.get('date', '')
            if date:
                date_parts = date.split('T')[0].split('-')
                if len(date_parts) == 3:
                    year, month, day = date_parts
                    base_patterns.extend([
                        f"https://lifeitself.org/blog/{year}/{month}/{day}/{slug}",
                        f"https://lifeitself.org/blog/{year}/{month}/{day}/{slug}/",
                        f"/blog/{year}/{month}/{day}/{slug}",
                        f"/blog/{year}/{month}/{day}/{slug}/",
                        f"/{year}/{month}/{day}/{slug}",
                        f"/{year}/{month}/{day}/{slug}/"
                    ])

        # Add category-based patterns
        if 'people/' in source_file:
            base_patterns.extend([
                f"https://lifeitself.org/people/{slug}",
                f"https://lifeitself.org/people/{slug}/",
                f"/people/{slug}",
                f"/people/{slug}/",
                f"https://lifeitself.org/author/{slug}",
                f"/author/{slug}"
            ])
        elif 'notes/' in source_file:
            base_patterns.extend([
                f"https://lifeitself.org/notes/{slug}",
                f"/notes/{slug}"
            ])
        elif 'initiatives/' in source_file:
            base_patterns.extend([
                f"https://lifeitself.org/initiatives/{slug}",
                f"/initiatives/{slug}"
            ])

        # Map all patterns to WordPress URL
        for pattern in base_patterns:
            url_mapping[pattern] = wordpress_url

    print(f"Created {len(url_mapping)} URL mappings")
    return url_mapping

def update_post_links(post_id, content, url_mapping, site_domain, headers):
    """Update links in a single post's content."""
    original_content = content
    updated_content = content

    # Count replacements
    replacements_made = 0

    # Replace URLs in href attributes
    for old_url, new_url in url_mapping.items():
        # Pattern for href attributes
        href_pattern = rf'href=["\']({re.escape(old_url)})["\']'
        if re.search(href_pattern, updated_content, re.IGNORECASE):
            updated_content = re.sub(href_pattern, f'href="{new_url}"', updated_content, flags=re.IGNORECASE)
            replacements_made += 1

        # Pattern for markdown-style links
        markdown_pattern = rf'\[([^\]]+)\]\({re.escape(old_url)}\)'
        if re.search(markdown_pattern, updated_content):
            updated_content = re.sub(markdown_pattern, rf'[\1]({new_url})', updated_content)
            replacements_made += 1

    # Only update if changes were made
    if updated_content != original_content:
        try:
            update_data = {'content': updated_content}
            update_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}'

            response = requests.post(update_url, headers=headers, json=update_data)

            if response.status_code in [200, 201]:
                return True, replacements_made
            else:
                return False, 0
        except Exception:
            return False, 0

    return True, 0  # No changes needed

def update_all_post_links():
    """Update links in all published posts."""
    print("Starting post-publication link updates...")

    # Setup
    site_domain, headers = setup_wordpress_client()
    url_mapping = create_url_mapping()

    # Load creation results
    results_file = Path('etl/5-create-content/full-migration-output/content_creation_results.json')
    with open(results_file, 'r', encoding='utf-8') as f:
        creation_results = json.load(f)

    print(f"Updating links in {len(creation_results)} posts...")

    success_count = 0
    update_count = 0
    total_replacements = 0
    failed_updates = []

    print("Progress: ", end="", flush=True)

    for i, post in enumerate(creation_results):
        try:
            post_id = post['wordpress_id']
            title = post['title']

            # Get current post content
            get_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}'
            response = requests.get(get_url, headers=headers)

            if response.status_code == 200:
                wp_post = response.json()
                current_content = wp_post.get('content', {}).get('raw', '')

                # Update links in content
                success, replacements = update_post_links(post_id, current_content, url_mapping, site_domain, headers)

                if success:
                    success_count += 1
                    if replacements > 0:
                        update_count += 1
                        total_replacements += replacements
                    print("+", end="", flush=True)
                else:
                    failed_updates.append({'id': post_id, 'title': title})
                    print("-", end="", flush=True)
            else:
                failed_updates.append({'id': post_id, 'title': title, 'error': f"Cannot fetch content: {response.status_code}"})
                print("x", end="", flush=True)

            # Progress indicator every 50 posts
            if (i + 1) % 50 == 0:
                print(f" [{i+1}/{len(creation_results)}]", end="", flush=True)

            # Rate limiting
            if (i + 1) % 10 == 0:
                time.sleep(1)

        except Exception as e:
            failed_updates.append({'id': post.get('wordpress_id', 'Unknown'), 'title': post.get('title', 'Unknown'), 'error': str(e)})
            print("x", end="", flush=True)

    print(f"\n\nLink update completed!")
    print("="*50)
    print(f"Posts processed: {success_count}/{len(creation_results)} ({success_count/len(creation_results)*100:.1f}%)")
    print(f"Posts with link updates: {update_count}")
    print(f"Total link replacements: {total_replacements}")
    print(f"Failed updates: {len(failed_updates)}")

    if failed_updates:
        failed_file = Path('link_update_failures.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_updates, f, indent=2, ensure_ascii=False)
        print(f"Failed updates saved to: {failed_file}")

    # Save URL mapping for reference
    mapping_file = Path('url_mapping_applied.json')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, indent=2, ensure_ascii=False)
    print(f"URL mapping saved to: {mapping_file}")

    print(f"\n+ Internal links updated successfully!")
    print(f"Visit your site to verify: https://{site_domain}")

    return success_count, len(failed_updates), total_replacements

if __name__ == '__main__':
    try:
        success, failed, replacements = update_all_post_links()
        print(f"\nSummary: {success} posts processed, {replacements} links updated, {failed} failures")
        exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"Link update failed: {e}")
        exit(1)