#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix mixed-language contamination in lang-content blocks.
Strategy:
1. For EN blocks with Chinese: re-extract English from source files more carefully.
2. For ZH blocks with English words: mostly proper nouns (Sarah, SPF, etc.) — keep them.
"""
import os
import re
from bs4 import BeautifulSoup

SRC_DIR = 'AddingArticleWorkSpace/1'
ARTICLES_DIR = 'articles'
LOG_FILE = 'scripts/fix_mixed_lang_log.md'

SLUG_TO_PATTERN = {
    '2026-tibet-year-round-travel-guide': '2026一起去西藏这个人生必去目的地全年出游攻略请查收',
    'tibet-celebrity-route-beginners': '被问爆的西藏明星同款线小白也能冲',
    'planet-earth-ngari': '当我以地球脉动的方式打开阿里',
    'first-tibet-trip-guide': '第一次去西藏旅行看这篇就够了',
    'ngari-spring-colors': '多巴胺爆棚阿里春日限定色号上线',
    'g216-coqen-blue-dream': '高原之巅蓝色梦境在216国道遇见措勤这些地方你可曾到达',
    'tibet-6-classic-routes': '旅游西藏6条经典路线311天全涵盖',
    'gerze-changtang-red-blue': '秘境改则在羌塘腹地聆听红与蓝的交响',
    '6-routes-update-tibet-list': '收藏6条游线更新你的西藏旅行清单',
    'ali-year-round-travel-guide': '所有人阿里全年出游攻略请查收',
    'tibet-52-tips-avoid-pitfalls': '西藏旅游超全避雷攻略52条血泪总结进藏前必看',
    'lens-nature-human-harmony': '在他的镜头里看见人与自然相融之美',
    'qingming-tibet-travel-guide': '绝美刷屏清明西藏出游攻略小众踏青地治愈整个春天',
    'spring-snow-peach-blossoms': '春染雪域桃花沐雪绘出好钱景',
    'spring-economy-tibet-tourism': '春日经济激发西藏文旅消费市场活力',
    'bomi-spring-photography': '每一张都能当壁纸这座宝藏小城的春天太惊艳了',
    'may-day-tibet-lazy-guide': '五一游西藏10种懒人玩法舒服',
}

def find_source_files(pattern):
    files = []
    for f in os.listdir(SRC_DIR):
        if pattern in f:
            files.append(os.path.join(SRC_DIR, f))
    return files

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def extract_en_from_md_clean(filepath):
    """Extract English translation section from MD more carefully."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Find English Translation section
    match = re.search(r'(?:^|\n)#\s*English Translation.*', text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    
    en_text = text[match.start():]
    lines = en_text.split('\n')
    parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^#\s*English Translation', line, re.I):
            continue
        # Skip lines that are mostly Chinese (likely not translated yet)
        chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', line)) / max(len(line), 1)
        if chinese_ratio > 0.3:
            continue
        if line.startswith('!['):
            m = re.search(r'!\[.*?\]\((.*?)\)', line)
            if m:
                parts.append(f'<img src="{m.group(1)}" alt="" loading="lazy">')
            continue
        if line.startswith('## '):
            parts.append(f'<h2>{line[3:]}</h2>')
            continue
        if line.startswith('### '):
            parts.append(f'<h3>{line[4:]}</h3>')
            continue
        if line.startswith('- '):
            content = line[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            parts.append(f'<p>• {content}</p>')
            continue
        content = line
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        if content:
            parts.append(f'<p>{content}</p>')
    
    return '\n'.join(parts)

def extract_en_from_html_clean(filepath):
    """Extract English from source HTML, avoiding Chinese contamination."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    en_div = soup.find(id='english_translation')
    if not en_div:
        return None
    
    parts = []
    for elem in en_div.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'img'], recursive=True):
        if elem.name == 'img':
            src = elem.get('src', '')
            if src:
                parts.append(f'<img src="{src}" alt="" loading="lazy">')
        elif elem.name in ('h2', 'h3', 'h4', 'h5'):
            text = elem.get_text(strip=True)
            if text and 'english translation' not in text.lower():
                # Skip if mostly Chinese
                if not has_chinese(text) or len(re.findall(r'[\u4e00-\u9fff]', text)) / len(text) < 0.1:
                    parts.append(f'<h2>{text}</h2>' if elem.name == 'h2' else f'<h3>{text}</h3>')
        elif elem.name == 'p':
            text = elem.get_text(strip=True)
            if text and len(text) > 2 and not text.startswith('▲'):
                # Skip editor credits
                if any(k in text.lower() for k in ['editor:', 'photo credit', 'proofreader', 'reviewer', 'source:']):
                    continue
                # Skip if mostly Chinese
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
                if len(chinese_chars) / max(len(text), 1) > 0.3:
                    continue
                strong_child = elem.find(['strong', 'b'])
                if strong_child and len(text) < 80 and text == strong_child.get_text(strip=True):
                    parts.append(f'<p><strong>{text}</strong></p>')
                else:
                    parts.append(f'<p>{text}</p>')
    
    return '\n'.join(parts)

def get_clean_en_content(slug, pattern):
    files = find_source_files(pattern)
    html_file = next((f for f in files if f.endswith('.html')), None)
    md_file = next((f for f in files if f.endswith('.md')), None)
    
    if md_file:
        en = extract_en_from_md_clean(md_file)
        if en:
            return en, 'md'
    
    if html_file:
        en = extract_en_from_html_clean(html_file)
        if en:
            return en, 'html'
    
    return None, None

def patch_article(slug, en_content, source_type, log_lines):
    filepath = os.path.join(ARTICLES_DIR, f'{slug}.html')
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find the article-body en block (not hero/breadcrumb)
    match = re.search(r'(<div class="article-body">.*?<div class="lang-content" data-lang="en">)(.*?)(</div>.*?</div>\s*<nav class="article-nav">)', html, re.DOTALL)
    if not match:
        # Fallback: any en block after zh block in article-body
        match = re.search(r'(<div class="lang-content" data-lang="zh">.*?</div>\s*)(<div class="lang-content" data-lang="en">)(.*?)(</div>)', html, re.DOTALL)
        if not match:
            return False
        prefix = match.group(1) + match.group(2)
        suffix = match.group(4)
        current = match.group(3)
    else:
        prefix = match.group(1)
        current = match.group(2)
        suffix = match.group(3)
    
    current_clean = current.strip()
    new_clean = en_content.strip()
    
    if current_clean == new_clean:
        return False
    
    new_block = f'{prefix}{en_content}{suffix}'
    
    if match.group(1).startswith('<div class="article-body">'):
        html_new = re.sub(r'<div class="article-body">.*?<nav class="article-nav">', new_block, html, count=1, flags=re.DOTALL)
    else:
        html_new = html[:match.start()] + new_block + html[match.end():]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_new)
    
    log_lines.append(f"### {slug}.html\n")
    log_lines.append(f"**EN block re-extracted** (source: {source_type})\n")
    return True

def main():
    log_lines = ["# Mixed Language Fix Log\n\n"]
    fixed = 0
    skipped = 0
    no_source = 0
    
    for slug, pattern in SLUG_TO_PATTERN.items():
        if not pattern:
            continue
        
        filepath = os.path.join(ARTICLES_DIR, f'{slug}.html')
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check if EN block has Chinese contamination
        en_match = re.search(r'<div class="lang-content" data-lang="en">(.*?)</div>', html, re.DOTALL)
        if not en_match:
            continue
        
        en_text = BeautifulSoup(en_match.group(1), 'html.parser').get_text()
        if not has_chinese(en_text):
            skipped += 1
            continue
        
        print(f"Fixing: {slug} (EN block has Chinese)")
        en_content, source_type = get_clean_en_content(slug, pattern)
        
        if not en_content:
            print(f"  No clean source found")
            no_source += 1
            continue
        
        if patch_article(slug, en_content, source_type, log_lines):
            print(f"  FIXED from {source_type}")
            log_lines.append(f"- Fixed EN block contamination\n\n")
            fixed += 1
        else:
            skipped += 1
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    
    print(f"\nDone! Fixed: {fixed}, Skipped: {skipped}, No source: {no_source}")
    print(f"Log written to {LOG_FILE}")

if __name__ == '__main__':
    main()
