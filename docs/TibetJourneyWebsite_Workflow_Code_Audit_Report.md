# TibetJourneyWebsite 内容发布工作流 — 深度代码审查与优化建议

> **版本**: v1.0  
> **日期**: 2026-04-29  
> **审计范围**: `scripts/` 目录下全部 22+ 脚本  
> **审计维度**: 冗余性、脆弱性、可维护性、扩展性、错误处理、自动化程度

---

## 一、审计摘要（Executive Summary）

当前工作流是**典型的"脚本考古层"（Script Archaeology）**——通过不断叠加新脚本来修复旧脚本的问题，导致：

- **22+ 个脚本**管理 24 篇文章的发布流程
- **同一功能存在 3-4 个版本**（如图片同步有 `fix_en_body_images.py` / `v2` / `v3` / `bs` 四个变体）
- **核心算法（栈深度遍历）在 6 个脚本中重复实现**
- **文章元数据硬编码在 5+ 个 Python 字典中**，无任何集中配置
- **无统一入口、无依赖管理、无回滚机制、无 CI 集成**

本报告按严重程度分级列出问题，并提供**可落地的重构路线图**。

---

## 二、问题分级总览

| 严重级别 | 数量 | 类别 |
|----------|------|------|
| 🔴 P0 - 阻断级 | 6 | 数据安全风险、隐式破坏、无回滚 |
| 🟠 P1 - 高风险 | 8 | 脆弱正则、顺序依赖陷阱、重复造轮子 |
| 🟡 P2 - 中风险 | 5 | 配置分散、错误处理缺失、可扩展性 |
| 🟢 P3 - 低风险 | 4 | 命名规范、代码组织、文档缺失 |

---

## 三、P0 阻断级问题

### P0-1: 原地文件覆写，无任何备份/回滚机制

**影响范围**: 几乎所有脚本

**问题描述**:

```python
# rebuild_en_from_source.py:141
with open(article_path, 'w', encoding='utf-8') as f:
    f.write(content)

# fix_en_image_distribution.py:143
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
```

所有脚本均直接覆写原文件，**没有临时文件、没有备份、没有原子写入**。一旦脚本逻辑出错（如正则匹配到错误位置），成品文件会被永久破坏。

**实际案例**: `fix_image_counts.py` 使用 `BeautifulSoup` 解析后再做 `raw.replace()`，若 BS 重新格式化了 HTML（如自闭合标签 `<img>` → `<img/>`），`replace()` 将失败或匹配错误内容，导致文件写入不完整。

**修复建议**:

```python
import tempfile
import shutil

def atomic_write(path, content):
    """Atomic file write with backup."""
    backup = path + '.backup'
    shutil.copy2(path, backup)  # Create backup
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        shutil.move(tmp, path)  # Atomic move
    except:
        shutil.move(backup, path)  # Rollback on failure
        raise
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
```

---

### P0-2: `rebuild_en_from_source.py` 的 `&` 替换会破坏 URL

**问题代码**:

```python
# rebuild_en_from_source.py:63
raw = raw.replace('&', '&')
```

这行代码意图修复 HTML 实体，但**它会把所有 `&` 替换为 `&`**，包括 URL 查询参数中的 `&`：

```
https://example.com?a=1&b=2  →  https://example.com?a=1&b=2
```

**修复建议**: 仅替换作为 HTML 实体一部分的 `&`：

```python
import html as html_module
raw = html_module.escape(html_module.unescape(raw))  # 标准化实体
```

---

### P0-3: `fix_remaining_cn.py` 的硬编码替换可能误伤

**问题代码**:

```python
# fix_remaining_cn.py
fixes = {
    "g216-coqen-blue-dream.html": [
        ("拉琼拉垭口", ""),  # 直接替换为空字符串，可能破坏上下文
    ],
}
```

无上下文验证的 `str.replace()` 可能误替换（例如 `"拉琼拉垭口"` 作为地名出现在正文中的正确位置）。

**修复建议**: 使用带上下文窗口的替换，或要求人工确认后再写入。

---

### P0-4: `fix_image_counts.py` 的 BS + 字符串替换混合模式

**问题代码**:

```python
# fix_image_counts.py
new_en_html = str(en_div)  # BS 可能重新格式化
old_en_html_match = re.search(r'<div class="lang-content" data-lang="en">.*?</div>', raw, re.S)
raw = raw.replace(old_en_html_match.group(0), new_en_html)  # 可能匹配不到
```

`BeautifulSoup` 的 `str()` 输出与原始 HTML 的格式可能不同（属性顺序、引号、自闭合标签），导致 `replace()` 静默失败。

**修复建议**: 全程使用 BS 处理 DOM，或全程使用字符串替换，不要混合。

---

### P0-5: `deep_audit.py` 的正则标题提取未使用栈遍历

**问题代码**:

```python
# deep_audit.py:150
 title_en = re.search(r'<div class="lang-content" data-lang="en">.*?<h[123][^>]*>(.*?)</h[123]>', content, re.S)
```

标题提取使用非贪婪正则 `.*?`，在 EN Hero 含嵌套标签时可能匹配到错误的闭合标签。虽然当前数据可能未触发，但结构变化后会误报。

**修复建议**: 标题提取也应使用栈遍历或 `BeautifulSoup`。

---

### P0-6: `convert_articles_v2.py` 中 `en_html = f'<p>{meta["excerptEn"]}</p>'` 是设计级缺陷

**根因**: 初始生成脚本故意产出半成品（EN Body 只有一句话摘要），导致后续必须运行 4-5 个修复脚本才能产出生成物。这是**工作流设计上的根本错误**。

**修复建议**: 初始生成即尝试从源文件提取英文内容；若无英文翻译，应标记为 `needs_translation` 而非产出占位数据。

---

## 四、P1 高风险问题

### P1-1: 栈深度遍历算法在 6 个脚本中重复实现

**重复出现的代码**（逐字符复制，仅变量名不同）：

| 脚本 | 函数名 | 行数 |
|------|--------|------|
| `rebuild_en_from_source.py` | `find_en_div_positions()` | 67-89 |
| `deep_audit.py` | `extract_blocks_safe()` | 30-61 |
| `fix_en_image_distribution.py` | `extract_en_div()` / `extract_zh_div()` | 16-69 |
| `fix_en_body_images_from_zh.py` | `extract_body_block()` | 6-40 |
| `scan_image_text_separation.py` | `extract_body_block()` | 14-44 |
| `final_comprehensive_fix.py` | `find_en_div_positions()` / `extract_body_block()` | 6-59 |

**问题**: 任何对解析逻辑的改进（如处理 `<section>` 嵌套、处理自闭合 `<div/>`）需要在 6 个地方同步修改，维护成本指数级增长。

**修复建议**: 提取为共享库模块：

```python
# scripts/lib/html_parser.py
def extract_lang_block(html: str, lang: str, after_pos: int = 0, within_body: bool = False) -> str | None:
    """Extract lang-content block with stack-based nested div handling."""
    ...
```

---

### P1-2: 文章映射字典在 5+ 个脚本中重复硬编码

**重复配置**:

| 脚本 | 字典名 | 键值对数 |
|------|--------|----------|
| `convert_articles_v2.py` | `ARTICLES_META` | 12 |
| `rebuild_en_from_source.py` | `FILE_MAP` | 16 |
| `fix_mixed_lang.py` | `SLUG_TO_PATTERN` | 17 |
| `fix_en_content.py` | `SLUG_TO_PATTERN` | 17 |
| `fix_all_heroes.py` | `TITLE_MAP` | 24 |
| `final_comprehensive_fix.py` | `TITLE_FIXES` | 5 |
| `extract_covers.py` | 硬编码列表 | 12 |
| `extract_og_covers.py` | 硬编码列表 | 12 |

**问题**: 新增一篇文章需要修改 5+ 个文件。修改作者/标题等元数据需要在多个地方同步。

**修复建议**: 统一为 `articles.yaml` 或 `articles.json`：

```yaml
# config/articles.yaml
articles:
  - slug: first-tibet-trip-guide
    source_pattern: "第一次去西藏旅行看这篇就够了"
    title_zh: "第一次去西藏旅行？看这篇就够了！"
    title_en: "First Time in Tibet? This Guide Has Everything You Need!"
    has_en_translation: true
    category: travel-guide
    author_zh: "小卓玛"
    author_en: "Xiao Zhuoma"
    date: "2026-02-20"
```

---

### P1-3: `fix_en_content.py` 与 `fix_mixed_lang.py` 几乎完全相同

**对比**:

| 维度 | `fix_en_content.py` | `fix_mixed_lang.py` |
|------|--------------------|--------------------|
| `SLUG_TO_PATTERN` | ✅ 存在 | ✅ 存在（相同内容） |
| `extract_en_from_html()` | ✅ 存在 | ✅ 存在（逻辑几乎相同） |
| `extract_en_from_md()` | ✅ 存在 | ✅ 存在（相同） |
| `find_source_files()` | ✅ 存在 | ✅ 存在 |
| `patch_article()` | ✅ 正则替换 | ✅ 正则替换（更复杂） |
| `render_blocks()` | ✅ 存在 | ❌ 内联 |
| 中文过滤阈值 | 无 | `chinese_ratio > 0.3` |

两者都是从源文件提取英文并修补 `articles/` 中的 EN block，只是 `fix_mixed_lang.py` 增加了中文比例过滤。这本质上是**同一功能的两份实现**。

**修复建议**: 合并为统一的 `extract_en_from_source()` 模块，通过参数控制过滤策略。

---

### P1-4: 图片同步/修复脚本的版本爆炸

当前存在以下处理图片的脚本：

| 脚本 | 用途 | 状态 |
|------|------|------|
| `fix_en_body_images_from_zh.py` | 按章节分布插入 ZH 图片到 EN | 主版本 |
| `fix_en_body_images_v2.py` | 同上，算法微调 | 废弃？ |
| `fix_en_body_images_v3.py` | 同上，算法微调 | 废弃？ |
| `fix_en_images_bs.py` | 使用 BeautifulSoup 版本 | 废弃？ |
| `fix_en_image_distribution.py` | 修复 `img-wall` 分布 | 活跃 |
| `fix_image_counts.py` | 删除 EN 多余图片 | 活跃 |
| `final_comprehensive_fix.py` | 综合修复（含图片去重） | 活跃 |

**问题**: 这 7 个脚本解决的是同一个问题（EN Body 图片管理），但因早期版本有缺陷（产生 `img-wall`），不得不叠加新脚本修复。版本之间没有清晰的演进关系或废弃标记。

**修复建议**: 统一为单一 `sync_images()` 模块，一步到位正确插入图片，无需后续修复。

---

### P1-5: `convert_articles_v2.py` 的 `related` 文章硬编码

**问题代码**:

```python
related = [
    {'img': 'https://mmbiz.qlogo.cn/...', 'url': 'altitude-sickness-tips.html', 'title': '黄色的狼性 —— 关于摩旅高反需要注意事项'},
    # ... 固定 4 篇
]
```

所有文章都显示相同的 4 篇相关文章，与当前文章主题无关。

**修复建议**: 按分类/标签动态匹配，或从配置读取每篇文章的相关推荐。

---

### P1-6: `fix_en_image_distribution.py` 的硬编码 `TARGET_FILES`

**问题代码**:

```python
TARGET_FILES = [
    'articles/altitude-sickness-tips.html',
    'articles/bianba-motorcycle-diary.html',
    # ... 固定 9 篇
]
```

新问题文件必须手动加入列表，无法自动发现。

**修复建议**: 直接调用 `scan_image_text_separation.py` 的检测逻辑，自动发现需要修复的文件。

---

### P1-7: 正则匹配 `lang-content` div 的陷阱

**问题代码**:

```python
# fix_en_content.py:162
en_match = re.search(r'<div class="lang-content" data-lang="en">\s*(.*?)\s*</div>', html, re.DOTALL)

# fix_mixed_lang.py:159
match = re.search(r'(<div class="article-body">.*?<div class="lang-content" data-lang="en">)(.*?)(</div>.*?</div>\s*<nav class="article-nav">)', html, re.DOTALL)
```

非贪婪正则 `.*?` 遇到嵌套 `<div>` 时会提前结束匹配。虽然实际 HTML 中 EN block 内部可能没有嵌套 `div`，但结构变化后（如添加 `<div class="caption">`）会立即触发 bug。

**修复建议**: 统一使用栈深度遍历提取 block，禁止在核心逻辑中使用正则匹配嵌套结构。

---

### P1-8: `scan_mixed_lang.py` 的正则扫描同样脆弱

**问题代码**:

```python
# scan_mixed_lang.py:31
pattern = rf'<div class="lang-content" data-lang="{lang}">(.*?)</div>'
matches = list(re.finditer(pattern, content, re.DOTALL))
```

与 P1-7 相同的问题：用正则匹配嵌套 `div`。

---

## 五、P2 中风险问题

### P2-1: 无集中配置系统

当前配置分散在 Python 常量中，无法被非技术人员编辑，也无法被脚本间共享。

**修复建议**: 引入 `config/articles.yaml` 或 `pyproject.toml` 作为单一事实来源。

---

### P2-2: 错误处理过于粗糙

**典型模式**:

```python
if not en_html:
    log.append(f"{slug}.html: No EN translation found")
    continue  # 静默跳过
```

脚本遇到异常时只是打印日志并跳过，**不返回非零退出码**，导致 CI 无法检测失败。

**修复建议**: 使用 `sys.exit(1)` 标记失败，或返回结构化结果供调用方判断。

---

### P2-3: `final_verify.py` 的 `SKIP_EN_WORDS` 是灾难性的硬编码

**问题代码**:

```python
SKIP_EN_WORDS = {
    'png', 'jpg', ..., 'k', 'k', 'k', ..., 'chengdu', 'zigong', ...
    # 约 800+ 个硬编码单词
}
```

这个集合试图排除所有可能在中文 block 中出现的英文单词，但：
1. 维护成本极高
2. 仍会漏报（如旅游文章中常见的 "SUV", "GPS", "WiFi"）
3. 也会误报（如人名、品牌名本就不应翻译）

**修复建议**: 改为白名单策略——仅检测明显的中文混入模式（如完整中文句子），允许保留专有名词。

---

### P2-4: `inject_referrer_meta.py` 和 `inject_fouc_fix.py` 是补丁而非流程

这两个脚本一次性修改所有 HTML 文件添加 meta 标签，说明模板系统不完善——**新特性通过全站搜索替换添加**，而非更新模板后重新生成。

**修复建议**: 使用 Jinja2 模板引擎，模板修改后重新生成全部页面。

---

### P2-5: `articles/index.html` 完全依赖手动更新

文章列表页没有自动生成机制，每次新增文章需要手动复制粘贴 HTML 卡片代码。

**修复建议**: 从 `config/articles.yaml` 自动生成 `index.html`。

---

## 六、P3 低风险问题

### P3-1: 脚本命名不规范

存在多种命名风格：`fix_en_body_images_from_zh.py`（长描述）、`fix_mixed_lang.py`（短描述）、`final_verify.py`（无动词前缀）、`inject_fouc_fix.py`（重复动词）。

### P3-2: 无 `requirements.txt` 或依赖声明

项目使用 `beautifulsoup4` 但未声明版本，不同版本可能导致解析行为差异。

### P3-3: 无单元测试

所有脚本均为"运行一次"的手动工具，没有自动化测试覆盖核心解析逻辑。

### P3-4: 日志分散在多个文件中

`rebuild_en_log.txt`、`fix_all_heroes_log.txt`、`fix_en_body_images_log.txt`、`fix_en_body_images_log_v2.txt`... 日志分散且格式不统一。

---

## 七、重构路线图

### Phase 1: 紧急止血（1-2 天）

| 任务 | 优先级 | 操作 |
|------|--------|------|
| 原子写入 | P0 | 为所有写文件脚本添加 `atomic_write()` 包装 |
| 修复 `&` 替换 | P0 | 将 `raw.replace('&', '&')` 改为 `html.escape()` |
| 废弃旧脚本 | P1 | 删除 `fix_en_body_images_v2.py` / `v3.py` / `bs.py`，移动至 `scripts/archive/` |
| 统一日志 | P3 | 统一使用 `logging` 模块，输出到 `scripts/logs/YYYYMMDD_HHMMSS.log` |

### Phase 2: 提取共享库（2-3 天）

创建 `scripts/lib/` 目录：

```
scripts/
├── lib/
│   ├── __init__.py
│   ├── html_parser.py      # 栈深度遍历、block 提取
│   ├── article_config.py   # 读取 config/articles.yaml
│   ├── atomic_io.py        # 原子写入、备份
│   ├── en_extractor.py     # 从源文件提取英文（合并 fix_en_content + fix_mixed_lang + rebuild_en）
│   └── validators.py       # HTML 校验、双语审计、分布检查
```

### Phase 3: 统一配置（1 天）

```yaml
# config/articles.yaml
articles:
  - slug: first-tibet-trip-guide
    source_pattern: "第一次去西藏旅行看这篇就够了"
    title: { zh: "...", en: "..." }
    has_en_translation: true
    category: travel-guide
    author: { zh: "小卓玛", en: "Xiao Zhuoma" }
    date: "2026-02-20"
    related:
      - altitude-sickness-tips
      - motorcycle-tibet-gear-guide
```

### Phase 4: 主控脚本（2-3 天）

创建单一入口脚本，替代当前 7 阶段手动流程：

```python
# scripts/build.py
import click
from lib import article_config, en_extractor, validators, atomic_io

@click.command()
@click.option('--slug', help='Build specific article')
@click.option('--validate/--no-validate', default=True)
def build(slug, validate):
    """Build articles from source files."""
    articles = article_config.load()
    for art in articles:
        if slug and art.slug != slug:
            continue
        # 1. Generate from source
        # 2. Extract EN if available
        # 3. Sync images with correct distribution
        # 4. Validate
        # 5. Write atomically
```

### Phase 5: CI 集成（1 天）

```yaml
# .github/workflows/build.yml
- name: Build Articles
  run: python scripts/build.py --validate
- name: Audit
  run: python scripts/build.py --audit-only
```

---

## 八、脚本合并/拆分方案

### 合并建议

| 新模块 | 合并来源 | 理由 |
|--------|----------|------|
| `lib/en_extractor.py` | `rebuild_en_from_source.py` + `fix_en_content.py` + `fix_mixed_lang.py` | 均从源文件提取英文 |
| `lib/image_sync.py` | `fix_en_body_images_from_zh.py` + `fix_en_image_distribution.py` + `fix_image_counts.py` + `final_comprehensive_fix.py` | 均管理 EN Body 图片 |
| `lib/html_parser.py` | 所有脚本中的 `find_en_div_positions()` / `extract_blocks_safe()` / `extract_body_block()` | 统一的 DOM 提取 |
| `build.py` | 全部脚本 | 单一入口 |

### 拆分建议

| 现有脚本 | 拆分后 | 理由 |
|----------|--------|------|
| `convert_articles_v2.py` | `build.py`（主控）+ `templates/article.html`（Jinja2 模板） | 模板与逻辑分离 |
| `fix_remaining_cn.py` | 数据文件 `config/manual_fixes.yaml` + 通用替换脚本 | 修复规则与执行分离 |

### 废弃建议

| 脚本 | 状态 | 理由 |
|------|------|------|
| `fix_en_body_images_v2.py` | 🗑️ 废弃 | 被 v3 / bs 替代 |
| `fix_en_body_images_v3.py` | 🗑️ 废弃 | 被 `fix_en_image_distribution.py` 替代 |
| `fix_en_images_bs.py` | 🗑️ 废弃 | 实验性版本 |
| `extract_covers.py` | 🗑️ 废弃 | 一次性工具 |
| `extract_og_covers.py` | 🗑️ 废弃 | 一次性工具 |
| `inject_referrer_meta.py` | 🗑️ 废弃 | 一次性补丁 |
| `inject_fouc_fix.py` | 🗑️ 废弃 | 一次性补丁 |

---

## 九、自动化程度提升路径

```
当前状态: 7 阶段手动脚本串联，人工判断每一步是否通过
    ↓
目标状态: 单一命令 `python scripts/build.py` 完成全部流程
```

**关键自动化点**:

1. **自动发现源文件**: 通过 `glob('AddingArticleWorkSpace/1/*')` 自动匹配，无需 `FILE_MAP`
2. **自动检测 EN 可用性**: 检查 `div#english_translation` 是否存在，自动选择有源/无源策略
3. **自动图片分布**: 初始生成即按 ZH 比例分布 EN 图片，无需后续修复
4. **自动生成索引**: 从配置自动生成 `articles/index.html`
5. **自动验证门禁**: 构建失败时自动阻止写入，无需人工运行三层验证

---

## 十、检查清单（重构前 vs 重构后）

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| 脚本数量 | 22+ | 5（build + lib/*） |
| 配置文件 | 0（硬编码） | 1（articles.yaml） |
| 构建命令 | 7 个手动步骤 | 1 个命令 |
| 备份机制 | 无 | 原子写入 + 自动备份 |
| 错误处理 | 打印跳过 | 结构化异常 + 非零退出码 |
| CI 集成 | 无 | GitHub Actions |
| 模板系统 | f-string 硬编码 | Jinja2 模板 |
| 单元测试 | 0 | 核心解析函数覆盖 |

---

> **审计人**: AI Assistant  
> **建议有效期**: 与项目生命周期一致  
> **下次审计建议**: 重构完成后 2 周
