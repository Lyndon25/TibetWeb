import os, re

articles_dir = "articles"

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract ZH body
    zh_match = re.search(r'<div class="lang-content" data-lang="zh">(.*?)</div>\s*<div class="lang-content" data-lang="en">', content, re.S)
    if not zh_match:
        return 0, "No ZH body found"
    zh_body = zh_match.group(1)
    
    # Extract EN body - find content between data-lang="en"> and the closing </div></div><nav
    en_match = re.search(r'<div class="lang-content" data-lang="en">(.*?)</div>\s*</div>\s*<nav', content, re.S)
    if not en_match:
        # Try alternate pattern
        en_match = re.search(r'<div class="lang-content" data-lang="en">(.*?)</div>\s*</div>\s*</div>\s*<nav', content, re.S)
    if not en_match:
        return 0, "No EN body found"
    en_body = en_match.group(1)
    
    # Extract <img> tags from ZH body
    zh_imgs = re.findall(r'<img[^>]*>', zh_body)
    if not zh_imgs:
        return 0, "No images in ZH body"
    
    # Check if EN body already has images
    en_imgs = re.findall(r'<img[^>]*>', en_body)
    if len(en_imgs) >= len(zh_imgs):
        return 0, f"EN already has {len(en_imgs)} images (ZH has {len(zh_imgs)})"
    
    # Strategy: Split EN body by <h2> or major sections, distribute images
    # Find <h2> tags to determine sections
    h2_positions = [m.start() for m in re.finditer(r'<h2', en_body)]
    
    if len(h2_positions) <= 1:
        # Few or no sections: put all images at the beginning
        new_en_body = '\n'.join(zh_imgs) + '\n' + en_body
    else:
        # Distribute images across sections
        # Split EN body at <h2> positions
        sections = []
        last_pos = 0
        for pos in h2_positions:
            if pos > last_pos:
                sections.append(en_body[last_pos:pos])
            last_pos = pos
        # Find end of last h2 tag
        last_h2_end = en_body.find('</h2>', last_pos)
        if last_h2_end > 0:
            last_h2_end += 5
            sections.append(en_body[last_pos:last_h2_end])
            sections.append(en_body[last_h2_end:])
        else:
            sections.append(en_body[last_pos:])
        
        # Distribute images: some before first section, rest after each h2
        num_sections = len([s for s in sections if s.strip().startswith('<h2')])
        total_sections = max(1, num_sections)
        imgs_per_section = len(zh_imgs) // total_sections
        remainder = len(zh_imgs) % total_sections
        
        new_sections = []
        img_idx = 0
        h2_seen = 0
        
        for section in sections:
            new_sections.append(section)
            if section.strip().startswith('<h2'):
                h2_seen += 1
                count = imgs_per_section + (1 if remainder > 0 else 0)
                remainder = max(0, remainder - 1)
                for _ in range(count):
                    if img_idx < len(zh_imgs):
                        new_sections.append('\n' + zh_imgs[img_idx] + '\n')
                        img_idx += 1
        
        # Add remaining images at the end
        while img_idx < len(zh_imgs):
            new_sections.append('\n' + zh_imgs[img_idx] + '\n')
            img_idx += 1
        
        new_en_body = ''.join(new_sections)
    
    new_content = content.replace(en_body, new_en_body)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return len(zh_imgs), "OK"

log = []
total_fixed = 0
for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html") or fn == "index.html":
        continue
    path = os.path.join(articles_dir, fn)
    count, msg = fix_file(path)
    if count > 0:
        log.append(f"{fn}: +{count} images ({msg})")
        total_fixed += 1
    else:
        log.append(f"{fn}: {msg}")

with open("scripts/fix_en_body_images_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print(f"Fixed {total_fixed} files")
for line in log:
    print(line)
