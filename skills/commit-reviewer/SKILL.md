---
name: commit-reviewer
description: Review 一个或多个 git commit 的代码变更。当用户提供 commitId、commit 范围或分支名时触发，覆盖代码逻辑、业务逻辑、代码规范三个维度。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
context: fork
---

# Commit Reviewer Skill

> 通过 `/commit-reviewer <参数>` 触发，对指定 commit 或 commit 范围进行增量代码审查，输出结构化报告。
> 与 `/kmp-cmp-reviewer` 互补：本工具聚焦**变更视角**，kmp-cmp-reviewer 聚焦**KMP/CMP 静态规范**。

---

## 调用语法

```
/commit-reviewer                               # 无参数 → 默认审查最新一笔（HEAD）
/commit-reviewer <commitId>                    # 单笔 commit
/commit-reviewer <id1> <id2>                   # id1 到 id2 的范围
/commit-reviewer <id1>..<id2>                  # range 语法
/commit-reviewer HEAD~3..HEAD                  # 最近 3 笔
/commit-reviewer --branch feature/xxx          # 整个分支对比 main
```

---

## 执行步骤

### Step 1：参数解析与验证

**无参数时默认使用 HEAD：**
```bash
# 未传参数 → target = HEAD
git log HEAD -1 --oneline   # 显示将要审查的 commit，让用户确认
```

识别四种模式：

| 输入形式 | 模式 | 处理方式 |
|----------|------|---------|
| 无参数 | `single` | 等同于传入 `HEAD` |
| 单个 commitId / `HEAD` | `single` | `git show <id>` |
| 两个 commitId 或 `id1..id2` | `range` | `git diff <id1>^ <id2>` |
| `--branch <name>` | `branch` | `git diff origin/main..<name>` |

验证 commit 是否存在：
```bash
git cat-file -t <commitId>   # 返回 "commit" 则有效，否则报错退出
```

---

### Step 0：加载通用规则

Read `skills/review-commons/RULES.md`（代码逻辑 + Kotlin 惯用法 + 代码规范 + 输出格式）

---

### Step 2：Git Diff 提取

**单笔 commit：**
```bash
git show <commitId> --stat                          # 变更统计概览
git show <commitId>                                 # 完整 diff
git log <commitId> -1 --format="%H|%an|%ae|%ad|%s" # 元信息
```

**多笔 commit 范围：**
```bash
git log <id1>..<id2> --oneline                      # 先列出范围内 commit 列表
git diff <id1>^ <id2> --stat                        # 变更统计
git diff <id1>^ <id2>                               # 完整 diff
```

**分支对比：**
```bash
git log origin/main..HEAD --oneline
git diff origin/main..HEAD --stat
git diff origin/main..HEAD
```

---

### Step 3：文件优先级分级（Tier）

**文件数 ≤ 15 时**：全量读取所有变更文件。

**文件数 > 15 时**，按以下优先级分级：

```
Tier 1 — 必审（全量读取文件内容）
  匹配规则：
  - 文件名含 ViewModel / UseCase / Repository / Service / Manager
  - 路径含 auth / token / encrypt / permission / payment / security
  - data class / entity / schema（数据模型）
  - 对应以上文件的 Test / Spec 文件

Tier 2 — 抽查（只读前 80 行 + diff 上下文各 10 行）
  匹配规则：
  - Composable / Screen / Fragment / Activity（UI 组件）
  - Module / Component / Koin（DI 配置）
  - 工具类、扩展函数（*Ext.kt / *Utils.kt / *Helper.kt）

Tier 3 — 跳过（仅记录文件名）
  匹配规则：
  - _generated / .pb / BuildConfig / R.java（自动生成）
  - .xml / .json / .png / drawable / assets（资源）
  - diff 新增行数 / 文件总行数 > 80%（纯格式化）
```

报告开头声明：「本次审查覆盖 X/Y 个文件，跳过 Z 个低优先级文件」

---

### Step 4：业务逻辑上下文收集

**4a. 自动推断**（从现有信息提取）：
- commit message 关键词 → 意图分类（bugfix / feature / refactor / performance）
- 变更文件路径 → 功能模块（payment / auth / profile / order 等）
- 测试文件变更 → 验证预期行为
- 关联 issue 编号（commit message 中 `#123` 或 `fixes:` 格式）

**4b. 若置信度不足，输出结构化问题（等待用户回复后继续）**：

```
── 业务逻辑 Review 需要补充信息 ──

从 commit message 推断此次变更意图为：{自动推断结果}

如需更准确的业务逻辑 review，请补充：
1. 此次 commit 解决的业务问题是什么？
2. 是否有关联的需求文档 / Jira ticket？
3. 这个改动是否影响已有的用户流程？（如订单流、登录流）

请补充后继续，或直接回复「跳过业务逻辑 review」
```

---

### Step 5：三维度分析

> **通用规则（代码逻辑 + 代码规范）已在 Step 0 加载，直接应用。**
> 本步骤只需补充 commit 视角特有的业务逻辑维度。

#### 维度 1：代码逻辑
→ 应用 `review-commons/RULES.md` 中的「维度 A」规则，仅针对 diff 变更行。

#### 维度 2：业务逻辑（commit 视角特有，结合 Step 4 上下文）

| 检查项 | 具体内容 |
|--------|---------|
| 变更意图对齐 | 实际改动与 commit message 是否一致 |
| 逻辑完整性 | 改动是否覆盖了业务场景的所有分支 |
| 数据一致性 | 跨服务/跨层数据是否一致（cache 与 DB、本地与远端） |
| 回退安全性 | 是否可安全回滚？有无数据迁移风险 |
| 向后兼容 | API / 接口是否破坏了下游已有调用 |

#### 维度 3：代码规范
→ 应用 `review-commons/RULES.md` 中的「维度 C」规则，**仅针对 diff 新增行**（不做全文件扫描）。

---

### Step 6：输出报告并保存

按以下模板生成报告，**保存到 `reviewer/` 目录**：

```bash
# 报告文件命名规范
reviewer/<作者名>-<commitId前8位>-<YYYY-MM-DD-HHmm>.md

# 示例
reviewer/hanxiao-abc1234ef-2026-04-28-1430.md
```

> ⚠️ **禁止自动执行 `git add` / `git commit`**，报告仅供人工审阅。

若 diff 包含 `.kt` 文件，在报告末尾追加：
> 检测到 Kotlin 文件变更，建议后续运行 `/kmp-cmp-reviewer` 进行深度 KMP/CMP 架构规范审查。

---

## 输出报告模板

```markdown
# Commit Review 报告

**Commit(s)**：`{commitId 或 range}`
**模式**：`{single / range / branch}`
**审查时间**：`{日期}`
**覆盖文件**：`{X / Y 个文件（跳过 Z 个低优先级文件）}`

---

## Commit 元信息

| 字段 | 内容 |
|------|------|
| Commit ID | `abc1234` |
| Author | name / email |
| Date | YYYY-MM-DD |
| Message | "fix: ..." |
| 变更统计 | +N 行 / -M 行，涉及 K 个文件 |

---

## 变更意图对齐

- **推断意图**：{bugfix / feature / refactor / performance}
- **功能模块**：{payment / auth / profile / ...}
- **意图一致性**：[一致 / 部分偏离 / 偏离]
- **偏离说明**：（若有，此 commit 同时包含了未声明的 XXX）

---

## 影响范围分析

- **直接修改模块**：...
- **跨平台影响**：Android only / iOS only / 共享层 / 全平台
- **破坏性变更**：[是 / 否] + 原因

---

## 🔴 代码逻辑问题

| 严重程度 | 文件 | 行号 | 问题描述 | 修复建议 |
|----------|------|------|----------|----------|
| Critical | `Foo.kt` | L42 | ... | ... |

---

## 🟠 业务逻辑问题

（基于提供的上下文分析，若跳过则标注「用户跳过业务逻辑 review」）

---

## 🟡 代码规范问题（仅 diff 新增行）

| 文件 | 行号 | 问题描述 | 修复建议 |
|------|------|----------|----------|

---

## ✅ 亮点

- ...

---

## 合入建议

- **结论**：[可直接合入 / 需修改后合入 / 建议拆分 commit / 需要更多信息]
- **拆分建议**：（若 commit 混合了多个目的）

---

## 后续跟进

（若包含 .kt 文件）建议运行 `/kmp-cmp-reviewer` 进行深度 KMP/CMP 架构规范审查。

---
*由 commit-reviewer skill 生成 | Claude Code*
```
