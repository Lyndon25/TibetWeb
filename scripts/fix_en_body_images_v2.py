import os, re

articles_dir = "articles"

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all lang-content blocks for zh and en
    zh_blocks = re.findall(r'<div class="lang-content" data-lang="zh">(.*?)</div>', content, re.S)
    en_blocks = re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', content, re.S)
    
    if len(zh_blocks) < 2 or len(en_blocks) < 2:
        return 0, f"Need at least 2 blocks each (got ZH={len(zh_blocks)}, EN={len(en_blocks)})"
    
    # Body blocks are typically the longest ones
    zh_body = max(zh_blocks, key=len)
    en_body = max(en_blocks, key=len)
    
    # Extract images from ZH body
    zh_imgs = re.findall(r'<img[^>]*>', zh_body)
    if not zh_imgs:
        return 0, "No images in ZH body"
    
    # Check EN body images
    en_imgs = re.findall(r'<img[^>]*>', en_body)
    
    if len(en_imgs) >= len(zh_imgs):
        return 0, f"EN already has sufficient images ({en_imgs}/{zh_imgs})"
    
    # Strategy: Find the EN body block in the original content and replace it
    # Build new EN body with images inserted
    
    # Find <h2> positions in EN body
    h2_matches = list(re.finditer(r'<h2', en_body))
    
    if len(h2_matches) <= 1:
        # Put all images at the start of EN body
        new_en_body = '\n'.join(zh_imgs) + '\n' + en_body
    else:
        # Distribute images among sections
        sections = []
        last_end = 0
        
        for m in h2_matches:
            pos = m.start()
            if pos > last_end:
                sections.append(('text', en_body[last_end:pos]))
            # Find end of this h2 tag
            h2_end = en_body.find('</h2>', pos)
            if h2_end > 0:
                h2_end += 5
                sections.append(('h2', en_body[pos:h2_end]))
                last_end = h2_end
            else:
                sections.append(('h2', en_body[pos:]))
                last_end = len(en_body)
        
        if last_end < len(en_body):
            sections.append(('text', en_body[last_end:]))
        
        # Distribute images
        num_h2_sections = sum(1 for t, _ in sections if t == 'h2')
        h2_sections = [i for i, (t, _) in enumerate(sections) if t == 'h2']
        
        total_sections = max(1, num_h2_sections)
        imgs_per_section = len(zh_imgs) // total_sections
        remainder = len(zh_imgs) % total_sections
        
        new_sections = []
        img_idx = 0
        h2_idx = 0
        
        for t, section in sections:
            new_sections.append(section)
            if t == 'h2':
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
    
    # Replace EN body in original content
    # Need to be careful to replace the right block (the longest one)
    # Find the actual EN body in content by its position
    en_body_positions = []
    for m in re.finditer(r'<div class="lang-content" data-lang="en">', content):
        start = m.end()
        # Find matching </div> - need to count nesting
        # Simple approach: find the </div> that ends this block
        # Since body en block is followed by </div></div><nav or similar
        end = content.find('</div>', start)
        while end > 0:
            block_content = content[start:end]
            # Check if this looks like the body block (long enough)
            if len(block_content) == len(en_body):
                en_body_positions.append((start, end))
                break
            end = content.find('</div>', end + 1)
    
    if not en_body_positions:
        # Fallback: just replace the longest en block content
        # This is risky but let's try
        # Find the exact text of en_body in content
        idx = content.find(en_body)
        if idx < 0:
            return 0, "Cannot locate EN body in content"
        new_content = content[:idx] + new_en_body + content[idx + len(en_body):]
    else:
        start, end = en_body_positions[0]
        new_content = content[:start] + new_en_body + content[end:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return len(zh_imgs), f"Added {len(zh_imgs)} images (EN had {len(en_imgs)})"

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

with open("scripts/fix_en_body_images_log_v2.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print(f"Fixed {total_fixed} files")
for line in log:
    print(line)
