#!/usr/bin/env python3
"""
Generate the articles/index.html JS article array.

Scans the articles directory for all articles, reads metadata from
config/articles.yaml (for known articles) or extracts from HTML (for others).
Replaces the hardcoded `var articles = [...]` block in articles/index.html.
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(SKILL_DIR, 'articles')
CONFIG_PATH = os.path.join(SKILL_DIR, 'config', 'articles.yaml')
INDEX_PATH = os.path.join(ARTICLES_DIR, 'index.html')


def load_config():
    """Load YAML config using the library's built-in parser (no PyYAML needed)."""
    sys.path.insert(0, SCRIPT_DIR)
    from lib.article_config import _load_yaml
    return _load_yaml(CONFIG_PATH)


def scan_articles():
    """Scan articles directory for all articles. Returns list of {slug, path}."""
    results = []
    for entry in sorted(os.listdir(ARTICLES_DIR)):
        d = os.path.join(ARTICLES_DIR, entry)
        if not os.path.isdir(d):
            continue
        idx = os.path.join(d, 'index.html')
        if os.path.exists(idx):
            results.append({'slug': entry, 'path': idx})
    return results


def extract_from_html(html, slug):
    """Extract article metadata from HTML."""
    meta = {'slug': slug}

    # Title
    zh_title_m = re.search(
        r'<div class="lang-content" data-lang="zh">\s*<h1[^>]*>(.*?)</h1>', html, re.S)
    en_title_m = re.search(
        r'<div class="lang-content" data-lang="en">\s*<h1[^>]*>(.*?)</h1>', html, re.S)

    meta['title'] = {
        'zh': zh_title_m.group(1).strip() if zh_title_m else slug,
        'en': en_title_m.group(1).strip() if en_title_m else slug,
    }

    # Date
    date_m = re.search(r'class="article-hero__date">([^<]+)<', html)
    if date_m:
        meta['date'] = date_m.group(1).strip()
    else:
        meta['date'] = ''

    # Category
    cat_m = re.search(r'class="article-hero__category">([^<]+)<', html)
    cat_label = cat_m.group(1).strip() if cat_m else ''

    # Map category label to slug and zh label
    cat_map = {
        'Travel Guide': ('travel-guide', '旅行指南'),
        'Photography': ('photography', '摄影'),
        'Travelogue': ('travelogue', '游记'),
        'Routes': ('routes', '路线'),
        'Gear': ('gear', '装备'),
        'Gear & Equipment': ('gear', '装备'),
        'Health & Safety': ('health', '健康与安全'),
        'Culture': ('culture', '文化'),
        'Reflection': ('reflection', '随笔'),
    }
    cat_info = cat_map.get(cat_label, ('travel-guide', '旅行指南' if cat_label else ''))
    meta['category'] = cat_info[0]
    meta['catLabel'] = cat_label
    meta['catLabelZh'] = cat_info[1]

    # Excerpt (first paragraph after hero)
    body_start = html.find('article-body')
    if body_start > 0:
        zh_body_start = html.find('data-lang="zh"', body_start)
        if zh_body_start > 0:
            zh_div = html.find('>', zh_body_start) + 1
            # Get text from first few p tags
            ps = re.findall(r'<p[^>]*>(.*?)</p>', html[zh_div:zh_div + 2000], re.S)
            zh_excerpt = ''
            for p in ps:
                text = re.sub(r'<[^>]+>', '', p).strip()
                if len(text) > 10:
                    zh_excerpt = text[:150]
                    break
            meta['excerpt'] = {'zh': zh_excerpt, 'en': zh_excerpt}

    if 'excerpt' not in meta:
        meta['excerpt'] = {'zh': '', 'en': ''}

    # Time / read time
    meta['time'] = '5 min read'

    # Featured (check if featured: true near the slug in the old JS)
    meta['featured'] = False

    # Cover image
    cover_m = re.search(r'<img[^>]+src="([^"]+)"', html[body_start:body_start + 5000] if body_start > 0 else html)
    meta['cover'] = cover_m.group(1) if cover_m else ''

    return meta


def merge_config(scan_results, config_articles):
    """Merge config data with scanned articles. Config takes precedence."""
    config_map = {a['slug']: a for a in config_articles}
    merged = []
    for art in scan_results:
        slug = art['slug']
        if slug in config_map:
            # Use config data, supplement with HTML-extracted data
            cfg = config_map[slug]
            meta = {
                'slug': slug,
                'category': cfg.get('category', 'travel-guide'),
                'catLabel': cfg.get('catLabel', ''),
                'catLabelZh': cfg.get('catLabelZh', ''),
                'title': cfg.get('title', {'zh': slug, 'en': slug}),
                'excerpt': cfg.get('excerpt', {'zh': '', 'en': ''}),
                'date': cfg.get('date', ''),
                'time': cfg.get('time', '5 min read'),
                'featured': cfg.get('featured', False),
            }
        else:
            # Extract from HTML
            meta = extract_from_html(
                open(art['path'], 'r', encoding='utf-8').read(), slug)
        merged.append(meta)
    return merged


def get_article_cover(slug):
    """Get cover image from article HTML."""
    idx_path = os.path.join(ARTICLES_DIR, slug, 'index.html')
    if not os.path.exists(idx_path):
        return ''
    with open(idx_path, 'r', encoding='utf-8') as f:
        html = f.read()
    body_start = html.find('article-body')
    if body_start < 0:
        body_start = 0
    img_m = re.search(r'<img[^>]+src="([^"]+)"', html[body_start:])
    return img_m.group(1) if img_m else ''


def build_article_js(articles):
    """Build the JavaScript array string."""
    lines = []
    for art in articles:
        slug = art.get('slug', '')
        cat = art.get('category', '')
        cat_label = art.get('catLabel', '')
        cat_label_zh = art.get('catLabelZh', '')

        title = art.get('title', {})
        if isinstance(title, dict):
            title_en = title.get('en', '')
            title_zh = title.get('zh', '')
        else:
            title_en = title_zh = str(title)

        excerpt = art.get('excerpt', {})
        if isinstance(excerpt, dict):
            excerpt_en = excerpt.get('en', '')
            excerpt_zh = excerpt.get('zh', '')
        else:
            excerpt_en = excerpt_zh = str(excerpt)

        date_str = art.get('date', '')
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            date_formatted = dt.strftime('%b %d, %Y')
        except (ValueError, TypeError):
            date_formatted = date_str

        time_str = art.get('time', '5 min read')
        cover = art.get('cover', '') or get_article_cover(slug)
        featured = 'true' if art.get('featured') else 'false'

        def js_escape(s):
            return str(s).replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ').replace('\r', '')

        lines.append(
            f"{{ cat:'{js_escape(cat)}', catLabel:'{js_escape(cat_label)}', "
            f"catLabelZh:'{js_escape(cat_label_zh)}', "
            f"title:'{js_escape(title_en)}', titleZh:'{js_escape(title_zh)}', "
            f"excerpt:'{js_escape(excerpt_en)}', excerptZh:'{js_escape(excerpt_zh)}', "
            f"date:'{js_escape(date_formatted)}', time:'{js_escape(time_str)}', "
            f"url:'{slug}/', img:'{js_escape(cover)}', featured:{featured} }}"
        )

    return ',\n    '.join(lines)


def update_index_html(js_array_str):
    """Replace the var articles = [...] block in index.html."""
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    pattern = r'var articles = \[[\s\S]*?\];'
    replacement = f'var articles = [\n    {js_array_str}\n  ];'
    updated = re.sub(pattern, replacement, html)

    if updated == html:
        print('WARNING: Could not find var articles = [...] block')
        return False

    tmp = INDEX_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(updated)
    os.replace(tmp, INDEX_PATH)
    return True


def main():
    scanned = scan_articles()
    print(f'Scanned {len(scanned)} article directories')

    config = load_config()
    config_articles = config.get('articles', [])

    merged = merge_config(scanned, config_articles)
    print(f'Merged {len(merged)} articles')

    # Sort by date descending
    def sort_key(a):
        d = a.get('date', '')
        return d if d else '0000-00-00'
    merged.sort(key=sort_key, reverse=True)

    js_array = build_article_js(merged)

    if update_index_html(js_array):
        print(f'Updated articles/index.html with {len(merged)} articles')
    else:
        print('Failed to update index.html')
        sys.exit(1)


if __name__ == '__main__':
    main()
