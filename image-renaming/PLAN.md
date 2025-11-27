i want you to look at the image files in the  subfolder and answer these questions

## Tasks

- [x] 1. are there any outside `assets` subfolder (of that folder). if so, how many and what are 5 examples. **✅2025-11-27 DONE. only ones are excalidraw svgs. Which i have now removed**
- [x]  how many of images have meaningless/random file names (and how many images in total) **✅2025-11-27 see below**
- [ ] Image renaming based on this.

## Subtask 2 how many of images have meaningless/random file names (and how many images in total)

Putting together a final summary explaining the image file counts and heuristic categories, including examples with inline file path references tagged at line 1 since these are binary files. I’ll break down counts like hash-like, IMG auto, and total meaningless names with their ratios, mention the ad-hoc script used, and suggest possible next steps for verifying flagged files. This will make the findings clear and structured for the user.

- Counted 865 image files under  and flagged 202 (~23%) as having meaningless/random names by scripting a few heuristics (hash-looking strings, timestamp-only names, camera defaults like IMG_1234, screenshot
    exports, WhatsApp auto names, and tokens with no vowels). Heuristics were implemented ad hoc via a Python scan of every image path.
- Breakdown of the **202 flagged filenames**:
  - 79 hash-like IDs (e.g. /assets/images/0552db0f-14a7-43e8-a7e5-80ec73e632a6.jpeg:1)
  -39 camera defaults such as IMG_… (e.g. /assets/images/IMG_8931-2-768x1024.png:1), 25 WhatsApp exports (/assets/images/WhatsApp-Image-2022-04-01-at-21.55.33-1024x576.jpeg:1)
  - 16 screenshots (/assets/images/Screenshot-2022-01-26-160522-
    1024x726.png:1
  -12 generic image_* names (/assets/images/image_2022-08-01_152115143-1024x769.png:1)
  - 8 DSC-style camera names (/assets/images/dsc_9495bw_sarah_hickson.jpg:1)
  - 8 pure timestamp/digit strings (/assets/images/15030006.jpg:1)
  - and 15 names with no vowels in any token (/assets/field-building-ddss.jpg:1). **This one seems fine. field-building-ddss is meaningful name. However, these can also be renamed just to keep it simple.**.
- The remaining 663 files have descriptive, human-readable names (e.g. /assets/images/tenzo-note-11.jpg:1). This count depends on the heuristics above—if you’d like the thresholds broadened or narrowed (e.g. treat plain image-of-x as meaningful), let me know and I can adjust the script.

## Substack 3: do the renaming of images

Given these ~ 202 images with bad files i want rename these. In fact, i think we may want to **rename many of the image files systematically (perhaps other than files with unsplash in their names)**

I suggest we rename based on the file name from which they are used e.g. if an image xxx.jpg used in blog/emergent-power.md we rename the image emergent-power-1.jpg (if there is image used in several files we can just use the first or last file - it doesn't matter).

This task should proceed in two steps. First, create a list of planned renamings. then once we have reviewed we'll do part 2. 

### Acceptance

Part 1

- [ ] Create list of planned renamings e.g. renamings.csv with the following columns: old_name, new_name, old_path, new_path
  - [ ] Create a list of all images
  - [ ] Search for the markdown files where they are used
  - [ ] Generate new image filename
  - [ ] Saved into renamings.csv
  
Part 2

renaming of images based on the planned renamings. (this probably needs a different command line option). This should assume that renamings.csv exists and is in the same directory as the script.

- [ ] Rename the images based on the planned renamings
- [ ] Go through all markdown files and replace the old image names with the new ones

NB: you don't have to do this in this exact order. whatever will work.

### Result

- Renamed 813 of the 865 images under assets/ using the plan in renamings.csv:1 (kept 52 descriptive names unchanged). Files were moved in two phases to avoid collisions, so every old_path now lives at its corresponding new_path.
- Updated 390 markdown files (897 references) so every ![](), <img>, image:/thumbnail: front‑matter entry, and Obsidian embed now points to the new filenames. For example, blog/art-of-impermanence-exhibition.md:7 and :19 now reference /
  assets/images/art-of-impermanence-exhibition-1.png and ![[art-of-impermanence-exhibition-1.png]], and second-renaissance.md:44–:46 now embed ![[second-renaissance-1.png]] etc.
- The seven .excalidraw.svg embeds noted earlier remain untouched (they live outside assets/), so no rename/update was attempted there; please decide whether to import those drawings or keep them as-is.
