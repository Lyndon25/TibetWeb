"""Add Article JSON-LD schema to article pages."""
import os, re, json

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
article_dates = {
    'tibet-trip-cost-2026': '2026-07-14',
    'is-tibet-safe-2026': '2026-07-14',
    'best-time-to-visit-tibet-2026': '2026-07-15',
    'plan-first-tibet-trip-2026': '2026-07-15',
}
author = 'Tenzin'

updated = 0

for dirpath, dirnames, filenames in os.walk(root):
    if any(skip in dirpath for skip in ['AddingArticleWorkSpace', 'templates', '.git', 'node_modules', 'scripts']):
        continue
    if '/articles/' not in dirpath.replace('\\', '/'):
        continue
    for f in filenames:
        if f != 'index.html':
            continue
        filepath = os.path.join(dirpath, f)

        with open(filepath, 'r', encoding='utf-8') as fh:
            content = fh.read()

        # Skip if already has Article JSON-LD
        if '"@type": "Article"' in content:
            continue

        # Skip if no FAQPage (older articles might not have any JSON-LD)
        # Actually, add Article even without FAQPage

        # Extract metadata
        m_title = re.search(r'<title>([^<]+)</title>', content)
        m_desc = re.search(r'<meta name="description" content="([^"]+)"', content)
        m_image = re.search(r'<meta property="og:image" content="([^"]+)"', content)
        m_canonical = re.search(r'<link rel="canonical" href="([^"]+)"', content)

        if not (m_title and m_canonical):
            continue

        headline = m_title.group(1).split('|')[0].strip()
        desc = m_desc.group(1)[:160] if m_desc else headline
        image = m_image.group(1) if m_image else 'https://www.tibetride.com/images/hero/alpine-mountains.webp'
        url = m_canonical.group(1)

        # Determine slug for date lookup
        slug = os.path.basename(os.path.dirname(filepath))
        date_pub = article_dates.get(slug, '2026-01-01')

        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "description": desc,
            "image": image,
            "url": url,
            "datePublished": date_pub,
            "author": {
                "@type": "Person",
                "name": author
            },
            "publisher": {
                "@type": "Organization",
                "name": "TibetRide",
                "url": "https://www.tibetride.com"
            }
        }

        json_str = json.dumps(article_schema, indent=2, ensure_ascii=False)
        article_ld = f'\n  <script type="application/ld+json">\n  {json_str}\n  </script>'

        # Insert after the FAQPage closing </script> tag, or before </head>
        # Find the last </script> before </head>
        head_end = content.index('</head>')
        head_section = content[:head_end]

        # Find last JSON-LD script block
        last_ld_close = head_section.rfind('</script>')
        if last_ld_close == -1:
            # No script blocks, insert before </head>
            insert_pos = head_end
        else:
            # After the last </script>
            insert_pos = last_ld_close + len('</script>')

        new_content = content[:insert_pos] + article_ld + content[insert_pos:]

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(new_content)
            updated += 1
            rel = os.path.relpath(filepath, root)
            print(f'OK: {rel} ({date_pub})')

print(f'\nUpdated: {updated} article pages')
