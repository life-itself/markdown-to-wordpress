## Usage

Set up the simple Node script in this repo to convert Markdown and upload to WordPress:

1.  **Install dependencies**:
    ```sh
    npm install
    ```
2.  **Configure Environment**: Copy `.env.sample` to `.env` and set the following variables:
    *   `WP_BASE_URL`: The base URL of your WordPress site (e.g., `https://example.com`).
    *   `WP_USERNAME`: Your WordPress username.
    *   `WP_APP_PASSWORD`: A WordPress [application password](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/).

3.  **Create Markdown Files**: Write your posts in Markdown with YAML front matter. The `title` field is required.

    *Example (`my-post.md`):*
    ```markdown
    ---
    title: My Awesome Post
    slug: my-awesome-post
    status: draft
    tags: [tech, blogging]
    excerpt: A brief summary of the post.
    ---

    Your post content here, written in GitHub-Flavored Markdown.
    ```

4.  **Run the Uploader**: Execute the script from your terminal, passing one or more paths to your Markdown files or directories containing them.

    *   **Upload a single file**:
        ```sh
        node upload.js path/to/my-post.md
        ```

    *   **Upload multiple files**:
        ```sh
        node upload.js file1.md file2.md
        ```

    *   **Upload all Markdown files in a directory (and its subdirectories)**:
        ```sh
        node upload.js path/to/my/posts/
        ```

    *   **Upload a combination of files and directories**:
        ```sh
        node upload.js file1.md my-blog/
        ```

    On success, the script will log the URL of each uploaded post.

5.  **(Optional) Run Tests**:
    To verify the Markdown processing module, run the tests:
    ```sh
    npm test
    ```

### Upload Media Files

Use `uploadMedia.js` to push local images to WordPress before wiring their URLs into Markdown posts:

1.  **Prepare images**: Pass file and/or directory paths pointing at images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.avif`, `.heic`, `.heif`). Directories are scanned recursively.
2.  **Run the media uploader**:
    ```sh
    node uploadMedia.js path/to/image.png another/folder/
    ```
    *Use `-m custom-map.json` to override the mapping file location (`uploadMediaMap.json` by default).* 
3.  **Idempotent uploads**: The script records each upload in `uploadMediaMap.json` (path → hash → destination URL). Identical files are skipped automatically; changed files are re-uploaded and the mapping is updated.
4.  **WordPress metadata**: Each media item receives the original local path and file hash inside `meta[original_local_path]` / `meta[original_local_hash]`, letting WordPress keep track of the source asset.

`uploadMediaMap.json` is committed to this repo so later steps (e.g., rewriting Markdown image references) can reference already-uploaded assets.
