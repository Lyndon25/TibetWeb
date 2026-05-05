#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate tour product pages from config/tours.yaml.

Usage:
    python scripts/generate_tours.py [--output-dir tours]
"""
import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def _load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _icon_svg(name: str) -> str:
    """Return a simple inline SVG icon by name."""
    icons = {
        'landmark': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l8-4 8 4v14"/><path d="M9 21v-6h6v6"/></svg>',
        'walking': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 4v6m0 0l4 4m-4-4l-4 4"/><circle cx="12" cy="2" r="1"/><path d="M7 21l3-4 1 3h4l1-3 3 4"/></svg>',
        'leaf': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.6C12.5 4.7 16 4 19 6c-2.8 2-4 5-2.2 8.5A7 7 0 0 1 11 20z"/><path d="M11 20v-9"/></svg>',
        'utensils': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 2v20"/><path d="M15 15a3 3 0 0 0 3-3V2"/></svg>',
        'file-check': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15l2 2 4-4"/></svg>',
        'water': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.74 5.87a8 8 0 1 1-11.48 0L12 2.69z"/></svg>',
        'temple': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M12 3v18"/></svg>',
        'mountain': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3l4 8 5-5 5 15H2L8 3z"/></svg>',
        'sun': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M4.93 4.93l1.41 1.41"/><path d="M17.66 17.66l1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M4.93 19.07l1.41-1.41"/><path d="M17.66 6.34l1.41-1.41"/></svg>',
        'users': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        'hiking': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 4v6m0 0l4 4m-4-4l-4 4"/><circle cx="12" cy="2" r="1"/><path d="M7 21l3-4 1 3h4l1-3 3 4"/></svg>',
        'paw': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 10c-1.5 0-2.5.5-3 1.5-.5 1-1 3-1 4.5 0 1.5.5 2.5 2 3 1.5.5 3-.5 4-2s1.5-3 1-4.5c-.5-1.5-2-2.5-4-2.5z"/><path d="M7 9c-1 0-2 .5-2.5 1.5S4 12 4 13s.5 2 1.5 2.5 2.5.5 3.5-.5 1.5-2.5 1-3.5-1.5-2-3-2z"/><path d="M17 9c1 0 2 .5 2.5 1.5S20 12 20 13s-.5 2-1.5 2.5-2.5.5-3.5-.5-1.5-2.5-1-3.5 1.5-2 3-2z"/><path d="M12 2c-1 0-2 .5-2.5 1.5S9 5 9 6s.5 2 1.5 2.5 2.5.5 3.5-.5 1.5-2.5 1-3.5S13 2 12 2z"/></svg>',
        'ruins': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l8-4 8 4v14"/><path d="M9 21v-6h6v6"/></svg>',
        'car': '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 16H9m10 0h3v-3.15a1 1 0 0 0-.84-.99L16 11l-2.7-3.6a1 1 0 0 0-.8-.4H5.24a2 2 0 0 0-1.8 1.1l-.8 1.63A6 6 0 0 0 2 12.42V16h2"/><circle cx="6.5" cy="16.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/></svg>',
    }
    return icons.get(name, icons['landmark'])


def _render_itinerary(itinerary: list[dict]) -> str:
    """Render itinerary days as HTML."""
    rows = []
    for item in itinerary:
        day = item.get('day', '')
        title = item.get('title', '')
        title_zh = item.get('titleZh', '')
        desc = item.get('desc', '')
        desc_zh = item.get('descZh', '')
        meals = ', '.join(item.get('meals', []))
        meals_zh = ', '.join(item.get('mealsZh', []))
        acc = item.get('accommodation', '')
        acc_zh = item.get('accommodationZh', '')

        rows.append(f'''
    <div class="itinerary-day">
      <div class="itinerary-day__header">
        <span class="itinerary-day__badge">Day {day}</span>
        <h3 class="itinerary-day__title" data-lang-zh="{title_zh}" data-lang-en="{title}">{title}</h3>
      </div>
      <p class="itinerary-day__desc" data-lang-zh="{desc_zh}" data-lang-en="{desc}">{desc}</p>
      <div class="itinerary-day__meta">
        <span data-lang-zh="&#127860; {meals_zh}" data-lang-en="&#127860; {meals}">&#127860; {meals}</span>
        <span data-lang-zh="&#127976; {acc_zh}" data-lang-en="&#127976; {acc}">&#127976; {acc}</span>
      </div>
    </div>''')
    return '\n'.join(rows)


def _render_highlights(highlights: list[dict]) -> str:
    """Render highlight items as HTML."""
    items = []
    for h in highlights:
        text = h.get('text', '')
        text_zh = h.get('textZh', '')
        icon = h.get('icon', 'landmark')
        svg = _icon_svg(icon)
        items.append(f'''
        <div class="highlight-item">
          <div class="highlight-item__icon">{svg}</div>
          <span data-lang-zh="{text_zh}" data-lang-en="{text}">{text}</span>
        </div>''')
    return '\n'.join(items)


def _render_list(items: list[str], items_zh: list[str] | None = None) -> str:
    """Render a bullet list with bilingual support."""
    li = []
    for i, en in enumerate(items):
        zh = items_zh[i] if items_zh and i < len(items_zh) else en
        li.append(f'        <li data-lang-zh="{zh}" data-lang-en="{en}">{en}</li>')
    return '\n'.join(li)


def _render_pricing(pricing: list[dict]) -> str:
    """Render pricing table rows."""
    rows = []
    for p in pricing:
        t = p.get('travelers', '')
        price = p.get('pricePerPerson', '')
        rows.append(f'''
          <tr>
            <td>{t} travelers</td>
            <td><strong>${price}</strong> / person</td>
          </tr>''')
    return '\n'.join(rows)


def _render_faq(faq: list[dict]) -> str:
    """Render FAQ items."""
    items = []
    for f in faq:
        q = f.get('q', '')
        a = f.get('a', '')
        q_zh = f.get('qZh', '')
        a_zh = f.get('aZh', '')
        items.append(f'''
      <details class="faq-item">
        <summary data-lang-zh="{q_zh}" data-lang-en="{q}">{q}</summary>
        <p data-lang-zh="{a_zh}" data-lang-en="{a}">{a}</p>
      </details>''')
    return '\n'.join(items)


def _render_json_ld(tour: dict) -> str:
    """Render Schema.org Product JSON-LD."""
    name = tour.get('name', '')
    desc = tour.get('metaDescription', tour.get('overview', ''))
    price = tour.get('startingPrice', '')
    currency = tour.get('currency', 'USD')
    image = tour.get('coverImage', '')
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{name}",
  "description": "{desc}",
  "image": "{image}",
  "offers": {{
    "@type": "Offer",
    "price": "{price}",
    "priceCurrency": "{currency}",
    "availability": "https://schema.org/InStock"
  }}
}}
</script>'''


def generate_tour_page(tour: dict) -> str:
    """Generate a single tour detail page HTML."""
    slug = tour.get('slug', '')
    name = tour.get('name', '')
    name_zh = tour.get('nameZh', '')
    duration = tour.get('duration', '')
    starting_price = tour.get('startingPrice', '')
    currency = tour.get('currency', 'USD')
    max_group = tour.get('maxGroupSize', '')
    difficulty = tour.get('difficulty', '')
    difficulty_zh = tour.get('difficultyZh', '')
    best_season = tour.get('bestSeason', '')
    best_season_zh = tour.get('bestSeasonZh', '')
    cover = tour.get('coverImage', '')
    cover_alt = tour.get('coverImageAlt', '')
    overview = tour.get('overview', '')
    overview_zh = tour.get('overviewZh', '')
    itinerary = tour.get('itinerary', [])
    highlights = tour.get('highlights', [])
    inclusions = tour.get('inclusions', [])
    inclusions_zh = tour.get('inclusionsZh', None)
    exclusions = tour.get('exclusions', [])
    exclusions_zh = tour.get('exclusionsZh', None)
    pricing = tour.get('pricing', [])
    faq = tour.get('faq', [])
    meta_title = tour.get('metaTitle', f"{name} | TibetRide")
    meta_desc = tour.get('metaDescription', overview[:160])

    itinerary_html = _render_itinerary(itinerary)
    highlights_html = _render_highlights(highlights)
    inclusions_html = _render_list(inclusions, inclusions_zh)
    exclusions_html = _render_list(exclusions, exclusions_zh)
    pricing_html = _render_pricing(pricing)
    faq_html = _render_faq(faq)
    json_ld = _render_json_ld(tour)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{meta_desc}">
  <title>{meta_title}</title>
  <link rel="stylesheet" href="../css/main.css">
  <link rel="stylesheet" href="../css/lang.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
  <script>
    (function(){{
      var k='site-lang',l=localStorage.getItem(k);
      if(l==='en'){{document.documentElement.setAttribute('lang','en');}}
      else{{document.documentElement.setAttribute('lang','zh-CN');}}
    }})();
  </script>
  <style>
    /* ===== Tour Page Styles ===== */
    .tour-hero {{
      position: relative;
      height: 70vh;
      min-height: 480px;
      max-height: 640px;
      display: flex;
      align-items: flex-end;
      overflow: hidden;
    }}
    .tour-hero__bg {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .tour-hero__overlay {{
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.65) 100%);
    }}
    .tour-hero__content {{
      position: relative;
      z-index: 1;
      max-width: var(--max-width);
      width: 100%;
      margin: 0 auto;
      padding: 3rem 1.5rem;
      color: #fff;
    }}
    .tour-hero__meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1rem;
      font-size: 0.85rem;
      opacity: 0.9;
    }}
    .tour-hero__meta span {{
      background: rgba(255,255,255,0.15);
      backdrop-filter: blur(8px);
      padding: 0.25rem 0.75rem;
      border-radius: 100px;
    }}
    .tour-hero__title {{
      font-size: clamp(2rem, 1.5rem + 3vw, 3.5rem);
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 1rem;
      max-width: 720px;
    }}
    .tour-hero__price {{
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 1.25rem;
    }}
    .tour-hero__price small {{
      font-size: 0.9rem;
      font-weight: 400;
      opacity: 0.8;
    }}
    .tour-hero__actions {{
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    /* ===== Highlights ===== */
    .highlights {{
      background: var(--color-earth-light);
      padding: 3rem 0;
    }}
    .highlights__grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.5rem;
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 0 1.5rem;
    }}
    .highlight-item {{
      display: flex;
      align-items: center;
      gap: 0.875rem;
      background: #fff;
      padding: 1.25rem;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-sm);
      font-size: 0.95rem;
      font-weight: 500;
    }}
    .highlight-item__icon {{
      color: var(--color-primary);
      flex-shrink: 0;
    }}

    /* ===== Itinerary ===== */
    .itinerary {{
      padding: 4rem 0;
      max-width: var(--max-width-narrow);
      margin: 0 auto;
    }}
    .itinerary__title {{
      text-align: center;
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 2.5rem;
    }}
    .itinerary-day {{
      background: #fff;
      border: 1px solid var(--color-earth);
      border-radius: var(--radius-md);
      padding: 1.5rem;
      margin-bottom: 1rem;
    }}
    .itinerary-day__header {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }}
    .itinerary-day__badge {{
      background: var(--color-primary);
      color: #fff;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.3rem 0.7rem;
      border-radius: 100px;
    }}
    .itinerary-day__title {{
      font-size: 1.15rem;
      font-weight: 600;
      margin: 0;
    }}
    .itinerary-day__desc {{
      color: var(--color-text-muted);
      margin-bottom: 0.75rem;
      line-height: 1.6;
    }}
    .itinerary-day__meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      font-size: 0.85rem;
      color: var(--color-text-light);
    }}

    /* ===== Inclusions / Exclusions ===== */
    .inclusions {{
      background: var(--color-secondary-light);
      padding: 3rem 0;
    }}
    .inclusions__grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 2.5rem;
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 0 1.5rem;
    }}
    .inclusions__block h3 {{
      font-size: 1.25rem;
      margin-bottom: 1rem;
      color: var(--color-secondary);
    }}
    .inclusions__block ul {{
      list-style: disc;
      padding-left: 1.25rem;
    }}
    .inclusions__block li {{
      margin-bottom: 0.5rem;
      color: var(--color-text-muted);
    }}

    /* ===== Pricing ===== */
    .pricing {{
      padding: 3rem 0;
      max-width: var(--max-width-narrow);
      margin: 0 auto;
      text-align: center;
    }}
    .pricing__title {{
      font-size: 1.75rem;
      margin-bottom: 0.5rem;
    }}
    .pricing__note {{
      color: var(--color-text-light);
      margin-bottom: 1.5rem;
    }}
    .pricing__table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 1.5rem;
    }}
    .pricing__table th, .pricing__table td {{
      padding: 1rem;
      border-bottom: 1px solid var(--color-earth);
    }}
    .pricing__table th {{
      background: var(--color-earth-light);
      font-weight: 600;
      text-align: left;
    }}
    .pricing__table td {{
      text-align: left;
    }}
    .pricing__table tr:last-child td {{
      border-bottom: none;
    }}

    /* ===== FAQ ===== */
    .faq {{
      padding: 3rem 0;
      max-width: var(--max-width-narrow);
      margin: 0 auto;
    }}
    .faq__title {{
      font-size: 1.75rem;
      text-align: center;
      margin-bottom: 2rem;
    }}
    .faq-item {{
      background: #fff;
      border: 1px solid var(--color-earth);
      border-radius: var(--radius-md);
      margin-bottom: 0.75rem;
      overflow: hidden;
    }}
    .faq-item summary {{
      padding: 1.25rem;
      font-weight: 600;
      cursor: pointer;
      list-style: none;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .faq-item summary::after {{
      content: '+';
      font-size: 1.25rem;
      color: var(--color-primary);
    }}
    .faq-item[open] summary::after {{
      content: '-';
    }}
    .faq-item p {{
      padding: 0 1.25rem 1.25rem;
      color: var(--color-text-muted);
      line-height: 1.6;
    }}

    /* ===== CTA Section ===== */
    .tour-cta {{
      background: var(--color-primary);
      color: #fff;
      text-align: center;
      padding: 4rem 1.5rem;
    }}
    .tour-cta__title {{
      font-size: 1.75rem;
      margin-bottom: 0.75rem;
    }}
    .tour-cta__desc {{
      opacity: 0.9;
      margin-bottom: 1.5rem;
      max-width: 480px;
      margin-left: auto;
      margin-right: auto;
    }}
  </style>
  {json_ld}
</head>
<body>

<!-- Navigation -->
<nav class="nav nav--scrolled">
  <div class="nav__inner">
    <a href="../index.html" class="nav__logo" style="color: var(--color-text);">
      <span class="nav__logo-icon">&#x1F3CD;</span>
      <span class="lang-content lang-content--inline" data-lang="zh">TibetRide</span>
      <span class="lang-content lang-content--inline" data-lang="en">TibetRide</span>
    </a>
    <ul class="nav__links">
      <li><a href="../index.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="首页" data-lang-en="Home">Home</a></li>
      <li><a href="index.html" class="nav__link nav__link--active" data-lang-zh="线路" data-lang-en="Tours">Tours</a></li>
      <li><a href="../guides/index.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="攻略" data-lang-en="Guide">Guide</a></li>
      <li><a href="../about.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="关于" data-lang-en="About">About</a></li>
      <li><a href="../contact.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="联系" data-lang-en="Contact">Contact</a></li>
    </ul>
    <button class="nav__toggle" aria-label="Toggle menu">
      <span style="background: var(--color-text);"></span>
      <span style="background: var(--color-text);"></span>
      <span style="background: var(--color-text);"></span>
    </button>
  </div>
</nav>

<!-- Hero -->
<section class="tour-hero">
  <img class="tour-hero__bg" src="{cover}" alt="{cover_alt}" loading="eager">
  <div class="tour-hero__overlay"></div>
  <div class="tour-hero__content">
    <div class="tour-hero__meta">
      <span data-lang-zh="&#128337; {duration}天" data-lang-en="&#128337; {duration} Days">&#128337; {duration} Days</span>
      <span data-lang-zh="&#128101; 最多{max_group}人" data-lang-en="&#128101; Max {max_group}">&#128101; Max {max_group}</span>
      <span data-lang-zh="&#127757; {best_season_zh}" data-lang-en="&#127757; {best_season}">&#127757; {best_season}</span>
      <span data-lang-zh="&#128170; {difficulty_zh}" data-lang-en="&#128170; {difficulty}">&#128170; {difficulty}</span>
    </div>
    <h1 class="tour-hero__title" data-lang-zh="{name_zh}" data-lang-en="{name}">{name}</h1>
    <div class="tour-hero__price">
      <span data-lang-zh="起价" data-lang-en="From">From</span> {currency} {starting_price} <small data-lang-zh="每人" data-lang-en="per person">per person</small>
    </div>
    <div class="tour-hero__actions">
      <a href="../customize.html?tour={slug}" class="btn btn--primary btn--lg" data-lang-zh="获取报价" data-lang-en="Get Free Quote">Get Free Quote</a>
      <a href="https://wa.me/?text=Hi%20TibetRide%2C%20I%20am%20interested%20in%20the%20{name.replace(' ', '%20')}" class="btn btn--outline btn--lg" target="_blank" rel="noopener" data-lang-zh="WhatsApp咨询" data-lang-en="Chat on WhatsApp">Chat on WhatsApp</a>
    </div>
  </div>
</section>

<!-- Overview -->
<section class="section">
  <div class="container container--narrow">
    <h2 class="section-title" data-lang-zh="行程概览" data-lang-en="Tour Overview">Tour Overview</h2>
    <p data-lang-zh="{overview_zh}" data-lang-en="{overview}">{overview}</p>
  </div>
</section>

<!-- Highlights -->
<section class="highlights">
  <div class="highlights__grid">
{highlights_html}
  </div>
</section>

<!-- Itinerary -->
<section class="itinerary">
  <h2 class="itinerary__title" data-lang-zh="每日行程" data-lang-en="Daily Itinerary">Daily Itinerary</h2>
{itinerary_html}
</section>

<!-- Inclusions & Exclusions -->
<section class="inclusions">
  <div class="inclusions__grid">
    <div class="inclusions__block">
      <h3 data-lang-zh="费用包含" data-lang-en="What's Included">What's Included</h3>
      <ul>
{inclusions_html}
      </ul>
    </div>
    <div class="inclusions__block">
      <h3 data-lang-zh="费用不含" data-lang-en="Not Included">Not Included</h3>
      <ul>
{exclusions_html}
      </ul>
    </div>
  </div>
</section>

<!-- Pricing -->
<section class="pricing">
  <h2 class="pricing__title" data-lang-zh="价格表" data-lang-en="Pricing">Pricing</h2>
  <p class="pricing__note" data-lang-zh="人数越多，人均价格越低" data-lang-en="Price per person decreases as group size increases">Price per person decreases as group size increases</p>
  <table class="pricing__table">
    <thead>
      <tr>
        <th data-lang-zh="人数" data-lang-en="Group Size">Group Size</th>
        <th data-lang-zh="人均价格" data-lang-en="Price Per Person">Price Per Person</th>
      </tr>
    </thead>
    <tbody>
{pricing_html}
    </tbody>
  </table>
</section>

<!-- FAQ -->
<section class="faq">
  <h2 class="faq__title" data-lang-zh="常见问题" data-lang-en="Frequently Asked Questions">Frequently Asked Questions</h2>
{faq_html}
</section>

<!-- CTA -->
<section class="tour-cta">
  <h2 class="tour-cta__title" data-lang-zh="准备好出发了吗？" data-lang-en="Ready to Book?">Ready to Book?</h2>
  <p class="tour-cta__desc" data-lang-zh="告诉我们您的旅行计划，我们将在24小时内回复。" data-lang-en="Tell us your travel plans and we will get back to you within 24 hours.">Tell us your travel plans and we will get back to you within 24 hours.</p>
  <a href="../customize.html?tour={slug}" class="btn btn--light btn--lg" data-lang-zh="获取免费报价" data-lang-en="Get Free Quote">Get Free Quote</a>
</section>

<!-- Footer -->
<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div>
        <div class="footer__brand">TibetRide</div>
        <p class="footer__desc" data-lang-zh="探索西藏，与本地专家同行。" data-lang-en="Explore Tibet with local experts.">Explore Tibet with local experts.</p>
      </div>
      <div>
        <div class="footer__heading" data-lang-zh="探索" data-lang-en="Explore">Explore</div>
        <ul class="footer__links">
          <li><a href="index.html" data-lang-zh="线路" data-lang-en="Tours">Tours</a></li>
          <li><a href="../guides/index.html" data-lang-zh="攻略" data-lang-en="Travel Guide">Travel Guide</a></li>
          <li><a href="../articles/index.html" data-lang-zh="故事" data-lang-en="Stories">Stories</a></li>
        </ul>
      </div>
      <div>
        <div class="footer__heading" data-lang-zh="公司" data-lang-en="Company">Company</div>
        <ul class="footer__links">
          <li><a href="../about.html" data-lang-zh="关于我们" data-lang-en="About Us">About Us</a></li>
          <li><a href="../contact.html" data-lang-zh="联系我们" data-lang-en="Contact">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <p>&copy; 2026 TibetRide.com. All rights reserved.</p>
    </div>
  </div>
</footer>

<script src="../js/lang.js"></script>
<script src="../js/main.js"></script>
</body>
</html>'''


def generate_tours_index(tours: list[dict]) -> str:
    """Generate the tours listing page."""
    cards = []
    for tour in tours:
        slug = tour.get('slug', '')
        name = tour.get('name', '')
        name_zh = tour.get('nameZh', '')
        duration = tour.get('duration', '')
        price = tour.get('startingPrice', '')
        currency = tour.get('currency', 'USD')
        cover = tour.get('coverImage', '')
        cover_alt = tour.get('coverImageAlt', '')
        difficulty = tour.get('difficulty', '')
        difficulty_zh = tour.get('difficultyZh', '')
        best = tour.get('bestSeason', '')
        best_zh = tour.get('bestSeasonZh', '')
        overview = tour.get('overview', '')[:140] + '...'
        overview_zh = tour.get('overviewZh', '')[:100] + '...'

        cards.append(f'''
      <article class="tour-card animate">
        <a href="{slug}.html" class="tour-card__image-wrap">
          <img class="tour-card__image" src="{cover}" alt="{cover_alt}" loading="lazy">
        </a>
        <div class="tour-card__body">
          <div class="tour-card__meta">
            <span>&#128337; {duration} Days</span>
            <span>&#128170; {difficulty}</span>
            <span>&#127757; {best}</span>
          </div>
          <h3 class="tour-card__title"><a href="{slug}.html" data-lang-zh="{name_zh}" data-lang-en="{name}">{name}</a></h3>
          <p class="tour-card__desc" data-lang-zh="{overview_zh}" data-lang-en="{overview}">{overview}</p>
          <div class="tour-card__footer">
            <span class="tour-card__price">From {currency} {price}</span>
            <a href="{slug}.html" class="btn btn--primary" data-lang-zh="查看详情" data-lang-en="View Details">View Details</a>
          </div>
        </div>
      </article>''')

    cards_html = '\n'.join(cards)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Small group Tibet tours with local experts. From Lhasa to Everest and Kailash, all permits included.">
  <title data-lang-zh="线路 - TibetRide" data-lang-en="Tibet Tours | TibetRide">Tibet Tours | TibetRide</title>
  <link rel="stylesheet" href="../css/main.css">
  <link rel="stylesheet" href="../css/lang.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
  <script>
    (function(){{
      var k='site-lang',l=localStorage.getItem(k);
      if(l==='en'){{document.documentElement.setAttribute('lang','en');}}
      else{{document.documentElement.setAttribute('lang','zh-CN');}}
    }})();
  </script>
  <style>
    .tours-hero {{
      background: linear-gradient(135deg, #1c1917 0%, #292524 50%, #44403c 100%);
      color: #fff;
      text-align: center;
      padding: 6rem 1.5rem 4rem;
    }}
    .tours-hero__title {{
      font-size: clamp(2rem, 1.5rem + 3vw, 3rem);
      font-weight: 800;
      margin-bottom: 0.75rem;
    }}
    .tours-hero__desc {{
      opacity: 0.85;
      max-width: 560px;
      margin: 0 auto;
    }}
    .tours-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 2rem;
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 3rem 1.5rem;
    }}
    .tour-card {{
      background: #fff;
      border-radius: var(--radius-lg);
      overflow: hidden;
      box-shadow: var(--shadow-md);
      transition: transform var(--transition-base), box-shadow var(--transition-base);
    }}
    .tour-card:hover {{
      transform: translateY(-6px);
      box-shadow: var(--shadow-xl);
    }}
    .tour-card__image-wrap {{
      display: block;
      aspect-ratio: 16 / 10;
      overflow: hidden;
    }}
    .tour-card__image {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.6s ease;
    }}
    .tour-card:hover .tour-card__image {{
      transform: scale(1.04);
    }}
    .tour-card__body {{
      padding: 1.5rem;
    }}
    .tour-card__meta {{
      display: flex;
      gap: 0.75rem;
      font-size: 0.8rem;
      color: var(--color-text-light);
      margin-bottom: 0.75rem;
    }}
    .tour-card__title {{
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      line-height: 1.3;
    }}
    .tour-card__title a:hover {{
      color: var(--color-primary);
    }}
    .tour-card__desc {{
      color: var(--color-text-muted);
      font-size: 0.9rem;
      line-height: 1.6;
      margin-bottom: 1rem;
    }}
    .tour-card__footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .tour-card__price {{
      font-weight: 700;
      color: var(--color-primary);
      font-size: 1.1rem;
    }}
  </style>
</head>
<body>

<nav class="nav nav--scrolled">
  <div class="nav__inner">
    <a href="../index.html" class="nav__logo" style="color: var(--color-text);">
      <span class="nav__logo-icon">&#x1F3CD;</span> TibetRide
    </a>
    <ul class="nav__links">
      <li><a href="../index.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="首页" data-lang-en="Home">Home</a></li>
      <li><a href="index.html" class="nav__link nav__link--active" data-lang-zh="线路" data-lang-en="Tours">Tours</a></li>
      <li><a href="../guides/index.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="攻略" data-lang-en="Guide">Guide</a></li>
      <li><a href="../about.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="关于" data-lang-en="About">About</a></li>
      <li><a href="../contact.html" class="nav__link" style="color: var(--color-text-muted);" data-lang-zh="联系" data-lang-en="Contact">Contact</a></li>
    </ul>
    <button class="nav__toggle" aria-label="Toggle menu">
      <span style="background: var(--color-text);"></span>
      <span style="background: var(--color-text);"></span>
      <span style="background: var(--color-text);"></span>
    </button>
  </div>
</nav>

<header class="tours-hero">
  <h1 class="tours-hero__title" data-lang-zh="精选西藏线路" data-lang-en="Curated Tibet Tours">Curated Tibet Tours</h1>
  <p class="tours-hero__desc" data-lang-zh="小团出行，本地专家带队，全程代办入藏函。" data-lang-en="Small groups, local expert guides, all permits handled.">Small groups, local expert guides, all permits handled.</p>
</header>

<main class="tours-grid">
{cards_html}
</main>

<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div>
        <div class="footer__brand">TibetRide</div>
        <p class="footer__desc" data-lang-zh="探索西藏，与本地专家同行。" data-lang-en="Explore Tibet with local experts.">Explore Tibet with local experts.</p>
      </div>
      <div>
        <div class="footer__heading" data-lang-zh="探索" data-lang-en="Explore">Explore</div>
        <ul class="footer__links">
          <li><a href="index.html">Tours</a></li>
          <li><a href="../guides/index.html">Travel Guide</a></li>
          <li><a href="../articles/index.html">Stories</a></li>
        </ul>
      </div>
      <div>
        <div class="footer__heading">Company</div>
        <ul class="footer__links">
          <li><a href="../about.html">About Us</a></li>
          <li><a href="../contact.html">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <p>&copy; 2026 TibetRide.com. All rights reserved.</p>
    </div>
  </div>
</footer>

<script src="../js/lang.js"></script>
<script src="../js/main.js"></script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description='Generate tour pages from config/tours.yaml')
    parser.add_argument('--output-dir', default='tours', help='Output directory for generated pages')
    parser.add_argument('--config', default='config/tours.yaml', help='Path to tours YAML config')
    args = parser.parse_args()

    config_path = os.path.join(_PROJECT_ROOT, args.config)
    output_dir = os.path.join(_PROJECT_ROOT, args.output_dir)

    if not os.path.exists(config_path):
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)

    data = _load_config(config_path)
    tours = data.get('tours', [])

    if not tours:
        print("[WARN] No tours found in config.")
        sys.exit(0)

    os.makedirs(output_dir, exist_ok=True)

    # Generate individual tour pages
    for tour in tours:
        slug = tour.get('slug', '')
        if not slug:
            print("[WARN] Tour missing slug, skipping.")
            continue
        html = generate_tour_page(tour)
        out_path = os.path.join(output_dir, f"{slug}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[OK] Generated {out_path}")

    # Generate tours index page
    index_html = generate_tours_index(tours)
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"[OK] Generated {index_path}")

    print(f"\n[DONE] {len(tours)} tour(s) generated in {output_dir}/")


if __name__ == '__main__':
    main()
