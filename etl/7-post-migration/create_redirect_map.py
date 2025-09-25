#!/usr/bin/env python3
"""
Create redirect mapping from old Flowershow URLs to new WordPress URLs.
"""

import json
from pathlib import Path

def create_redirect_mapping():
    """Generate redirect mappings from old paths to new WordPress URLs."""

    # Load creation results
    results_file = Path('etl/5-create-content/full-migration-output/content_creation_results.json')
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Load prepared content for more metadata
    content_file = Path('etl/1-prepare-content/full-migration-output/prepared_content.json')
    with open(content_file, 'r', encoding='utf-8') as f:
        prepared_content = json.load(f)

    # Create slug to content mapping
    slug_to_content = {p['slug']: p for p in prepared_content}

    # Create redirect mapping
    redirects = {}

    for post in results:
        slug = post.get('slug', '')
        wordpress_url = post.get('wordpress_url', '')
        source_file = post.get('source_file', '')
        post_type = post.get('type', 'post')

        if not slug or not wordpress_url:
            continue

        # Get original content metadata
        content_meta = slug_to_content.get(slug, {})

        # Generate old URL based on content type and structure
        if post_type == 'post' or 'blog/' in source_file:
            # Blog posts with date structure
            date = content_meta.get('date', '')
            if date:
                # Extract year/month/day from date
                date_parts = date.split('T')[0].split('-')
                if len(date_parts) == 3:
                    year, month, day = date_parts
                    old_path = f"/blog/{year}/{month}/{day}/{slug}"
                    redirects[old_path] = wordpress_url

                    # Also add year-only pattern (from _redirects file pattern)
                    old_path_year = f"/{year}/{month}/{day}/{slug}"
                    redirects[old_path_year] = wordpress_url

            # Also add direct blog slug
            old_path_direct = f"/blog/{slug}"
            redirects[old_path_direct] = wordpress_url

        elif post_type == 'page':
            # Pages at root level
            old_path = f"/{slug}"
            redirects[old_path] = wordpress_url

            # Handle special cases from source file path
            if 'notes/' in source_file:
                old_path_notes = f"/notes/{slug}"
                redirects[old_path_notes] = wordpress_url
            elif 'people/' in source_file:
                old_path_people = f"/people/{slug}"
                redirects[old_path_people] = wordpress_url
                # Also add author redirect pattern
                old_path_author = f"/author/{slug}"
                redirects[old_path_author] = wordpress_url
            elif 'initiatives/' in source_file:
                old_path_init = f"/initiatives/{slug}"
                redirects[old_path_init] = wordpress_url

    # Add hardcoded redirects from _redirects file
    static_redirects = {
        "/manifesto": "/blog/2015/11/01/manifesto",
        "/27aout": "/blog/2022/07/15/art-eco-spirituality-aug-2022",
        "/sunflower-school": "/blog/2021/11/12/sunflower-school-ecole-des-tournesols",
        "/mindfulness": "/blog/2020/06/29/mindfulness-an-introduction",
        "/bergerac-build": "/blog/2020/07/09/bergerac-build-festival-2020-gathering-builders-diggers-and-dreamers",
        "/imaginary-society": "/blog/2020/08/18/the-imaginary-society-series",
        "/community-projects": "/blog/2021/03/18/berlin-hub-community-projects",
        "/institute/compassionate-mental-health": "/blog/2021/05/14/compassionate-mental-health/",
        "/deliberately-developmental-space": "/blog/2021/10/05/deliberately-developmental-spaces-a-key-to-addressing-the-metacrisis",
        "/hangouts": "/community",
        "/once-upon-a-time-series": "/ordinary-people",
        "/tao/community-guidelines": "/community",
        "/blog": "/categories/all",
        "/ecosystem": "https://ecosystem.lifeitself.org",
        "/learn/culturology": "/learn/cultural-evolution",
        "/programs": "/residencies",
        "/qr": "/",
        "/awakening-society": "/learn/awakening-society",
        "/notes/wisdom-gap": "/learn/wisdom-gap"
    }

    # Map static redirects to WordPress URLs if they exist in our results
    for old, new in static_redirects.items():
        # Try to find the WordPress URL for the redirect target
        target_slug = new.split('/')[-1] if '/' in new else new
        for post in results:
            if post.get('slug', '') == target_slug:
                redirects[old] = post['wordpress_url']
                break
        else:
            # Keep original mapping if not found in WordPress
            redirects[old] = new

    return redirects

def save_redirect_mappings(redirects):
    """Save redirect mappings to various formats."""

    output_dir = Path('migration-redirects')
    output_dir.mkdir(exist_ok=True)

    # Save as JSON
    with open(output_dir / 'redirect_map.json', 'w', encoding='utf-8') as f:
        json.dump(redirects, f, indent=2, ensure_ascii=False)

    # Save as Nginx format
    with open(output_dir / 'nginx_redirects.conf', 'w', encoding='utf-8') as f:
        f.write("# Nginx redirect rules for Life Itself migration\n\n")
        for old_path, new_url in redirects.items():
            if new_url.startswith('http'):
                f.write(f"rewrite ^{old_path}$ {new_url} permanent;\n")
            else:
                f.write(f"rewrite ^{old_path}$ {new_url} permanent;\n")

    # Save as Apache .htaccess format
    with open(output_dir / 'htaccess_redirects.txt', 'w', encoding='utf-8') as f:
        f.write("# Apache redirect rules for Life Itself migration\n\n")
        for old_path, new_url in redirects.items():
            f.write(f"Redirect 301 {old_path} {new_url}\n")

    # Save as WordPress PHP redirects
    with open(output_dir / 'wordpress_redirects.php', 'w', encoding='utf-8') as f:
        f.write("<?php\n")
        f.write("// WordPress redirect rules for Life Itself migration\n")
        f.write("// Add this to your theme's functions.php or a custom plugin\n\n")
        f.write("function lifeitself_legacy_redirects() {\n")
        f.write("    \\$redirects = array(\n")
        for old_path, new_url in redirects.items():
            f.write(f"        '{old_path}' => '{new_url}',\n")
        f.write("    );\n\n")
        f.write("    \\$request_uri = \\$_SERVER['REQUEST_URI'];\n")
        f.write("    if (isset(\\$redirects[\\$request_uri])) {\n")
        f.write("        wp_redirect(\\$redirects[\\$request_uri], 301);\n")
        f.write("        exit;\n")
        f.write("    }\n")
        f.write("}\n")
        f.write("add_action('init', 'lifeitself_legacy_redirects');\n")

    print(f"+ Created redirect mappings with {len(redirects)} rules")
    print(f"+ Saved to {output_dir}/")
    return len(redirects)

if __name__ == '__main__':
    print("Creating redirect mappings...")
    redirects = create_redirect_mapping()

    # Show sample mappings
    print("\nSample redirect mappings (first 20):")
    for i, (old, new) in enumerate(list(redirects.items())[:20]):
        print(f"  {old} -> {new}")
        if i >= 19:
            break

    total = save_redirect_mappings(redirects)
    print(f"\nTotal redirect rules created: {total}")