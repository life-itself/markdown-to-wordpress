Cleaning up original lifeitself.org markdown repo.

- [x] Do initial analysis of state **✅2025-11-24 see https://github.com/life-itself/community/issues/1253**
- [x] Clean up (remove stuff in original repo)
    - [x] Notes can go (already in github.com/life-itself/community)
    - [x] Tao can go ...
- [ ] copied to next.lifeitself.org repo so we didn't mess with live site
    - [x] Copy to a new repo (get rid of git lfs)
- [x] Removed unused images **✅2025-11-24**
  - [ ] 🚩 but had some issues and some images may now be missing. See analysis in `debug-missing-images`. This may need some further debugging.
  - [ ] Need to re-add excalidraw svgs (either export as png (probably better) or support svgs in wordpress or host on another server)
- [ ] Rename images to more meaningful names **✅2025-11-28 ❌ aborted. did this and realized it may cause issues especially if debugging missing images so reverted. Not really needed. See [image-renaming](image-renaming) **
- [x] Moved all blog files to base directory - see Task 2 below **✅2025-11-30**
- [ ] Began prep for a more substantial refactor/cleanup of "pages" (non blog pages) **🚧2025-11-26 see [review.md](review.md)**
- [ ] Check all broken links (e.g. saw at least one link to notes which are now removed)
  - [ ] e.g. in /blog/research-hackathon-june-2023.md `We want to create [[/notes/reading-lists-hackathon-project|reading-lists-hackathon-project|simple reading lists for key ideas and background]] in our emerging field.`

2025-11-28 Things we'll need to fix at the end

- [ ] svgs that are missing.
- [ ] images that are now missing in next
- [ ] check broken links in general

# Tasks

## Analysis of initial state

TODO: copy from github issue

- [ ] ❓ Rename images

Analysis notes

- [ ] Only 3 non-markdown pages: index (home), initiatives and residencies (and categories)

## 📥 Notes on repo content

- [ ] duplicated metacrisis.md files

## Unused images

Make a list of all image files in content directory and then find out which markdown or jsx/html files they are used in (so that we can work out which images are unused).

You should search just by basename of the image file (not full path).

## Outputs

- [ ] Text file with a list of images
- [ ] csv file of usage as per description below
- [ ] Python file for doing this work

### csv file headings

```
image | used | files
```

- `image` is path to image
- used is `y/n` indicated if image is used somewhere
- files is list of files separated by ` :: ` where image is used

## Task 2: flattening the blog 

Motivation: on wordpress i can't have posts with a url structure - only a single slug. That means i need all the markdown posts to be flattened into a single folder.

- [x] Question: If i flattened the file structure here to have markdown posts at the base folder would there be any naming conflicts? or put another way are there any markdown posts in this folder and subfolders with the same base filename? **• Flattening would be safe: I found 390 .md files and all have unique filenames
  (no duplicates on stem or even case-insensitive), so moving them all to the
  base folder won’t create naming conflicts.**
- [x] Assuming not, let's flatten the file structure here to have markdown posts at the base folder.
  > Flatten the blog directory by moving all markdown files in blog directory to the root blog folder. I have already checked there are no name collisions. If any image or media (e.g. pdf) links in frontmatter, html links, markdown links or obsidian links ![[...]] have *relative* paths i.e. begin with ../ you may need to fix these up. Otherwise you can leave the links as is as they should keep working.

DONE

- Moved all markdown posts from dated subfolders into the root blog/ directory and removed the empty year/month directories (see git status for the mass delete/add pairs).
- Adjusted relative links now that everything lives in blog/: updated asset/excalidraw paths in blog/co-living-at-art-earth-tech.md, blog/deliberately-developmental-spaces-a-key-to-addressing-the-metacrisis.md, blog/tenzo-note-4.md; fixed
  hub/notes references in blog/research-hackathon-{june,may}-2023/2024.md; corrected the internal links in blog/collective-wisdom-reflections.md and blog/new-community-chat.md.
- Verified no nested files remain (find blog -mindepth 2 -type f returns nothing) and all ../ references now point from the new root.

› Just to check did any image paths need to be rewritten?

- Yes. These were rewritten to stay valid after the move:
  - blog/co-living-at-art-earth-tech.md: four Obsidian image refs -> ../excalidraw/... and ../assets/images/....
  - blog/deliberately-developmental-spaces-a-key-to-addressing-the-metacrisis.md: hero image -> ../assets/images/Group-528.png.
  - blog/tenzo-note-4.md: two gallery images -> ../assets/images/tenzo-note-4-cooking*.jpg.

## ✅ Task 2b: correct all relative links to absolute

 OK, can we also now update those relative links to be absolute links e.g. /assets/ rather `../assets/...` and `/excalidraw` rather than `../


## Task 3: tidy up people / authors ...

- [x] Remove khalil-ali overall
- [x] Remove jamesredenbaugh
- [x] merge artearthtech with lifexitself  
  - [x]  Rename lifexitself to lifeitselfteam
  - [x] Change artearthtech to lifeitselfteam
- [x] Fix `liu bauer` to `liu-bauer`
- [x] Fix `Eilidh Ross` to `eilidhross`

### People entries missing an avatar in frontmatter:

```
people/artearthtech.md XX
people/charley-lee.md
people/elisalifeitself.md
people/jamesredenbaugh.md XX
people/joe-hughes.md
people/julie-dayot.md
people/lifexitself.md
people/nareshgg7.md
people/sophie84d503f875.md
```

### Research

Which authors need creating on server (if we want to map all authors)?

#### Which authors exist locally and need creating on wordpress?

> OK, get a me a list of authors with post counts who don't exist on server (no wordpress_id) but do existing in people directory in next.lifeitself.org (add a flag on authors.json exists_local: true if there is local info on them.

id, name, posts, pages, example
eilidhross, Eilidh Ross, 35, 3,
artearthtech, artearthtech, 28, 4,
theo-cox, Theo Cox, 22, 4,
petronellac3ecd0923b, Petronella Tyson, 18, 0,
iljad20a2d59ebb, Ilja Maiber, 14, 0,
nareshgg7, Naresh Giangrande, 7, 0,
matthew-mccarthy, Matthew McCarthy, 6, 0,
sophie84d503f875, Sophie Kirkham, 5, 1,
elisalifeitself, Elisa Paka, 5, 0,
moon-immisch, Moon Immisch, 5, 0,
joe-hughes, Joe Hughes, 4, 0,
lifexitself, Life Itself, 4, 0,
alexia, Alexia Netcu, 2, 0,
zaibul-nisa, Zaibul Nisa, 2, 0,
liu-bauer, Liu Bauer, 1, 1,
charley-lee, Charley Lee, 1, 0, blog/life-itself-community-hangouts.md
james-davies-warner, James Davies-Warner, 1, 0, blog/renewal-and-renovation-petit-bois-martin.md
julie-dayot, Julie Dayot, 1, 0, blog/we-are-not-here-to-change-the-world.md
sen-zhan, Sen Zhan, 1, 0, blog/hubbook-a-collective-evolution.md
khalil-ali, Khalil Ali, 0, 2,
marc-santolini, Marc Santolini, 0, 1, learn/praxis-ecology.md

#### Which would need creating locally *and* remote (i.e. don't exist locally either in people folder?)

9 authors in research/authors.json with some posts/pages without:

- mapping to wordpress (no wordpress_id)
- no next.lifeitself.org/people entry; counted posts by scanning author/authors front matter across next.lifeitself.org/**/*.md:

```
Geoff Mulgan 1
Jamie Bristow 1
matt-osborn 2
Oren Slozberg 1
Simon Grant 1

# No longer relevant
zaib-nisa 1 XX (dupe of zaibulnisa)
liu bauer 1 XX (dupe of liubauer)
author-id-here 1 XX
Eilidh Ross 7 XX (dupe of eilidhross)
```

Which have posts?

```
Geoff Mulgan 1 next.lifeitself.org/blog/can-new-social-and-digital-technologies-transform-governance.md

Jamie Bristow 1 next.lifeitself.org/blog/ecosystem-mapping-of-contemplative-approaches-to-transformative-social-change.md

matt-osborn 2 next.lifeitself.org/blog/visualisation-ideas.md next.lifeitself.org/blog/second-renaissance-mapping-and-sensemaking.md

Oren Slozberg 1 next.lifeitself.org/blog/developmental-spaces-for-an-age-of-transition.md

Simon Grant 1 next.lifeitself.org/blog/intentional-coming-together.md
```
