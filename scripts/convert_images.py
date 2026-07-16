"""Convert oversized PNGs to WebP and update HTML references."""
import os, re
from PIL import Image

root = r'C:\Users\86137\Desktop\WorkSpace\tibetride\TibetWeb'
min_size = 500 * 1024  # 500KB
converted = 0
total_saved = 0

# Find all large PNGs (excluding AddingArticleWorkSpace)
for dirpath, dirnames, filenames in os.walk(root):
    if 'AddingArticleWorkSpace' in dirpath:
        continue
    for f in filenames:
        if f.lower().endswith('.png'):
            filepath = os.path.join(dirpath, f)
            size = os.path.getsize(filepath)
            if size < min_size:
                continue

            # Convert to WebP
            webp_name = f[:-4] + '.webp'
            webp_path = os.path.join(dirpath, webp_name)

            try:
                img = Image.open(filepath)
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                img.save(webp_path, 'WEBP', quality=80)
                webp_size = os.path.getsize(webp_path)

                saved = size - webp_size
                total_saved += saved
                rel = os.path.relpath(filepath, root)
                print(f'Converted: {rel} ({size/1024/1024:.1f}MB -> {webp_size/1024/1024:.1f}MB, saved {saved/1024:.0f}KB)')
                converted += 1

                # Update HTML references
                for ddir, ddirs, ffiles in os.walk(root):
                    if 'AddingArticleWorkSpace' in ddir:
                        continue
                    for hf in ffiles:
                        if hf.endswith('.html'):
                            hpath = os.path.join(ddir, hf)
                            with open(hpath, 'r', encoding='utf-8') as fh:
                                content = fh.read()
                            if f in content:
                                new_content = content.replace(f, webp_name)
                                if new_content != content:
                                    with open(hpath, 'w', encoding='utf-8') as fh:
                                        fh.write(new_content)
                                    print(f'  Updated HTML: {os.path.relpath(hpath, root)}')

            except Exception as e:
                print(f'ERROR converting {filepath}: {e}')

print(f'\nConverted: {converted} images')
print(f'Total saved: {total_saved/1024/1024:.1f}MB')
