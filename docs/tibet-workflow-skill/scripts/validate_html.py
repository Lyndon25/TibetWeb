"""
HTML structure validation for all article files.
Refactored to use shared validators library.

Usage:
    python scripts/validate_html.py
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

sys.path.insert(0, _SCRIPT_DIR)
from lib import validators


def main():
    articles_dir = os.path.join(_SKILL_DIR, 'articles')
    errors = validators.validate_all_articles(articles_dir)
    if errors:
        print("HTML VALIDATION FAILED:")
        for fn, err_list in errors.items():
            print(f"  {fn}: {err_list}")
        sys.exit(1)
    else:
        print("All HTML files validated successfully.")


if __name__ == '__main__':
    main()
