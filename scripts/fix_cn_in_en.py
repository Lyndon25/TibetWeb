import os
import re

articles_dir = "articles"

REPLACEMENTS = {
    'ali-year-round-travel-guide.html': [
        ('光影 (light and shadow)', 'light and shadow'),
    ],
    'g216-coqen-blue-dream.html': [
        ('<strong>Coqen (措勤)</strong>', '<strong>Coqen</strong>'),
    ],
    'may-day-tibet-lazy-guide.html': [
        ('矿物颜料', 'mineral pigments'),
        ('藏面', 'Tibetan noodles'),
        ('炸土豆', 'fried potatoes'),
        ('甜茶馆', 'sweet tea house'),
        ('一壶酥油茶', 'a pot of butter tea'),
    ],
    'motorcycle-healing-journey.html': [
        ('暴走模式', 'berserk mode'),
    ],
    'motorcycle-tibet-shannan.html': [
        ('泥土味', 'earthy scent'),
    ],
    'sichuan-tibet-central-route.html': [
        ('颠簸程度堪称"全身按摩"', 'bumpy enough to feel like a full-body massage'),
        ('简陋', 'simple and crude'),
        ('"with mice."', '"with mice."'),
    ],
    'spring-economy-tibet-tourism.html': [
        ('雪域高原', 'snowland plateau'),
        ('将西藏春天的旅游答卷铺展在游客面前', 'presents Tibet\'s spring tourism offerings to visitors'),
    ],
    'tibet-celebrity-route-beginners.html': [
        ('徒步中国 (Hiking China)', 'Hiking China'),
        ('一措再措', '"one lake after another"'),
        ('库拉岗日', 'Kula Kangri'),
    ],
    'wheels-shackles-tibet.html': [
        ('上去？你要上去？', '"Going up? Are you going up?"'),
        ('来吃嘛！', '"Come eat!"'),
    ],
}

log = []

for fn, replacements in REPLACEMENTS.items():
    path = os.path.join(articles_dir, fn)
    if not os.path.exists(path):
        log.append(f"{fn}: File not found")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find EN body block
    body_start = content.find('<div class="article-body">')
    en_start = content.find('<div class="lang-content" data-lang="en">', body_start)
    
    if en_start < 0:
        log.append(f"{fn}: No EN body block found")
        continue
    
    # Find EN body block end
    content_start = en_start + len('<div class="lang-content" data-lang="en">')
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
                en_end = next_close + 6
                break
            p = next_close + 6
    else:
        log.append(f"{fn}: Could not find EN body end")
        continue
    
    en_block = content[en_start:en_end]
    original = en_block
    
    for old, new in replacements:
        en_block = en_block.replace(old, new)
    
    if en_block != original:
        content = content[:en_start] + en_block + content[en_end:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        log.append(f"{fn}: Fixed {len(replacements)} replacements")
    else:
        log.append(f"{fn}: No replacements applied")

with open("scripts/fix_cn_in_en_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))
print('\n'.join(log))
