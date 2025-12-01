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
