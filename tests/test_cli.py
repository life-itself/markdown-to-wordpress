"""Unit tests for the CLI module."""

import pytest
from unittest.mock import MagicMock, patch, call
from click.testing import CliRunner
from pathlib import Path

from src.cli import cli, validate, inspect, migrate


class TestCLI:
    """Test suite for CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_main_command(self):
        """Test main CLI command shows version and help."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Markdown to WordPress Migration Tool' in result.output
        assert 'validate' in result.output
        assert 'inspect' in result.output
        assert 'migrate' in result.output
    
    @patch('src.cli.MarkdownParser')
    def test_validate_command_success(self, mock_parser_class, temp_markdown_dir):
        """Test successful validation command."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md",
            f"{temp_markdown_dir}/events/event1.md"
        ]
        
        # Create mock parsed files
        mock_parsed1 = MagicMock()
        mock_parsed1.front_matter.title = "Blog Post"
        mock_parsed1.front_matter.slug = "blog-post"
        mock_parsed1.front_matter.type = "blog"
        mock_parsed1.front_matter.tags = ["test"]
        mock_parsed1.front_matter.categories = None
        mock_parsed1.front_matter.start_date = None
        mock_parsed1.front_matter.episode_number = None
        mock_parsed1.front_matter.audio_url = None
        mock_parsed1.content = "Blog content"
        
        mock_parsed2 = MagicMock()
        mock_parsed2.front_matter.title = "Test Event"
        mock_parsed2.front_matter.slug = "test-event"
        mock_parsed2.front_matter.type = "event"
        mock_parsed2.front_matter.tags = None
        mock_parsed2.front_matter.categories = None
        mock_parsed2.front_matter.start_date = "2025-10-01"
        mock_parsed2.front_matter.episode_number = None
        mock_parsed2.front_matter.audio_url = None
        mock_parsed2.content = "Event description"
        
        mock_parser.parse_file.side_effect = [mock_parsed1, mock_parsed2]
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(validate, ['--input-path', temp_markdown_dir])
        
        assert result.exit_code == 0
        assert "Found 2 markdown files" in result.output
        assert "SUCCESS" in result.output or "OK" in result.output
    
    @patch('src.cli.MarkdownParser')
    def test_validate_command_no_files(self, mock_parser_class, tmp_path):
        """Test validation with no markdown files."""
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = []
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(validate, ['--input-path', str(tmp_path)])
        
        assert result.exit_code == 0
        assert "No markdown files found" in result.output
    
    @patch('src.cli.MarkdownParser')
    def test_validate_command_with_errors(self, mock_parser_class, temp_markdown_dir):
        """Test validation with file errors."""
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        
        # Create mock parsed file with missing required fields
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = None  # Missing title
        mock_parsed.front_matter.slug = None  # Missing slug
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.tags = None
        mock_parsed.front_matter.categories = None
        mock_parsed.front_matter.start_date = None
        mock_parsed.front_matter.episode_number = None
        mock_parsed.front_matter.audio_url = None
        mock_parsed.content = "  "  # Empty content
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(validate, ['--input-path', temp_markdown_dir])
        
        assert result.exit_code == 0
        # Check for validation issues in output - may be in table or error format
        output_lower = result.output.lower()
        assert "missing title" in output_lower or "n/a" in result.output
        assert "missing slug" in output_lower or "error" in output_lower
    
    @patch('src.cli.MarkdownParser')
    def test_validate_command_verbose(self, mock_parser_class, temp_markdown_dir):
        """Test validation with verbose output."""
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "Test Post"
        mock_parsed.front_matter.slug = "test-post"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.tags = ["tag1", "tag2"]
        mock_parsed.front_matter.categories = ["cat1"]
        mock_parsed.front_matter.start_date = None
        mock_parsed.front_matter.episode_number = None
        mock_parsed.front_matter.audio_url = None
        mock_parsed.content = "Content" * 100
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(validate, ['--input-path', temp_markdown_dir, '--verbose'])
        
        assert result.exit_code == 0
        assert "post1.md" in result.output
        assert "Type: blog" in result.output
        assert "Title: Test Post" in result.output
        assert "Slug: test-post" in result.output
        assert "Content length:" in result.output
        assert "Tags: tag1, tag2" in result.output
        assert "Categories: cat1" in result.output
    
    @patch('src.cli.MarkdownParser')
    @patch('os.path.exists')
    def test_inspect_command_success(self, mock_exists, mock_parser_class, temp_markdown_file):
        """Test successful file inspection."""
        mock_exists.return_value = True
        
        mock_parser = MagicMock()
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "Test Post"
        mock_parsed.front_matter.slug = "test-post"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.status = "publish"
        mock_parsed.front_matter.date_published = "2025-01-15"
        mock_parsed.front_matter.authors = ["John Doe"]
        mock_parsed.front_matter.tags = ["test", "sample"]
        mock_parsed.front_matter.categories = ["Tech"]
        mock_parsed.front_matter.featured_image = "./test.jpg"
        mock_parsed.front_matter.start_date = None
        mock_parsed.front_matter.end_date = None
        mock_parsed.front_matter.location_name = None
        mock_parsed.front_matter.episode_number = None
        mock_parsed.front_matter.audio_url = None
        mock_parsed.content = "Test content with multiple lines and paragraphs."
        mock_parsed.html = "<p>Test HTML content</p>"
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(inspect, ['--file-path', temp_markdown_file])
        
        assert result.exit_code == 0
        assert "Test Post" in result.output
        assert "test-post" in result.output
        assert "blog" in result.output
        assert "John Doe" in result.output
        assert "test, sample" in result.output
    
    @patch('os.path.exists')
    def test_inspect_command_file_not_found(self, mock_exists):
        """Test inspection with non-existent file."""
        mock_exists.return_value = False
        
        result = self.runner.invoke(inspect, ['--file-path', '/nonexistent/file.md'])
        
        assert result.exit_code == 0
        assert "File not found" in result.output
    
    @patch('src.cli.MarkdownParser')
    @patch('os.path.exists')
    def test_inspect_command_show_html(self, mock_exists, mock_parser_class):
        """Test inspection with HTML output."""
        mock_exists.return_value = True
        
        mock_parser = MagicMock()
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "Test"
        mock_parsed.front_matter.slug = "test"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.status = None
        mock_parsed.front_matter.date_published = None
        mock_parsed.front_matter.authors = None
        mock_parsed.front_matter.tags = None
        mock_parsed.front_matter.categories = None
        mock_parsed.front_matter.featured_image = None
        mock_parsed.front_matter.start_date = None
        mock_parsed.front_matter.end_date = None
        mock_parsed.front_matter.location_name = None
        mock_parsed.front_matter.episode_number = None
        mock_parsed.front_matter.audio_url = None
        mock_parsed.content = "Content"
        mock_parsed.html = "<h1>Heading</h1><p>HTML content with formatting</p>"
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        result = self.runner.invoke(inspect, ['--file-path', 'test.md', '--show-html'])
        
        assert result.exit_code == 0
        assert "Generated HTML:" in result.output
        assert "<h1>Heading</h1>" in result.output
    
    @patch('src.cli.WordPressClient')
    @patch('src.cli.ContentMapper')
    @patch('src.cli.MarkdownParser')
    def test_migrate_command_dry_run(self, mock_parser_class, mock_mapper_class, mock_wp_client_class, temp_markdown_dir):
        """Test migration in dry-run mode."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "Test Post"
        mock_parsed.front_matter.slug = "test-post"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.status = None
        mock_parsed.content = "Content"
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        # Mock WordPress client
        mock_wp_client = MagicMock()
        mock_wp_client_class.return_value = mock_wp_client
        
        # Mock mapper
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        
        result = self.runner.invoke(migrate, [
            '--input-path', temp_markdown_dir,
            '--wp-url', 'https://example.com',
            '--wp-user', 'testuser',
            '--wp-password', 'testpass',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "Would create/update" in result.output
        assert "test-post" in result.output
        
        # Ensure no actual WordPress calls were made
        mock_wp_client.test_connection.assert_not_called()
        mock_wp_client.create_post.assert_not_called()
        mock_wp_client.update_post.assert_not_called()
    
    @patch('src.cli.WordPressClient')
    @patch('src.cli.ContentMapper')
    @patch('src.cli.MarkdownParser')
    def test_migrate_command_create_post(self, mock_parser_class, mock_mapper_class, mock_wp_client_class, temp_markdown_dir):
        """Test migration creating new posts."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "New Post"
        mock_parsed.front_matter.slug = "new-post"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.status = None
        mock_parsed.content = "Content"
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        # Mock WordPress client
        mock_wp_client = MagicMock()
        mock_wp_client.test_connection.return_value = True
        mock_wp_client.find_post_by_slug.return_value = None
        mock_wp_client.find_post_by_meta.return_value = None
        mock_wp_client.create_post.return_value = {"id": 123, "slug": "new-post"}
        mock_wp_client_class.return_value = mock_wp_client
        
        # Mock mapper
        mock_mapper = MagicMock()
        mock_mapper.map_to_wordpress.return_value = {
            "title": "New Post",
            "slug": "new-post",
            "content": "Content",
            "meta": {"_external_id": "new-post"}
        }
        mock_mapper.get_post_type.return_value = "posts"
        mock_mapper_class.return_value = mock_mapper
        
        result = self.runner.invoke(migrate, [
            '--input-path', temp_markdown_dir,
            '--wp-url', 'https://example.com',
            '--wp-user', 'testuser',
            '--wp-password', 'testpass'
        ])
        
        assert result.exit_code == 0
        assert "Connected to WordPress" in result.output
        assert "Created:" in result.output
        assert "New Post" in result.output
        assert "ID: 123" in result.output
        
        mock_wp_client.create_post.assert_called_once()
    
    @patch('src.cli.WordPressClient')
    @patch('src.cli.ContentMapper')
    @patch('src.cli.MarkdownParser')
    def test_migrate_command_update_post(self, mock_parser_class, mock_mapper_class, mock_wp_client_class, temp_markdown_dir):
        """Test migration updating existing posts."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        
        mock_parsed = MagicMock()
        mock_parsed.front_matter.title = "Existing Post"
        mock_parsed.front_matter.slug = "existing-post"
        mock_parsed.front_matter.type = "blog"
        mock_parsed.front_matter.status = None
        mock_parsed.content = "Updated content"
        
        mock_parser.parse_file.return_value = mock_parsed
        mock_parser_class.return_value = mock_parser
        
        # Mock WordPress client
        mock_wp_client = MagicMock()
        mock_wp_client.test_connection.return_value = True
        mock_wp_client.find_post_by_slug.return_value = {"id": 456, "slug": "existing-post"}
        mock_wp_client.update_post.return_value = {"id": 456, "slug": "existing-post"}
        mock_wp_client_class.return_value = mock_wp_client
        
        # Mock mapper
        mock_mapper = MagicMock()
        mock_mapper.map_to_wordpress.return_value = {
            "title": "Existing Post",
            "slug": "existing-post",
            "content": "Updated content"
        }
        mock_mapper.get_post_type.return_value = "posts"
        mock_mapper_class.return_value = mock_mapper
        
        result = self.runner.invoke(migrate, [
            '--input-path', temp_markdown_dir,
            '--wp-url', 'https://example.com',
            '--wp-user', 'testuser',
            '--wp-password', 'testpass'
        ])
        
        assert result.exit_code == 0
        assert "Updated:" in result.output
        assert "Existing Post" in result.output
        assert "ID: 456" in result.output
        
        mock_wp_client.update_post.assert_called_once()
    
    @patch('src.cli.WordPressClient')
    @patch('src.cli.ContentMapper')
    @patch('src.cli.MarkdownParser')
    def test_migrate_command_connection_failure(self, mock_parser_class, mock_mapper_class, mock_wp_client_class, temp_markdown_dir):
        """Test migration with WordPress connection failure."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md"
        ]
        mock_parser_class.return_value = mock_parser
        
        # Mock WordPress client with connection failure
        mock_wp_client = MagicMock()
        mock_wp_client.test_connection.return_value = False
        mock_wp_client_class.return_value = mock_wp_client
        
        # Mock mapper
        mock_mapper = MagicMock()
        mock_mapper_class.return_value = mock_mapper
        
        result = self.runner.invoke(migrate, [
            '--input-path', temp_markdown_dir,
            '--wp-url', 'https://example.com',
            '--wp-user', 'testuser',
            '--wp-password', 'testpass'
        ])
        
        assert result.exit_code == 0
        assert "WordPress connection failed" in result.output
    
    @patch('src.cli.WordPressClient')
    @patch('src.cli.ContentMapper')
    @patch('src.cli.MarkdownParser')
    def test_migrate_command_with_errors(self, mock_parser_class, mock_mapper_class, mock_wp_client_class, temp_markdown_dir):
        """Test migration with processing errors."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.find_markdown_files.return_value = [
            f"{temp_markdown_dir}/blog/post1.md",
            f"{temp_markdown_dir}/blog/post2.md"
        ]
        
        mock_parsed1 = MagicMock()
        mock_parsed1.front_matter.title = "Good Post"
        mock_parsed1.front_matter.slug = "good-post"
        mock_parsed1.front_matter.type = "blog"
        mock_parsed1.front_matter.status = None
        
        mock_parsed2 = MagicMock()
        mock_parsed2.front_matter.title = "Bad Post"
        mock_parsed2.front_matter.slug = "bad-post"
        mock_parsed2.front_matter.type = "blog"
        mock_parsed2.front_matter.status = None
        
        mock_parser.parse_file.side_effect = [mock_parsed1, mock_parsed2]
        mock_parser_class.return_value = mock_parser
        
        # Mock WordPress client
        mock_wp_client = MagicMock()
        mock_wp_client.test_connection.return_value = True
        mock_wp_client.find_post_by_slug.return_value = None
        mock_wp_client.find_post_by_meta.return_value = None
        mock_wp_client.create_post.side_effect = [
            {"id": 123, "slug": "good-post"},
            Exception("Creation failed")
        ]
        mock_wp_client_class.return_value = mock_wp_client
        
        # Mock mapper
        mock_mapper = MagicMock()
        mock_mapper.map_to_wordpress.return_value = {"title": "Test", "slug": "test"}
        mock_mapper.get_post_type.return_value = "posts"
        mock_mapper_class.return_value = mock_mapper
        
        result = self.runner.invoke(migrate, [
            '--input-path', temp_markdown_dir,
            '--wp-url', 'https://example.com',
            '--wp-user', 'testuser',
            '--wp-password', 'testpass'
        ])
        
        assert result.exit_code == 0
        assert "Created: 1" in result.output
        assert "Errors: 1" in result.output
        assert "Migration completed with 1 errors" in result.output