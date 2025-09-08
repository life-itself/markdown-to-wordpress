#!/usr/bin/env python3
"""Unit tests for image processor."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ImageProcessor


class TestImageProcessor:
    """Test suite for ImageProcessor class."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary input and output directories."""
        input_dir = Path(tempfile.mkdtemp())
        output_dir = Path(tempfile.mkdtemp())
        
        yield input_dir, output_dir
        
        # Cleanup
        shutil.rmtree(input_dir)
        shutil.rmtree(output_dir)
    
    @pytest.fixture
    def sample_content(self, temp_dirs):
        """Create sample content for testing."""
        input_dir, output_dir = temp_dirs
        
        # Create directory structure
        blog_dir = input_dir / "blog"
        assets_dir = input_dir / "assets"
        blog_dir.mkdir()
        assets_dir.mkdir()
        
        # Create sample markdown files
        blog_post1 = blog_dir / "2023-01-15-my-first-post.md"
        blog_post1.write_text("""---
title: My First Blog Post
slug: my-first-post
featured_image: ../assets/hero-image.jpg
tags: [tech, blogging]
---

# My First Post

Here's an image: ![Sample](../assets/sample-image.png)

And another: ![Diagram](./images/diagram.svg)

Some HTML: <img src="../assets/inline-photo.jpg" alt="Photo">
""")
        
        blog_post2 = blog_dir / "2023-02-01-second-post.md"
        blog_post2.write_text("""---
title: "Second Post: Advanced Topics"
date: 2023-02-01
image: ../assets/cover.webp
---

# Advanced Topics

Reusing an image: ![Sample](../assets/sample-image.png)

New image: ![Chart](../assets/chart.gif)
""")
        
        # Create single-use post
        single_post = blog_dir / "standalone.md"
        single_post.write_text("""---
title: Standalone Article
---

![Unique](../assets/unique-image.jpg)
""")
        
        # Create image files
        images = [
            "hero-image.jpg",
            "sample-image.png", 
            "inline-photo.jpg",
            "cover.webp",
            "chart.gif",
            "unique-image.jpg",
            "orphaned-image.png"  # Not used anywhere
        ]
        
        for img in images:
            (assets_dir / img).write_text(f"fake image content for {img}")
        
        # Create subfolder image
        img_subdir = blog_dir / "images"
        img_subdir.mkdir()
        (img_subdir / "diagram.svg").write_text("fake svg content")
        
        return input_dir, output_dir
    
    def test_find_markdown_files(self, sample_content):
        """Test finding markdown files."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        md_files = processor.find_markdown_files()
        
        assert len(md_files) == 3
        filenames = [f.name for f in md_files]
        assert "2023-01-15-my-first-post.md" in filenames
        assert "2023-02-01-second-post.md" in filenames
        assert "standalone.md" in filenames
    
    def test_find_image_files(self, sample_content):
        """Test finding image files."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        img_files = processor.find_image_files()
        
        assert len(img_files) == 8  # 7 in assets + 1 in blog/images
        filenames = [f.name for f in img_files]
        assert "hero-image.jpg" in filenames
        assert "sample-image.png" in filenames
        assert "diagram.svg" in filenames
    
    def test_extract_frontmatter_and_content(self, sample_content):
        """Test frontmatter extraction."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        md_file = input_dir / "blog" / "2023-01-15-my-first-post.md"
        frontmatter, content = processor.extract_frontmatter_and_content(md_file)
        
        assert frontmatter['title'] == "My First Blog Post"
        assert frontmatter['slug'] == "my-first-post"
        assert frontmatter['featured_image'] == "../assets/hero-image.jpg"
        assert "Here's an image:" in content
    
    def test_find_images_in_content(self, sample_content):
        """Test finding images in markdown content."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        content = """
        ![Sample](../assets/sample-image.png)
        <img src="../assets/inline-photo.jpg" alt="Photo">
        ![External](https://example.com/image.jpg)
        """
        
        images = processor.find_images_in_content(content, input_dir / "blog" / "test.md")
        
        # Should find 2 local images, ignore external URL
        assert len(images) == 2
        paths = [img[0] for img in images]
        assert "../assets/sample-image.png" in paths
        assert "../assets/inline-photo.jpg" in paths
    
    def test_resolve_image_path(self, sample_content):
        """Test resolving relative image paths."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        md_file = input_dir / "blog" / "2023-01-15-my-first-post.md"
        
        # Test relative path
        resolved = processor.resolve_image_path("../assets/hero-image.jpg", md_file)
        assert resolved is not None
        assert resolved.name == "hero-image.jpg"
        
        # Test current directory path
        resolved = processor.resolve_image_path("./images/diagram.svg", md_file)
        assert resolved is not None
        assert resolved.name == "diagram.svg"
    
    def test_analyze_image_usage(self, sample_content):
        """Test image usage analysis."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        processor.analyze_image_usage()
        
        # Check that sample-image.png is used in 2 files
        sample_img_path = input_dir / "assets" / "sample-image.png"
        assert len(processor.image_usage[sample_img_path]) == 2
        
        # Check featured images
        assert len(processor.featured_images) == 2  # hero-image.jpg and cover.webp
        
        # Check image references
        hero_img_path = input_dir / "assets" / "hero-image.jpg"
        references = processor.image_references[hero_img_path]
        assert any(ref[1] == 'featured' for ref in references)
    
    def test_slugify(self, sample_content):
        """Test slug generation."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        test_cases = [
            ("My First Blog Post", "my-first-blog-post"),
            ("Second Post: Advanced Topics", "second-post-advanced-topics"),
            ("Special!@#$%Characters", "specialcharacters"),
            ("Accented Café", "accented-cafe"),
            ("Multiple---Hyphens", "multiple-hyphens"),
            ("  Spaces  Around  ", "spaces-around"),
        ]
        
        for input_text, expected in test_cases:
            assert processor._slugify(input_text) == expected
    
    def test_extract_slug_from_file(self, sample_content):
        """Test slug extraction from markdown files."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        # Test file with explicit slug
        md_file = input_dir / "blog" / "2023-01-15-my-first-post.md"
        slug = processor._extract_slug_from_file(md_file)
        assert slug == "my-first-post"
        
        # Test file with title but no slug
        md_file = input_dir / "blog" / "2023-02-01-second-post.md"
        slug = processor._extract_slug_from_file(md_file)
        assert slug == "second-post-advanced-topics"
        
        # Test file with no frontmatter (fallback to filename)
        md_file = input_dir / "blog" / "standalone.md"
        slug = processor._extract_slug_from_file(md_file)
        assert slug == "standalone-article"  # Uses title from frontmatter
    
    def test_generate_seo_filename(self, sample_content):
        """Test SEO filename generation."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        # Single file usage, featured image
        img_path = input_dir / "assets" / "hero-image.jpg"
        md_file = input_dir / "blog" / "2023-01-15-my-first-post.md"
        
        filename = processor.generate_seo_filename(img_path, [md_file], is_featured=True)
        assert filename == "my-first-post-feature.jpg"
        
        # Single file usage, inline image with sequence
        filename = processor.generate_seo_filename(img_path, [md_file], sequence=1)
        assert filename == "my-first-post-01.jpg"
        
        # Multiple files usage (keep original-ish name)
        md_file2 = input_dir / "blog" / "2023-02-01-second-post.md"
        filename = processor.generate_seo_filename(img_path, [md_file, md_file2])
        assert "hero-image.jpg" in filename
    
    def test_create_rename_dictionary(self, sample_content):
        """Test rename dictionary creation."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        processor.analyze_image_usage()
        rename_dict = processor.create_rename_dictionary()
        
        # Check that we have rename entries
        assert len(rename_dict) > 0
        
        # Check specific renames (handle Windows path separators)
        hero_key = next((k for k in rename_dict.keys() if "hero-image.jpg" in k), None)
        assert hero_key is not None
        assert rename_dict[hero_key] == "my-first-post-feature.jpg"
        
        # Featured image for second post
        cover_key = next((k for k in rename_dict.keys() if "cover.webp" in k), None)
        assert cover_key is not None
        assert rename_dict[cover_key] == "second-post-advanced-topics-feature.webp"
    
    def test_find_orphaned_images(self, sample_content):
        """Test finding orphaned images."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        processor.analyze_image_usage()
        orphaned = processor.find_orphaned_images()
        
        # Should find orphaned-image.png (handle Windows path separators)
        orphaned_found = any("orphaned-image.png" in path for path in orphaned)
        assert orphaned_found
        assert len(orphaned) == 1
    
    def test_create_usage_report(self, sample_content):
        """Test usage report creation."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        processor.analyze_image_usage()
        report = processor.create_usage_report()
        
        assert report['total_images'] > 0
        assert report['featured_images'] == 2
        assert len(report['multi_use_images']) > 0  # sample-image.png used twice
        assert len(report['single_use_images']) > 0
    
    def test_full_process(self, sample_content):
        """Test the complete processing pipeline."""
        input_dir, output_dir = sample_content
        processor = ImageProcessor(input_dir, output_dir)
        
        outputs = processor.process()
        
        # Check that all output files are created
        expected_files = [
            'image_rename_dict.json',
            'image_usage_report.json', 
            'orphaned_images.json'
        ]
        
        for filename in expected_files:
            assert filename in outputs
            file_path = output_dir / filename
            assert file_path.exists()
            
            # Verify JSON is valid
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, dict)
        
        # Verify rename dictionary has expected structure
        rename_dict = outputs['image_rename_dict.json']
        assert isinstance(rename_dict, dict)
        assert len(rename_dict) > 0
        
        # Verify all values are just filenames (not paths)
        for old_path, new_filename in rename_dict.items():
            assert '/' not in new_filename  # Should be filename only
            assert old_path.endswith(('.jpg', '.png', '.gif', '.webp', '.svg'))
            assert new_filename.endswith(('.jpg', '.png', '.gif', '.webp', '.svg'))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])