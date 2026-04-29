import os, re

SKIP_DIRS = {'AddingArticleWorkSpace', 'scripts', 'docs'}
META_TAG = '  <meta name="referrer" content="no-referrer">\n'

def find_html_files(root='.'):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.html'):
                files.append(os.path.join(dirpath, fn))
    return files

def inject_meta(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Already has referrer meta?
    if 'name="referrer"' in content.lower():
        return False, 'already has referrer meta'

    # Find <head> tag
    match = re.search(r'(<head(?:\s[^>]*)?>)', content, re.IGNORECASE)
    if not match:
        return False, 'no <head> tag found'

    insert_pos = match.end()
    new_content = content[:insert_pos] + '\n' + META_TAG + content[insert_pos:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True, 'injected'

def main():
    files = find_html_files()
    files.sort()
    modified = []
    skipped = []

    for path in files:
        ok, reason = inject_meta(path)
        if ok:
            modified.append(path)
        else:
            skipped.append((path, reason))

    print(f"Modified: {len(modified)}")
    for p in modified:
        print(f"  + {p}")
    print(f"Skipped: {len(skipped)}")
    for p, r in skipped:
        print(f"  - {p}: {r}")

if __name__ == '__main__':
    main()
