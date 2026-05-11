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
import os, sys, re, argparse, subprocess
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
    slug = re.sub(r'[^\w\s-]', '', title.lower().strip())
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    return slug[:80].rstrip('-') or f'article-{datetime.now():%Y%m%d}'

def _gen_fp(title):
    fp = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
    fp = re.sub(r'[\s]+', '', fp)
    return fp[:120] or f'未命名文章{datetime.now():%Y%m%d}'

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
