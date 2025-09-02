# Markdown to WordPress Migration Tool - Development Guide

## Project Overview

You are building a **Node.js CLI tool** that migrates markdown content with YAML front matter from a GitHub repository (https://github.com/life-itself/lifeitself.org) to WordPress via the REST API. The existing site has ~1,000 posts published with Flowershow that need to be migrated to WordPress while preserving content integrity, relationships, and media.

## Core Requirements

### Primary Goal
Create a reliable, idempotent, and resumable migration tool that:
- Converts markdown files with front matter to WordPress posts/pages
- Handles multiple content types (blog posts, podcasts, events, pages)
- Uploads and correctly links media files
- Preserves metadata, taxonomies, and relationships
- Supports safe re-runs without duplicating content

### Technology Stack
- **Runtime**: Node.js (LTS version)
- **Language**: JavaScript/TypeScript (prefer TypeScript for type safety)
- **API**: WordPress REST API (with ACF support if needed)
- **Authentication**: WordPress Application Passwords or JWT
- **Markdown Parser**: markdown-it or remark/unified
- **CLI Framework**: Commander.js or yargs
- **HTTP Client**: axios or node-fetch
- **Configuration**: YAML/JSON files

## Implementation Phases

### Phase 1: Core Infrastructure
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