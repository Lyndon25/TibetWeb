# Tibet Workflow Skill

TibetJourneyWebsite content publishing workflow — an Agent Skill for generating, rebuilding, syncing, and validating bilingual (ZH/EN) travel articles.

## Quick Start

```bash
# 1. Install dependency
pip install beautifulsoup4

# 2. Full pipeline (convert → rebuild EN → sync images → validate)
python scripts/build.py --all

# 3. Run validation only
python scripts/build.py --validate

# 4. Process a single article
python scripts/build.py --convert --slug 2026-tibet-year-round-travel-guide
```

## Directory Structure

```
tibet-workflow-skill/
├── scripts/
│   ├── build.py                    # Unified build entry point
│   ├── convert_articles_v2.py      # Generate articles from WeChat source HTML
│   ├── rebuild_en.py               # Rebuild English content from source files
│   ├── sync_images.py              # Sync ZH/EN body images
│   ├── validate_html.py            # HTML structure validation
│   ├── deep_audit.py               # Bilingual consistency audit
│   ├── scan_image_text_separation.py # Image-text separation check
│   ├── lib/                        # Shared libraries
│   │   ├── __init__.py
│   │   ├── html_parser.py          # Stack-based HTML block extraction
│   │   ├── atomic_io.py            # Atomic file writes with rollback
│   │   ├── article_config.py       # Article metadata loader
│   │   ├── en_extractor.py         # EN extraction from WeChat HTML/MD
│   │   └── validators.py           # Three-layer validation suite
│   └── archive/                    # Legacy scripts (reference only)
├── skill.json                      # Skill metadata
├── README.md                       # This file
└── PREFLIGHT.md                    # Prerequisites & troubleshooting
```

## Core Scripts

### `scripts/build.py`

Unified pipeline. Supports running individual phases or the full workflow.

```bash
python scripts/build.py --all
python scripts/build.py --convert --rebuild --sync
python scripts/build.py --validate
python scripts/build.py --slug <slug>
```

### `scripts/convert_articles_v2.py`

Generates `articles/<slug>.html` from WeChat source HTML in `AddingArticleWorkSpace/1/`.

```bash
python scripts/convert_articles_v2.py
```

### `scripts/rebuild_en.py`

Extracts English translations from source files and injects them into existing articles.

```bash
python scripts/rebuild_en.py           # All articles
python scripts/rebuild_en.py --strict  # Apply strict Chinese filter
python scripts/rebuild_en.py --slug <slug>
```

### `scripts/sync_images.py`

Synchronizes image counts between ZH and EN body blocks, and fixes proportional distribution.

```bash
python scripts/sync_images.py                  # Full sync + redistribution
python scripts/sync_images.py --no-fix-distribution  # Count sync only
python scripts/sync_images.py --slug <slug>
```

### `scripts/validate_html.py`

Runs Layer 1 (HTML structure) validation across all `articles/*.html`.

```bash
python scripts/validate_html.py
```

### `scripts/deep_audit.py`

Runs Layer 2 (bilingual consistency) audit and writes results to `scripts/deep_audit_results.txt`.

```bash
python scripts/deep_audit.py
```

### `scripts/scan_image_text_separation.py`

Runs Layer 3 (image-text distribution) check on EN body blocks.

```bash
python scripts/scan_image_text_separation.py
```

## Git Workflow

```bash
cd tibet-workflow-skill

# Stage changes
git add .

# Commit
git commit -m "feat: update articles via tibet-workflow-skill"

# Push to origin
git push origin main
```

## Notes

- The Skill expects `articles/` and `AddingArticleWorkSpace/1/` to exist at the Skill root.
- All paths are resolved dynamically from `__file__` / `sys.argv[0]`, so the Skill is relocatable.
