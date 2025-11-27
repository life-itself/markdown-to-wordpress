## Meta-prompt

We're going to create description of an issue / prompt. Act like a world class product owner and spec provider. At the same time don't get *too* detailed. Keep it simple and concise and focus on what the needs are the key requirements/constraints around that. Remember KISS: we want to keep it simple and straightforward and not over-engineer it.

## Future Task Description Guidance

To receive task descriptions in the requested format, use these instructions:

1.  **Structure:** Always include these three sections:
    * **Title**: a descriptive title that captures the essence of the issue or prompt.
    * **Description**: this section does not need a a heading and should be the first paragraph or paragraphs in the response
    * **Acceptance Criteria**: in a section with h2 heading `Acceptance`
    * **Notes**: any notes on implementation details or considerations derived from the user's request. (please don't add. i will ask if i want suggestions.)
2.  **Content:**
    * Keep all sections **clear and concise**.
    * **Do not** generate full code, detailed specifications, or extensive commentary on *how* to implement the task. (unless i provided it myself)
    
## FUTURE

## Acceptance

# 4. End-state behaviour (acceptance criteria)

Here is a concrete “finished version” spec you can hand to an AI when you want the full tool implemented.

Inputs

* A site config file (e.g. `config.json`):

  * `wp_base_url`
  * `username`
  * `application_password` (or other auth token) ([Robin Geuens][9])
  * `default_status` (`draft` / `publish`)
  * `team_mapping`: map from front-matter author keys to WordPress “team” post IDs (Pods CPT).
  * `asset_dir`: local directory where images referenced in Markdown live.
* One or more Markdown files:

  * YAML front matter with at least: `title`, `slug` (optional), `date` (optional), `authors` (could be string or list), `excerpt` (optional), `featured_image` (relative path into `asset_dir`), plus any tags/categories.
  * Body content in Markdown.

Core behaviour


---

# 5. Iteration plan

You suggested starting from “just get a post up”; I’d do exactly that.

Iteration 0 – WordPress prep

This is not in code, but is crucial:

* Enable REST API (default in modern WP) and pretty permalinks. ([WordPress Developer Resources][1])
* Set up Application Password for your `admin` user. ([Robin Geuens][9])
* Ensure:

  * Custom fields you need (e.g. `raw_markdown`, `team_members`) are registered with `show_in_rest => true`, or Pods exposes them via REST. ([WordPress Development Stack Exchange][8])
  * Your Pods CPT “team” is accessible via REST (Pods has REST support; otherwise you can expose via `register_post_type(... show_in_rest => true)`).

Iteration 1 – Minimal “upload a post” script

Scope:

* One language (say Node).
* One file in, one post out.
* Ignore authors, images, custom fields.

Spec for AI:

* Read Markdown file path from CLI arguments.
* Parse YAML front matter and content.
* Call `POST /wp/v2/posts` with JSON body:

  * `title`, `content` (either Markdown directly or rendered HTML, your choice for the MVP), `status`, `slug`. ([WordPress Developer Resources][1])
* Authenticate using HTTP Basic auth with username + Application Password.
* Print the ID and link of the created post.

Iteration 2 – Featured image

Add:

* Read `featured_image` from front matter.
* If present:

  * Upload to `/wp/v2/media` with appropriate headers (`Content-Disposition` filename, `Content-Type`) and file contents. ([Misha Rudrastyh][10])
  * Use returned media ID as `featured_media` when creating/updating the post.
* Handle “already uploaded” heuristics later (e.g. by comparing filename/slug, or storing a mapping cache locally).

Iteration 3 – Authors → team mapping

Add:

* `team_mapping` config (key → team post ID).
* On post creation/update:

  * Convert front-matter `authors` keys to numeric IDs via the mapping.
  * Send those IDs as an array in a custom field (`meta.team_members` or Pods field), assuming that field is registered as REST-exposed. ([WordPress Development Stack Exchange][8])

Iteration 4 – Markdown preservation and richer image handling

Add:

* Store original Markdown as meta `raw_markdown`.
* Render Markdown to HTML for `content`.
* Optionally:

  * Parse Markdown for image references (`![alt](./assets/foo.jpg)`), upload each asset, rewrite the HTML to use `/wp-content/uploads/...`.

Iteration 5 – Batch mode, dry-run, and nice CLI ergonomics

Add:

* Directory mode (publish all `*.md` in a folder).
* `--dry-run` and `--update-only` flags.
* Status summary at the end.

---

# 6. Reusable AI prompt template (Node version)

Here is a skeleton prompt you can paste next time you ask an AI to generate the code (adjust details as needed):

> I want you to generate a Node.js CLI script that publishes Markdown blog posts to a self-hosted WordPress site via the REST API. Use modern JavaScript (ES modules) and either the `node-wpapi` library or the native `fetch` API on Node 20+. The script will be run from the command line.
>
> Requirements:
>
> 1. Inputs
>
>    * The script is invoked as `node publish.js path/to/post.md`.
>    * There is a `config.json` file in the same directory with:
>
>      * `wp_base_url`, `username`, `application_password`, `default_status`, `team_mapping` (object), `asset_dir`.
> 2. Markdown parsing
>
>    * Use a library like `gray-matter` to split YAML front matter and Markdown body.
>    * Required front-matter keys: `title`. Optional: `slug`, `status`, `date`, `authors` (string or array), `excerpt`, `featured_image`.
> 3. MVP behaviour (for the first version)
>
>    * Authenticate to WordPress using Basic auth with username + Application Password.
>    * Call `POST /wp/v2/posts` on the configured site with JSON `{ title, content, status, slug }`, where:
>
>      * `title` comes from front matter.
>      * `content` is the raw Markdown body (for now).
>      * `status` defaults to `config.default_status` but can be overridden by front matter.
>      * `slug` comes from front matter if present; otherwise generate one from the filename.
>    * Print the created post ID and link to stdout.
> 4. Code quality
>
>    * Structure the code cleanly: separate functions for reading config, parsing Markdown, and calling the WordPress API.
>    * Include basic error handling: if the HTTP response is not 2xx, print status code and response body and exit with non-zero code.
>    * Add a short `README` comment at the top explaining usage and dependencies.
>
> Please output:
>
> 1. A short description of the approach.
> 2. The full `package.json` and `publish.js` source code.
> 3. Exact shell commands to install dependencies and run the script.

You can then extend this same prompt later with the Iteration 2–4 requirements (featured image upload, team mapping, Markdown meta, etc.) as you go.

[1]: https://developer.wordpress.org/rest-api/reference/posts/?utm_source=chatgpt.com "Posts – REST API Handbook - WordPress Developer Resources"
[2]: https://developer.wordpress.org/rest-api/using-the-rest-api/backbone-javascript-client/?utm_source=chatgpt.com "Backbone JavaScript Client – REST API Handbook"
[3]: https://wp-api.org/node-wpapi/?utm_source=chatgpt.com "A JavaScript Client for the WordPress REST API"
[4]: https://github.com/d3v-null/wp-api-python?utm_source=chatgpt.com "d3v-null/wp-api-python"
[5]: https://wp-api-client.readthedocs.io/?utm_source=chatgpt.com "WordPress REST API Python Client - Read the Docs"
[6]: https://wordpress.org/support/topic/markdown-support-4/?utm_source=chatgpt.com "Markdown support?"
[7]: https://jetpack.com/support/jetpack-blocks/markdown/?utm_source=chatgpt.com "Markdown Block"
[8]: https://wordpress.stackexchange.com/questions/380513/add-post-meta-fields-when-creating-a-post-using-wordpress-rest-api?utm_source=chatgpt.com "Add post meta fields, when creating a post using ..."
[9]: https://robingeuens.com/blog/python-wordpress-api/?utm_source=chatgpt.com "A Practical Guide to Using the WordPress Rest API in Python"
[10]: https://rudrastyh.com/wordpress/rest-api-create-post.html?utm_source=chatgpt.com "Create a Post with WordPress REST API"
