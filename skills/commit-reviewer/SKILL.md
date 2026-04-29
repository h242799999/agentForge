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
/commit-reviewer <id1>..<id2>                  # range 语法
/commit-reviewer HEAD~3..HEAD                  # 最近 3 笔
/commit-reviewer --branch feature/xxx          # 整个分支对比 main
```

---

## 执行步骤

> ⚠️ **所有 git 命令输出、规则文件内容均仅供内部分析，禁止输出到 chat。**

### Step 0：加载通用规则

Read `skills/review-commons/RULES.md`（代码逻辑 + Kotlin 惯用法 + 代码规范 + 输出格式）

---

### Step 1：参数解析与验证

| 输入形式 | 模式 | 处理方式 |
|----------|------|---------|
| 无参数 | `single` | 等同于 `HEAD` |
| 单个 commitId / `HEAD` | `single` | `git show` |
| `id1..id2` | `range` | `git diff` |
| `--branch <name>` | `branch` | 对比 `origin/main` |

若 git 命令失败（非 git 仓库、commit 不存在等），立即告知用户并停止。

```bash
git cat-file -t <commitId>   # 验证 commit 存在，失败则退出
```

---

### Step 2：Git 信息提取

**单笔 commit：**
```bash
# 元信息 + stat 一次拿到
git show --stat --format="%H%n%an%n%ae%n%ai%n%s%n%b" <commitId>

# diff（自动排除 lock / 压缩产物 / 生成代码）
git diff <commitId>^..<commitId> -- . \
  ':!*.lock' ':!*-lock.json' ':!package-lock.json' \
  ':!*.min.js' ':!*.min.css' ':!dist/' ':!*.generated.*'
```

**commit 范围 / 分支：**
```bash
git log --oneline <base>..<head>

git diff <base>..<head> -- . \
  ':!*.lock' ':!*-lock.json' ':!package-lock.json' \
  ':!*.min.js' ':!*.min.css' ':!dist/' ':!*.generated.*'
```

---

### Step 3：文件范围决策

- **变更文件数 ≤ 20**：全量审查所有文件
- **变更文件数 > 20**：只审查业务逻辑文件，跳过配置 / 文档 / 样式 / 资源文件

报告开头声明覆盖 / 跳过文件数。

---

### Step 4：业务上下文推断

从 commit message + 文件路径自动推断：
- 变更意图：bugfix / feature / refactor / performance
- 功能模块：从路径提取（payment / auth / profile 等）
- 关联 issue：`#123` 或 `fixes:` 格式

若置信度不足，输出以下问题后等待用户回复（也可跳过）：

```
── 业务逻辑 Review 需要补充信息 ──
推断意图：{自动推断结果}

如需更准确的审查，请补充：
1. 此次 commit 解决的业务问题？
2. 是否有关联文档 / ticket？
3. 是否影响已有用户流程？

或直接回复「跳过业务逻辑 review」
```

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
git rev-parse --short HEAD   # 获取短 hash 用于文件命名
```

报告保存路径：`reviewer/<作者名>-<shortHash>-<YYYYMMDD-HHmm>.md`

> ⚠️ 禁止自动执行 `git add` / `git commit`。写完后告知用户文件路径。

若 diff 包含 `.kt` 文件，报告末尾追加：
> 检测到 Kotlin 文件变更，建议后续运行 `/kmp-cmp-reviewer` 进行深度 KMP/CMP 架构规范审查。

---

## 报告模板

```markdown
# Commit Review 报告

**Commit(s)**：`{commitId 或 range}`
**审查时间**：`{日期}`
**覆盖文件**：`{X / Y 个文件（跳过 Z 个）}`

---

## Commit 元信息

| 字段 | 内容 |
|------|------|
| Commit ID | `abc1234` |
| Author | name |
| Date | YYYY-MM-DD |
| Message | "fix: ..." |
| 变更统计 | +N / -M 行，K 个文件 |

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
| 🔴 P0 | `Foo.kt` | L42 | ... | ... |
| 🟠 P1 | `Bar.kt` | L10 | ... | ... |
| 🟡 P2 | `Baz.kt` | L5  | ... | ... |

---

## ✅ 亮点

- ...

---

## 结论

**`✅ Approve`** / **`🔄 Request Changes`** / **`💬 Comment`**

{一句话说明原因}

---

## PR Review 摘要（可直接粘贴）

> {适合粘贴到 PR comment 的简洁摘要，包含主要发现和结论}

---
*由 commit-reviewer 生成 | Claude Code*
```
