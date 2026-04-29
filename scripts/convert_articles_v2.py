#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert WeChat-style HTML articles to standard Tibet Moto Travel article format v2.
Improved: merge short paragraphs, detect captions, cleaner content extraction.
"""

import os
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString

ARTICLES_META = [
    {
        'file_pattern': '2026一起去西藏这个人生必去目的地全年出游攻略请查收',
        'slug': '2026-tibet-year-round-travel-guide',
        'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
        'date': 'Jan 5, 2026', 'time': '8 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
        'titleZh': '2026一起去西藏！这个人生必去目的地，全年出游攻略请查收！',
        'titleEn': "2026 Let's Go to Tibet! Your Year-Round Travel Guide to This Must-Visit Destination",
        'excerptZh': '从春花到冬雪，从林芝桃花到阿里荒原，2026西藏全年出游攻略帮你规划最佳旅行时间。',
        'excerptEn': 'From spring blossoms to winter snow, from Nyingchi peach flowers to Ali wilderness — plan your perfect Tibet trip month by month.',
    },
    {
        'file_pattern': '被问爆的西藏明星同款线小白也能冲',
        'slug': 'tibet-celebrity-route-beginners',
        'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
        'date': 'Mar 15, 2026', 'time': '7 min read', 'authorZh': '小鱼/般般', 'authorEn': 'Xiaoyu / Banban',
        'titleZh': '被问爆的西藏"明星同款线"，小白也能冲！',
        'titleEn': "Tibet's Most Asked-About Celebrity Route — Beginners Welcome!",
        'excerptZh': '库拉岗日徒步节、羊卓雍错环湖、普莫雍错蓝冰……这些西藏明星同款线路，新手也能轻松驾驭。',
        'excerptEn': 'Kula Gangri trekking, Yamdrok Lake circuit, Pumoyongcuo blue ice — these celebrity-level Tibet routes are beginner-friendly too.',
    },
    {
        'file_pattern': '当我以地球脉动的方式打开阿里',
        'slug': 'planet-earth-ngari',
        'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
        'date': 'Apr 8, 2026', 'time': '6 min read', 'authorZh': '文化西藏', 'authorEn': 'Culture Tibet',
        'titleZh': '当我以"地球脉动"的方式打开阿里',
        'titleEn': 'Opening Ngari Through a "Planet Earth" Lens',
        'excerptZh': '用纪录片视角探索西藏阿里——从冈仁波齐到玛旁雍错，感受地球最原始的脉动。',
        'excerptEn': "Exploring Tibet's Ngari through a documentary lens — from Mount Kailash to Lake Manasarovar, feel the planet's primordial pulse.",
    },
    {
        'file_pattern': '第一次去西藏旅行看这篇就够了',
        'slug': 'first-tibet-trip-guide',
        'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
        'date': 'Feb 20, 2026', 'time': '10 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
        'titleZh': '第一次去西藏旅行？看这篇就够了！',
        'titleEn': 'First Time in Tibet? This Guide Has Everything You Need!',
        'excerptZh': '高反预防、最佳季节、必备装备、经典路线——首次进藏全攻略，一篇解决所有疑问。',
        'excerptEn': 'Altitude sickness prevention, best seasons, essential gear, classic routes — your complete first-timer guide to Tibet.',
    },
    {
        'file_pattern': '多巴胺爆棚阿里春日限定色号上线',
        'slug': 'ngari-spring-colors',
        'cat': 'photography', 'catLabel': 'Photography', 'catLabelZh': '摄影',
        'date': 'Apr 12, 2026', 'time': '5 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
        'titleZh': '多巴胺爆棚！阿里春日限定色号上线',
        'titleEn': 'Dopamine Overload! Ngari Spring Limited Color Palette',
        'excerptZh': '阿里春天的色彩盛宴——从土林的金黄到圣湖的湛蓝，每一帧都是大自然的调色盘。',
        'excerptEn': "A feast of spring colors in Ngari — from golden earth forests to sapphire sacred lakes, every frame is nature's palette.",
    },
    {
        'file_pattern': '高原之巅蓝色梦境在216国道遇见措勤这些地方你可曾到达',
        'slug': 'g216-coqen-blue-dream',
        'cat': 'routes', 'catLabel': 'Routes', 'catLabelZh': '路线',
        'date': 'Apr 18, 2026', 'time': '6 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
        'titleZh': '高原之巅蓝色梦境：在216国道遇见措勤，这些地方你可曾到达？',
        'titleEn': 'Blue Dreams on the Plateau Summit: Discovering Coqen Along G216',
        'excerptZh': '沿着216国道穿越羌塘高原，在措勤遇见遗世独立的蓝色梦境——仁多乡、扎日南木错、当惹雍错。',
        'excerptEn': 'Crossing the Changtang Plateau along G216, discover the secluded blue dreamscapes of Coqen.',
    },
    {
        'file_pattern': '旅游西藏6条经典路线311天全涵盖',
        'slug': 'tibet-6-classic-routes',
        'cat': 'routes', 'catLabel': 'Routes', 'catLabelZh': '路线',
        'date': 'Mar 1, 2026', 'time': '9 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
        'titleZh': '旅游西藏6条经典路线，3-11天全涵盖！',
        'titleEn': '6 Classic Tibet Routes, From 3 to 11 Days — All Covered!',
        'excerptZh': '从拉萨环线到阿里大北线，6条经典西藏路线覆盖3-11天行程，满足不同时间和预算需求。',
        'excerptEn': 'From Lhasa loop to Ali northern route, 6 classic Tibet itineraries spanning 3-11 days.',
    },
    {
        'file_pattern': '秘境改则在羌塘腹地聆听红与蓝的交响',
        'slug': 'gerze-changtang-red-blue',
        'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
        'date': 'Apr 15, 2026', 'time': '6 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
        'titleZh': '秘境改则：在羌塘腹地聆听红与蓝的交响',
        'titleEn': "Secret Gerze: Listening to the Symphony of Red and Blue in Changtang's Heart",
        'excerptZh': '深入羌塘腹地，在改则县感受红土达坂的赤红与扎日南木错的湛蓝交织出的自然交响。',
        'excerptEn': 'Deep into the Changtang heartland, experience the natural symphony where red earth passes meet sapphire lakes in Gerze.',
    },
    {
        'file_pattern': '收藏6条游线更新你的西藏旅行清单',
        'slug': '6-routes-update-tibet-list',
        'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
        'date': 'Mar 20, 2026', 'time': '7 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
        'titleZh': '收藏！6条游线更新你的西藏旅行清单',
        'titleEn': 'Bookmark These! 6 Routes to Refresh Your Tibet Travel List',
        'excerptZh': '6条精选西藏游线，从经典到小众，从人文到自然，全面升级你的西藏旅行清单。',
        'excerptEn': '6 curated Tibet routes, from classic to offbeat, from cultural to natural — a complete upgrade for your travel list.',
    },
    {
        'file_pattern': '所有人阿里全年出游攻略请查收',
        'slug': 'ali-year-round-travel-guide',
        'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
        'date': 'Mar 25, 2026', 'time': '8 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
        'titleZh': '所有人，阿里全年出游攻略请查收！',
        'titleEn': "Everyone, Here's Your Year-Round Ali Travel Guide!",
        'excerptZh': '阿里四季皆美——春赏花、夏观湖、秋探土林、冬览蓝冰，全年出游攻略一网打尽。',
        'excerptEn': 'Ali is beautiful all year round — spring flowers, summer lakes, autumn earth forests, winter blue ice.',
    },
    {
        'file_pattern': '西藏旅游超全避雷攻略52条血泪总结进藏前必看',
        'slug': 'tibet-52-tips-avoid-pitfalls',
        'cat': 'health', 'catLabel': 'Health & Safety', 'catLabelZh': '健康与安全',
        'date': 'Feb 10, 2026', 'time': '12 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
        'titleZh': '西藏旅游超全避雷攻略！52条血泪总结，进藏前必看！',
        'titleEn': 'Ultimate Tibet Pitfall Avoidance Guide! 52 Hard-Learned Tips Before You Go',
        'excerptZh': '52条进藏实用避坑指南，从高反预防到购物防骗，从路线规划到住宿选择，让你西藏之旅少走弯路。',
        'excerptEn': '52 practical Tibet tips, from altitude prevention to shopping scams, route planning to accommodation.',
    },
    {
        'file_pattern': '在他的镜头里看见人与自然相融之美',
        'slug': 'lens-nature-human-harmony',
        'cat': 'photography', 'catLabel': 'Photography', 'catLabelZh': '摄影',
        'date': 'Apr 5, 2026', 'time': '5 min read', 'authorZh': '西藏商报全媒体', 'authorEn': 'Tibet Business Daily',
        'titleZh': '在他的镜头里，看见人与自然相融之美',
        'titleEn': 'Through His Lens: The Beauty of Nature and Humanity in Harmony',
        'excerptZh': '西藏摄影师镜头下的高原生灵与游牧生活——黑颈鹤、藏羚羊、牧民转场，定格人与自然最动人的瞬间。',
        'excerptEn': "Highland wildlife and nomadic life through a Tibetan photographer's lens — black-necked cranes, Tibetan antelopes, herder migrations.",
    },
]

CAPTION_PATTERNS = re.compile(r'图源|摄|来源|摄影师|Photo by| photographer| photographer|小红书|@')
SKIP_PATTERNS = re.compile(r'^(使用完整服务|去阅读|在小说阅读器读本章|微信扫一扫|关注该公众号|阅读原文|预览时标签不可点)$')

def is_caption(text):
    """Check if text is an image caption."""
    text = text.strip()
    if len(text) < 5 or len(text) > 80:
        return False
    return bool(CAPTION_PATTERNS.search(text))


def clean_text(text):
    """Clean text content."""
    if not text:
        return ''
    text = text.replace('\u200b', '').replace('\xa0', ' ').replace('\u3000', ' ')
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def should_skip(text):
    """Check if text should be skipped."""
    text = text.strip()
    if not text or text in ('', ' ', '\n'):
        return True
    if SKIP_PATTERNS.match(text):
        return True
    return False


def extract_blocks(soup):
    """
    Extract content blocks from WeChat HTML.
    Returns list of (type, content) tuples.
    Types: 'img', 'h2', 'h3', 'p', 'caption', 'strong'
    """
    content_div = soup.find('div', class_='rich_media_content') or soup.find(id='js_content')
    if not content_div:
        content_div = soup.body if soup.body else soup

    blocks = []
    elements = list(content_div.descendants)

    i = 0
    while i < len(elements):
        elem = elements[i]
        if isinstance(elem, NavigableString):
            i += 1
            continue

        if elem.name == 'img':
            src = elem.get('data-src') or elem.get('src')
            if src and src.startswith('http'):
                blocks.append(('img', src))
            i += 1
            continue

        if elem.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = clean_text(elem.get_text())
            if text and not should_skip(text):
                if len(text) <= 30:
                    blocks.append(('h2', text))
                else:
                    blocks.append(('h3', text))
            i += 1
            continue

        if elem.name == 'p':
            text = clean_text(elem.get_text())
            if not text or should_skip(text):
                i += 1
                continue

            # Check if this is a caption for previous image
            if blocks and blocks[-1][0] == 'img' and is_caption(text):
                blocks.append(('caption', text))
                i += 1
                continue

            # Check if strong/b only
            strong_children = elem.find_all(['strong', 'b'])
            if strong_children and len(strong_children) == len([c for c in elem.children if not isinstance(c, NavigableString) or str(c).strip()]):
                # All children are strong/b
                blocks.append(('strong', text))
                i += 1
                continue

            # Check for list items
            if elem.find('ul') or elem.find('ol') or elem.find('li'):
                # Process list separately
                pass

            blocks.append(('p', text))
            i += 1
            continue

        if elem.name in ('section', 'div') and elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'img'], recursive=False):
            # Section with direct children - will be processed by descendants
            pass

        i += 1

    return blocks


def merge_paragraphs(blocks):
    """Merge short consecutive paragraphs into single paragraphs."""
    merged = []
    buffer = []

    for btype, content in blocks:
        if btype == 'img':
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype == 'caption':
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype in ('h2', 'h3', 'strong'):
            if buffer:
                merged.append(('p', ' '.join(buffer)))
                buffer = []
            merged.append((btype, content))
        elif btype == 'p':
            # Check if this is very short - merge into buffer
            if len(content) < 20 and not content.endswith('。') and not content.endswith('！') and not content.endswith('？'):
                buffer.append(content)
            else:
                if buffer:
                    buffer.append(content)
                    merged.append(('p', ' '.join(buffer)))
                    buffer = []
                else:
                    merged.append((btype, content))

    if buffer:
        merged.append(('p', ' '.join(buffer)))

    return merged


def render_blocks(blocks):
    """Render blocks to HTML."""
    parts = []
    for btype, content in blocks:
        if btype == 'img':
            parts.append(f'<img src="{content}" alt="" loading="lazy">')
        elif btype == 'caption':
            parts.append(f'<p class="caption">{content}</p>')
        elif btype == 'h2':
            parts.append(f'<h2>{content}</h2>')
        elif btype == 'h3':
            parts.append(f'<h3>{content}</h3>')
        elif btype == 'strong':
            parts.append(f'<p><strong>{content}</strong></p>')
        elif btype == 'p':
            parts.append(f'<p>{content}</p>')
    return '\n'.join(parts)


def process_article(filepath, meta, prev_slug=None, next_slug=None):
    """Process a single article."""
    print(f"Processing: {os.path.basename(filepath)}")

    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Extract cover image from og:image or first image
    cover = ''
    og_img = soup.find('meta', property='og:image')
    if og_img:
        cover = og_img.get('content', '')

    # Extract blocks
    blocks = extract_blocks(soup)
    blocks = merge_paragraphs(blocks)

    # Use first image as cover if no og:image
    if not cover:
        for btype, content in blocks:
            if btype == 'img':
                cover = content
                break

    zh_html = render_blocks(blocks)

    # English placeholder
    en_html = f'<p>{meta["excerptEn"]}</p>'

    # Build article HTML
    prev_link = ''
    if prev_slug:
        prev_meta = next((m for m in ARTICLES_META if m['slug'] == prev_slug), None)
        if prev_meta:
            prev_link = f'<a href="{prev_slug}.html" class="article-nav__link article-nav__link--prev"><span>&larr; Previous</span>{prev_meta["titleEn"]}</a>'

    next_link = ''
    if next_slug:
        next_meta = next((m for m in ARTICLES_META if m['slug'] == next_slug), None)
        if next_meta:
            next_link = f'<a href="{next_slug}.html" class="article-nav__link article-nav__link--next"><span>Next &rarr;</span>{next_meta["titleEn"]}</a>'

    nav_html = ''
    if prev_link or next_link:
        nav_html = f'<nav class="article-nav">\n{prev_link}\n{next_link}\n</nav>'

    related = [
        {'img': 'https://mmbiz.qlogo.cn/mmbiz_jpg/QkrbI0NiaOvBBJcrsnwFFRIhuRbQOosbOU4hQHeTyG2ARnbFUX6Rf4yrHr44uPTOhiay8MibPvOL7IUSiaRHYO9wkg/0?wx_fmt=jpeg', 'url': 'altitude-sickness-tips.html', 'title': '黄色的狼性 —— 关于摩旅高反需要注意事项'},
        {'img': 'https://mmbiz.qpic.cn/sz_mmbiz_jpg/V7KibjiawnhicqDC1wANzsMLsxPMy0CdjafSDlDwQYn3POAwib69K7AawDFjjtQkWuutc7QSzFjBg3s3S2wwaQlaS6KaI4qJvthIUn7ur3dL0uw/0?wx_fmt=jpeg', 'url': 'motorcycle-tibet-gear-guide.html', 'title': '老铁，您摩旅西藏最重要的装备是啥？！'},
        {'img': 'https://mmbiz.qpic.cn/sz_mmbiz_jpg/QkrbI0NiaOvDcNicYzMfJzKExLuy2Jlofxial3hSsg737fvMa7KnjuaFZrI6EyjlNr4zPUwLOh6gQibvziazPEaLZLQ/0?wx_fmt=jpeg', 'url': 'motorcycle-healing-journey.html', 'title': '走，我们骑摩托疗愈去'},
        {'img': 'https://mmbiz.qpic.cn/sz_mmbiz_jpg/QkrbI0NiaOvCxrkFdZedyLYLYcE8HrlynpTd1uudiaEohYRYsyaNWIe0ssULfs42ELJNiad1kj6DQlKhXRyGHwOkA/0?wx_fmt=jpeg', 'url': 'sichuan-tibet-central-route.html', 'title': '川藏中线变身记：从前是硬核地狱，如今是踏板天堂！'},
    ]
    related_html = '\n'.join([
        f'<div class="sidebar-article">\n<img class="sidebar-article__image" src="{r["img"]}" alt="" loading="lazy">\n<a class="sidebar-article__title" href="{r["url"]}">{r["title"]}</a>\n</div>'
        for r in related
    ])

    hero_style = f"--hero-image: url('{cover}')" if cover else ""

    template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta['titleZh']} | {meta['titleEn']}</title>
<link rel="stylesheet" href="../css/main.css">
<link rel="stylesheet" href="../css/lang.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script>
    (function(){{
      var k='site-lang',l=localStorage.getItem(k);
      if(l==='en'){{document.documentElement.setAttribute('lang','en');}}
      else{{document.documentElement.setAttribute('lang','zh-CN');}}
    }})();
  </script>
</head>
<body>
<nav class="nav nav--scrolled">
<div class="nav__inner">
<a href="../index.html" class="nav__logo">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1.75rem;height:1.75rem;"><path d="M9 17a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM19 17a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/><path d="M13 17V6a2 2 0 0 0-2-2H5l5.5 7H13z"/><path d="M13 17h3.5L22 10h-5"/></svg>
<span class="nav__logo-text">西藏摩旅</span>
</a>
<ul class="nav__links">
<li><a href="../index.html" data-lang-zh="首页" data-lang-en="Home">首页</a></li>
<li><a href="../routes.html" data-lang-zh="路线" data-lang-en="Routes">路线</a></li>
<li><a href="index.html" data-lang-zh="文章" data-lang-en="Articles">文章</a></li>
<li><a href="../about.html" data-lang-zh="关于" data-lang-en="About">关于</a></li>
</ul>
<div class="lang-switch">
<button class="lang-btn" id="btnZh" onclick="setLang('zh')">中文</button>
<span style="color:var(--color-border);font-size:0.7rem;">|</span>
<button class="lang-btn" id="btnEn" onclick="setLang('en')">EN</button>
</div>
</div>
</nav>

<header class="article-hero" style="{hero_style}">
<div class="article-hero__overlay"></div>
<div class="article-hero__content">
<div class="container container--narrow">
<div class="article-hero__meta">
<span class="article-hero__category">{meta['catLabel']}</span>
<span class="article-hero__date">{meta['date']}</span>
<span class="article-hero__author">{meta['authorZh']}</span>
</div>
<div class="lang-content" data-lang="zh"><h1 class="article-hero__title">{meta['titleZh']}</h1></div>
<div class="lang-content" data-lang="en"><h1 class="article-hero__title">{meta['titleEn']}</h1></div>
</div>
</div>
</header>

<div class="container">
<nav class="breadcrumb" style="margin-top: 2rem;">
<a href="../index.html" data-lang-zh="首页" data-lang-en="Home">首页</a>
<span>/</span>
<a href="index.html" data-lang-zh="文章" data-lang-en="Articles">文章</a>
<span>/</span>
<span class="lang-content" data-lang="zh">{meta['titleZh']}</span>
<span class="lang-content" data-lang="en">{meta['titleEn']}</span>
</nav>
</div>

<main class="container">
<div class="article-layout">
<div class="article-layout__main">
<div class="article-body">
<div class="lang-content" data-lang="zh">
{zh_html}
</div>
<div class="lang-content" data-lang="en">
{en_html}
</div>
</div>
{nav_html}
</div>
<aside class="article-layout__sidebar">
<div class="sidebar-section">
<h3 class="sidebar-section__title" data-lang-zh="相关文章" data-lang-en="Related Articles">Related Articles</h3>
{related_html}
</div>
</aside>
</div>
</main>

<footer class="footer">
<div class="container">
<div class="footer__grid">
<div>
<h3 class="footer__title" data-lang-zh="西藏摩旅" data-lang-en="Tibet Moto Travel">西藏摩旅</h3>
<p class="footer__text" data-lang-zh="探索世界屋脊的极致旅程" data-lang-en="Explore the Roof of the World">探索世界屋脊的极致旅程</p>
</div>
<div>
<h4 class="footer__title" data-lang-zh="探索" data-lang-en="Explore">探索</h4>
<ul class="footer__links">
<li><a href="../routes.html" data-lang-zh="经典路线" data-lang-en="Routes">经典路线</a></li>
<li><a href="index.html" data-lang-zh="摩旅文章" data-lang-en="Articles">摩旅文章</a></li>
</ul>
</div>
<div>
<h4 class="footer__title" data-lang-zh="关于" data-lang-en="About">关于</h4>
<ul class="footer__links">
<li><a href="../about.html" data-lang-zh="关于我们" data-lang-en="About Us">关于我们</a></li>
</ul>
</div>
<div>
<h4 class="footer__title" data-lang-zh="联系" data-lang-en="Contact">联系</h4>
<ul class="footer__links">
<li><a href="mailto:info@tibetmotorcycle.com">info@tibetmotorcycle.com</a></li>
</ul>
</div>
</div>
<div class="footer__bottom">
<p>&copy; 2026 Tibet Moto Travel. All rights reserved.</p>
</div>
</div>
</footer>
<script src="../js/lang.js"></script>
</body>
</html>'''

    out_path = os.path.join('articles', f"{meta['slug']}.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"  -> {out_path}  ({len(blocks)} blocks)")
    return True


def main():
    src_dir = 'AddingArticleWorkSpace/1'
    files = [f for f in os.listdir(src_dir) if f.endswith('.html')]

    to_process = []
    for meta in ARTICLES_META:
        matched = None
        for f in files:
            if meta['file_pattern'] in f:
                matched = f
                break
        if matched:
            to_process.append((os.path.join(src_dir, matched), meta))
        else:
            print(f"WARNING: No file found for: {meta['file_pattern']}")

    to_process.sort(key=lambda x: x[1]['date'])

    for i, (filepath, meta) in enumerate(to_process):
        prev_slug = to_process[i-1][1]['slug'] if i > 0 else None
        next_slug = to_process[i+1][1]['slug'] if i < len(to_process)-1 else None
        process_article(filepath, meta, prev_slug, next_slug)

    print(f"\nDone! Processed {len(to_process)} articles.")


if __name__ == '__main__':
    main()
