#!/usr/bin/env python3
"""
Step 0: Image Processing
Creates a dictionary of image rename mappings based on usage context.
"""

import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import hashlib


class ImageProcessor:
    """Processes images and creates rename dictionaries."""
    
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data structures
        self.image_usage = defaultdict(list)  # image_path -> list of files using it
        self.file_images = defaultdict(list)  # file_path -> list of images used
        self.featured_images = {}  # file_path -> featured_image_path
        self.image_references = defaultdict(list)  # image_path -> list of (file, reference_type, context)
        
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in input directory."""
        md_files = []
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(Path(root) / file)
        return md_files
    
    def find_image_files(self) -> List[Path]:
        """Find all image files in input directory."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
        image_files = []
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    image_files.append(Path(root) / file)
        return image_files
    
    def extract_frontmatter_and_content(self, file_path: Path) -> Tuple[Dict, str]:
        """Extract frontmatter and content from markdown file."""
        import frontmatter
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            return post.metadata, post.content
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return {}, ""
    
    def find_images_in_content(self, content: str, file_path: Path) -> List[Tuple[str, str]]:
        """
        Find image references in markdown content.
        Returns list of (image_path, reference_type) tuples.
        """
        images = []
        
        # Markdown image syntax: ![alt](path)
        md_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for match in re.finditer(md_pattern, content):
            alt_text = match.group(1)
            img_path = match.group(2)
            if not self._is_external_url(img_path):
                images.append((img_path, 'markdown'))
        
        # HTML img tags: <img src="path">
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(html_pattern, content):
            img_path = match.group(1)
            if not self._is_external_url(img_path):
                images.append((img_path, 'html'))
        
        return images
    
    def _is_external_url(self, path: str) -> bool:
        """Check if path is external URL."""
        return path.startswith(('http://', 'https://', '//', 'data:'))
    
    def resolve_image_path(self, img_path: str, markdown_file: Path) -> Optional[Path]:
        """Resolve relative image path to absolute path."""
        if img_path.startswith('/'):
            # Absolute path from content root
            resolved = self.input_dir / img_path.lstrip('/')
        elif img_path.startswith('./') or img_path.startswith('../'):
            # Relative to markdown file
            resolved = (markdown_file.parent / img_path).resolve()
        else:
            # Try relative to markdown file first
            resolved = (markdown_file.parent / img_path).resolve()
            if not resolved.exists():
                # Try relative to input root
                resolved = self.input_dir / img_path
        
        return resolved if resolved.exists() else None
    
    def analyze_image_usage(self):
        """Analyze how images are used across all markdown files."""
        print("Analyzing image usage...")
        
        md_files = self.find_markdown_files()
        
        for md_file in md_files:
            frontmatter, content = self.extract_frontmatter_and_content(md_file)
            
            # Check for featured image in frontmatter
            featured_img = None
            for key in ['featured_image', 'image', 'cover_image', 'hero_image']:
                if key in frontmatter and frontmatter[key]:
                    featured_img = frontmatter[key]
                    break
            
            if featured_img:
                resolved_path = self.resolve_image_path(featured_img, md_file)
                if resolved_path:
                    self.featured_images[md_file] = resolved_path
                    self.image_usage[resolved_path].append(md_file)
                    self.image_references[resolved_path].append((md_file, 'featured', featured_img))
            
            # Find images in content
            content_images = self.find_images_in_content(content, md_file)
            for img_path, ref_type in content_images:
                resolved_path = self.resolve_image_path(img_path, md_file)
                if resolved_path:
                    self.image_usage[resolved_path].append(md_file)
                    self.file_images[md_file].append(resolved_path)
                    self.image_references[resolved_path].append((md_file, ref_type, img_path))
        
        print(f"FOUND: {len(self.image_usage)} images used in {len(md_files)} markdown files")
    
    def generate_seo_filename(self, original_path: Path, usage_context: List[Path], 
                            is_featured: bool = False, sequence: int = 0) -> str:
        """Generate SEO-friendly filename based on usage context."""
        
        # Get file extension
        ext = original_path.suffix.lower()
        
        # If used in only one file, base name on that file
        if len(usage_context) == 1:
            md_file = usage_context[0]
            # Try to get slug from filename or frontmatter
            slug = self._extract_slug_from_file(md_file)
            
            if is_featured:
                return f"{slug}-feature{ext}"
            elif sequence > 0:
                return f"{slug}-{sequence:02d}{ext}"
            else:
                return f"{slug}{ext}"
        
        # If used in multiple files, keep original or use generic name
        else:
            original_stem = original_path.stem
            # Clean up the original name
            clean_name = self._slugify(original_stem)
            return f"{clean_name}{ext}"
    
    def _extract_slug_from_file(self, md_file: Path) -> str:
        """Extract or generate slug from markdown file."""
        # Try frontmatter first
        frontmatter, _ = self.extract_frontmatter_and_content(md_file)
        if 'slug' in frontmatter:
            return self._slugify(frontmatter['slug'])
        
        if 'title' in frontmatter:
            return self._slugify(frontmatter['title'])
        
        # Fall back to filename
        filename = md_file.stem
        # Remove date prefixes like "2023-01-01-"
        filename = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename)
        return self._slugify(filename)
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import unicodedata
        
        # Convert to lowercase and strip
        slug = str(text).lower().strip()
        
        # Remove accented characters
        slug = unicodedata.normalize('NFKD', slug)
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Replace non-alphanumeric with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Strip hyphens from start/end
        slug = slug.strip('-')
        
        return slug or 'untitled'
    
    def create_rename_dictionary(self) -> Dict[str, str]:
        """Create dictionary mapping original paths to new filenames."""
        print("Creating rename dictionary...")
        
        rename_dict = {}
        image_counters = defaultdict(int)  # For tracking sequences per file
        
        for img_path, usage_files in self.image_usage.items():
            # Check if this is a featured image
            is_featured = img_path in self.featured_images.values()
            
            # Count how many images this file already has for sequencing
            if len(usage_files) == 1 and not is_featured:
                md_file = usage_files[0]
                image_counters[md_file] += 1
                sequence = image_counters[md_file] if image_counters[md_file] > 1 else 0
            else:
                sequence = 0
            
            # Generate new filename
            new_filename = self.generate_seo_filename(
                img_path, usage_files, is_featured, sequence
            )
            
            # Store relative path from input directory
            relative_original = img_path.relative_to(self.input_dir)
            rename_dict[str(relative_original)] = new_filename
        
        return rename_dict
    
    def find_orphaned_images(self) -> List[str]:
        """Find image files not referenced in any markdown."""
        all_images = set(self.find_image_files())
        used_images = set(self.image_usage.keys())
        
        orphaned = []
        for img in all_images:
            if img not in used_images:
                relative_path = img.relative_to(self.input_dir)
                orphaned.append(str(relative_path))
        
        return orphaned
    
    def create_usage_report(self) -> Dict:
        """Create detailed usage report."""
        report = {
            'total_images': len(self.image_usage),
            'total_markdown_files': len(set().union(*self.image_usage.values())) if self.image_usage else 0,
            'featured_images': len(self.featured_images),
            'usage_breakdown': {},
            'multi_use_images': [],
            'single_use_images': [],
        }
        
        for img_path, usage_files in self.image_usage.items():
            relative_path = str(img_path.relative_to(self.input_dir))
            usage_count = len(usage_files)
            
            report['usage_breakdown'][relative_path] = {
                'usage_count': usage_count,
                'used_in': [str(f.relative_to(self.input_dir)) for f in usage_files],
                'is_featured': img_path in self.featured_images.values()
            }
            
            if usage_count > 1:
                report['multi_use_images'].append(relative_path)
            else:
                report['single_use_images'].append(relative_path)
        
        return report
    
    def process(self):
        """Run the complete image processing pipeline."""
        print("Starting image processing...")
        
        # Step 1: Analyze usage
        self.analyze_image_usage()
        
        # Step 2: Create rename dictionary
        rename_dict = self.create_rename_dictionary()
        
        # Step 3: Find orphaned images
        orphaned_images = self.find_orphaned_images()
        
        # Step 4: Create usage report
        usage_report = self.create_usage_report()
        
        # Step 5: Save outputs
        outputs = {
            'image_rename_dict.json': rename_dict,
            'image_usage_report.json': usage_report,
            'orphaned_images.json': {'orphaned_images': orphaned_images}
        }
        
        for filename, data in outputs.items():
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"SAVED: {output_path}")
        
        # Print summary
        print("\nSummary:")
        print(f"   Images to rename: {len(rename_dict)}")
        print(f"   Orphaned images: {len(orphaned_images)}")
        print(f"   Multi-use images: {len(usage_report['multi_use_images'])}")
        print(f"   Single-use images: {len(usage_report['single_use_images'])}")
        
        return outputs


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Process images and create rename dictionary')
    parser.add_argument('--input-dir', type=str, default='input', 
                       help='Input directory containing markdown files and assets')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for generated files')
    
    args = parser.parse_args()
    
    processor = ImageProcessor(args.input_dir, args.output_dir)
    processor.process()


if __name__ == '__main__':
    main()