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

1. Handle content:
   * Put rendered HTML (Markdown → HTML) into the WordPress `content` field.
   * Store original Markdown in post meta (`raw_markdown`).
2. Determine target post:
   * If a `slug` exists and a post with that slug already exists, update that post; otherwise create a new post.
   * Slug determiend by file path if no slug field or frontmatter in the post.
3. Handle media:
   * If `featured_image` is given and is a local file, upload it to `/wp/v2/media` using multipart/form-data and get back its ID. ([WordPress Developer Resources][1])
   * Use that ID as `featured_media` on the post.
   * (Optional later: scan Markdown body for local image references, upload each, and rewrite the Markdown/HTML accordingly.)
4. Handle authors / team mapping:
   * Look up each front-matter author key in `team_mapping`.
   * Write the corresponding team IDs into a custom field on the post (e.g. `team_members`), assuming that field is registered with `show_in_rest` or handled by Pods’ REST integration. ([WordPress Development Stack Exchange][8])

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
- [x] Test that uploads existing files
- [x] Use slugs and idempotency

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
  * runs conversion
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

## Substack no 4: Implement Idempotent Uploads via Slug Check

> ok, how does wordpress set paths/slugs for posts or pages? and how can i do idempotent creation so that when i upload a local file ath path x and it matches wordpress existing pages/post at x then we update rather than create. I want you to research this briefly then create a task description for doing this based on type of structure you find in @PLAN.md and then output this here. you can ask me questions as you go if there is somethign you want to check. 

**Goal:** Modify the upload script to prevent creating duplicate posts. The script should check if a post with a given slug already exists on WordPress. If it does, update it; otherwise, create a new one. The slug should be derived from the markdown filename.

### Acceptance Criteria

* [ ] The upload function will determine the slug for a markdown file from its filename (e.g., `my-post.md` becomes `my-post`).
* [ ] Before uploading, the function will query the WordPress REST API (`GET /wp/v2/posts?slug=<slug>`) to check if a post with that slug already exists.
  * [ ] **If a post exists:** The function will use the post ID from the API response to perform an **update** (`POST /wp/v2/posts/<id>`) with the new content and metadata.
  * [ ] **If no post exists:** The function will **create** a new post (`POST /wp/v2/posts`), explicitly setting the `slug` in the request body.
* [ ] The unit test file (`markdownProcessor.test.js`) will be updated to incorporate this idempotency logic, ensuring tests can be run multiple times without creating duplicate posts.

### Implementation Notes

* **Slug Derivation:** The slug should be the basename of the file, stripped of its `.md` extension.
* **API Interaction:**
    * Use the existing WordPress client library.
    * Implement a `findPostBySlug(slug)` function that performs the `GET` request.
    * Modify the main upload logic to call this function and decide whether to call the `create` or `update` function on the client.
* **Updating Posts:** When updating, ensure all relevant fields are sent, including title, content, featured image, categories, tags, etc.
* **Testing:** The tests should mock the API calls.
    * Create a test case where the mock API returns an existing post, and verify that the `update` method is called.
    * Create a test case where the mock API returns an empty array, and verify that the `create` method is called.

### How WordPress Manages Paths and Slugs

WordPress uses a "slug" to create the user-friendly URL for a post or page. For example, a post titled "My New Post" would typically have a slug of `my-new-post`. The full URL might be `https://example.com/my-new-post/` or `https://example.com/2023/11/my-new-post/`, depending on your site's permalink settings.

Slugs must be unique for each post type. If you try to create a new post with a slug that already exists, WordPress will automatically append a number to it (e.g., `my-new-post-2`) to ensure uniqueness.

### A Strategy for Idempotent Uploads

We can leverage the slug system to ensure our uploads are "idempotent"—that is, running the upload script multiple times for the same file will update the existing post rather than creating duplicates. The process is as follows:

1.  **Derive the Slug:** For each local Markdown file, derive the intended slug from its filename (e.g., `my-first-post.md` becomes `my-first-post`).
2.  **Check for Existence:** Before uploading, use the WordPress REST API to check if a post with this slug already exists. You can do this by sending a `GET` request to `/wp/v2/posts?slug=my-first-post`.
3.  **Create or Update:**
    *   If the API returns an existing post, use its ID to **update** it with the new content.
    *   If the API returns nothing, **create** a new post, making sure to set the `slug` field to your desired value in the creation request.

This approach ensures that each file corresponds to exactly one post on your WordPress site.

## Subtask no 5: store original raw file content (markdown) into wordpress

Modify uploader library to store the original markdown in `raw_markdown` field in wordpress metadata.

this means the original markdown process code should have an additional metadata key for the raw markdown and this should be be used by uploader code.

By raw markdown i mean the literal content of the file whatever it is in pure format including the frontmatter.

## Substack no 6: image uploading command line tool and script

This extends are library and adds a new command line script uploadMedia.js to handle the uploading of image files to WordPress. The script must accept a single file path or a directory path. It will utilize a local JSON file, `media-mapping.json`, to store key-value pairs of local file paths (and optionally their hash) against their final WordPress destination URLs, enabling **idempotent uploads** (skipping already processed files).

I want the media-mapping.json so it can be used in subsequent steps to rewrite links in markdown files ahead of their uploading.

To test this out you can use the content in `next.lifeitself.org` subdirectory relative to this file.

I would test out by just uploading a single file.

### Acceptance Criteria

1. **Command:** A new CLI script must be created.
2. **Input:** The script must accept arguments of either file(s) or directory(ies).all contained **image files** must be scanned and selected for upload.
3. **Idempotency & Mapping:**
    * The script must read the existing mapping data from a file named **`media-mapping.json`**.
    * This file stores pairs of `[local_file_path]` (and optionally a file hash) and the `[destination_url]`.
    * **Skip Logic:** Before uploading a file, the script must check `media-mapping.json`. If a match is found, the file must be **skipped**, and this action must be noted.
    * **Update Logic:** If the file is uploaded successfully, its local path/hash and destination URL must be added to the mapping data.
      * Store the local file path used for uploading in the wordpress metadata of the uploaded file
    * The **`media-mapping.json`** file must be rewritten/updated after all successful uploads.
4. **Logging:** The script must provide **terminal output** indicating which files were uploaded and which were skipped.

### Implementation Notes

* **File Filtering:** The script needs logic to specifically filter for common image file extensions when processing a directory.
* **Idempotency Key:** Consider using a combination of the local file path and a **file hash** (e.g., MD5 or SHA) as the key in `media-mapping.json` to ensure a file isn't re-uploaded if it has changed locally but retained the same path.
* **WordPress API:** The tool will rely on the WordPress REST API, specifically the `/wp/v2/media` endpoint, for file uploads.
  * use wordpress login info in the `.env` file. See README.md in this directory for how that works (and example of usage in `upload.js`)
* **Metadata:** To set custom metadata, you may need to utilize the `meta` fields within the API request during upload, or potentially use a custom endpoint/plugin if the standard API is too restrictive for setting arbitrary metadata fields like the local path.
* **CLI Progress:** (nice to have). show progress e.g. how many files to upload, how many uploaded so far.
