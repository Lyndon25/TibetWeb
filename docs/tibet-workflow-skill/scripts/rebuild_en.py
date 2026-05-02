"""
Rebuild English content in articles from WeChat source files.
Consolidates: rebuild_en_from_source.py + fix_en_content.py + fix_mixed_lang.py

Usage:
    python scripts/rebuild_en.py [--strict] [--slug <slug>]
"""
import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

from lib import atomic_io, html_parser as hp, article_config, en_extractor

SRC_DIR = os.path.join(_SKILL_DIR, 'AddingArticleWorkSpace', '1')
ARTICLES_DIR = os.path.join(_SKILL_DIR, 'articles')


def rebuild_article(slug: str, file_pattern: str, strict: bool = False) -> tuple[bool, str]:
    """Rebuild EN content for a single article."""
    article_path = os.path.join(ARTICLES_DIR, f'{slug}.html')
    if not os.path.exists(article_path):
        return False, 'article not found'

    en_html, source_type = en_extractor.extract_en(SRC_DIR, file_pattern, strict=strict)
    if not en_html:
        return False, 'no EN translation found in source'

    content = atomic_io.read_file(article_path)

    # Extract title
    title = en_extractor.get_title_from_en_html(en_html)

    # Find hero and body EN blocks
    body_start = content.find('<div class="article-body">')

    hero_en = None
    body_en = None
    pos = 0
    while True:
        s, e = hp.find_lang_block_positions(content, 'en', pos)
        if s is None or e is None:
            break
        if body_start > 0 and s < body_start:
            hero_en = (s, e)
        elif body_start > 0 and s > body_start:
            body_en = (s, e)
            break
        pos = e

    # Replace hero EN (only h1)
    if hero_en:
        s, e = hero_en
        new_hero = f'<div class="lang-content" data-lang="en"><h1 class="article-hero__title">{title}</h1></div>'
        content = content[:s] + new_hero + content[e:]

    # Replace body EN
    if body_en:
        new_body_start = content.find('<div class="article-body">')
        if new_body_start >= 0:
            s, e = hp.find_lang_block_positions(content, 'en', new_body_start)
            if s is not None and e is not None:
                new_body = f'<div class="lang-content" data-lang="en">\n{en_html}\n</div>'
                content = content[:s] + new_body + content[e:]

    atomic_io.atomic_write(article_path, content)
    return True, f'rebuilt from {source_type} ({len(en_html)} chars)'


def main():
    parser = argparse.ArgumentParser(description='Rebuild English article content from source files')
    parser.add_argument('--strict', action='store_true', help='Apply strict Chinese filter')
    parser.add_argument('--slug', type=str, help='Rebuild only this slug')
    args = parser.parse_args()

    articles = article_config.load_articles()
    file_map = article_config.build_file_map(articles)

    log = []
    failed = False

    for slug, pattern in file_map.items():
        if args.slug and slug != args.slug:
            continue
        ok, msg = rebuild_article(slug, pattern, strict=args.strict)
        line = f'{slug}.html: {msg}'
        log.append(line)
        print(line)
        if not ok:
            failed = True

    log_path = os.path.join(_SKILL_DIR, 'scripts', 'rebuild_en_log.txt')
    atomic_io.atomic_write(log_path, '\n'.join(log))

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
