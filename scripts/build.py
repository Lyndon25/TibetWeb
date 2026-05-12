# -*- coding: utf-8 -*-
"""
Unified build entry point for TibetRide content pipeline.

Phases:
  1. convert   - Generate articles from WeChat source HTML
  2. index     - Regenerate articles listing page
  3. validate  - Run HTML + audit + distribution checks

EN translation is handled by AI agent via the skill, not this pipeline.

Usage:
    python scripts/build.py --all
    python scripts/build.py --convert --slug <slug>
    python scripts/build.py --validate
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

from lib import validators, atomic_io


LOG_DIR = os.path.join(_SKILL_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


def _log(phase: str, message: str) -> None:
    """Print and log a message."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] [{phase}] {message}"
    print(line)
    log_file = os.path.join(LOG_DIR, datetime.now().strftime('%Y%m%d') + '.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def _run_script(script_name: str, args: list[str] | None = None) -> tuple[bool, str]:
    """Run a Python script as a subprocess."""
    script_path = os.path.join(_SCRIPT_DIR, script_name)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=300, cwd=_SKILL_DIR,
        )
        if result.returncode != 0:
            return False, result.stderr or result.stdout
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout after 300s"
    except Exception as e:
        return False, str(e)


def run_convert(slug: str | None = None, no_download: bool = False) -> bool:
    """Run article generation from WeChat source."""
    _log('CONVERT', 'Starting article generation...')
    args = []
    if slug:
        args.extend(['--slug', slug])
    if no_download:
        args.append('--no-download')
    ok, output = _run_script('convert_articles_v2.py', args)
    if ok:
        _log('CONVERT', 'Completed successfully')
    else:
        _log('CONVERT', f'FAILED: {output[:200]}')
    return ok


def run_index() -> bool:
    """Regenerate articles listing page."""
    _log('INDEX', 'Regenerating articles index...')
    ok, output = _run_script('generate_index.py')
    if ok:
        _log('INDEX', 'Completed successfully')
    else:
        _log('INDEX', f'FAILED: {output[:200]}')
    return ok


def run_validate(articles_dir: str) -> tuple[bool, dict]:
    """Run all validation checks."""
    _log('VALIDATE', 'Starting validation...')
    results = {}
    ok = True

    html_errors = validators.validate_all_articles(articles_dir)
    if html_errors:
        _log('VALIDATE', f"HTML validation failed: {len(html_errors)} files")
        for fn, errs in html_errors.items():
            _log('VALIDATE', f"  {fn}: {errs}")
        ok = False
    else:
        _log('VALIDATE', '[PASS] HTML structure OK')
    results['html'] = html_errors

    audit_issues = validators.audit_all_articles(articles_dir)
    if audit_issues:
        _log('VALIDATE', f"Audit found {len(audit_issues)} files with issues")
        for fn, issues in audit_issues.items():
            _log('VALIDATE', f"  {fn}: {len(issues)} issues")
        ok = False
    else:
        _log('VALIDATE', '[PASS] Bilingual consistency OK')
    results['audit'] = audit_issues

    dist_issues = validators.check_all_distributions(articles_dir)
    if dist_issues:
        _log('VALIDATE', f"Image distribution issues in {len(dist_issues)} files")
        for fn, issue in dist_issues.items():
            _log('VALIDATE', f"  {fn}: {issue}")
        ok = False
    else:
        _log('VALIDATE', '[PASS] Image distribution OK')
    results['distribution'] = dist_issues

    return ok, results


def main():
    parser = argparse.ArgumentParser(description='TibetRide unified build')
    parser.add_argument('--convert', action='store_true', help='Generate articles from WeChat source')
    parser.add_argument('--index', action='store_true', help='Regenerate articles listing page')
    parser.add_argument('--validate', action='store_true', help='Run validation checks')
    parser.add_argument('--slug', type=str, help='Process only this slug')
    parser.add_argument('--no-download', action='store_true', help='Skip image downloading')
    parser.add_argument('--all', action='store_true', help='Run full pipeline (convert + index + validate)')
    args = parser.parse_args()

    if not any([args.convert, args.index, args.validate, args.all]):
        parser.print_help()
        sys.exit(1)

    articles_dir = os.path.join(_SKILL_DIR, 'articles')
    ok = True

    if args.all or args.convert:
        ok &= run_convert(slug=args.slug, no_download=args.no_download)

    if args.all or args.index:
        ok &= run_index()

    if args.all or args.validate:
        validate_ok, _ = run_validate(articles_dir)
        ok &= validate_ok

    _log('BUILD', '=' * 50)
    if ok:
        _log('BUILD', 'BUILD PASSED')
        sys.exit(0)
    else:
        _log('BUILD', 'BUILD FAILED - check logs above')
        sys.exit(1)


if __name__ == '__main__':
    main()
