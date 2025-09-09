#!/usr/bin/env python3
"""Tests for content preparer using real sample data."""

import pytest
import json
from pathlib import Path
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ContentPreparer


class TestContentPreparer:
    """Test suite for content preparation."""
    
    @pytest.fixture
    def sample_processor(self):
        """Create processor with real sample data."""
        project_root = Path(__file__).parent.parent.parent
        input_dir = project_root / "sample-data"
        output_dir = project_root / "test-output"
        rename_dict_path = project_root / "etl/0-image-processing/test-output/image_rename_dict.json"
        
        output_dir.mkdir(exist_ok=True)
        
        return ContentPreparer(input_dir, output_dir, rename_dict_path), input_dir, output_dir
    
    def test_find_markdown_files(self, sample_processor):
        """Test finding markdown files."""
        processor, _, _ = sample_processor
        
        md_files = processor.find_markdown_files()
        assert len(md_files) > 0, "Should find at least one markdown file"
        
        for file in md_files:
            assert file.suffix == '.md'
            assert file.exists()
    
    def test_extract_frontmatter_and_content(self, sample_processor):
        """Test frontmatter extraction."""
        processor, _, _ = sample_processor
        
        md_files = processor.find_markdown_files()
        assert len(md_files) > 0
        
        # Test with the first file
        frontmatter, content = processor.extract_frontmatter_and_content(md_files[0])
        
        assert isinstance(frontmatter, dict)
        assert isinstance(content, str)
        assert len(content) > 0
    
    def test_slugify(self, sample_processor):
        """Test slug generation."""
        processor, _, _ = sample_processor
        
        test_cases = [
            ("My Test Post", "my-test-post"),
            ("Special!@#Characters", "special-characters"),  # Fixed expectation
            ("Multiple---Hyphens", "multiple-hyphens")
        ]
        
        for input_text, expected in test_cases:
            assert processor.slugify(input_text) == expected
    
    def test_convert_markdown_to_html(self, sample_processor):
        """Test markdown to HTML conversion."""
        processor, _, _ = sample_processor
        
        markdown_text = "# Test Heading\n\nSome **bold** text."
        html = processor.convert_markdown_to_html(markdown_text)
        
        assert "<h1" in html  # h1 with possible attributes
        assert "<strong>" in html or "<b>" in html
    
    def test_prepare_wordpress_data(self, sample_processor):
        """Test WordPress data preparation."""
        processor, _, _ = sample_processor
        
        # Test with sample frontmatter and content
        frontmatter = {
            'title': 'Test Post',
            'tags': ['test', 'sample'],
            'categories': ['blog'],
            'created': '2023-01-01'
        }
        content = "# Test Content\n\nThis is a test post."
        
        # Use a file path within the input directory
        md_file = processor.input_dir / "test.md"
        wp_data = processor.prepare_wordpress_data(md_file, frontmatter, content)
        
        assert wp_data['title'] == 'Test Post'
        assert wp_data['slug'] == 'test-post'
        assert isinstance(wp_data['content'], str)
        assert len(wp_data['content']) > 0
        assert wp_data['tags'] == ['test', 'sample']
        assert wp_data['categories'] == ['blog']
    
    def test_process_pipeline(self, sample_processor):
        """Test the complete content preparation pipeline."""
        processor, _, output_dir = sample_processor
        
        outputs = processor.process()
        
        # Check that output files are generated
        assert 'prepared_content.json' in outputs
        
        # Check file was created
        output_file = output_dir / 'prepared_content.json'
        assert output_file.exists()
        
        # Verify JSON is valid
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Check structure of first item
            first_item = data[0]
            required_fields = ['title', 'slug', 'content', 'type']
            for field in required_fields:
                assert field in first_item, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])