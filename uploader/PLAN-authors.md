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
