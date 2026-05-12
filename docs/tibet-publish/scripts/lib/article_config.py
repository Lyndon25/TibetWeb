"""
Centralized article configuration loader.

Reads metadata from a single source of truth (articles.yaml or articles.json).
Falls back to the inline dict if config file missing.
"""
import os
import json
from typing import Optional


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

CONFIG_PATHS = [
    os.path.join(_SKILL_DIR, 'config', 'articles.yaml'),
    os.path.join(_SKILL_DIR, 'config', 'articles.json'),
    os.path.join(_SKILL_DIR, 'scripts', 'articles.json'),
]


def _fallback_meta() -> list[dict]:
    """Fallback inline metadata (compact version for backward compatibility)."""
    # This will be used only if no YAML/JSON config exists
    return []


def _load_yaml(path: str) -> dict:
    """Load YAML without PyYAML dependency using basic parser."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple YAML subset parser for our config structure
    result = {'articles': [], 'defaults': {}}
    current_article: Optional[dict] = None
    current_section = None
    indent_stack = []

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level keys
        if stripped.startswith('articles:') and indent == 0:
            current_section = 'articles'
            i += 1
            continue

        if stripped.startswith('defaults:') and indent == 0:
            current_section = 'defaults'
            i += 1
            continue

        # Article entries (- slug: ...)
        if stripped.startswith('- slug:') and current_section == 'articles':
            if current_article:
                result['articles'].append(current_article)
            slug_val = stripped.split(':', 1)[1].strip().strip('"\'')
            current_article = {'slug': slug_val}
            i += 1
            continue

        # Nested properties
        if current_section == 'articles' and current_article and ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"\'')

            # Handle nested objects (title, author, excerpt)
            if key in ('title', 'author', 'excerpt', 'site_name', 'site_tagline'):
                # Check next lines for zh/en sub-properties
                sub_props = {}
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith('#'):
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= indent:
                        break
                    if ':' in next_stripped:
                        sk, sv = next_stripped.split(':', 1)
                        sk = sk.strip()
                        sv = sv.strip().strip('"\'')
                        sub_props[sk] = sv
                    j += 1
                if sub_props:
                    current_article[key] = sub_props
                else:
                    current_article[key] = val
                i = j
                continue
            elif key == 'related':
                # List of slugs
                related = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith('#'):
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= indent:
                        break
                    if next_stripped.startswith('- '):
                        related.append(next_stripped[2:].strip().strip('"\''))
                    j += 1
                current_article[key] = related
                i = j
                continue
            else:
                if val.lower() in ('true', 'yes'):
                    current_article[key] = True
                elif val.lower() in ('false', 'no'):
                    current_article[key] = False
                else:
                    current_article[key] = val

        # Defaults section
        if current_section == 'defaults' and ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            if key in ('site_name', 'site_tagline'):
                sub_props = {}
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith('#'):
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= indent:
                        break
                    if ':' in next_stripped:
                        sk, sv = next_stripped.split(':', 1)
                        sk = sk.strip()
                        sv = sv.strip().strip('"\'')
                        sub_props[sk] = sv
                    j += 1
                if sub_props:
                    result['defaults'][key] = sub_props
                else:
                    result['defaults'][key] = val
                i = j
                continue
            else:
                if val.lower() in ('true', 'yes'):
                    result['defaults'][key] = True
                elif val.lower() in ('false', 'no'):
                    result['defaults'][key] = False
                else:
                    result['defaults'][key] = val

        i += 1

    if current_article:
        result['articles'].append(current_article)

    return result


def load_articles() -> list[dict]:
    """Load article metadata from config file or fallback dict."""
    for path in CONFIG_PATHS:
        if not os.path.exists(path):
            continue
        if path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('articles', data)
        if path.endswith('.yaml'):
            data = _load_yaml(path)
            return data.get('articles', [])
    return _fallback_meta()


def load_defaults() -> dict:
    """Load site default settings from config."""
    for path in CONFIG_PATHS:
        if not os.path.exists(path):
            continue
        if path.endswith('.json'):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('defaults', {})
        if path.endswith('.yaml'):
            data = _load_yaml(path)
            return data.get('defaults', {})
    return {}


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
    title_map = {}
    for a in articles:
        title = a.get('title')
        if isinstance(title, dict):
            title_map[a['slug']] = title.get('en', '')
        else:
            title_map[a['slug']] = a.get('titleEn', '')
    return title_map


def get_related_articles(article: dict, all_articles: list[dict]) -> list[dict]:
    """Get related article metadata for a given article."""
    related_slugs = article.get('related', [])
    result = []
    seen = set()
    for slug in related_slugs:
        if slug in seen:
            continue
        seen.add(slug)
        art = get_article_by_slug(all_articles, slug)
        if art:
            result.append(art)
    return result
