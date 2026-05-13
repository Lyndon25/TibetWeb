"""
Download WeChat CDN images to local storage for article processing.

Usage:
    from lib.image_downloader import download_article_images
    mapping = download_article_images(slug, ['https://mmbiz.qpic.cn/...', ...])
    # Returns: {'https://mmbiz.qpic.cn/...': '../images/articles/slug/001.jpg', ...}
"""
import os
import re
import hashlib
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

# Default image output co-located with article: articles/<slug>/images/
DEFAULT_IMAGES_BASE = os.path.join(_SKILL_DIR, 'articles')

# URL patterns that indicate WeChat CDN
WECHAT_DOMAINS = {
    'mmbiz.qpic.cn', 'mmbiz.qlogo.cn',
    'mp.weixin.qq.com', 'mmsns.qpic.cn',
}


def _is_wechat_url(url: str) -> bool:
    """Check if URL is from WeChat CDN."""
    url_lower = url.lower()
    for domain in WECHAT_DOMAINS:
        if domain in url_lower:
            return True
    return False


def _guess_extension(url: str, content_type: Optional[str] = None) -> str:
    """Guess image file extension from URL or Content-Type."""
    # From URL query parameter wx_fmt
    m = re.search(r'wx_fmt=(\w+)', url, re.I)
    if m:
        fmt = m.group(1).lower()
        if fmt in ('jpeg', 'jpg'):
            return '.jpg'
        if fmt == 'png':
            return '.png'
        if fmt == 'gif':
            return '.gif'
        if fmt == 'webp':
            return '.webp'

    # From Content-Type
    if content_type:
        ct = content_type.lower()
        if 'jpeg' in ct or 'jpg' in ct:
            return '.jpg'
        if 'png' in ct:
            return '.png'
        if 'gif' in ct:
            return '.gif'
        if 'webp' in ct:
            return '.webp'
        if 'svg' in ct:
            return '.svg'

    # From URL path extension
    path = url.split('?')[0].split('#')[0]
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'):
        return ext if ext != '.jpeg' else '.jpg'

    # Default fallback
    return '.jpg'


def _generate_filename(url: str, index: int, ext: str) -> str:
    """Generate a unique local filename for the image."""
    # Use short hash of URL for uniqueness + index for ordering
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:6]
    return f"{index:03d}_{url_hash}{ext}"


def _download_single(url: str, dest_path: str, timeout: int = 30) -> tuple[bool, Optional[str]]:
    """
    Download a single image.
    Returns: (success, error_message)
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer': 'https://mp.weixin.qq.com/',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        # Bypass system proxy for image downloads
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', '')
            data = resp.read()
            if len(data) < 100:
                return False, f"Too small ({len(data)} bytes)"
            with open(dest_path, 'wb') as f:
                f.write(data)
        return True, None
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"URL error: {e.reason}"
    except Exception as e:
        return False, str(e)


def download_article_images(
    slug: str,
    image_urls: list[str],
    images_base: Optional[str] = None,
    max_workers: int = 4,
    skip_existing: bool = True,
) -> dict[str, str]:
    """
    Download all images for an article and return a URL -> local path mapping.

    Args:
        slug: Article slug, used to create subdirectory
        image_urls: List of image URLs from WeChat source
        images_base: Base directory for images (default: ../../images/articles/)
        max_workers: Number of concurrent download threads
        skip_existing: Skip if file already exists

    Returns:
        Mapping of original URL -> relative path for HTML src attribute
    """
    if images_base is None:
        images_base = DEFAULT_IMAGES_BASE

    article_img_dir = os.path.join(images_base, slug, 'images')
    os.makedirs(article_img_dir, exist_ok=True)

    mapping: dict[str, str] = {}
    tasks: list[tuple[str, str, str]] = []  # (url, dest_path, rel_path)

    for i, url in enumerate(image_urls, 1):
        if not url or not url.startswith('http'):
            continue
        ext = _guess_extension(url)
        filename = _generate_filename(url, i, ext)
        dest_path = os.path.join(article_img_dir, filename)
        # Relative path from articles/<slug>/index.html -> images/filename (co-located)
        rel_path = f"images/{filename}"

        if skip_existing and os.path.exists(dest_path) and os.path.getsize(dest_path) > 100:
            mapping[url] = rel_path
            continue

        tasks.append((url, dest_path, rel_path))

    if not tasks:
        return mapping

    # Download with thread pool
    downloaded = 0
    failed = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(_download_single, url, dest_path): (url, dest_path, rel_path)
            for url, dest_path, rel_path in tasks
        }

        for future in as_completed(future_to_task):
            url, dest_path, rel_path = future_to_task[future]
            try:
                ok, err = future.result()
                if ok:
                    mapping[url] = rel_path
                    downloaded += 1
                else:
                    failed.append((url, err))
                    # Fallback: keep original URL
                    mapping[url] = url
            except Exception as e:
                failed.append((url, str(e)))
                mapping[url] = url

    # Log results
    if failed:
        print(f"  [Images] Downloaded {downloaded}/{len(tasks)}, {len(failed)} failed")
        for url, err in failed[:5]:
            print(f"    - FAIL: {url[:80]}... ({err})")
    else:
        print(f"  [Images] Downloaded {downloaded}/{len(tasks)} OK")

    return mapping


def replace_image_urls(html: str, mapping: dict[str, str]) -> str:
    """
    Replace image URLs in HTML with local paths.
    Handles both src="url" and data-src="url" attributes.
    """
    result = html
    for old_url, new_path in mapping.items():
        # Escape special regex chars in URL
        escaped = re.escape(old_url)
        # Replace src="old_url"
        result = re.sub(
            rf'src=["\']{escaped}["\']',
            f'src="{new_path}"',
            result,
        )
        # Replace data-src="old_url"
        result = re.sub(
            rf'data-src=["\']{escaped}["\']',
            f'data-src="{new_path}"',
            result,
        )
    return result


def extract_image_urls_from_html(html: str) -> list[str]:
    """Extract all image URLs from HTML content."""
    urls = []
    # Match src and data-src attributes
    for pattern in (r'src=["\'](https?://[^"\']+)["\']', r'data-src=["\'](https?://[^"\']+)["\']'):
        urls.extend(re.findall(pattern, html))
    # Deduplicate while preserving order
    seen = set()
    result = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
