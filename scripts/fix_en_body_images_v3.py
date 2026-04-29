import os, re

articles_dir = "articles"

def find_lang_blocks(content, lang):
    """Find all lang-content blocks with precise positions."""
    blocks = []
    search_start = 0
    prefix = f'<div class="lang-content" data-lang="{lang}">'
    while True:
        idx = content.find(prefix, search_start)
        if idx < 0:
            break
        start = idx + len(prefix)
        depth = 1
        pos = start
        while depth > 0 and pos < len(content):
            next_open = content.find('<div', pos)
            next_close = content.find('</div>', pos)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    end = next_close
                    break
                pos = next_close + 6
        blocks.append({
            'full_start': idx,
            'content_start': start,
            'end': end,
            'content': content[start:end]
        })
        search_start = end + 6
    return blocks

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    zh_blocks = find_lang_blocks(content, "zh")
    en_blocks = find_lang_blocks(content, "en")
    
    if len(zh_blocks) < 2 or len(en_blocks) < 2:
        return 0, f"Need 2+ blocks (ZH={len(zh_blocks)}, EN={len(en_blocks)})"
    
    # Hero = first block, Body = second block (longest remaining)
    zh_hero = zh_blocks[0]
    zh_body = max(zh_blocks[1:], key=lambda b: len(b['content']))
    en_hero = en_blocks[0]
    en_body = max(en_blocks[1:], key=lambda b: len(b['content']))
    
    # Extract images from ZH body
    zh_imgs = re.findall(r'<img[^>]*>', zh_body['content'])
    if not zh_imgs:
        return 0, "No images in ZH body"
    
    # Clean hero EN block: remove all images
    en_hero_clean = re.sub(r'\s*<img[^>]*>\s*', '\n', en_hero['content'])
    en_hero_clean = re.sub(r'\n\n+', '\n', en_hero_clean)
    
    # Check if body EN block already has images
    en_body_imgs = re.findall(r'<img[^>]*>', en_body['content'])
    
    # Build new body EN block with images
    en_body_content = en_body['content']
    
    # Remove any existing images from body EN (they may be misplaced)
    en_body_clean = re.sub(r'\s*<img[^>]*>\s*', '\n', en_body_content)
    en_body_clean = re.sub(r'\n\n+', '\n', en_body_clean)
    
    # Distribute images across h2 sections
    h2_matches = list(re.finditer(r'<h2', en_body_clean))
    
    if len(h2_matches) <= 1:
        new_en_body = '\n'.join(zh_imgs) + '\n' + en_body_clean
    else:
        sections = []
        last_end = 0
        for m in h2_matches:
            pos = m.start()
            if pos > last_end:
                sections.append(('text', en_body_clean[last_end:pos]))
            h2_end = en_body_clean.find('</h2>', pos)
            if h2_end > 0:
                h2_end += 5
                sections.append(('h2', en_body_clean[pos:h2_end]))
                last_end = h2_end
            else:
                sections.append(('h2', en_body_clean[pos:]))
                last_end = len(en_body_clean)
        if last_end < len(en_body_clean):
            sections.append(('text', en_body_clean[last_end:]))
        
        num_h2 = sum(1 for t, _ in sections if t == 'h2')
        total_sections = max(1, num_h2)
        imgs_per = len(zh_imgs) // total_sections
        remainder = len(zh_imgs) % total_sections
        
        new_sections = []
        img_idx = 0
        
        for t, section in sections:
            new_sections.append(section)
            if t == 'h2':
                count = imgs_per + (1 if remainder > 0 else 0)
                remainder = max(0, remainder - 1)
                for _ in range(count):
                    if img_idx < len(zh_imgs):
                        new_sections.append('\n' + zh_imgs[img_idx] + '\n')
                        img_idx += 1
        
        while img_idx < len(zh_imgs):
            new_sections.append('\n' + zh_imgs[img_idx] + '\n')
            img_idx += 1
        
        new_en_body = ''.join(new_sections)
    
    # Apply changes to content
    # Replace hero EN content
    new_content = content[:en_hero['content_start']] + en_hero_clean + content[en_hero['end']:]
    
    # Need to recalculate body EN positions since content changed
    # Find body EN block again in new_content
    en_blocks_2 = find_lang_blocks(new_content, "en")
    if len(en_blocks_2) >= 2:
        en_body_2 = max(en_blocks_2[1:], key=lambda b: len(b['content']))
        new_content = new_content[:en_body_2['content_start']] + new_en_body + new_content[en_body_2['end']:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return len(zh_imgs), f"Hero cleaned, Body +{len(zh_imgs)} imgs (was {len(en_body_imgs)})"

log = []
total_fixed = 0
for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html") or fn == "index.html":
        continue
    path = os.path.join(articles_dir, fn)
    count, msg = fix_file(path)
    if count > 0:
        total_fixed += 1
    log.append(f"{fn}: {msg}")

with open("scripts/fix_en_body_images_log_v3.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print(f"Processed {total_fixed} files")
for line in log:
    print(line)
