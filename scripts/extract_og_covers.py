#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

# Map file patterns to slugs
mapping = [
    ('2026一起去西藏这个人生必去目的地全年出游攻略请查收', '2026-tibet-year-round-travel-guide'),
    ('被问爆的西藏明星同款线小白也能冲', 'tibet-celebrity-route-beginners'),
    ('当我以地球脉动的方式打开阿里', 'planet-earth-ngari'),
    ('第一次去西藏旅行看这篇就够了', 'first-tibet-trip-guide'),
    ('多巴胺爆棚阿里春日限定色号上线', 'ngari-spring-colors'),
    ('高原之巅蓝色梦境在216国道遇见措勤这些地方你可曾到达', 'g216-coqen-blue-dream'),
    ('旅游西藏6条经典路线311天全涵盖', 'tibet-6-classic-routes'),
    ('秘境改则在羌塘腹地聆听红与蓝的交响', 'gerze-changtang-red-blue'),
    ('收藏6条游线更新你的西藏旅行清单', '6-routes-update-tibet-list'),
    ('所有人阿里全年出游攻略请查收', 'ali-year-round-travel-guide'),
    ('西藏旅游超全避雷攻略52条血泪总结进藏前必看', 'tibet-52-tips-avoid-pitfalls'),
    ('在他的镜头里看见人与自然相融之美', 'lens-nature-human-harmony'),
]

src_dir = 'AddingArticleWorkSpace/1'
files = os.listdir(src_dir)

for pattern, slug in mapping:
    matched = None
    for f in files:
        if pattern in f and f.endswith('.html'):
            matched = f
            break
    if not matched:
        print(f"  # missing: {pattern}")
        continue
    
    with open(os.path.join(src_dir, matched), 'r', encoding='utf-8') as f:
        html = f.read()
    
    og = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', html)
    if not og:
        og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
    
    cover = og.group(1) if og else ''
    print(f"  '{slug}': '{cover}'")
