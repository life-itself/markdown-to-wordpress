A migration tool (command line tool) to migrate our existing markdown material to WordPress in a fairly complex way.

## Context

We are migrating the **Life Itself website https://lifeitself.org/** to WordPress.

- The existing site contains a large volume of content (around 1,000 posts) along with images and other assets
- The content is stored in **GitHub at https://github.com/life-itself/lifeitself.org** and published with Flowershow (old self-hosted version) 
- We need a migration script that can transfer posts and media into WordPress, upload images to the Media Library, relink them correctly within posts, and map existing metadata such as tags or taxonomies.
- The aim is to create a reliable, repeatable process that handles the scale and complexity of the migration while preserving content integrity.

## Spec (experiments)

So far, neither are great ... as a bit over-complex. Insight is to break down parts myself and then spec one part at a time and create that and then chain them together.

- SPEC v0.1 (openai)
- Spec v0.2 (Cursor)

## Overview

# WordPress Migration Steps

0. Sort out images
1. Prepare source content  
2. Decide mappings  
3. Upload media  
4. Rewrite links in content  
5. Create content in WordPress  
6. Verify & tidy  
7. Iterate (optional, later)  

---

### 0. Image processing

- [ ] Renaming image assets (based on file they are used in)
- [ ] Uploading image assets
- [ ] Updating links in markdown files to corrected image links

### 1. Prepare source content

- [ ] Clean up front-matter (titles, dates, slugs, tags)  
- [ ] Fix/standardize Markdown 
- [ ] Rename images sensibly; ensure alt text  
- [ ] Fixing wiki markdown links like `[[]]` which aren't fully qualified
  - [ ] Locate broken links

### 2. Decide mappings

- [ ] Map folders/files to WordPress types (post, page, etc.)  
- [ ] Decide taxonomy use (tags/categories)  
- [ ] Choose final permalink style (usually slug-based)  

### 3. Upload media

- [ ] Upload all referenced images/files to the WP media library  
- [ ] Record the final URLs/IDs  

### 4. Rewrite links in content

- [ ] Replace local image paths with their WP media URLs  
- [ ] Convert internal links to their final slugs/paths  

### 5. Create content in WordPress

- [ ] Create posts/pages with title, slug, date, status, excerpt  
- [ ] Set featured image where relevant  
- [ ] Assign tags/categories  

### 6. Verify & tidy

- [ ] Spot-check a sample: images display, links work, formatting looks right  
- [ ] Add redirects for any old URLs if needed  
- [ ] Generate a short report of anything to fix later  

### 7. Iterate (optional, later)

- [ ] Add custom post types/fields if needed  
- [ ] Improve images (sizes/WebP)  
- [ ] Add richer blocks, embeds, or shortcodes  

# Notes

## Things to cover

- [ ] Fixing wiki markdown links like `[[]]` which aren't fully qualified

## Inbox

- [ ] ➕2025-08-29 https://gitlab.com/obviate.io/hugo2wordpress/-/blob/main/hugo2wordpress.py - a sort of useful script