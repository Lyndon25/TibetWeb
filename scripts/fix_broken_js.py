"""Fix broken JS array entries and img tags in articles/index.html."""
import os, re

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
filepath = os.path.join(root, 'articles', 'index.html')

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = content

# Fix: img:'images/xxxxx.webp featured:false },  -> img:'images/xxxxx.webp', featured:false },
content = re.sub(
    r"(img:'images/[a-f0-9]+\.webp) (featured:\w+)",
    r"\1', \2",
    content
)
# Fix: img:'images/DDD_HASH.jpg featured:false },  -> img:'images/DDD_HASH.jpg', featured:false },
content = re.sub(
    r"(img:'images/\d+_[a-f0-9]+\.jpg) (featured:\w+)",
    r"\1', \2",
    content
)
# Also fix any other img:'images/... pattern missing closing quote
content = re.sub(
    r"(img:'images/[a-f0-9_]+\.(?:webp|jpg|jpeg|png)) (featured|},)",
    r"\1', \2",
    content
)

if content != old:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed articles/index.html')

# Verify
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for any remaining broken img entries
broken = []
for line in content.split('\n'):
    if "img:'" in line and line.strip().endswith('featured:false },'):
        if not re.search(r"img:'[^']+',", line):
            broken.append(line.strip()[:120])

if broken:
    print(f'WARNING: {len(broken)} still broken:')
    for b in broken[:5]:
        print(f'  {b}')
else:
    print('All JS entries valid!')

# Now also fix broken img tags in article HTML files
# Pattern: <img src="images/xxxxx.webp" ... > where the closing " is missing
count = 0
for dirpath, dirnames, filenames in os.walk(root):
    if 'AddingArticleWorkSpace' in dirpath or '.git' in dirpath:
        continue
    for f in filenames:
        if f.endswith('.html'):
            fpath = os.path.join(dirpath, f)
            with open(fpath, 'r', encoding='utf-8') as fh:
                c = fh.read()

            old_c = c
            # Fix: src="images/xxx.webp alt=" -> src="images/xxx.webp" alt="
            c = re.sub(r'(src="images/[a-f0-9]+\.webp) (alt=|loading=|class=|width=|height=|style=|data-)', r'\1" \2', c)
            # Fix: src="images/xxx.webp> or src="images/xxx.webp<
            c = re.sub(r'(src="images/[a-f0-9]+\.webp)([>\s<])', r'\1"\2', c)

            if c != old_c:
                with open(fpath, 'w', encoding='utf-8') as fh:
                    fh.write(c)
                count += 1
                rel = os.path.relpath(fpath, root)
                print(f'Fixed img tags: {rel}')

print(f'Fixed img tags in {count} files')
