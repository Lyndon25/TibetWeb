import os
import re
from bs4 import BeautifulSoup

articles_dir = "articles"
src_dir = "AddingArticleWorkSpace/1"

FILE_MAP = {
    '2026-tibet-year-round-travel-guide': '2026一起去西藏这个人生必去目的地全年出游攻略请查收（中英）',
    'tibet-celebrity-route-beginners': '被问爆的西藏明星同款线小白也能冲（中英）',
    'planet-earth-ngari': '当我以地球脉动的方式打开阿里（中英）',
    'first-tibet-trip-guide': '第一次去西藏旅行看这篇就够了（中英）',
    'ngari-spring-colors': '多巴胺爆棚阿里春日限定色号上线（中英）',
    'g216-coqen-blue-dream': '高原之巅蓝色梦境在216国道遇见措勤这些地方你可曾到达（中英）',
    'tibet-6-classic-routes': '旅游西藏6条经典路线311天全涵盖（中英）',
    'gerze-changtang-red-blue': '秘境改则在羌塘腹地聆听红与蓝的交响（中英）',
    '6-routes-update-tibet-list': '收藏6条游线更新你的西藏旅行清单（中英）',
    'ali-year-round-travel-guide': '所有人阿里全年出游攻略请查收（中英）',
    'tibet-52-tips-avoid-pitfalls': '西藏旅游超全避雷攻略52条血泪总结进藏前必看（中英）',
    'lens-nature-human-harmony': '在他的镜头里看见人与自然相融之美（中英）',
    'qingming-tibet-travel-guide': '绝美刷屏清明西藏出游攻略小众踏青地治愈整个春天（中英）',
    'spring-snow-peach-blossoms': '春染雪域桃花沐雪绘出好钱景（中英）',
    'spring-economy-tibet-tourism': '春日经济激发西藏文旅消费市场活力（中英）',
    'bomi-spring-photography': '每一张都能当壁纸这座宝藏小城的春天太惊艳了（中英）',
}

def clean_img_tag(m: re.Match) -> str:
    attrs = m.group(1)
    src_match = re.search(r'src=["\']([^"\']+)["\']', attrs)
    data_src_match = re.search(r'data-src=["\']([^"\']+)["\']', attrs)
    url = src_match.group(1) if src_match else (data_src_match.group(1) if data_src_match else '')
    return f'<img src="{url}" alt="" loading="lazy">'

def extract_en_html(src_path: str) -> str | None:
    with open(src_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    en_div = soup.find('div', id='english_translation')
    if not en_div:
        return None

    inner = en_div.find('div', style=lambda s: bool(s and 'line-height' in s))
    if not inner:
        inner = en_div

    raw = str(inner)
    close_tag = '</div>'
    content_start = raw.find('>') + 1
    # Remove trailing </div>
    if raw.rstrip().endswith(close_tag):
        raw = raw[content_start:raw.rfind(close_tag)]
    else:
        raw = raw[content_start:]

    # Clean up
    raw = re.sub(r'<h2[^>]*>\s*English Translation\s*</h2>', '', raw, flags=re.S)
    raw = re.sub(r'<p[^>]*style="text-align:center;"[^>]*>\s*(<img[^>]*>)\s*</p>', r'\1', raw, flags=re.S)
    raw = re.sub(r'<p[^>]*style="font-size:13px;color:#999;text-align:center;"[^>]*>(.*?)</p>', r'<p class="caption">\1</p>', raw, flags=re.S)
    raw = re.sub(r' style="[^"]*"', '', raw)
    raw = re.sub(r' data-src="[^"]*"', '', raw)
    raw = re.sub(r'<img([^>]*)>', clean_img_tag, raw)
    raw = re.sub(r'<p[^>]*>\s*(Editor:|Source:|Proofreader:|Reviewer:).*?</p>', '', raw, flags=re.S)
    raw = raw.replace('&', '&')

    return raw.strip()

def find_en_div_positions(content: str, after_pos: int = 0) -> tuple[int | None, int | None]:
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

def fix_article(article_path: str, en_html: str) -> bool:
    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from en_html (first h1/h2/h3)
    title_match = re.search(r'<h[123][^>]*>(.*?)</h[123]>', en_html, re.S)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    else:
        # Fallback: use first line of text
        plain = re.sub(r'<[^>]+>', '', en_html)
        title = plain.strip()[:60] if plain.strip() else 'Article'

    body_start = content.find('<div class="article-body">')

    # Find all EN divs
    en_divs: list[tuple[int, int]] = []
    pos = 0
    while True:
        s, e = find_en_div_positions(content, pos)
        if s is None or e is None:
            break
        en_divs.append((s, e))
        pos = e

    # Hero EN = before body, Body EN = after body
    hero_en: tuple[int, int] | None = None
    body_en: tuple[int, int] | None = None
    for s, e in en_divs:
        if body_start > 0 and s < body_start:
            hero_en = (s, e)
        elif body_start > 0 and s > body_start:
            body_en = (s, e)
            break

    # Replace hero EN
    if hero_en:
        s, e = hero_en
        new_hero = f'<div class="lang-content" data-lang="en"><h1 class="article-hero__title">{title}</h1></div>'
        content = content[:s] + new_hero + content[e:]

    # Replace body EN - must re-find after hero replacement
    if body_en:
        new_body_start = content.find('<div class="article-body">')
        if new_body_start >= 0:
            s, e = find_en_div_positions(content, new_body_start)
            if s is not None and e is not None:
                new_body = f'<div class="lang-content" data-lang="en">\n{en_html}\n</div>'
                content = content[:s] + new_body + content[e:]

    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

log: list[str] = []
for slug, src_pattern in FILE_MAP.items():
    article_path = os.path.join(articles_dir, f"{slug}.html")

    # Find source file
    src_file = None
    for fname in os.listdir(src_dir):
        if fname.startswith(src_pattern) and fname.endswith('.html'):
            src_file = fname
            break

    if not src_file:
        log.append(f"{slug}.html: Source file not found")
        continue

    src_path = os.path.join(src_dir, src_file)
    en_html = extract_en_html(src_path)

    if not en_html:
        log.append(f"{slug}.html: No EN translation found")
        continue

    if fix_article(article_path, en_html):
        log.append(f"{slug}.html: Rebuilt from source ({len(en_html)} chars)")
    else:
        log.append(f"{slug}.html: Fix failed")

with open("scripts/rebuild_en_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
