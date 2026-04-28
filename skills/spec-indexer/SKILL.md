---
name: spec-indexer
description: 扫描 specs/ 目录中的设计文档，自动生成或更新 specs/INDEX.md 映射表。在首次使用 spec-reviewer 之前运行，或在添加新文档后更新索引。
tools: Read, Grep, Glob, Bash, Write
disable-model-invocation: true
---

# Spec Indexer Skill

> 通过 `/spec-indexer` 触发，扫描 `specs/` 目录，提取文档结构，生成 `specs/INDEX.md` 映射表。
> 生成后请人工审查并补充代码路径与文档章节的映射关系。

---

## 调用语法

```
/spec-indexer                    # 扫描 specs/ 目录，生成/更新 INDEX.md
/spec-indexer --xlsx <dir>       # 从 xlsx 目录提取规格并转换为 Markdown
/spec-indexer --dir docs/specs/  # 指定文档目录
/spec-indexer --dry-run          # 预览，不写入文件
```

---

## 执行步骤

### Step 0：检测 xlsx 文件（Shimano SDK 专用）

检查项目根目录下是否存在 `scripts/extract-specs.py`：

```bash
ls scripts/extract-specs.py 2>/dev/null && echo "exists" || echo "not found"
```

若存在，且用户指定了 `--xlsx <dir>` 或 `specs/` 中尚无 `api-spec-*.md` 文件，则先运行转换：

```bash
# 从默认路径提取（Shimano SDK）
python3 scripts/extract-specs.py

# 或指定 xlsx 目录
python3 scripts/extract-specs.py "/path/to/xlsx目录" "./specs"
```

转换完成后继续 Step 1。

---

### Step 1：扫描文档目录

```bash
# 列出所有文档文件
find specs/ -type f \( -name "*.md" -o -name "*.txt" \) | sort

# 统计文档数量和大小
find specs/ -type f \( -name "*.md" -o -name "*.txt" \) | wc -l
```

---

### Step 2：提取每个文档的章节结构

对每个文档文件：

```bash
# 提取所有标题（Markdown h1-h3）
grep -n "^#\{1,3\} " specs/api-design.md

# 提取行数（用于计算章节范围）
wc -l specs/api-design.md
```

---

### Step 3：从代码目录提取模块关键词

```bash
# 提取主要代码模块目录
find . -type d -name "*.kt" -prune -o -type d -print | grep -v ".git\|build\|.gradle" | head -30

# 提取主要 Kotlin 文件名（去掉路径和扩展名作为关键词）
find . -name "*.kt" -not -path "*/build/*" | xargs -I{} basename {} .kt | sort -u | head -50
```

---

### Step 4：生成 INDEX.md

基于提取的信息，生成结构化的 INDEX.md：

```markdown
# Spec Index

> 维护代码模块与设计文档章节的映射关系。
> 由 /spec-indexer 自动生成框架，请人工补充「代码路径/关键词」列。

**最后更新**：{日期}
**文档目录**：`specs/`

---

## 文档清单

| 文档ID | 文件路径 | 描述 | 章节数 | 大小 |
|--------|---------|------|-------|------|
| API | specs/api-design.md | （请填写描述） | N | XX KB |
| DD | specs/detailed-design/ | （请填写描述） | N | XX KB |

---

## 章节索引

### api-design.md

| 章节 | 标题 | 起始行 | 建议关联代码路径 |
|------|------|-------|----------------|
| §1 | Overview | L1 | （请填写） |
| §2 | 认证接口 | L45 | （请填写，如 `**/auth/**`） |
| §3 | 支付接口 | L120 | （请填写，如 `**/payment/**`） |

---

## 模块映射表

> ⚠️ 以下为自动推断，请人工核对并修正

| 代码路径/关键词 | 文档ID | 章节 | 检查重点 |
|---------------|--------|------|---------|
| `**/payment/**` | API | §3 支付接口 | 接口参数、错误码 |
| `**/auth/**` | API | §2 认证接口 | Token 格式、过期处理 |
| `**ViewModel**` | DD | §2.x 对应模块 | 状态机、业务流程 |
| `**Screen**` | UI | §5.x 对应页面 | 组件规范、交互行为 |

---

## 使用说明

`/spec-reviewer` 根据此文件的「模块映射表」定位相关规格章节，
然后从对应文档的指定行号范围加载内容，无需加载整个文档。

路径匹配规则：
- `**/payment/**` — 路径中包含 payment 的所有文件
- `**ViewModel**` — 文件名包含 ViewModel 的所有文件
- `PaymentApi.kt` — 精确文件名匹配
```

---

### Step 5：输出结果

```
✅ 索引生成完成

扫描文档：N 个文件
提取章节：M 个
自动推断映射：K 条（需人工审核）

已写入：specs/INDEX.md

⚠️ 请人工审核以下内容：
1. 为每个章节填写「建议关联代码路径」
2. 确认「模块映射表」中的自动推断是否正确
3. 添加未被自动识别的特殊映射关系

完成后运行 /spec-reviewer 开始代码规格审查。
```
