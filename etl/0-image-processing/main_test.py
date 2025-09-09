#!/usr/bin/env python3
"""Tests for image processor using real sample data from lifeitself.org."""

import pytest
import json
from pathlib import Path
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ImageProcessor


class TestImageProcessor:
    """Test suite using real sample data from lifeitself.org."""

    @pytest.fixture
    def sample_processor(self):
        """Create processor with real sample data."""
        # Use the sample-data folder at project root
        project_root = Path(__file__).parent.parent.parent  # Go up to markdown-to-wordpress root
        input_dir = project_root / "sample-data"
        output_dir = project_root / "test-output"

        # Create output directory
        output_dir.mkdir(exist_ok=True)

        return ImageProcessor(input_dir, output_dir), input_dir, output_dir

    def test_find_markdown_files(self, sample_processor):
        """Test finding markdown files dynamically."""
        processor, input_dir, _ = sample_processor

        md_files = processor.find_markdown_files()

        # Should find at least one markdown file
        assert len(md_files) > 0, "No markdown files found in sample-data"

        # All found files should be .md files
        for file in md_files:
            assert file.suffix == '.md'
            assert file.exists()

    def test_extract_frontmatter(self, sample_processor):
        """Test extracting frontmatter from any available post."""
        processor, input_dir, _ = sample_processor

        # Find any markdown file dynamically
        md_files = processor.find_markdown_files()
        assert len(md_files) > 0, "No markdown files to test"

        # Test the first available markdown file
        test_file = md_files[0]
        frontmatter, content = processor.extract_frontmatter_and_content(test_file)

        # Basic validations that should work for any markdown file
        assert isinstance(frontmatter, dict)
        assert isinstance(content, str)

        # Most posts should have a title
        if frontmatter:  # If frontmatter exists
            # Check common fields that might exist
            possible_title_fields = ['title', 'name', 'heading']
            has_title = any(field in frontmatter for field in possible_title_fields)
            assert has_title or len(content) > 0, "File should have either frontmatter with title or content"

    def test_find_image_files(self, sample_processor):
        """Test finding image files dynamically."""
        processor, _, _ = sample_processor

        img_files = processor.find_image_files()

        # Check that any found images have valid extensions
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
        for img in img_files:
            assert img.suffix.lower() in valid_extensions
            assert img.exists()

    def test_slugify(self, sample_processor):
        """Test slug generation with various inputs."""
        processor, _, _ = sample_processor

        test_cases = [
            ("My First Blog Post", "my-first-blog-post"),
            ("Second Post: Advanced Topics", "second-post-advanced-topics"),
            ("Special!@#$%Characters", "specialcharacters"),
            ("Multiple---Hyphens", "multiple-hyphens"),
            ("  Spaces  Around  ", "spaces-around"),
        ]

        for input_text, expected in test_cases: 
            assert processor._slugify(input_text) == expected

    def test_image_processing_pipeline(self, sample_processor):
        """Test the complete processing pipeline with any available data."""
        processor, _, output_dir = sample_processor

        outputs = processor.process()

        # Check that some output files are generated
        assert len(outputs) > 0, "Should generate at least one output"

        # For each output file generated
        for filename, data in outputs.items():
            # Check if it's a JSON file
            if filename.endswith('.json'):
                # Check file was created
                output_path = output_dir / filename
                assert output_path.exists(), f"File not created: {output_path}"

                # Verify JSON is valid
                with open(output_path, 'r') as f:
                    loaded_data = json.load(f)
                    assert isinstance(loaded_data, dict), f"Invalid JSON structure in {filename}"

        # Check rename dictionary format (if it exists and has content)
        rename_dict = outputs.get('image_rename_dict.json', {})
        if rename_dict:  # Only validate if there are renames
            for old_path, new_name in rename_dict.items():
                # Validate the format of renamed files
                assert isinstance(new_name, str), "New name should be a string"
                assert len(new_name) > 0, "New name should not be empty"
                assert '/' not in new_name and '\\' not in new_name, "Should be filename only, not path"

                # Check it has a valid image extension
                valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')
                assert new_name.lower().endswith(valid_extensions), f"Invalid extension in {new_name}"

    def test_process_with_any_content(self, sample_processor):
        """Test that processor handles whatever content is available."""
        processor, input_dir, _ = sample_processor

        # Count available content
        md_files = processor.find_markdown_files()
        img_files = processor.find_image_files()

        print(f"Testing with {len(md_files)} markdown files and {len(img_files)} image files")

        # Process should complete without errors regardless of content
        outputs = processor.process()

        # Should produce some output files
        assert len(outputs) > 0, "Should produce at least one output file"
        assert isinstance(outputs, dict), "Outputs should be a dictionary"

        # All outputs should be valid JSON-serializable dicts
        for filename, data in outputs.items():
            assert isinstance(data, dict), f"Output {filename} should be a dictionary"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])