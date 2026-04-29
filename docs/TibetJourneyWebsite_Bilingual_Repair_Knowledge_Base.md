# TibetJourneyWebsite 多语言HTML修复任务 — 知识沉淀文档

> **版本**: v1.0  
> **日期**: 2026-04-29  
> **任务**: 24篇双语文章深度复核与修复  
> **状态**: 已完成（100%验证通过）

---

## 一、项目背景与目标

### 1.1 问题概述

TibetJourneyWebsite 是一个中英双语静态网站，采用 `lang-content` + `data-lang` 属性实现语言切换。在文章生成流程中，**英文内容仅被填充为摘要（`meta["excerptEn"]`）**，导致英文页面内容严重缺失。后续批处理修复脚本进一步造成结构损坏（将正文图片错误插入 Hero 区域、标题错位等）。

### 1.2 修复目标

| 维度 | 目标 |
|------|------|
| **标题** | EN/ZH 语义对等，Hero 仅保留 `<h1>`，语言纯净无混杂 |
| **正文** | EN body 与 ZH body 图片数量、文件名、位置完全一致 |
| **结构** | HTML 标签层级、class 属性、内容区块顺序无错乱 |
| **内容** | EN body 完整翻译，无中文混入（地名括号标注除外） |

---

## 二、技术架构概述

### 2.1 双语切换机制

```html
<!-- Hero 区域：仅标题 -->
<header class="article-hero">
  <div class="lang-content" data-lang="zh">
    <h1 class="article-hero__title">中文标题</h1>
  </div>
  <div class="lang-content" data-lang="en">
    <h1 class="article-hero__title">English Title</h1>
  </div>
</header>

<!-- Body 区域：完整内容 -->
<div class="article-body">
  <div class="lang-content" data-lang="zh">
    <!-- 中文正文 + 图片 -->
  </div>
  <div class="lang-content" data-lang="en">
    <!-- 英文正文 + 图片 -->
  </div>
</div>
```

### 2.2 CSS 语言切换

```css
/* 默认隐藏所有语言 */
.lang-content { display: none; }

/* 显示当前语言 */
html[lang="zh"] .lang-content[data-lang="zh"] { display: block; }
html[lang="en"] .lang-content[data-lang="en"] { display: block; }
```

### 2.3 文件组织结构

```
articles/                          # 生成的文章页面
├── index.html                     # 文章列表页
├── qingming-tibet-travel-guide.html
├── altitude-sickness-tips.html
└── ... (24篇)

AddingArticleWorkSpace/1/          # 源文件（微信公众号HTML导出）
├── 绝美刷屏清明西藏出游攻略...（中英）.html
├── 西藏旅游超全避雷攻略...（中英）.html
└── ... (16篇含英文翻译)

scripts/                           # 工具脚本
├── convert_articles_v2.py         # 原始生成脚本（问题根源）
├── rebuild_en_from_source.py      # 从源文件重建EN区块
├── validate_html.py               # HTML结构校验
├── deep_audit.py                  # 双语一致性扫描
└── ...
```

---

## 三、rebuild_en_from_source.py 根因分析与修复

### 3.1 原始 Bug（`convert_articles_v2.py` 第329行）

```python
# 原始生成逻辑：仅用摘要作为EN body
en_html = f'<p>{meta["excerptEn"]}</p>'  # 仅一句话！
```

这导致所有英文页面正文只有一句摘要，完全缺失完整内容。

### 3.2 重建策略设计

**核心思路**：源文件（微信公众号HTML）中包含 `div#english_translation`，内有完整英文翻译。提取并清洗后，替换损坏的EN区块。

#### 3.2.1 提取流程

```python
def extract_en_html(src_path: str) -> str | None:
    soup = BeautifulSoup(html, 'html.parser')
    en_div = soup.find('div', id='english_translation')
    
    # 提取内层容器
    inner = en_div.find('div', style=lambda s: bool(s and 'line-height' in s))
    if not inner:
        inner = en_div
    
    raw = str(inner)
    # 移除外层 <div>...</div> 包装
    content_start = raw.find('>') + 1
    raw = raw[content_start:raw.rfind('</div>')]
    
    # 清洗：移除内联样式、data-src、编辑者信息
    raw = re.sub(r' style="[^"]*"', '', raw)
    raw = re.sub(r' data-src="[^"]*"', '', raw)
    raw = re.sub(r'<p[^>]*>\s*(Editor:|Source:|Proofreader:).*?</p>', '', raw, flags=re.S)
    
    # 标准化 img 标签
    raw = re.sub(r'<img([^>]*)>', clean_img_tag, raw)
    
    return raw.strip()
```

#### 3.2.2 关键清洗规则

| 规则 | 目的 | 示例 |
|------|------|------|
| `style="[^"]*"` | 移除内联样式 | `style="text-align:center"` → 空 |
| `data-src="[^"]*"` | 移除微信懒加载属性 | 保留 `src` 主属性 |
| `Editor:/Source:/Proofreader:` | 移除编辑信息行 | 避免混入元数据 |
| `clean_img_tag()` | 标准化图片标签 | `<img src="url" alt="" loading="lazy">` |

#### 3.2.3 修复方法：栈深度遍历定位 div

**问题**：简单正则 `<div class="lang-content" data-lang="en">(.*?)</div>` 无法处理**嵌套 div**。

```python
# ❌ 错误：正则无法匹配嵌套
re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', content, re.S)
# 遇到嵌套 <div> 时，匹配会在第一个 </div> 处结束，导致内容截断

# ✅ 正确：栈深度遍历
def find_en_div_positions(content: str, after_pos: int = 0) -> tuple[int | None, int | None]:
    idx = content.find('<div class="lang-content" data-lang="en">', after_pos)
    if idx < 0:
        return (None, None)
    start = idx
    content_start = idx + len('<div class="lang-content" data-lang="en">')
    depth = 1
    p = content_start
    while depth > 0 and p < len(content):
        next_open = content.find('<div', p)
        next_close = content.find('</div>', p)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1      # 遇到内层 <div>，深度+1
            p = next_open + 4
        else:
            depth -= 1      # 遇到 </div>，深度-1
            if depth == 0:
                end = next_close + 6
                return (start, end)
            p = next_close + 6
    return (None, None)
```

**关键洞察**：HTML 是嵌套结构，必须用栈来跟踪 `div` 的开启/关闭匹配，而非贪婪或非贪婪正则。

### 3.3 有源文件 vs 无源文件的分别策略

#### 有源文件（16篇）：自动化重建

```
流程：源文件 → extract_en_html() → 清洗 → 替换 Hero EN (仅h1) + Body EN (全文)
```

- **Hero EN**：从提取的HTML中取第一个 `<h1>` 作为标题
- **Body EN**：完整替换为清洗后的英文内容

#### 无源文件（8篇）：手动修复 + 脚本辅助

| 文件 | 问题 | 修复方式 |
|------|------|----------|
| `altitude-sickness-tips` | EN hero含全篇内容 | `fix_all_heroes.py` 缩短为仅h1 |
| `bianba-motorcycle-diary` | EN hero含全篇内容 | `fix_all_heroes.py` 缩短为仅h1 |
| `may-day-tibet-lazy-guide` | EN hero含全篇内容 + 中文混入 | `fix_all_heroes.py` + `apply_diff` 逐行修复 |
| `motorcycle-healing-journey` | EN hero含全篇内容 | `fix_all_heroes.py` |
| `motorcycle-tibet-gear-guide` | EN hero含全篇内容 | `fix_all_heroes.py` |
| `motorcycle-tibet-shannan` | EN hero含全篇内容 | `fix_all_heroes.py` |
| `sichuan-tibet-central-route` | EN hero含全篇内容 + 中文混入 | `fix_all_heroes.py` + `apply_diff` |
| `wheels-shackles-tibet` | EN hero含全篇内容 + 中文混入 | `fix_all_heroes.py` + `apply_diff` |

---

## 四、deep_audit.py 误报识别与阈值调整

### 4.1 原始误报类型

#### 误报1：嵌套div匹配错误（已修复）

```python
# ❌ 原始代码
zh_blocks = re.findall(r'<div class="lang-content" data-lang="zh">(.*?)</div>', content, re.S)
en_blocks = re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', content, re.S)
```

**影响**：EN block 被截断，实际内容落入 ZH block 匹配范围内，导致 "Chinese in EN" 误报。

**修复**：见 3.2.3 `extract_blocks_safe()` 栈深度遍历。

#### 误报2：EN hero 长度检查阈值过严

```python
# ❌ 原始阈值
if len(en_hero_text) > len(zh_hero_text) * 3:
    issues.append(f"EN hero much longer than ZH hero")

# 示例：ZH标题 "黄色的狼性" (5字) vs EN标题 "The Yellow Wolf: Essential Tips..." (56字符)
# 56 > 5 * 3 = 15 → 误报！
```

**根因**：英文标题自然比中文长（字符数），但语义内容相同。例如：
- ZH: "第一次去西藏旅行？看这篇就够了！"（16字）
- EN: "First Time in Tibet? This Guide Has Everything You Need!"（56字符）

**修复策略**：将阈值从 `3x` 调整为**绝对长度阈值**（>200字符视为结构损坏）

```python
# ✅ 修复后
if len(en_hero_text) > 200:
    issues.append(f"EN hero suspiciously long ({len(en_hero_text)} chars)")
```

**判断逻辑**：正常 EN hero 仅含 `<h1>` 标题，通常 <100字符。>200字符说明有图片或正文被错误插入。

#### 误报3：地名括号中文标注被误报

```python
# 旅游文章中常见的双语标注：
"Shannan (山南) — the true cradle of Tibetan culture"
"Yalong (雅砻), the birthplace of Tibetan civilization"
"Nyenchen Tanglha (念青唐古拉山), one of Tibet's four sacred mountains"
```

**修复**：在 `find_chinese_in_en()` 中增加括号中文过滤

```python
def find_chinese_in_en(block):
    text = re.sub(r'<[^>]+>', ' ', block)
    text = html.unescape(text)
    # 移除括号内的中文地名标注
    text = re.sub(r'\([\u4e00-\u9fff\s·]+\)', '', text)
    # ... 后续检测
```

### 4.2 Audit 检查项矩阵

| 检查项 | 逻辑 | 阈值 | 修复状态 |
|--------|------|------|----------|
| EN hero 过长 | 纯文本长度 > 200 | 200 chars | ✅ 已修复 |
| EN hero 含中文 | `find_chinese_in_en()` 返回非空 | 排除括号标注 | ✅ 已修复 |
| 图片数量不匹配 | `count_imgs(en_body) != count_imgs(zh_body)` | 严格相等 | ✅ 已修复 |
| EN body 含中文 | `find_chinese_in_en()` 返回非空 | 排除括号标注 | ✅ 已修复 |
| EN title 含中文 | `has_chinese()` 检测 EN hero h1 | 零容忍 | ✅ 已修复 |
| Block 数量不匹配 | `len(en_blocks) != len(zh_blocks)` | 严格相等 | ✅ 已修复 |

---

## 五、验证流程设计

### 5.1 三层验证架构

```
第一层：validate_html.py
  └── 目标：HTML标签闭合、嵌套正确
  └── 方法：HTMLParser 栈追踪
  └── 通过标准：0 errors, 0 unclosed tags

第二层：deep_audit.py
  └── 目标：双语内容一致性
  └── 方法：栈深度遍历提取 + 文本分析
  └── 通过标准：0 issues

第三层：scan_image_text_separation.py
  └── 目标：EN body 图片-文字分布对齐
  └── 方法：检测 img 与 text 标签的相对位置
  └── 通过标准：0 files with separation issues
```

### 5.1a 图片分布检查（新增）

**问题模式**：`images_at_start` — 所有 `<img>` 连续堆在 EN body 开头，`<p>`/`<h2>` 等文本全部排在末尾，形成 "img-wall + text-wall"，与 ZH body 的交错分布（`img → text → img → text`）严重不符。

**检测逻辑**：
```python
last_img_pos = max(img.start() for img in en_imgs)
first_text_pos = min(text.start() for text in en_text_tags)
if last_img_pos < first_text_pos:
    issue = "images_at_start"  # 图片全部在文本之前
```

**触发场景**：
- `fix_en_body_images_from_zh.py` 早期版本将图片全部 prepend 到文本前
- 批量重建 EN body 后未执行分布对齐
- 手动编辑时不小心将图片集中到某一段落

### 5.2 validate_html.py 设计要点

```python
class HTMLValidator(HTMLParser):
    self_closing = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    
    def handle_starttag(self, tag, attrs):
        if tag not in self.self_closing:
            self.stack.append(tag)
    
    def handle_endtag(self, tag):
        if tag in self.self_closing:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"Unexpected closing </{tag}>")
```

**关键设计**：
1. **自关闭标签白名单**：`img`, `br`, `input` 等不需要 `</tag>`
2. **栈匹配**：严格检查 LIFO 顺序，`<div><p></div></p>` 会被捕获
3. **未关闭标签**：运行结束后栈非空，报告未关闭标签

### 5.3 验证执行顺序

```bash
# Step 1: 每次文件修改后立即运行
python scripts/validate_html.py
# → All HTML files validated successfully.

# Step 2: 验证通过后再运行
python scripts/deep_audit.py
# → Files with issues: 0
```

**强制规则**：任何修改后必须通过两层验证，否则禁止提交。

---

## 六、规范化操作手册

### 6.1 批量重建流程（有源文件）

```bash
# 1. 准备 FILE_MAP（slug → 源文件前缀映射）
# 2. 运行重建脚本
python scripts/rebuild_en_from_source.py
# 3. 检查日志
# 4. 运行三层验证
python scripts/validate_html.py
python scripts/deep_audit.py
python scripts/scan_image_text_separation.py
```

### 6.1a EN Body 图片分布修复流程（新增）

**前置条件**：`scan_image_text_separation.py` 报告 `images_at_start` 或 `images_at_end`

```bash
# Step 1: 扫描确认问题文件列表
python scripts/scan_image_text_separation.py

# Step 2: 将问题文件加入 fix_en_image_distribution.py TARGET_FILES
# Step 3: 执行修复
python scripts/fix_en_image_distribution.py

# Step 4: 重新扫描确认归零
python scripts/scan_image_text_separation.py
# → Found 0 files with image-text separation issues

# Step 5: 运行完整三层验证
python scripts/validate_html.py && python scripts/deep_audit.py
```

**修复算法**：
1. 读取 ZH body 中每张图片前的文本节点数（`text_tokens_before_img`）
2. 移除 EN body 中所有图片，得到纯文本流
3. 按 ZH 的文本节点比例，在 EN 文本流中定位插入点
4. 插入 EN 图片（保留全部原始属性：src, alt, loading）

**关键约束**：
- 图片总数不变
- 图片属性不变
- 仅改变插入位置
- 严格按 ZH 分布模式对齐

### 6.2 无源文件修复流程

```bash
# 1. 运行 hero 修复脚本（缩短 EN hero 为仅h1）
python scripts/fix_all_heroes.py

# 2. 运行图片同步脚本（ZH → EN 图片复制）
python scripts/fix_en_body_images_from_zh.py

# 3. 手动修复中文混入（apply_diff 逐行替换）
#    - 搜索正则: [\u4e00-\u9fff]+ 
#    - 限制范围: EN body 区块内

# 4. 运行双重验证
python scripts/validate_html.py && python scripts/deep_audit.py
```

### 6.3 中文混入修复规范

**检测方法**：
```bash
# 在EN body中搜索中文字符
grep -rP "[\x{4e00}-\x{9fff}]" articles/*.html
```

**修复优先级**：
1. **高优先级**：纯中文句子/段落（如 "走过路过不要错过"）
2. **中优先级**：中英混合词组（如 "自带治愈性舒缓解压"）
3. **低优先级**：地名括号标注（如 "Shannan (山南)"）— 允许保留

**翻译原则**：
- 保持原文语义
- 适配旅游语境
- 保留HTML标签结构

### 6.4 图片同步规范

```python
def sync_images(zh_block: str, en_block: str) -> str:
    """
    将ZH block中的图片按相同顺序插入EN block
    """
    zh_imgs = re.findall(r'<img[^>]*>', zh_block, re.I)
    en_imgs = re.findall(r'<img[^>]*>', en_block, re.I)
    
    if len(en_imgs) < len(zh_imgs):
        # 需要补全图片
        # 策略：按章节分布（h2/h3/h4 分割点）
        pass
    elif len(en_imgs) > len(zh_imgs):
        # 需要删除多余图片
        # 策略：从末尾删除
        pass
```

---

## 七、CI检查规则建议

### 7.1 推荐的 GitHub Actions 工作流

```yaml
name: Bilingual Content Check

on:
  push:
    paths:
      - 'articles/**.html'
  pull_request:
    paths:
      - 'articles/**.html'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install beautifulsoup4
      
      - name: HTML Structure Validation
        run: python scripts/validate_html.py
      
      - name: Bilingual Consistency Audit
        run: python scripts/deep_audit.py
      
      - name: Check audit results
        run: |
          if grep -q "Files with issues: [1-9]" scripts/deep_audit_results.txt; then
            echo "❌ Audit failed! Check scripts/deep_audit_results.txt"
            cat scripts/deep_audit_results.txt
            exit 1
          fi
          echo "✅ All checks passed!"
```

### 7.2 预提交钩子（Pre-commit Hook）

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: html-validate
        name: HTML Structure Validation
        entry: python scripts/validate_html.py
        language: system
        files: ^articles/.*\.html$
        pass_filenames: false
      
      - id: bilingual-audit
        name: Bilingual Consistency Audit
        entry: python scripts/deep_audit.py
        language: system
        files: ^articles/.*\.html$
        pass_filenames: false
```

### 7.3 检查规则清单

| 规则 | 触发条件 | 严重级别 | 自动修复 |
|------|----------|----------|----------|
| HTML标签闭合 | 任何HTML修改 | 🔴 阻断 | ❌ |
| EN/ZH block数量匹配 | 任何文章修改 | 🔴 阻断 | ❌ |
| EN body图片数量 = ZH body | 任何文章修改 | 🔴 阻断 | ✅ 可脚本化 |
| EN body图片分布对齐 | 任何文章修改 | 🟡 警告 | ✅ 可脚本化 |
| EN hero长度 < 200 | 任何文章修改 | 🟡 警告 | ✅ 可脚本化 |
| EN body无中文混入 | 任何文章修改 | 🔴 阻断 | ❌ |
| EN title无中文 | 任何文章修改 | 🔴 阻断 | ❌ |

**EN body图片分布对齐说明**：
- 检测 `images_at_start`（所有 img 在文本之前）或 `images_at_end`（所有 img 在文本之后）
- 脚本：`scan_image_text_separation.py`
- 修复：`fix_en_image_distribution.py`（按 ZH body 文本节点比例重分布）
- 通过标准：`Found 0 files with image-text separation issues`

---

## 八、技术决策记录（ADR）

### ADR-001：使用栈深度遍历替代正则匹配嵌套 div

**背景**：`re.findall(r'<div class="lang-content" data-lang="en">(.*?)</div>', re.S)` 无法正确匹配嵌套 div。

**决策**：使用栈深度遍历（`find_en_div_positions()`）精确定位 div 边界。

**后果**：
- ✅ 正确匹配嵌套结构
- ✅ 避免误报 "Chinese in EN"
- ⚠️ 性能略低于正则（O(n) vs 近似O(n)，但常数更大）

### ADR-002：从源文件 `div#english_translation` 重建 EN 内容

**背景**：原生成脚本仅用 `meta["excerptEn"]` 填充 EN body。

**决策**：从源 HTML 的 `div#english_translation` 提取完整英文翻译。

**替代方案考虑**：
- 方案A：手动翻译每篇文章 → ❌ 工作量过大（24篇）
- 方案B：使用机器翻译API → ❌ 质量不可控
- 方案C：从源文件提取 → ✅ 已有现成翻译

### ADR-003：Hero EN 仅保留 `<h1>`

**背景**：修复前 EN hero 被错误插入全篇内容+图片。

**决策**：EN hero 严格限制为 `<div class="lang-content" data-lang="en"><h1 class="article-hero__title">{title}</h1></div>`。

**理由**：Hero 区域仅用于展示标题，正文应在 `article-body` 中。

### ADR-004：允许地名括号双语标注

**背景**：旅游文章中地名常带中文标注（如 "Shannan (山南)"）。

**决策**：在 `find_chinese_in_en()` 中过滤 `\([\u4e00-\u9fff\s·]+\)` 模式。

**理由**：括号内中文是标准的地名注释，非混入内容。

### ADR-005：EN Body 图片按 ZH 文本节点比例重分布

**背景**：`fix_en_body_images_from_zh.py` 早期版本将图片全部 prepend 到 EN body 开头，导致 `img-wall + text-wall` 结构，与 ZH body 的交错分布严重不符。

**决策**：
1. 新增 `scan_image_text_separation.py` 检测分离问题
2. 新增 `fix_en_image_distribution.py` 按 ZH body 文本节点比例重分布 EN 图片

**算法**：
```python
# 读取 ZH 分布：每张图片前的文本节点数
zh_dist = [(img_tag, text_tokens_before) for each_img_in_zh]

# 提取 EN 纯文本，移除所有图片
en_text_only = remove_imgs(en_block)

# 按比例映射插入点
for i, (img, zh_before) in enumerate(zh_dist):
    ratio = zh_before / zh_total_text
    en_idx = int(ratio * len(en_tokens))
    insert_img_at(en_text_only, en_tokens[en_idx], img)
```

**约束**：
- 图片总数不变
- 图片属性不变（src, alt, loading）
- 仅改变插入位置
- 严格按 ZH 分布模式对齐

**后果**：
- ✅ 修复后 9 篇文件全部通过 `scan_image_text_separation.py`（0 issues）
- ✅ HTML 结构和双语一致性均不受影响
- ⚠️ 需作为 CI 检查项纳入（ADR-005 后续）

---

## 九、脚本优化清单

### 9.1 已完成的优化

| 脚本 | 优化项 | 效果 |
|------|--------|------|
| `rebuild_en_from_source.py` | 修复 `style` lambda 返回类型 | 消除 Pylance 类型错误 |
| `rebuild_en_from_source.py` | 修复 `after_pos` 类型注解 | 支持 `int \| None` |
| `rebuild_en_from_source.py` | 修复 `&` → `&` 替换 | 防止HTML实体破坏 |
| `deep_audit.py` | 替换正则匹配为栈深度遍历 | 消除嵌套div误报 |
| `deep_audit.py` | 增加括号中文过滤 | 消除地名标注误报 |
| `deep_audit.py` | 调整 hero 长度阈值 (3x → 200 chars) | 消除自然长度差异误报 |

### 9.2 建议的未来优化

1. **增量检查**：仅检查修改过的文件，而非全部24篇
2. **并行处理**：使用 `multiprocessing` 并行处理多文件
3. **配置化**：将 FILE_MAP、阈值等提取为 YAML/JSON 配置文件
4. **单元测试**：为 `find_en_div_positions()`、`extract_blocks_safe()` 编写单元测试
5. **Diff报告**：生成 HTML diff 报告便于人工审核
6. **图片Alt检测**：验证 EN/ZH 图片 `alt` 属性是否正确

---

## 十、最佳实践与维护指南

### 10.1 文章生成规范

```
源文件 → convert_articles_v2.py → articles/
                ↓
        [必须修复] EN body 不再使用 excerptEn
                ↓
        从 div#english_translation 提取完整翻译
```

### 10.2 修改前检查清单

- [ ] 备份目标文件
- [ ] 确认修改范围（Hero / Body / 两者）
- [ ] 运行 `validate_html.py`
- [ ] 运行 `deep_audit.py`
- [ ] 运行 `scan_image_text_separation.py`
- [ ] 确认修改后再次运行三层验证
- [ ] 抽查关键文件（如 `qingming-tibet-travel-guide.html`）

### 10.3 常见问题排查

| 症状 | 可能原因 | 排查方法 |
|------|----------|----------|
| EN页面内容缺失 | `excerptEn` 仅填充摘要 | 检查EN body字符数 |
| EN hero含图片/正文 | 脚本误插入 | 检查EN hero img标签数 |
| ZH/EN图片数不等 | 重建后未同步图片 | 运行 `fix_en_body_images_from_zh.py` |
| audit报Chinese in EN | 嵌套div匹配错误 | 检查 `extract_blocks_safe()` |
| audit报hero过长 | 阈值过严或真损坏 | 检查hero纯文本长度 |

### 10.4 新增文章流程

```
1. 准备源文件（含中英文）
2. 更新 FILE_MAP（如有源文件）
3. 运行 convert_articles_v2.py
4. [关键] 运行 rebuild_en_from_source.py 重建EN
5. 运行 validate_html.py
6. 运行 deep_audit.py
7. 修复任何问题
8. 更新 articles/index.html 列表
9. 提交并验证
```

---

## 附录：关键脚本源码索引

| 脚本 | 路径 | 核心函数 | 用途 |
|------|------|----------|------|
| `rebuild_en_from_source.py` | `scripts/rebuild_en_from_source.py` | `extract_en_html()`, `find_en_div_positions()`, `fix_article()` | 从源文件重建 EN 区块 |
| `deep_audit.py` | `scripts/deep_audit.py` | `extract_blocks_safe()`, `find_chinese_in_en()` | 双语一致性扫描 |
| `validate_html.py` | `scripts/validate_html.py` | `HTMLValidator` 类 | HTML 结构校验 |
| `fix_en_body_images_from_zh.py` | `scripts/fix_en_body_images_from_zh.py` | `insert_imgs_into_en()` | ZH → EN 图片数量同步 |
| `final_comprehensive_fix.py` | `scripts/final_comprehensive_fix.py` | Hero缩短 + 图片去重 | 综合修复 |
| `scan_image_text_separation.py` | `scripts/scan_image_text_separation.py` | `analyze_distribution()` | 检测 EN body 图片-文字分离 |
| `fix_en_image_distribution.py` | `scripts/fix_en_image_distribution.py` | `fix_file()` | 按 ZH 模式重分布 EN 图片 |

### 脚本依赖关系

```
articles/*.html
    ├── scan_image_text_separation.py   → 检测 img-wall/text-wall 问题
    ├── fix_en_image_distribution.py    → 按 ZH 比例重分布 EN 图片
    ├── validate_html.py                → HTML 标签闭合校验
    └── deep_audit.py                   → 双语内容一致性校验
```

### 新增文章完整流程（含图片分布校验）

```
1. 生成 articles/*.html
2. rebuild_en_from_source.py          → 重建 EN 内容
3. fix_en_body_images_from_zh.py      → 同步图片数量
4. scan_image_text_separation.py      → 检测图片分布 → 0 issues
5. validate_html.py                   → HTML 结构 → All pass
6. deep_audit.py                      → 双语一致性 → 0 issues
7. git commit & push
```

---

> **文档维护**：每次重大修复后更新本文档  
> **审核人**：技术负责人  
> **有效期**：与项目生命周期一致
