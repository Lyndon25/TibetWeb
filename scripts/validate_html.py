"""
HTML structure validation for all article files.
Refactored to use shared validators library.
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

sys.path.insert(0, _SCRIPT_DIR)
from lib import validators, atomic_io


def main():
    articles_dir = os.path.join(_SKILL_DIR, 'articles')
    results = validators.validate_all_articles(articles_dir)
    out_path = os.path.join(_SKILL_DIR, 'scripts', 'validate_html_results.txt')

    lines = []
    if not results:
        lines.append("All HTML files are structurally valid.\n")
    else:
        for fn, errs in results.items():
            lines.append(f"\n=== {fn} ===\n")
            for err in errs:
                lines.append(f"  - {err}\n")

    atomic_io.atomic_write(out_path, ''.join(lines))

    print(f"Validation complete. Results in {out_path}")
    if results:
        print(f"Files with errors: {len(results)}")
        for fn in results:
            print(f"  - {fn}")
        sys.exit(1)
    else:
        print("All OK!")


if __name__ == '__main__':
    main()
