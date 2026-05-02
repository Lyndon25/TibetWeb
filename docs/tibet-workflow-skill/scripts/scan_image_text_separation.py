"""
Scan EN body blocks for image-text separation issues.
Refactored to use shared validators library.

Usage:
    python scripts/scan_image_text_separation.py
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

sys.path.insert(0, _SCRIPT_DIR)
from lib import validators


def main():
    articles_dir = os.path.join(_SKILL_DIR, 'articles')
    issues = validators.check_all_distributions(articles_dir)

    print(f"Found {len(issues)} files with image-text separation issues in EN body:\n")
    for fn, issue in issues.items():
        print(f"  {fn}")
        print(f"    Issue: {issue}")
        print()

    if issues:
        sys.exit(1)


if __name__ == '__main__':
    main()
