---
name: tibet-publish
description: >
  Publish WeChat Official Account articles to the TibetRide website (tibetride.com).
  Use when the user provides a WeChat article URL (mp.weixin.qq.com) and wants to
  deploy it to their website. Also use when the user asks to "publish an article",
  "deploy a WeChat article", "add a new article to the website", or mentions the
  TibetRide or TibetWeb publishing workflow. Handles the full pipeline from fetch
  through image download, HTML generation, bilingual template rendering, and git push.
---

# Tibet Publish Skill

Publish WeChat Official Account articles to the TibetRide website with one command.

## Quick Start

```bash
python scripts/pipeline.py --url "https://mp.weixin.qq.com/s/..."
```

The pipeline: clones/updates the website repo, fetches the WeChat article, downloads images, generates a bilingual page matching the website's design, and git pushes.

## Options

```bash
python scripts/pipeline.py --url "URL"                    # Full pipeline
python scripts/pipeline.py --url "URL" --skip-push        # Skip git push
python scripts/pipeline.py --url "URL" --slug my-article  # Custom slug
python scripts/pipeline.py --url "URL" --repo-path /path  # Use existing local repo
```

## Hardcoded Git Configuration

- **Remote**: `https://github.com/Lyndon25/TibetWeb.git`
- **Branch**: `main`

## Prerequisites

```bash
pip install requests beautifulsoup4 html2text pyyaml jinja2
```

## Pipeline Phases

| Phase | What happens |
|---|---|
| **FETCH** | Downloads WeChat article HTML, extracts metadata (title, author, cover), downloads images from WeChat CDN |
| **SAVE** | Writes localized HTML + original source HTML to workspace (`AddingArticleWorkSpace/1/`) |
| **BUILD** | `convert` (Jinja2 template rendering) -> `rebuild` (EN translation extraction) -> `sync` (image distribution) -> `validate` (HTML + bilingual audit) |
| **GIT** | `git add .` -> `git commit` -> `git push origin main` |

## Bundled Resources

- `scripts/pipeline.py` -- Single entry point
- `scripts/build.py` -- Build orchestrator
- `scripts/convert_articles_v2.py` -- Article HTML generation
- `scripts/rebuild_en.py` -- EN translation extraction
- `scripts/sync_images.py` -- Image synchronization
- `scripts/lib/` -- Shared modules (wechat_fetcher, git_manager, validators, etc.)
- `assets/templates/article.html` -- Jinja2 template matching tibetride.com
- `assets/css/main.css`, `assets/css/lang.css` -- Website stylesheets
- `assets/js/lang.js`, `assets/js/main.js` -- Language switching
- `assets/config/settings.yaml` -- Hardcoded config

## Important

- The pipeline pushes to `main` by default.
- On first run the pipeline seeds the website repo with CSS, JS, templates, and scripts.
- Images go to `images/articles/<slug>/` in the website repo.
- Rich WeChat formatting (bold, italics, links, line breaks) is preserved.
