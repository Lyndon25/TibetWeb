#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch fix: download WeChat CDN images locally for all existing articles,
then replace remote URLs with local paths.

Usage:
    python scripts/fix_images_batch.py --repo-path /path/to/TibetWeb
    python scripts/fix_images_batch.py --repo-path /path/to/TibetWeb --dry-run
    python scripts/fix_images_batch.py --repo-path /path/to/TibetWeb --slug my-article
"""

import argparse
import hashlib
import os
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent

WECHAT_CDN = re.compile(
    r'https?://(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn|mmecoa\.qpic\.cn|'
    r'mmsns\.qpic\.cn|mp\.weixin\.qq\.com)/\S+?(?=["\')\s]|$)',
    re.I,
)

NO_REFERRER_META = '<meta name="referrer" content="strict-origin-when-cross-origin">'


def _log(msg: str):
    print(msg)


def _gen_filename(url: str, index: int) -> str:
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:6]
    ext_match = re.search(r'wx_fmt=(\w+)', url, re.I)
    ext = ext_match.group(1).lower() if ext_match else 'jpg'
    if ext == 'jpeg':
        ext = 'jpg'
    return f"{index:03d}_{url_hash}.{ext}"


def _download(url: str, dest: str) -> bool:
    strategies = [
        {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        },
        {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Referer': 'https://mp.weixin.qq.com/',
        },
    ]

    for headers in strategies:
        try:
            req = urllib.request.Request(url, headers=headers)
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            with opener.open(req, timeout=30) as resp:
                data = resp.read()
                if len(data) < 500:
                    continue
                Path(dest).parent.mkdir(parents=True, exist_ok=True)
                with open(dest, 'wb') as f:
                    f.write(data)
            return True
        except Exception:
            continue
    return False


def extract_urls_from_html(html: str) -> list[str]:
    """Extract all WeChat CDN image URLs from HTML/JS content."""
    urls = set()
    # img src / data-src attributes
    for m in re.finditer(r'''(?:src|data-src)=["'](https?://[^"']+)["']''', html):
        url = m.group(1)
        if WECHAT_CDN.match(url):
            urls.add(url)
    # CSS url() values
    for m in re.finditer(r'''url\(["']?(https?://[^)"']+)["']?\)''', html):
        url = m.group(1)
        if WECHAT_CDN.match(url):
            urls.add(url)
    # JS object property values: img:'URL', cover:'URL'
    for m in re.finditer(r'''(?:img|cover|src)\s*:\s*['"](https?://[^"']+)['"]''', html):
        url = m.group(1)
        if WECHAT_CDN.match(url):
            urls.add(url)
    return list(urls)


def fix_article(article_path: Path, images_base: Path, slug: str, dry_run: bool = False) -> int:
    """Download all WeChat CDN images in an article and replace URLs. Returns count of replaced URLs."""
    html = article_path.read_text(encoding='utf-8')
    urls = extract_urls_from_html(html)
    if not urls:
        return 0

    img_dir = images_base / slug
    replaced = 0
    mapping = {}

    for i, url in enumerate(urls, 1):
        filename = _gen_filename(url, i)
        dest = img_dir / filename
        rel_path = f"../images/articles/{slug}/{filename}"

        if dest.exists() and dest.stat().st_size > 500:
            mapping[url] = rel_path
            replaced += 1
            continue

        if not dry_run:
            if _download(url, str(dest)):
                mapping[url] = rel_path
                replaced += 1
                _log(f"  [{replaced}/{len(urls)}] {filename}")
            else:
                _log(f"  [FAIL] {url[:80]}...")
        else:
            _log(f"  [DRY-RUN] {url[:80]}... -> {rel_path}")
            mapping[url] = rel_path
            replaced += 1

    # Replace URLs in HTML
    if mapping and not dry_run:
        new_html = html
        for old_url, new_path in mapping.items():
            new_html = new_html.replace(old_url, new_path)
        if new_html != html:
            article_path.write_text(new_html, encoding='utf-8')

    return replaced


def fix_index_page(index_path: Path, images_base: Path, dry_run: bool = False) -> int:
    """Download cover images referenced in articles/index.html JS array and replace with local paths."""
    html = index_path.read_text(encoding='utf-8')
    urls = extract_urls_from_html(html)
    if not urls:
        return 0

    covers_dir = images_base / '_index_covers'
    replaced = 0
    mapping = {}

    for i, url in enumerate(urls, 1):
        filename = _gen_filename(url, i)
        dest = covers_dir / filename
        rel_path = f"../images/articles/_index_covers/{filename}"

        if dest.exists() and dest.stat().st_size > 500:
            mapping[url] = rel_path
            replaced += 1
            continue

        if not dry_run:
            if _download(url, str(dest)):
                mapping[url] = rel_path
                replaced += 1
        else:
            mapping[url] = rel_path
            replaced += 1

    if mapping and not dry_run:
        new_html = html
        for old_url, new_path in mapping.items():
            new_html = new_html.replace(old_url, new_path)
        if new_html != html:
            index_path.write_text(new_html, encoding='utf-8')

    return replaced


def ensure_no_referrer(html_path: Path):
    """Ensure the HTML file has <meta name='referrer' content='no-referrer'> for hotlink bypass."""
    html = html_path.read_text(encoding='utf-8')
    if 'no-referrer' in html:
        return
    # Insert after <head> or <meta charset>
    if '<meta charset' in html:
        html = html.replace('<meta charset', f'{NO_REFERRER_META}\n<meta charset', 1)
    elif '<head>' in html:
        html = html.replace('<head>', f'<head>\n{NO_REFERRER_META}', 1)
    else:
        return
    html_path.write_text(html, encoding='utf-8')
    _log(f"  Added no-referrer meta to {html_path.name}")


def main():
    ap = argparse.ArgumentParser(description='Batch fix WeChat CDN images to local')
    ap.add_argument('--repo-path', '-r', required=True, help='Path to website repo')
    ap.add_argument('--slug', '-s', help='Process only this article slug')
    ap.add_argument('--dry-run', action='store_true', help='Show what would be done')
    ap.add_argument('--no-index', action='store_true', help='Skip index page fix')
    ap.add_argument('--no-referrer-check', action='store_true', help='Skip no-referrer check')
    args = ap.parse_args()

    repo = Path(args.repo_path)
    articles_dir = repo / 'articles'
    images_base = repo / 'images' / 'articles'

    if not articles_dir.is_dir():
        _log(f"ERROR: articles dir not found: {articles_dir}")
        sys.exit(1)

    # Collect articles to process
    html_files = sorted(articles_dir.glob('*.html'))
    if args.slug:
        html_files = [articles_dir / f'{args.slug}.html']

    # Filter out index.html (handled separately)
    article_files = [f for f in html_files if f.name != 'index.html']
    index_file = articles_dir / 'index.html'

    total_replaced = 0

    # Process each article
    for af in article_files:
        slug = af.stem
        _log(f"\n{'='*50}")
        _log(f"Processing: {slug}")

        # Ensure no-referrer meta tag
        if not args.no_referrer_check:
            ensure_no_referrer(af)

        n = fix_article(af, images_base, slug, dry_run=args.dry_run)
        total_replaced += n
        _log(f"  Replaced: {n} images")

    # Fix index page cover images
    if index_file.exists() and not args.no_index:
        _log(f"\n{'='*50}")
        _log("Fixing articles/index.html cover images...")
        if not args.no_referrer_check:
            ensure_no_referrer(index_file)
        n = fix_index_page(index_file, images_base, dry_run=args.dry_run)
        total_replaced += n
        _log(f"  Replaced: {n} cover images")

    _log(f"\n{'='*50}")
    _log(f"Done! Total images replaced: {total_replaced}")
    if args.dry_run:
        _log("DRY RUN — no changes made. Remove --dry-run to apply.")


if __name__ == '__main__':
    main()
