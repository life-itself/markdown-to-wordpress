This is the plan for the media uploader.

## Substack no 6: image uploading command line tool and script

This extends are library and adds a new command line script uploadMedia.js to handle the uploading of media assets (images + PDFs) to WordPress. The script must accept a single file path or a directory path. It will utilize a local JSON file, `uploadMediaMap.json`, to store key-value pairs of local file paths (and optionally their hash) against their final WordPress destination URLs, enabling **idempotent uploads** (skipping already processed files).

I want the `uploadMediaMap.json` so it can be used in subsequent steps to rewrite links in markdown files ahead of their uploading.

To test this out you can use the content in `next.lifeitself.org` subdirectory relative to this file.

I would test out by just uploading a single file.

### Acceptance Criteria

1. **Command:** A new CLI script must be created.
2. **Input:** The script must accept arguments of either file(s) or directory(ies).all contained **image files** must be scanned and selected for upload.
3. **Idempotency & Mapping:**
    * The script must read the existing mapping data from a file named **`uploadMediaMap.json`**.
    * This file stores pairs of `[local_file_path]` (and optionally a file hash) and the `[destination_url]`.
    * **Skip Logic:** Before uploading a file, the script must check `uploadMediaMap.json`. If a match is found, the file must be **skipped**, and this action must be noted.
    * **Update Logic:** If the file is uploaded successfully, its local path/hash and destination URL must be added to the mapping data.
      * Store the local file path used for uploading in the wordpress metadata of the uploaded file
    * The **`uploadMediaMap.json`** file must be rewritten/updated after all successful uploads.
4. **Logging:** The script must provide **terminal output** indicating which files were uploaded and which were skipped.

### Implementation Notes

* **File Filtering:** The script needs logic to specifically filter for common image file extensions when processing a directory.
* **Idempotency Key:** Consider using a combination of the local file path and a **file hash** (e.g., MD5 or SHA) as the key in `uploadMediaMap.json` to ensure a file isn't re-uploaded if it has changed locally but retained the same path.
* **WordPress API:** The tool will rely on the WordPress REST API, specifically the `/wp/v2/media` endpoint, for file uploads.
  * use wordpress login info in the `.env` file. See README.md in this directory for how that works (and example of usage in `upload.js`)
* **Metadata:** To set custom metadata, you may need to utilize the `meta` fields within the API request during upload, or potentially use a custom endpoint/plugin if the standard API is too restrictive for setting arbitrary metadata fields like the local path.
* **CLI Progress:** (nice to have). show progress e.g. how many files to upload, how many uploaded so far.

### Unique image file names?

Are image file names unique so we can use them as the idempotency key?

Yes, for our purposes.

- Ran a quick scan over assets/** with a Python script; filenames are not unique.
- Duplicate basenames found: catherine-bio.png (assets/images/..., assets/site/team/...), cecile-cropped.png, lauren-wigmore-profile-image.jpg, lifeitself-landingpage.webp, profile-pic-boaz.jpg, profile-pic-matthew.jpg.
- Each duplicate pair lives under different subfolders (assets/images, assets/site/team, or root assets), confirming same filenames on different paths.

Then asked: Are the images themselves different?

- Checked SHA-256 hashes for each duplicate filename pair under assets/**.
- catherine-bio.png, cecile-cropped.png, lauren-wigmore-profile-image.jpg, profile-pic-matthew.jpg, and lifeitself-landingpage.webp are byte-for-byte identical across their duplicate paths.
- profile-pic-boaz.jpg differs: assets/images/... hash b2f2289…64688, while assets/site/team/... hash 05c7ad2…a2b4, so these two files are distinct versions.

Checked boaz picture by eye and this is the same.

### UPDATE: update to store only image filename in media upload

use only image filename as the key in uploadMediaMap.json when building the upload info dictionary.

### UPDATE 6.b: upload pdfs as well as images and store in same way

As it says: let's upload pdfs too.

## 2025-11-28 improvements

Update the upload media (`uploadMedia.js` etc) to in command line mode:

- [ ] have a total list of files to upload (calculate at start)
- [ ] have a progress counter at the top showing total files uploaded and percentage complete
- [ ] just show the latest file processed and current file(s) (if multiple files) being processed (rather than log each file to console)
- [ ] write to map as we go along ... (rather than just at the end and ensure we write if the process exits badly)

Investigate how to parallelize upload without compromising the integrity of the map and propose if this possible (probably parallelize no more than 5-10 files at a time)

- [ ] parallelize upload (may be a tension with writing the map ... but if we have an overall process that is delegating files to upload should not be a problem)

## 2025-11-28 part 2 improvements

- [x] Progress updates must redraw in place (single-line status with spinner) instead of spooling the terminal.
  - Use `stdout.isTTY` guard; fallback to simple logging if not TTY.
  - Show spinner + counts: `⟳ uploading 3/42 (7%) :: current: foo.png`.
  - When logging a completed upload/skip/failure, temporarily write a newline, then resume spinner on the next tick.
  - Stop the spinner cleanly on exit (success or error) and print a final summary line.
  - Keep overall progress counters consistent with the totals calculated at start.
  - Track and display ongoing totals (uploaded, skipped, failed) in the spinner line so it’s always visible without scrolling.

Ask me to clarify what i mean if you need help.

## 2025-11-28 part 3 improvements

- [x] log errors specifically to terminal in a different color and log them in background to a simple log file e.g. `upload_media_errors.log`
