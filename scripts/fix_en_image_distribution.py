import os, re

TARGET_FILES = [
    'articles/altitude-sickness-tips.html',
    'articles/bianba-motorcycle-diary.html',
    'articles/may-day-tibet-lazy-guide.html',
    'articles/motorcycle-healing-journey.html',
    'articles/motorcycle-tibet-gear-guide.html',
    'articles/motorcycle-tibet-shannan.html',
    'articles/sichuan-tibet-central-route.html',
    'articles/spring-snow-peach-blossoms.html',
    'articles/wheels-shackles-tibet.html',
]


def extract_en_div(content):
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return None, 0, 0
    marker = '<div class="lang-content" data-lang="en">'
    after_body = content[body_start:]
    idx = after_body.find(marker)
    if idx < 0:
        return None, 0, 0
    start = body_start + idx + len(marker)
    depth = 1
    p = start
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
                return content[start:next_close], start, next_close
            p = next_close + 6
    return None, 0, 0


def extract_zh_div(content):
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return None
    marker = '<div class="lang-content" data-lang="zh">'
    after_body = content[body_start:]
    idx = after_body.find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    depth = 1
    p = start
    while depth > 0 and p < len(after_body):
        next_open = after_body.find('<div', p)
        next_close = after_body.find('</div>', p)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            p = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return after_body[start:next_close]
            p = next_close + 6
    return None


def analyze_zh_distribution(zh_block):
    """Split ZH block by imgs, return list of (img_tag, text_tokens_before)."""
    parts = re.split(r'(<img[^>]*>)', zh_block)
    result = []
    text_count = 0
    for part in parts:
        if part.startswith('<img'):
            result.append((part, text_count))
        else:
            text_count += len(re.findall(r'<(?:p|h[2-6])[^>]*>', part))
    return result, text_count


def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    zh_block = extract_zh_div(content)
    en_block, en_start, en_end = extract_en_div(content)

    if not zh_block or not en_block:
        return False, 'missing blocks'

    # Check if EN has images-before-text separation
    en_imgs = [(m.start(), m.group(0)) for m in re.finditer(r'<img[^>]*>', en_block)]
    en_text_pos = [m.start() for m in re.finditer(r'<(?:p|h[2-6])', en_block)]

    if not en_imgs or not en_text_pos:
        return False, 'no imgs or no text'

    last_img = max(pos for pos, _ in en_imgs)
    first_text = min(en_text_pos)
    if last_img >= first_text:
        return False, 'no separation issue'

    # Analyze ZH distribution
    zh_img_dist, zh_total_text = analyze_zh_distribution(zh_block)
    en_img_tags = [tag for _, tag in en_imgs]

    # EN text-only (remove imgs)
    en_text_only = re.sub(r'<img[^>]*>\s*', '', en_block).strip()
    en_tokens = [(m.start(), m.group(0)) for m in re.finditer(r'<(?:p|h[2-6])[^>]*>', en_text_only)]

    if not en_tokens:
        return False, 'no text tokens in EN'

    # Build new EN block: insert imgs proportionally based on ZH distribution
    result = en_text_only
    offset = 0

    for i, (_, zh_text_before) in enumerate(zh_img_dist):
        if i >= len(en_img_tags):
            break

        if zh_total_text > 0:
            ratio = zh_text_before / zh_total_text
        else:
            ratio = (i + 1) / (len(zh_img_dist) + 1)

        en_idx = min(int(ratio * len(en_tokens)), len(en_tokens) - 1)
        if en_idx < 0:
            en_idx = 0

        insert_pos = en_tokens[en_idx][0] + offset
        img_html = en_img_tags[i] + '\n'
        result = result[:insert_pos] + img_html + result[insert_pos:]
        offset += len(img_html)

    # Replace EN block in original content
    new_content = content[:en_start] + result + content[en_end:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True, f'redistributed {len(en_img_tags)} imgs (ZH ref: {len(zh_img_dist)} imgs, {zh_total_text} text tokens)'


def main():
    fixed = []
    skipped = []
    for path in TARGET_FILES:
        ok, reason = fix_file(path)
        if ok:
            fixed.append((path, reason))
        else:
            skipped.append((path, reason))

    print(f"Fixed: {len(fixed)}")
    for p, r in fixed:
        print(f"  + {p}: {r}")
    print(f"Skipped: {len(skipped)}")
    for p, r in skipped:
        print(f"  - {p}: {r}")


if __name__ == '__main__':
    main()
