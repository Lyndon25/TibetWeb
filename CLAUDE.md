# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TibetRide (tibetride.com) is a bilingual (zh/en) static tourism website for Tibet small-group tours. Deployed on Vercel. No JS framework — pure HTML/CSS/JS with Python scripts for the content pipeline.

## Build & Development

```bash
# Full content pipeline (convert → rebuild → sync → validate)
python scripts/build.py --all

# Single article (from WeChat source HTML)
python scripts/build.py --convert --slug <slug>

# Validate only
python scripts/build.py --validate

# Publish a WeChat article end-to-end (fetch → config → build → git push)
python scripts/tibet_publish.py --url https://mp.weixin.qq.com/s/...

# Publish without pushing to git
python scripts/tibet_publish.py --url <URL> --skip-push
```

There is no local dev server, no bundler, no test suite. The site is a set of static `.html` files served by Vercel with one Python serverless function at `api/contact.py`.

## Bilingual Pattern

The entire site supports zh-CN and EN via a `html[lang]` CSS toggle and data attributes:

- **Block-level content**: Wrap zh and en versions in `<div class="lang-content" data-lang="zh">` and `<div class="lang-content" data-lang="en">`. CSS hides the inactive language based on `html[lang]`.
- **Inline text**: Use `data-lang-zh` and `data-lang-en` attributes on any element. `lang.js` swaps `textContent` at runtime.
- **Language switcher**: Injected by `lang.js` into `.nav__inner` on DOMContentLoaded. Defaults to `zh`; stored in `localStorage` key `site-lang`.
- **Script order matters**: Load `main.js` before `lang.js` in `<body>`.

## Directory Map

| Directory | Purpose |
|-----------|---------|
| `/` (root `.html`) | Core pages: `index`, `about`, `contact`, `customize`, `routes` |
| `articles/` | Generated article `.html` files, one per article slug |
| `tours/` | Tour detail pages (`lhasa-5-days.html`, etc.) + tour listing `index.html` |
| `templates/` | `article.html` — Jinja2-style template with `{{ var }}` syntax, used by `build.py` |
| `config/` | `articles.yaml` (article metadata), `tours.yaml` (full bilingual tour data) |
| `api/` | `contact.py` — Vercel serverless function: writes to Feishu Bitable + sends Feishu bot notification via webhook |
| `scripts/` | Content pipeline scripts (see below) |
| `scripts/lib/` | Shared Python modules for the pipeline |
| `css/` | `main.css` (styling), `lang.css` (bilingual toggle styles) |
| `js/` | `main.js` (nav, scroll animations), `lang.js` (language switching) |
| `images/` | Static images for the site |

## Content Pipeline (`scripts/`)

**Orchestrators**: `build.py` (content phases) and `tibet_publish.py` (full WeChat→deploy pipeline).

`build.py` runs four ordered phases:
1. `--convert` → `convert_articles_v2.py` — generates article HTML from WeChat source files in `AddingArticleWorkSpace/`
2. `--rebuild` → `rebuild_en.py` — extracts EN translations from source
3. `--sync` → `sync_images.py` — syncs and distributes images across zh/en article bodies
4. `--validate` → `validate_html.py` + `deep_audit.py` + `scan_image_text_separation.py` — HTML structure, bilingual consistency, image distribution checks

**Library modules** (`scripts/lib/`):
- `wechat_fetcher.py` — fetch and parse WeChat articles, download images
- `html_parser.py` — parse/manipulate article HTML
- `en_extractor.py` — extract English translations from source files
- `validators.py` — HTML validation, bilingual audit, image distribution checks
- `git_manager.py` — git add/commit/push wrappers
- `yaml_updater.py` — read/write `config/articles.yaml`
- `article_config.py` — article metadata helpers
- `image_downloader.py` — download images to local storage
- `atomic_io.py` — atomic file writes

## API (`api/contact.py`)

Vercel Python serverless function. Handles POST from the contact/booking form. Validates fields (name, email, travel_date, travelers), writes the inquiry to a Feishu Bitable record, and sends an interactive card notification to a Feishu group bot via webhook. All Feishu credentials come from Vercel environment variables (`FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_APP_TOKEN`, `FEISHU_TABLE_ID`, `FEISHU_WEBHOOK`).

## Article Template (`templates/article.html`)

Uses `{{ var }}` syntax for template variables. Key variables:
- `title.zh`, `title.en` — bilingual title object
- `body_zh`, `body_en` — full HTML article body per language
- `cover` — hero background image URL
- `author.zh`, `date`, `catLabel`, `catLabelZh`
- `nav_html` — optional in-article navigation
- `related_html` — sidebar related articles HTML

## Tours Config (`config/tours.yaml`)

Each tour under `tours:` has these key fields: `slug`, `name`/`nameZh`, `duration`, `startingPrice`, `maxGroupSize`, `highlights[]`, `itinerary[]` (day-by-day with bilingual title/desc), `inclusions`/`inclusionsZh`, `exclusions`/`exclusionsZh`, `pricing[]`, `faq[]` (with bilingual q/a), `metaTitle`, `metaDescription`.

## Vercel Routing (`vercel.json`)

Clean URL rewrites: `/tours` → `/tours/index.html`, `/articles` → `/articles/index.html`, `/about` → `/about.html`, `/contact` → `/customize.html`. API routes under `/api/*` routed to serverless functions. Long cache lifetimes on CSS/JS/images.

## Key Conventions

- Article file names use the Chinese title as the file pattern (e.g., `西藏自驾全境全览上篇川藏线G318进藏拉萨及周边.html`), slug is a shorter hyphenated form.
- `AddingArticleWorkSpace/` is gitignored; it's the staging area for fetched WeChat articles before processing.
- No external Python dependencies in production (requirements.txt is empty — only stdlib used in `api/contact.py`). Scripts may use `bs4`, `html2text`, `yaml` locally.
