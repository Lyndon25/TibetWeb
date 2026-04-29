import os
import re

articles_dir = "articles"

def find_en_div_positions(content, after_pos=0):
    idx = content.find('<div class="lang-content" data-lang="en">', after_pos)
    if idx < 0:
        return (None, None)
    start = idx
    content_start = idx + len('<div class="lang-content" data-lang="en">')
    depth = 1
    p = content_start
    while depth > 0 and p < len(content):
        next_open = content.find('<div', p)
        next_close = content.find('</div>', p)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            p = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                end = next_close + 6
                return (start, end)
            p = next_close + 6
    return (None, None)

def extract_body_block(content, lang):
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return None
    search_start = body_start
    pattern = f'<div class="lang-content" data-lang="{lang}">'
    idx = content.find(pattern, search_start)
    if idx < 0:
        return None
    start = idx
    content_start = idx + len(pattern)
    depth = 1
    p = content_start
    while depth > 0 and p < len(content):
        next_open = content.find('<div', p)
        next_close = content.find('</div>', p)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            p = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                end = next_close + 6
                break
            p = next_close + 6
    else:
        return None
    return content[start:end]

def count_imgs(block):
    return len(re.findall(r'<img\b', block, re.I))

# Manual title translations for files without source
TITLE_FIXES = {
    'altitude-sickness-tips': 'The Yellow Wolf: Essential Tips for Altitude Sickness on Motorcycle Tours',
    'bianba-motorcycle-diary': 'Bianba Chronicles: Enxing Rider\'s Tibet Motorcycle Journey',
    'motorcycle-healing-journey': 'Let\'s Ride: A Healing Journey Through Tibet by Motorcycle',
    'motorcycle-tibet-gear-guide': 'Hey Bro, What\'s the Most Important Gear for Your Tibet Motorcycle Trip?!',
    'wheels-shackles-tibet': 'Chains on Wheels: A Fable of Survival in Tibet and Modern Society',
}

log = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith('.html') or fn == 'index.html':
        continue
    path = os.path.join(articles_dir, fn)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    slug = fn.replace('.html', '')
    body_start = content.find('<div class="article-body">')
    changed = False
    
    # === FIX 1: Shorten EN hero ===
    hero_en = None
    pos = 0
    while True:
        s, e = find_en_div_positions(content, pos)
        if s is None:
            break
        if body_start > 0 and s < body_start:
            hero_en = (s, e)
        pos = e
    
    if hero_en:
        s, e = hero_en
        hero_text = content[s:e]
        stripped = re.sub(r'<[^>]+>', '', hero_text).strip()
        
        zh_hero_match = re.search(r'<div class="lang-content" data-lang="zh">(.*?)</div>', content[:body_start], re.S)
        zh_stripped = re.sub(r'<[^>]+>', '', zh_hero_match.group(1)).strip() if zh_hero_match else ''
        
        if len(stripped) > len(zh_stripped) * 2 + 10:
            title_match = re.search(r'<h[123][^>]*>(.*?)</h[123]>', hero_text, re.S)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            else:
                title = stripped[:80]
            
            # Check if this file needs manual title fix
            if slug in TITLE_FIXES:
                title = TITLE_FIXES[slug]
            
            # Also check for Chinese in title
            if re.search(r'[\u4e00-\u9fff]', title) and slug in TITLE_FIXES:
                title = TITLE_FIXES[slug]
            
            new_hero = f'<div class="lang-content" data-lang="en"><h1 class="article-hero__title">{title}</h1></div>'
            content = content[:s] + new_hero + content[e:]
            changed = True
            log.append(f"{fn}: Shortened hero EN ({len(stripped)} -> {len(title)} chars)")
    
    # === FIX 2: Remove excess EN body images ===
    zh_block = extract_body_block(content, 'zh')
    en_block = extract_body_block(content, 'en')
    
    if zh_block and en_block:
        zh_imgs = count_imgs(zh_block)
        en_imgs = count_imgs(en_block)
        
        if en_imgs > zh_imgs:
            # Need to remove excess images from EN body
            excess = en_imgs - zh_imgs
            inner = en_block[len('<div class="lang-content" data-lang="en">'):-6]
            
            # Find all img positions
            img_matches = list(re.finditer(r'<img[^>]*>', inner, re.I))
            
            if len(img_matches) > zh_imgs:
                # Remove excess images from the end
                to_remove = img_matches[zh_imgs:]
                # Build new inner by removing these img tags
                # Work backwards to preserve indices
                new_inner = inner
                for m in reversed(to_remove):
                    new_inner = new_inner[:m.start()] + new_inner[m.end():]
                
                new_en = f'<div class="lang-content" data-lang="en">{new_inner}</div>'
                en_start = content.find(en_block)
                if en_start >= 0:
                    content = content[:en_start] + new_en + content[en_start + len(en_block):]
                    changed = True
                    log.append(f"{fn}: Removed {excess} excess EN imgs ({en_imgs} -> {zh_imgs})")
    
    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

with open("scripts/final_comprehensive_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))
print('\n'.join(log))
