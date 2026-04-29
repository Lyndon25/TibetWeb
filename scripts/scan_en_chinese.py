import os, re, html

articles_dir = "articles"
pattern = re.compile(r'<div class="lang-content" data-lang="en">(.*?)</div>\s*</div>', re.S)
zh_char = re.compile(r'[\u4e00-\u9fff]')

results = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html") or fn == "index.html":
        continue
    path = os.path.join(articles_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    m = pattern.search(content)
    if not m:
        continue
    en_block = m.group(1)
    # Strip HTML tags for cleaner display of text
    text = re.sub(r'<[^>]+>', '', en_block)
    text = html.unescape(text)
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines, 1):
        if zh_char.search(line):
            found.append((i, line.strip()))
    if found:
        results.append((fn, found))

if not results:
    print("No Chinese found in EN blocks.")
else:
    for fn, found in results:
        print(f"\n=== {fn} ===")
        for line_no, line_text in found:
            print(f"  L{line_no}: {line_text}")
