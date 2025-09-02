"""Command line interface for the migration tool."""

import click
import logging
import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .parser import MarkdownParser
from .wordpress_client import WordPressClient
from .mapper import ContentMapper
from .types import Config

# Set up console for rich output
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Markdown to WordPress Migration Tool (Python Version)"""
    rprint("[bold blue]Markdown to WordPress Migration Tool v1.0.0[/bold blue]")
    rprint("[dim]Python implementation for testing and validation[/dim]\n")


@cli.command()
@click.option('--input-path', '-i', required=True, help='Path to markdown files')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def validate(input_path: str, verbose: bool):
    """Validate markdown files and show parsing results."""
    try:
        # Initialize parser
        parser = MarkdownParser()
        
        # Find markdown files
        console.print(f"[blue]Searching for markdown files in:[/blue] {input_path}")
        files = parser.find_markdown_files(input_path)
        
        if not files:
            console.print("[red]No markdown files found![/red]")
            return
        
        console.print(f"[green]Found {len(files)} markdown files[/green]\n")
        
        # Create results table
        table = Table(title="Validation Results")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Title", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Issues", style="red")
        
        # Parse and validate each file
        total_parsed = 0
        total_errors = 0
        
        for file_path in files:
            try:
                parsed = parser.parse_file(file_path)
                total_parsed += 1
                
                # Basic validation
                issues = []
                if not parsed.front_matter.title:
                    issues.append("Missing title")
                if not parsed.front_matter.slug:
                    issues.append("Missing slug")
                if not parsed.content.strip():
                    issues.append("Empty content")
                
                # Type-specific validation
                if parsed.front_matter.type == 'event':
                    if not parsed.front_matter.start_date:
                        issues.append("Missing start_date")
                elif parsed.front_matter.type == 'podcast':
                    if not parsed.front_matter.episode_number and not parsed.front_matter.audio_url:
                        issues.append("Missing episode_number or audio_url")
                
                # Add to table
                file_name = Path(file_path).name
                issues_str = ", ".join(issues) if issues else "OK"
                status = "ERROR" if issues else "OK"
                
                if issues:
                    total_errors += 1
                
                table.add_row(
                    file_name,
                    parsed.front_matter.type or "unknown",
                    parsed.front_matter.title or "N/A",
                    status,
                    issues_str
                )
                
                # Show detailed info if verbose
                if verbose:
                    console.print(f"\n[bold]{file_name}[/bold]")
                    console.print(f"  Type: {parsed.front_matter.type}")
                    console.print(f"  Title: {parsed.front_matter.title}")
                    console.print(f"  Slug: {parsed.front_matter.slug}")
                    console.print(f"  Content length: {len(parsed.content)} chars")
                    if parsed.front_matter.tags:
                        console.print(f"  Tags: {', '.join(parsed.front_matter.tags)}")
                    if parsed.front_matter.categories:
                        console.print(f"  Categories: {', '.join(parsed.front_matter.categories)}")
            
            except Exception as e:
                total_errors += 1
                file_name = Path(file_path).name
                table.add_row(file_name, "ERROR", "N/A", "PARSE_ERROR", str(e))
                logger.error(f"Failed to parse {file_path}: {e}")
        
        # Show table
        console.print(table)
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total files: {len(files)}")
        console.print(f"  Parsed successfully: {total_parsed}")
        console.print(f"  Errors: {total_errors}")
        
        if total_errors > 0:
            console.print(f"[red]WARNING: {total_errors} files have issues[/red]")
        else:
            console.print("[green]SUCCESS: All files validated successfully![/green]")
    
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.option('--file-path', '-f', required=True, help='Path to markdown file')
@click.option('--show-html', is_flag=True, help='Show generated HTML')
def inspect(file_path: str, show_html: bool):
    """Inspect a single markdown file and show details."""
    try:
        if not os.path.exists(file_path):
            console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Parse the file
        parser = MarkdownParser()
        parsed = parser.parse_file(file_path)
        
        # Show file info
        console.print(f"[bold blue]Inspecting:[/bold blue] {file_path}")
        console.rule(style="blue")
        
        # Front matter
        console.print("[bold]Front Matter:[/bold]")
        fm = parsed.front_matter
        
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Type", fm.type or "N/A")
        info_table.add_row("Title", fm.title or "N/A")
        info_table.add_row("Slug", fm.slug or "N/A")
        info_table.add_row("Status", fm.status or "N/A")
        
        if fm.date_published:
            info_table.add_row("Published", fm.date_published)
        if fm.authors:
            info_table.add_row("Authors", ", ".join(fm.authors))
        if fm.tags:
            info_table.add_row("Tags", ", ".join(fm.tags))
        if fm.categories:
            info_table.add_row("Categories", ", ".join(fm.categories))
        if fm.featured_image:
            info_table.add_row("Featured Image", fm.featured_image)
        
        # Event specific
        if fm.type == 'event':
            if fm.start_date:
                info_table.add_row("Start Date", fm.start_date)
            if fm.end_date:
                info_table.add_row("End Date", fm.end_date)
            if fm.location_name:
                info_table.add_row("Location", fm.location_name)
        
        # Podcast specific
        if fm.type == 'podcast':
            if fm.episode_number:
                info_table.add_row("Episode", str(fm.episode_number))
            if fm.audio_url:
                info_table.add_row("Audio URL", fm.audio_url)
        
        console.print(info_table)
        
        # Content preview
        console.print(f"\n[bold]Content Preview:[/bold] ({len(parsed.content)} chars)")
        preview = parsed.content[:300] + "..." if len(parsed.content) > 300 else parsed.content
        console.print(f"[dim]{preview}[/dim]")
        
        # HTML output
        if show_html and parsed.html:
            console.print(f"\n[bold]Generated HTML:[/bold] ({len(parsed.html)} chars)")
            html_preview = parsed.html[:500] + "..." if len(parsed.html) > 500 else parsed.html
            console.print(f"[dim]{html_preview}[/dim]")
        
        # Validation
        console.print(f"\n[bold]Validation:[/bold]")
        issues = []
        
        if not fm.title:
            issues.append("Missing title")
        if not fm.slug:
            issues.append("Missing slug")
        if not parsed.content.strip():
            issues.append("Empty content")
        
        if fm.type == 'event' and not fm.start_date:
            issues.append("Event missing start_date")
        
        if issues:
            for issue in issues:
                console.print(f"  [red]- {issue}[/red]")
        else:
            console.print("  [green]OK - No issues found[/green]")
    
    except Exception as e:
        console.print(f"[red]Inspection failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.option('--input-path', '-i', required=True, help='Path to markdown files')
@click.option('--wp-url', required=True, help='WordPress site URL')
@click.option('--wp-user', required=True, help='WordPress username')
@click.option('--wp-password', required=True, help='WordPress application password')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def migrate(input_path: str, wp_url: str, wp_user: str, wp_password: str, dry_run: bool):
    """Migrate markdown files to WordPress (basic implementation)."""
    try:
        if dry_run:
            console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]\n")
        
        # Create config
        config = Config(
            wordpress_url=wp_url,
            username=wp_user,
            password=wp_password
        )
        
        # Initialize components
        parser = MarkdownParser()
        wp_client = WordPressClient(config)
        mapper = ContentMapper(config, wp_client)
        
        # Test WordPress connection (unless dry run)
        if not dry_run:
            console.print("[blue]Testing WordPress connection...[/blue]")
            if not wp_client.test_connection():
                console.print("[red]WordPress connection failed![/red]")
                return
            console.print("[green]✓ Connected to WordPress[/green]\n")
        
        # Find and parse files
        console.print(f"[blue]Finding markdown files in:[/blue] {input_path}")
        files = parser.find_markdown_files(input_path)
        
        if not files:
            console.print("[red]No markdown files found![/red]")
            return
        
        console.print(f"[green]Found {len(files)} markdown files[/green]\n")
        
        # Process each file
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for file_path in files:
            try:
                # Parse file
                parsed = parser.parse_file(file_path)
                file_name = Path(file_path).name
                
                console.print(f"[cyan]Processing:[/cyan] {file_name}")
                
                if dry_run:
                    # Just show what would be done
                    console.print(f"  Would create/update: {parsed.front_matter.type} - {parsed.front_matter.title}")
                    console.print(f"  Slug: {parsed.front_matter.slug}")
                    console.print(f"  Status: {parsed.front_matter.status or config.default_status}")
                else:
                    # Actually create/update post
                    post_data = mapper.map_to_wordpress(parsed)
                    post_type = mapper.get_post_type(parsed.front_matter.type or "blog")
                    
                    # Check if post already exists
                    existing = wp_client.find_post_by_slug(parsed.front_matter.slug, post_type)
                    if not existing and post_data.get("meta", {}).get("_external_id"):
                        existing = wp_client.find_post_by_meta("_external_id", post_data["meta"]["_external_id"], post_type)
                    
                    if existing:
                        # Update existing post
                        wp_client.update_post(existing["id"], post_data, post_type)
                        console.print(f"  [blue]✓ Updated:[/blue] {parsed.front_matter.title} (ID: {existing['id']})")
                        updated_count += 1
                    else:
                        # Create new post
                        result = wp_client.create_post(post_data, post_type)
                        console.print(f"  [green]✓ Created:[/green] {parsed.front_matter.title} (ID: {result['id']})")
                        created_count += 1
                
                console.print()
                
            except Exception as e:
                console.print(f"  [red]✗ Error: {e}[/red]\n")
                logger.error(f"Failed to process {file_path}: {e}")
                error_count += 1
        
        if dry_run:
            console.print("[yellow]Dry run completed. Run without --dry-run to perform actual migration.[/yellow]")
        else:
            console.print(f"\n[bold]Migration Summary:[/bold]")
            console.print(f"  Created: {created_count}")
            console.print(f"  Updated: {updated_count}")
            console.print(f"  Errors: {error_count}")
            console.print(f"  Total: {len(files)}")
            
            if error_count == 0:
                console.print("[green]✓ Migration completed successfully![/green]")
            else:
                console.print(f"[yellow]Migration completed with {error_count} errors[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Migration failed: {e}[/red]")
        raise click.Abort()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()