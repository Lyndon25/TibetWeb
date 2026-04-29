import os, re

articles_dir = 'articles'
for f in sorted(os.listdir(articles_dir)):
    if not f.endswith('.html') or f == 'index.html':
        continue
    with open(os.path.join(articles_dir, f), 'r', encoding='utf-8') as file:
        content = file.read()
    matches = re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', content, re.DOTALL)
    if matches:
        longest = max(len(m.strip()) for m in matches)
        status = 'OK' if longest > 800 else 'SHORT'
    else:
        longest = 0
        status = 'MISSING'
    print(f"{f:45s} {status:8s} {longest:5d} chars")
