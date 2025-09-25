#!/usr/bin/env python3
"""
Specific functional test for comparing original Life Itself content
with migrated WordPress content, focusing on known issues.

Test case: "Second Renaissance Name Why" post
Original: https://lifeitself.org/blog/second-renaissance-name-why
Migrated: WordPress post ID 940
"""

import requests
import json
import re
from pathlib import Path
import sys
from bs4 import BeautifulSoup
import difflib

class SpecificPostMigrationTest:
    """Test specific migration issues in a real post."""

    def __init__(self):
        self.original_url = "https://lifeitself.org/blog/second-renaissance-name-why"
        self.wordpress_site = "https://app-67d6f672c1ac1810207db362.closte.com"
        self.wordpress_api = f"{self.wordpress_site}/?rest_route=/wp/v2"
        self.post_id = 940
        self.test_results = []

    def fetch_original_content(self):
        """Fetch content from original Life Itself site."""
        try:
            response = requests.get(self.original_url, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch original content: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching original: {e}")
            return None

    def fetch_wordpress_content(self):
        """Fetch content from WordPress migration."""
        try:
            # Get via REST API
            response = requests.get(f"{self.wordpress_api}/posts/{self.post_id}")
            if response.status_code == 200:
                post = response.json()
                return {
                    'title': post.get('title', {}).get('rendered', ''),
                    'content': post.get('content', {}).get('rendered', ''),
                    'excerpt': post.get('excerpt', {}).get('rendered', ''),
                    'author': post.get('author', ''),
                    'meta': post.get('meta', {}),
                    'featured_media': post.get('featured_media', 0)
                }
            else:
                print(f"Failed to fetch WordPress content: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching WordPress content: {e}")
            return None

    def test_footnotes(self, original_html, wordpress_content):
        """Test if footnotes are properly migrated."""
        print("\n[TEST] Footnote Migration")
        print("-" * 40)

        issues = []

        # Check for broken footnote references in WordPress
        wordpress_html = wordpress_content['content']

        # Pattern for broken footnotes like "[^1]: An intere..."
        broken_footnotes = re.findall(r'\[\^?\d+\]:\s*[A-Z]', wordpress_html)
        if broken_footnotes:
            issues.append(f"Found {len(broken_footnotes)} broken footnote references")
            print(f"  - FAIL: Found broken footnotes: {broken_footnotes[:3]}...")

        # Check for proper footnote formatting
        # Original uses superscript links, WordPress should too
        original_footnotes = re.findall(r'<sup.*?>\s*\d+\s*</sup>', original_html) if original_html else []
        wp_footnotes = re.findall(r'<sup.*?>\s*\d+\s*</sup>', wordpress_html)

        if original_html and len(original_footnotes) > 0:
            if len(wp_footnotes) == 0:
                issues.append("No properly formatted footnotes found in WordPress")
                print(f"  - FAIL: Original has {len(original_footnotes)} footnotes, WordPress has {len(wp_footnotes)}")
            else:
                print(f"  + PASS: Found {len(wp_footnotes)} footnotes in WordPress")

        # Check for footnote content at the bottom
        if "[^1]:" in wordpress_html or "[1]:" in wordpress_html:
            issues.append("Raw markdown footnote syntax found in HTML")
            print("  - FAIL: Raw markdown footnote syntax not converted to HTML")

        return len(issues) == 0, issues

    def test_special_blocks(self, wordpress_content):
        """Test if special markdown blocks like [!note] are properly handled."""
        print("\n[TEST] Special Markdown Blocks")
        print("-" * 40)

        issues = []
        wordpress_html = wordpress_content['content']

        # Check for unconverted [!note] blocks
        note_blocks = re.findall(r'\[!note\]', wordpress_html)
        if note_blocks:
            issues.append(f"Found {len(note_blocks)} unconverted [!note] blocks")
            print(f"  - FAIL: Unconverted [!note] blocks found")

        # Check for other callout blocks
        callout_patterns = [
            r'\[!warning\]',
            r'\[!info\]',
            r'\[!tip\]',
            r'\[!important\]'
        ]

        for pattern in callout_patterns:
            matches = re.findall(pattern, wordpress_html)
            if matches:
                issues.append(f"Unconverted {pattern} blocks: {len(matches)}")

        if not issues:
            print("  + PASS: No unconverted special blocks found")

        return len(issues) == 0, issues

    def test_authors(self, original_html, wordpress_content):
        """Test if authors are properly migrated."""
        print("\n[TEST] Author Information")
        print("-" * 40)

        issues = []

        # In WordPress, check if author is properly set
        author_id = wordpress_content.get('author', 0)

        if author_id == 0 or author_id == 1:  # Often defaults to admin (ID 1)
            issues.append("Author defaulted to admin instead of actual author")
            print(f"  - FAIL: Author ID is {author_id} (likely admin default)")

        # Check for author information in content or meta
        # Original Life Itself shows author with picture
        if original_html:
            # Try to find author info in original
            soup = BeautifulSoup(original_html, 'html.parser')

            # Look for author section
            author_elements = soup.find_all(text=re.compile(r'(Rufus Pollock|Theo Cox|Sylvie Barbier)', re.I))

            if author_elements:
                print(f"  INFO: Original has author information for: {author_elements[0][:50]}...")

                # Check if WordPress has any author info
                wp_has_author = any(
                    name in wordpress_content['content']
                    for name in ['Rufus Pollock', 'Theo Cox', 'Sylvie Barbier']
                )

                if not wp_has_author:
                    issues.append("Author information lost in migration")
                    print("  - FAIL: Author information not preserved in WordPress")

        return len(issues) == 0, issues

    def test_images(self, wordpress_content):
        """Test if images are properly migrated."""
        print("\n[TEST] Image Migration")
        print("-" * 40)

        issues = []
        wordpress_html = wordpress_content['content']

        # Extract all images
        images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', wordpress_html)

        if not images:
            print("  INFO: No images found in content")
        else:
            for img_url in images:
                # Check if image is properly hosted on WordPress
                if '/wp-content/uploads/' not in img_url and self.wordpress_site not in img_url:
                    issues.append(f"External image not migrated: {img_url}")
                    print(f"  - FAIL: Non-WordPress image URL: {img_url[:80]}...")
                else:
                    # Check if image file actually exists
                    full_url = img_url if img_url.startswith('http') else f"{self.wordpress_site}{img_url}"
                    try:
                        img_response = requests.head(full_url, timeout=10)
                        if img_response.status_code == 200:
                            print(f"  + PASS: WordPress image accessible: {img_url[:80]}...")
                        else:
                            issues.append(f"Image file not accessible (HTTP {img_response.status_code}): {img_url}")
                            print(f"  - FAIL: Image returns {img_response.status_code}: {img_url[:80]}...")
                    except Exception as e:
                        issues.append(f"Could not check image accessibility: {img_url}")
                        print(f"  - FAIL: Cannot access image: {img_url[:80]}...")

        # Check for image display issues - alt text instead of actual image
        # Look for specific patterns that indicate display problems
        bridge_image_patterns = [
            "An engraving-style image depicting a bridge connecting two eras",
            "first-renaissance-to-second-renaissance-bridge"
        ]

        for pattern in bridge_image_patterns:
            if pattern in wordpress_html:
                # Check if it's in an img tag or just as text
                img_match = re.search(f'<img[^>]*alt=["\'][^"\']*{re.escape(pattern)}[^"\']*["\'][^>]*>', wordpress_html)
                if img_match:
                    # Check if the img tag has a valid src
                    src_match = re.search(r'src=["\']([^"\']+)["\']', img_match.group(0))
                    if src_match and '/wp-content/uploads/' in src_match.group(1):
                        print(f"  + PASS: Bridge image properly embedded with alt text")
                    else:
                        issues.append("Bridge image shows alt text instead of actual image")
                        print(f"  - FAIL: Bridge image not displaying - shows alt text only")
                else:
                    # Alt text found but not in img tag - possible display issue
                    if "bridge connecting two eras" in wordpress_html and "<img" not in wordpress_html:
                        issues.append("Image alt text found but no img tag - display issue")
                        print(f"  - FAIL: Alt text present but image not displaying")

        # Check featured image
        if wordpress_content.get('featured_media', 0) > 0:
            print(f"  + PASS: Has featured image (ID: {wordpress_content['featured_media']})")

        return len(issues) == 0, issues

    def test_content_structure(self, wordpress_content):
        """Test overall content structure and formatting."""
        print("\n[TEST] Content Structure")
        print("-" * 40)

        issues = []
        wordpress_html = wordpress_content['content']

        # Check for proper HTML structure
        checks = {
            'has_paragraphs': '<p>' in wordpress_html,
            'has_headings': bool(re.search(r'<h[1-6]', wordpress_html)),
            'no_raw_markdown_headers': not bool(re.search(r'^#{1,6}\s+', wordpress_html, re.M)),
            'no_raw_markdown_bold': not bool(re.search(r'\*\*[^*]+\*\*', wordpress_html)),
            'no_raw_markdown_italic': not bool(re.search(r'(?<!\*)\*[^*]+\*(?!\*)', wordpress_html)),
            'no_wiki_links': not bool(re.search(r'\[\[.*?\]\]', wordpress_html))
        }

        for check_name, passed in checks.items():
            if not passed:
                issues.append(f"Failed: {check_name}")
                print(f"  - FAIL: {check_name}")
            else:
                print(f"  + PASS: {check_name}")

        return len(issues) == 0, issues

    def run_tests(self):
        """Run all tests for the specific post."""
        print("\n" + "="*70)
        print("SPECIFIC POST MIGRATION TEST")
        print("="*70)
        print(f"Original: {self.original_url}")
        print(f"WordPress: Post ID {self.post_id}")
        print("="*70)

        # Fetch content
        print("\nFetching content...")
        original_html = self.fetch_original_content()
        wordpress_content = self.fetch_wordpress_content()

        if not wordpress_content:
            print("ERROR: Could not fetch WordPress content")
            return False

        print(f"WordPress Title: {wordpress_content['title']}")

        # Run tests
        all_issues = []
        test_results = []

        # Test 1: Footnotes
        passed, issues = self.test_footnotes(original_html, wordpress_content)
        test_results.append(('Footnotes', passed))
        all_issues.extend(issues)

        # Test 2: Special Blocks
        passed, issues = self.test_special_blocks(wordpress_content)
        test_results.append(('Special Blocks', passed))
        all_issues.extend(issues)

        # Test 3: Authors
        passed, issues = self.test_authors(original_html, wordpress_content)
        test_results.append(('Authors', passed))
        all_issues.extend(issues)

        # Test 4: Images
        passed, issues = self.test_images(wordpress_content)
        test_results.append(('Images', passed))
        all_issues.extend(issues)

        # Test 5: Content Structure
        passed, issues = self.test_content_structure(wordpress_content)
        test_results.append(('Content Structure', passed))
        all_issues.extend(issues)

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed_count = sum(1 for _, passed in test_results if passed)
        total_tests = len(test_results)

        for test_name, passed in test_results:
            status = "PASS" if passed else "FAIL"
            print(f"{test_name:20} {status}")

        print("-"*40)
        print(f"Total: {passed_count}/{total_tests} tests passed")
        print(f"Success Rate: {(passed_count/total_tests)*100:.1f}%")

        if all_issues:
            print("\nISSUES FOUND:")
            for i, issue in enumerate(all_issues, 1):
                print(f"  {i}. {issue}")

        # Save results
        self.save_results(test_results, all_issues, wordpress_content)

        return passed_count == total_tests

    def save_results(self, test_results, issues, wordpress_content):
        """Save detailed test results."""
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)

        results = {
            'post_tested': {
                'original_url': self.original_url,
                'wordpress_id': self.post_id,
                'wordpress_title': wordpress_content['title']
            },
            'test_results': [
                {'test': name, 'passed': passed}
                for name, passed in test_results
            ],
            'issues': issues,
            'success_rate': sum(1 for _, p in test_results if p) / len(test_results) * 100
        }

        with open(output_dir / 'specific_post_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: {output_dir / 'specific_post_test_results.json'}")


def main():
    """Run specific post migration test."""
    tester = SpecificPostMigrationTest()
    success = tester.run_tests()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())