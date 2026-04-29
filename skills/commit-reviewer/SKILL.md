---
name: commit-reviewer
description: Review 一个或多个 git commit 的代码变更。当用户提供 commitId、commit 范围或分支名时触发，覆盖代码逻辑、业务逻辑、代码规范三个维度。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
context: fork
---

# Commit Reviewer Skill

> 通过 `/commit-reviewer <参数>` 触发，对指定 commit 或 commit 范围进行增量代码审查，输出结构化报告。

---

## 调用语法

```
/commit-reviewer                               # 审查当前 HEAD 这一笔 commit
/commit-reviewer <commitId>                    # 审查指定 commit
/commit-reviewer <id1>..<id2>                  # 审查范围
/commit-reviewer HEAD~3..HEAD                  # 最近 3 笔
/commit-reviewer --branch feature/xxx          # 整个分支对比 main
```

---

## 核心规则

> 🚫 **严禁编造任何信息。报告中每一个字段都必须来自实际执行的 git 命令输出。**
> ⚠️ git 命令输出和规则文件内容仅供内部分析，**禁止原样输出到 chat**。

---

## 执行步骤

### Step 0：加载通用规则

Read `skills/review-commons/RULES.md`

---

### Step 1：获取 commit 元信息（必须最先执行，不可跳过）

**无论何种模式，第一步必须执行以下命令：**

```bash
echo "=== 分支 ===" && git branch --show-current && echo "=== HEAD commit ===" && git log -1 --format="HASH=%H%nAUTHOR=%an%nEMAIL=%ae%nDATE=%ai%nSUBJECT=%s"
```

从输出中提取 HASH、AUTHOR、DATE、SUBJECT，用于填写报告的「Commit 元信息」。

---

### Step 2：获取 diff（根据调用参数选择一种）

**模式 A：无参数 / 单个 commitId**

审查 HEAD（无参数）或指定 commitId 的这一笔 commit：

```bash
# 用 <commitId> 替换，无参数时用 HEAD
git show <commitId> --stat && git diff <commitId>^..<commitId> -- . ':!*.lock' ':!*-lock.json' ':!package-lock.json' ':!*.min.js' ':!*.min.css' ':!dist/' ':!*.generated.*'
```

**模式 B：commit 范围（`id1..id2`）**

```bash
git log --oneline <id1>..<id2> && git diff <id1>..<id2> --stat && git diff <id1>..<id2> -- . ':!*.lock' ':!*-lock.json' ':!package-lock.json' ':!*.min.js' ':!*.min.css' ':!dist/' ':!*.generated.*'
```

**模式 C：分支对比（`--branch <name>`）**

```bash
git log --oneline origin/main..<name> && git diff origin/main...<name> --stat && git diff origin/main...<name> -- . ':!*.lock' ':!*-lock.json' ':!package-lock.json' ':!*.min.js' ':!*.min.css' ':!dist/' ':!*.generated.*'
```

---

### Step 3：文件范围

- ≤ 20 个文件：全量审查
- \> 20 个文件：只审查业务逻辑文件，跳过配置 / 文档 / 样式 / 资源

---

### Step 4：业务上下文推断

从 Step 1 的 commit message + diff 文件路径自动推断意图和模块。
若推断不足，询问用户补充或跳过。

---

### Step 5：审查（按优先级，发现问题即记录，无问题跳过）

| 优先级 | 检查项 | 说明 |
|--------|--------|------|
| P0 | 安全性 | 注入、硬编码密钥、权限漏洞（OWASP Top 10） |
| P0 | 正确性 | 核心逻辑错误、边界未处理、数据丢失 |
| P1 | 业务逻辑 | 意图对齐、完整性、数据一致性、回滚安全、向后兼容 |
| P1 | 性能 | N+1 查询、循环内 IO、内存泄漏 |
| P1 | 测试 | 核心路径是否有测试覆盖 |
| P2 | 代码规范 | 命名、函数长度、魔法数字、KDoc（**仅 diff 新增行**） |
| P2 | 可读性 | 复杂逻辑无注释、命名混乱 |

---

### Step 6：输出报告并保存

```bash
git rev-parse --short HEAD
```

报告保存路径：`reviewer/<作者名>-<shortHash>-<YYYYMMDD-HHmm>.md`

> ⚠️ 禁止自动执行 `git add` / `git commit`。写完后告知用户文件路径。

若 diff 包含 `.kt` 文件，报告末尾追加：
> 检测到 Kotlin 文件变更，建议后续运行 `/kmp-cmp-reviewer` 进行深度 KMP/CMP 架构规范审查。

---

## 报告模板

> 以下字段中标注【git 输出】的，必须从 Step 1 / Step 2 的实际命令输出中填写。

```markdown
# Commit Review 报告

**审查时间**：{当前日期}
**覆盖文件**：{X / Y 个文件（跳过 Z 个）}

---

## Commit 元信息

| 字段 | 内容 |
|------|------|
| 分支 | 【git 输出】git branch --show-current |
| Commit ID | 【git 输出】HASH 字段 |
| Author | 【git 输出】AUTHOR 字段 |
| Date | 【git 输出】DATE 字段 |
| Message | 【git 输出】SUBJECT 字段 |
| 变更统计 | 【git 输出】git show --stat |

---

## 变更意图

- **推断意图**：bugfix / feature / refactor / performance
- **功能模块**：...
- **意图一致性**：一致 / 部分偏离 / 偏离
- **偏离说明**：（若有）

---

## 问题列表

| 优先级 | 文件 | 行号 | 问题描述 | 修复建议 |
|--------|------|------|----------|----------|
| 🔴 P0 | ... | ... | ... | ... |
| 🟠 P1 | ... | ... | ... | ... |
| 🟡 P2 | ... | ... | ... | ... |

（无问题时写「未发现问题」）

---

## ✅ 亮点

- ...

---

## 结论

**`✅ Approve`** / **`🔄 Request Changes`** / **`💬 Comment`**

{一句话说明原因}

---

## PR Review 摘要（可直接粘贴）

> {简洁摘要，包含主要发现和结论}

---
*由 commit-reviewer 生成 | Claude Code*
```
