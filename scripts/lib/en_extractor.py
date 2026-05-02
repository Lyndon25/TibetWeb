"""
Extract English content from WeChat source HTML/MD files.
Consolidates logic from rebuild_en_from_source.py, fix_en_content.py, fix_mixed_lang.py.
"""
import os
import re
import html
from bs4 import BeautifulSoup


def _clean_img_tag(m: re.Match) -> str:
    attrs = m.group(1)
    src_match = re.search(r'src=["\']([^"\']+)["\']', attrs)
    data_src_match = re.search(r'data-src=["\']([^"\']+)["\']', attrs)
    url = src_match.group(1) if src_match else (data_src_match.group(1) if data_src_match else '')
    return f'<img src="{url}" alt="" loading="lazy">'


def _has_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def _chinese_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(re.findall(r'[\u4e00-\u9fff]', text)) / len(text)


def _normalize_html_entities(raw: str) -> str:
    """Safely normalize HTML entities without breaking URLs."""
    # First unescape any existing entities, then re-escape properly
    return html.escape(html.unescape(raw))


def extract_from_html(src_path: str, strict_chinese_filter: bool = False) -> str | None:
    """
    Extract English translation from a WeChat HTML source file.

    Args:
        src_path: path to the source HTML file
        strict_chinese_filter: if True, skip paragraphs with >30% Chinese chars
    """
    with open(src_path, 'r', encoding='utf-8') as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, 'html.parser')
    en_div = soup.find('div', id='english_translation')
    if not en_div:
        return None

    inner = en_div.find('div', style=lambda s: bool(s and 'line-height' in s))
    if not inner:
        inner = en_div

    raw = str(inner)
    close_tag = '</div>'
    content_start = raw.find('>') + 1
    if raw.rstrip().endswith(close_tag):
        raw = raw[content_start:raw.rfind(close_tag)]
    else:
        raw = raw[content_start:]

    # Clean up WeChat artifacts
    raw = re.sub(r'<h2[^>]*>\s*English Translation\s*</h2>', '', raw, flags=re.S)
    raw = re.sub(r'<p[^>]*style="text-align:center;"[^>]*>\s*(<img[^>]*>)\s*</p>', r'\1', raw, flags=re.S)
    raw = re.sub(r'<p[^>]*style="font-size:13px;color:#999;text-align:center;"[^>]*>(.*?)</p>',
                 r'<p class="caption">\1</p>', raw, flags=re.S)
    raw = re.sub(r' style="[^"]*"', '', raw)
    raw = re.sub(r' data-src="[^"]*"', '', raw)
    raw = re.sub(r'<img([^>]*)>', _clean_img_tag, raw)
    raw = re.sub(r'<p[^>]*>\s*(Editor:|Source:|Proofreader:|Reviewer:).*?</p>', '', raw, flags=re.S)
    raw = _normalize_html_entities(raw)

    raw = raw.strip()

    # Optional strict filtering (from fix_mixed_lang.py)
    if strict_chinese_filter and raw:
        soup2 = BeautifulSoup(raw, 'html.parser')
        parts = []
        for elem in soup2.find_all(['h2', 'h3', 'h4', 'h5', 'p', 'img'], recursive=True):
            if elem.name == 'img':
                src = elem.get('src', '')
                if src:
                    parts.append(f'<img src="{src}" alt="" loading="lazy">')
            elif elem.name in ('h2', 'h3', 'h4', 'h5'):
                text = elem.get_text(strip=True)
                if text and 'english translation' not in text.lower():
                    if not _has_chinese(text) or _chinese_ratio(text) < 0.1:
                        parts.append(f'<h2>{text}</h2>' if elem.name == 'h2' else f'<h3>{text}</h3>')
            elif elem.name == 'p':
                text = elem.get_text(strip=True)
                if text and len(text) > 2 and not text.startswith('▲'):
                    if any(k in text.lower() for k in ['editor:', 'photo credit', 'proofreader', 'reviewer', 'source:']):
                        continue
                    if _chinese_ratio(text) > 0.3:
                        continue
                    strong_child = elem.find(['strong', 'b'])
                    if strong_child and len(text) < 80 and text == strong_child.get_text(strip=True):
                        parts.append(f'<p><strong>{text}</strong></p>')
                    else:
                        parts.append(f'<p>{text}</p>')
        raw = '\n'.join(parts)

    return raw if raw else None


def extract_from_md(src_path: str) -> str | None:
    """Extract English translation from a Markdown source file."""
    with open(src_path, 'r', encoding='utf-8') as f:
        text = f.read()

    match = re.search(r'(?:^|\n)#\s*English Translation.*', text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    en_text = text[match.start():]
    lines = en_text.split('\n')
    parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^#\s*English Translation', line, re.I):
            continue
        if _chinese_ratio(line) > 0.3:
            continue
        if line.startswith('!['):
            m = re.search(r'!\[.*?\]\((.*?)\)', line)
            if m:
                parts.append(f'<img src="{m.group(1)}" alt="" loading="lazy">')
            continue
        if line.startswith('## '):
            parts.append(f'<h2>{line[3:]}</h2>')
            continue
        if line.startswith('### '):
            parts.append(f'<h3>{line[4:]}</h3>')
            continue
        if line.startswith('- '):
            content = line[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            parts.append(f'<p>• {content}</p>')
            continue
        content = line
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        if content:
            parts.append(f'<p>{content}</p>')

    return '\n'.join(parts) if parts else None


def extract_en(src_dir: str, file_pattern: str, strict: bool = False) -> tuple[str | None, str]:
    """
    Find source file by pattern and extract English content.

    Returns:
        (en_html, source_type) where source_type is 'html', 'md', or ''
    """
    files = [f for f in os.listdir(src_dir) if file_pattern in f]
    html_file = next((f for f in files if f.endswith('.html')), None)
    md_file = next((f for f in files if f.endswith('.md')), None)

    if html_file:
        en = extract_from_html(os.path.join(src_dir, html_file), strict_chinese_filter=strict)
        if en:
            return en, 'html'

    if md_file:
        en = extract_from_md(os.path.join(src_dir, md_file))
        if en:
            return en, 'md'

    return None, ''


def get_title_from_en_html(en_html: str, fallback: str = 'Article') -> str:
    """Extract the first heading as title from English HTML."""
    title_match = re.search(r'<h[123][^>]*>(.*?)</h[123]>', en_html, re.S)
    if title_match:
        return re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    plain = re.sub(r'<[^>]+>', '', en_html)
    return plain.strip()[:60] if plain.strip() else fallback
