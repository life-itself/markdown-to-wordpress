#!/usr/bin/env python3
"""
Pre-publication analysis and verification script.
Comprehensive checks before publishing migrated content.
"""

import json
import requests
import os
import re
import base64
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

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

def load_migration_data():
    """Load all migration data files."""
    print("Loading migration data...")

    # Load content creation results
    results_file = Path('etl/5-create-content/full-migration-output/content_creation_results.json')
    with open(results_file, 'r', encoding='utf-8') as f:
        creation_results = json.load(f)

    # Load prepared content
    content_file = Path('etl/1-prepare-content/full-migration-output/prepared_content.json')
    with open(content_file, 'r', encoding='utf-8') as f:
        prepared_content = json.load(f)

    # Load media upload map
    media_file = Path('etl/3-upload-media/full-migration-output/media_upload_map.json')
    with open(media_file, 'r', encoding='utf-8') as f:
        media_map = json.load(f)

    print(f"+ Loaded {len(creation_results)} created posts")
    print(f"+ Loaded {len(prepared_content)} prepared posts")
    print(f"+ Loaded {len(media_map)} media mappings")

    return creation_results, prepared_content, media_map

def check_wordpress_content_access(site_domain, headers):
    """Verify we can access WordPress content via API."""
    print("\n=== WORDPRESS API ACCESS CHECK ===")

    try:
        # Check draft posts
        posts_url = f'https://{site_domain}/?rest_route=/wp/v2/posts&status=draft&per_page=5'
        response = requests.get(posts_url, headers=headers)

        if response.status_code == 200:
            drafts = response.json()
            print(f"+ API Access: Successfully fetched {len(drafts)} draft posts")

            # Sample a post to check structure
            if drafts:
                sample_post = drafts[0]
                print(f"+ Sample Post ID: {sample_post.get('id')}")
                print(f"+ Sample Title: {sample_post.get('title', {}).get('rendered', 'No title')[:50]}...")
                return True
        else:
            print(f"- API Error: {response.status_code} - {response.text[:100]}")
            return False

    except Exception as e:
        print(f"- Connection Error: {e}")
        return False

def verify_featured_images(creation_results, media_map, site_domain, headers):
    """Check if featured images are properly linked."""
    print("\n=== FEATURED IMAGES VERIFICATION ===")

    posts_with_featured = [p for p in creation_results if p.get('featured_media')]
    print(f"Posts with featured images: {len(posts_with_featured)}")

    # Sample 5 posts to verify
    sample_posts = posts_with_featured[:5] if posts_with_featured else []

    success_count = 0
    for post in sample_posts:
        try:
            post_id = post['wordpress_id']
            media_id = post['featured_media']

            # Get post data from WordPress
            post_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}'
            response = requests.get(post_url, headers=headers)

            if response.status_code == 200:
                wp_post = response.json()
                wp_featured_media = wp_post.get('featured_media', 0)

                if wp_featured_media == media_id:
                    print(f"+ {post['title']}: Featured image ID {media_id} correctly linked")
                    success_count += 1
                else:
                    print(f"- {post['title']}: Featured media mismatch - expected {media_id}, got {wp_featured_media}")
            else:
                print(f"- {post['title']}: Cannot fetch post data")

        except Exception as e:
            print(f"- {post.get('title', 'Unknown')}: Error - {e}")

    success_rate = (success_count / len(sample_posts)) * 100 if sample_posts else 0
    print(f"Featured Images Success Rate: {success_rate:.1f}% ({success_count}/{len(sample_posts)} sampled)")

    return success_rate > 80  # 80% threshold

def analyze_internal_links(prepared_content):
    """Analyze internal links and wiki-style links in content."""
    print("\n=== INTERNAL LINKS ANALYSIS ===")

    wiki_links = []
    internal_links = []
    external_links = []

    for post in prepared_content[:100]:  # Sample first 100 posts
        content = post.get('content', '')
        title = post.get('title', 'Unknown')

        # Find wiki-style links [[...]]
        wiki_pattern = r'\[\[([^\]]+)\]\]'
        wiki_matches = re.findall(wiki_pattern, content)
        for match in wiki_matches:
            wiki_links.append({'post': title, 'link': match})

        # Find regular internal links (relative paths)
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
        link_matches = re.findall(link_pattern, content)
        for link in link_matches:
            if link.startswith('/'):
                internal_links.append({'post': title, 'link': link})
            elif link.startswith('http'):
                if 'lifeitself.org' in link:
                    internal_links.append({'post': title, 'link': link})
                else:
                    external_links.append({'post': title, 'link': link})

    print(f"Wiki-style links found: {len(wiki_links)}")
    print(f"Internal links found: {len(internal_links)}")
    print(f"External links found: {len(external_links)}")

    # Sample problematic links
    if wiki_links:
        print(f"\nSample wiki links (first 5):")
        for link in wiki_links[:5]:
            print(f"  {link['post']}: [[{link['link']}]]")

    if internal_links:
        print(f"\nSample internal links (first 5):")
        for link in internal_links[:5]:
            print(f"  {link['post']}: {link['link']}")

    # Identify links that need updating
    problematic_links = len(wiki_links) + len([l for l in internal_links if not l['link'].startswith('http')])
    print(f"\nLinks needing WordPress URL mapping: {problematic_links}")

    return {
        'wiki_links': len(wiki_links),
        'internal_links': len(internal_links),
        'problematic_links': problematic_links
    }

def verify_content_rendering(creation_results, site_domain, headers):
    """Test content rendering for sample posts."""
    print("\n=== CONTENT RENDERING VERIFICATION ===")

    # Sample different types of posts
    sample_posts = creation_results[:5]  # First 5 posts

    success_count = 0
    for post in sample_posts:
        try:
            post_id = post['wordpress_id']
            title = post['title']

            # Get post content
            post_url = f'https://{site_domain}/?rest_route=/wp/v2/posts/{post_id}'
            response = requests.get(post_url, headers=headers)

            if response.status_code == 200:
                wp_post = response.json()
                content = wp_post.get('content', {}).get('rendered', '')

                # Basic checks
                checks = {
                    'has_content': len(content.strip()) > 0,
                    'has_paragraphs': '<p>' in content,
                    'no_raw_markdown': not ('##' in content or '**' in content),
                    'proper_images': '/wp-content/uploads/' in content if '<img' in content else True
                }

                passed = sum(checks.values())
                total = len(checks)

                if passed == total:
                    print(f"+ {title}: All rendering checks passed ({passed}/{total})")
                    success_count += 1
                else:
                    print(f"- {title}: Rendering issues ({passed}/{total} checks passed)")
                    for check, result in checks.items():
                        if not result:
                            print(f"    - Failed: {check}")
            else:
                print(f"- {title}: Cannot fetch content ({response.status_code})")

        except Exception as e:
            print(f"- {post.get('title', 'Unknown')}: Error - {e}")

    success_rate = (success_count / len(sample_posts)) * 100 if sample_posts else 0
    print(f"Content Rendering Success Rate: {success_rate:.1f}% ({success_count}/{len(sample_posts)} sampled)")

    return success_rate > 80

def check_media_accessibility(media_map):
    """Verify uploaded media is accessible."""
    print("\n=== MEDIA ACCESSIBILITY CHECK ===")

    # Sample 10 media items
    media_items = list(media_map.items())[:10]
    success_count = 0

    for path, media_info in media_items:
        try:
            wordpress_url = media_info.get('wordpress_url', '')
            if wordpress_url:
                response = requests.head(wordpress_url, timeout=10)
                if response.status_code == 200:
                    print(f"+ {media_info.get('new_filename', 'Unknown')}: Accessible")
                    success_count += 1
                else:
                    print(f"- {media_info.get('new_filename', 'Unknown')}: HTTP {response.status_code}")
            else:
                print(f"- {path}: No WordPress URL")
        except Exception as e:
            print(f"- {media_info.get('new_filename', 'Unknown')}: Error - {e}")

    success_rate = (success_count / len(media_items)) * 100 if media_items else 0
    print(f"Media Accessibility: {success_rate:.1f}% ({success_count}/{len(media_items)} sampled)")

    return success_rate > 80

def generate_readiness_report(results):
    """Generate final readiness report."""
    print("\n" + "="*60)
    print("=== PRE-PUBLICATION READINESS REPORT ===")
    print("="*60)

    all_checks = [
        ("WordPress API Access", results.get('api_access', False)),
        ("Featured Images", results.get('featured_images', False)),
        ("Content Rendering", results.get('content_rendering', False)),
        ("Media Accessibility", results.get('media_access', False))
    ]

    passed_checks = sum(1 for _, status in all_checks if status)
    total_checks = len(all_checks)

    print(f"\nReadiness Checks: {passed_checks}/{total_checks} passed")

    for check_name, status in all_checks:
        status_icon = "+" if status else "-"
        print(f"{status_icon} {check_name}")

    # Link analysis summary
    links_info = results.get('links_analysis', {})
    print(f"\nLink Analysis:")
    print(f"  - Wiki-style links: {links_info.get('wiki_links', 0)}")
    print(f"  - Internal links: {links_info.get('internal_links', 0)}")
    print(f"  - Links needing mapping: {links_info.get('problematic_links', 0)}")

    # Overall readiness
    is_ready = passed_checks >= 3  # At least 3/4 checks must pass

    print(f"\n{'='*60}")
    if is_ready:
        print("+ READY FOR PUBLICATION")
        print("The migration is ready to be published!")
        if links_info.get('problematic_links', 0) > 0:
            print("WARNING: Some internal links may need updating after publication")
    else:
        print("- NOT READY FOR PUBLICATION")
        print("Issues need to be resolved before publishing.")
    print("="*60)

    return is_ready

def main():
    """Run complete pre-publication analysis."""
    print("Starting Pre-Publication Analysis...")
    print("This will verify all aspects of the migration before publishing.")

    try:
        # Setup
        site_domain, headers = setup_wordpress_client()
        creation_results, prepared_content, media_map = load_migration_data()

        # Run all checks
        results = {}

        results['api_access'] = check_wordpress_content_access(site_domain, headers)
        results['featured_images'] = verify_featured_images(creation_results, media_map, site_domain, headers)
        results['links_analysis'] = analyze_internal_links(prepared_content)
        results['content_rendering'] = verify_content_rendering(creation_results, site_domain, headers)
        results['media_access'] = check_media_accessibility(media_map)

        # Generate final report
        is_ready = generate_readiness_report(results)

        # Save detailed results
        report_file = Path('pre_publication_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed report saved to: {report_file}")

        return is_ready

    except Exception as e:
        print(f"Analysis failed: {e}")
        return False

if __name__ == '__main__':
    ready = main()
    exit(0 if ready else 1)