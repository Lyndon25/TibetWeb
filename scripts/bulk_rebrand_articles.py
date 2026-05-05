#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk rebrand all articles from 'Tibet Moto Travel' / '西藏摩旅' to 'TibetRide'.
Updates navigation, logo, footer, and copyright in all articles/*.html files.
"""
import os
import re
import glob

ARTICLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'articles')

# Replacement rules: (pattern, replacement)
# Order matters: more specific patterns first
RULES = [
    # Logo text
    (
        '<span class="nav__logo-text">西藏摩旅</span>',
        '<span class="nav__logo-text">TibetRide</span>'
    ),
    # Footer title ( bilingual )
    (
        '<h3 class="footer__title" data-lang-zh="西藏摩旅" data-lang-en="Tibet Moto Travel">西藏摩旅</h3>',
        '<h3 class="footer__title" data-lang-zh="TibetRide" data-lang-en="TibetRide">TibetRide</h3>'
    ),
    # Footer text ( bilingual )
    (
        '<p class="footer__text" data-lang-zh="探索世界屋脊的极致旅程" data-lang-en="Explore the Roof of the World">探索世界屋脊的极致旅程</p>',
        '<p class="footer__text" data-lang-zh="探索西藏，与本地专家同行。" data-lang-en="Explore Tibet with local experts.">探索西藏，与本地专家同行。</p>'
    ),
    # Copyright
    (
        '<p>&copy; 2026 Tibet Moto Travel. All rights reserved.</p>',
        '<p>&copy; 2026 TibetRide.com. All rights reserved.</p>'
    ),
]

# Navigation link replacements (old URLs -> new URLs)
# We need to be careful not to break article internal links
NAV_REPLACEMENTS = [
    # Replace the old nav link list with new ones
    # Old pattern: Home / Articles / Routes / About
    # New pattern: Home / Tours / Guide / About / Contact
]


def replace_in_file(path: str) -> bool:
    """Apply replacements to a single file. Return True if modified."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    for pattern, replacement in RULES:
        content = content.replace(pattern, replacement)

    # Handle navigation links in articles
    # These are tricky because they're in a specific block
    # Let's do targeted regex replacements for the nav block

    # Replace nav links: add Tours, change Articles->Guide, add Contact
    # Old:
    #   <li><a href="../index.html" data-lang-zh="首页" data-lang-en="Home">首页</a></li>
    #   <li><a href="../articles/index.html" ...>文章</a></li>
    #   <li><a href="../routes.html" ...>路线</a></li>
    #   <li><a href="../about.html" ...>关于</a></li>
    # New:
    #   <li><a href="../index.html" data-lang-zh="首页" data-lang-en="Home">Home</a></li>
    #   <li><a href="../tours/index.html" data-lang-zh="线路" data-lang-en="Tours">Tours</a></li>
    #   <li><a href="../articles/index.html" data-lang-zh="攻略" data-lang-en="Guide">Guide</a></li>
    #   <li><a href="../about.html" data-lang-zh="关于" data-lang-en="About">About</a></li>
    #   <li><a href="../contact.html" data-lang-zh="联系" data-lang-en="Contact">Contact</a></li>

    # Replace "文章" link text -> "Guide" and add data-lang attributes
    content = re.sub(
        r'<li><a href="\.\./articles/index\.html"[^>]*>文章</a></li>',
        '<li><a href="../articles/index.html" data-lang-zh="攻略" data-lang-en="Guide">Guide</a></li>',
        content
    )

    # Replace "路线" link -> "Tours" link
    content = re.sub(
        r'<li><a href="\.\./routes\.html"[^>]*>路线</a></li>',
        '<li><a href="../tours/index.html" data-lang-zh="线路" data-lang-en="Tours">Tours</a></li>',
        content
    )

    # Replace "关于" link, ensure it has data-lang
    content = re.sub(
        r'<li><a href="\.\./about\.html"[^>]*>关于</a></li>',
        '<li><a href="../about.html" data-lang-zh="关于" data-lang-en="About">About</a></li>',
        content
    )

    # Replace "首页" link, ensure it has data-lang and text is "Home"
    content = re.sub(
        r'<li><a href="\.\./index\.html"[^>]*>首页</a></li>',
        '<li><a href="../index.html" data-lang-zh="首页" data-lang-en="Home">Home</a></li>',
        content
    )

    # Add Contact link after About link if not present
    if '<li><a href="../contact.html"' not in content:
        content = content.replace(
            '<li><a href="../about.html" data-lang-zh="关于" data-lang-en="About">About</a></li>',
            '<li><a href="../about.html" data-lang-zh="关于" data-lang-en="About">About</a></li>\n<li><a href="../contact.html" data-lang-zh="联系" data-lang-en="Contact">Contact</a></li>'
        )

    if content == original:
        return False

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def main():
    pattern = os.path.join(ARTICLES_DIR, '*.html')
    files = glob.glob(pattern)
    modified = 0

    for path in sorted(files):
        # Skip index.html (handled separately)
        if os.path.basename(path) == 'index.html':
            continue
        if replace_in_file(path):
            print(f"[OK] Rebranded {os.path.basename(path)}")
            modified += 1
        else:
            print(f"[SKIP] No changes in {os.path.basename(path)}")

    print(f"\n[DONE] {modified} article(s) rebranded.")


if __name__ == '__main__':
    main()
