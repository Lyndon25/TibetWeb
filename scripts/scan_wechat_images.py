"""Scan how many WeChat CDN references each article has vs local images."""
import os, re

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
results = []

for dirpath, dirnames, filenames in os.walk(root):
    rel_dir = os.path.relpath(dirpath, root).replace('\\', '/')
    if not rel_dir.startswith('articles/'):
        continue
    if 'AddingArticleWorkSpace' in dirpath:
        continue

    local_imgs = [f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

    html_path = os.path.join(dirpath, 'index.html')
    if not os.path.exists(html_path):
        continue

    with open(html_path, 'r', encoding='utf-8') as fh:
        content = fh.read()

    wechat_count = len(re.findall(r'https?://[^\"\s]*mmbiz\.qpic\.cn[^\"\s]*', content))
    wechat_count += len(re.findall(r'https?://[^\"\s]*mmecoa\.qpic\.cn[^\"\s]*', content))

    if wechat_count > 0:
        results.append((rel_dir, len(local_imgs), wechat_count))

results.sort(key=lambda x: -x[2])
print(f"{'Article':<60} {'Local':>6} {'WeChat':>7}")
print('-' * 75)
for rel, local, wc in results:
    slug = rel.split('/')[-1] if '/' in rel else rel
    print(f'{slug:<60} {local:>6} {wc:>7}')

print('-' * 75)
total_wc = sum(r[2] for r in results)
total_articles = len(results)
print(f'{total_articles} articles, {total_wc} total WeChat image references')
print(f'\nArticles needing most help:')
for rel, local, wc in results[:5]:
    print(f'  {rel} ({wc} refs, {local} local images)')
