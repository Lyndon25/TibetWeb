"""
Centralized article configuration loader.

Reads metadata from a single source of truth (articles.yaml or articles.json).
Falls back to the inline dict in convert_articles_v2.py if config file missing.

TODO: Migrate all hard-coded metadata into config/articles.yaml and remove fallback.
"""
import os
import json
from typing import Optional


CONFIG_PATHS = [
    'config/articles.yaml',
    'config/articles.json',
    'scripts/articles.json',
]


def _fallback_meta() -> list[dict]:
    """Fallback inline metadata copied from convert_articles_v2.py.
    Kept for backward compatibility until YAML config is populated."""
    return [
        {
            'file_pattern': '2026一起去西藏这个人生必去目的地全年出游攻略请查收',
            'slug': '2026-tibet-year-round-travel-guide',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Jan 5, 2026', 'time': '8 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '2026一起去西藏！这个人生必去目的地，全年出游攻略请查收！',
            'titleEn': "2026 Let's Go to Tibet! Your Year-Round Travel Guide to This Must-Visit Destination",
            'excerptZh': '从春花到冬雪，从林芝桃花到阿里荒原，2026西藏全年出游攻略帮你规划最佳旅行时间。',
            'excerptEn': 'From spring blossoms to winter snow, from Nyingchi peach flowers to Ali wilderness — plan your perfect Tibet trip month by month.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '被问爆的西藏明星同款线小白也能冲',
            'slug': 'tibet-celebrity-route-beginners',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Mar 15, 2026', 'time': '7 min read', 'authorZh': '小鱼/般般', 'authorEn': 'Xiaoyu / Banban',
            'titleZh': '被问爆的西藏"明星同款线"，小白也能冲！',
            'titleEn': "Tibet's Most Asked-About Celebrity Route — Beginners Welcome!",
            'excerptZh': '库拉岗日徒步节、羊卓雍错环湖、普莫雍错蓝冰……这些西藏明星同款线路，新手也能轻松驾驭。',
            'excerptEn': 'Kula Gangri trekking, Yamdrok Lake circuit, Pumoyongcuo blue ice — these celebrity-level Tibet routes are beginner-friendly too.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '当我以地球脉动的方式打开阿里',
            'slug': 'planet-earth-ngari',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Apr 8, 2026', 'time': '6 min read', 'authorZh': '文化西藏', 'authorEn': 'Culture Tibet',
            'titleZh': '当我以"地球脉动"的方式打开阿里',
            'titleEn': 'Opening Ngari Through a "Planet Earth" Lens',
            'excerptZh': '用纪录片视角探索西藏阿里——从冈仁波齐到玛旁雍错，感受地球最原始的脉动。',
            'excerptEn': "Exploring Tibet's Ngari through a documentary lens — from Mount Kailash to Lake Manasarovar, feel the planet's primordial pulse.",
            'has_en_translation': True,
        },
        {
            'file_pattern': '第一次去西藏旅行看这篇就够了',
            'slug': 'first-tibet-trip-guide',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Feb 20, 2026', 'time': '10 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '第一次去西藏旅行？看这篇就够了！',
            'titleEn': 'First Time in Tibet? This Guide Has Everything You Need!',
            'excerptZh': '高反预防、最佳季节、必备装备、经典路线——首次进藏全攻略，一篇解决所有疑问。',
            'excerptEn': 'Altitude sickness prevention, best seasons, essential gear, classic routes — your complete first-timer guide to Tibet.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '多巴胺爆棚阿里春日限定色号上线',
            'slug': 'ngari-spring-colors',
            'cat': 'photography', 'catLabel': 'Photography', 'catLabelZh': '摄影',
            'date': 'Apr 12, 2026', 'time': '5 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
            'titleZh': '多巴胺爆棚！阿里春日限定色号上线',
            'titleEn': 'Dopamine Overload! Ngari Spring Limited Color Palette',
            'excerptZh': '阿里春天的色彩盛宴——从土林的金黄到圣湖的湛蓝，每一帧都是大自然的调色盘。',
            'excerptEn': "A feast of spring colors in Ngari — from golden earth forests to sapphire sacred lakes, every frame is nature's palette.",
            'has_en_translation': True,
        },
        {
            'file_pattern': '高原之巅蓝色梦境在216国道遇见措勤这些地方你可曾到达',
            'slug': 'g216-coqen-blue-dream',
            'cat': 'routes', 'catLabel': 'Routes', 'catLabelZh': '路线',
            'date': 'Apr 18, 2026', 'time': '6 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
            'titleZh': '高原之巅蓝色梦境：在216国道遇见措勤，这些地方你可曾到达？',
            'titleEn': 'Blue Dreams on the Plateau Summit: Discovering Coqen Along G216',
            'excerptZh': '沿着216国道穿越羌塘高原，在措勤遇见遗世独立的蓝色梦境——仁多乡、扎日南木错、当惹雍错。',
            'excerptEn': 'Crossing the Changtang Plateau along G216, discover the secluded blue dreamscapes of Coqen.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '旅游西藏6条经典路线311天全涵盖',
            'slug': 'tibet-6-classic-routes',
            'cat': 'routes', 'catLabel': 'Routes', 'catLabelZh': '路线',
            'date': 'Mar 1, 2026', 'time': '9 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '旅游西藏6条经典路线，3-11天全涵盖！',
            'titleEn': '6 Classic Tibet Routes, From 3 to 11 Days — All Covered!',
            'excerptZh': '从拉萨环线到阿里大北线，6条经典西藏路线覆盖3-11天行程，满足不同时间和预算需求。',
            'excerptEn': 'From Lhasa loop to Ali northern route, 6 classic Tibet itineraries spanning 3-11 days.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '秘境改则在羌塘腹地聆听红与蓝的交响',
            'slug': 'gerze-changtang-red-blue',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Apr 15, 2026', 'time': '6 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
            'titleZh': '秘境改则：在羌塘腹地聆听红与蓝的交响',
            'titleEn': "Secret Gerze: Listening to the Symphony of Red and Blue in Changtang's Heart",
            'excerptZh': '深入羌塘腹地，在改则县感受红土达坂的赤红与扎日南木错的湛蓝交织出的自然交响。',
            'excerptEn': 'Deep into the Changtang heartland, experience the natural symphony where red earth passes meet sapphire lakes in Gerze.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '收藏6条游线更新你的西藏旅行清单',
            'slug': '6-routes-update-tibet-list',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Mar 20, 2026', 'time': '7 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '收藏！6条游线更新你的西藏旅行清单',
            'titleEn': 'Bookmark These! 6 Routes to Refresh Your Tibet Travel List',
            'excerptZh': '6条精选西藏游线，从经典到小众，从人文到自然，全面升级你的西藏旅行清单。',
            'excerptEn': '6 curated Tibet routes, from classic to offbeat, from cultural to natural — a complete upgrade for your travel list.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '所有人阿里全年出游攻略请查收',
            'slug': 'ali-year-round-travel-guide',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Mar 25, 2026', 'time': '8 min read', 'authorZh': '阿里文旅', 'authorEn': 'Ali Cultural Tourism',
            'titleZh': '所有人，阿里全年出游攻略请查收！',
            'titleEn': "Everyone, Here's Your Year-Round Ali Travel Guide!",
            'excerptZh': '阿里四季皆美——春赏花、夏观湖、秋探土林、冬览蓝冰，全年出游攻略一网打尽。',
            'excerptEn': 'Ali is beautiful all year round — spring flowers, summer lakes, autumn earth forests, winter blue ice.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '西藏旅游超全避雷攻略52条血泪总结进藏前必看',
            'slug': 'tibet-52-tips-avoid-pitfalls',
            'cat': 'health', 'catLabel': 'Health & Safety', 'catLabelZh': '健康与安全',
            'date': 'Feb 10, 2026', 'time': '12 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '西藏旅游超全避雷攻略！52条血泪总结，进藏前必看！',
            'titleEn': 'Ultimate Tibet Pitfall Avoidance Guide! 52 Hard-Learned Tips Before You Go',
            'excerptZh': '52条进藏实用避坑指南，从高反预防到购物防骗，从路线规划到住宿选择，让你西藏之旅少走弯路。',
            'excerptEn': '52 practical Tibet tips, from altitude prevention to shopping scams, route planning to accommodation.',
            'has_en_translation': True,
        },
        {
            'file_pattern': '在他的镜头里看见人与自然相融之美',
            'slug': 'lens-nature-human-harmony',
            'cat': 'photography', 'catLabel': 'Photography', 'catLabelZh': '摄影',
            'date': 'Apr 5, 2026', 'time': '5 min read', 'authorZh': '西藏商报全媒体', 'authorEn': 'Tibet Business Daily',
            'titleZh': '在他的镜头里，看见人与自然相融之美',
            'titleEn': 'Through His Lens: The Beauty of Nature and Humanity in Harmony',
            'excerptZh': '西藏摄影师镜头下的高原生灵与游牧生活——黑颈鹤、藏羚羊、牧民转场，定格人与自然最动人的瞬间。',
            'excerptEn': "Highland wildlife and nomadic life through a Tibetan photographer's lens — black-necked cranes, Tibetan antelopes, herder migrations.",
            'has_en_translation': True,
        },
        # Legacy motorcycle articles without source translations
        {
            'file_pattern': '', 'slug': 'altitude-sickness-tips',
            'cat': 'health', 'catLabel': 'Health & Safety', 'catLabelZh': '健康与安全',
            'date': 'Jan 15, 2026', 'time': '8 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '黄色的狼性 —— 关于摩旅高反需要注意事项',
            'titleEn': 'Altitude Sickness Prevention for Tibet Motorcycle Travel',
            'excerptZh': '摩旅西藏高反预防全攻略，从症状识别到应对措施，助你安全穿越世界屋脊。',
            'excerptEn': 'Altitude sickness prevention guide for Tibet motorcycle travel, from symptom recognition to countermeasures.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'bianba-motorcycle-diary',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Jan 20, 2026', 'time': '10 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '般巴摩旅日记：最后的蓝冰洞',
            'titleEn': 'Bianba Motorcycle Diary: The Last Blue Ice Cave',
            'excerptZh': '一段关于西藏摩旅的真实记录，穿越冰川与荒野，寻找最后的蓝冰洞。',
            'excerptEn': 'A true record of Tibet motorcycle travel, crossing glaciers and wilderness to find the last blue ice cave.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'may-day-tibet-lazy-guide',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Apr 25, 2026', 'time': '6 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '五一游西藏10种懒人玩法舒服',
            'titleEn': '10 Lazy Ways to Enjoy Tibet During May Day Holiday',
            'excerptZh': '不想折腾？五一西藏懒人玩法，舒服又省心，照样玩转高原。',
            'excerptEn': 'Too lazy for hardcore travel? Here are 10 comfortable ways to enjoy Tibet during the May Day holiday.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'motorcycle-healing-journey',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Feb 5, 2026', 'time': '9 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '走，我们骑摩托疗愈去',
            'titleEn': 'Born to Roam | A Motorcycle Healing Journey',
            'excerptZh': '骑上摩托车，穿越西藏的雪山与草原，在风与自由中寻找内心的疗愈。',
            'excerptEn': 'Hop on a motorcycle, cross the snowy mountains and grasslands of Tibet, find inner healing in wind and freedom.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'motorcycle-tibet-gear-guide',
            'cat': 'gear', 'catLabel': 'Gear', 'catLabelZh': '装备',
            'date': 'Feb 12, 2026', 'time': '8 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '老铁，您摩旅西藏最重要的装备是啥？！',
            'titleEn': 'Essential Motorcycle Gear for Tibet Travel',
            'excerptZh': '摩旅西藏装备清单，从头盔到骑行服，老司机带你避坑省钱。',
            'excerptEn': 'Motorcycle gear checklist for Tibet travel, from helmets to riding gear — learn from the pros.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'motorcycle-tibet-shannan',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Mar 5, 2026', 'time': '9 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '川藏中线变身记：从前是硬核地狱，如今是踏板天堂！',
            'titleEn': 'Born to Roam | A Motorcycle Journey Deep Into Shannan, Tibet',
            'excerptZh': '深入山南的摩旅日记，从前是硬核地狱路线，如今踏板也能轻松穿越。',
            'excerptEn': 'A motorcycle journey deep into Shannan, Tibet — once a hardcore hell route, now accessible even to scooters.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'qingming-tibet-travel-guide',
            'cat': 'travel-guide', 'catLabel': 'Travel Guide', 'catLabelZh': '旅行指南',
            'date': 'Mar 28, 2026', 'time': '7 min read', 'authorZh': '小卓玛', 'authorEn': 'Xiao Zhuoma',
            'titleZh': '绝美刷屏！清明西藏出游攻略，小众踏青地治愈整个春天',
            'titleEn': "Qingming Tibet Travel Guide: Hidden Spring Getaways That Heal the Soul",
            'excerptZh': '清明假期西藏小众踏青地推荐，避开人潮，在雪山与花海间治愈身心。',
            'excerptEn': 'Hidden spring getaways in Tibet for the Qingming holiday — avoid the crowds and heal among snow mountains and flower fields.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'sichuan-tibet-central-route',
            'cat': 'routes', 'catLabel': 'Routes', 'catLabelZh': '路线',
            'date': 'Feb 25, 2026', 'time': '11 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '川藏中线变身记：从前是硬核地狱，如今是踏板天堂！',
            'titleEn': 'Sichuan-Tibet Central Route Transformation: From Hardcore Hell to Scooter Heaven',
            'excerptZh': '川藏中线最新路况与攻略，从前只有硬派越野敢走，如今踏板也能轻松穿越。',
            'excerptEn': 'Latest guide to the Sichuan-Tibet Central Route — once only for hardcore off-roaders, now accessible to scooters.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'spring-economy-tibet-tourism',
            'cat': 'news', 'catLabel': 'News', 'catLabelZh': '资讯',
            'date': 'Apr 2, 2026', 'time': '4 min read', 'authorZh': '西藏商报', 'authorEn': 'Tibet Business Daily',
            'titleZh': '春日经济激发西藏文旅消费市场活力',
            'titleEn': 'Spring Economy Boosts Tibet Tourism and Cultural Consumption',
            'excerptZh': '春日经济带动西藏文旅消费，赏花游、文化体验成热门。',
            'excerptEn': 'Spring economy drives Tibet tourism and cultural consumption, with flower viewing and cultural experiences trending.',
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'spring-snow-peach-blossoms',
            'cat': 'photography', 'catLabel': 'Photography', 'catLabelZh': '摄影',
            'date': 'Mar 18, 2026', 'time': '5 min read', 'authorZh': '西藏文旅', 'authorEn': 'Tibet Tourism',
            'titleZh': '春染雪域桃花沐雪绘出好钱景',
            'titleEn': 'Spring in Tibet: Peach Blossoms and Snow Paint a Prosperous Picture',
            'excerptZh': '西藏春天的桃花与雪山，绘制出一幅幅令人心动的画卷。',
            'excerptEn': "Tibet's spring peach blossoms and snow mountains paint heart-stirring pictures.",
            'has_en_translation': False,
        },
        {
            'file_pattern': '', 'slug': 'wheels-shackles-tibet',
            'cat': 'travelogue', 'catLabel': 'Travelogue', 'catLabelZh': '游记',
            'date': 'Jan 30, 2026', 'time': '10 min read', 'authorZh': '般般', 'authorEn': 'Banban',
            'titleZh': '车轮上的枷锁：西藏生存寓言与现代社会的碰撞',
            'titleEn': 'Wheels and Shackles: A Motorcycle Journey Across Tibet',
            'excerptZh': '一场关于自由与束缚的西藏摩旅，车轮滚滚中思考现代社会的精神困境。',
            'excerptEn': 'A motorcycle journey across Tibet about freedom and constraints, pondering modern spiritual dilemmas on the road.',
            'has_en_translation': False,
        },
    ]


def load_articles() -> list[dict]:
    """Load article metadata from config file or fallback dict."""
    for path in CONFIG_PATHS:
        if not os.path.exists(path):
            continue
        if path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('articles', data)
        # TODO: add yaml support when PyYAML available
    return _fallback_meta()


def get_article_by_slug(articles: list[dict], slug: str) -> Optional[dict]:
    for art in articles:
        if art.get('slug') == slug:
            return art
    return None


def build_file_map(articles: list[dict]) -> dict[str, str]:
    """Build slug -> source file prefix mapping for articles with translations."""
    return {
        a['slug']: a['file_pattern']
        for a in articles
        if a.get('file_pattern') and a.get('has_en_translation')
    }


def build_title_map(articles: list[dict]) -> dict[str, str]:
    """Build slug -> English title mapping."""
    return {a['slug']: a['titleEn'] for a in articles}
