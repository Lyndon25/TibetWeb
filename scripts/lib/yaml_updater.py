"""YAML config updater for articles.yaml."""
import os
import re
import yaml as _yaml


def slug_exists(config_path: str, slug: str) -> bool:
    if not os.path.exists(config_path):
        return False
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = _yaml.safe_load(f) or {}
        articles = data.get('articles', [])
        return any(a.get('slug') == slug for a in articles)
    except Exception:
        return False


def add_new_article(config_path: str, article: dict) -> bool:
    try:
        if not os.path.exists(config_path):
            return _write_new_config(config_path, article)

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        data = _yaml.safe_load(content) or {}
        articles = data.get('articles', [])

        if any(a.get('slug') == article.get('slug') for a in articles):
            return True

        articles.append(article)

        # Write back using structured YAML
        data['articles'] = articles
        with open(config_path, 'w', encoding='utf-8') as f:
            _yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False,
                            sort_keys=False, width=120)
        return True
    except Exception:
        import traceback
        traceback.print_exc()
        return False


def _write_new_config(config_path: str, article: dict) -> bool:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    data = {'articles': [article], 'defaults': {}}
    with open(config_path, 'w', encoding='utf-8') as f:
        _yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False,
                        sort_keys=False, width=120)
    return True
