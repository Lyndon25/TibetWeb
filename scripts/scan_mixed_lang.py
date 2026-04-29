#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan articles for mixed-language contamination within lang-content blocks.
"""
import os
import re
from bs4 import BeautifulSoup

ARTICLES_DIR = 'articles'

def extract_text_content(html_fragment):
    """Extract plain text from HTML, excluding tags."""
    soup = BeautifulSoup(html_fragment, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def find_mixed_lang():
    issues = []
    
    for fname in sorted(os.listdir(ARTICLES_DIR)):
        if not fname.endswith('.html') or fname == 'index.html':
            continue
        
        fpath = os.path.join(ARTICLES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all lang-content blocks
        for lang in ['zh', 'en']:
            pattern = rf'<div class="lang-content" data-lang="{lang}">(.*?)</div>'
            matches = list(re.finditer(pattern, content, re.DOTALL))
            
            for i, m in enumerate(matches):
                block_html = m.group(1)
                text = extract_text_content(block_html)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                for line in lines:
                    if lang == 'zh':
                        # In Chinese block: look for English words/phrases
                        # Exclude: URLs, image alt text patterns, numbers with units, common abbreviations
                        # Look for sequences of 2+ Latin letters
                        en_words = re.findall(r'[a-zA-Z]{2,}', line)
                        # Filter out common non-translatable terms
                        skip_words = {'png', 'jpg', 'jpeg', 'svg', 'gif', 'webp', 'src', 'alt', 'href', 'html', 'css', 'js', 'http', 'https', 'www', 'com', 'cn', 'org', 'net', 'mp', 'mmbiz', 'wx_fmt', 'appmsg', 'wxw', 'wx', 'qqpic', 'qpic', 'mmbiz', 'data', 'type', 'ratio', 'lazy', 'loading', 'width', 'height', 'style', 'class', 'id', 'span', 'div', 'p', 'img', 'section', 'strong', 'em', 'br', 'hr', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'caption', 'leaf', 'nodeleaf', 'center', 'box', 'sizing', 'border', 'color', 'rgb', 'font', 'size', 'background', 'margin', 'padding', 'display', 'inline', 'block', 'vertical', 'align', 'max', 'auto', 'important', 'overflow', 'hidden', 'position', 'relative', 'absolute', 'fixed', 'top', 'bottom', 'left', 'right', 'inset', 'none', 'solid', 'transparent', 'white', 'black', 'red', 'blue', 'green', 'yellow', 'px', 'rem', 'em', 'vh', 'vw', 'pct', 'px', 'svg', 'amp', 'from', 'wx', 'fmt', 'jpeg', 'url', 'min', 'text', 'align', 'justify', 'normal', 'space', 'letter', 'spacing', 'line', 'family', 'serif', 'sans', 'weight', 'bold', 'italic', 'underline', 'decoration', 'shadow', 'radius', 'cursor', 'pointer', 'default', 'hover', 'active', 'focus', 'visited', 'disabled', 'readonly', 'required', 'checked', 'selected', 'hidden', 'visible', 'collapse', 'separate', 'collapse', 'clip', 'origin', 'transform', 'transition', 'animation', 'keyframes', 'media', 'screen', 'print', 'speech', 'all', 'not', 'only', 'and', 'or', 'min', 'max', 'device', 'aspect', 'ratio', 'orientation', 'portrait', 'landscape', 'resolution', 'dpi', 'dpcm', 'color', 'index', 'monochrome', 'grid', 'scan', 'interlace', 'progressive', 'prefers', 'reduced', 'motion', 'contrast', 'scheme', 'dark', 'light', 'lang', 'dir', 'ltr', 'rtl', 'role', 'aria', 'label', 'labelledby', 'describedby', 'controls', 'live', 'atomic', 'relevant', 'busy', 'disabled', 'hidden', 'expanded', 'pressed', 'checked', 'selected', 'valuenow', 'valuemin', 'valuemax', 'multiline', 'multiselectable', 'readonly', 'required', 'invalid', 'modal', 'haspopup', 'level', 'setsize', 'posinset', 'colspan', 'rowspan', 'headers', 'scope', 'abbr', 'sort', 'draggable', 'dropzone', 'spellcheck', 'translate', 'contenteditable', 'contextmenu', 'tabindex', 'accesskey', 'title', 'target', 'rel', 'download', 'ping', 'media', 'type', 'coords', 'shape', 'usemap', 'ismap', 'srcset', 'sizes', 'crossorigin', 'integrity', 'referrerpolicy', 'autoplay', 'controls', 'loop', 'muted', 'preload', 'poster', 'playsinline', 'object', 'param', 'embed', 'iframe', 'sandbox', 'seamless', 'allow', 'form', 'action', 'method', 'enctype', 'novalidate', 'autocomplete', 'autofocus', 'disabled', 'formaction', 'formenctype', 'formmethod', 'formnovalidate', 'formtarget', 'name', 'value', 'placeholder', 'readonly', 'required', 'size', 'maxlength', 'minlength', 'multiple', 'pattern', 'step', 'cols', 'rows', 'wrap', 'accept', 'capture', 'checked', 'dirname', 'list', 'max', 'min', 'optimum', 'low', 'high', 'challenge', 'keytype', 'charset', 'http', 'equiv', 'content', 'scheme', 'name', 'property', 'itemprop', 'itemscope', 'itemtype', 'itemid', 'itemref'}
                        
                        real_en = [w for w in en_words if w.lower() not in skip_words]
                        if real_en:
                            issues.append({
                                'file': fname,
                                'lang': lang,
                                'block_idx': i,
                                'line': line[:120],
                                'en_words': real_en,
                                'full_text': text[:300]
                            })
                    else:
                        # In English block: look for Chinese characters
                        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', line)
                        if chinese_chars:
                            issues.append({
                                'file': fname,
                                'lang': lang,
                                'block_idx': i,
                                'line': line[:120],
                                'chinese': chinese_chars,
                                'full_text': text[:300]
                            })
    
    return issues

if __name__ == '__main__':
    issues = find_mixed_lang()
    print(f"Found {len(issues)} potential mixed-language issues:\n")
    
    current_file = None
    for issue in issues:
        if issue['file'] != current_file:
            current_file = issue['file']
            print(f"\n=== {current_file} ===")
        
        lang_label = "ZH block" if issue['lang'] == 'zh' else "EN block"
        if issue['lang'] == 'zh':
            print(f"  [{lang_label}] EN words: {issue['en_words']}")
        else:
            print(f"  [{lang_label}] Chinese: {issue['chinese']}")
        print(f"    Line: {issue['line']}")
