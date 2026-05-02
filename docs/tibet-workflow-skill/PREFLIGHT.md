# Preflight Checklist

Before running the Tibet Workflow Skill, verify the following.

## Prerequisites

- [ ] Python **3.10+** installed
- [ ] `beautifulsoup4` installed: `pip install beautifulsoup4`
- [ ] `articles/` directory exists at Skill root (or will be created by `convert_articles_v2.py`)
- [ ] `AddingArticleWorkSpace/1/` directory contains source WeChat HTML files (for `--convert` / `--rebuild`)

## Built-in Validation

Run the following command to verify the Skill is healthy:

```bash
python scripts/build.py --validate
```

This executes three layers:

| Layer | Check | Script |
|-------|-------|--------|
| 1 | HTML structure validation | `validators.validate_all_articles()` |
| 2 | Bilingual consistency audit | `validators.audit_all_articles()` |
| 3 | Image-text distribution | `validators.check_all_distributions()` |

## Troubleshooting

### `ModuleNotFoundError: No module named 'lib'`

Ensure you are running scripts from the Skill root (`tibet-workflow-skill/`), or that `scripts/` is on `sys.path`. The scripts auto-inject `sys.path` when run directly.

### `FileNotFoundError: AddingArticleWorkSpace/1/...`

Place WeChat source HTML files into `AddingArticleWorkSpace/1/` before running `--convert` or `--rebuild`.

### Validation fails with "Image count mismatch"

Run `python scripts/sync_images.py` to auto-correct image counts and distribution.

### Validation fails with "Chinese in EN body"

Run `python scripts/rebuild_en.py --strict` to re-extract English content with a stricter Chinese-character filter.

### `articles/` directory missing

The `convert_articles_v2.py` script will create `articles/` automatically. If you only need validation, create it manually:

```bash
mkdir articles
```
