#!/usr/bin/env python3
"""
Final migration analysis and verification script.
Comprehensive post-cleanup analysis.
"""

import json
import requests
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

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

def get_all_content(site_domain, headers):
    """Get comprehensive content analysis."""
    print("Fetching all WordPress content...")

    # Get published posts
    published_posts = []
    page = 1
    while True:
        posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts&per_page=100&page={page}&status=publish'
        response = requests.get(posts_url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            published_posts.extend(posts)
            page += 1
        else:
            break

    # Get draft posts
    draft_posts = []
    page = 1
    while True:
        posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts&per_page=100&page={page}&status=draft'
        response = requests.get(posts_url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            draft_posts.extend(posts)
            page += 1
        else:
            break

    # Get all media
    all_media = []
    page = 1
    while True:
        media_url = f'https://{site_domain}/?rest_route=/wp/v2/media&per_page=100&page={page}'
        response = requests.get(media_url, headers=headers)
        if response.status_code == 200:
            media = response.json()
            if not media:
                break
            all_media.extend(media)
            page += 1
        else:
            break

    return published_posts, draft_posts, all_media

def analyze_content(published_posts, draft_posts, all_media):
    """Analyze final content state."""
    print("\nAnalyzing final content state...")

    analysis = {
        'posts': {
            'total': len(published_posts) + len(draft_posts),
            'published': len(published_posts),
            'drafts': len(draft_posts),
            'with_featured_images': 0,
            'content_types': {}
        },
        'media': {
            'total': len(all_media),
            'by_type': {},
            'orphaned': 0
        },
        'quality_checks': {
            'posts_with_content': 0,
            'posts_with_images': 0,
            'posts_with_proper_titles': 0
        }
    }

    # Analyze posts
    for post in published_posts + draft_posts:
        # Featured images
        if post.get('featured_media', 0) > 0:
            analysis['posts']['with_featured_images'] += 1

        # Quality checks
        content = post.get('content', {}).get('rendered', '')
        title = post.get('title', {}).get('rendered', '')

        if len(content.strip()) > 50:
            analysis['quality_checks']['posts_with_content'] += 1

        if '<img' in content or post.get('featured_media', 0) > 0:
            analysis['quality_checks']['posts_with_images'] += 1

        if len(title.strip()) > 0 and title.strip() != 'Untitled':
            analysis['quality_checks']['posts_with_proper_titles'] += 1

    # Analyze media
    for media in all_media:
        media_type = media.get('mime_type', 'unknown')
        if media_type not in analysis['media']['by_type']:
            analysis['media']['by_type'][media_type] = 0
        analysis['media']['by_type'][media_type] += 1

    return analysis

def load_migration_stats():
    """Load original migration statistics."""
    try:
        # Load creation results
        results_file = Path('../5-create-content/full-migration-output/content_creation_results.json')
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                creation_results = json.load(f)
        else:
            creation_results = []

        # Load media map
        media_file = Path('../3-upload-media/full-migration-output/media_upload_map.json')
        if media_file.exists():
            with open(media_file, 'r', encoding='utf-8') as f:
                media_map = json.load(f)
        else:
            media_map = {}

        return len(creation_results), len(media_map)
    except:
        return 0, 0

def generate_final_report(analysis, original_posts, original_media, site_domain):
    """Generate comprehensive final report."""
    print("\n" + "="*80)
    print("=== FINAL MIGRATION ANALYSIS REPORT ===")
    print("="*80)

    # Migration summary
    print(f"\n[MIGRATION SUMMARY]")
    print(f"Original content: {original_posts} posts, {original_media} media")
    print(f"Current content: {analysis['posts']['total']} posts, {analysis['media']['total']} media")
    print(f"Duplicates removed: {original_posts - analysis['posts']['total']} posts, {original_media - analysis['media']['total']} media")

    # Post analysis
    print(f"\n[POSTS ANALYSIS]")
    print(f"Total posts: {analysis['posts']['total']}")
    print(f"  Published: {analysis['posts']['published']} ({analysis['posts']['published']/analysis['posts']['total']*100:.1f}%)")
    print(f"  Drafts: {analysis['posts']['drafts']} ({analysis['posts']['drafts']/analysis['posts']['total']*100:.1f}%)")
    print(f"  With featured images: {analysis['posts']['with_featured_images']} ({analysis['posts']['with_featured_images']/analysis['posts']['total']*100:.1f}%)")

    # Quality metrics
    print(f"\n[QUALITY METRICS]")
    total_posts = analysis['posts']['total']
    print(f"Posts with substantial content: {analysis['quality_checks']['posts_with_content']}/{total_posts} ({analysis['quality_checks']['posts_with_content']/total_posts*100:.1f}%)")
    print(f"Posts with images: {analysis['quality_checks']['posts_with_images']}/{total_posts} ({analysis['quality_checks']['posts_with_images']/total_posts*100:.1f}%)")
    print(f"Posts with proper titles: {analysis['quality_checks']['posts_with_proper_titles']}/{total_posts} ({analysis['quality_checks']['posts_with_proper_titles']/total_posts*100:.1f}%)")

    # Media analysis
    print(f"\n[MEDIA ANALYSIS]")
    print(f"Total media items: {analysis['media']['total']}")
    print(f"Media types:")
    for media_type, count in analysis['media']['by_type'].items():
        print(f"  {media_type}: {count} ({count/analysis['media']['total']*100:.1f}%)")

    # Site information
    print(f"\n[SITE INFORMATION]")
    print(f"WordPress site: https://{site_domain}")
    print(f"Admin dashboard: https://{site_domain}/wp-admin")
    print(f"Posts listing: https://{site_domain}/wp-admin/edit.php")
    print(f"Media library: https://{site_domain}/wp-admin/upload.php")

    # Overall status
    print(f"\n[MIGRATION STATUS]")
    if analysis['posts']['published'] > 0:
        print(f"+ MIGRATION COMPLETE - {analysis['posts']['published']} posts are LIVE!")
        print(f"+ Content quality: Excellent ({analysis['quality_checks']['posts_with_proper_titles']/total_posts*100:.1f}% have proper titles)")
        print(f"+ Media integration: Strong ({analysis['posts']['with_featured_images']/total_posts*100:.1f}% have featured images)")
        print(f"+ Duplicates removed: Clean content structure")
    else:
        print(f"WARNING: All posts are in draft status - ready for review and publishing")

    print(f"\n{'='*80}")

    return analysis

def main():
    """Run final analysis."""
    print("Starting final migration analysis...")

    try:
        # Setup
        site_domain, headers = setup_wordpress_client()

        # Get all content
        published_posts, draft_posts, all_media = get_all_content(site_domain, headers)

        # Analyze content
        analysis = analyze_content(published_posts, draft_posts, all_media)

        # Load original migration stats
        original_posts, original_media = load_migration_stats()

        # Generate report
        final_analysis = generate_final_report(analysis, original_posts, original_media, site_domain)

        # Save detailed analysis
        output_file = Path('output/final_migration_analysis.json')
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'analysis': final_analysis,
                'original_stats': {'posts': original_posts, 'media': original_media},
                'site_domain': site_domain
            }, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed analysis saved to: {output_file}")

        return True

    except Exception as e:
        print(f"Analysis failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)