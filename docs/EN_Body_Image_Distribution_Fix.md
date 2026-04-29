# EN Body 图片-文字交错分布修复 — 实操文档

> **用途**: 当 EN body 出现图片扎堆（img-wall + text-wall）时，按 ZH body 分布模式重分布  
> **版本**: v1.0  
> **日期**: 2026-04-29  
> **范围**: 9 篇文件修复经验沉淀

---

## 一、问题根因

| 现象 | 说明 |
|------|------|
| **img-wall + text-wall** | EN body 中所有 `<img>` 连续堆在开头，`<p>`/`<h2>` 等文本全部排在末尾 |
| **正确结构** | ZH body 为交错模式：`img → text → img → text → img` |
| **根因** | `fix_en_body_images_from_zh.py` 早期版本批量插入图片时，未按 ZH 的段落间隔分布，而是全部 prepend 到文本前 |

---

## 二、修复动作

### 2.1 前置扫描（必须执行）

```bash
python scripts/scan_image_text_separation.py
```

**输出示例**:
```
Found 9 files with image-text separation issues in EN body:
  altitude-sickness-tips.html      images_at_start: 16 imgs before 15 text
  bianba-motorcycle-diary.html     images_at_start: 27 imgs before 23 text
  ...
```

**判定标准**：`last_img_pos < first_text_pos` 即所有图片在首段文本之前

### 2.2 执行修复

```bash
python scripts/fix_en_image_distribution.py
```

**核心算法**（`fix_en_image_distribution.py`）:

```python
# Step 1: 提取 ZH 分布模式
zh_parts = split_by_img(zh_block)     # 按 <img> 切分 ZH body
zh_counts = [count_text_tokens(p) for p in zh_parts]  # 每张图片前的文本节点数

# Step 2: 提取 EN 纯文本（移除全部 img）
en_text_only = remove_imgs(en_block)
en_tokens = find_text_tokens(en_text_only)

# Step 3: 比例映射：按 ZH 文本节点比例，在 EN 文本中定位插入点
for i, zh_before in enumerate(zh_counts):
    ratio = zh_before / zh_total_text
    en_idx = int(ratio * len(en_tokens))
    insert_img_at(en_text_only, en_tokens[en_idx].pos, en_imgs[i])
```

### 2.3 批量策略

- 硬编码 `TARGET_FILES` 列表（9 个已知问题文件），不做全站自动遍历
- 每张 EN 图片保持原有的 `src`、`alt`、`loading="lazy"` 属性不变
- 图片总数不变，仅改变插入位置

---

## 三、验证闭环

```bash
# Layer 1: 分离问题归零
python scripts/scan_image_text_separation.py
# → Found 0 files with image-text separation issues

# Layer 2: HTML 结构完好
python scripts/validate_html.py
# → All HTML files validated successfully.

# Layer 3: 双语一致性
python scripts/deep_audit.py
# → Files with issues: 0
```

**强制规则**：三层验证全部通过前，禁止提交 Git

---

## 四、反模式 — 禁止事项

| 编号 | 反模式 | 后果 | 正确做法 |
|------|--------|------|----------|
| 1 | 不扫描分离状态直接改模板 | 漏修或过度修复 | 先执行 `scan_image_text_separation.py` 定位问题 |
| 2 | 硬编码文件列表后不再验证 | 新产生的分离问题无法发现 | 修复后重新扫描全站 |
| 3 | 用 regex 提取 `<div class="lang-content" data-lang="en">` | 嵌套 div 导致截断，匹配到错误区块 | 使用栈深度遍历（`depth += 1` on `<div`, `depth -= 1` on `</div>`） |
| 4 | 直接替换整块 EN body HTML | 丢失 alt 属性、inline style、data-src | 仅移动 `<img>` 标签位置，保留全部属性 |
| 5 | 按图片数量平均分布到文本段落 | 忽略 ZH 原有的疏密节奏 | 严格按 ZH 文本节点比例映射 |
| 6 | 修复后仅做 HTML 校验 | 分离问题可能未暴露为 HTML 错误 | 必须叠加 `scan_image_text_separation.py` + `deep_audit.py` |
| 7 | 修改后未运行 `deep_audit.py` | 图片移动可能意外破坏双语 block 结构 | 三级验证缺一不可 |

---

## 五、可复用检查清单

```markdown
- [ ] 运行 scan_image_text_separation.py 获取问题文件列表
- [ ] 将问题文件加入 fix_en_image_distribution.py TARGET_FILES
- [ ] 运行 fix_en_image_distribution.py
- [ ] 重新运行 scan_image_text_separation.py → 确认 0 issues
- [ ] 运行 validate_html.py → 确认 All pass
- [ ] 运行 deep_audit.py → 确认 Files with issues: 0
- [ ] git diff 抽查 2-3 个文件确认 img 分布已交错
- [ ] git add -A && git commit -m "..." && git push
```

---

## 六、Git 提交规范

```bash
git commit -m "fix: redistribute EN body images to match ZH layout pattern

- Fixes img-wall + text-wall separation in EN body blocks
- Affected: 9 articles, 11-45 imgs each
- Algorithm: proportional mapping based on ZH text token distribution
- Validation: 0 separation issues, 0 HTML errors, 0 audit issues"
```

---

## 七、历史修复记录

| 日期 | 文件数 | 总图片数 | 提交 |
|------|--------|----------|------|
| 2026-04-29 | 9 | 238 | `a201664` |
