#  Create Node.js Script to Upload Markdown Blog Posts to WordPress via REST API

Create a nodejs script with best wordpress client library for uploading a new blog post from a markdown file. Keep this as simple as possible and use remark library for the markdown parsing. I want to support footnotes and other aspects of gfm.

I also want you to create a sample .env file that you read from for the key variables to access the wordpress instance. also output a minimal documentation into bottom of README.md file on how to use this. The script should be outputted into markdown-to-wordpress subdirectory

Summary: Create a minimal Node.js script that takes a Markdown file or files with front matter, converts it into a structure suitable for WordPress, and uploads it via the WordPress REST API. This should not be a command-line tool; just a Node script executed directly with `node`. Keep the design simple.

## Acceptance

Given a Markdown file(s) or directories of files successfully create or update posts in wordpress with:

* Correct title, slug, status, date, content.
* Featured image properly uploaded and linked.
* Team mapping correctly filled based on front matter authors.
* Running the tool twice on the same file is idempotent (no duplicate posts).

## Notes

For each Markdown file:

1. Parse front matter and content.
2. Determine target post:
   * If a `slug` exists and a post with that slug already exists, update that post; otherwise create a new post.
3. Handle media:
   * If `featured_image` is given and is a local file, upload it to `/wp/v2/media` using multipart/form-data and get back its ID. ([WordPress Developer Resources][1])
   * Use that ID as `featured_media` on the post.
   * (Optional later: scan Markdown body for local image references, upload each, and rewrite the Markdown/HTML accordingly.)
4. Handle authors / team mapping:
   * Look up each front-matter author key in `team_mapping`.
   * Write the corresponding team IDs into a custom field on the post (e.g. `team_members`), assuming that field is registered with `show_in_rest` or handled by Pods’ REST integration. ([WordPress Development Stack Exchange][8])
5. Handle content:
   * Put rendered HTML (Markdown → HTML) into the WordPress `content` field.
   * Store original Markdown in post meta (`raw_markdown`).
6. Handle other metadata:
   * Map front-matter tags/categories to WordPress taxonomies; create terms on demand if they don’t exist.
   * Set `status` based on config or front-matter override.
   * Set `date` if provided; otherwise use “now”.
7. Idempotency / safety:
   * Dry-run mode that prints what would be done without actually calling the API.
   * Support `--update-only` and `--create-only` modes (optional).
8. Output:
   * Print new/updated post ID, slug, and URL.
   * On error, show HTTP status, response body and the file that failed.


## Tasks

We will split this work into subtasks and try and complete each one in turn.

See substacks below for details on each one

- [x] Basic working script for one file
- [x] Basic working command line for multiple files
- [ ] Test that uploads existing files

---
---

# Subtasks


## Subtask no 1

* Convert Markdown → HTML using `remark` (including parsing frontmatter)
* Produce a clean JS object containing whatever is needed for WordPress upload
* Create a sample Markdown input file e.g. `sample-post.md`, with typical front matter fields such as `title`, `date`, `status`, `tags`.
* Provide a basic Node script (e.g., `uploadPost.js`) that:
  * loads `.env`
  * reads a hardcoded Markdown file path for now
  * runs conversion → upload
  * logs the result
* Provide a `.env.sample` file with required WordPress credentials.
  ```
  WP_BASE_URL="https://example.com"
  WP_USERNAME="your_username"
  WP_APP_PASSWORD="your_app_password"
  ```
* Provide a minimal `package.json` containing only necessary dependencies.
* Extend the existing README with a section describing setup and usage.
* Include **tests only for the Markdown → WordPress-ready structure** (no tests for the API upload step).
* Extend the README with relevant informaion:
  * how to configure `.env`
  * how to structure the Markdown file
  * how to run the script using Node
  * how to run the tests

Suggestions

* Run as simple node script (no need for CLI as yet)
  * Use `remark` for Markdown parsing and conversion.
* Upload to WordPress using its REST API with credentials from environment variables.
* Keep implementation minimal and avoid abstraction unless necessary.
* Use this client library for wordpress https://github.com/WP-API/node-wpapi

---

## Subtask no 2

So I want to update the upload.js and make it into a command line script where I can pass it a file or a directory or a combination of files and directories and it will then upload those.

It will log to the terminal the urls of the resulting uploaded files on the WordPress site.

---

## Substack no 3: Unit Test for URL Upload and Verification

> Raw: I want to add a unit test in a separate unit test file that takes the urls in filestotest.js and locate them in the next.lifeitself.org subdirectory and uploads them to the website with the same urls on the new website as as given by their paths on disk. I then want a check they are uploaded e.g. there is an html 200 code.

Implement a new **unit test file** that:

- reads target URLs from the *existing* `filestotest.js`
- locates the corresponding content within the existing subdirectory `next.lifeitself.org` subdirectory
- uploads this contet. use the on-disk path structure to determine the final target URL on the new website.
- verifies successful accessibility on the new website by asserting e.g. an **HTTP 200 (OK)** status code.

For now do **NOT** modify the existing upload code we have - just use it (we know there are things mising setting the url, or idempotency - we will come to that in next task).

### Acceptance Criteria

- [ ] A dedicated, separate unit test file must be created.
- [ ] The test must successfully read and process the list of URLs defined in `filestotest.js`.
- [ ] The test must locate the source files by mapping the URLs to files within the **`next.lifeitself.org` subdirectory**.
- [ ] The content must be uploaded to the new website, with the final URL path directly corresponding to the source file's relative path on disk.
- [ ] Some tests for this should be create e.g. check url exists in some way.

### Implementation Notes

* 🚩 Please use the filestotest.js that is already in the directory (and don't modify it).
* don't touch the next.lifeitself.org directory (which is alreeady there). Just use the files that are in there.
* **File I/O:** Need functionality to load the target URL list from the specified `.js` file.
* **Path Mapping:** Logic must be implemented to translate the target URL into a relative file path within the `next.lifeitself.org` subdirectory for sourcing, and use that relative path to construct the final upload URL.
