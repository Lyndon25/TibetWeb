import os, re
from bs4 import BeautifulSoup

articles_dir = "articles"

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    
    soup = BeautifulSoup(raw, 'html.parser')
    
    article_body = soup.find('div', class_='article-body')
    if not article_body:
        return 0, "No article-body"
    
    zh_div = article_body.find('div', attrs={'data-lang': 'zh'})
    en_div = article_body.find('div', attrs={'data-lang': 'en'})
    
    if not zh_div or not en_div:
        return 0, "Missing lang divs"
    
    zh_imgs = zh_div.find_all('img')
    en_imgs = en_div.find_all('img')
    
    if len(en_imgs) > len(zh_imgs):
        # Remove excess images from EN body
        excess = len(en_imgs) - len(zh_imgs)
        for img in en_imgs[-excess:]:
            img.decompose()
        
        new_en_html = str(en_div)
        old_en_html_match = re.search(r'<div class="lang-content" data-lang="en">.*?</div>', raw, re.S)
        if old_en_html_match:
            old_en_html = old_en_html_match.group(0)
            # Find the actual EN div in raw (the longest one in article-body)
            # Use BeautifulSoup to get the exact representation
            raw = raw.replace(old_en_html, new_en_html)
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
            return excess, f"Removed {excess} excess images (ZH={len(zh_imgs)}, EN was {len(en_imgs)})"
    
    return 0, f"OK (ZH={len(zh_imgs)}, EN={len(en_imgs)})"

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

with open("scripts/fix_image_counts_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
