# TibetJourneyWebsite 内容发布工作流指南 v2

> **版本**: v2.0  
> **日期**: 2026-04-29  
> **适用范围**: 重构后的 scripts/ 目录  
> **状态**: 活跃

---

## 一、重构概览

本工作流基于代码审计报告进行了系统性重构，核心改进如下：

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| 脚本数量 | 34 | 7 (+ 5 lib modules) |
| 废弃脚本 | 0 | 29 (已归档至 `scripts/archive/`) |
| 核心算法复制 | 6 处栈遍历重复实现 | 统一至 `lib/html_parser.py` |
| 配置分散 | 5+ 个硬编码字典 | 统一至 `lib/article_config.py`（待迁移 YAML） |
| 文件写入 | 直接覆写，无备份 | 原子写入 + 自动备份/回滚 |
| 验证入口 | 3 个独立脚本手动运行 | 统一至 `build.py --validate` |
| HTML 实体 | `str.replace('&', '&')` 破坏 URL | 使用 `html.escape()` 安全处理 |

---

## 二、目录结构

```
TibetJourneyWebsite/
├── articles/                        # 成品文章页面（输出）
│   ├── index.html                   # 文章列表页（仍须手动更新）
│   └── *.html                       # 文章页面
├── AddingArticleWorkSpace/1/        # 源文件目录（输入）
├── scripts/                         # 工具脚本
│   ├── lib/                         # 共享库（NEW）
│   │   ├── __init__.py
│   │   ├── html_parser.py           # 统一 DOM 提取（栈深度遍历）
│   │   ├── atomic_io.py             # 原子写入 + 备份/回滚
│   │   ├── article_config.py        # 文章元数据配置中心
│   │   ├── en_extractor.py          # 英文内容提取（合并 3 个旧脚本）
│   │   └── validators.py            # 三层验证合一
│   ├── build.py                     # 统一入口（NEW）
│   ├── convert_articles_v2.py       # 初始生成（保留核心逻辑）
│   ├── rebuild_en.py                # EN 内容重建（合并 3 个旧脚本）
│   ├── sync_images.py               # 图片同步 + 分布修复（合并 4 个旧脚本）
│   ├── validate_html.py             # HTML 结构校验（重构）
│   ├── deep_audit.py                # 双语一致性审计（重构）
│   └── scan_image_text_separation.py # 图片分布检查（重构）
├── scripts/archive/                 # 废弃脚本归档（29 个）
├── css/                             # 样式文件
├── docs/                            # 文档（本文件所在目录）
│   ├── TibetJourneyWebsite_Workflow_Guide_v2.md      # 本指南
│   └── TibetJourneyWebsite_Workflow_Code_Audit_Report.md  # 审计报告
```

---

## 三、快速开始

### 3.1 单一命令构建（推荐）

```bash
cd scripts
python build.py --all
```

执行完整流水线：
1. 生成初始文章（`convert_articles_v2.py`）
2. 重建英文内容（`rebuild_en.py`）
3. 同步图片分布（`sync_images.py`）
4. 三层验证（HTML + Audit + Distribution）

### 3.2 分步构建

```bash
# Step 1: 生成文章
python scripts/convert_articles_v2.py

# Step 2: 重建英文（仅限有源文件的文章）
python scripts/rebuild_en.py

# Step 3: 同步图片（自动修复数量不匹配 + 分布问题）
python scripts/sync_images.py

# Step 4: 验证
python scripts/build.py --validate
```

### 3.3 单独验证

```bash
# 仅运行三层验证（不重新构建）
python scripts/build.py --validate

# 或分别运行：
python scripts/validate_html.py
python scripts/deep_audit.py
python scripts/scan_image_text_separation.py
```

### 3.4 单文章处理

```bash
# 仅重建指定文章的英文
python scripts/rebuild_en.py --slug first-tibet-trip-guide

# 仅同步指定文章的图片
python scripts/sync_images.py --slug first-tibet-trip-guide
```

---

## 四、脚本详解

### 4.1 统一入口：`build.py`

**用途**: 单一命令执行完整构建流水线或单独验证。

```bash
python scripts/build.py --all           # 完整流水线
python scripts/build.py --convert       # 仅生成
python scripts/build.py --rebuild       # 仅重建 EN
python scripts/build.py --sync          # 仅同步图片
python scripts/build.py --validate      # 仅验证
python scripts/build.py --all --slug <slug>  # 仅处理指定文章
```

**验证门禁**: 若任何一层验证失败，`build.py` 返回非零退出码，适合 CI 集成。

---

### 4.2 初始生成：`convert_articles_v2.py`

**用途**: 从微信公众号源 HTML 提取中文正文，生成初始文章页面。

**配置方式**: 修改 `scripts/lib/article_config.py` 中的 `_fallback_meta()`，或创建 `config/articles.json`。

**已知保留项**: 此脚本保留原始核心逻辑（BeautifulSoup 解析 + f-string 模板），因其功能稳定且重构成本较高。后续可通过 Jinja2 模板引擎进一步解耦（见 TODO）。

**修复项**:
- 英文 Body 仍使用 `excerptEn` 占位（设计约束：源文件 EN 翻译在后续 `rebuild_en.py` 阶段注入）
- 相关文章仍为硬编码 4 篇（待后续按分类动态匹配）

---

### 4.3 EN 重建：`rebuild_en.py`

**合并来源**: `rebuild_en_from_source.py` + `fix_en_content.py` + `fix_mixed_lang.py`

**用途**:
1. 从 `AddingArticleWorkSpace/1/*.html` 的 `div#english_translation` 提取完整英文翻译
2. 清洗内联样式、data-src、编辑者信息
3. Hero EN 缩短为仅 `<h1>`
4. Body EN 替换为完整翻译

**安全写入**: 使用 `lib/atomic_io.atomic_write()`，失败自动回滚。

**参数**:
```bash
python scripts/rebuild_en.py           # 全部有源文件的文章
python scripts/rebuild_en.py --strict  # 启用严格中文过滤
python scripts/rebuild_en.py --slug first-tibet-trip-guide
```

---

### 4.4 图片同步：`sync_images.py`

**合并来源**: `fix_en_body_images_from_zh.py` + `fix_en_image_distribution.py` + `fix_image_counts.py` + `final_comprehensive_fix.py`

**用途**: 一步完成图片数量同步 + 分布修复：
1. **数量修复**: EN 图片多于 ZH → 删除多余；EN 图片少于 ZH → 补充缺失
2. **分布修复**: 检测 `img-wall`（所有图片在文本前），按 ZH 文本节点比例重分布

**参数**:
```bash
python scripts/sync_images.py                      # 全部文章
python scripts/sync_images.py --no-fix-distribution # 仅同步数量，不修复分布
python scripts/sync_images.py --slug <slug>
```

---

### 4.5 三层验证

#### `validate_html.py` — HTML 结构校验

```bash
python scripts/validate_html.py
# → All HTML files validated successfully.
```

检查标签闭合、嵌套正确。使用 `HTMLParser` 栈追踪 + 自关闭标签白名单。

#### `deep_audit.py` — 双语一致性审计

```bash
python scripts/deep_audit.py
# → Files with issues: 0
```

**修复项**: 标题提取从脆弱正则改为使用 `lib/html_parser` 的栈遍历。

检查项：
- EN Hero 长度 > 200 chars
- EN Hero/Body 含中文（排除括号地名标注）
- ZH/EN 图片数量不匹配
- Block 数量不匹配
- EN 标题含中文

#### `scan_image_text_separation.py` — 图片分布检查

```bash
python scripts/scan_image_text_separation.py
# → Found 0 files with image-text separation issues
```

检测 `images_at_start` / `images_at_end` / `mostly_images_first` / `mostly_images_last`。

---

## 五、共享库（`scripts/lib/`）

### 5.1 `html_parser.py`

统一栈深度遍历，替代之前 6 个脚本中的重复实现。

```python
from lib import html_parser as hp

# 提取 EN body block（正确处理嵌套 div）
en_body = hp.extract_lang_block(content, 'en', within_body=True)

# 提取所有 ZH blocks
zh_blocks = hp.extract_all_lang_blocks(content, 'zh')

# 计数图片
n = hp.count_imgs(block_html)
```

### 5.2 `atomic_io.py`

原子文件写入，带自动备份和回滚。

```python
from lib import atomic_io

# 安全覆写（失败自动恢复原始文件）
atomic_io.atomic_write('articles/foo.html', new_content)

# 读取
content = atomic_io.read_file('articles/foo.html')
```

### 5.3 `article_config.py`

集中配置中心，统一返回文章元数据。

```python
from lib import article_config

articles = article_config.load_articles()        # 全部元数据
art = article_config.get_article_by_slug(articles, 'first-tibet-trip-guide')
file_map = article_config.build_file_map(articles)      # slug → source pattern
title_map = article_config.build_title_map(articles)    # slug → EN title
```

**TODO**: 当前使用内联 fallback dict。迁移至 `config/articles.yaml` 后，非技术人员可直接编辑配置。

### 5.4 `en_extractor.py`

英文内容提取，合并了 3 个旧脚本的提取逻辑。

```python
from lib import en_extractor

# 从 HTML 源文件提取英文
en_html = en_extractor.extract_from_html('source.html', strict_chinese_filter=False)

# 自动选择 HTML 或 MD 源文件
en_html, src_type = en_extractor.extract_en('AddingArticleWorkSpace/1', 'file_pattern')

# 从英文 HTML 提取标题
title = en_extractor.get_title_from_en_html(en_html)
```

**修复项**: `_normalize_html_entities()` 使用 `html.escape(html.unescape(raw))`，不再破坏 URL 中的 `&`。

### 5.5 `validators.py`

三层验证合一，提供统一 API。

```python
from lib import validators

# 单层
html_errors = validators.validate_all_articles('articles')
audit_issues = validators.audit_all_articles('articles')
dist_issues = validators.check_all_distributions('articles')

# 全部
results = validators.run_full_validation('articles')
```

---

## 六、新增文章完整流程

```bash
# 1. 准备源文件
#    └── 将微信公众号导出的 HTML 放入 AddingArticleWorkSpace/1/
#    └── 确认包含 div#english_translation（如有英文翻译）

# 2. 配置元数据
#    └── 编辑 scripts/lib/article_config.py → _fallback_meta()
#    └── 或创建 config/articles.json（未来优先方案）

# 3. 执行完整构建
python scripts/build.py --all

# 4. 检查结果
#    └── 三层验证全部通过（HTML + Audit + Distribution）
#    └── 如有失败，build.py 会输出具体问题

# 5. 更新文章列表页（仍须手动）
#    └── 编辑 articles/index.html 添加新文章卡片
#    └── TODO: 未来改为从配置自动生成

# 6. 提交
#    └── git add -A
#    └── git commit -m "content: add {slug} article"
```

---

## 七、已归档脚本（`scripts/archive/`）

以下 29 个脚本已废弃并移至归档目录，不再维护：

| 脚本 | 替代方案 | 归档原因 |
|------|----------|----------|
| `rebuild_en_from_source.py` | `rebuild_en.py` | 功能合并，无共享库 |
| `fix_en_content.py` | `rebuild_en.py` | 功能合并 |
| `fix_mixed_lang.py` | `rebuild_en.py --strict` | 功能合并 |
| `fix_en_body_images_from_zh.py` | `sync_images.py` | 功能合并，产生 img-wall 副作用 |
| `fix_en_body_images_v2.py` | `sync_images.py` | 废弃版本 |
| `fix_en_body_images_v3.py` | `sync_images.py` | 废弃版本 |
| `fix_en_images_bs.py` | `sync_images.py` | 实验性版本 |
| `fix_en_image_distribution.py` | `sync_images.py` | 功能合并 |
| `fix_image_counts.py` | `sync_images.py` | 功能合并 |
| `final_comprehensive_fix.py` | `sync_images.py` | 功能合并 |
| `fix_all_heroes.py` | `rebuild_en.py` | 功能合并 |
| `fix_remaining_cn.py` | `rebuild_en.py --strict` | 硬编码替换，维护困难 |
| `fix_remaining_mixed.py` | `rebuild_en.py --strict` | 同上 |
| `extract_covers.py` | 无（一次性工具） | 一次性运行 |
| `extract_og_covers.py` | 无（一次性工具） | 一次性运行 |
| `inject_referrer_meta.py` | 模板层处理 | 一次性补丁 |
| `inject_fouc_fix.py` | 模板层处理 | 一次性补丁 |
| `scan_mixed_lang.py` | `deep_audit.py` | 功能重复 |
| `scan_en_chinese.py` | `deep_audit.py` | 功能重复 |
| `scan_en_chinese_v2.py` | `deep_audit.py` | 废弃版本 |
| `scan_html_in_datalang.py` | `deep_audit.py` | 功能重复 |
| `scan_zh_english.py` | `deep_audit.py` | 功能重复 |
| `check_en_status.py` | `deep_audit.py` | 功能重复 |
| `final_verify.py` | `validators.run_full_validation()` | 功能重复，800+ 硬编码单词 |
| `fix_cn_in_en.py` | 无 | 废弃 |
| `clean_en_chinese.py` | 无 | 废弃 |
| `fix_hero_structure.py` | `rebuild_en.py` | 功能合并 |
| `convert_articles.py` | `convert_articles_v2.py` | 旧版本 |
| `fix_en_body_images.py` | `sync_images.py` | 旧版本 |

---

## 八、TODO 清单（待处理事项）

以下改进因缺少外部依赖或重构成本较高，暂保持现状，已在代码中标注 TODO：

| 优先级 | 事项 | 当前状态 | 阻塞原因 |
|--------|------|----------|----------|
| P1 | `config/articles.yaml` 集中配置 | `article_config.py` 已预留接口 | 缺少 PyYAML 依赖 |
| P1 | Jinja2 模板引擎 | `convert_articles_v2.py` 仍用 f-string | 模板迁移成本高 |
| P2 | 自动生成 `articles/index.html` | 仍须手动更新 | 需先完成 YAML 配置 |
| P2 | `convert_articles_v2.py` 使用共享库 | 保持原有逻辑 | 核心解析逻辑稳定，重构风险高 |
| P2 | 增量构建（仅处理变更文件） | 每次全量处理 | 需增加文件哈希/时间戳追踪 |
| P3 | 单元测试覆盖 `lib/` | 无 | 时间约束 |
| P3 | `requirements.txt` 依赖声明 | 无 | 时间约束 |
| P3 | CI GitHub Actions 工作流 | 无 | 需先完成上述 P1/P2 项 |

---

## 九、Git 提交规范

```bash
# 内容新增
git commit -m "content: add {slug} article

- Source: AddingArticleWorkSpace/1/{source_file}
- EN rebuilt via rebuild_en.py
- Images synced via sync_images.py
- Validation: build.py --validate passed"

# 修复提交
git commit -m "fix: redistribute EN body images

- Ran: python scripts/sync_images.py
- Affected: {n} articles
- Validation: 0 HTML errors, 0 audit issues, 0 separation issues"

# 重构提交
git commit -m "refactor: consolidate scripts into lib/ + unified build.py

- Extracted shared: html_parser, atomic_io, article_config, en_extractor, validators
- Merged: rebuild_en_from_source + fix_en_content + fix_mixed_lang → rebuild_en.py
- Merged: 4 image scripts → sync_images.py
- Archived 29 obsolete scripts to scripts/archive/"
```

---

## 十、故障排查

| 症状 | 排查命令 | 可能原因 |
|------|----------|----------|
| `build.py --all` 失败 | `python scripts/build.py --validate` | 某阶段验证未通过 |
| EN 内容缺失 | `python scripts/rebuild_en.py --slug <slug>` | 源文件缺少 `div#english_translation` |
| 图片数量不匹配 | `python scripts/sync_images.py --slug <slug>` | 重建后未同步图片 |
| audit 报 Chinese in EN | `python scripts/rebuild_en.py --strict --slug <slug>` | 源文件翻译中含中文杂质 |
| 图片全部堆在开头 | `python scripts/sync_images.py --slug <slug>` | 需要运行分布修复 |
| HTML 标签未闭合 | `python scripts/validate_html.py` | 源文件含嵌套异常 |

---

> **文档维护**: 每次脚本更新或流程变更后更新本指南  
> **上次重构**: 2026-04-29  
> **下次审查建议**: 完成 YAML 配置 + Jinja2 模板迁移后
