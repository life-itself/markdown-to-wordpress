# Markdown to WordPress Migration Tool - Development Guide

# CURRENT STATUS (2025-01-09):
**IMPLEMENTED & WORKING:**
✅ **Step 0: Image Processing** - SEO-friendly image renaming based on usage context
✅ **Step 1: Prepare Content** - Markdown to WordPress-ready JSON conversion  
✅ **Step 3: Upload Media** - WordPress REST API media upload with deduplication
✅ **Testing Infrastructure** - Dynamic tests using real lifeitself.org sample data
✅ **Configuration** - Working WordPress.com OAuth connection to flowerdemo4.wordpress.com
✅ **Sample Data** - Real content from lifeitself.org repository integrated

**ARCHITECTURE DECISION:**
Following ETL pipeline approach from DESIGN.md with **Python implementation** instead of Node.js
- Each step is isolated with clear inputs/outputs
- Modular structure: `/etl/0-image-processing/`, `/etl/1-prepare-content/`, etc.
- Each module has `main.py` + `main_test.py` for clean testing
- Uses real sample data from lifeitself.org content repository

# TLDR:
1. Clear project overview with the migration goal and context
2. **UPDATED**: Python-based ETL pipeline (not Node.js) following DESIGN.md principles
3. Complete content type specifications for blogs, events, podcasts, and pages
4. **IMPLEMENTED**: Working image processing and media upload to WordPress
5. Configuration file templates and working .env setup
6. **IMPLEMENTED**: Dynamic testing with real sample data
7. Special considerations for image processing, wiki-style links, and author handling
8. **UPDATED**: Python project structure with modular ETL steps
9. Success criteria to measure project completion

This tool is being developed as a production-ready **Python ETL pipeline** that can handle the complexity of migrating ~1,000 posts from markdown to WordPress while maintaining data integrity and supporting resumable, idempotent operations.

## Project Overview

You are building a **Python ETL pipeline** that migrates markdown content with YAML front matter from a GitHub repository (https://github.com/life-itself/lifeitself.org) to WordPress via the REST API. The existing site has ~1,000 posts published with Flowershow that need to be migrated to WordPress while preserving content integrity, relationships, and media.

**Current Implementation Status:**
- **WordPress Site**: flowerdemo4.wordpress.com (WordPress.com hosted)  
- **Authentication**: OAuth token configured in `.env`
- **Sample Data**: Real content from lifeitself.org repository in `/sample-data/`
- **Testing**: All modules use dynamic testing with real sample data (no hardcoded filenames)

## Core Requirements

### Primary Goal

Create a reliable, idempotent, and resumable migration tool that:

- Converts markdown files with front matter to WordPress posts/pages
- Handles multiple content types (blog posts, podcasts, events, pages)
- Uploads and correctly links media files
- Preserves metadata, taxonomies, and relationships
- Supports safe re-runs without duplicating content

### Technology Stack (**UPDATED - Python Implementation**)

- **Runtime**: Python 3.13+ 
- **Language**: Python (with type hints)
- **API**: WordPress REST API (WordPress.com OAuth)
- **Authentication**: OAuth Bearer Token (configured in .env)
- **Markdown Parser**: `markdown` library with extensions
- **HTTP Client**: `requests` library
- **Configuration**: `.env` files + JSON output files
- **Testing**: `pytest` with dynamic sample data
- **Dependencies**: `pyyaml`, `python-dotenv`, `requests`, `markdown`

## **IMPLEMENTED ETL PIPELINE STEPS**

### Step 0: Image Processing ✅ **COMPLETE**
**Location**: `/etl/0-image-processing/`
**Purpose**: Analyze image usage and generate SEO-friendly rename mappings
**Files**: `main.py`, `main_test.py`

**What it does:**
- Scans all markdown files to find image references (frontmatter + inline)
- Analyzes image usage patterns (single-use vs multi-use)
- Generates SEO-friendly filenames based on post context
- Creates `image_rename_dict.json` mapping old paths to new names
- Example: `eco-communities-blog.jpg` → `10-eco-communities-to-visit-in-europe-feature.jpg`

**Input**: Sample data from lifeitself.org repository  
**Output**: `image_rename_dict.json`, `image_usage_report.json`, `orphaned_images.json`

### Step 1: Prepare Content ✅ **COMPLETE**
**Location**: `/etl/1-prepare-content/`  
**Purpose**: Convert markdown files to WordPress-ready JSON format
**Files**: `main.py`, `main_test.py`

**What it does:**
- Extracts YAML frontmatter and markdown content
- Converts markdown to HTML using `markdown` library
- Processes wiki-style links `[[]]`
- Updates image references using rename dictionary
- Generates proper slugs, handles dates, taxonomies
- Creates WordPress-compatible data structure

**Input**: Sample data + rename dictionary from Step 0  
**Output**: `prepared_content.json` with all posts ready for WordPress

### Step 3: Upload Media ✅ **COMPLETE** 
**Location**: `/etl/3-upload-media/`
**Purpose**: Upload images to WordPress Media Library
**Files**: `main.py`, `main_test.py`

**What it does:**
- Uses WordPress.com REST API with OAuth authentication
- Uploads images with SEO-friendly names from rename dictionary  
- Handles deduplication (checks if media already exists)
- Implements rate limiting and error handling
- Creates mapping of local paths to WordPress media IDs/URLs

**Input**: Sample data + rename dictionary from Step 0
**Output**: `media_upload_map.json` with WordPress media IDs and URLs
**Live Result**: Successfully uploaded to flowerdemo4.wordpress.com (media ID 13)

### **REMAINING STEPS TO IMPLEMENT:**

### Step 2: Decide Mappings (TODO)
- Map content types to WordPress post types
- Configure taxonomy mappings
- Set up field mappings

### Step 4: Rewrite Links (TODO)  
- Update image URLs in content using media upload map
- Fix internal wiki-style links
- Update relative paths to absolute WordPress URLs

### Step 5: Create Content (TODO)
- Create WordPress posts/pages using prepared content
- Set featured images using media IDs
- Assign taxonomies and meta fields
- Handle idempotent updates (don't duplicate)

### Step 6: Verify (TODO)
- Check all content migrated correctly
- Validate image display and link functionality
- Generate migration report

## **CURRENT PROJECT STRUCTURE**

```
markdown-to-wordpress/
├── etl/
│   ├── 0-image-processing/
│   │   ├── main.py                    ✅ Image processing & renaming
│   │   ├── main_test.py               ✅ Dynamic tests
│   │   └── test-output/               ✅ Generated rename dictionaries
│   ├── 1-prepare-content/
│   │   ├── main.py                    ✅ Markdown → WordPress JSON  
│   │   ├── main_test.py               ✅ Content preparation tests
│   │   └── output/                    ✅ prepared_content.json
│   ├── 3-upload-media/
│   │   ├── main.py                    ✅ WordPress media upload
│   │   ├── main_test.py               ✅ Upload tests (mocked)
│   │   └── output/                    ✅ media_upload_map.json
│   └── run_pipeline.py                📝 Pipeline orchestration
├── sample-data/                       ✅ Real lifeitself.org content
│   ├── blog/                          ✅ Sample markdown files
│   └── assets/images/                 ✅ Sample image files  
├── .env                               ✅ WordPress.com OAuth config
├── .env.example                       ✅ Configuration template
└── CLAUDE.md                          ✅ This development guide
```

## **TESTING APPROACH** 

**Dynamic Testing Philosophy**: All tests use real sample data and avoid hardcoded assumptions
- Tests work with any markdown/image files in `sample-data/`
- No hardcoded filenames, image counts, or specific content expectations  
- Tests validate patterns and data structures, not specific values
- Easy to add new sample data without breaking tests

**Test Files**: Each ETL step has `main_test.py` with comprehensive test coverage
- Step 0: 4 tests covering image discovery, usage analysis, renaming
- Step 1: 6 tests covering markdown parsing, HTML conversion, WordPress formatting
- Step 3: 6 tests covering connection, upload, deduplication (with mocking)

**Sample Data Integration**: Uses real content from lifeitself.org repository
- Blog posts: `10-eco-communities-to-visit-in-europe.md`, `governance-at-life-itself-v2.md`, `possibility-now.md`
- Images: `eco-communities-blog.jpg`, `sample-image.jpg`
- Structure matches actual lifeitself.org content organization

## **CONFIGURATION & CREDENTIALS**

**WordPress Connection**: Currently configured for WordPress.com hosted site
```bash
# .env file configuration (WORKING)
WORDPRESS_SITE_DOMAIN=flowerdemo4.wordpress.com
WORDPRESS_OAUTH_TOKEN=[OAuth token from WordPress.com]
DEFAULT_AUTHOR=admin
DEFAULT_STATUS=draft
UPLOAD_MEDIA=true
BATCH_SIZE=10
RETRY_DELAY=1000
```

**Authentication Method**: WordPress.com OAuth Bearer Token
- More secure than username/password
- Works with WordPress.com hosted sites  
- Token configured in `.env` file
- Successfully tested with media upload (media ID 13 created)

**Usage Examples**:
```bash
# Step 0: Process images and create rename dictionary
cd etl/0-image-processing
python main.py --input-dir ../../sample-data --output-dir ./test-output

# Step 1: Prepare content for WordPress  
cd etl/1-prepare-content  
python main.py --input-dir ../../sample-data --output-dir ./output --rename-dict ../0-image-processing/test-output/image_rename_dict.json

# Step 3: Upload media to WordPress
cd etl/3-upload-media
python main.py --input-dir ../../sample-data --output-dir ./output --rename-dict ../0-image-processing/test-output/image_rename_dict.json

# Run tests
python -m pytest main_test.py -v
```

## **NEXT STEPS FOR DEVELOPMENT**

1. **Implement Step 2: Decide Mappings** - Content type and taxonomy mapping
2. **Implement Step 4: Rewrite Links** - Update image URLs using media upload map  
3. **Implement Step 5: Create Content** - WordPress post/page creation with idempotency
4. **Implement Step 6: Verify** - Migration validation and reporting
5. **Create Pipeline Orchestrator** - Chain all steps together with error handling
6. **Scale Testing** - Test with larger sample datasets
7. **Production Migration** - Run full lifeitself.org content migration

## Implementation Phases

1. **CLI Setup**

   - Command structure: `migrate`, `validate`, `inspect`
   - Configuration loading (config.yml, mappings.yml)
   - Environment variable support for credentials
   - Logging system (structured JSON + console output)

2. **File Discovery & Parsing**
   - Recursive markdown file discovery
   - Front matter extraction (YAML)
   - Content type detection (by path or front matter `type` field)
   - Validation against JSON schemas

### Phase 2: Content Processing Pipeline

1. **Field Mapping Engine**

   ```javascript
   // Example mapping structure
   {
     "post": {
       "wpType": "post",
       "fields": {
         "title": "title",
         "excerpt": "subtitle",
         "date": "date_published",
         "modified": "date_updated",
         "slug": "slug",
         "content": "BODY", // Special token for markdown body
         "featured_media": "featured_image"
       },
       "taxonomies": {
         "post_tag": "tags",
         "category": "categories",
         "initiative": "initiatives"
       },
       "meta": {
         "featured": "featured",
         "_external_id": "slug"
       }
     }
   }
   ```

2. **Markdown to HTML Conversion**

   - GitHub-flavored markdown support
   - Preserve heading hierarchy
   - Handle wiki-style links `[[]]`
   - Convert relative image paths to absolute URLs

3. **Media Handling**
   - Extract featured images and inline images
   - Upload to WordPress Media Library
   - Deduplicate by filename or content hash
   - Update image references in content
   - Generate appropriate alt text from filenames

### Phase 3: WordPress Integration

1. **API Client**

   - Rate limiting and retry logic
   - Batch operations support
   - Error handling with detailed logging
   - Progress tracking and resumability

2. **Idempotent Operations**

   - Lookup existing content by:
     1. `_external_id` meta field
     2. `slug` match within post type
     3. Title match (with warning)
   - Update only changed fields
   - Maintain migration ledger (source → WP post ID mapping)

3. **Content Creation/Update**
   ```javascript
   // Upsert logic pseudocode
   async function upsertContent(item) {
     const existing = await findExisting(item.slug, item.type);
     if (existing) {
       return updatePost(existing.id, item, updateMask);
     } else {
       return createPost(item);
     }
   }
   ```

## Content Type Specifications

### Blog/News Posts

```yaml
type: blog
title: "Article Title"
subtitle: "Brief description"
slug: "article-slug"
date_published: 2024-05-01T10:00:00Z
date_updated: 2024-06-10T18:30:00Z
featured_image: ./images/feature.jpg
authors: ["Author Name", "author@email.com"]
status: publish
featured: true
tags: [tag1, tag2]
categories: [category1]
initiatives: [initiative1]
```

### Events/Residencies

```yaml
type: event
title: "Event Name"
slug: "event-slug"
start_date: 2025-10-01
end_date: 2025-10-15
location_name: "Venue Name"
location_address: "Full Address"
host: ["Host Organization"]
featured_image: ./images/event.jpg
registration_url: "https://..."
```

### Podcasts

```yaml
type: podcast
title: "Episode Title"
slug: "podcast-ep-01"
episode_number: 1
audio_url: "https://..."
duration: "00:48:22"
guests: ["Guest Name"]
show: "Podcast Series Name"
```

### Pages

```yaml
type: page
title: "Page Title"
slug: "page-slug"
template: "custom-template"
parent_slug: "parent-page"
description: "Page description"
```

## CLI Commands

### Main Migration Command

```bash
node migrate.js migrate \
  --config ./config.yml \
  --input ./content \
  --type blog|podcast|event|page|auto \
  --dry-run \
  --concurrency 4 \
  --limit 100 \
  --since 2025-01-01 \
  --media-mode upload|skip
```

### Validation Command

```bash
node migrate.js validate \
  --input ./content \
  --type blog
```

### Inspection Command

```bash
node migrate.js inspect \
  --file ./content/posts/example.md \
  --verbose
```

## Configuration Files

### config.yml

```yaml
wordpress:
  base_url: https://example.com
  auth:
    method: application_passwords
    username: admin
    application_password: ${WP_APP_PASSWORD}
  endpoints:
    posts: /wp-json/wp/v2/posts
    pages: /wp-json/wp/v2/pages
    media: /wp-json/wp/v2/media
    podcast: /wp-json/wp/v2/podcast
    event: /wp-json/wp/v2/event

defaults:
  status: draft
  timezone: Europe/London
  author_fallback: migration-bot
  media:
    upload: true
    dedupe_by: filename
    max_size_mb: 10

migration:
  concurrency: 4
  retry_attempts: 3
  retry_delay_ms: 1000
  rate_limit_ms: 100
```

### mappings.yml

```yaml
post_types:
  blog:
    endpoint: /wp-json/wp/v2/posts
    required_fields: [title, slug]
    meta_prefix: _li_
  podcast:
    endpoint: /wp-json/wp/v2/podcast
    required_fields: [title, episode_number, audio_url]
  event:
    endpoint: /wp-json/wp/v2/event
    required_fields: [title, start_date]
  page:
    endpoint: /wp-json/wp/v2/pages
    required_fields: [title, slug]

taxonomies:
  tag: post_tag
  category: category
  initiatives: initiatives

relationships:
  initiatives:
    mode: taxonomy # or 'relation' for ACF relationships
```

## Key Implementation Details

### Error Handling

- Validate all inputs before processing
- Implement circuit breaker pattern for API failures
- Log all errors with context (file path, line number, field)
- Continue processing other files on individual failures
- Generate error report at end of migration

### Performance Optimization

- Process files in batches with configurable concurrency
- Implement request pooling for API calls
- Cache taxonomy and author lookups
- Use streaming for large file processing
- Implement progress bars for long operations

### Logging & Reporting

```javascript
// Log entry structure
{
  timestamp: "2025-01-15T10:30:00Z",
  level: "info|warn|error",
  action: "create|update|skip|error",
  source: "content/posts/example.md",
  target: {
    type: "post",
    id: 123,
    slug: "example-post"
  },
  details: {},
  duration_ms: 250
}
```

### Testing Strategy

1. **Unit Tests**: Field mapping, markdown conversion, validation
2. **Integration Tests**: API client with mock server
3. **E2E Tests**: Full pipeline with test WordPress instance
4. **Dry Run Mode**: Generate all payloads without writing

## Special Considerations

### Image Processing

1. **Renaming Strategy**

   - Generate SEO-friendly names from post title + sequence
   - Preserve original as meta field
   - Example: `article-title-feature.jpg`, `article-title-01.jpg`

2. **Upload Optimization**
   - Check if image already exists (by hash or filename)
   - Resize large images before upload (optional)
   - Generate WordPress-compatible metadata

### Wiki-Style Links

- Pattern: `[[Page Name]]` or `[[page-slug|Display Text]]`
- Resolution:
  1. Look up target by slug in migration ledger
  2. Fall back to WordPress search
  3. Convert to proper WordPress URL
  4. Log unresolved links for manual review

### Author Handling

```javascript
async function resolveAuthor(authorRef) {
  // Try email first
  if (isEmail(authorRef)) {
    return await findUserByEmail(authorRef);
  }
  // Try display name
  const user = await findUserByDisplayName(authorRef);
  if (user) return user;
  // Create if allowed
  if (config.allow_create_authors) {
    return await createUser(authorRef);
  }
  // Use fallback
  return config.author_fallback;
}
```

### Taxonomy Management

- Ensure all terms exist before assignment
- Create missing terms with proper hierarchy
- Map flat tags to hierarchical categories where needed
- Support both built-in and custom taxonomies

## Development Workflow

### Project Structure

```
markdown-to-wordpress/
├── src/
│   ├── cli/
│   │   ├── commands/
│   │   └── index.js
│   ├── core/
│   │   ├── parser.js
│   │   ├── mapper.js
│   │   └── validator.js
│   ├── wordpress/
│   │   ├── client.js
│   │   ├── media.js
│   │   └── taxonomies.js
│   ├── utils/
│   │   ├── logger.js
│   │   └── helpers.js
│   └── types/
│       └── index.d.ts
├── config/
│   ├── config.yml
│   └── mappings.yml
├── schemas/
│   ├── blog.schema.json
│   ├── event.schema.json
│   └── podcast.schema.json
├── tests/
├── package.json
└── README.md
```

### Dependencies

```json
{
  "dependencies": {
    "commander": "^12.0.0",
    "axios": "^1.6.0",
    "markdown-it": "^14.0.0",
    "gray-matter": "^4.0.3",
    "js-yaml": "^4.1.0",
    "ajv": "^8.12.0",
    "p-limit": "^5.0.0",
    "chalk": "^5.3.0",
    "ora": "^8.0.1",
    "winston": "^3.11.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0"
  }
}
```

## Success Criteria

1. **Reliability**

   - Zero data loss during migration
   - Graceful handling of all error cases
   - Complete audit trail of all operations

2. **Performance**

   - Process 1000 posts in under 30 minutes
   - Efficient media upload with deduplication
   - Minimal memory footprint

3. **Maintainability**

   - Clear, documented code structure
   - Comprehensive test coverage
   - Easy configuration updates

4. **Usability**
   - Intuitive CLI interface
   - Helpful error messages
   - Progress indication for long operations
   - Dry-run mode for testing

## Next Steps for Implementation

1. **Start with Phase 1**: Set up project structure, CLI framework, and configuration loading
2. **Implement core parser**: Front matter extraction and markdown parsing
3. **Build WordPress client**: Authentication and basic CRUD operations
4. **Add media handling**: Upload and URL replacement
5. **Implement idempotency**: Lookup and update logic
6. **Add content types**: One at a time (blog → event → podcast → page)
7. **Testing & validation**: Unit tests, integration tests, dry runs
8. **Documentation**: User guide, API docs, troubleshooting guide

## Important Notes

- Always validate WordPress endpoint availability before bulk operations
- Implement graceful shutdown handling (SIGINT/SIGTERM)
- Consider WordPress rate limits and implement appropriate throttling
- Store sensitive credentials in environment variables only
- Maintain backward compatibility with configuration changes
- Document all mapping decisions and edge cases
- Create rollback strategy for failed migrations

This tool should be production-ready, well-tested, and capable of handling the full complexity of the Life Itself website migration while being reusable for similar projects.
