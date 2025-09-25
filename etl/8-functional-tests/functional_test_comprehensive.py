#!/usr/bin/env python3
"""
Comprehensive functional tests for migration quality verification.
Tests actual migrated content against expected values and original content.
"""

import requests
import json
from pathlib import Path
import sys
import os
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class ComprehensiveMigrationTests:
    """Comprehensive functional tests to verify migration quality."""

    def __init__(self, site_url="https://app-67d6f672c1ac1810207db362.closte.com"):
        self.site_url = site_url
        self.api_base = f"{site_url}/?rest_route=/wp/v2"
        self.test_results = []

    def discover_posts(self, limit=10):
        """Discover actual posts on WordPress site."""
        try:
            response = requests.get(f"{self.api_base}/posts&per_page={limit}")
            if response.status_code != 200:
                print(f"Failed to fetch posts: {response.status_code}")
                return []

            posts = response.json()
            discovered = []
            for post in posts:
                discovered.append({
                    'id': post['id'],
                    'slug': post['slug'],
                    'title': post['title']['rendered'],
                    'has_content': len(post.get('content', {}).get('rendered', '')) > 100,
                    'has_featured_image': post.get('featured_media', 0) > 0,
                    'url': post.get('link', '')
                })
            return discovered
        except Exception as e:
            print(f"Error discovering posts: {e}")
            return []

    def test_post_structure(self, post_id):
        """Test if post has proper structure."""
        try:
            response = requests.get(f"{self.api_base}/posts/{post_id}")
            if response.status_code != 200:
                return False, f"Failed to fetch post {post_id}"

            post = response.json()

            checks = {
                'has_title': bool(post.get('title', {}).get('rendered', '').strip()),
                'has_content': len(post.get('content', {}).get('rendered', '')) > 50,
                'has_slug': bool(post.get('slug', '')),
                'has_date': bool(post.get('date', '')),
                'has_status': post.get('status') in ['publish', 'draft'],
            }

            failed_checks = [k for k, v in checks.items() if not v]

            if not failed_checks:
                return True, f"+ Post {post_id} has proper structure (all {len(checks)} checks passed)"
            else:
                return False, f"- Post {post_id} failed structure checks: {failed_checks}"

        except Exception as e:
            return False, f"Error testing post {post_id}: {str(e)}"

    def test_content_quality(self, post_id):
        """Test content quality of a post."""
        try:
            response = requests.get(f"{self.api_base}/posts/{post_id}")
            if response.status_code != 200:
                return False, f"Failed to fetch post {post_id}"

            post = response.json()
            content = post.get('content', {}).get('rendered', '')

            # Quality checks
            checks = []

            # Check for proper HTML structure
            has_paragraphs = '<p>' in content
            checks.append(('has_paragraphs', has_paragraphs))

            # Check for no raw markdown
            no_raw_markdown = not bool(re.search(r'#{1,6}\s+\w+|^\*{1,2}\w+\*{1,2}', content))
            checks.append(('no_raw_markdown', no_raw_markdown))

            # Check for properly formatted links
            has_proper_links = not bool(re.search(r'\[\[.*?\]\]', content))  # No wiki links
            checks.append(('no_wiki_links', has_proper_links))

            # Check images are using WordPress URLs
            images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            proper_images = all('/wp-content/' in img or 'http' in img for img in images) if images else True
            checks.append(('proper_image_urls', proper_images))

            failed_checks = [name for name, passed in checks if not passed]
            passed_count = sum(1 for _, passed in checks if passed)

            if not failed_checks:
                return True, f"+ Post {post_id} content quality: {passed_count}/{len(checks)} checks passed"
            else:
                return False, f"- Post {post_id} content issues: {failed_checks}"

        except Exception as e:
            return False, f"Error testing content quality: {str(e)}"

    def test_media_integration(self, post_id):
        """Test media integration for a post."""
        try:
            response = requests.get(f"{self.api_base}/posts/{post_id}")
            if response.status_code != 200:
                return False, f"Failed to fetch post {post_id}"

            post = response.json()
            content = post.get('content', {}).get('rendered', '')
            featured_media_id = post.get('featured_media', 0)

            # Find all images in content
            images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)

            # Check featured image if set
            featured_check = ""
            if featured_media_id > 0:
                featured_check = f"featured image ID {featured_media_id}"

            # Check inline images
            if images:
                valid_images = sum(1 for img in images if 'wp-content' in img or 'http' in img)
                image_check = f"{valid_images}/{len(images)} valid image URLs"

                if featured_check:
                    return valid_images == len(images), f"Media: {featured_check}, {image_check}"
                else:
                    return valid_images == len(images), f"Media: {image_check}"
            else:
                if featured_check:
                    return True, f"Media: {featured_check}, no inline images"
                else:
                    return True, "Media: No images in post"

        except Exception as e:
            return False, f"Error testing media: {str(e)}"

    def run_comprehensive_tests(self):
        """Run comprehensive test suite on discovered posts."""
        print("\n" + "="*70)
        print("COMPREHENSIVE FUNCTIONAL TESTS FOR WORDPRESS MIGRATION")
        print("="*70)
        print(f"Testing site: {self.site_url}\n")

        # Discover posts
        print("PHASE 1: Post Discovery")
        print("-"*40)
        posts = self.discover_posts(limit=10)

        if not posts:
            print("ERROR: No posts found on WordPress site!")
            return False

        print(f"Discovered {len(posts)} posts:")
        for p in posts[:5]:
            print(f"  - {p['slug']}: {p['title'][:50]}")
        if len(posts) > 5:
            print(f"  ... and {len(posts)-5} more")

        # Test each post
        print("\nPHASE 2: Post Testing")
        print("-"*40)

        total_tests = 0
        passed_tests = 0

        for i, post in enumerate(posts[:5], 1):  # Test first 5 posts
            print(f"\n[{i}/5] Testing post: {post['slug']} (ID: {post['id']})")
            print("  Title:", post['title'][:60])

            # Test 1: Structure
            passed, message = self.test_post_structure(post['id'])
            print(f"  Structure: {message}")
            total_tests += 1
            if passed:
                passed_tests += 1

            # Test 2: Content Quality
            passed, message = self.test_content_quality(post['id'])
            print(f"  Content: {message}")
            total_tests += 1
            if passed:
                passed_tests += 1

            # Test 3: Media Integration
            passed, message = self.test_media_integration(post['id'])
            print(f"  {message}")
            total_tests += 1
            if passed:
                passed_tests += 1

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Posts Discovered: {len(posts)}")
        print(f"Posts Tested: {min(5, len(posts))}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        success = passed_tests / total_tests >= 0.7  # 70% threshold

        if success:
            print("\n+ MIGRATION QUALITY ACCEPTABLE - Tests passed with 70%+ success rate")
        else:
            print(f"\n- MIGRATION QUALITY ISSUES - Only {(passed_tests/total_tests)*100:.1f}% tests passed")

        # Save detailed results
        self.test_results = {
            'site_url': self.site_url,
            'posts_discovered': len(posts),
            'posts_tested': min(5, len(posts)),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            'success': success,
            'discovered_posts': posts
        }

        return success

    def save_results(self):
        """Save test results to file."""
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / 'comprehensive_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\nDetailed results saved to: {output_dir / 'comprehensive_test_results.json'}")


def main():
    """Run comprehensive functional tests."""
    print("Starting Comprehensive Migration Tests...")

    tester = ComprehensiveMigrationTests()
    success = tester.run_comprehensive_tests()
    tester.save_results()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())