#  Create Node.js Script to Upload Markdown Blog Posts to WordPress via REST API

Create a nodejs script with best wordpress client library for uploading a new blog post from a markdown file. Keep this as simple as possible and use remark library for the markdown parsing. I want to support footnotes and other aspects of gfm.

I also want you to create a sample .env file that you read from for the key variables to access the wordpress instance. also output a minimal documentation into bottom of README.md file on how to use this. The script should be outputted into markdown-to-wordpress subdirectory

Summary: Create a minimal Node.js script that takes a Markdown file with front matter, converts it into a structure suitable for WordPress, and uploads it via the WordPress REST API. This should not be a command-line tool; just a Node script executed directly with `node`. Keep the design simple.

## Acceptance

* Convert Markdown → HTML using `remark` (including parsing frontmatter)
* Produce a clean JS object containing whatever is needed for WordPress upload
* Create a sample Markdown input file.
* Provide a basic Node script (e.g., `uploadPost.js`) that:
  * loads `.env`
  * reads a hardcoded Markdown file path for now
  * runs conversion → upload
  * logs the result
* Provide a `.env.sample` file with required WordPress credentials.
* Provide a minimal `package.json` containing only necessary dependencies.
* Extend the existing README with a section describing setup and usage.
* Include **tests only for the Markdown → WordPress-ready structure** (no tests for the API upload step).

## Requirements

* Run as simple node script (no need for CLI as yet)
* Use `remark` for Markdown parsing and conversion.
* Upload to WordPress using its REST API with credentials from environment variables.
* Keep implementation minimal and avoid abstraction unless necessary.
* Use this client library for wordpress https://github.com/WP-API/node-wpapi

## Analysis & Design

### Input

* One sample Markdown file (`sample-post.md`) with typical front matter fields such as `title`, `date`, `status`, `tags`.

### Architecture (Two Parts)

#### 1. Markdown Processing Module

* Reads a Markdown file.
* Parses front matter via relevant remark frontmatter plugin.
* Converts Markdown → HTML via `remark`.
* Returns an object suitable for uploading to Wordpress
* Has unit tests:
  * front matter extraction
  * Markdown → HTML conversion
  * structure of the output object

#### 2. WordPress Upload Module

* Accepts input from markdown processing module
* Constructs JSON payload expected by WordPress.
* Performs authenticated POST request with `axios`.
* No tests required at this stage.

### Script

* A top-level script (e.g., `uploadPost.js`) that:

  * loads `.env`
  * imports the two modules
  * defines the Markdown file path internally
  * converts then uploads
  * logs result or errors

### Environment

A `sample.env` file should include:

```
WP_BASE_URL="https://example.com"
WP_USERNAME="your_username"
WP_APP_PASSWORD="your_app_password"
```

### Documentation

Extend the README with:

* how to configure `.env`
* how to structure the Markdown file
* how to run the script using Node
* how to run the tests for the Markdown processor

## Subtask no 2

So I want to update the upload.js and make it into a command line script where I can pass it a file or a directory or a combination of files and directories and it will then upload those.

It will log to the terminal the urls of the resulting uploaded files on the WordPress site.
