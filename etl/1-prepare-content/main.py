#!/usr/bin/env python3
"""
Step 1: Prepare Content
Converts markdown files to WordPress-ready format with metadata.
"""

import os
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import re
import markdown
from markdown.extensions import fenced_code, tables, toc


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class ContentPreparer:
    """Prepares markdown content for WordPress migration."""
    
    def __init__(self, input_dir: Path, output_dir: Path, rename_dict_path: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load image rename dictionary if provided
        self.rename_dict = {}
        if rename_dict_path and rename_dict_path.exists():
            with open(rename_dict_path, 'r') as f:
                self.rename_dict = json.load(f)
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in input directory."""
        md_files = []
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(Path(root) / file)
        return md_files
    
    def extract_frontmatter_and_content(self, file_path: Path) -> tuple[Dict, str]:
        """Extract YAML frontmatter and content from markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1]
                    content_body = parts[2].strip()
                    
                    try:
                        frontmatter = yaml.safe_load(frontmatter_str) or {}
                    except yaml.YAMLError as e:
                        print(f"Warning: Could not parse frontmatter in {file_path}: {e}")
                        frontmatter = {}
                else:
                    frontmatter = {}
                    content_body = content
            else:
                frontmatter = {}
                content_body = content
            
            return frontmatter, content_body
            
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return {}, ""
    
    def convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML."""
        # Configure markdown extensions
        extensions = [
            'fenced_code',
            'tables',
            'toc',
            'nl2br',
            'sane_lists',
            'smarty',
            'attr_list'
        ]
        
        md = markdown.Markdown(extensions=extensions)
        html = md.convert(markdown_content)
        
        return html
    
    def process_wiki_links(self, content: str) -> str:
        """Convert wiki-style links [[page]] to regular markdown links."""
        # Pattern for [[link|text]] or [[link]]
        wiki_pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        
        def replace_wiki_link(match):
            link = match.group(1)
            text = match.group(2) if match.group(2) else link
            # Convert to markdown link
            # TODO: In production, resolve these to actual WordPress URLs
            slug = self.slugify(link)
            return f'[{text}](/{slug}/)'
        
        return re.sub(wiki_pattern, replace_wiki_link, content)
    
    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        # Convert to lowercase
        slug = text.lower()
        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        # Collapse multiple hyphens
        slug = re.sub(r'-+', '-', slug)
        return slug
    
    def update_image_references(self, content: str, md_file_path: Path) -> str:
        """Update image references based on rename dictionary."""
        if not self.rename_dict:
            return content
        
        # Update markdown image syntax: ![alt](path)
        def replace_md_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Resolve relative path to absolute
            if not img_path.startswith('http'):
                # Handle absolute paths starting with /
                if img_path.startswith('/'):
                    img_path = img_path.lstrip('/')
                    rel_to_input = Path(img_path)
                else:
                    # Get relative path from markdown file location
                    try:
                        abs_path = (md_file_path.parent / img_path).resolve()
                        rel_to_input = abs_path.relative_to(self.input_dir.resolve())
                    except ValueError:
                        # Path is outside input dir, use as-is
                        rel_to_input = Path(img_path)
                
                # Check if this image should be renamed
                for old_path, new_name in self.rename_dict.items():
                    if str(rel_to_input).replace('/', '\\') == old_path or \
                       str(rel_to_input).replace('\\', '/') == old_path.replace('\\', '/'):
                        # Use the new name (will be updated with WordPress URL later)
                        return f'![{alt_text}](/wp-content/uploads/{new_name})'
            
            return match.group(0)
        
        # Update HTML img tags: <img src="path" ...>
        def replace_html_image(match):
            tag_content = match.group(1)
            src_match = re.search(r'src=["\']([^"\']+)["\']', tag_content)
            if src_match:
                img_path = src_match.group(1)
                
                if not img_path.startswith('http'):
                    # Handle absolute paths starting with /
                    if img_path.startswith('/'):
                        img_path = img_path.lstrip('/')
                        rel_to_input = Path(img_path)
                    else:
                        try:
                            abs_path = (md_file_path.parent / img_path).resolve()
                            rel_to_input = abs_path.relative_to(self.input_dir.resolve())
                        except ValueError:
                            # Path is outside input dir, use as-is
                            rel_to_input = Path(img_path)
                    
                    for old_path, new_name in self.rename_dict.items():
                        if str(rel_to_input).replace('/', '\\') == old_path or \
                           str(rel_to_input).replace('\\', '/') == old_path.replace('\\', '/'):
                            new_tag = tag_content.replace(
                                src_match.group(0),
                                f'src="/wp-content/uploads/{new_name}"'
                            )
                            return f'<img {new_tag}>'
            
            return match.group(0)
        
        # Apply replacements
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, content)
        content = re.sub(r'<img\s+([^>]+)>', replace_html_image, content)
        
        return content
    
    def prepare_wordpress_data(self, md_file: Path, frontmatter: Dict, content: str) -> Dict:
        """Prepare data in WordPress-ready format."""
        # Process content
        content = self.process_wiki_links(content)
        content = self.update_image_references(content, md_file)
        html_content = self.convert_markdown_to_html(content)
        
        # Extract or generate slug
        slug = frontmatter.get('slug', '')
        if not slug:
            if 'title' in frontmatter:
                slug = self.slugify(frontmatter['title'])
            else:
                # Use filename as fallback
                slug = md_file.stem
        
        # Determine post type
        post_type = frontmatter.get('type', 'post')
        if post_type == 'blog':
            post_type = 'post'
        
        # Process dates
        date_published = frontmatter.get('date_published') or \
                        frontmatter.get('created') or \
                        frontmatter.get('date')
        
        if date_published:
            if hasattr(date_published, 'isoformat'):
                # It's already a date/datetime object
                date_published = date_published.isoformat()
            elif isinstance(date_published, str):
                try:
                    date_published = datetime.fromisoformat(date_published.replace('Z', '+00:00'))
                    date_published = date_published.isoformat()
                except:
                    pass  # Keep as string if parsing fails
        
        # Build WordPress data
        wp_data = {
            'title': frontmatter.get('title', md_file.stem),
            'slug': slug,
            'content': html_content,
            'excerpt': frontmatter.get('subtitle') or frontmatter.get('excerpt', ''),
            'status': frontmatter.get('status', 'draft'),
            'type': post_type,
            'date': date_published,
            'modified': frontmatter.get('date_updated'),
            'author': frontmatter.get('author') or frontmatter.get('authors', []),
            'featured_image': frontmatter.get('featured_image') or frontmatter.get('image'),
            'categories': frontmatter.get('categories', []),
            'tags': frontmatter.get('tags', []),
            'meta': {
                '_source_file': str(md_file.relative_to(self.input_dir)),
                '_migration_timestamp': datetime.now().isoformat()
            }
        }
        
        # Add custom fields
        for key, value in frontmatter.items():
            if key not in ['title', 'slug', 'content', 'excerpt', 'status', 'type', 
                          'date', 'modified', 'author', 'featured_image', 'categories', 'tags']:
                wp_data['meta'][key] = value
        
        # Update featured image path if it's in rename dict
        if wp_data['featured_image'] and not wp_data['featured_image'].startswith('http'):
            # Handle both relative and absolute paths
            feat_image = wp_data['featured_image']
            if feat_image.startswith('/'):
                # Absolute path from content root
                feat_image = feat_image.lstrip('/')
                
            # Check in rename dict
            for old_path, new_name in self.rename_dict.items():
                # Normalize paths for comparison
                old_normalized = old_path.replace('\\', '/')
                feat_normalized = feat_image.replace('\\', '/')
                
                if feat_normalized.endswith(old_normalized) or old_normalized.endswith(feat_normalized):
                    wp_data['featured_image'] = new_name
                    break
        
        return wp_data
    
    def process(self) -> Dict:
        """Process all markdown files."""
        print("Starting content preparation...")
        
        md_files = self.find_markdown_files()
        print(f"Found {len(md_files)} markdown files")
        
        prepared_content = []
        errors = []
        
        for md_file in md_files:
            try:
                frontmatter, content = self.extract_frontmatter_and_content(md_file)
                wp_data = self.prepare_wordpress_data(md_file, frontmatter, content)
                prepared_content.append(wp_data)
                print(f"  + Processed: {md_file.name}")
            except Exception as e:
                error_msg = f"Failed to process {md_file}: {e}"
                print(f"  x {error_msg}")
                errors.append(error_msg)
        
        # Save prepared content
        output_file = self.output_dir / 'prepared_content.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(prepared_content, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        print(f"\nSAVED: {output_file}")
        
        # Save errors if any
        if errors:
            error_file = self.output_dir / 'preparation_errors.json'
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({'errors': errors}, f, indent=2)
            print(f"SAVED: {error_file}")
        
        print(f"\nSummary:")
        print(f"   Prepared: {len(prepared_content)} posts")
        print(f"   Errors: {len(errors)}")
        
        return {
            'prepared_content.json': prepared_content,
            'preparation_errors.json': {'errors': errors} if errors else {}
        }


def main():
    parser = argparse.ArgumentParser(description='Prepare markdown content for WordPress')
    parser.add_argument('--input-dir', default='input', 
                       help='Input directory containing markdown files')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for prepared content')
    parser.add_argument('--rename-dict', 
                       help='Path to image rename dictionary from step 0')
    
    args = parser.parse_args()
    
    processor = ContentPreparer(
        Path(args.input_dir),
        Path(args.output_dir),
        Path(args.rename_dict) if args.rename_dict else None
    )
    
    processor.process()


if __name__ == '__main__':
    main()