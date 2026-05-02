"""Unified HTML block extraction using stack-based nested div traversal."""
import re
from typing import Optional


def find_lang_block_positions(
    content: str,
    lang: str,
    after_pos: int = 0,
    within_body: bool = False
) -> tuple[Optional[int], Optional[int]]:
    """
    Find the start and end positions of a <div class="lang-content" data-lang="{lang}"> block.
    Uses stack-based depth tracking to correctly handle nested divs.

    Args:
        content: HTML string to search
        lang: language code ('zh' or 'en')
        after_pos: start searching after this position
        within_body: if True, only search after '<div class="article-body">'

    Returns:
        (start_pos, end_pos) of the entire div tag, or (None, None) if not found
    """
    search = content
    offset = 0

    if within_body:
        body_start = content.find('<div class="article-body">')
        if body_start < 0:
            return (None, None)
        search = content[body_start:]
        offset = body_start

    marker = f'<div class="lang-content" data-lang="{lang}">'
    idx = search.find(marker, max(0, after_pos - offset))
    if idx < 0:
        return (None, None)

    start = offset + idx
    content_start = start + len(marker)
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


def extract_lang_block(
    content: str,
    lang: str,
    after_pos: int = 0,
    within_body: bool = False
) -> Optional[str]:
    """Extract the inner content of a lang-content block (without wrapper div)."""
    start, end = find_lang_block_positions(content, lang, after_pos, within_body)
    if start is None or end is None:
        return None
    marker = f'<div class="lang-content" data-lang="{lang}">'
    inner_start = start + len(marker)
    return content[inner_start:end - 6]  # strip closing </div>


def extract_all_lang_blocks(content: str, lang: str) -> list[str]:
    """Extract all lang-content blocks for a given language."""
    blocks = []
    pos = 0
    while True:
        start, end = find_lang_block_positions(content, lang, pos)
        if start is None or end is None:
            break
        marker = f'<div class="lang-content" data-lang="{lang}">'
        inner = content[start + len(marker):end - 6]
        blocks.append(inner)
        pos = end
    return blocks


def count_imgs(block_html: str) -> int:
    """Count <img> tags in an HTML fragment."""
    return len(re.findall(r'<img\b', block_html, re.IGNORECASE))


def extract_imgs(block_html: str) -> list[str]:
    """Extract all <img ...> tag strings from HTML."""
    return re.findall(r'<img[^>]*>', block_html, re.IGNORECASE)


def strip_tags(html: str) -> str:
    """Remove HTML tags, return plain text."""
    return re.sub(r'<[^>]+>', ' ', html)
