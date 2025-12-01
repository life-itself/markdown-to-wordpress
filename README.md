Migrating existing https://lifeitself.org/ that is in markdown and published with Flowershow (self-hosted) - see https://github.com/life-itself/lifeitself.org - to a new Wordpress site at https://next.lifeitself.org (and soon lifeitself.org). More context in SCQH at bottom.

TODO: explain the various subdirectories

# 🎉

2025-12-01T0130

```sh
rgrp@mac-23 uploader % node upload.js media push next.lifeitself.org                                                         
Prefill: fetched 995 remote media items; matched 751 local files; added 0 new mapping entries.
Found 886 media file(s) to process. Running with concurrency 5.
⠦ uploading 886/886 (100%) | uploaded:5 skipped:881 failed:0
Done. Uploaded: 5, Skipped: 881, Failed: 0. Mapping saved to /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/mediamap.json.
rgrp@mac-23 uploader % node upload.js media missing next.lifeitself.org
Missing: 0 file(s) not present in /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/mediamap.json
# 🎉 all done!
# NB: this was 4h of pain due to trying to debug why we kept getting duplicate uploading issues ...
```

And then the authors 🎉

```sh
rgrp@android-c0c553e9fddd64d8 uploader % node upload.js people build next.lifeitself.org/people
Step 1/3: building local authors map...
Wrote 33 author(s) to /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/authors.json.
Step 2/3: merging remote WordPress author IDs...
Merged remote WordPress IDs into /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/authors.json using 8 remote entries.
Step 3/3: creating/updating people in WordPress...
Created zaibul-nisa.md -> zaibul-nisa (id 2123)
Skipped valerie.md: authors mapping has wordpress_id 829.
Created theo-cox.md -> theo-cox (id 2124)
Skipped sylvieshiweibarbier.md: authors mapping has wordpress_id 107.
Created sophie84d503f875.md -> sophie84d503f875 (id 2125)
Created sen-zhan.md -> sen-zhan (id 2126)
Skipped rufuspollock.md: authors mapping has wordpress_id 103.
Created petronellac3ecd0923b.md -> petronellac3ecd0923b (id 2127)
Skipped nathen-fitchen.md: authors mapping has wordpress_id 136.
Created nareshgg7.md -> nareshgg7 (id 2128)
Created moon-immisch.md -> moon-immisch (id 2129)
Created matthew-mccarthy.md -> matthew-maccarthy (id 2130)
Created marc-santolini.md -> marc-santolini (id 2131)
Created liu-bauer.md -> liu-bauer (id 2132)
Created lifeitselfteam.md -> lifeitselfteam (id 2133)
Skipped liamaet.md: authors mapping has wordpress_id 826.
Skipped lauren-wigmore.md: authors mapping has wordpress_id 132.
Created julie-dayot.md -> julie-dayot (id 2134)
Created joe-hughes.md -> joe-hughes (id 2135)
Created james-davies-warner.md -> james-davies-warner (id 2136)
Created iljad20a2d59ebb.md -> iljad20a2d59ebb (id 2137)
Created elisalifeitself.md -> elisalifeitself (id 2138)
Created eilidhross.md -> eilidhross (id 2139)
Skipped catherine-tran.md: authors mapping has wordpress_id 128.
Skipped boaz-feldman.md: authors mapping has wordpress_id 124.
Created alexia.md -> alexia (id 2140)
Updated authors mapping at /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/authors.json.
```

Blog posts

```sh
Found 390 markdown file(s) to upload.
Loaded 880 media mapping entries from /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/mediamap.json.
Loaded 34 author mapping entries from /Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/authors.json.
Uploaded write-your-autobiography.md: https://app-6893b532c1ac1829f80cae6e.closte.com/?p=2141
Failed to upload word-laundrette-1-nirvana.md: Invalid parameter(s): tags
Failed to upload wiser-policy-forum-launch-bulletin.md: Invalid parameter(s): tags
```

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

Next up ... 2025-12-01

- [ ] podcasts
- [ ] pages ...

---

## Flowershow route

- [x] Push repo
- [x] Create flowershow site and build **✅2025-11-24 https://my.flowershow.app/@rufuspollock/next.lifeitself.org**
- [ ] Sort out home page (get it running) **✅2025-11-24 see [wp-to-markdown/PLAN.md](wp-to-markdown/PLAN.md) and https://my.flowershow.app/@rufuspollock/next.lifeitself.org**

🏆

- [ ] Sort out residencies
- [ ] Sort out initiatives
