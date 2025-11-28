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
