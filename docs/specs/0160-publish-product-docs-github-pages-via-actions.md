---
id: SPEC-0160
title: "Publish product docs to GitHub Pages via Actions"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
tags: [docs, ci, github-pages]
depends_on: [SPEC-0143]
---

## Context

Follow-on to [SPEC-0143](./0143-mkdocs-material-docs-site-toolchain.md) (which
shipped local `mkdocs build --strict` / `scripts/docs-serve.sh` and deferred
GitHub Pages). The repo `origin` is `brunosmmm/wt`; product docs need a durable
public URL without hand-running `mkdocs gh-deploy`. Not attached as a child of
done epic SPEC-0141 so the epic ledger stays closed.

## Goals / Non-goals

**Goals**

- On push to `main` (and manual `workflow_dispatch`), GitHub Actions builds the
  MkDocs site strictly and deploys `site/` to **GitHub Pages**.
- `mkdocs.yml` declares `site_url` for the Pages URL so absolute links resolve.
- A small automated test pins the workflow file’s existence and critical keys.

**Non-goals**

- Cloudflare / Netlify / custom domain DNS (can follow later).
- Regenerating SVG captures inside CI (committed assets stay the source of truth
  per SPEC-0149).
- Full pytest in this workflow (docs publish stays fast; other CI can stay separate).

## Decision

Use the official **Actions → Pages** path (`actions/upload-pages-artifact` +
`actions/deploy-pages`), not `mkdocs gh-deploy` / force-push to `gh-pages`.
Build with `uv sync` + `uv run mkdocs build --strict` so the toolchain matches
local/dev.

## Design

Shipped:

- `.github/workflows/docs-pages.yml` — `push`/`workflow_dispatch` → `uv sync
  --frozen --group dev` → `mkdocs build --strict` → upload `site/` →
  `actions/deploy-pages` under environment `github-pages`.
- `mkdocs.yml`: `site_url: https://brunosmmm.github.io/wt/`
- `tests/test_docs_pages_workflow.py` pins workflow + `site_url`.
- Operator once: GitHub → Settings → Pages → Source = **GitHub Actions**.

## Alternatives considered

- **`mkdocs gh-deploy`** — rejected: orphan `gh-pages` branch; Actions artifact
  deploy is the GitHub-recommended path and matches “via actions”.
- **Cloudflare Pages** — deferred.

## Acceptance criteria

- [x] `.github/workflows/docs-pages.yml` builds with `mkdocs build --strict` and
      deploys via `actions/deploy-pages`.
- [x] `mkdocs.yml` sets `site_url` to `https://brunosmmm.github.io/wt/`.
- [x] Automated test asserts the workflow file exists and mentions
      `deploy-pages` + `mkdocs build --strict`.
- [x] `python3 tools/spec_lint.py` clean; ledger lists SPEC-0160.

## Test plan

- **Automated:** `tests/test_docs_pages_workflow.py` + existing
  `tests/test_docs_mkdocs_build.py`. Executed 2026-09-09.
- **Manual:** After first push, set Pages source to GitHub Actions if needed;
  confirm Actions run and `https://brunosmmm.github.io/wt/`.
- **Regression:** capture script unchanged; product Markdown unchanged beyond
  `site_url`.

## Rollout / migration

1. Land workflow + `site_url` + test (this change).
2. In GitHub → Settings → Pages → Source: **GitHub Actions**.
3. Push / re-run workflow; confirm the Pages URL.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; docs tests green.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- None — Pages source toggle is an operator step after the first workflow lands.
