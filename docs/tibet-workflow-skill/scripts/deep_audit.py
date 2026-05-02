"""
Bilingual consistency audit for all article files.
Refactored to use shared validators library.
Fixes: title extraction now uses safe stack-based parsing instead of fragile regex.

Usage:
    python scripts/deep_audit.py
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

sys.path.insert(0, _SCRIPT_DIR)
from lib import validators, atomic_io


def main():
    articles_dir = os.path.join(_SKILL_DIR, 'articles')
    results = validators.audit_all_articles(articles_dir)
    out_path = os.path.join(_SKILL_DIR, 'scripts', 'deep_audit_results.txt')

    lines = []
    if not results:
        lines.append("No issues found in any files.\n")
    else:
        for fn, issues in results.items():
            lines.append(f"\n=== {fn} ===\n")
            for issue in issues:
                lines.append(f"  - {issue}\n")

    atomic_io.atomic_write(out_path, ''.join(lines))

    print(f"Audit complete. Results in {out_path}")
    print(f"Files with issues: {len(results)}")
    for fn in results:
        print(f"  - {fn}")

    if results:
        sys.exit(1)


if __name__ == '__main__':
    main()
