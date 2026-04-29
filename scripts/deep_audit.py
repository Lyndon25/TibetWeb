import os, re, html
from html.parser import HTMLParser

articles_dir = "articles"

class TagExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.img_count = 0
        self.current_text = []
        self.in_skip = 0
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in ('script','style'):
            self.in_skip += 1
            return
        self.tags.append(('start', tag, attrs_dict))
        if tag == 'img':
            self.img_count += 1
    def handle_endtag(self, tag):
        if tag in ('script','style'):
            self.in_skip -= 1
            return
        self.tags.append(('end', tag, {}))
    def handle_data(self, data):
        if self.in_skip <= 0:
            self.current_text.append(data)

def extract_blocks_safe(content, lang):
    """Extract lang-content blocks correctly handling nested divs."""
    blocks = []
    pattern_start = f'<div class="lang-content" data-lang="{lang}">'
    pos = 0
    while True:
        idx = content.find(pattern_start, pos)
        if idx < 0:
            break
        start = idx + len(pattern_start)
        depth = 1
        p = start
        while depth > 0 and p < len(content):
            next_open = content.find('<div', p)
            next_close = content.find('</div>', p)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                p = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    end = next_close
                    break
                p = next_close + 6
        else:
            pos = start + 1
            continue
        blocks.append(content[start:end])
        pos = end + 6
    return blocks

def count_imgs(block):
    return len(re.findall(r'<img\b', block, re.I))

def count_tags(block):
    ext = TagExtractor()
    try:
        ext.feed(block)
    except:
        pass
    return ext.tags, ext.img_count

def find_chinese_in_en(block):
    zh = re.compile(r'[\u4e00-\u9fff]')
    # Remove HTML tags for cleaner text
    text = re.sub(r'<[^>]+>', ' ', block)
    text = html.unescape(text)
    # Remove parenthetical Chinese annotations like "Shannan (山南)"
    text = re.sub(r'\([\u4e00-\u9fff\s·]+\)', '', text)
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and zh.search(stripped):
            found.append((i, stripped[:120]))
    return found

zh_char = re.compile(r'[\u4e00-\u9fff]')

def has_chinese(text):
    return bool(zh_char.search(text))

results = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html") or fn == "index.html":
        continue
    path = os.path.join(articles_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract all lang-content blocks
    zh_blocks = extract_blocks_safe(content, 'zh')
    en_blocks = extract_blocks_safe(content, 'en')
    
    issues = []
    
    # 1. Check hero block structure (first block typically in hero)
    if len(en_blocks) >= 1:
        en_hero = en_blocks[0]
        zh_hero = zh_blocks[0] if zh_blocks else ""
        # Check if EN hero has way more content than ZH hero
        en_hero_text = re.sub(r'<[^>]+>', '', en_hero)
        zh_hero_text = re.sub(r'<[^>]+>', '', zh_hero)
        # EN hero naturally longer than ZH due to language characteristics
        # Only flag if EN hero is extremely long (>200 chars) which indicates corruption
        if len(en_hero_text) > 200:
            issues.append(f"EN hero suspiciously long ({len(en_hero_text)} chars)")
        # Check for Chinese in EN hero
        zh_in_en_hero = find_chinese_in_en(en_hero)
        if zh_in_en_hero:
            issues.append(f"Chinese in EN hero: {len(zh_in_en_hero)} lines")
    
    # 2. Check body blocks (second block typically)
    if len(en_blocks) >= 2 and len(zh_blocks) >= 2:
        en_body = en_blocks[1]
        zh_body = zh_blocks[1]
        
        en_imgs = count_imgs(en_body)
        zh_imgs = count_imgs(zh_body)
        if en_imgs != zh_imgs:
            issues.append(f"Image count mismatch: ZH={zh_imgs}, EN={en_imgs}")
        
        zh_in_en_body = find_chinese_in_en(en_body)
        if zh_in_en_body:
            issues.append(f"Chinese in EN body: {len(zh_in_en_body)} lines")
            for line_no, line_text in zh_in_en_body[:3]:
                issues.append(f"  L{line_no}: {line_text[:80]}")
    elif len(en_blocks) != len(zh_blocks):
        issues.append(f"Block count mismatch: ZH={len(zh_blocks)}, EN={len(en_blocks)}")
    
    # 3. Check for Chinese in any EN block
    for i, en_block in enumerate(en_blocks):
        zh_found = find_chinese_in_en(en_block)
        if zh_found:
            issues.append(f"EN block {i}: {len(zh_found)} Chinese lines")
    
    # 4. Check title structure
    title_zh = re.search(r'<h1[^>]*class="article-hero__title"[^>]*>(.*?)</h1>', content, re.S)
    title_en = re.search(r'<div class="lang-content" data-lang="en">.*?<h[123][^>]*>(.*?)</h[123]>', content, re.S)
    if title_zh and title_en:
        zh_title_text = re.sub(r'<[^>]+>', '', title_zh.group(1))
        en_title_text = re.sub(r'<[^>]+>', '', title_en.group(1))
        if has_chinese(en_title_text):
            issues.append(f"EN title contains Chinese: {en_title_text[:60]}")
        if has_chinese(zh_title_text) == False and len(zh_title_text.strip()) > 0:
            # ZH title should have Chinese
            pass
    
    if issues:
        results.append((fn, issues))

out_path = "scripts/deep_audit_results.txt"
with open(out_path, "w", encoding="utf-8") as f:
    if not results:
        f.write("No issues found in any files.\n")
    else:
        for fn, issues in results:
            f.write(f"\n=== {fn} ===\n")
            for issue in issues:
                f.write(f"  - {issue}\n")

print(f"Audit complete. Results in {out_path}")
print(f"Files with issues: {len(results)}")
for fn, _ in results:
    print(f"  - {fn}")
