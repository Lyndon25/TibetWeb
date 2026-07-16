"""Generate updated sitemap.xml — only include reachable URLs."""
import os, re
from datetime import date

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
base = 'https://www.tibetride.com'

pages = []

for dirpath, dirnames, filenames in os.walk(root):
    rel_dir = os.path.relpath(dirpath, root).replace('\\', '/')
    if any(skip in rel_dir.split('/')[0] for skip in ['AddingArticleWorkSpace', 'templates', '.git', 'node_modules', 'scripts']):
        continue
    for f in sorted(filenames):
        if f.endswith('.html') and f != 'gsc-helper.html':
            rel = os.path.relpath(os.path.join(dirpath, f), root).replace('\\', '/')

            if rel == 'index.html':
                url = '/'
            elif f == 'index.html':
                # Subdirectory index: articles/{slug}/index.html -> /articles/{slug}
                url = '/' + rel[:-11]
            else:
                # Standalone .html file (not index.html)
                slug_no_ext = rel[:-5]
                dir_check = os.path.join(root, slug_no_ext, 'index.html')

                if os.path.exists(dir_check):
                    # Directory version exists — skip this standalone file
                    # (directory index.html takes precedence via Vercel route)
                    continue
                elif slug_no_ext.startswith('articles/'):
                    # Article .html without directory version: MUST use .html
                    # because Vercel route redirects clean URL to nonexistent index.html
                    url = '/' + slug_no_ext + '.html'
                else:
                    # Root-level or guides: clean URL works via Vercel route
                    url = '/' + slug_no_ext

            pages.append(url)

def get_priority(url):
    if url == '/':
        return '1.0', 'weekly'
    if url in ['/tours', '/articles']:
        return '0.9', 'weekly'
    if url in ['/customize']:
        return '0.8', 'monthly'
    if url.startswith('/tours/'):
        return '0.8', 'monthly'
    if url in ['/about', '/contact', '/routes', '/guides', '/videos']:
        return '0.7', 'monthly'
    if url.startswith('/guides/'):
        return '0.7', 'monthly'
    high_priority = ['tibet-trip-cost-2026', 'is-tibet-safe-2026', 'best-time-to-visit-tibet-2026', 'plan-first-tibet-trip-2026']
    for hp in high_priority:
        if hp in url:
            return '0.7', 'monthly'
    if '/articles/' in url:
        return '0.6', 'monthly'
    return '0.6', 'monthly'

today = date.today().strftime('%Y-%m-%d')
urls = sorted(set(pages), key=lambda u: (get_priority(u)[0], u), reverse=True)

xml = ['<?xml version="1.0" encoding="UTF-8"?>']
xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
xml.append(f'<!-- Generated: {today} | Total URLs: {len(urls)} -->')

for url in urls:
    priority, changefreq = get_priority(url)
    xml.append('  <url>')
    xml.append(f'    <loc>{base}{url}</loc>')
    xml.append(f'    <lastmod>{today}</lastmod>')
    xml.append(f'    <changefreq>{changefreq}</changefreq>')
    xml.append(f'    <priority>{priority}</priority>')
    xml.append('  </url>')

xml.append('</urlset>')
xml.append('')

sitemap_path = os.path.join(root, 'sitemap.xml')
with open(sitemap_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(xml))

print(f'Sitemap: {len(urls)} URLs (was 27, now +{len(urls)-27})')

# Verify all URLs are clean (no .html except for legacy articles)
for u in urls:
    if u.endswith('.html') and not u.startswith('/articles/'):
        print(f'WARN: Non-article .html URL: {u}')
    if u.endswith('.html'):
        print(f'LEGACY .html URL: {u}')
