import os, re

articles_dir = "articles"

fixes = {
    "g216-coqen-blue-dream.html": [
        ("西藏阿里文旅 (Tibet Ngari Cultural Tourism)", "Tibet Ngari Cultural Tourism"),
        ("拉琼拉垭口", ""),
        ("桑木拉达坂", ""),
    ],
    "may-day-tibet-lazy-guide.html": [],  # Need manual inspection
    "motorcycle-healing-journey.html": [
        ('爽文 mode', 'winning-life mode'),
    ],
    "motorcycle-tibet-shannan.html": [],  # Need manual inspection
    "qingming-tibet-travel-guide.html": [],  # Need manual inspection
    "sichuan-tibet-central-route.html": [
        ('专治"路面太平想找刺激"的病', 'for those who find paved roads too boring'),
        ('蹭WiFi', 'use WiFi'),
    ],
    "tibet-52-tips-avoid-pitfalls.html": [
        ('寻疆旅行 (Xunjiang Travel)', 'Xunjiang Travel'),
        ('最强效 (strongest)', 'strongest'),
        ('大型 (large)', 'large'),
    ],
    "tibet-celebrity-route-beginners.html": [
        ('"Yumco" (雍措)', '"Yumco"'),
    ],
    "wheels-shackles-tibet.html": [],  # Need manual inspection
}

log = []
for fn, replacements in fixes.items():
    path = os.path.join(articles_dir, fn)
    if not os.path.exists(path):
        log.append(f"{fn}: Not found")
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        log.append(f"{fn}: Fixed {len(replacements)} replacements")
    else:
        log.append(f"{fn}: No changes")

with open("scripts/fix_remaining_cn_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
