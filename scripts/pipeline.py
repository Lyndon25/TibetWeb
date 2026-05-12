#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tibet Publish Skill — One-shot entry point.
Takes a WeChat article URL and deploys to the TibetJourneyWebsite.

Hardcoded:
  - Git remote: https://github.com/Lyndon25/TibetWeb.git
  - Git branch: main

Usage:
    python pipeline.py --url "https://mp.weixin.qq.com/s/..."
    python pipeline.py --url "..." --repo-path /path/to/local/repo --skip-push
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# ── Hardcoded git config ──────────────────────────────────────────────
GIT_REMOTE_URL = "https://github.com/Lyndon25/TibetWeb.git"
GIT_BRANCH = "main"

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent


def _log(phase: str, msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{phase}] {msg}")


# ── Repo setup ────────────────────────────────────────────────────────

def ensure_repo(repo_path: str) -> Path:
    """Clone or update the website repo. Returns Path to repo."""
    repo = Path(repo_path)
    if not (repo / '.git').exists():
        _log('REPO', f'Cloning {GIT_REMOTE_URL} ...')
        subprocess.run(['git', 'clone', GIT_REMOTE_URL, str(repo)],
                       check=True, capture_output=True)

    # Ensure we're on the right branch
    subprocess.run(['git', '-C', str(repo), 'fetch', 'origin', GIT_BRANCH],
                   capture_output=True)
    r = subprocess.run(['git', '-C', str(repo), 'checkout', GIT_BRANCH],
                       capture_output=True)
    if r.returncode != 0:
        subprocess.run(
            ['git', '-C', str(repo), 'checkout', '-b', GIT_BRANCH,
             f'origin/{GIT_BRANCH}'], capture_output=True)
    subprocess.run(['git', '-C', str(repo), 'pull', 'origin', GIT_BRANCH],
                   capture_output=True)
    _log('REPO', f'Ready at {repo}')
    return repo


def seed_repo(repo: Path):
    """Copy skill assets into the website repo so the build pipeline can run."""
    assets_dir = _SKILL_DIR / 'assets'

    # Copy CSS / JS
    for folder in ['css', 'js']:
        src = assets_dir / folder
        dst = repo / folder
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for f in src.iterdir():
                shutil.copy2(f, dst / f.name)
                _log('SEED', f'{folder}/{f.name}')

    # Copy template
    tmpl_src = assets_dir / 'templates' / 'article.html'
    tmpl_dst = repo / 'templates' / 'article.html'
    if tmpl_src.exists():
        tmpl_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tmpl_src, tmpl_dst)
        _log('SEED', 'templates/article.html')

    # Copy scripts (convert, build, lib)
    scripts_src = _SKILL_DIR / 'scripts'
    scripts_dst = repo / 'scripts'
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for item in scripts_src.iterdir():
        if item.is_dir():
            dst_dir = scripts_dst / item.name
            dst_dir.mkdir(exist_ok=True)
            for f in item.iterdir():
                if f.suffix == '.py':
                    shutil.copy2(f, dst_dir / f.name)
        elif item.suffix == '.py' and item.name != 'pipeline.py':
            shutil.copy2(item, scripts_dst / item.name)
    _log('SEED', 'scripts/')

    # Copy config if not present
    config_dst = repo / 'config' / 'articles.yaml'
    if not config_dst.exists():
        config_dst.parent.mkdir(parents=True, exist_ok=True)
        config_dst.write_text(
            '# Article metadata — managed by tibet-publish skill\n'
            'articles: []\n\n'
            'defaults:\n'
            '  site_name:\n'
            '    zh: "TibetRide"\n'
            '    en: "TibetRide"\n'
            '  site_tagline:\n'
            '    zh: "探索西藏"\n'
            '    en: "Explore Tibet"\n',
            encoding='utf-8')
        _log('SEED', 'config/articles.yaml')

    # Ensure workspace directory
    ws = repo / 'AddingArticleWorkSpace' / '1'
    ws.mkdir(parents=True, exist_ok=True)
    (ws / 'images').mkdir(exist_ok=True)

    # Ensure output directories
    (repo / 'articles').mkdir(exist_ok=True)
    (repo / 'images' / 'articles').mkdir(parents=True, exist_ok=True)


# ── Article fetch & save ──────────────────────────────────────────────

def _gen_slug(title: str) -> str:
    """Generate a short English-friendly slug from ASCII keywords, matching existing article naming."""
    ascii_words = re.findall(r'[a-zA-Z0-9]{2,}', title)
    if ascii_words:
        return '-'.join(w.lower() for w in ascii_words[:6])
    # Fallback for titles with no ASCII content
    return 'tibet-article-' + hashlib.md5(title.encode('utf-8')).hexdigest()[:6]


def _gen_fp(title: str) -> str:
    """File pattern now uses the slug directly for consistent naming."""
    return _gen_slug(title)


def fetch_article(url: str, repo: Path) -> dict | None:
    """Fetch WeChat article, save HTML to repo workspace. Returns article dict."""
    sys.path.insert(0, str(_SCRIPT_DIR))
    from lib import wechat_fetcher

    _log('FETCH', f'Fetching {url[:80]}...')
    article = wechat_fetcher.fetch_wechat_article(url)
    if not article:
        _log('FETCH', 'FAILED')
        return None
    _log('FETCH', f'OK: {article.get("title", "?")[:60]}')

    content_soup = article.get('content_soup')
    original_html = str(content_soup) if content_soup else article.get('content_html', '')
    article['content_html_original'] = original_html

    # Download images
    ws = repo / 'AddingArticleWorkSpace' / '1'
    img_dir = ws / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)
    if content_soup:
        try:
            mapping = wechat_fetcher.download_images(content_soup, str(img_dir), 'images')
            article['img_mapping'] = mapping
            article['content_html'] = str(content_soup)
            _log('FETCH', f'Images downloaded: {len(mapping)}')
        except Exception as e:
            _log('FETCH', f'Image warning: {e}')

    # Save files
    fp = _gen_fp(article.get('title', ''))
    slug = _gen_slug(article.get('title', ''))
    (ws / f'{fp}.html').write_text(article.get('content_html', ''), encoding='utf-8')
    (ws / f'{fp}_source.html').write_text(original_html, encoding='utf-8')
    _log('SAVE', f'HTML saved: {fp}.html')

    article['slug'] = slug
    article['file_pattern'] = fp
    return article


# ── Config update ─────────────────────────────────────────────────────

def write_config(repo: Path, article: dict):
    """Add article metadata to config/articles.yaml."""
    from lib import yaml_updater
    config_path = repo / 'config' / 'articles.yaml'
    slug = article['slug']
    if yaml_updater.slug_exists(str(config_path), slug):
        _log('CONFIG', f'Slug {slug} exists, skip')
        return
    entry = {
        'slug': slug,
        'file_pattern': article['file_pattern'],
        'has_en_translation': True,
        'category': 'travel-guide',
        'catLabel': 'Travel Guide',
        'catLabelZh': '旅行指南',
        'date': f'{datetime.now():%Y-%m-%d}',
        'time': '5 min read',
        'author': {
            'zh': article.get('author', '') or article.get('account_name', '未知'),
            'en': article.get('author', '') or 'Unknown',
        },
        'title': {
            'zh': article.get('title', ''),
            'en': article.get('title', ''),
        },
        'excerpt': {
            'zh': (article.get('description', '') or article.get('title', ''))[:120],
            'en': (article.get('description', '') or article.get('title', ''))[:120],
        },
        'related': [],
    }
    try:
        yaml_updater.add_new_article(str(config_path), entry)
        _log('CONFIG', 'OK')
    except Exception as e:
        _log('CONFIG', f'WARNING: {e}')


def _update_article_index(repo: Path, article: dict):
    """Insert new article into the hardcoded JS array in articles/index.html."""
    index_path = repo / 'articles' / 'index.html'
    if not index_path.exists():
        _log('INDEX', 'articles/index.html not found, skip')
        return

    content = index_path.read_text(encoding='utf-8')

    # Locate the articles array start: "var articles = ["
    marker = 'var articles = ['
    pos = content.find(marker)
    if pos == -1:
        _log('INDEX', 'articles array not found, skip')
        return

    # Build the new entry
    title = article.get('title', '')
    desc = article.get('description', '') or ''
    cover = ''
    if article.get('content_soup'):
        og_img = article['content_soup'].find('meta', property='og:image')
        if og_img:
            cover = og_img.get('content', '')
    if not cover:
        imgs = article.get('content_soup') and article['content_soup'].find_all('img')
        if imgs:
            for img in imgs:
                src = img.get('data-src') or img.get('src', '')
                if src and src.startswith('http'):
                    cover = src
                    break

    date_str = datetime.now().strftime('%b %d, %Y')
    slug = article['slug']

    entry = (
        "{ cat:'travel-guide', catLabel:'Travel Guide', catLabelZh:'旅行指南', "
        f"title:'{title}', titleZh:'{title}', "
        f"excerpt:'{desc[:120]}', excerptZh:'{desc[:120]}', "
        f"date:'{date_str}', time:'5 min read', "
        f"url:'{slug}.html', img:'{cover}', featured:false }}"
    )

    # Insert new entry after "var articles = ["
    insert_pos = pos + len(marker)
    after_marker = content[insert_pos:insert_pos + 10].strip()
    if after_marker:
        # Array already has entries — prepend with comma
        entry = '\n    ' + entry + ',\n    '
    else:
        # Empty array
        entry = '\n    ' + entry + '\n  '

    new_content = content[:insert_pos] + entry + content[insert_pos:]
    index_path.write_text(new_content, encoding='utf-8')
    _log('INDEX', f'Inserted article into index.html (slug={slug})')


# ── Build pipeline ────────────────────────────────────────────────────

def run_build(repo: Path, slug: str) -> bool:
    """Run convert → rebuild → sync → validate phases."""
    build_py = repo / 'scripts' / 'build.py'
    if not build_py.exists():
        _log('BUILD', 'build.py not found, skipping')
        return True

    ok = True
    for phase in ['convert', 'rebuild', 'sync', 'validate']:
        _log('BUILD', f'--{phase}...')
        try:
            r = subprocess.run(
                [sys.executable, str(build_py), f'--{phase}', '--slug', slug],
                capture_output=True, text=True, timeout=300, cwd=str(repo)
            )
            if r.returncode != 0:
                _log('BUILD', f'--{phase} FAILED: {r.stderr[:200]}')
                ok = False
            else:
                _log('BUILD', f'--{phase} OK')
        except Exception as e:
            _log('BUILD', f'--{phase} error: {e}')
            ok = False
    return ok


# ── Git push ──────────────────────────────────────────────────────────

def git_push(repo: Path, slug: str) -> bool:
    """Stage, commit, and push changes."""
    repo_str = str(repo)
    for cmd_name, cmd_args in [
        ('add', ['git', '-C', repo_str, 'add', '.']),
        ('commit', ['git', '-C', repo_str, 'commit', '-m',
                    f'feat(article): add {slug}']),
        ('push', ['git', '-C', repo_str, 'push', 'origin', GIT_BRANCH]),
    ]:
        _log('GIT', f'{cmd_name}...')
        r = subprocess.run(cmd_args, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            stderr = r.stderr.strip()
            # commit can fail with "nothing to commit" — that's OK
            if cmd_name == 'commit' and 'nothing to commit' in stderr:
                _log('GIT', 'commit: nothing to commit (OK)')
                continue
            _log('GIT', f'{cmd_name} FAILED: {stderr[:200]}')
            return False
        _log('GIT', f'{cmd_name} OK')
    return True


# ── Main ──────────────────────────────────────────────────────────────

def run(url: str, repo_path: str | None = None, slug: str | None = None,
        skip_push: bool = False) -> bool:
    """Run the full pipeline. Returns True on success."""
    repo_path = repo_path or os.path.join(tempfile.gettempdir(), 'TibetWeb')

    _log('PIPELINE', f'URL: {url[:80]}...')
    repo = ensure_repo(repo_path)
    seed_repo(repo)

    article = fetch_article(url, repo)
    if not article:
        return False

    slug = slug or article['slug']
    _log('PIPELINE', f'Slug={slug}')

    write_config(repo, article)
    build_ok = run_build(repo, slug)

    if build_ok:
        _update_article_index(repo, article)

    if not skip_push:
        git_push(repo, slug)

    print(f"\nDone!  Article: {article.get('title', '')}  Slug: {slug}")
    print(f"Repo: {repo}")
    return build_ok


def main():
    ap = argparse.ArgumentParser(description='Tibet Publish — WeChat URL to deployed article')
    ap.add_argument('--url', '-u', required=True, help='WeChat article URL')
    ap.add_argument('--repo-path', '-r', help='Path to local website repo (cloned if absent)')
    ap.add_argument('--slug', '-s', help='Article slug (auto-generated from title if omitted)')
    ap.add_argument('--skip-push', action='store_true', help='Skip git push')
    args = ap.parse_args()

    success = run(args.url, args.repo_path, args.slug, args.skip_push)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
