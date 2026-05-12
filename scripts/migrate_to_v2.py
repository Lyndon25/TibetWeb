#!/usr/bin/env python3
"""
One-time migration: move 28 articles from flat files to directory structure.

Before:
  articles/{slug}.html
  images/articles/{slug}/xxx.jpg  (only 2 articles)

After:
  articles/{slug}/index.html
  articles/{slug}/images/xxx.jpg

Also updates all cross-article links from slug.html to slug/.
"""
import os
import re
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(SKILL_DIR, 'articles')
IMAGES_ARTICLES_DIR = os.path.join(SKILL_DIR, 'images', 'articles')


def get_article_slugs():
    """Get list of article slugs from existing HTML files."""
    slugs = []
    for f in sorted(os.listdir(ARTICLES_DIR)):
        if f.endswith('.html') and f != 'index.html':
            slugs.append(f.replace('.html', ''))
    return slugs


def collect_article_links(html):
    """Extract all cross-article hrefs from HTML (sidebar, nav, related)."""
    links = set()
    for m in re.finditer(r'href="(?!https?://|\.\./|/)([^"]+\.html)"', html):
        links.add(m.group(1))
    for m in re.finditer(r"href='(?!https?://|\.\./|/)([^']+\.html)'", html):
        links.add(m.group(1))
    return links


def update_cross_links(html, slug_map):
    """Replace slug.html with slug/ in href attributes."""
    for old_slug, new_dir in slug_map.items():
        html = html.replace(f'href="{old_slug}.html"', f'href="../{new_dir}/"')
        html = html.replace(f"href='{old_slug}.html'", f"href='../{new_dir}/'")
    return html


def update_image_paths(html, slug):
    """Update image paths from ../images/articles/{slug}/ to images/."""
    pattern = f'../images/articles/{slug}/'
    return html.replace(pattern, 'images/')


def migrate_article(slug, slug_map):
    """Migrate a single article from flat file to directory."""
    src_html = os.path.join(ARTICLES_DIR, f'{slug}.html')
    article_dir = os.path.join(ARTICLES_DIR, slug)
    dest_html = os.path.join(article_dir, 'index.html')
    images_src = os.path.join(IMAGES_ARTICLES_DIR, slug)
    images_dest = os.path.join(article_dir, 'images')

    if not os.path.exists(src_html):
        print(f'  SKIP: {slug}.html not found')
        return False

    os.makedirs(article_dir, exist_ok=True)

    with open(src_html, 'r', encoding='utf-8') as f:
        html = f.read()

    # Update cross-article links (other article references)
    html = update_cross_links(html, slug_map)

    # Update self-referencing links (sidebar "related" might link to this article)
    html = html.replace(f'href="{slug}.html"', f'href="./"')
    html = html.replace(f"href='{slug}.html'", f"href='./'")

    # Update image paths if local images exist
    if os.path.exists(images_src):
        html = update_image_paths(html, slug)
        os.makedirs(images_dest, exist_ok=True)
        for f in os.listdir(images_src):
            shutil.move(os.path.join(images_src, f), os.path.join(images_dest, f))
        os.rmdir(images_src)
        print(f'  Moved images: {images_src} -> {images_dest}')

    atomic_write(dest_html, html)

    # Remove old flat file
    os.remove(src_html)
    print(f'  {slug}.html -> {slug}/index.html')
    return True


def atomic_write(path, content):
    """Atomic file write via temp file."""
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)


def migrate_index_page(slug_map):
    """Update articles/index.html with new directory URLs."""
    index_path = os.path.join(ARTICLES_DIR, 'index.html')
    if not os.path.exists(index_path):
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Update URLs in the hardcoded JS array
    for old_slug in slug_map:
        html = html.replace(f"url:'{old_slug}.html'", f"url:'{old_slug}/'")
        html = html.replace(f'url:"{old_slug}.html"', f'url:"{old_slug}/"')

    # Update footer/article links
    for old_slug in slug_map:
        html = html.replace(f'href="{old_slug}.html"', f'href="{old_slug}/"')
        html = html.replace(f"href='{old_slug}.html'", f"href='{old_slug}/'")

    atomic_write(index_path, html)
    print(f'Updated articles/index.html with {len(slug_map)} URL rewrites')


def update_core_pages(slug_map):
    """Update root and guides pages that reference articles."""
    root_html_files = ['index.html', 'about.html', 'customize.html', 'routes.html']
    for fname in root_html_files:
        path = os.path.join(SKILL_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        updated = html
        for slug in slug_map:
            updated = updated.replace(f'articles/{slug}.html', f'articles/{slug}/')
        if updated != html:
            atomic_write(path, updated)
            print(f'Updated {fname}')

    # Guides directory
    guides_dir = os.path.join(SKILL_DIR, 'guides')
    if os.path.exists(guides_dir):
        for fname in os.listdir(guides_dir):
            if not fname.endswith('.html'):
                continue
            path = os.path.join(guides_dir, fname)
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            updated = html
            for slug in slug_map:
                updated = updated.replace(f'../articles/{slug}.html', f'../articles/{slug}/')
            if updated != html:
                atomic_write(path, updated)
                print(f'Updated guides/{fname}')

    # Tours directory
    tours_dir = os.path.join(SKILL_DIR, 'tours')
    if os.path.exists(tours_dir):
        for fname in os.listdir(tours_dir):
            if not fname.endswith('.html'):
                continue
            path = os.path.join(tours_dir, fname)
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            updated = html
            for slug in slug_map:
                updated = updated.replace(f'../articles/{slug}.html', f'../articles/{slug}/')
            if updated != html:
                atomic_write(path, updated)
                print(f'Updated tours/{fname}')


def verify_migration(slugs):
    """Verify all articles were migrated correctly."""
    errors = []
    for slug in slugs:
        idx_path = os.path.join(ARTICLES_DIR, slug, 'index.html')
        if not os.path.exists(idx_path):
            errors.append(f'MISSING: articles/{slug}/index.html')
            continue
        with open(idx_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Check for stale flat-file links within articles directory
        stale = re.findall(r'href="(?!https?://|\.\./|\./|#)([\w-]+\.html)"', html)
        if stale:
            errors.append(f'STALE LINKS in {slug}/index.html: {stale}')
    return errors


def main():
    slugs = get_article_slugs()
    print(f'Found {len(slugs)} articles to migrate')
    print()

    slug_map = {s: s for s in slugs}

    # Phase 1: Migrate each article to directory
    success = 0
    for slug in slugs:
        ok = migrate_article(slug, slug_map)
        if ok:
            success += 1

    print(f'\nMigrated {success}/{len(slugs)} articles')

    # Phase 2: Update articles/index.html
    migrate_index_page(slug_map)

    # Phase 3: Update core pages (index, about, routes, contact, guides, tours)
    update_core_pages(slug_map)

    # Phase 4: Verify
    print('\nVerifying...')
    errors = verify_migration(slugs)
    if errors:
        print(f'ERRORS ({len(errors)}):')
        for e in errors:
            print(f'  {e}')
    else:
        print('All articles migrated successfully!')

    # Clean up old image directories
    if os.path.exists(IMAGES_ARTICLES_DIR):
        remaining = os.listdir(IMAGES_ARTICLES_DIR)
        if not remaining:
            os.rmdir(IMAGES_ARTICLES_DIR)
            print(f'Removed empty: {IMAGES_ARTICLES_DIR}')
        else:
            print(f'Note: {IMAGES_ARTICLES_DIR} still has entries: {remaining}')


if __name__ == '__main__':
    main()
