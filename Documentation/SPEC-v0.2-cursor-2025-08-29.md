### Markdown → WordPress Migration Tool (Node.js) — Specification

This specification defines a Node.js CLI tool that ingests Markdown files with front matter and migrates them into WordPress via the REST API. It supports multiple data types (custom post types and pages), configurable mappings, idempotent updates, and robust media/taxonomy handling.

- **Source**: Markdown + YAML/JSON front matter (from `lifeitself.org` or similar).
- **Targets (initial)**: `blog/news` (standard post), `podcast` (CPT), `event/residency` (CPT). Optional: `page` for initiatives/learn/topic pages.
- **Outcomes**: Deterministic, idempotent, resumable migrations with clear logs, dry run, and validation.

### CLI

```
markdown-to-wordpress migrate \
  --config ./config.yml \
  --input ./content \
  --type blog|podcast|event|page|auto \
  --dry-run \
  --concurrency 4 \
  --limit 100 \
  --filter "tag:initiative-x" \
  --map ./mappings.yml
```

- **Commands**:
  - `migrate`: Execute migration.
  - `validate`: Validate inputs vs schemas only.
  - `inspect`: Print computed payloads for a single file.
- **Flags**:
  - `--type`: Force target type; `auto` detects via front matter or path.
  - `--dry-run`: Produce payloads without writes (including media).
  - `--concurrency`: Parallelism for HTTP calls.
  - `--limit`, `--since`, `--changed-only` (git-based file selection).
  - `--map`: Override/extend default field mappings.

### Configuration (config.yml)

```yaml
wordpress:
  base_url: https://example.com
  auth:
    method: application_passwords # or jwt
    username: admin
    application_password: ${WP_APP_PASSWORD}
  endpoints:
    posts: /wp-json/wp/v2/posts
    pages: /wp-json/wp/v2/pages
    media: /wp-json/wp/v2/media
    podcast: /wp-json/wp/v2/podcast
    event: /wp-json/wp/v2/event

defaults:
  timezone: Europe/London
  status: draft
  author_fallback: migration-bot

taxonomies:
  tag: tags
  category: categories
  initiatives: initiatives # optional custom taxonomy

relationships:
  initiatives:
    mode: taxonomy # or relation
    page_post_type: page # used when mode=relation
```

### Input schemas (front matter)

All types share Core fields; each type extends them. Markdown body is the main content.

- **Core**:
  - `type` (blog|news|event|podcast|page)
  - `title` (string, required)
  - `slug` (string; derived from filename if missing)
  - `description` (string; subtitle/summary)
  - `date_published` (ISO 8601)
  - `date_updated` (ISO 8601)
  - `featured_image` (path or URL)
  - `authors` (array of names or emails)
  - `status` (draft|publish|private)
  - `tags` (array of strings)
  - `categories` (array of strings)
  - `initiatives` (array of strings; taxonomy or relations)
  - `external_id` (string; stable id for idempotency)

- **Blog/News** (`type: blog` or `news`):
  - Inherits Core
  - `featured` (boolean)

- **Event/Residency** (`type: event`):
  - Inherits Core
  - `start_date` (ISO 8601, required)
  - `end_date` (ISO 8601)
  - `host` (string)
  - `location_name` (string)
  - `location_address` (string)
  - `location_lat` (number)
  - `location_lng` (number)
  - `registration_url` (string)

- **Podcast** (`type: podcast`):
  - Inherits Core
  - `episode_number` (integer)
  - `audio_url` (URL)
  - `duration` (string or number)
  - `show` (string)

- **Page** (`type: page`):
  - Inherits Core (authors optional)
  - `template` (WP page template slug)
  - `parent_slug` (string)

Example (blog):

```yaml
---
type: blog
title: The Future of X
slug: future-of-x
description: A short teaser
date_published: 2024-05-01T10:00:00Z
date_updated: 2024-06-10T18:30:00Z
featured_image: ./images/future.jpg
authors: ["Alice Example", "bob@example.org"]
status: publish
featured: true
tags: [innovation, future]
categories: [analysis]
initiatives: [Open Knowledge, Resilient Communities]
external_id: blog-000123
---
```

### Mapping to WordPress

- **Routing** by `type`:
  - blog/news → `wp/v2/posts`
  - podcast → `wp/v2/podcast`
  - event → `wp/v2/event`
  - page → `wp/v2/pages`

- **Core mapping**:
  - `title` → `title`
  - `slug` → `slug`
  - `description` → `excerpt`
  - `status` → `status`
  - `date_published` → `date` / `date_gmt`
  - `date_updated` → `modified` / `modified_gmt`
  - Markdown body → `content` (HTML via remark/unified)
  - `featured_image` → upload to media; set `featured_media`
  - `authors` → resolve/create users; set `author` (single) and/or multi-author field (ACF/co-authors)
  - `tags`/`categories`/`initiatives` → ensure terms; assign IDs
  - `external_id` → meta `_external_id`

- **Type-specific**:
  - event: `start_date`, `end_date`, `host`, `location_*`, `registration_url` → meta fields (ACF or CPT meta)
  - podcast: `episode_number`, `audio_url`, `duration`, `show` → meta; optional enclosure support
  - blog/news: `featured` → boolean meta or reserved tag
  - page: `template` → `template`, `parent_slug` → resolve parent ID → `parent`

### Taxonomies vs relationships for initiatives/topics

- **Taxonomy mode** (recommended for grouping):
  - Ensure custom taxonomy `initiatives` exists
  - Map `initiatives: ["Name"]` to that taxonomy; archive pages become available

- **Relation mode** (when canonical landing pages exist):
  - Ensure/create a `page` per initiative
  - Store relation via post meta (e.g., `_related_initiatives` array of page IDs) or ACF Relationship field
  - Front-end queries posts by related page meta

Configured via `config.yml.relationships.initiatives.mode`.

### Authors

- Resolve by email first; fallback to exact display name match
- If missing and `allow_create_authors=true`, create with default role; else use `author_fallback`
- Multi-author options: ACF repeater of user IDs, co-authors plugin, or `byline` meta + primary author

### Media

- `featured_image` may be local path or URL
- De-duplicate by content hash/filename; reuse existing media where possible
- Upload media before post creation/update to set `featured_media`
- Optional: rewrite inline Markdown images to WP media URLs

### Idempotency & updates

- Lookup sequence:
  1) `external_id` meta match
  2) `slug` match within target post type
  3) Title match (warn)
- If found: update according to `update_mask` (whitelist of fields to overwrite)
- If not found: create
- Maintain a migration ledger (JSON) mapping source path → WP post ID

### Validation

- JSON Schemas per type; enforced pre-flight
- Strict ISO date parsing and timezone normalization
- Validate taxonomy/relationship modes and required meta keys for CPTs

### Reliability

- Retries with exponential backoff for 429/5xx
- Respect pagination (e.g., `X-WP-TotalPages`) for lookups
- Circuit breaker + retry queue on repeated failures

### Logging & reporting

- Structured logs (JSON) + human console output
- Per-file: created/updated/skipped/error with reason
- Summaries per type and taxonomy creations
- Optional CSV/JSON export of results

### Directory conventions

```
content/
  blog/**/post.md
  podcast/**/episode.md
  events/**/event.md
  pages/**/page.md
images/**
config.yml
mappings.yml
```

Type auto-detection may use directory names or `type` in front matter.

### Mappings override (mappings.yml)

```yaml
post_types:
  blog:
    endpoint: /wp-json/wp/v2/posts
    meta:
      featured: _li_featured
  podcast:
    endpoint: /wp-json/wp/v2/podcast
    meta:
      episode_number: _episode_number
      audio_url: _audio_url
      duration: _duration
      show: _show
  event:
    endpoint: /wp-json/wp/v2/event
    meta:
      start_date: _start_date
      end_date: _end_date
      host: _host
      location_name: _location_name
      location_address: _location_address
      location_lat: _location_lat
      location_lng: _location_lng
      registration_url: _registration_url
  page:
    endpoint: /wp-json/wp/v2/pages

taxonomies:
  tag: post_tag
  category: category
  initiatives: initiatives

meta:
  external_id: _external_id
  related_initiatives: _related_initiatives
```

### Authentication

- Application Passwords (preferred): Basic auth `username:application_password`
- JWT (alternative): obtain token, send `Authorization: Bearer <token>`

### Operational notes

- Default concurrency: 4 (configurable)
- `--dry-run` performs no writes, including media
- `--resume` uses the migration ledger
- `--only-changed` can select files via git diff against a base ref

### Acceptance checklist (for code generation)

- CLI with `migrate`, `validate`, `inspect`
- Config + mappings loading and validation
- Per-type JSON Schemas
- Idempotent lookup by `external_id`/`slug`
- Media upload + `featured_media` assignment with dedupe
- Author resolution/creation with fallback
- Taxonomy creation/assignment (tags, categories, initiatives)
- Relationship mode for initiatives → pages via meta/ACF
- Create/update with `update_mask`
- Logging, reporting, proper exit codes

### Inputs needed to finalize

- Sample Markdown for each type (blog, podcast, event, page)
- Confirm CPT slugs and meta keys (or ACF field keys)
- Decide initiatives: taxonomy vs relation
- Author policy (create missing?)
- Target WP URL and auth method
