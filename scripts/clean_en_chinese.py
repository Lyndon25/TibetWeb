#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean remaining Chinese annotations from EN blocks.
These are patterns like: 英文 (中文) or 中文/English
"""
import os
import re

ARTICLES_DIR = 'articles'

# File-specific replacements
REPLACEMENTS = {
    'ali-year-round-travel-guide.html': [
        (r'its snow peak轮廓 \(silhouette\)清晰 \(crystal clear\)', 'its snow peak silhouette crystal clear'),
        (r'呈现 \(presenting\) pure blue', 'presenting pure blue'),
        (r'enters its最佳 \(best\) viewing season', 'enters its best viewing season'),
        (r'After千万年 \(millions of years\) of wind and rain erosion', 'After millions of years of wind and rain erosion'),
        (r'the奇特 \(unique\) landform presents', 'the unique landform presents'),
        (r'Huge day-night温差 \(difference\)', 'Huge day-night temperature difference'),
        (r'April gradually摆脱 \(shakes off\) the cold', 'April gradually shakes off the cold'),
        (r'but the草原 \(grassland\) is greener after rain', 'but the grassland is greener after rain'),
        (r'offers原始 \(pristine\) and magnificent scenery', 'offers pristine and magnificent scenery'),
        (r'lake water presents a deep blue,澄澈 \(crystal clear\)', 'lake water presents a deep blue, crystal clear'),
        (r'Large day-night温差 \(difference\)', 'Large day-night temperature difference'),
        (r'Distant snow mountains stand巍峨 \(towering\)', 'Distant snow mountains stand towering'),
        (r'Respect local礼仪 \(etiquette\)', 'Respect local etiquette'),
        (r'every month in Ngari hides极致 \(ultimate\) surprises and震撼 \(awe\)', 'every month in Ngari hides ultimate surprises and awe'),
    ],
    'g216-coqen-blue-dream.html': [
        (r'<strong>Coqen \(措勤\)</strong>', '<strong>Coqen</strong>'),
        (r'nature is放大 \(magnified\) to the extreme', 'nature is magnified to the extreme'),
        (r'also a必经 \(must-pass\) station', 'also a must-pass station'),
        (r'Azure彼岸 \(Other Shore\)', 'Azure Other Shore'),
        (r'Like a sapphire镶嵌 \(inlaid\) in the Changtang earth', 'Like a sapphire inlaid in the Changtang earth'),
        (r'the more you越野 \(off-road\), the more Ngari you see', 'the more you off-road, the more Ngari you see'),
        (r'await a高原 \(plateau\) sunset', 'await a plateau sunset'),
        (r'highest民用 \(civilian\) highway pass', 'highest civilian highway pass'),
        (r'the深浅 \(varying\) red stripes', 'the varying red stripes'),
        (r'occasionally镶嵌 \(inlaid\)', 'occasionally inlaid'),
        (r'composing a高原 \(plateau\) "Song of Ice and Fire"', 'composing a plateau "Song of Ice and Fire"'),
        (r'warm and包容 \(embracing\)', 'warm and embracing'),
        (r'all登山 \(mountaineering\) activities prohibited', 'all mountaineering activities prohibited'),
        (r'world\'s highest民用 \(civilian\) highway pass', 'world\'s highest civilian highway pass'),
    ],
}

def main():
    for fname, reps in REPLACEMENTS.items():
        fpath = os.path.join(ARTICLES_DIR, fname)
        if not os.path.exists(fpath):
            print(f"SKIP: {fname} not found")
            continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        for pattern, replacement in reps:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                print(f"  {fname}: '{pattern[:50]}...' -> '{replacement[:50]}...'")
        
        if modified:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SAVED: {fname}")
        else:
            print(f"NO CHANGES: {fname}")

if __name__ == '__main__':
    main()
