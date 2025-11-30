#  Create Node.js Script to Upload Markdown Blog Posts to WordPress via REST API

Create a nodejs script with best wordpress client library for uploading a new blog post from a markdown file. Keep this as simple as possible and use remark library for the markdown parsing. I want to support footnotes and other aspects of gfm.

I also want you to create a sample .env file that you read from for the key variables to access the wordpress instance. also output a minimal documentation into bottom of README.md file on how to use this. The script should be outputted into markdown-to-wordpress subdirectory

Summary: Create a minimal Node.js script that takes a Markdown file or files with front matter, converts it into a structure suitable for WordPress, and uploads it via the WordPress REST API. This should not be a command-line tool; just a Node script executed directly with `node`. Keep the design simple.

## Acceptance

Given a Markdown file(s) or directories of files successfully create or update posts (or pages) in wordpress. Specifically:

- [ ] Upload posts
  - [x] Correct title
  - [x] content
    - [x] Put rendered HTML (Markdown → HTML) into the WordPress `content` field.
      - [ ] check footnotes and other non-standard markdown
    - [x] Store original Markdown in post meta (`raw_markdown`).
  - [x] slug **✅2025-11-27 this is working**
    * If a `slug` exists and a post with that slug already exists, update that post; otherwise create a new post.
    * Slug determiend by file path if no slug field or frontmatter in the post.
  - [x] date **✅2025-11-28**
    * Set `date` if provided; otherwise use “now”.
  - [ ] status (?? ❓) - should be set to `publish`
  - [x] images and media - see handle media item as preliminary for this to work
    - [ ] set featured image using either `image:` in frontmatter or first image
    - [ ] Images and media (e.g. pdfs) in body. Need to support obsidian and markdown links etc
  - [ ] Handle tags and taxonomies: **💬2025-11-28 ❓ not sure this is needed.**
    * Map front-matter tags/categories to WordPress taxonomies; create terms on demand if they don’t exist.
    * Set `status` based on config or front-matter override. ❓ what is status?
- [x] Upload pages **✅2025-11-29 ❌ won't do for now. Not sure pages are so crucial.**
- [x] 3. Handle media - see below **✅2025-11-28**
- [x] 4. Handle authors / team mapping **🚧2025-11-29 this is working but we don't yet look up our mapping of names to team members.**
- [x] 5. Idempotency / safety. **✅2025-11-28 given we use slugs and file names on media**
- [ ] 6. Output:
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

## ✅ Subtask no 1

* Convert Markdown → HTML using `remark` (including parsing frontmatter)
* Produce a clean JS object containing whatever is needed for WordPress upload
* Create a sample Markdown input file e.g. `tests/fixtures/sample-post.md`, with typical front matter fields such as `title`, `date`, `status`, `tags`.
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

## Task 6: Support date extraction and fallback when uploading posts

Add date parsing in the markdown layer: prefer `date`, fall back to `created`, otherwise leave unset for WordPress to default to today.

Ensure WordPress upload layer sets current date only when upstream did not supply one.

Add tests in markdown layer to cover `date`, `created`, and missing date cases; add E2E test plan stub for the same scenarios.

### Acceptance Criteria:

- [x] Markdown parsing returns the `date` value when present.
- [x] Markdown parsing returns the `created` value when `date` is absent.
- [x] When neither field exists, markdown layer leaves date undefined; WordPress layer assigns today's date on upload.
- [x] Tests exist for markdown date extraction logic as unit test
- [ ] Tests exist in E2E tests covering that case (inspect for date that should show up for at least one of the uploaded posts)

Raw dictation

> OK, I want to outline adding dates to your posts. So I want to make sure I mark down there extracts the date, which should be either in the date field or in the created field. Either one of if the date field use that field, if there's a creative field use that field. So what I mean, sorry, use the date field primarily if fall back to the created field. And if not, I guess you set today's date. Actually, don't set today's date. Let's do that the WordPress layer. So at the WordPress layer, if you don't set the date, let's set it to today when we do the uploading. And I want to suit a test for that in the markdown layer. And I think we could also set a test for that in the end to end tests, even though we can't run them. So please distill that. We're going to then out of that create like a small description of this issue and then the acceptance criteria for it as

## Task no 7: 🏞️ WordPress Post Uploader: Image Rewriting

Update the content upload code to WordPress (upload.js etc) to correctly handle and **rewrite all local image references** within a Markdown post's content (including front matter, HTML tags, and Obsidian-style links). The core logic involves replacing local paths with the corresponding URLs on the wordpress server generated during the media upload step (and stored in `uploadMediaMap.json`).

The process must also automatically determine and set the post's **Featured Image**.

Notes:

- We can assume we have a mapping file (`uploadMediaMap.json`) that contains `filename` to `destination_url` pairs.

### Acceptance Criteria

- [ ] Do test driven development: this can be unit tested for the markdown processing module.
  - [ ] Have a mock media mapping file (`uploadMediaMap.json`) for testing purposes in fixtures directory
  - [ ] Have one or two sample wordpress files
  - [ ] Check that the payload generated for wordpress by the markdown processing module correctly handles local image references.
- [ ] Additionally you can also update the e2e tests in basic ways e.g test that featured image is correctly set (retrieve the featured image from the wordpress API)
- [ ] **Image Link Identification & Rewriting:** The code must locate and rewrite local image paths for the following three types of references:
    * **Front Matter:** A key-value pair `image: [local_path]`.
    * **HTML Tags:** Within the post body, locate image and PDF references using standard HTML tags (e.g., `<img src="...">`, `<a href="...pdf">`).
    * **Markdown Links:** Locate and process references using the format standard Markdown `![alt](local_path)`.
    * **Obsidian Links:** Locate and process references using the format `![[local_path]]`
- [ ] **URL Replacement:** The local paths identified must be replaced with their corresponding absolute WordPress destination URLs found in the media mapping file.
    * Note it would make sense to use relative urls on the server to make this info more portable i.e. `/uploads/filename.jpg` rather than absolute urls like `https://example.com/uploads/filename.jpg`
    * I would suggest this be an option with a default value of `true`.
- [ ]  **Featured Image Logic:** The script must set the WordPress post's featured image based on the following priority:
    * **Priority 1:** Use the image URL specified in the **Front Matter** (if present).
    * **Priority 2:** If no image is found in the Front Matter, use the URL of the **first image found** within the post body. (if any)
- [ ] Update README.md here to reflect this new feature (in a concise way)

### Implementation Notes

* **Mapping Dependency:** The script requires the **`uploadMediaMap.json`** file (or equivalent) to be loaded and accessible for lookups.
  * NB: the markdown processing code should be passed a map (not a path to a file) to make the code more portable and easier to test.
  * It should be the command line that loads an actual map. This map should default to `uploadMediaMap.json` in current directory and have a `--media-map` option to specify a different file.
* **Regular Expressions/Parsing:** Robust parsing tools (e.g., regex, dedicated Markdown parsers) are necessary to accurately identify and extract the three different reference formats (Front Matter keys, HTML attributes, and Markdown/Obsidian syntax).
* **Front Matter Library:** A library to safely parse YAML/TOML Front Matter is recommended for the first priority check.
* **WordPress API:** The final Featured Image URL must be linked to the post during the main post creation/update API call (typically using the media item's WordPress ID).

## ✅ Task 8a: strip blog prefix from slug if it exists

> why do uploaded posts get blog prefixed to their slug? is this due to our code or to do with configuration of wordpress server?

Ans: The uploader never adds blog to slugs. In src/lib.js the slug sent to WordPress is just frontmatter.slug or the filename basename (no prefix), and api-output-for-sample-blog-post.json shows the stored slug is second-renaissance-name-why while the returned link is …/blog/second-renaissance-name-why/. That blog segment comes from the WordPress site’s permalink/site configuration (e.g., WP installed under /blog or permalink structure /blog/%postname%/). If you want it gone, change the WordPress permalink/base path; no code changes here are needed.

Ok, that suggests we should make some change to our uploader code ... which is that if the slug starts with blog prefix (because it came from a directory /blog/xxx) then we should strip that from the slug before uploading (otherwise we will end up with blog prefix duplicated). please implement that. this should go in the wordpress uploading code not in the markdown processing btw.

## ✅ Task 9a: Create people / team on the server based on local markdown files

I want a new cli command in `upload.js` for people and corresponding library code that:

- [ ] given a markdown file like those inside of next.life.org/people
  - NB: you might want to investigate that to look at the standard structure of those files and document that
- [ ] It creates an entry on the WordPress instance of the team kind of post type
  - or whatever type that is (? the author’s type) for that person.
  - You can research what the structure should look like by getting an existing author - you can find that information I think in `research/list-wordpress-team.js`.
  - BONUS: also add a cli command to list existing team members on the server (maybe with `people list` option)
- [ ] I want to exit if there is an existing team member of the same name.
  - [ ] I want an --override flag that will update the existing entry if it exists
- [ ] I can pass a single file or files or a directory. I think in the best case I even just want to pass it the people folder. In general, it should test whether there is an existing team member with that name.
- Let's create some unit tests for this functionality
- [ ] and an e2e test against the WordPress instance.
- [ ] Let's update README.md with some info about this command (and put relevant info in the command cli help etc)

## Task 9b: integrate author mapping in doing the author setting on uploading

From our work with in PLAN-authors.md we have obtained a `authors.json` which maps local author names to WordPress author IDs. We need to use this mapping to set the author on the uploaded post.

We also have authors.e2e.test.js which shows how to set authors on a wordpress post.

We want to update the wordpress library code that does uploading to set authors using the `authors.json` file and set the author on the uploaded post.

### Acceptance

- [ ] Update the wordpress library code to use the authors.json file to set the author on the uploaded post
  - [ ] Create a fixtures authors file (can just copy the authors.json) and have e2e tests to use it
  - [ ] Probably split out a sub-function now (if not there already) that given the output from markdown layer prepares the json structure for uploading to wordpress (so we can unit test it)
  - [ ] Add unit tests for the sub-function that prepares the json structure for uploading to wordpress
- [ ] Update the e2e tests as well for authors mapping
- [ ] update `upload.js` to have an `authors` option to point to authors file default to `authors.json` in current directory.

Notes

- [ ] What do i do about authors that aren't existing on wordpress? (i.e. no `wordpress_id`)
  - In this case skip setting authors and console log a warning

## Task 10: overall migration

- [ ] How do i set .env differently for dev and prod and use that in upload scripts
  - [ ] Can i run the upload scripts from a different directory

Qu

- [ ] Do i want to automate all of this end to end and have it able to restart if necessary? I'm guessing yes ...
  - [ ] i want a cache directory or somesuch
  - [ ] I need to provide the authors list
    - [ ] would be kind of cool to automated this ... (but that's an exercise for later)

To run:

- [ ] Media upload (use media mapping if already exists) `node upload.js media --mapping mediamap.json`
- [x] Get authors mapping: `node upload.js people --mapping ../sandbox/mediamap-staging.json --authors authors.json "next.lifeitself.org/people"`  
- [ ] Upload all blog posts using media mapping and authors mapping `node upload.js posts --mapping mediamap.json --authors authors.json next.lifeitself.org/blog`
