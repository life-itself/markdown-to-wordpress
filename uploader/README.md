## Usage

Set up the simple Node script in this repo to convert Markdown and upload to WordPress:

1. Install dependencies: `npm install`.
2. Copy `.env.sample` to `.env` and set `WP_BASE_URL`, `WP_USERNAME`, and `WP_APP_PASSWORD` (WordPress application password).
3. Create a Markdown file with YAML front matter, e.g.

   ```markdown
   ---
   title: My Post
   slug: my-post
   status: draft
   tags:
     - gardening
     - learning
   excerpt: |
     A short preview paragraph.
   ---

   Body content in GitHub-flavored Markdown with tables and footnotes.
   ```

4. Update `uploadPost.js` (or use `sample-post.md`) to point at the Markdown file you want to publish.
5. Run the uploader with `node uploadPost.js`. On success the script logs the WordPress post ID, link, and status.
6. (Optional) Run Markdown conversion tests with `npm test` to verify the Markdown processing module.
