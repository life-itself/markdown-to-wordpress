# Pages command design (concise)

Goal
- Add `pages` to `upload.js` to upload Markdown pages (not posts) to WordPress.
- Recurse when requested, skip already-existing pages, reuse media rewriting/featured image/author logic, and report skips/creates/updates.

CLI UX
- Usage: `node upload.js pages [paths...]`
- Args: one or more Markdown files and/or directories; directories are not recursed unless `-r/--recurse` is provided.
- Options: `--mapping/-m` (default `mediamap.json`), `--authors/-a` (default `authors.json`), `--exclude-file/-x <path>` pointing to a file of newline-separated glob patterns (e.g., `index*`) applied after discovery, `--absolute-media-urls` (reuse existing behavior), `-r/--recurse` to walk subdirectories.

Discovery & filtering
- Walk provided paths; include only `.md`; recurse only when `-r/--recurse` is set.
- Apply excludes from the `--exclude-file` patterns file.
- Ignore front matter `slug`; derive slug from filename stem only.

Markdown → payload
- Parse front matter for title, status (default publish), authors (optional), image hints, raw markdown.
- Reuse existing parsing/rewrite logic in `src/` (markdown parsing, media rewriting, featured image selection, author mapping); pass raw markdown as meta as with posts.
- Authors: if present, map via authors file; if no match, warn and omit.
- Dates generally not needed for pages; if present pass through.

WordPress upsert
- Existence check: `GET /wp/v2/pages?slug=<slug>`; any hit means “exists”.
- Create: `POST /wp/v2/pages` with slug, title, content, status, author, featured_media, raw_markdown.
- Existing hit: skip upload and report (future: opt-in update/override).
- No nested parent creation for now; assume flat URLs (future: parent lookup).

Reporting & behavior
- Per file log: create/update/skip (already exists), slug, remote link if available.
- Errors: include file path + HTTP status/body excerpt.
- Continue on per-file errors; exit non-zero if any failed.

Future extension (optional)
- Add parent page creation for nested paths when needed.
- Add tests for pages payload and idempotency; add e2e smoke once creds available.
- Add basic unit tests for slug derivation, payload prep, exclusion handling using existing parsing helpers.

## Raw prompt

i want to create a pages command for upload.js that uploads a page or aall pages in a directory. we will skip the subfolder called blog if it exists when searching for posts to upload.

We will also skip pages that already exist on the server.

We will update `upload.js` to include a new command called `pages` that uploads a page or all pages in a directory (and sub-directories).
