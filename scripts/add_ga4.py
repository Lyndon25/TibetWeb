"""Add GA4 tracking code to all HTML files, inserting before </head>."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GA4_SNIPPET = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3FM3SN8GG6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-3FM3SN8GG6');
</script>
'''

count = 0
skipped = 0
errors = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip workspace, scripts dir itself, and hidden dirs
    if 'AddingArticleWorkSpace' in dirpath or '.git' in dirpath:
        continue
    for fn in filenames:
        if not fn.endswith('.html'):
            continue
        fp = os.path.join(dirpath, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'G-3FM3SN8GG6' in content:
            skipped += 1
            continue

        if '</head>' not in content:
            errors.append(f'{fp}: no </head> found')
            continue

        content = content.replace('</head>', GA4_SNIPPET + '\n</head>', 1)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1
        print(f'  OK: {os.path.relpath(fp, ROOT)}')

print(f'\nDone: {count} files updated, {skipped} already had GA4, {len(errors)} errors')
for e in errors:
    print(f'  ERR: {e}')
