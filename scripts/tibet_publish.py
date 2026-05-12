#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TibetWorkflow 一键发布管道 - 从微信链接到 Git Push

流程:
  1. FETCH   - 抓取微信文章 + 图片本地化
  2. CONFIG  - 写入文章元数据到 articles.yaml
  3. BUILD   - 调用 build.py (convert → rebuild → sync → validate)
  4. PUBLISH - Git add → commit → push

用法:
    python scripts/tibet_publish.py --url https://mp.weixin.qq.com/s/...
    python scripts/tibet_publish.py --url <URL> --slug my-article
    python scripts/tibet_publish.py --url <URL> --skip-push
"""
import hashlib, os, sys, re, argparse, subprocess
from datetime import datetime
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

from lib import wechat_fetcher, git_manager, yaml_updater, atomic_io

LOG_DIR = os.path.join(_SKILL_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

def _log(phase, msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] [{phase}] {msg}"
    print(line)
    with open(os.path.join(LOG_DIR, f'{datetime.now():%Y%m%d}.log'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def _load_settings():
    sp = os.path.join(_SKILL_DIR, 'config', 'settings.yaml')
    d = {'build': {'auto_push': True, 'validate': True, 'download_images': True, 'request_delay': 2.0},
         'directories': {'workspace': 'AddingArticleWorkSpace'}, 'repository': {}, 'defaults': {}}
    if not os.path.exists(sp):
        return d
    try:
        import yaml
        with open(sp, encoding='utf-8') as f:
            return yaml.safe_load(f) or d
    except ImportError:
        return d
    except Exception:
        return d

def _gen_slug(title):
    """Generate a short English-friendly slug from ASCII keywords, matching existing article naming."""
    ascii_words = re.findall(r'[a-zA-Z0-9]{2,}', title)
    if ascii_words:
        return '-'.join(w.lower() for w in ascii_words[:6])
    # Fallback for titles with no ASCII content
    return 'tibet-article-' + hashlib.md5(title.encode('utf-8')).hexdigest()[:6]

def _gen_fp(title):
    """File pattern now uses the slug directly for consistent naming."""
    return _gen_slug(title)

def step_fetch(url, settings):
    _log('FETCH', f'Fetching: {url[:80]}...')
    a = wechat_fetcher.fetch_wechat_article(url)
    if not a:
        _log('FETCH', 'FAILED: no article returned'); return None
    _log('FETCH', f'OK: {a.get("title","?")[:60]}')
    # Save original HTML (with WeChat CDN URLs) before image localization
    a['content_html_original'] = str(a['content_soup']) if a.get('content_soup') else a.get('content_html', '')
    if settings.get('build',{}).get('download_images', True) and a.get('content_soup'):
        ws = os.path.join(_SKILL_DIR, settings.get('directories',{}).get('workspace','AddingArticleWorkSpace'), '1')
        os.makedirs(os.path.join(ws, 'images'), exist_ok=True)
        try:
            m = wechat_fetcher.download_images(a['content_soup'], os.path.join(ws, 'images'), 'images')
            a['img_mapping'] = m; a['content_html'] = str(a['content_soup'])
            _log('FETCH', f'Images: {len(m)}')
        except Exception as e:
            _log('FETCH', f'Image warning: {e}')
    return a

def step_save(a, fp, settings):
    ws = os.path.join(_SKILL_DIR, settings.get('directories',{}).get('workspace','AddingArticleWorkSpace'), '1')
    os.makedirs(ws, exist_ok=True)
    try:
        atomic_io.atomic_write(os.path.join(ws, f'{fp}.html'), a.get('content_html',''))
        _log('SAVE', f'HTML saved: {fp}.html')
    except Exception as e:
        _log('SAVE', f'FAILED: {e}'); return False
    # Save original HTML (with WeChat CDN URLs) for image extraction during build
    if a.get('content_html_original'):
        try:
            atomic_io.atomic_write(os.path.join(ws, f'{fp}_source.html'), a['content_html_original'])
            _log('SAVE', f'Source HTML saved: {fp}_source.html')
        except Exception as e:
            _log('SAVE', f'Source HTML FAILED: {e}')
    try:
        import html2text
        h = html2text.HTML2Text(); h.body_width = 0; h.ignore_links = False
        md = h.handle(a.get('content_html',''))
    except ImportError:
        from bs4 import BeautifulSoup
        md = f"# {a.get('title','')}\n\n{BeautifulSoup(a.get('content_html',''), 'html.parser').get_text(strip=True)}"
    try:
        atomic_io.atomic_write(os.path.join(ws, f'{fp}.md'), md)
        _log('SAVE', f'MD saved: {fp}.md')
    except Exception as e:
        _log('SAVE', f'MD FAILED: {e}'); return False
    return True

def _update_article_index(article, slug):
    """Insert new article into the hardcoded JS array in articles/index.html."""
    index_path = os.path.join(_SKILL_DIR, 'articles', 'index.html')
    if not os.path.exists(index_path):
        _log('INDEX', 'articles/index.html not found, skip')
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    marker = 'var articles = ['
    pos = content.find(marker)
    if pos == -1:
        _log('INDEX', 'articles array not found, skip')
        return

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

    entry = (
        "{ cat:'travel-guide', catLabel:'Travel Guide', catLabelZh:'旅行指南', "
        f"title:'{title}', titleZh:'{title}', "
        f"excerpt:'{desc[:120]}', excerptZh:'{desc[:120]}', "
        f"date:'{date_str}', time:'5 min read', "
        f"url:'{slug}.html', img:'{cover}', featured:false }}"
    )

    insert_pos = pos + len(marker)
    after_marker = content[insert_pos:insert_pos + 10].strip()
    if after_marker:
        entry = '\n    ' + entry + ',\n    '
    else:
        entry = '\n    ' + entry + '\n  '

    new_content = content[:insert_pos] + entry + content[insert_pos:]
    atomic_io.atomic_write(index_path, new_content)
    _log('INDEX', f'Inserted article into index.html (slug={slug})')


def step_config(a, slug, fp, settings):
    cp = os.path.join(_SKILL_DIR, 'config', 'articles.yaml')
    if yaml_updater.slug_exists(cp, slug):
        _log('CONFIG', f'Slug {slug} exists, skip'); return True
    na = {
        'slug': slug, 'file_pattern': fp, 'has_en_translation': True,
        'category': settings.get('defaults',{}).get('category','travel-guide'),
        'catLabel': settings.get('defaults',{}).get('catLabel','Travel Guide'),
        'catLabelZh': settings.get('defaults',{}).get('catLabelZh','旅行指南'),
        'date': f'{datetime.now():%Y-%m-%d}', 'time': '5 min read',
        'author': {'zh': a.get('author','') or a.get('account_name','未知'), 'en': a.get('author','') or 'Unknown'},
        'title': {'zh': a.get('title',''), 'en': a.get('title','')},
        'excerpt': {'zh': (a.get('description','') or a.get('title',''))[:120],
                     'en': (a.get('description','') or a.get('title',''))[:120]},
        'related': []}
    try:
        r = yaml_updater.add_new_article(cp, na)
        _log('CONFIG', f'Config {"OK" if r else "FAILED"}')
        return r if r else True
    except Exception as e:
        _log('CONFIG', f'WARNING: {e}'); return True

def step_build(slug, settings):
    bp = os.path.join(_SCRIPT_DIR, 'build.py')
    if not os.path.exists(bp):
        _log('BUILD', 'build.py not found, skip'); return True
    phases = ['convert', 'rebuild', 'sync']
    if settings.get('build',{}).get('validate', True):
        phases.append('validate')
    ok = True
    for p in phases:
        _log('BUILD', f'--{p}...')
        try:
            r = subprocess.run([sys.executable, bp, f'--{p}', '--slug', slug],
                capture_output=True, text=True, timeout=300, cwd=_SKILL_DIR)
            if r.returncode != 0:
                _log('BUILD', f'--{p} FAILED: {r.stderr[:200]}'); ok = False
            else:
                _log('BUILD', f'--{p} OK')
        except Exception as e:
            _log('BUILD', f'--{p} error: {e}'); ok = False
    return ok

def step_git(slug, settings):
    rp = settings.get('repository',{}).get('path', _SKILL_DIR)
    branch = settings.get('repository',{}).get('branch', 'claude-code-torch')
    if not rp or not git_manager.is_git_repo(rp):
        _log('GIT', 'No git repo, skip'); return False
    msg = f'feat(article): add {slug}'
    for cmd, args in [('add',['.']), ('commit',[msg]), ('push',['origin', branch])]:
        ok, m = getattr(git_manager, f'git_{cmd}')(rp, *args)
        if not ok:
            _log('GIT', f'{cmd} FAILED: {m}'); return False
        _log('GIT', f'{cmd} OK')
    return True

def run_pipeline(url, slug=None, skip_push=False):
    s = _load_settings()
    if skip_push:
        s.setdefault('build',{})['auto_push'] = False
    _log('PIPELINE', f'Starting: {url[:80]}...')
    a = step_fetch(url, s)
    if not a:
        return False
    slug = slug or _gen_slug(a.get('title',''))
    fp = _gen_fp(a.get('title',''))
    _log('PIPELINE', f'Slug={slug} FP={fp}')
    ok = step_save(a, fp, s); step_config(a, slug, fp, s); step_build(slug, s)
    if ok:
        _update_article_index(a, slug)
    if not skip_push:
        step_git(slug, s)
    print(f'\n完成! 文章: {a.get("title","")}  标识: {slug}')
    return ok

def main():
    ap = argparse.ArgumentParser(description='TibetWorkflow 一键发布')
    ap.add_argument('--url','-u', required=True)
    ap.add_argument('--slug','-s')
    ap.add_argument('--skip-push', action='store_true')
    args = ap.parse_args()
    sys.exit(0 if run_pipeline(args.url, args.slug, args.skip_push) else 1)

if __name__ == '__main__':
    main()
