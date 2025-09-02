# Markdown to WordPress Migration Tool (Python Version)

This is a Python implementation of the markdown-to-wordpress migration tool, designed for testing and validation with small datasets.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Test with sample data:**
```bash
python test_simple.py
```

3. **Validate markdown files:**
```bash
python -m src.cli validate -i sample-data/content
```

4. **Inspect a single file:**
```bash
python -m src.cli inspect -f sample-data/content/about.md
```

5. **Migrate to WordPress:**
```bash
python -m src.cli migrate -i sample-data/content --wp-url https://your-site.com --wp-user admin --wp-password your-app-password --dry-run
```

## Sample Data

The `sample-data/` directory contains:
- **3 markdown files** representing different content types (blog, page, event)
- **4 placeholder images** in `assets/images/`

### Sample Files:
1. `about.md` - A page about Life Itself
2. `community.md` - A blog post about community
3. `conscious-coliving-retreat.md` - An event listing

## Features Implemented

✅ **Core Parser**
- Front matter extraction with python-frontmatter
- Markdown to HTML conversion
- Content type detection (blog, event, podcast, page)
- Wiki-style link processing (`[[link]]` → `<a href="/slug">link</a>`)
- Image path processing for later media handling

✅ **WordPress Client**
- REST API connection with application password auth
- Post creation/update operations
- Taxonomy term management
- User lookup by email/name
- Idempotent operations (find existing by slug/meta)

✅ **CLI Interface**
- `validate` - Check markdown files for issues
- `inspect` - Show detailed info about a single file
- `migrate` - Full WordPress post creation and management

## Testing Results

Running `python test_simple.py` shows:

```
=== Testing Markdown Parser ===

Looking for files in: sample-data/content
Found 3 files:
  - about.md
  - community.md
  - conscious-coliving-retreat.md

=== Parsing Files ===

--- about.md ---
Title: About Life Itself
Type: page
Slug: about
Status: publish
Content Length: 733 chars
HTML Length: 1058 chars
STATUS: OK

--- community.md ---
Title: Our Community
Type: blog
Slug: community
Status: publish
Tags: community, connection, wisdom
Authors: Rufus Pollock, Sylvie Barbier
Content Length: 963 chars
HTML Length: 1401 chars
STATUS: OK

--- conscious-coliving-retreat.md ---
Title: Conscious Coliving Retreat - Spring 2024
Type: event
Slug: conscious-coliving-retreat-spring-2024
Status: publish
Tags: retreat, coliving, community
Start Date: 2024-04-15T00:00:00
Location: Life Itself Hub, Bergerac
Content Length: 1193 chars
HTML Length: 1768 chars
STATUS: OK
```

## WordPress Post Creation

The tool now supports **full WordPress post creation**! See `MIGRATION_GUIDE.md` for complete instructions.

**What's Implemented:**
✅ WordPress REST API integration  
✅ Post/page creation and updates  
✅ Taxonomy management (tags, categories)  
✅ Author resolution  
✅ Content mapping from front matter  
✅ Idempotent operations (safe re-runs)  

**Next Steps for Production Scale:**
1. **Media Handler** - Implement image upload to WordPress Media Library
2. **Bulk Processing** - Handle 1000+ files efficiently  
3. **Configuration** - YAML config file support
4. **Error Recovery** - Better error handling and retry logic

## Project Structure

```
markdown-to-wordpress/
├── src/
│   ├── cli.py              # Command line interface
│   ├── parser.py           # Markdown parsing and front matter extraction
│   ├── wordpress_client.py # WordPress REST API client
│   ├── mapper.py           # Content mapping to WordPress format
│   └── types.py            # Type definitions
├── sample-data/
│   ├── content/            # Sample markdown files
│   └── assets/images/      # Sample images (placeholders)
├── config/
│   └── config.example.yml  # Configuration example
├── test_simple.py          # Simple test script
├── requirements.txt        # Python dependencies
├── MIGRATION_GUIDE.md      # Step-by-step WordPress migration guide
└── README.md               # This file
```

## Dependencies

- `requests` - HTTP client for WordPress API
- `pyyaml` - YAML configuration support  
- `python-frontmatter` - Front matter parsing
- `markdown` - Markdown to HTML conversion
- `click` - CLI framework
- `rich` - Rich console output (optional)

## Testing Philosophy

This Python version focuses on:
- **Small datasets** - Test with 2-3 files only
- **Step-by-step validation** - Ensure each component works
- **Simple testing** - Basic validation before complex features
- **Unit testing approach** - Test parser, client, and mapper separately

Perfect for validating the approach before scaling to 1000+ files!
