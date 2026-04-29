import os, re

articles_dir = "articles"

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if there's a lang-content data-lang="en" in the header that contains body content
    # Look for the pattern: <header>...<div class="lang-content" data-lang="en">...<h2 or lots of <p>...</header>
    
    # Find header section
    header_match = re.search(r'(<header[^>]*>)(.*?)(</header>)', content, re.S)
    if not header_match:
        return 0, "No header found"
    
    header_start, header_inner, header_end = header_match.groups()
    
    # Check if header's EN lang-content contains body-level content (<h2> or multiple <p>)
    en_hero_match = re.search(r'(<div class="lang-content" data-lang="en">)(.*?)(</div>)', header_inner, re.S)
    if not en_hero_match:
        return 0, "No EN hero found"
    
    en_hero_open, en_hero_content, en_hero_close = en_hero_match.groups()
    
    # Check if this contains body content
    h2_count = len(re.findall(r'<h[23]', en_hero_content))
    p_count = len(re.findall(r'<p>', en_hero_content))
    img_count = len(re.findall(r'<img', en_hero_content))
    
    # If it has h2 or many p tags or many images, it's likely corrupted
    if h2_count == 0 and p_count <= 2 and img_count <= 1:
        return 0, f"Hero looks OK (h2={h2_count}, p={p_count}, img={img_count})"
    
    # Find the split point - first occurrence of <h2>, or after images if no h2
    split_patterns = [r'<h2', r'<h3', r'<p><strong>']
    split_pos = -1
    
    for pattern in split_patterns:
        m = re.search(pattern, en_hero_content)
        if m:
            split_pos = m.start()
            break
    
    if split_pos < 0:
        # No clear split - check if there are too many images
        if img_count > 5:
            # Find position after reasonable number of images
            img_matches = list(re.finditer(r'<img', en_hero_content))
            if len(img_matches) > 3:
                # Keep first few images in hero (or none), move rest to body
                split_pos = img_matches[0].start() if img_matches else 0
        else:
            return 0, "Cannot find split point"
    
    # Split the content
    hero_part = en_hero_content[:split_pos]
    body_part = en_hero_content[split_pos:]
    
    # Clean hero part - remove images, keep only title if present
    hero_clean = re.sub(r'\s*<img[^>]*>\s*', '', hero_part)
    hero_clean = re.sub(r'\s*<p>.*?</p>\s*', '', hero_clean, flags=re.S)
    hero_clean = hero_clean.strip()
    
    if not hero_clean:
        # No title found in hero, extract from meta
        hero_clean = '<h1 class="article-hero__title">Article</h1>'
    
    # Build new header inner
    new_en_hero = f'<div class="lang-content" data-lang="en">{hero_clean}</div>'
    
    # Build body EN block
    new_en_body = f'<div class="lang-content" data-lang="en">{body_part}</div>'
    
    # Replace in header inner
    new_header_inner = header_inner.replace(
        en_hero_open + en_hero_content + en_hero_close,
        new_en_hero
    )
    
    # Rebuild content with fixed header
    new_content = content.replace(
        header_start + header_inner + header_end,
        header_start + new_header_inner + header_end
    )
    
    # Now find the body EN div in main and replace it
    # But first check if body EN div exists separately
    body_en_matches = list(re.finditer(
        r'<div class="lang-content" data-lang="en">.*?</div>\s*</div>\s*<nav',
        new_content, re.S
    ))
    
    if len(body_en_matches) >= 1:
        # Replace the last body EN div with our new content
        last_match = body_en_matches[-1]
        old_body_en = last_match.group(0)
        # Remove the trailing </div><nav part
        new_body_en = new_en_body + '\n</div>\n<nav'
        new_content = new_content.replace(old_body_en, new_body_en)
    else:
        # Insert body EN before </div><nav
        new_content = re.sub(
            r'(</div>\s*<nav)',
            new_en_body + '\n\\1',
            new_content,
            count=1
        )
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return 1, f"Fixed hero structure (h2={h2_count}, p={p_count}, img={img_count})"

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

with open("scripts/fix_hero_structure_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
