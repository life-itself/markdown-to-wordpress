# Tasks

## Task 1: Research

I want to investigate how to set authors on the lifeitself blog on wordpress. these aren't see using normal wordpress user info, instead we use a reference special node type (coming from PODs system)

I want you to first access wordpress rest api and retrieve the metadata for the post here

https://next.lifeitself.org/blog/second-renaissance-name-why/

please create a small separate script investigate-api-for-pods.js in uploader in node.

Use the standard .env structure for getting credentials (see the README.md in that folder). 

Then let's run this script get the output. Then you can update this PLAN-authors.md file with the information you find.

## Investigation output

See 

```
$ node investigate-api-for-pods.js second-renaissance-name-why
```

See uploader/api-output/second-renaissance-name-why.json

This shows there is an authors array:

```
  "authors": [
    {
      "job_title": "Technologist and Co-founder",
      "posts": [
        91,
        237,
        376,
        381
      ],
      "residencies": [
        16
      ],
      "initiatives": [
        177,
        244,
        248
      ],
      "ID": 103,
      "post_title": "Rufus Pollock",
...
```

## Task 2: Try out seting an Author on a post

Given the context in [@PLAN-authors.md](file:///Users/rgrp/src/lifeitself/markdown-to-wordpress/uploader/PLAN-authors.md)  draft the outline for this Task 2 which is to try out how we set the author.

I suspect first we have 2 substacks:

- [ ] 1. find author/team member ids. e.g. query posts in wordpress api and try and find the posts with the node type for team members / authors. Once we have that. we can get their ids.
- [x] 2. use those author ids to experiment with how we set the authors on the wordpress api e.g. by setting the authors array with ids in the objects in that array e.g. 

Right now i suggest we jump to step 2 straight away by creating an initial authors list based on the info in `investigating-api-for-pods.js`. We can:

1. extract the list of author ids there.
2. use that structure to guess how we set the elevant fields in the wordpress rest api call to create a post.

### Acceptance

By investigating the structure of `investigating-api-for-pods.js` and what you can find about wordpress API ... create a unit test that calls the wordpress api to create a post with an author.

- [x] A unit test that calls the wordpress api to create a post with an author
  - [x] Can load env config for wordpress access as e2e tests do
- [x] A mocked up list of author (ids) (can be directly in the test file)
- [x] A sample payload then using those authors to create a post on wordpress

### Notes on the test payload

- Added `tests/authors.e2e.test.js` which loads `.env.test` (matching the upload e2e test) to create a WP client.
- Uses mocked author IDs pulled from the investigation output (`103` Rufus Pollock, `107` Sylvie Barbier) and submits them as the `authors` array.
- Posts to slug `wpapi-author-e2e-test` with a simple draft payload plus placeholder `meta.raw_markdown`, then re-fetches the post and asserts the returned `authors` list contains the mocked IDs.

## Task 3: get a list of all author names used in local markdown repo

Scan all markdown posts in `next.lifeitself.org` (excluding `people/`), extract unique author IDs from `author`/`authors` front matter, resolve each ID to a full name via the matching file in `people`, and print `id name` pairs. (if no match in people print out the id anyway). (don't bother listing items in people where id not used in any posts).

### Acceptance

- [ ] Traverse markdown posts under `next.lifeitself.org` except `people/`.
- [ ] Extracts `author`/`authors` values, handles string or array, and de-dupes IDs.
- [ ] Reads corresponding `people/<id>.md` (or equivalent) to obtain full names.
- [ ] Outputs a simple json file in file specified in `--authors` defaulting to `authors.json`
  - [ ] key is `id` of author and value is an object with `name` key (which can be empty if not found)
  - [ ] Also compute `posts_count` and `pages_count` for each author (posts being markdown posts in blog directory and pages everything else) and add these.

### Notes

Added list-local-authors.js to scan next.lifeitself.org markdown (excluding people/), extract/de-dupe author/authors front matter, resolve names from matching people/<id>.md, and flag missing or name-less entries.

## Task 4: get a list of all the authors and their names and ids from wordpress (so that we can use that when we set authors when doing uploading - see PLAN.md)

We want to try and find the list of authors or team members that are defined on our WordPress website.
It's using the Pods system for creating custom node or post types.

First, we want to understand how Pods identifies posts which are a certain node type, in this case, like team node type. I want to then get a list of all team members and their IDs. For example, the people I know who are currently in the team, Valerie Duchauvelle, Liam Kavanagh, Rufus Pollock and Sylvie Barbier, just as a hint.

I want to work out from the rest API. I want to first work out how I find posts of that post type and then I want to get the kind of IDs or the author IDs associated to them so that I can use that when I set the authors the rest of the context in this issue.

Basically, I think you want to write a script. My guess is to query the rest of the API to get all the posts because there aren't that many. Then try and work out which ones are to do with these team author members. Then extract that list and look at how to get the author IDs and then print that out.

- You can use the outputs I've already gotten in the research directory from doing this work to help you do this.
- We are doing research so store scripts and outputs in `research` subdirectory.

### Acceptance

- [x] Create a script to do this in `research`
- [x] Dump some sample output in `research`
- [x] Produce a list of author names and their IDs (from wordpress) in a txt file called e.g. `wordpress-authors.txt`

### Outputs

> Question: should I also query a specific Pods/custom post type (e.g., a “team”/“people” post type) to capture members not currently attached to posts?

Yes, please do that. In fact, let's focus on that. i.e. searching by that post type - if there is a way to do that.

- Added research/list-wordpress-team.js to discover relevant custom types (team/people/author/pod markers), fetch their entries via the WP REST API, and write outputs.
- Generated research/wordpress-team-authors.txt (TSV) and research/wordpress-team-authors.json (types + entries). Current Team entries:
    - 124 Boaz B. Feldman (boaz-b-feldman) — Deliberately Developmental Space Researcher
    - 128 Catherine Tran (catherine-tran) — Generalist / Researcher
    - 132 Lauren Wigmore (lauren-wigmore) — Communications
    - 826 Liam Kavanagh (liam-kavanagh) — Researcher and Co-founder
    - 136 Nathen Fitchen (nathen-fitchen) — Communications
    - 103 Rufus Pollock (rufus-pollock) — Technologist and Co-founder
    - 107 Sylvie Barbier (sylvie-barbier) — Artist and Co-founder
    - 829 Valerie Duvauchelle (valerie-duvauchelle) — Conscious Food Designer

Files: research/list-wordpress-team.js, research/wordpress-team-authors.txt, research/wordpress-team-authors.json.

## Task 5: Add WordPress IDs and Names to authors.json

Ok, now go through research/authors.json and use the data in research/wordpress-team-authors.json to add `wordpress_id` and `wordpress_name` wherever you can. So if you have an exact or close match on id or name between value in authors.json and that in wordpress-team-authors you can add the worpress stuff based on info in wordpress-team-authors.json

## ✅ Task 6: refactor to be called people.js

rename uploadPerson.js to people.js and switch that first argument is a command and current action of uploading from markdown is called create

## ✅ Task 7: refactor to multiple commands.

OK, we want to make changes from where we are now ...

We want to consolidate much of the above into the `upload.js` command.

- [ ] We can to create a command on `people listlocal` that creates the authors.json as per task 3 above (note we already have `list-local-authors.js` that does quite a bit of this)
- [ ] Then we want a command called `people mergeremote` which consolidates task 4 and task 5 above into a single command that updates the existing `authors.json` with `wordpress_id` and `wordpress_name` from remote. you can use existing work from `list-wordpress-team.js`
- [ ] Create a `people` command like `node upload.js people build --mapping ../sandbox/mediamap-staging.json --authors authors.json "next.lifeitself.org/people` that builds the `authors.json` from scratch e.g. internally does in order `people listlocal`, then `people mergeremote` then `peoplecreate` (logging status as it goes at each step ...)
