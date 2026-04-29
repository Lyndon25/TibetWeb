import os, re
from bs4 import BeautifulSoup

articles_dir = "articles"

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    
    soup = BeautifulSoup(raw, 'html.parser')
    
    # Find ZH body block (inside article-body)
    article_body = soup.find('div', class_='article-body')
    if not article_body:
        return 0, "No article-body found"
    
    zh_div = article_body.find('div', attrs={'data-lang': 'zh'})
    en_div = article_body.find('div', attrs={'data-lang': 'en'})
    
    if not zh_div or not en_div:
        return 0, "Missing ZH or EN body div"
    
    # Extract images from ZH body
    zh_imgs = zh_div.find_all('img')
    if not zh_imgs:
        return 0, "No images in ZH body"
    
    # Get image HTML strings (with proper formatting)
    img_htmls = []
    for img in zh_imgs:
        # Remove all attributes except src, alt, loading
        src = img.get('src', '')
        alt = img.get('alt', '')
        loading = img.get('loading', 'lazy')
        img_htmls.append(f'<img src="{src}" alt="{alt}" loading="{loading}">')
    
    # Clean EN div: remove all existing images
    for img in en_div.find_all('img'):
        img.decompose()
    
    # Get EN div content as text
    en_html = str(en_div)
    # Extract inner content (between <div ...> and </div>)
    en_inner = en_html[en_html.find('>')+1:-6]  # Remove <div ...> and </div>
    
    # Distribute images in EN body
    h2_positions = [m.start() for m in re.finditer(r'<h2', en_inner)]
    
    if len(h2_positions) <= 1:
        new_inner = '\n'.join(img_htmls) + '\n' + en_inner
    else:
        sections = []
        last_end = 0
        for pos in h2_positions:
            if pos > last_end:
                sections.append(en_inner[last_end:pos])
            h2_end = en_inner.find('</h2>', pos)
            if h2_end > 0:
                h2_end += 5
                sections.append(en_inner[pos:h2_end])
                last_end = h2_end
            else:
                sections.append(en_inner[pos:])
                last_end = len(en_inner)
        if last_end < len(en_inner):
            sections.append(en_inner[last_end:])
        
        num_h2 = sum(1 for s in sections if s.strip().startswith('<h2'))
        total = max(1, num_h2)
        imgs_per = len(img_htmls) // total
        remainder = len(img_htmls) % total
        
        new_sections = []
        img_idx = 0
        
        for section in sections:
            new_sections.append(section)
            if section.strip().startswith('<h2'):
                count = imgs_per + (1 if remainder > 0 else 0)
                remainder = max(0, remainder - 1)
                for _ in range(count):
                    if img_idx < len(img_htmls):
                        new_sections.append('\n' + img_htmls[img_idx] + '\n')
                        img_idx += 1
        
        while img_idx < len(img_htmls):
            new_sections.append('\n' + img_htmls[img_idx] + '\n')
            img_idx += 1
        
        new_inner = ''.join(new_sections)
    
    # Replace EN div inner content
    new_en_html = en_html[:en_html.find('>')+1] + new_inner + '</div>'
    
    # Also clean hero EN div (remove images, keep only title)
    hero = soup.find('header', class_='article-hero')
    if hero:
        hero_en = hero.find('div', attrs={'data-lang': 'en'})
        if hero_en:
            for img in hero_en.find_all('img'):
                img.decompose()
            hero_en_html = str(hero_en)
            # Replace in raw
            raw = raw.replace(str(hero.find('div', attrs={'data-lang': 'en'})), hero_en_html)
    
    # Replace body EN div in raw
    raw = raw.replace(en_html, new_en_html)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    
    return len(img_htmls), f"Added {len(img_htmls)} images to body"

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

with open("scripts/fix_en_images_bs_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print(f"Processed {total_fixed} files")
for line in log:
    print(line)
