# WordPress HTML to Markdown Conversion

Create a process that downloads the raw HTML source from a specified WordPress URL, locally caches the source html, converts the HTML content to **HTML and Tailwind css**.

This is a complex multi-step task involving web scraping, local caching, HTML-to-Markdown conversion, and styling transformation (to Tailwind CSS).

## Acceptance Criteria

- [ ] Given a single, external WordPress URL convert this to clean html + tailwind css. Output file should be saved in the local directory with a suitable name
- [ ] Resulting html + css is responsive (works on mobile and desktop)
- [ ] All images and media work (and are linking back to original urls on source site)
- [ ] This should be done in NodeJS and have a simple command line interface
  - [ ] Should output the name of the resulting output file and the cache path of the source html

## Notes

- **Caching:** The raw HTML source must be downloaded and stored locally in a designated directory (e.g., `tmp/`).
-  **Core Conversion:** The core content of the HTML must be accurately converted to html + css
- **Responsiveness:** The output structure must be fully responsive, supporting both mobile and full-screen layouts. Existing responsive structures should be retained; otherwise, standard Tailwind responsiveness must be applied.
- **Asset Handling:** All existing external asset URLs (images, videos, etc.) must be kept.
-  **Relative Path Resolution:** Any relative asset URLs in the original HTML must be resolved to their absolute path using the original base URL provided.
  * **URL Tracking:** Crucially, the **original base URL** must be retained throughout the process to correctly resolve relative asset paths.
