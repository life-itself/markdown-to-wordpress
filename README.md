Migrating existing https://lifeitself.org/ that is in markdown and published with Flowershow (self-hosted) - see https://github.com/life-itself/lifeitself.org - to a new Wordpress site at https://next.lifeitself.org (and soon lifeitself.org). More context in SCQH at bottom.

TODO: explain the various subdirectories

## SCQA (short)

*redone 2025-11-24*

### Situation

- In an old version of Flowershow (self-hosted)
- Options:
    - Move to wordpress
    - Move to Flowershow cloud

### Complication

- Not sure how to push markdown in lossless way to wordpress
- If we stay in flowershow we may have problems making things easily editable (or at least w/o breaking things)

### Question

Should we migrate to wordpress or to flowershow cloud and how would we do each one?

### Hypothesis

let's go with wordpress route. (why? TODO)

- How you do wordpress is below in "Wordpress route"
- How you do flowershow cloud is below in "Flowershow route"

---

# Doing it

## Wordpress route

- **Clean up** original markdown repo -- see `clean`
- **Upload media**: We'll upload media uploader/uploadMedia.js caching the relevant fild mapping
- **Get authors mapping** get an author mapping (cached locally) for the ids for post authors
- **Upload posts**: run the main upload.js script to upload all blog posts
- **Upload pages**:  Page uploading is not yet done (we  need to finish our local clean up of the markdown repo)

More details:

- [x] Create a staging site **✅2025-11-24 https://app-689360d2c1ac1829f80cac86.closte.com/**
  - [ ] Research options **✅2025-11-24 it exists on closte https://closte.com/support/wordpress/staging-environment**
  - [x] Setup the site
  - [x] Check login credentials etc
- [ ] Do a test upload ...
- [ ] Start scripting this proper **🚧2025-11-30 see [uploader](uploader)**

---

## Flowershow route

- [x] Push repo
- [x] Create flowershow site and build **✅2025-11-24 https://my.flowershow.app/@rufuspollock/next.lifeitself.org**
- [ ] Sort out home page (get it running) **✅2025-11-24 see [wp-to-markdown/PLAN.md](wp-to-markdown/PLAN.md) and https://my.flowershow.app/@rufuspollock/next.lifeitself.org**

🏆

- [ ] Sort out residencies
- [ ] Sort out initiatives
