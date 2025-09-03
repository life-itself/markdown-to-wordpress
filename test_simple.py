#!/usr/bin/env python3
"""Simple test script without Rich to avoid Windows encoding issues."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from src.parser import MarkdownParser

def test_parser():
    """Test the markdown parser with sample data."""
    print("=== Testing Markdown Parser ===\n")

    # Initialize parser
    parser = MarkdownParser()

    # Find files
    sample_path = "sample/content"
    if not os.path.exists(sample_path):
        print(f"ERROR: Sample path not found: {sample_path}")
        return

    print(f"Looking for files in: {sample_path}")
    files = parser.find_markdown_files(sample_path)

    print(f"Found {len(files)} files:")
    for f in files:
        print(f"  - {Path(f).name}")

    print("\n=== Parsing Files ===\n")

    # Parse each file
    for file_path in files:
        print(f"--- {Path(file_path).name} ---")

        try:
            parsed = parser.parse_file(file_path)
            fm = parsed.front_matter

            print(f"Title: {fm.title}")
            print(f"Type: {fm.type}")
            print(f"Slug: {fm.slug}")
            print(f"Status: {fm.status}")

            if fm.tags:
                print(f"Tags: {', '.join(fm.tags)}")
            if fm.authors:
                print(f"Authors: {', '.join(fm.authors)}")

            # Type-specific info
            if fm.type == 'event':
                print(f"Start Date: {fm.start_date}")
                print(f"Location: {fm.location_name}")
            elif fm.type == 'podcast':
                print(f"Episode: {fm.episode_number}")
                print(f"Audio: {fm.audio_url}")

            print(f"Content Length: {len(parsed.content)} chars")
            print(f"HTML Length: {len(parsed.html)} chars" if parsed.html else "No HTML")

            # Basic validation
            issues = []
            if not fm.title:
                issues.append("Missing title")
            if not fm.slug:
                issues.append("Missing slug")
            if fm.type == 'event' and not fm.start_date:
                issues.append("Event missing start_date")

            if issues:
                print("ISSUES:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("STATUS: OK")

            print()

        except Exception as e:
            print(f"ERROR parsing file: {e}")
            print()

if __name__ == "__main__":
    test_parser()
