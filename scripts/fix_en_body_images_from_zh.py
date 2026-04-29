import os
import re

articles_dir = "articles"

def extract_body_block(content, lang):
    """Extract the article-body lang-content block for given language."""
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return None
    
    # Find the lang-content div inside article-body
    search_start = body_start
    pattern = f'<div class="lang-content" data-lang="{lang}">'
    idx = content.find(pattern, search_start)
    if idx < 0:
        return None
    
    start = idx
    content_start = idx + len(pattern)
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
                break
            p = next_close + 6
    else:
        return None
    
    return content[start:end]

def extract_imgs(block):
    """Extract all <img> tags from a block."""
    return re.findall(r'<img[^>]*>', block, re.IGNORECASE)

def split_into_sections(html):
    """Split HTML into sections by h2/h3/h4 tags."""
    # Split on heading tags but keep them
    parts = re.split(r'(<h[234][^>]*>.*?</h[234]>)', html, flags=re.S)
    return parts

def insert_imgs_into_en(en_block, imgs):
    """Insert images into EN block, distributing them across sections."""
    if not imgs:
        return en_block
    
    # Remove the wrapper div tags
    inner = en_block[len('<div class="lang-content" data-lang="en">'):-6]
    
    # Split into sections by headings
    parts = split_into_sections(inner)
    
    # Calculate how many imgs per section (excluding the first part before any heading)
    heading_sections = [i for i, p in enumerate(parts) if re.match(r'<h[234]', p, re.I)]
    num_sections = len(heading_sections)
    
    if num_sections == 0:
        # No headings - put all imgs at start
        new_inner = '\n'.join(imgs) + '\n' + inner
        return f'<div class="lang-content" data-lang="en">{new_inner}</div>'
    
    # Distribute imgs: cover first, then per section
    # First img (usually cover) goes right after opening
    result_parts = []
    img_idx = 0
    
    # Put first image at the very beginning if it looks like a cover
    if imgs:
        result_parts.append(imgs[0])
        img_idx = 1
    
    remaining_imgs = imgs[img_idx:]
    
    # Split remaining images among sections
    if num_sections > 0 and remaining_imgs:
        imgs_per_section = max(1, len(remaining_imgs) // num_sections)
    else:
        imgs_per_section = 0
    
    section_img_idx = 0
    for i, part in enumerate(parts):
        result_parts.append(part)
        if re.match(r'<h[234]', part, re.I) and remaining_imgs:
            # Insert some images after this heading
            to_insert = imgs_per_section
            if section_img_idx == num_sections - 1:
                # Last section gets all remaining
                to_insert = len(remaining_imgs)
            for _ in range(to_insert):
                if remaining_imgs:
                    result_parts.append(remaining_imgs.pop(0))
            section_img_idx += 1
    
    # Any remaining imgs go at the end
    if remaining_imgs:
        result_parts.extend(remaining_imgs)
    
    new_inner = '\n'.join(result_parts)
    return f'<div class="lang-content" data-lang="en">{new_inner}</div>'

log = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith('.html') or fn == 'index.html':
        continue
    
    path = os.path.join(articles_dir, fn)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    zh_block = extract_body_block(content, 'zh')
    en_block = extract_body_block(content, 'en')
    
    if not zh_block or not en_block:
        log.append(f"{fn}: Missing ZH or EN body block")
        continue
    
    zh_imgs = extract_imgs(zh_block)
    en_imgs = extract_imgs(en_block)
    
    if len(en_imgs) >= len(zh_imgs):
        log.append(f"{fn}: EN already has {len(en_imgs)} imgs (ZH has {len(zh_imgs)})")
        continue
    
    # Need to add images to EN body
    new_en_block = insert_imgs_into_en(en_block, zh_imgs)
    
    # Replace in content
    en_start = content.find(en_block)
    if en_start < 0:
        log.append(f"{fn}: Could not find EN block position")
        continue
    
    content = content[:en_start] + new_en_block + content[en_start + len(en_block):]
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log.append(f"{fn}: Added {len(zh_imgs)} imgs to EN body (was {len(en_imgs)})")

with open("scripts/fix_en_images_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
