"""Markdown parser with front matter extraction."""

import os
import re
from pathlib import Path
from typing import List, Dict, Any
import frontmatter
import markdown
from datetime import datetime

from .types import MarkdownFile, FrontMatter


class MarkdownParser:
    """Parses markdown files and extracts front matter."""
    
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc'
            ]
        )
    
    def find_markdown_files(self, input_path: str, pattern: str = "**/*.md") -> List[str]:
        """Find all markdown files in the given directory."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {input_path}")
        
        # Use glob to find markdown files
        files = list(path.glob(pattern))
        
        # Convert to absolute path strings
        return [str(f.resolve()) for f in files if f.is_file()]
    
    def parse_file(self, file_path: str) -> MarkdownFile:
        """Parse a single markdown file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        # Load and parse the file with python-frontmatter
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Extract and normalize front matter
        front_matter = self._normalize_front_matter(post.metadata, file_path)
        
        # Convert markdown to HTML
        html = self._convert_to_html(post.content, front_matter)
        
        return MarkdownFile(
            path=file_path,
            front_matter=front_matter,
            content=post.content,
            html=html
        )
    
    def _normalize_front_matter(self, metadata: Dict[str, Any], file_path: str) -> FrontMatter:
        """Normalize front matter data."""
        # Generate slug from filename if not provided
        if not metadata.get('slug'):
            filename = Path(file_path).stem
            metadata['slug'] = self._generate_slug(filename)
        
        # Detect type from path if not specified
        if not metadata.get('type'):
            metadata['type'] = self._detect_type_from_path(file_path)
        
        # Ensure arrays for array fields
        array_fields = ['authors', 'tags', 'categories', 'initiatives', 'guests']
        for field in array_fields:
            if field in metadata and not isinstance(metadata[field], list):
                metadata[field] = [metadata[field]] if metadata[field] else []
        
        # Normalize dates
        date_fields = ['date_published', 'date_updated', 'start_date', 'end_date']
        for field in date_fields:
            if field in metadata:
                metadata[field] = self._normalize_date(metadata[field])
        
        # Set external_id if not provided
        if not metadata.get('external_id'):
            metadata['external_id'] = metadata['slug']
        
        # Create FrontMatter object with only valid fields
        valid_fields = {
            field.name for field in FrontMatter.__dataclass_fields__.values()
        }
        
        filtered_metadata = {
            k: v for k, v in metadata.items() 
            if k in valid_fields
        }
        
        return FrontMatter(**filtered_metadata)
    
    def _convert_to_html(self, content: str, front_matter: FrontMatter) -> str:
        """Convert markdown content to HTML."""
        # Convert basic markdown
        html = self.md.convert(content)
        
        # Process wiki-style links [[Page Name]] or [[slug|Display Text]]
        html = self._process_wiki_links(html)
        
        # Process image paths (mark for later media handling)
        html = self._process_image_paths(html)
        
        return html
    
    def _process_wiki_links(self, html: str) -> str:
        """Convert wiki-style links to proper HTML links."""
        # Pattern for [[Page Name]] or [[slug|Display Text]]
        wiki_pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        
        def replace_wiki_link(match):
            target = match.group(1)
            display_text = match.group(2) or target
            slug = self._generate_slug(target)
            
            # Create placeholder link for later resolution
            return f'<a href="/{slug}" data-wiki-link="{target}">{display_text}</a>'
        
        return re.sub(wiki_pattern, replace_wiki_link, html)
    
    def _process_image_paths(self, html: str) -> str:
        """Process image paths and mark for later media handling."""
        # Pattern for img tags with relative paths
        img_pattern = r'<img([^>]+)src="(?!https?://)([^"]+)"([^>]*)>'
        
        def replace_image(match):
            before = match.group(1)
            src = match.group(2)
            after = match.group(3)
            
            # Mark relative images for later processing
            return f'<img{before}src="{src}" data-local-image="{src}"{after}>'
        
        return re.sub(img_pattern, replace_image, html)
    
    def _generate_slug(self, text: str) -> str:
        """Generate a URL-friendly slug from text."""
        # Convert to lowercase
        slug = text.lower()
        
        # Remove special characters and replace with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug
    
    def _detect_type_from_path(self, file_path: str) -> str:
        """Detect content type from file path."""
        path_lower = file_path.lower().replace('\\', '/')
        
        if '/podcast' in path_lower or '/episodes' in path_lower:
            return 'podcast'
        elif '/event' in path_lower or '/gathering' in path_lower:
            return 'event'
        elif '/blog' in path_lower or '/posts' in path_lower:
            return 'blog'
        elif '/page' in path_lower or path_lower.endswith('/about.md') or path_lower.endswith('/contact.md'):
            return 'page'
        
        # Default to blog
        return 'blog'
    
    def _normalize_date(self, date_value: Any) -> str:
        """Normalize date to ISO format."""
        if not date_value:
            return datetime.now().isoformat()
        
        if isinstance(date_value, str):
            try:
                # Try parsing different formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue
                
                # If no format works, return as-is
                return date_value
            except Exception:
                return datetime.now().isoformat()
        
        return str(date_value)