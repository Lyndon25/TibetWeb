import os, re

SKIP_DIRS = {'AddingArticleWorkSpace', 'scripts', 'docs'}

# Pattern: data-lang-zh or data-lang-en containing HTML tags
# We look for data-lang-*="...<...>..."  (angle brackets inside attribute values)
PATTERN = re.compile(r'data-lang-(zh|en)=["\']([^"\']*<[a-zA-Z/][^>]*>[^"\']*)["\']')

def find_html_files(root='.'):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.html'):
                files.append(os.path.join(dirpath, fn))
    return files

def scan_file(path):
    issues = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in PATTERN.finditer(content):
        attr_name = m.group(1)
        value = m.group(2)
        start = max(0, m.start() - 20)
        end = min(len(content), m.end() + 20)
        context = content[start:end]
        issues.append({
            'line': content[:m.start()].count('\n') + 1,
            'attr': f'data-lang-{attr_name}',
            'value': value,
            'context': context
        })
    return issues

def main():
    files = find_html_files()
    total = 0
    for path in sorted(files):
        issues = scan_file(path)
        if issues:
            print(f"\n=== {path} ===")
            for iss in issues:
                print(f"  Line {iss['line']} | {iss['attr']}")
                print(f"    Context: ...{iss['context']}...")
                total += 1
    print(f"\nTotal issues: {total}")

if __name__ == '__main__':
    main()
