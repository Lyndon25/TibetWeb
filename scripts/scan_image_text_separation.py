import os, re

SKIP_DIRS = {'AddingArticleWorkSpace', 'scripts', 'docs'}

def find_html_files(root='.'):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.html'):
                files.append(os.path.join(dirpath, fn))
    return files

def extract_body_block(content, lang):
    """Extract article-body content for given language."""
    start_marker = f'<div class="lang-content" data-lang="{lang}">'
    # Find body block (not hero block)
    # Heroes are inside <header>, body blocks are inside <div class="article-body">
    body_start = content.find('<div class="article-body">')
    if body_start < 0:
        return None
    
    after_body = content[body_start:]
    idx = after_body.find(start_marker)
    if idx < 0:
        return None
    
    start = idx + len(start_marker)
    depth = 1
    p = start
    while depth > 0 and p < len(after_body):
        next_open = after_body.find('<div', p)
        next_close = after_body.find('</div>', p)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            p = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return after_body[start:next_close]
            p = next_close + 6
    return None

def analyze_distribution(block):
    """Check if all images are clustered at start or end, separated from text."""
    if not block:
        return None
    
    # Find positions of all <img> and text nodes (non-tag content)
    # Simplified: check order of <img> tags vs <h2>, <h3>, <h4>, <p> tags
    
    # Remove whitespace-only at start/end
    block = block.strip()
    if not block:
        return None
    
    # Extract first-level tags (not nested)
    tags = re.findall(r'<(/?)([a-zA-Z0-9]+)[^>]*>', block)
    
    # Find positions of img tags and paragraph/heading tags
    img_positions = [m.start() for m in re.finditer(r'<img', block)]
    text_positions = [m.start() for m in re.finditer(r'<(?:p|h[2-6])', block)]
    
    if not img_positions or not text_positions:
        return None
    
    # Check if ALL imgs are before ALL text (images-then-text)
    last_img = max(img_positions)
    first_text = min(text_positions)
    if last_img < first_text:
        return f"images_at_start: {len(img_positions)} imgs before {len(text_positions)} text blocks"
    
    # Check if ALL imgs are after ALL text (text-then-images)
    first_img = min(img_positions)
    last_text = max(text_positions)
    if first_img > last_text:
        return f"images_at_end: {len(img_positions)} imgs after {len(text_positions)} text blocks"
    
    # Check if imgs are very front-heavy (>80% imgs before first text)
    imgs_before_first_text = sum(1 for p in img_positions if p < first_text)
    if imgs_before_first_text >= len(img_positions) * 0.8 and imgs_before_first_text >= 3:
        return f"mostly_images_first: {imgs_before_first_text}/{len(img_positions)} imgs before text"
    
    # Check if imgs are very back-heavy
    imgs_after_last_text = sum(1 for p in img_positions if p > last_text)
    if imgs_after_last_text >= len(img_positions) * 0.8 and imgs_after_last_text >= 3:
        return f"mostly_images_last: {imgs_after_last_text}/{len(img_positions)} imgs after text"
    
    return None

def main():
    files = find_html_files()
    issues = []
    
    for path in sorted(files):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        zh_block = extract_body_block(content, 'zh')
        en_block = extract_body_block(content, 'en')
        
        if not zh_block or not en_block:
            continue
        
        zh_imgs = len(re.findall(r'<img', zh_block))
        en_imgs = len(re.findall(r'<img', en_block))
        
        # Check EN distribution
        en_issue = analyze_distribution(en_block)
        if en_issue:
            issues.append({
                'file': path,
                'issue': en_issue,
                'zh_imgs': zh_imgs,
                'en_imgs': en_imgs,
                'en_len': len(en_block),
                'zh_len': len(zh_block)
            })
    
    print(f"Found {len(issues)} files with image-text separation issues in EN body:\n")
    for iss in issues:
        print(f"  {iss['file']}")
        print(f"    EN: {iss['en_imgs']} imgs, {iss['en_len']} chars | ZH: {iss['zh_imgs']} imgs, {iss['zh_len']} chars")
        print(f"    Issue: {iss['issue']}")
        print()

if __name__ == '__main__':
    main()
