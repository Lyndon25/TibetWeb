#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix missing English content in articles by extracting from source HTML/MD files.
"""
import os
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString

SRC_DIR = 'AddingArticleWorkSpace/1'
ARTICLES_DIR = 'articles'

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

def render_blocks(blocks):
    parts = []
    for btype, content in blocks:
        if btype == 'img':
            parts.append(f'<img src="{content}" alt="" loading="lazy">')
        elif btype == 'h2':
            parts.append(f'<h2>{content}</h2>')
        elif btype == 'h3':
            parts.append(f'<h3>{content}</h3>')
        elif btype == 'strong':
            parts.append(f'<p><strong>{content}</strong></p>')
        elif btype == 'p':
            parts.append(f'<p>{content}</p>')
    return '\n'.join(parts)

def extract_en_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    en_div = soup.find(id='english_translation')
    if not en_div:
        return None
    
    blocks = []
    # Look for structural elements inside the translation div
    for elem in en_div.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'img'], recursive=True):
        if elem.name == 'img':
            src = elem.get('src', '')
            if src:
                blocks.append(('img', src))
        elif elem.name in ('h2', 'h3', 'h4', 'h5'):
            text = elem.get_text(strip=True)
            if text and 'english translation' not in text.lower():
                blocks.append(('h2' if elem.name == 'h2' else 'h3', text))
        elif elem.name == 'p':
            text = elem.get_text(strip=True)
            # Skip captions and metadata lines that look like editor credits
            if text and len(text) > 2 and not text.startswith('▲') and 'editor:' not in text.lower() and 'photo credit' not in text.lower():
                # Check if the paragraph is essentially a bold heading
                strong_child = elem.find(['strong', 'b'])
                if strong_child and len(elem.get_text(strip=True)) < 60 and elem.get_text(strip=True) == strong_child.get_text(strip=True):
                    blocks.append(('strong', text))
                else:
                    blocks.append(('p', text))
    
    # Deduplicate consecutive identical blocks
    deduped = []
    for b in blocks:
        if not deduped or b != deduped[-1]:
            deduped.append(b)
    
    return render_blocks(deduped)

def extract_en_from_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
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
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        if content:
            parts.append(f'<p>{content}</p>')
    
    return '\n'.join(parts)

def get_en_content(slug, pattern):
    files = find_source_files(pattern)
    html_file = next((f for f in files if f.endswith('.html')), None)
    md_file = next((f for f in files if f.endswith('.md')), None)
    
    if html_file:
        en = extract_en_from_html(html_file)
        if en:
            return en, 'html'
    
    if md_file:
        en = extract_en_from_md(md_file)
        if en:
            return en, 'md'
    
    return None, None

def patch_article(slug, en_content):
    filepath = os.path.join(ARTICLES_DIR, f'{slug}.html')
    if not os.path.exists(filepath):
        print(f"  SKIP: {filepath} not found")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    en_match = re.search(r'<div class="lang-content" data-lang="en">\s*(.*?)\s*</div>', html, re.DOTALL)
    if not en_match:
        print(f"  SKIP: No English block found in {slug}")
        return False
    
    current_en = en_match.group(1).strip()
    # If already substantial (>800 chars), skip
    if len(current_en) > 800:
        print(f"  SKIP: {slug} already has substantial English ({len(current_en)} chars)")
        return False
    
    new_en_block = f'<div class="lang-content" data-lang="en">\n{en_content}\n</div>'
    new_html = re.sub(
        r'<div class="lang-content" data-lang="en">.*?</div>',
        new_en_block,
        html,
        count=1,
        flags=re.DOTALL
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    return True

def main():
    fixed = 0
    skipped = 0
    no_source = 0
    
    for slug, pattern in SLUG_TO_PATTERN.items():
        if not pattern:
            continue
        
        print(f"Processing: {slug}")
        en_content, source_type = get_en_content(slug, pattern)
        
        if not en_content:
            print(f"  No English source found")
            no_source += 1
            continue
        
        if patch_article(slug, en_content):
            print(f"  FIXED from {source_type} ({len(en_content)} chars)")
            fixed += 1
        else:
            skipped += 1
    
    print(f"\nDone! Fixed: {fixed}, Skipped: {skipped}, No source: {no_source}")

if __name__ == '__main__':
    main()
