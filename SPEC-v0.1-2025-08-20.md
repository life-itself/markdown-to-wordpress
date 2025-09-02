# Life Itself → WordPress Migration Tool (Spec)

*ChatGPT*

## Prompt

So, regarding the conversion script from our other site, it's become increasingly clear, as I understand it, that almost everything that is in a series, be it like a podcast or residency, like events, or our blog posts, or our news, are post types, they're types of posts. And what we want to do in our script is to have us think that once we've decided the rough data type in WordPress, we want something that takes the markdown and its front matter and converts it over, and we'll want to target these different types. Now, there's something a little bit more subtle, which is the page, when there are different pages which aren't really posts, but are more like actual pages on the website, like learn pages, like pages about particular topics, where we'll also want to invent them, or also the other example where we have a catalog of things is our initiatives. And the reason I kind of think initiatives and other things like that are more like pages is they're not really...I also think I actually want to associate posts to those pages. For example, I want to show on an initiative or a project that we're doing all of the news, all of the articles related to that. Now, I guess I can also use tags for that. I don't know quite how I do that. Yeah, I either use relationship fields to manually select relationships between different front-end types, or use the taxonomy, use it as a taxonomy, create a taxonomy for it. So if it's more of a bucket, and I don't need a singular page for it, I only need an archive of it. Yes. Yeah, I understand. I understand. But what I'm trying to come back to now is designing the script. I'm trying to create...what I want you to generate here, ChatGPT, is I want you to generate the kind of requirements or briefing for code generation for a JavaScript, probably a Node.js script that will take the input markdown files, and I'll provide some of those as templates, and then generate the code to upload those to WordPress via the WordPress API, but we're targeting different WordPress post types that we will specify as well. So at this point, I don't need you to actually generate any code, but I want you to start generating a kind of spec that would be fed into something that will then generate this code based on what I'm describing. Now I will need to provide more information, like the example markdown files and then the target post types, but I'd like you to already outline the idea. And I think if the target post types we already have, or let's call them data types, are podcast, normal blog or news article, and residencies or events, like just events basically. And I mean, a blog post is to say it's going to have authors, it's going to have a featured, basically a selected featured image. I would like there to...there's probably a date it's published, maybe a date it's been latest updated because that does happen. I think I want to have obviously a title and a subtitle or description text. And I think that's...and whether it's...there'll be other things like whether it's featured or not. And then obviously there's like tags or kind of topics, tags on me that it covers. Then for residencies, we've got a start, end date. We've got maybe who's hosting, where it's located, where the event is taking place. Yeah, I mean, again, featured image, description, title, and the full text. And then I've got podcasts, which I think are fairly standard. But yeah, if you could just take that and generate an outline, that would be...of a kind of spec or a readme for a project that would be used for input into something which would auto-generate the code.

## 1) Goal

Convert Markdown content (with YAML front matter) from the current FlowerShow/Next.js repo into WordPress content via API, supporting multiple **target post types** and **pages**, with safe re-runs as the model evolves.

## 2) Scope (MVP)

* Input: Local Markdown files + assets (images), organized by folders.
* Output: WordPress posts/pages of specified **post types**:

  * `post` (Blog/News)
  * `podcast` (custom post type)
  * `event` (Residency/Event; custom post type)
  * `page` (for “Learn”, “Initiatives” etc.)
* Optional relationships/taxonomies:

  * Tags/topics (core WP `post_tag` + custom taxonomies).
  * Project/Initiative linkage via **taxonomy** or **relationship field** (decide per content area).
* Media: Upload featured images and in-body images; re-link image URLs.
* Re-runnable: **Upsert** based on a stable key (slug or external\_id); safe to run multiple times.

## 3) Non-Goals (MVP)

* No UI; CLI-only.
* No HTML→Markdown conversion (input is already Markdown).
* No complex WYSIWYG cleanup; minimal formatting normalization only.

## 4) Architecture

* Runtime: **Node.js** (LTS).
* WP API: **WordPress REST API** (+ **ACF to REST API** if using ACF fields).
* Auth: WP Application Passwords or JWT (configurable).
* Config-driven mappings (YAML/JSON) to avoid hardcoding.

## 5) Inputs & Structure

```
content/
  posts/               // blog+news
    2024-...md
  podcasts/
    ep-001.md
  events/
    2025-...md
  pages/
    initiatives/       // initiative pages (or treat as taxonomy later)
      index.md
    learn/
      index.md
assets/
  images/...
config/
  mapping.yaml         // mapping of front matter → WP fields per type
  taxonomies.yaml      // tag/topic mappings, initiative taxonomy slugs, etc.
```

### 5.1 Front Matter Examples

**Blog/News (`post`)**

```yaml
title: "Why Sense-making Matters"
subtitle: "A gentle intro"
date: 2025-05-12
updated: 2025-08-01
slug: "sensemaking-matters"
authors: ["Rufus Pollock", "Rosie Bell"]
featured_image: "./assets/images/sensemaking.jpg"
featured: true
tags: ["sensemaking", "second-renaissance"]
topics: ["culture","education"]        # optional custom taxonomy
initiatives: ["life-itself-studio"]    # taxonomy or relationship
```

**Event/Residency (`event`)**

```yaml
title: "Bergerac Residency – Autumn"
slug: "bergerac-residency-autumn-2025"
start_date: 2025-10-01
end_date: 2025-10-15
location_name: "Oasis, Bergerac"
location_address: "..."
host: ["Life Itself"]
featured_image: "./assets/images/bergerac.jpg"
tags: ["residency"]
initiatives: ["practice-hubs"]
```

**Podcast (`podcast`)**

```yaml
title: "Ep.12 – Metacrisis 101"
slug: "podcast-ep-12-metacrisis-101"
date: 2025-04-02
audio_url: "https://.../ep12.mp3"       # or local file to upload
duration: "00:48:22"
guests: ["Jamie Bristow"]
featured_image: "./assets/images/podcast-ep12.jpg"
tags: ["podcast","metacrisis"]
initiatives: ["little-wiser"]
```

**Page**

```yaml
title: "Initiative: Life Itself Studio"
slug: "life-itself-studio"
type: "page"
featured_image: "./assets/images/studio-hero.jpg"
description: "Overview page..."
```

> Note: Keep `slug` stable; it’s the **external\_id** for upserts.

## 6) Configuration (mapping.yaml)

* **Global**

  * `site.baseUrl`
  * `media.basePath` (local)
  * `rewrite.imageBaseUrl` (final)
* **Auth**

  * `wp.baseUrl`
  * `wp.auth.method`: `appPassword` | `jwt`
  * secrets via env vars.
* **Per Target Type**

  * `post`:

    * `wpType`: `post`
    * field map: `title`, `excerpt` ← `subtitle`, `date` ← `date`, `modified` ← `updated`, `featured_media` ← `featured_image`
    * taxonomies: `post_tag` ← `tags`, `topic` ← `topics`
    * meta/ACF: `featured` ← `featured`
    * relationships: `initiative` taxonomy or `initiatives_rel` ACF
  * `podcast`:

    * `wpType`: `podcast`
    * fields: `title`, `date`, `featured_media`
    * taxonomies: `post_tag`
    * meta/ACF: `audio_url`, `duration`, `guests`
  * `event`:

    * `wpType`: `event`
    * meta/ACF: `start_date`, `end_date`, `location_name`, `location_address`, `host`
    * taxonomies: `post_tag`, `initiative`
  * `page`:

    * `wpType`: `page`
    * fields: `title`, `slug`, `featured_media`
    * meta/ACF as needed.

> Decision knob: **Initiatives** as taxonomy vs relationship
>
> * If you want an **archive and filters** → use taxonomy `initiative`.
> * If you want curated hand-picks on pages → ACF relationship field.

## 7) CLI & Modes

```
migrate-wp \
  --type post|podcast|event|page|all \
  --src ./content/posts \
  --since 2025-01-01           # optional filter (front matter date)
  --dry-run                    # no writes; print plan
  --concurrency 4              # API parallelism
  --media-mode upload|skip     # skip to test mapping first
  --map ./config/mapping.yaml
  --tax ./config/taxonomies.yaml
```

## 8) Processing Pipeline

1. **Discover** files by type/folder or front matter `type`.
2. **Parse** front matter (YAML) + Markdown body.
3. **Normalize** fields (dates → ISO, arrays, booleans).
4. **Resolve Mapping** (per target type):

   * Required fields present? (title/slug/date as needed)
   * Map to WP core fields, taxonomies, ACF/meta.
5. **Media Handling**

   * Find `featured_image` + images referenced in Markdown.
   * Upload to WP Media (dedupe by checksum filename).
   * Replace local/relative image paths in content with WP URLs.
6. **Transform Content**

   * Convert Markdown → HTML (GitHub-flavored, keep simple).
   * Optional: keep raw markdown in ACF field for reference.
7. **Upsert**

   * Lookup by `slug` (or custom meta `external_id`).
   * Create if missing; otherwise update:

     * Core fields (title, content, excerpt, status)
     * Taxonomies
     * Meta/ACF
     * Featured media
8. **Relationships / Taxonomies**

   * Ensure terms exist (create if missing) for tags/topics/initiatives.
   * If using ACF relationships, resolve target IDs (pages or CPT items).
9. **Status**

   * Default `draft` (configurable `status: publish` for production).
10. **Log & Report**

    * JSONL log per item: action, id, slug, warnings, errors.
    * Summary at end.

## 9) Idempotency & Re-runs

* **Key**: `slug` or `external_id` → unique identifier.
* **Strategy**:

  * On re-run: compare incoming fields with live; update diffs only.
  * Optional `--force` to overwrite all mapped fields.
  * Keep a **content hash** of input to skip unchanged items (cache/DB file).
* **Deletion policy** (out of scope MVP): never delete by default; future flag `--prune`.

## 10) Error Handling & Resilience

* Network/API retries with backoff.
* Rate limiting via `concurrency` and request pacing.
* Partial failures do not stop the batch; record and continue.
* Validate required meta (e.g., events must have `start_date`, `end_date`).

## 11) Authors

* Mapping strategy:

  * If `authors` present:

    * Match by display name or email (configurable).
    * Create stub users **only if** configured; else fallback to default author and add original names into meta.
* Multi-author support via plugin (optional); otherwise put co-authors in meta.

## 12) Video Fields

* For **podcast** or posts with video:

  * If `audio_url`/`video_url` is remote (Vimeo/YouTube), store in ACF/meta and render via shortcode/template.
  * If local file path, optionally upload to WP Media and store URL (no adaptive streaming—see site policy).

## 13) Pages vs Initiatives

* If **Initiatives as pages**:

  * Create `page` with slug per initiative.
  * Later, theme/template shows **related content** by:

    * taxonomy `initiative` on posts, **or**
    * ACF relationship field pointing from posts to the initiative page.
* If **Initiatives as taxonomy**:

  * Create terms; initiative page uses term archive with custom template.

> Finalize this choice before codegen to set clean mappings.

## 14) Configuration Examples (mapping.yaml - sketch)

```yaml
wp:
  baseUrl: "https://example.com"
  auth:
    method: "appPassword"
    usernameEnv: "WP_USER"
    appPasswordEnv: "WP_APP_PASSWORD"

defaults:
  status: "draft"
  media:
    upload: true
    dedupeBy: "filename"   # or "sha1"
    linkImagesInContent: true

types:
  post:
    wpType: "post"
    fields:
      title: "title"
      excerpt: "subtitle"
      date: "date"
      modified: "updated"
      slug: "slug"
      content: "BODY"            # special token = markdown body
      featured_media: "featured_image"
    taxonomies:
      post_tag: "tags"
      topic: "topics"
      initiative: "initiatives"
    meta:
      featured: "featured"
      external_id: "slug"
  podcast:
    wpType: "podcast"
    fields:
      title: "title"
      date: "date"
      slug: "slug"
      content: "BODY"
      featured_media: "featured_image"
    taxonomies:
      post_tag: "tags"
      initiative: "initiatives"
    meta:
      audio_url: "audio_url"
      duration: "duration"
      guests: "guests"
      external_id: "slug"
  event:
    wpType: "event"
    fields:
      title: "title"
      slug: "slug"
      content: "BODY"
      featured_media: "featured_image"
    taxonomies:
      post_tag: "tags"
      initiative: "initiatives"
    meta:
      start_date: "start_date"
      end_date: "end_date"
      location_name: "location_name"
      location_address: "location_address"
      host: "host"
      external_id: "slug"
  page:
    wpType: "page"
    fields:
      title: "title"
      slug: "slug"
      content: "BODY"
      featured_media: "featured_image"
    meta:
      description: "description"
```

## 15) Content Transformation

* Markdown → HTML using a robust parser (e.g., `marked`, `markdown-it`).
* Preserve headings/links; convert image refs to uploaded WP URLs.
* Option to add `<!--more-->` break after first paragraph if excerpt missing.

## 16) Testing Plan

* **Dry-run** on 5 items per type; verify mapping and intended API payload.
* **Staging** WP environment first; confirm post types, ACF fields, taxonomies exist.
* Validate:

  * Slug collisions
  * Media upload & relinking
  * Event date rendering in theme
  * Podcast embed/playout
  * Initiative linkage (taxonomy or relationship)

## 17) Operational Checklist

* [ ] Decide **Initiatives**: taxonomy vs ACF relationship.
* [ ] Freeze post type names & ACF keys.
* [ ] Provide 2–3 **representative Markdown samples** per type.
* [ ] Provide **author mapping** policy.
* [ ] Provide **hosting/auth** creds to staging.
* [ ] Agree default `status` for imported items.

## 18) Roadmap (suggested)

* Phase 1: Prototype on `post` + media handling (dry-run → staging).
* Phase 2: Add `event` + `podcast` with ACF fields.
* Phase 3: Migrate selected `page`s (Initiatives/Learn).
* Phase 4: Relationships/taxonomies for Initiative rollups.
* Phase 5: Harden idempotency, pruning strategy, and reporting.

---

If you want, I can also produce:

* a **filled `mapping.yaml`** stub tailored to your exact ACF keys/post type names, and
* a **sample JSONL log format** spec for auditing each import.
