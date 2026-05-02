"""
Unified build entry point for TibetJourneyWebsite content pipeline.

Replaces the previous 7-phase manual workflow with a single command:

    python scripts/build.py [--validate-only] [--audit-only] [--slug <slug>]

Phases:
  1. convert   — Generate articles from WeChat source HTML
  2. rebuild   — Extract EN translations from source files
  3. sync      — Synchronize and distribute images across ZH/EN bodies
  4. validate  — Run HTML + audit + distribution checks

TODO:
  - Jinja2 template support (currently keeps f-string template in convert)
  - Auto-generate articles/index.html from config
  - Incremental builds (only process changed files)
"""
import os
import sys
import argparse

# Ensure lib is on path when run directly
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

from lib import validators, atomic_io


def _run_phase(name: str, module_name: str, func_name: str = 'main', *args) -> bool:
    """Run a build phase module, return True on success."""
    print(f"\n{'='*60}")
    print(f"PHASE: {name}")
    print('='*60)
    try:
        mod = __import__(module_name, fromlist=[func_name])
        fn = getattr(mod, func_name)
        # For modules that use argparse, we can't easily pass args;
        # they should be refactored to expose a callable API.
        # For now, call main() which parses sys.argv.
        fn()
        return True
    except SystemExit as e:
        if e.code != 0:
            print(f"[FAIL] Phase '{name}' exited with code {e.code}")
            return False
        return True
    except Exception as e:
        print(f"[FAIL] Phase '{name}' raised: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='TibetJourneyWebsite unified build')
    parser.add_argument('--convert', action='store_true', help='Run article generation')
    parser.add_argument('--rebuild', action='store_true', help='Run EN content rebuild')
    parser.add_argument('--sync', action='store_true', help='Run image sync')
    parser.add_argument('--validate', action='store_true', help='Run validation only')
    parser.add_argument('--slug', type=str, help='Process only this slug')
    parser.add_argument('--all', action='store_true', help='Run full pipeline')
    args = parser.parse_args()

    if not any([args.convert, args.rebuild, args.sync, args.validate, args.all]):
        parser.print_help()
        sys.exit(1)

    ok = True

    if args.all or args.convert:
        # Pass --slug to convert_articles_v2 if supported
        ok &= _run_phase('Article Generation', 'convert_articles_v2')

    if args.all or args.rebuild:
        ok &= _run_phase('EN Rebuild', 'rebuild_en')

    if args.all or args.sync:
        ok &= _run_phase('Image Sync', 'sync_images')

    if args.all or args.validate:
        print(f"\n{'='*60}")
        print("PHASE: Validation")
        print('='*60)

        articles_dir = os.path.join(_SKILL_DIR, 'articles')

        # Layer 1: HTML
        html_errors = validators.validate_all_articles(articles_dir)
        if html_errors:
            print("[FAIL] HTML validation failed:")
            for fn, errs in html_errors.items():
                print(f"  {fn}: {errs}")
            ok = False
        else:
            print("[PASS] HTML structure OK")

        # Layer 2: Audit
        audit_issues = validators.audit_all_articles(articles_dir)
        if audit_issues:
            print(f"[FAIL] Audit found {len(audit_issues)} files with issues:")
            for fn in audit_issues:
                print(f"  - {fn}")
            ok = False
        else:
            print("[PASS] Bilingual consistency OK")

        # Layer 3: Distribution
        dist_issues = validators.check_all_distributions(articles_dir)
        if dist_issues:
            print(f"[FAIL] Image distribution issues in {len(dist_issues)} files:")
            for fn, issue in dist_issues.items():
                print(f"  {fn}: {issue}")
            ok = False
        else:
            print("[PASS] Image distribution OK")

    print(f"\n{'='*60}")
    if ok:
        print("BUILD PASSED")
        print('='*60)
        sys.exit(0)
    else:
        print("BUILD FAILED")
        print('='*60)
        sys.exit(1)


if __name__ == '__main__':
    main()
