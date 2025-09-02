# Markdown to WordPress Migration Tool

A powerful Node.js CLI tool for migrating markdown content with YAML front matter to WordPress via the REST API. Designed to handle large-scale migrations (1000+ posts) with support for multiple content types, media uploads, taxonomies, and idempotent operations.

## Features

- **Multiple Content Types**: Support for blog posts, podcasts, events, and pages
- **Idempotent Operations**: Safe re-runs without duplicating content
- **Media Handling**: Automatic upload and linking of images to WordPress Media Library
- **Taxonomy Management**: Automatic creation and assignment of tags, categories, and custom taxonomies
- **Wiki Link Resolution**: Converts `[[wiki-style]]` links to proper URLs
- **Validation**: Schema-based validation before migration
- **Dry Run Mode**: Test migrations without making changes
- **Progress Tracking**: Real-time progress updates and detailed logging
- **Resumable**: Migration ledger tracks processed files for resumability

## Installation

```bash
# Clone the repository
git clone https://github.com/life-itself/markdown-to-wordpress.git
cd markdown-to-wordpress

# Install dependencies
npm install

# Build the project
npm run build

# Optional: Link globally for CLI access
npm link
```

## Quick Start

1. **Set up configuration files:**

```bash
# Copy example configs
cp config/config.example.yml config/config.yml
cp config/mappings.example.yml config/mappings.yml
cp .env.example .env
```

2. **Configure WordPress authentication:**

Edit `.env` and add your WordPress application password:

```env
WP_APP_PASSWORD=your-application-password-here
```

3. **Update config.yml with your WordPress site details:**

```yaml
wordpress:
  base_url: https://your-wordpress-site.com
  auth:
    username: your-username
```

4. **Run migration:**

```bash
# Dry run first to test
npm run migrate -- migrate -c config/config.yml -i ./content --dry-run

# Actual migration
npm run migrate -- migrate -c config/config.yml -i ./content
```

## Usage

### Commands

#### Migrate

Migrate markdown files to WordPress:

```bash
markdown-to-wordpress migrate -c config.yml -i ./content [options]

Options:
  -t, --type <type>        Content type (blog|podcast|event|page|auto)
  --dry-run                Simulate without making changes
  --concurrency <number>   Number of concurrent operations (default: 4)
  --limit <number>         Limit number of files to process
  --since <date>           Only process files since date (YYYY-MM-DD)
  --media-mode <mode>      Media handling (upload|skip)
  -v, --verbose            Show detailed output
```

#### Validate

Validate markdown files against schemas:

```bash
markdown-to-wordpress validate -c config.yml -i ./content [options]

Options:
  -t, --type <type>    Content type to validate
  -v, --verbose        Show detailed validation errors
```

#### Inspect

Inspect a single file and show how it will be mapped:

```bash
markdown-to-wordpress inspect -f ./content/post.md -c config.yml [options]

Options:
  -v, --verbose    Show detailed output
```

## Front Matter Format

### Blog/News Post

```yaml
---
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
---
```

### Event

```yaml
---
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
---
```

### Podcast

```yaml
---
type: podcast
title: "Episode Title"
slug: "podcast-ep-01"
episode_number: 1
audio_url: "https://..."
duration: "00:48:22"
guests: ["Guest Name"]
show: "Podcast Series Name"
---
```

### Page

```yaml
---
type: page
title: "Page Title"
slug: "page-slug"
template: "custom-template"
parent_slug: "parent-page"
description: "Page description"
---
```

## Configuration

### config.yml

Main configuration file for WordPress connection and migration settings.

### mappings.yml

Defines how front matter fields map to WordPress fields and taxonomies.

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## Project Structure

```
markdown-to-wordpress/
├── src/
│   ├── cli/           # CLI commands
│   ├── core/          # Core logic (parser, mapper, migrator)
│   ├── wordpress/     # WordPress API client and media handler
│   ├── utils/         # Utilities (logger, config loader)
│   └── types/         # TypeScript type definitions
├── config/            # Configuration files
├── schemas/           # JSON schemas for validation
└── tests/             # Test files
```

## Requirements

- Node.js 18+ (LTS recommended)
- WordPress 5.0+ with REST API enabled
- WordPress Application Passwords or JWT authentication

## Troubleshooting

### Authentication Issues

- Ensure Application Passwords are enabled in WordPress
- Check username and password in config
- Verify REST API is accessible at `/wp-json/wp/v2/`

### Media Upload Failures

- Check file size limits in WordPress
- Verify write permissions on WordPress media directory
- Ensure image paths are correct in markdown files

### Custom Post Types Not Found

- Verify custom post types are registered with REST API support
- Check endpoint URLs in config.yml

## License

ISC

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## Support

For issues and questions, please open an issue on GitHub.
