#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert WeChat-style HTML articles to standard Tibet Moto Travel article format v3.

Improvements over v2:
- Jinja2 template rendering (no more hard-coded f-string)
- Local image downloading (WeChat CDN -> local storage)
- Enhanced content filtering (removes ads, follow prompts, unrelated WeChat noise)
- Preserves copyright captions (Photo by, 图源, etc.)
- Supports list extraction (ul/ol/li)
- Attempts EN translation extraction during initial generation
"""

import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import NavigableString

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

from lib import article_config, image_downloader, en_extractor, atomic_io

# ---------------------------------------------------------------------------
# Jinja2 setup (optional dependency)
# ---------------------------------------------------------------------------
try:
    from jinja2 import Environment, FileSystemLoader
    _HAS_JINJA = True
except ImportError:
    _HAS_JINJA = False
    print("WARNING: jinja2 not installed. Falling back to basic string.Template.")

# ---------------------------------------------------------------------------
# Content filtering patterns
# ---------------------------------------------------------------------------

# Caption patterns: preserve these as image captions (copyright info)
CAPTION_PATTERNS = re.compile(
    r'\u56fe\u6e90|\u6444|\u6765\u6e90|\u6444\u5f71\u5e08|Photo by|photographer|Image by|\u00a9|\u7248\u6743|'
    r'\u00a9|\u5c0f\u7ea2\u4e66|@.*?\u6444\u5f71|.*?\u62cd\u6444|\u89c6\u89c9\u4e2d\u56fd|Getty|Unsplash|Pexels',
    re.I,
)

# Skip patterns: remove these as WeChat noise (ads, prompts, etc.)
SKIP_PATTERNS = re.compile(
    r'^(\u4f7f\u7528\u5b8c\u6574\u670d\u52a1|\u53bb\u9605\u8bfb|\u5728\u5c0f\u8bf4\u9605\u8bfb\u5668\u8bfb\u672c\u7ae0|\u5fae\u4fe1\u626b\u4e00\u626b|\u5173\u6ce8\u8be5\u516c\u4f17\u53f7|'
    r'\u9605\u8bfb\u539f\u6587|\u9884\u89c8\u65f6\u6807\u7b7e\u4e0d\u53ef\u70b9|\u70b9\u51fb.*?(\u5173\u6ce8|\u9605\u8bfb)|.*?\u626b\u7801.*?\u5173\u6ce8|'
    r'.*?\u957f\u6309.*?\u8bc6\u522b|.*?\u4e8c\u7ef4\u7801|.*?\u5c0f\u7a0b\u5e8f|\u5f80\u671f\u63a8\u8350|\u76f8\u5173\u9605\u8bfb|'
    r'\u7cbe\u9009\u7559\u8a00|\u5199\u7559\u8a00|\u8d5e\u8d4f|\u559c\u6b22\u4f5c\u8005|\u5206\u4eab|\u6536\u85cf|\u5728\u770b|'
    r'\u5e7f\u544a\u6295\u653e|\u5546\u52a1\u5408\u4f5c|\u8054\u7cfb.*?\u5fae\u4fe1|.*?\u516c\u4f17\u53f7|'
    r'\u70b9\u51fb\u4e0b\u65b9|\u6233\u8fd9\u91cc|\u6233.*?\u9605\u8bfb\u539f\u6587|'
    r'\u672c\u6587.*?\u7f16\u8f91|\u672c\u6587.*?\u6765\u6e90|\u8d23\u4efb\u7f16\u8f91|\u5ba1\u7a3f|\u6392\u7248|'
    r'^\u9884\u8ba2\u70ed\u7ebf|^\u5fae\u4fe1\u53f7|^\u5fae\u4fe1\u53f7\u7801|'
    r'^\u5173\u6ce8.*?\u516c\u4f17\u53f7|^\u5173\u6ce8.*?\u5fae\u4fe1)$|'
    r'^\u25b2.*$|'
    r'\u7559\u8a00\u5206\u4eab|\u540e\u53f0\u7559\u8a00|\u968f\u65f6\u95ee\u6211|\u7ed3\u4f34\u540c\u884c|'
    r'^\u9884\u8ba2$|^Booking$|'
    r'^AD[\uff1a:]|^\u5e7f\u544a[\uff1a:]|'
    r'^PS[\uff1a:]|^P\.S[\uff1a:.]|'
    r'^Sharing the spring moments|^Share your moments',
    re.I,
)

# WeChat element selectors to remove entirely
WECHAT_NOISE_SELECTORS = [
    'mpvoice',           # Voice messages
    'iframe',            # Embedded iframes
    'qqmusic',           # QQ music
    'span[data-weui-...]',  # WeUI components
    'div[class*="ad_"]',    # Ad containers
    'div[class*="sponsor"]', # Sponsor content
    'div[style*="display:none"]', # Hidden elements
    'div[role="dialog"]',     # Dialogs/popups
    'img[data-ratio="0"]',    # Placeholder images (often ads)
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_date(date_str: str) -> str:
    """Convert ISO date (2026-05-11) to human-readable format (May 11, 2026)."""
    if not date_str:
        return ''
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except ValueError:
        return date_str


def clean_text(text: str) -> str:
    """Clean text content from WeChat artifacts."""
    if not text:
        return ''
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\ufeff', '')
    # Normalize spaces
    text = text.replace('\xa0', ' ').replace('\u3000', ' ')
    # Collapse whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def extract_paragraph_html(elem) -> str:
    """
    Extract paragraph content preserving inline formatting (br, strong, b, em, i)
    while stripping WeChat noise (span, font wrappers).
    Returns HTML string safe for embedding in <p> tags.
    """
    from bs4 import NavigableString
    from copy import copy

    # Clone the element so we can modify it
    soup = copy(elem)

    # Remove WeChat noise elements from the clone
    for tag in soup.find_all(['mpvoice', 'iframe', 'qqmusic']):
        tag.decompose()
    for tag in soup.find_all(style=lambda v: v and ('display:none' in v or 'visibility:hidden' in v)):
        tag.decompose()

    # Unwrap span/font tags (keep their content, remove the wrapper)
    for tag_name in ['span', 'font']:
        for tag in soup.find_all(tag_name):
            tag.unwrap()

    # Convert br tags to self-closing form
    for br in soup.find_all('br'):
        br.replace_with('\n')

    # Get HTML, then clean up
    # Use decode_contents to get only inner HTML (no outer <p>)
    inner = ''
    for child in soup.children:
        if isinstance(child, NavigableString):
            inner += str(child)
        elif hasattr(child, 'name'):
            if child.name in ('strong', 'b', 'em', 'i', 'a'):
                inner += str(child)
            elif child.name == 'br':
                inner += '\n'
            else:
                inner += child.get_text()

    # Clean up the text
    inner = inner.replace('\u200b', '').replace('\ufeff', '')
    inner = inner.replace('\xa0', ' ').replace('\u3000', ' ')
    # Remove WeChat-specific inline styles
    inner = re.sub(r'\s*style="[^"]*mso-[^"]*"', '', inner)
    inner = re.sub(r'\n{3,}', '\n\n', inner)
    inner = inner.strip()

    return inner


def should_skip(text: str) -> bool:
    """Check if text should be skipped as WeChat noise."""
    text = text.strip()
    if not text:
        return True
    if text in ('', ' ', '\n', '•', '·'):
        return True
    if SKIP_PATTERNS.search(text):
        return True
    # Skip pure whitespace lines
    if re.match(r'^[\s\u200b\xa0]+$', text):
        return True
    return False


def is_caption(text: str) -> bool:
    """Check if text is an image caption (copyright info)."""
    text = text.strip()
    if len(text) < 3 or len(text) > 120:
        return False
    return bool(CAPTION_PATTERNS.search(text))


def _cleanup_html(html: str) -> str:
    """Post-process generated HTML to remove noise that survived block extraction."""
    # Remove empty paragraphs (including those with only whitespace entities)
    html = re.sub(r'<p>\s*</p>\n?', '', html)
    html = re.sub(r'<p><strong>\s*</strong></p>\n?', '', html)
    html = re.sub(r'<p><strong>\s*<br/?>\s*</strong></p>\n?', '', html)

    # Remove WeChat link cards split across tags: [text\n](url)
    html = re.sub(r'<p>\s*\[\s*[^<]*\s*</p>\n?', '', html)
    html = re.sub(r'<p>\s*\].*?</p>\n?', '', html)

    # Remove standalone links to mp.weixin.qq.com (WeChat article cards)
    html = re.sub(
        r'<p>\s*<a[^>]*href="https?://mp\.weixin\.qq\.com[^"]*"[^>]*>.*?</a>\s*</p>\n?',
        '', html
    )
    html = re.sub(
        r'<p>\s*https?://mp\.weixin\.qq\.com\S*\s*</p>\n?',
        '', html
    )

    # Remove phone/WeChat contact info lines (promotional)
    html = re.sub(
        r'<p[^>]*>\s*(?:<strong>)?\s*(?:预订热线|热线|电话|微信号|微信)[：:]\s*\d[\d\s-]{6,}\s*(?:</strong>)?\s*</p>\n?',
        '', html
    )

    # Collapse consecutive empty lines
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html


def is_ad_or_noise(elem) -> bool:
    """Check if an element is likely an ad or WeChat noise."""
    # Check style for common ad indicators
    style = elem.get('style', '')
    if 'display:none' in style or 'visibility:hidden' in style:
        return True

    # Check class names
    cls = ' '.join(elem.get('class', []))
    noise_keywords = ['ad_', 'sponsor', 'promote', 'banner', 'popup', 'dialog']
    for kw in noise_keywords:
        if kw in cls.lower():
            return True

    # Check for tracking/minimal images
    if elem.name == 'img':
        width = elem.get('data-w') or elem.get('width', '')
        height = elem.get('data-ratio') or elem.get('height', '')
        try:
            if int(width) < 10 or int(height) < 10:
                return True
        except (ValueError, TypeError):
            pass

    return False


# ---------------------------------------------------------------------------
# Block extraction
# ---------------------------------------------------------------------------

def extract_blocks(soup) -> list[tuple[str, str]]:
    """
    Extract content blocks from WeChat HTML.
    Returns list of (type, content) tuples.
    Types: 'img', 'h2', 'h3', 'p', 'caption', 'strong', 'list'
    """
    content_div = soup.find('div', class_='rich_media_content') or soup.find(id='js_content')
    if not content_div:
        content_div = soup.body if soup.body else soup

    # Remove WeChat noise elements before processing
    for selector in WECHAT_NOISE_SELECTORS:
        try:
            for bad in content_div.select(selector):
                bad.decompose()
        except Exception:
            pass

    blocks = []
    elements = list(content_div.descendants)

    i = 0
    while i < len(elements):
        elem = elements[i]
        if isinstance(elem, NavigableString):
            i += 1
            continue

        if is_ad_or_noise(elem):
            i += 1
            continue

        if elem.name == 'img':
            src = elem.get('data-src') or elem.get('src')
            if src and src.startswith('http'):
                # Skip tiny/placeholder images
                data_w = elem.get('data-w', '')
                try:
                    if data_w and int(data_w) < 50:
                        i += 1
                        continue
                except ValueError:
                    pass
                blocks.append(('img', src))
            i += 1
            continue

        if elem.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = clean_text(elem.get_text())
            if text and not should_skip(text):
                if len(text) <= 30:
                    blocks.append(('h2', text))
                else:
                    blocks.append(('h3', text))
            i += 1
            continue

        if elem.name == 'p':
            plain_text = clean_text(elem.get_text())
            if not plain_text or should_skip(plain_text):
                i += 1
                continue

            # Use rich extraction that preserves inline formatting (br, strong, em)
            para_html = extract_paragraph_html(elem)

            # Check if this is a caption for previous image
            if blocks and blocks[-1][0] == 'img' and is_caption(plain_text):
                blocks.append(('caption', plain_text))
                i += 1
                continue

            # Check if strong/b only
            strong_children = elem.find_all(['strong', 'b'])
            non_empty_children = [
                c for c in elem.children
                if not isinstance(c, NavigableString) or str(c).strip()
            ]
            if (strong_children and len(strong_children) == len(non_empty_children)
                    and len(plain_text) < 80):
                blocks.append(('strong', plain_text))
                i += 1
                continue

            blocks.append(('p', para_html if para_html else plain_text))
            i += 1
            continue

        if elem.name in ('ul', 'ol'):
            items = []
            for li in elem.find_all('li', recursive=False):
                li_text = clean_text(li.get_text())
                if li_text and not should_skip(li_text):
                    items.append(li_text)
            if items:
                blocks.append(('list', '\n'.join(items)))
            i += 1
            continue

        # Skip section/div wrappers that don't add content
        i += 1

    return blocks


def merge_paragraphs(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Merge short consecutive paragraphs into single paragraphs."""
    merged = []
    buffer = []

    for btype, content in blocks:
        if btype == 'img':
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype == 'caption':
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype in ('h2', 'h3', 'strong', 'list'):
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype == 'p':
            # Check if this is very short - merge into buffer
            if (len(content) < 20
                    and not content.endswith('\u3002')
                    and not content.endswith('\uff01')
                    and not content.endswith('\uff1f')
                    and not content.endswith('.')):
                buffer.append(content)
            else:
                if buffer:
                    buffer.append(content)
                    merged.append(('p', ' '.join(buffer)))
                    buffer = []
                else:
                    merged.append((btype, content))

    if buffer:
        merged.append(('p', ' '.join(buffer)))

    return merged


def render_blocks(blocks: list[tuple[str, str]], img_mapping: dict[str, str] | None = None) -> str:
    """Render blocks to HTML with optional image URL replacement."""
    parts = []
    for btype, content in blocks:
        if btype == 'img':
            src = content
            if img_mapping and src in img_mapping:
                src = img_mapping[src]
            parts.append(f'<img src="{src}" alt="" loading="lazy">')
        elif btype == 'caption':
            parts.append(f'<p class="caption">{content}</p>')
        elif btype == 'h2':
            parts.append(f'<h2>{content}</h2>')
        elif btype == 'h3':
            parts.append(f'<h3>{content}</h3>')
        elif btype == 'strong':
            parts.append(f'<p><strong>{content}</strong></p>')
        elif btype == 'list':
            items = [f'<li>{item}</li>' for item in content.split('\n')]
            parts.append(f'<ul>\n' + '\n'.join(items) + '\n</ul>')
        elif btype == 'p':
            parts.append(f'<p>{content}</p>')
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Related articles
# ---------------------------------------------------------------------------

def build_related_html(article: dict, all_articles: list[dict]) -> str:
    """Build related articles HTML from config."""
    related = article_config.get_related_articles(article, all_articles)
    if not related:
        # Fallback: pick articles from same category
        cat = article.get('category', '')
        related = [a for a in all_articles
                   if a.get('category') == cat and a.get('slug') != article.get('slug')]
        related = related[:4]

    parts = []
    for art in related[:4]:
        slug = art.get('slug', '')
        title = art.get('title', {})
        if isinstance(title, dict):
            title_text = title.get('zh', '')
        else:
            title_text = art.get('titleZh', '')

        # Try to find a cover image from existing article
        cover = _find_article_cover(slug)

        parts.append(
            f'<div class="sidebar-article">\n'
            f'<img class="sidebar-article__image" src="{cover}" alt="" loading="lazy">\n'
            f'<a class="sidebar-article__title" href="{slug}.html">{title_text}</a>\n'
            f'</div>'
        )

    return '\n'.join(parts) if parts else ''


def _find_article_cover(slug: str) -> str:
    """Find cover image for an article by checking its HTML file."""
    article_path = os.path.join(_SKILL_DIR, 'articles', f'{slug}.html')
    if os.path.exists(article_path):
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.search(r'--hero-image:\s*url\(["\']?(.*?)["\']?\)', content)
            if m:
                return m.group(1)
        except Exception:
            pass
    # Default placeholder
    return '../images/placeholder.jpg'


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_template(data: dict) -> str:
    """Render article HTML using Jinja2 or fallback."""
    template_path = os.path.join(_SKILL_DIR, 'templates', 'article.html')

    if _HAS_JINJA and os.path.exists(template_path):
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template('article.html')
        return template.render(**data)

    # Fallback: simple string replacement
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
    else:
        # Ultra-minimal fallback
        return _render_minimal_fallback(data)

    for key, val in data.items():
        if isinstance(val, str):
            template_str = template_str.replace(f'{{{{ {key} | safe }}}}', val)
            template_str = template_str.replace(f'{{{{ {key} }}}}',
                                               val.replace('&', '&').replace('<', '<'))
    return template_str


def _render_minimal_fallback(data: dict) -> str:
    """Minimal HTML fallback if no template exists."""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{data.get('title', {}).get('zh', '')}</title></head>
<body>
<h1>{data.get('title', {}).get('zh', '')}</h1>
<div>{data.get('body_zh', '')}</div>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Main article processing
# ---------------------------------------------------------------------------

def _get_val(val: dict | str | None, key: str, fallback: str = '') -> str:
    """Safely get value from dict or string, handling None."""
    if val is None:
        return fallback
    if isinstance(val, dict):
        return val.get(key, fallback)
    return fallback


def process_article(
    filepath: str,
    meta: dict,
    all_articles: list[dict],
    prev_slug: str | None = None,
    next_slug: str | None = None,
    download_images: bool = True,
) -> bool:
    """Process a single article from WeChat source to website HTML."""
    slug = meta['slug']
    print(f"Processing: {os.path.basename(filepath)} -> {slug}.html")

    # Prefer source HTML (with original WeChat CDN URLs) for image extraction
    source_file = filepath.replace('.html', '_source.html')
    read_path = source_file if os.path.exists(source_file) else filepath
    if read_path != filepath:
        print(f"  Using source HTML for image URLs: {os.path.basename(read_path)}")

    with open(read_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Extract cover image
    cover_url = ''
    og_img = soup.find('meta', property='og:image')
    if og_img:
        cover_url = og_img.get('content', '')

    # Extract content blocks
    blocks = extract_blocks(soup)
    blocks = merge_paragraphs(blocks)

    # Use first image as cover if no og:image
    if not cover_url:
        for btype, content in blocks:
            if btype == 'img':
                cover_url = content
                break

    # Remove cover image from body blocks if it's the first image (hero already shows it)
    if cover_url:
        for i, (btype, content) in enumerate(blocks):
            if btype == 'img' and content == cover_url:
                blocks.pop(i)
                break

    # Download images (body + cover) in one batch
    img_mapping = None
    if download_images:
        # Collect all image URLs, putting cover first for consistent indexing
        body_urls = [content for btype, content in blocks if btype == 'img']
        all_urls = []
        if cover_url:
            all_urls.append(cover_url)
        for u in body_urls:
            if u != cover_url:
                all_urls.append(u)
        if all_urls:
            img_mapping = image_downloader.download_article_images(slug, all_urls)

    cover = img_mapping.get(cover_url, cover_url) if img_mapping else cover_url

    # Build ZH body HTML
    zh_html = render_blocks(blocks, img_mapping)
    zh_html = _cleanup_html(zh_html)

    # Try to extract EN translation from source
    en_html = None
    if meta.get('has_en_translation') and meta.get('file_pattern'):
        src_dir = os.path.join(_SKILL_DIR, 'AddingArticleWorkSpace', '1')
        en_html, source_type = en_extractor.extract_en(src_dir, meta['file_pattern'])
        if en_html:
            print(f"  [EN] Extracted from {source_type}")
            # Replace image URLs in EN content too
            if img_mapping:
                en_html = image_downloader.replace_image_urls(en_html, img_mapping)

    if en_html:
        en_html = _cleanup_html(en_html)
    else:
        # Use excerpt as placeholder, marked for translation
        excerpt_en = _get_val(meta.get('excerpt'), 'en', meta.get('excerptEn', ''))
        en_html = f'<p class="translation-needed"><em>English translation coming soon. {excerpt_en}</em></p>'
        print(f"  [EN] No translation found, marked as needs_translation")

    # Build navigation links
    nav_html = ''
    if prev_slug or next_slug:
        prev_link = ''
        if prev_slug:
            prev_meta = article_config.get_article_by_slug(all_articles, prev_slug)
            if prev_meta:
                prev_title = _get_val(prev_meta.get('title'), 'en', prev_meta.get('titleEn', ''))
                prev_link = f'<a href="{prev_slug}.html" class="article-nav__link article-nav__link--prev"><span>&larr; Previous</span>{prev_title}</a>'

        next_link = ''
        if next_slug:
            next_meta = article_config.get_article_by_slug(all_articles, next_slug)
            if next_meta:
                next_title = _get_val(next_meta.get('title'), 'en', next_meta.get('titleEn', ''))
                next_link = f'<a href="{next_slug}.html" class="article-nav__link article-nav__link--next"><span>Next &rarr;</span>{next_title}</a>'

        nav_html = f'<nav class="article-nav">\n{prev_link}\n{next_link}\n</nav>'

    # Build related articles
    related_html = build_related_html(meta, all_articles)

    # Prepare template data
    defaults = article_config.load_defaults()

    template_data = {
        'title': {
            'zh': _get_val(meta.get('title'), 'zh', meta.get('titleZh', '')),
            'en': _get_val(meta.get('title'), 'en', meta.get('titleEn', '')),
        },
        'author': {
            'zh': _get_val(meta.get('author'), 'zh', meta.get('authorZh', '')),
            'en': _get_val(meta.get('author'), 'en', meta.get('authorEn', '')),
        },
        'excerpt': {
            'zh': _get_val(meta.get('excerpt'), 'zh', meta.get('excerptZh', '')),
            'en': _get_val(meta.get('excerpt'), 'en', meta.get('excerptEn', '')),
        },
        'catLabel': meta.get('catLabel', ''),
        'catLabelZh': meta.get('catLabelZh', ''),
        'date': _format_date(meta.get('date', '')),
        'time': meta.get('time', ''),
        'cover': cover,
        'hero_style': f"--hero-image: url('{cover}')" if cover else "",
        'body_zh': zh_html,
        'body_en': en_html,
        'nav_html': nav_html,
        'related_html': related_html,
        'contact_email': defaults.get('contact_email', 'info@tibetride.com'),
        'year': defaults.get('year', '2026'),
    }

    # Render final HTML
    final_html = render_template(template_data)

    # Write output
    out_path = os.path.join(_SKILL_DIR, 'articles', f"{slug}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    atomic_io.atomic_write(out_path, final_html)

    print(f"  -> {out_path} ({len(blocks)} blocks, {len([b for b in blocks if b[0] == 'img'])} images)")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert WeChat HTML articles to website format')
    parser.add_argument('--slug', type=str, help='Process only this slug')
    parser.add_argument('--no-download', action='store_true', help='Skip image downloading')
    parser.add_argument('--src-dir', type=str, default=None, help='Source directory (default: AddingArticleWorkSpace/1)')
    args = parser.parse_args()

    src_dir = args.src_dir or os.path.join(_SKILL_DIR, 'AddingArticleWorkSpace', '1')

    if not os.path.exists(src_dir):
        print(f"ERROR: Source directory not found: {src_dir}")
        sys.exit(1)

    all_articles = article_config.load_articles()
    files = [f for f in os.listdir(src_dir) if f.endswith('.html') or f.endswith('.md')]

    to_process = []
    for meta in all_articles:
        if args.slug and meta['slug'] != args.slug:
            continue
        if not meta.get('file_pattern'):
            continue
        matched = None
        for f in files:
            if meta['file_pattern'] in f:
                matched = f
                break
        if matched:
            to_process.append((os.path.join(src_dir, matched), meta))
        else:
            print(f"WARNING: No source file found for: {meta['file_pattern']}")

    to_process.sort(key=lambda x: x[1].get('date', ''))

    for i, (filepath, meta) in enumerate(to_process):
        prev_slug = to_process[i - 1][1]['slug'] if i > 0 else None
        next_slug = to_process[i + 1][1]['slug'] if i < len(to_process) - 1 else None
        process_article(
            filepath, meta, all_articles,
            prev_slug, next_slug,
            download_images=not args.no_download,
        )

    print(f"\nDone! Processed {len(to_process)} articles.")


if __name__ == '__main__':
    main()
