import os, re

articles_dir = "articles"

# Mapping of article slugs to their English titles from convert_articles_v2.py meta
TITLE_MAP = {
    '2026-tibet-year-round-travel-guide': "2026 Let's Go to Tibet! Your Year-Round Travel Guide to This Must-Visit Destination",
    '6-routes-update-tibet-list': 'Bookmark These! 6 Routes to Refresh Your Tibet Travel List',
    'ali-year-round-travel-guide': "Attention Everyone: Ngari's Year-Round Travel Guide Is Here!",
    'altitude-sickness-tips': 'Altitude Sickness Prevention for Tibet Motorcycle Travel',
    'bianba-motorcycle-diary': 'Bianba Motorcycle Diary: The Last Blue Ice Cave',
    'bomi-spring-photography': 'Every Shot is Wallpaper-Worthy: The Stunning Spring of This Hidden Tibetan Town',
    'first-tibet-trip-guide': 'First Time in Tibet? This Guide Has Everything You Need!',
    'g216-coqen-blue-dream': 'Blue Dreams on the Plateau Summit: Discovering Coqen Along G216',
    'gerze-changtang-red-blue': "Secret Gerze: Listening to the Symphony of Red and Blue in Changtang's Heart",
    'lens-nature-human-harmony': 'Through His Lens: The Beauty of Nature and Humanity in Harmony',
    'may-day-tibet-lazy-guide': '10 Lazy Ways to Enjoy Tibet During May Day Holiday',
    'motorcycle-healing-journey': 'Born to Roam | A Motorcycle Healing Journey',
    'motorcycle-tibet-gear-guide': 'Essential Motorcycle Gear for Tibet Travel',
    'motorcycle-tibet-shannan': 'Born to Roam | A Motorcycle Journey Deep Into Shannan, Tibet',
    'ngari-spring-colors': 'Dopamine Overload! Ngari Spring Limited Color Palette',
    'planet-earth-ngari': 'Opening Ngari Through a "Planet Earth" Lens',
    'qingming-tibet-travel-guide': 'Qingming Tibet Travel Guide: Hidden Spring Getaways That Heal the Soul',
    'sichuan-tibet-central-route': 'Sichuan-Tibet Central Route Transformation: From Hardcore Hell to Scooter Heaven',
    'spring-economy-tibet-tourism': 'Spring Economy Boosts Tibet Tourism and Cultural Consumption',
    'spring-snow-peach-blossoms': 'Spring in Tibet: Peach Blossoms and Snow Paint a Prosperous Picture',
    'tibet-52-tips-avoid-pitfalls': 'Ultimate Tibet Pitfall Avoidance Guide! 52 Hard-Learned Tips Before You Go',
    'tibet-6-classic-routes': '6 Classic Tibet Routes, From 3 to 11 Days — All Covered!',
    'tibet-celebrity-route-beginners': "Tibet's Most Asked-About Celebrity Route — Beginners Welcome!",
    'wheels-shackles-tibet': 'Wheels and Shackles: A Motorcycle Journey Across Tibet',
}

log = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html") or fn == "index.html":
        continue
    
    path = os.path.join(articles_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    slug = fn.replace('.html', '')
    title = TITLE_MAP.get(slug, '')
    if not title:
        log.append(f"{fn}: No title in map")
        continue
    
    # Find hero EN block and replace with just title
    # Pattern: <div class="lang-content" data-lang="en"> in header
    hero_pattern = re.compile(r'(<header[^>]*>.*?<div class="lang-content" data-lang="en">).*?(</div>\s*</div>\s*</div>\s*</header>)', re.S)
    
    def replace_hero(match):
        return match.group(1) + f'<h1 class="article-hero__title">{title}</h1>' + match.group(2)
    
    new_content = hero_pattern.sub(replace_hero, content)
    
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        log.append(f"{fn}: Hero fixed")
    else:
        log.append(f"{fn}: No change")

with open("scripts/fix_all_heroes_log.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(log))

print('\n'.join(log))
