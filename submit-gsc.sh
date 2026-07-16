#!/bin/bash
# Google Search Console — 一键提交脚本
# 使用前请确保浏览器已登录 Google 账号（拥有 tibetride.com GSC 权限）

echo "========================================="
echo "  TibetRide GSC 索引提交助手"
echo "========================================="
echo ""
echo "请确保浏览器已登录 Google 账号"
echo "如果没有 GSC 权限，请先添加网站属性"
echo ""

# Step 1: 打开 GSC sitemap 提交页面
echo "【第1步】打开 Sitemap 提交页面..."
echo "  在页面中点击 'Add a new sitemap' → 输入 'sitemap.xml' → Submit"
cmd.exe /c start "" "https://search.google.com/search-console/sitemaps?resource_id=sc-domain:tibetride.com" 2>/dev/null
sleep 1

read -p "  完成 sitemap 提交后，按 Enter 继续..."

echo ""

# Step 2: 逐个打开 URL 检查页面
URLS=(
  "https://www.tibetride.com/"
  "https://www.tibetride.com/articles/tibet-trip-cost-2026"
  "https://www.tibetride.com/articles/is-tibet-safe-2026"
  "https://www.tibetride.com/articles/best-time-to-visit-tibet-2026"
  "https://www.tibetride.com/articles/plan-first-tibet-trip-2026"
)

echo "【第2步】逐个提交 URL 索引请求..."
echo "  对每个打开的页面："
echo "    1. 等待 Google 检查完毕"
echo "    2. 点击 'REQUEST INDEXING' 按钮"
echo "    3. 关闭标签页，按 Enter 继续下一个"
echo ""

count=1
for url in "${URLS[@]}"; do
  encoded_url=$(python -c "import urllib.parse; print(urllib.parse.quote('$url', safe=''))")
  echo "  [$count/${#URLS[@]}] 打开: $url"
  cmd.exe /c start "" "https://search.google.com/search-console/inspect?resource_id=sc-domain:tibetride.com&id=$encoded_url" 2>/dev/null
  count=$((count + 1))
  sleep 2
  read -p "  提交完成后按 Enter 继续下一个..."
done

echo ""
echo "========================================="
echo "  全部完成！Google 已收到索引请求"
echo "  通常 1-2 天内新页面会被收录"
echo "========================================="
