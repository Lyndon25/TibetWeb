import os, re, html

articles_dir = "articles"
out_path = "scripts/scan_zh_english_results.txt"

# Pattern to find ZH lang-content block
pattern = re.compile(r'<div class="lang-content" data-lang="zh">(.*?)</div>\s*<div class="lang-content" data-lang="en">', re.S)

# English word pattern (at least 2 chars, excluding common proper nouns and codes)
english_word = re.compile(r'[a-zA-Z]{2,}')

# Exclusions: common proper nouns, brands, locations, HTML attributes, URLs
exclusions = {
    # Common HTML/CSS/tech
    "src", "alt", "href", "class", "style", "loading", "lazy", "img", "div", "span", "p", "h1", "h2", "h3", "strong", "em",
    # Common proper nouns/locations
    "Tibet", "Lhasa", "Nyingchi", "Shigatse", "Ngari", "Shannan", "Chamdo", "Nagqu",
    "Everest", "Himalaya", "Himalayas", "Yarlung", "Tsangpo", "Brahmaputra",
    "Kailash", "Manasarovar", "Rakshastal", "Yamdrok", "Namtso", "Namcha", "Barwa",
    "Bomi", "Lhunzhub", "Lhozhag", "Gyirong", "Zanda", "Burang", "Gerze", "Coqen",
    "Qinghai", "Sichuan", "Yunnan", "Nepal", "Bhutan", "India",
    "Potala", "Jokhang", "Norbulingka", "Barkhor", "Sera", "Drepung", "Ganden",
    "Kagyu", "Gelug", "Sakya", "Nyingma", "Karma",
    "Songtsen", "Gampo", "Gesar", "Rinpoche", "Guru",
    # Months
    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec",
    # Common English words in Chinese context that are acceptable
    "KM", "kg", "km", "mm", "cm", "m", "MP", "GPS", "WiFi", "DNA", "VIP",
    "vs", "VS", "OK", "TV", "PC", "CD", "USB", "ID", "DIY",
    "Spring", "Summer", "Autumn", "Winter", "Festival", "New", "Year",
    "Day", "Route", "Route", "Tour", "Travel", "Tourism",
    "China", "Chinese", "Tibetan", "English",
    # Common terms
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
}

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
    zh_block = m.group(1)
    text = re.sub(r'<[^>]+>', '', zh_block)
    text = html.unescape(text)
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines, 1):
        words = english_word.findall(line)
        # Filter out excluded words and single letters
        filtered = [w for w in words if w not in exclusions and len(w) > 1]
        if filtered:
            found.append((i, line.strip(), filtered))
    if found:
        results.append((fn, found))

with open(out_path, "w", encoding="utf-8") as f:
    if not results:
        f.write("No unexpected English found in ZH blocks.\n")
    else:
        for fn, found in results:
            f.write(f"\n=== {fn} ===\n")
            for line_no, line_text, words in found:
                f.write(f"  L{line_no}: [{', '.join(words)}] | {line_text}\n")

print(f"Results written to {out_path}")
print(f"Files with unexpected English in ZH block: {len(results)}")
for fn, _ in results:
    print(f"  - {fn}")
