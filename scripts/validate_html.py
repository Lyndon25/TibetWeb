import os
from html.parser import HTMLParser

class HTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.self_closing = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.self_closing:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.self_closing:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"Unexpected closing </{tag}>, expected </{self.stack[-1]}>" if self.stack else f"Unexpected closing </{tag}>")

articles_dir = "articles"
error_files = []

for fn in sorted(os.listdir(articles_dir)):
    if not fn.endswith(".html"):
        continue
    path = os.path.join(articles_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parser = HTMLValidator()
    try:
        parser.feed(content)
    except Exception as e:
        error_files.append((fn, f"Parse error: {e}"))
        continue
    if parser.errors:
        error_files.append((fn, parser.errors))
    elif parser.stack:
        error_files.append((fn, f"Unclosed tags: {parser.stack}"))

if error_files:
    print("HTML VALIDATION FAILED:")
    for fn, err in error_files:
        print(f"  {fn}: {err}")
else:
    print("All HTML files validated successfully.")
