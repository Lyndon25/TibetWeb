import os, re

fixes = {
    "articles/spring-economy-tibet-tourism.html": [
        ("activated off-season客流,", "activated off-season tourist flow,"),
        ('The常规热门线路依旧以拉萨、林芝、珠峰为核心的"铁三角"为主.', 'The classic hot routes still center on Lhasa, Nyingchi, and Everest as the "iron triangle."'),
    ],
    "articles/spring-snow-peach-blossoms.html": [
        ('镶嵌在雪线、蓝天、白云之下,春意盎然,"钱"景正好.', 'set against snowlines, blue sky, and white clouds — a vibrant spring with promising prospects.'),
        ("has翻越垭口 as promised", "has crossed mountain passes as promised"),
        ("not just about遍野的花色", "not just about blossoms across the fields"),
        ("attracts大量游客观赏桃花 each year", "attracts large numbers of tourists to admire peach blossoms each year"),
        ("cloud tea fragrance致富 stories", "cloud tea fragrance prosperity stories"),
        ("plateau specialty products走出深山", "plateau specialty products emerging from remote mountains"),
    ],
    "articles/tibet-52-tips-avoid-pitfalls.html": [
        ("心肺 (cardiopulmonary)", "cardiopulmonary"),
        ("红景天", "Rhodiola rosea"),
        ("温差 (temperature difference)", "temperature difference"),
        ("确认/confirmation", "confirmation"),
        ("正规 (formal)", "formal"),
        ("极致 (ultimate)", "ultimate"),
        ("分段 (in segments)", "in segments"),
        ("以及其他 (and others)", "and others"),
        ('Key phrase:"Tashi Delek" (扎西德勒)', 'Key phrase: "Tashi Delek"'),
    ],
    "articles/tibet-celebrity-route-beginners.html": [
        ('(一措再措)', ''),
        ('(库拉岗日)', ''),
        ('Shannan (山南)', 'Shannan'),
        ('Yalong (雅砻)', 'Yalong'),
        ('Nyenchen Tanglha (念青唐古拉山)', 'Nyenchen Tanglha'),
        ('Yamdrok Yumco (羊卓雍错)', 'Yamdrok Yumco'),
        ('Ritro Temple (日托寺)', 'Ritro Temple'),
        ('Puma Yumco (普莫雍错)', 'Puma Yumco'),
        ('Tuwa Temple (推瓦寺)', 'Tuwa Temple'),
        ('Baima Linco (白马林错)', 'Baima Linco'),
        ('Zhegong Co (折公错)', 'Zhegong Co'),
        ('Jiejiu Co (介久错)', 'Jiejiu Co'),
        ('徒步中国 (Hiking China)', 'Hiking China'),
    ],
}

log = []
for path, replacements in fixes.items():
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        log.append(f"Modified: {path}")
    else:
        log.append(f"No changes: {path}")

with open("scripts/fix_remaining_mixed_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))

print("\n".join(log))
