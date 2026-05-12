#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章抓取模块
提供微信文章获取、解析和图片本地化功能
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup


# 目录常量
_SCRIPT_DIR = Path(__file__).parent.resolve()
_SKILL_DIR = _SCRIPT_DIR.parent.parent.resolve()


def _log(message: str, level: str = "INFO") -> None:
    """简单日志输出"""
    print(f"[{level}] {message}")


def is_valid_wechat_url(url: str) -> bool:
    """验证是否为有效的微信公众号URL"""
    patterns = [
        r'https?://mp\.weixin\.qq\.com/s\?',
        r'https?://mp\.weixin\.qq\.com/s/',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False


def sanitize_filename(name: str, max_length: int = 150) -> str:
    """清理文件名，移除非法字符并限制长度"""
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']
    for char in illegal_chars:
        name = name.replace(char, '_')
    
    if len(name) > max_length:
        name = name[:max_length]
    
    return name.strip()


def _get_session() -> requests.Session:
    """创建请求会话，设置合适的请求头"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    session.trust_env = False  # bypass system proxy
    return session


def _download_single_image(img_url: str, save_path: Path, session: requests.Session = None) -> bool:
    """下载单张图片到指定路径"""
    try:
        if not img_url or not img_url.startswith(('http://', 'https://')):
            return False
        
        if session is None:
            session = _get_session()
        
        # 微信图片可能需要特殊处理
        headers = session.headers.copy()
        headers.update({
            'Referer': 'https://mp.weixin.qq.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        })
        
        response = session.get(img_url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return True
    except Exception as e:
        _log(f"图片下载失败: {img_url[:50]}..., 错误: {e}", "WARN")
    
    return False


def download_images(content_soup: BeautifulSoup, target_dir: str, relative_prefix: str = '') -> Dict[str, str]:
    """本地化文章中的图片，返回原始URL到本地路径的映射
    
    Args:
        content_soup: 文章内容的BeautifulSoup对象
        target_dir: 图片保存目录
        relative_prefix: 生成相对路径时的前缀（用于HTML中引用）
    
    Returns:
        Dict[original_url: local_path] 映射
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    img_mapping = {}  # 原始URL -> 本地路径
    
    if not content_soup:
        return img_mapping
    
    img_tags = content_soup.find_all('img')
    _log(f"发现 {len(img_tags)} 张图片")
    
    for idx, img in enumerate(img_tags, 1):
        # 获取图片URL（微信使用data-src属性）
        src = img.get('data-src', '') or img.get('src', '')
        if not src:
            continue
        
        if src in img_mapping:
            # 已经处理过的图片，更新src属性
            local_rel_path = img_mapping[src]
            if relative_prefix:
                img['src'] = str(Path(relative_prefix) / local_rel_path)
            else:
                img['src'] = local_rel_path
            if 'data-src' in img.attrs:
                del img['data-src']
            continue
        
        # 确定文件扩展名
        if 'wx_fmt=' in src:
            fmt_match = re.search(r'wx_fmt=(\w+)', src)
            ext = fmt_match.group(1) if fmt_match else 'jpg'
        else:
            parsed = urlparse(src)
            ext = Path(unquote(parsed.path)).suffix[1:] or 'jpg'
        
        # 限制扩展名长度
        ext = ext[:5] if len(ext) > 5 else ext
        
        # 生成文件名
        filename = f"img_{idx:03d}.{ext}"
        save_path = target_path / filename
        
        # 下载图片
        if _download_single_image(src, save_path):
            relative_path = filename
            if relative_prefix:
                img['src'] = str(Path(relative_prefix) / relative_path)
            else:
                img['src'] = relative_path
            if 'data-src' in img.attrs:
                del img['data-src']
            img_mapping[src] = relative_path
            _log(f"  下载成功: {filename}")
        else:
            # 下载失败，保留原始URL
            img['src'] = src
    
    _log(f"图片处理完成: {len(img_mapping)}/{len(img_tags)} 张成功下载")
    return img_mapping


def _parse_article_content(soup: BeautifulSoup, url: str) -> Dict:
    """解析文章内容，提取元数据和正文内容"""
    # 提取标题
    title = ""
    title_selectors = [
        'h1#activity-name',
        'h1.rich_media_title',
        '.rich_media_title',
        '#activity-name',
        'meta[property="og:title"]',
    ]
    
    for selector in title_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    title = elem.get('content', '')
                else:
                    title = elem.get_text(strip=True)
                if title:
                    break
        except:
            continue
    
    if not title:
        title = "未命名文章_" + datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 提取作者
    author = ""
    author_selectors = [
        '#js_name',
        '.rich_media_meta_nickname',
        '.profile_nickname',
        '.original_author',
        'meta[name="author"]',
    ]
    
    for selector in author_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    author = elem.get('content', '')
                else:
                    author = elem.get_text(strip=True)
                if author:
                    break
        except:
            continue
    
    # 提取公众号名称
    account_name = ""
    account_selectors = [
        '.profile_nickname',
        '#js_name',
        '.rich_media_meta_nickname',
        'a#js_name',
    ]
    
    for selector in account_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                account_name = elem.get_text(strip=True)
                if account_name:
                    break
        except:
            continue
    
    # 提取发布时间
    publish_time = ""
    
    # 方法1: meta标签
    meta_ctime = soup.find('meta', attrs={'name': 'ct'})
    if meta_ctime:
        try:
            ts = int(meta_ctime.get('content', '0'))
            if ts > 0:
                publish_time = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    
    # 方法2: 查找时间元素
    if not publish_time:
        time_selectors = [
            '#publish_time',
            '.rich_media_meta_list em',
            '.publish_time',
        ]
        for selector in time_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5:
                        publish_time = text
                        break
            except:
                continue
    
    if not publish_time:
        publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 提取封面图
    cover_image = ""
    cover_selectors = [
        'meta[property="og:image"]',
        'meta[name="og:image"]',
    ]
    
    for selector in cover_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                cover_image = elem.get('content', '')
                if cover_image:
                    break
        except:
            continue
    
    # 提取正文内容元素
    content_elem = None
    content_selectors = [
        '#js_content',
        '.rich_media_content',
        'div.rich_media_content',
    ]
    
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            break
    
    if not content_elem:
        _log("未找到正文内容，使用整个页面body", "WARN")
        content_elem = soup.body if soup.body else soup
    
    content_html = str(content_elem)
    
    # 提取摘要
    description = ""
    desc_selectors = [
        'meta[property="og:description"]',
        'meta[name="description"]',
    ]
    for selector in desc_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                description = elem.get('content', '')
                break
        except:
            continue
    
    return {
        'title': title,
        'author': author,
        'account_name': account_name,
        'publish_time': publish_time,
        'content_html': content_html,
        'content_soup': content_elem,
        'cover_image': cover_image,
        'description': description,
        'original_url': url,
    }


def fetch_wechat_article(url: str) -> Optional[Dict]:
    """获取并解析微信文章
    
    Args:
        url: 微信公众号文章URL
    
    Returns:
        包含文章信息的字典，失败返回None
        字段: title, author, account_name, publish_time, content_html, 
              content_soup, cover_image, description, original_url
    """
    try:
        _log(f"正在获取: {url[:80]}...")
        
        # 验证URL
        if not is_valid_wechat_url(url):
            _log("不是有效的微信公众号URL (应为 mp.weixin.qq.com/s/... 格式)", "ERROR")
            return None
        
        # 发送请求
        session = _get_session()
        response = session.get(url, timeout=30, allow_redirects=True)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            _log(f"请求失败: HTTP {response.status_code}", "ERROR")
            return None
        
        _log(f"页面获取成功 (大小: {len(response.text)} 字节)")
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取文章信息
        article = _parse_article_content(soup, url)
        
        _log(f"文章标题: {article['title'][:60]}..." if len(article['title']) > 60 else f"文章标题: {article['title']}")
        _log(f"作者/公众号: {article['author'] or article['account_name'] or '未知'}")
        
        return article
        
    except Exception as e:
        _log(f"获取文章失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 简单测试
    print("=" * 60)
    print("微信文章抓取模块 - 测试")
    print("=" * 60)
    print("\n可用函数:")
    print("  - fetch_wechat_article(url: str) -> dict")
    print("  - download_images(content_soup, target_dir, relative_prefix='') -> dict")
    print("  - is_valid_wechat_url(url: str) -> bool")
    print("  - sanitize_filename(name: str) -> str")
    print("\n目录常量:")
    print(f"  _SCRIPT_DIR: {_SCRIPT_DIR}")
    print(f"  _SKILL_DIR: {_SKILL_DIR}")
