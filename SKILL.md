---
name: tibet-publish
description: >
  Publish WeChat Official Account articles to the TibetRide website (tibetride.com).
  Use when the user provides a WeChat article URL (mp.weixin.qq.com) and wants to
  deploy it to their website. Also use when the user asks to "publish an article",
  "deploy a WeChat article", "add a new article to the website", or mentions the
  TibetRide or TibetWeb publishing workflow. Handles the full pipeline from fetch
  through image download, AI English translation, HTML generation, and git push.
---

# Tibet Publish Skill

Publish WeChat Official Account articles to the TibetRide website. All source articles are Chinese; English is generated via AI translation.

## Quick Start

```bash
python scripts/pipeline.py --url "https://mp.weixin.qq.com/s/..."
```

## Pipeline Phases

| Phase | What happens |
|---|---|
| **FETCH** | Downloads WeChat article HTML, extracts metadata, downloads images |
| **SAVE** | Writes source to workspace `AddingArticleWorkSpace/1/` |
| **BUILD** | `convert` generates Chinese article with EN placeholder |
| **TRANSLATE** | **AI agent translates Chinese content to English** |
| **INDEX** | Regenerates articles listing page via `generate_index.py` |
| **VALIDATE** | HTML + bilingual + image distribution checks |
| **GIT** | Commit and push to `claude-code-torch` |

## AI Translation Step (REQUIRED)

After the Chinese article HTML is generated:

1. Read the article at `articles/{slug}/index.html`
2. Extract Chinese text from `<div class="lang-content" data-lang="zh">` in the article body
3. Translate ALL text to natural English, preserving ALL HTML tags exactly
4. Translate the title from the hero section
5. Write English into `<div class="lang-content" data-lang="en">` sections
6. Update the `<title>` tag

**Rules:** Preserve HTML structure. Only translate text between tags. Keep img tags unchanged. Make English natural.

## Article Directory Structure

Articles live in `articles/{slug}/index.html` with co-located images in `articles/{slug}/images/`.

## Bilingual Pattern

- Block content: `<div class="lang-content" data-lang="zh">` / `<div class="lang-content" data-lang="en">`
- Inline text: `data-lang-zh` and `data-lang-en` attributes (swapped by `lang.js`)
- CSS (`lang.css`) handles visibility via `html[lang]` attribute

## Git Config
- Remote: `https://github.com/Lyndon25/TibetWeb.git`
- Branch: `claude-code-torch` (never push to main)

## Prerequisites
```bash
pip install requests beautifulsoup4 html2text pyyaml jinja2
```
