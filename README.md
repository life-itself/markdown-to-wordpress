Migrating existing https://lifeitself.org/ that is in markdown and published with Flowershow (self-hosted) - see https://github.com/life-itself/lifeitself.org - to a new Wordpress site at https://next.lifeitself.org (and soon lifeitself.org). More context in SCQH at bottom.

```
clean/     # analyse and clean up original markdown files
uploader/  # upload to wordpress. see node uploader/upload.js
e2e/       # integration tests (discarded)
wp-to-markdown  # convert wordpress content to markdown (for flowershow)
```

Generally:

- `PLAN.md` or `PLAN-xxx.md` are design / prompt documents
- `README.md` is usage of the tool (though sometimes this is consolidated when no tooling e.g. in [clean](clean))

Rest is self-explanatory e.g. `tests` etc.

## Meta-prompt

We're going to create description of an issue / prompt. Act like a world class product owner and spec provider. At the same time don't get *too* detailed. Keep it simple and concise and focus on what the needs are the key requirements/constraints around that. Remember KISS: we want to keep it simple and straightforward and not over-engineer it.

To prepare task descriptions in the requested format, use these instructions:

1.  **Structure:** Always include these three sections:
    * **Title**: a descriptive title that captures the essence of the issue or prompt.
    * **Description**: this section does not need a a heading and should be the first paragraph or paragraphs in the response
    * **Acceptance Criteria**: in a section with h2 heading `Acceptance`
    * **Notes**: any notes on implementation details or considerations derived from the user's request. (please don't add. i will ask if i want suggestions.)
2.  **Content:**
    * Keep all sections **clear and concise**.
    * **Do not** generate full code, detailed specifications, or extensive commentary on *how* to implement the task. (unless i provided it myself)
