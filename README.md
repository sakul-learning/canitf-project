# canitf project

A first-stab automation pipeline for tracking feature divergence between
[Terraform](https://github.com/hashicorp/terraform) and
[OpenTofu](https://github.com/opentofu/opentofu).

## Finding from cani.tf

[`cani.tf`](https://cani.tf/) already has a GitHub repo:
[`virtualroot/canitf`](https://github.com/virtualroot/canitf). Its source of
truth is a manually maintained `tools/tools.yaml`; `go run main.go` validates
and regenerates `data/tools.json` and the public `/tools.json` API. That is
useful to consume, but it is not a changelog extraction pipeline.

This repo implements Plan B: download official release notes/changelogs from
GitHub, extract candidate feature bullets, and build a repeatable comparison
table. It can optionally seed/merge the manually curated cani.tf table so human
curation and release-note discovery can coexist.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

# Fetch official GitHub releases. Set GITHUB_TOKEN to avoid low anonymous limits.
canitf fetch --out data/releases.json

# Build JSON + Markdown feature table from releases, optionally merging cani.tf.
canitf build-table \
  --input data/releases.json \
  --json-out data/features.json \
  --markdown-out data/feature-table.md \
  --include-canitf
```

## Current approach

1. `fetch` calls the GitHub Releases API for:
   - `hashicorp/terraform`
   - `opentofu/opentofu`
2. `build-table` extracts release-note bullets under feature-ish sections
   (`new`, `feature`, `enhancement`, `language`, `backend`, `provider`, etc.).
3. Each bullet is normalized into a stable-ish key.
4. The tool emits:
   - machine-readable JSON with source release URLs
   - a Markdown comparison table for quick review

This is intentionally conservative: it produces candidate feature rows with
source links, not a claim of perfect semantic equivalence. The next step should
be adding curated aliases/rules for known equivalent-but-differently-worded
features.

## Useful commands

```bash
canitf inspect-canitf
canitf fetch --per-page 30 --max-pages 2 --out data/releases.json
canitf build-table --input data/releases.json --markdown-out table.md
```

## Development

```bash
python -m unittest discover -s tests -v
```

## Repo status

This is a working initial scaffold: it fetches real official release data,
extracts candidate rows, merges existing cani.tf rows if requested, and has unit
tests for the parser/table builder. It is not yet a full semantic matching
system.
