#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

slugs = [
    '2026-tibet-year-round-travel-guide',
    'tibet-celebrity-route-beginners',
    'planet-earth-ngari',
    'first-tibet-trip-guide',
    'ngari-spring-colors',
    'g216-coqen-blue-dream',
    'tibet-6-classic-routes',
    'gerze-changtang-red-blue',
    '6-routes-update-tibet-list',
    'ali-year-round-travel-guide',
    'tibet-52-tips-avoid-pitfalls',
    'lens-nature-human-harmony',
]

for slug in slugs:
    filepath = os.path.join('articles', f'{slug}.html')
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # First img in lang-content zh
    m = re.search(r'<div class="lang-content" data-lang="zh">.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)
    cover = m.group(1) if m else ''
    
    print(f"  '{slug}': '{cover}'")
