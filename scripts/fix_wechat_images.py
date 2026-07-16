"""Download WeChat CDN images locally and update HTML references."""
import os, re, hashlib, time, urllib.request
from PIL import Image
import io

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
wechat_pattern = re.compile(r'(https?://[^\"\s]*(?:mmbiz|mmecoa)\.qpic\.cn[^\"\s]*)')
total_downloaded = 0
total_skipped = 0
total_failed = 0

for dirpath, dirnames, filenames in os.walk(root):
    if 'AddingArticleWorkSpace' in dirpath:
        continue

    for f in filenames:
        if not f.endswith('.html'):
            continue
        # Also handle standalone .html files in articles/
        if f != 'index.html' and '/articles/' not in dirpath.replace('\\', '/'):
            if f != 'articles/index.html':
                continue

        filepath = os.path.join(dirpath, f)
        with open(filepath, 'r', encoding='utf-8') as fh:
            content = fh.read()

        urls = wechat_pattern.findall(content)
        if not urls:
            continue

        rel = os.path.relpath(filepath, root)
        print(f'\n{rel}: {len(urls)} WeChat refs')

        # Determine images directory
        if f == 'index.html':
            img_dir = os.path.join(dirpath, 'images')
        else:
            # Standalone .html file like articles/foo.html
            base = f[:-5]
            img_dir = os.path.join(dirpath, 'images')

        os.makedirs(img_dir, exist_ok=True)

        # Deduplicate URLs while preserving order
        seen = {}
        url_map = {}  # old_url -> local_filename

        for url in urls:
            if url in seen:
                total_skipped += 1
                continue
            seen[url] = True

            # Generate a short hash-based filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            # Try to preserve extension from URL
            ext = '.jpg'  # default
            if '.png' in url.split('?')[0] or 'wx_fmt=png' in url:
                ext = '.png'
            elif 'wx_fmt=jpeg' in url or 'wx_fmt=jpg' in url:
                ext = '.jpg'
            elif 'wx_fmt=gif' in url:
                ext = '.gif'

            # Check if already downloaded
            existing = None
            for e in ['.webp', '.jpg', '.jpeg', '.png', '.gif']:
                candidate = os.path.join(img_dir, url_hash + e)
                if os.path.exists(candidate) and os.path.getsize(candidate) > 100:
                    existing = candidate
                    break

            if existing:
                local_name = os.path.basename(existing)
                url_map[url] = 'images/' + local_name
                total_skipped += 1
                continue

            # Download
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://mp.weixin.qq.com/'
                })
                resp = urllib.request.urlopen(req, timeout=15)
                data = resp.read()

                if len(data) < 100:
                    raise Exception(f'Too small: {len(data)} bytes')

                # Convert to WebP
                img = Image.open(io.BytesIO(data))
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if too large (>2000px wide)
                if img.width > 2000:
                    ratio = 2000 / img.width
                    new_h = int(img.height * ratio)
                    img = img.resize((2000, new_h), Image.LANCZOS)

                local_path = os.path.join(img_dir, url_hash + '.webp')
                img.save(local_path, 'WEBP', quality=80)

                local_name = url_hash + '.webp'
                url_map[url] = 'images/' + local_name
                total_downloaded += 1
                size_kb = len(data) / 1024
                webp_kb = os.path.getsize(local_path) / 1024
                print(f'  OK [{total_downloaded}]: {url_hash}.webp ({size_kb:.0f}KB -> {webp_kb:.0f}KB)')

            except Exception as e:
                url_map[url] = url  # keep original URL if download fails
                total_failed += 1
                print(f'  FAIL: {url_hash} - {str(e)[:60]}')

            time.sleep(0.05)  # be gentle

        # Update HTML
        if url_map:
            new_content = content
            for old_url, local_path in url_map.items():
                if local_path.startswith('images/'):
                    new_content = new_content.replace(old_url, local_path)
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as fh:
                    fh.write(new_content)

print(f'\n{"="*60}')
print(f'Done! Downloaded: {total_downloaded}, Skipped: {total_skipped}, Failed: {total_failed}')
