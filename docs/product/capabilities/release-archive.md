# Release archive

Pack **git HEAD** plus a filtered ideas org slice into one `.tar.gz` for handoff
installs (SPEC-0133).

## Commands

```bash
wt release-archive
wt release-archive -o /tmp/wt.tgz --project Meta-Tools
wt release-archive --no-all          # omit done/archived ideas from the slice
```

Default output path is beside the repo: `../work-tracking-YYYYMMDD-<sha>.tar.gz`.
Project filter defaults to Meta-Tools for the ideas slice.
