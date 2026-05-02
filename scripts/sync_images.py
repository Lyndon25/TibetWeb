"""
Synchronize images between ZH and EN body blocks with proportional distribution.
Consolidates: fix_en_body_images_from_zh.py + fix_en_image_distribution.py + fix_image_counts.py

Usage:
    python scripts/sync_images.py [--fix-distribution]
"""
import os
import sys
import re
import argparse

from lib import atomic_io, html_parser as hp

ARTICLES_DIR = 'articles'


def _analyze_zh_distribution(zh_block: str) -> tuple[list[tuple[str, int]], int]:
    """Split ZH block by imgs, return list of (img_tag, text_tokens_before) and total text tokens."""
    parts = re.split(r'(<img[^>]*>)', zh_block)
    result = []
    text_count = 0
    for part in parts:
        if part.startswith('<img'):
            result.append((part, text_count))
        else:
            text_count += len(re.findall(r'<(?:p|h[2-6])[^>]*>', part))
    return result, text_count


def _has_separation_issue(en_block: str) -> bool:
    """Check if all images are clustered before all text."""
    en_imgs = [(m.start(), m.group(0)) for m in re.finditer(r'<img[^>]*>', en_block)]
    en_text_pos = [m.start() for m in re.finditer(r'<(?:p|h[2-6])', en_block)]
    if not en_imgs or not en_text_pos:
        return False
    return max(pos for pos, _ in en_imgs) < min(en_text_pos)


def _redistribute_imgs(en_block: str, zh_block: str) -> str:
    """Redistribute EN images proportionally based on ZH text token distribution."""
    zh_img_dist, zh_total_text = _analyze_zh_distribution(zh_block)
    en_imgs = [(m.start(), m.group(0)) for m in re.finditer(r'<img[^>]*>', en_block)]
    en_img_tags = [tag for _, tag in en_imgs]

    # Remove all images from EN block
    en_text_only = re.sub(r'<img[^>]*>\s*', '', en_block).strip()
    en_tokens = [(m.start(), m.group(0)) for m in re.finditer(r'<(?:p|h[2-6])[^>]*>', en_text_only)]

    if not en_tokens:
        return en_block

    result = en_text_only
    offset = 0

    for i, (_, zh_text_before) in enumerate(zh_img_dist):
        if i >= len(en_img_tags):
            break
        ratio = zh_text_before / zh_total_text if zh_total_text > 0 else (i + 1) / (len(zh_img_dist) + 1)
        en_idx = min(int(ratio * len(en_tokens)), len(en_tokens) - 1)
        if en_idx < 0:
            en_idx = 0

        insert_pos = en_tokens[en_idx][0] + offset
        img_html = en_img_tags[i] + '\n'
        result = result[:insert_pos] + img_html + result[insert_pos:]
        offset += len(img_html)

    return result


def sync_file(path: str, fix_distribution: bool = True) -> tuple[bool, str]:
    """Synchronize images for a single article."""
    content = atomic_io.read_file(path)

    zh_block_full = hp.extract_lang_block(content, 'zh', within_body=True)
    en_block_full = hp.extract_lang_block(content, 'en', within_body=True)

    if not zh_block_full or not en_block_full:
        return False, 'missing ZH or EN body block'

    zh_imgs = hp.extract_imgs(zh_block_full)
    en_imgs = hp.extract_imgs(en_block_full)

    # Count mismatch fix
    changed = False
    en_block_new = en_block_full

    if len(en_imgs) > len(zh_imgs):
        # Remove excess images from EN
        excess = len(en_imgs) - len(zh_imgs)
        for _ in range(excess):
            last = en_block_new.rfind(en_imgs[-1])
            if last >= 0:
                en_block_new = en_block_new[:last] + en_block_new[last + len(en_imgs[-1]):]
                en_imgs.pop()
        changed = True

    elif len(en_imgs) < len(zh_imgs):
        # Add missing images from ZH to EN
        missing = zh_imgs[len(en_imgs):]
        en_block_new = '\n'.join(missing) + '\n' + en_block_new
        changed = True

    # Distribution fix
    if fix_distribution and _has_separation_issue(en_block_new):
        en_block_new = _redistribute_imgs(en_block_new, zh_block_full)
        changed = True

    if not changed:
        return True, 'no changes needed'

    # Replace EN block in original content
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return False, 'no article-body found'

    s, e = hp.find_lang_block_positions(content, 'en', body_start)
    if s is None or e is None:
        return False, 'cannot locate EN body block for replacement'

    new_en = f'<div class="lang-content" data-lang="en">\n{en_block_new}\n</div>'
    content = content[:s] + new_en + content[e:]
    atomic_io.atomic_write(path, content)

    return True, f'synced (ZH={len(zh_imgs)} imgs, final distribution OK)'


def main():
    parser = argparse.ArgumentParser(description='Synchronize ZH/EN body images')
    parser.add_argument('--no-fix-distribution', action='store_true',
                        help='Skip proportional redistribution (only sync counts)')
    parser.add_argument('--slug', type=str, help='Process only this slug')
    args = parser.parse_args()

    fix_dist = not args.no_fix_distribution
    log = []
    failed = False

    for fn in sorted(os.listdir(ARTICLES_DIR)):
        if not fn.endswith('.html') or fn == 'index.html':
            continue
        if args.slug and fn != f'{args.slug}.html':
            continue

        path = os.path.join(ARTICLES_DIR, fn)
        ok, msg = sync_file(path, fix_distribution=fix_dist)
        line = f'{fn}: {msg}'
        log.append(line)
        print(line)
        if not ok:
            failed = True

    log_path = os.path.join('scripts', 'sync_images_log.txt')
    atomic_io.atomic_write(log_path, '\n'.join(log))

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
