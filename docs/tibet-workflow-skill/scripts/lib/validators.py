"""
Three-layer validation suite:
  1. HTML structure validation
  2. Bilingual consistency audit
  3. Image-text distribution check
"""
import os
import re
import html
from html.parser import HTMLParser
from typing import Optional

from . import html_parser as hp


# ---------------------------------------------------------------------------
# Layer 1: HTML Structure
# ---------------------------------------------------------------------------
class HTMLValidator(HTMLParser):
    SELF_CLOSING = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr',
    }

    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag not in self.SELF_CLOSING:
            self.stack.append(tag)

    def handle_endtag(self, tag: str):
        if tag in self.SELF_CLOSING:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            expected = self.stack[-1] if self.stack else 'none'
            self.errors.append(f"Unexpected closing </{tag}>, expected </{expected}>")


def validate_html_file(path: str) -> list[str]:
    """Validate a single HTML file. Returns list of error messages."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"Read error: {e}"]

    parser = HTMLValidator()
    try:
        parser.feed(content)
    except Exception as e:
        return [f"Parse error: {e}"]

    errors = list(parser.errors)
    if parser.stack:
        errors.append(f"Unclosed tags: {parser.stack}")
    return errors


def validate_all_articles(articles_dir: str = 'articles') -> dict[str, list[str]]:
    """Validate all HTML files in articles_dir. Returns {filename: errors}."""
    results: dict[str, list[str]] = {}
    for fn in sorted(os.listdir(articles_dir)):
        if not fn.endswith('.html'):
            continue
        path = os.path.join(articles_dir, fn)
        errs = validate_html_file(path)
        if errs:
            results[fn] = errs
    return results


# ---------------------------------------------------------------------------
# Layer 2: Bilingual Consistency Audit
# ---------------------------------------------------------------------------
ZH_CHAR = re.compile(r'[\u4e00-\u9fff]')


def _strip_tags(html_frag: str) -> str:
    return re.sub(r'<[^>]+>', ' ', html_frag)


def find_chinese_in_en(block: str) -> list[tuple[int, str]]:
    """Find Chinese character lines in an EN block, excluding parenthetical annotations."""
    text = _strip_tags(block)
    text = html.unescape(text)
    # Remove parenthetical Chinese annotations like "Shannan (山南)"
    text = re.sub(r'\([\u4e00-\u9fff\s·]+\)', '', text)
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and ZH_CHAR.search(stripped):
            found.append((i, stripped[:120]))
    return found


def has_chinese(text: str) -> bool:
    return bool(ZH_CHAR.search(text))


def audit_file(path: str) -> list[str]:
    """Audit a single article for bilingual consistency issues."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues: list[str] = []
    zh_blocks = hp.extract_all_lang_blocks(content, 'zh')
    en_blocks = hp.extract_all_lang_blocks(content, 'en')

    # 1. Hero EN length check
    if en_blocks:
        en_hero = en_blocks[0]
        en_hero_text = _strip_tags(en_hero).strip()
        if len(en_hero_text) > 200:
            issues.append(f"EN hero suspiciously long ({len(en_hero_text)} chars)")

        zh_in_en_hero = find_chinese_in_en(en_hero)
        if zh_in_en_hero:
            issues.append(f"Chinese in EN hero: {len(zh_in_en_hero)} lines")

    # 2. Body block checks
    if len(en_blocks) >= 2 and len(zh_blocks) >= 2:
        en_body = en_blocks[1]
        zh_body = zh_blocks[1]

        en_imgs = hp.count_imgs(en_body)
        zh_imgs = hp.count_imgs(zh_body)
        if en_imgs != zh_imgs:
            issues.append(f"Image count mismatch: ZH={zh_imgs}, EN={en_imgs}")

        zh_in_en_body = find_chinese_in_en(en_body)
        if zh_in_en_body:
            issues.append(f"Chinese in EN body: {len(zh_in_en_body)} lines")
            for line_no, line_text in zh_in_en_body[:3]:
                issues.append(f"  L{line_no}: {line_text[:80]}")
    elif len(en_blocks) != len(zh_blocks):
        issues.append(f"Block count mismatch: ZH={len(zh_blocks)}, EN={len(en_blocks)}")

    # 3. Chinese in any EN block
    for i, en_block in enumerate(en_blocks):
        zh_found = find_chinese_in_en(en_block)
        if zh_found:
            # Skip if already reported for hero/body
            if i < 2:
                continue
            issues.append(f"EN block {i}: {len(zh_found)} Chinese lines")

    # 4. EN title check (safe regex using stack extraction)
    title_en_match = hp.extract_lang_block(content, 'en', within_body=False)
    if title_en_match:
        title_text = _strip_tags(title_en_match).strip()
        if has_chinese(title_text):
            issues.append(f"EN title contains Chinese: {title_text[:60]}")

    return issues


def audit_all_articles(articles_dir: str = 'articles') -> dict[str, list[str]]:
    """Audit all articles. Returns {filename: issues}."""
    results: dict[str, list[str]] = {}
    for fn in sorted(os.listdir(articles_dir)):
        if not fn.endswith('.html') or fn == 'index.html':
            continue
        path = os.path.join(articles_dir, fn)
        issues = audit_file(path)
        if issues:
            results[fn] = issues
    return results


# ---------------------------------------------------------------------------
# Layer 3: Image-Text Distribution
# ---------------------------------------------------------------------------
def analyze_distribution(block: str) -> Optional[str]:
    """
    Check if images are clustered at start or end of block.
    Returns issue description or None if distribution is OK.
    """
    block = block.strip()
    if not block:
        return None

    img_positions = [m.start() for m in re.finditer(r'<img', block)]
    text_positions = [m.start() for m in re.finditer(r'<(?:p|h[2-6])', block)]

    if not img_positions or not text_positions:
        return None

    last_img = max(img_positions)
    first_text = min(text_positions)
    if last_img < first_text:
        return f"images_at_start: {len(img_positions)} imgs before {len(text_positions)} text blocks"

    first_img = min(img_positions)
    last_text = max(text_positions)
    if first_img > last_text:
        return f"images_at_end: {len(img_positions)} imgs after {len(text_positions)} text blocks"

    imgs_before_first = sum(1 for p in img_positions if p < first_text)
    if imgs_before_first >= len(img_positions) * 0.8 and imgs_before_first >= 3:
        return f"mostly_images_first: {imgs_before_first}/{len(img_positions)} imgs before text"

    imgs_after_last = sum(1 for p in img_positions if p > last_text)
    if imgs_after_last >= len(img_positions) * 0.8 and imgs_after_last >= 3:
        return f"mostly_images_last: {imgs_after_last}/{len(img_positions)} imgs after text"

    return None


def check_distribution(path: str) -> Optional[str]:
    """Check image distribution for a single article's EN body."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    en_body = hp.extract_lang_block(content, 'en', within_body=True)
    if not en_body:
        return None
    return analyze_distribution(en_body)


def check_all_distributions(articles_dir: str = 'articles') -> dict[str, str]:
    """Check all articles. Returns {filename: issue}."""
    results: dict[str, str] = {}
    for fn in sorted(os.listdir(articles_dir)):
        if not fn.endswith('.html') or fn == 'index.html':
            continue
        path = os.path.join(articles_dir, fn)
        issue = check_distribution(path)
        if issue:
            results[fn] = issue
    return results


# ---------------------------------------------------------------------------
# Unified runner
# ---------------------------------------------------------------------------
from typing import Any

def run_full_validation(articles_dir: str = 'articles') -> dict[str, Any]:
    """Run all three validation layers and return structured results."""
    return {
        'html': validate_all_articles(articles_dir),
        'audit': audit_all_articles(articles_dir),
        'distribution': check_all_distributions(articles_dir),
    }
