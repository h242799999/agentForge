---
name: xq-review
description: XQ 项目完整代码审查入口。--commit 选择内容来源（提交 diff），--code/--business/--ui/--all 选择审查维度，两者可自由组合。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# XQ 代码审查

> XQ 项目审查统一入口。`--commit` 决定**看什么**（文件 vs 提交 diff），维度 flag 决定**怎么审**。
> **业务维度前置条件**：ragForge MCP 已启动，`xq` 项目索引已构建。

---

## 调用语法

```
# ── 文件模式（指定文件或目录）──────────────────────────────
/xq-review <target>                       # 默认：code + business
/xq-review <target> --code                # 仅代码规范
/xq-review <target> --business            # 仅业务逻辑（RAG）
/xq-review <target> --ui                  # 仅 KMP/Compose UI
/xq-review <target> --all                 # 全量：code + business + ui

# ── 提交模式（以 commit diff 为审查对象）───────────────────
/xq-review --commit                       # HEAD，默认：code + business
/xq-review --commit <id>                  # 指定 commit，默认：code + business
/xq-review --commit --code                # HEAD，仅代码规范
/xq-review --commit <id> --business       # 指定 commit，仅业务逻辑
/xq-review --commit --ui                  # HEAD，仅 KMP/Compose UI
/xq-review --commit <id> --all            # 指定 commit，全量
```

---

## Phase 1：解析参数 & 加载内容

### 1-A：确定来源和维度

| 参数 | 作用 |
|------|------|
| `--commit [id]` | 来源 = 提交 diff；TARGET = id 或 HEAD |
| `<target>`（无 --commit） | 来源 = 文件路径 |
| `--code` | 审查维度：代码规范 |
| `--business` | 审查维度：业务逻辑（RAG） |
| `--ui` | 审查维度：KMP/Compose |
| `--all` | 审查维度：code + business + ui |
| 无维度 flag | 默认：code + business |

### 1-B：文件模式 — 读取文件

```bash
find <target> -name "*.kt" -not -path "*/build/*" | sort
```

逐文件读取全部内容。

### 1-C：提交模式 — 获取 diff

```bash
# 元信息
git log -1 --format="HASH=%H%nSHORT=%h%nAUTHOR=%an%nDATE=%ai%nSUBJECT=%s" <TARGET>

# 变更统计 + diff（过滤锁文件和构建产物）
git show <TARGET> --stat
git diff <TARGET>^..<TARGET> -- . ':!*.lock' ':!*-lock.json' ':!dist/' ':!*.generated.*'
```

提取：变更文件列表、新增行（`+` 开头）、模块路径（供业务维度用）。

---

## Phase 2：执行选定审查维度

按选定的维度依次执行对应的 § 节。

---

## § CODE — 代码规范审查

> **文件模式**：审查文件全部内容。
> **提交模式**：聚焦 diff 新增行（`+` 开头），上下文行仅作参考，不对删除行报告问题。

### 代码逻辑检查（维度 A）

| 项目 | 检查点 |
|------|--------|
| A.1 空指针 | `!!` 强解包、未处理 null 路径 |
| A.2 资源泄漏 | 协程 scope 未关闭、Flow 未 cancel、文件流未关闭 |
| A.3 并发 | 共享可变状态、非线程安全集合在多线程使用 |
| A.4 错误处理 | 吞异常（空 catch）、协程内未捕获异常、Result 分支遗漏 |
| A.5 边界条件 | 空集合调用 `first()`、0 或负数未校验 |
| A.6 逻辑缺陷 | 死代码、遗漏分支、循环体内执行 IO |

### 代码规范检查（维度 C）

| 项目 | 检查点 |
|------|--------|
| C.1 命名 | 类 PascalCase、函数/变量 camelCase、常量 UPPER_SNAKE |
| C.2 函数长度 | > 40 行建议拆分；嵌套 > 3 层提取子函数 |
| C.3 魔法数字 | 硬编码数值/字符串应提取为具名常量 |
| C.4 可见性 | 最小可见性；`MutableStateFlow` 不对外暴露 |
| C.5 KDoc | `public` / `internal` 函数必须有 KDoc |
| C.6 测试 | 新增业务逻辑是否有对应单元测试 |

---

## § BUSINESS — 业务逻辑审查（RAG）

> **文件模式**：2-3 次 RAG 查询，全面对比规格。
> **提交模式**：1-2 次 RAG 查询（`top_k=3`），聚焦变更行是否符合业务规格。

### B-1：提取业务概念

- **文件模式**：从文件路径和代码内容提取模块域、类名、状态名、错误码、协议命令
- **提交模式**：从变更文件路径和 diff 新增行提取模块域和关键操作

### B-2：构建 RAG 查询

**文件模式**（2-3 个查询）：
- Query 1 模块级：`"<模块域> 状態機 接続フロー"` — `top_k=5`
- Query 2 操作级：`"<关键操作> 処理シーケンス"` — `top_k=5`
- Query 3 表格级（按需，有错误码/命令码时）：`top_k=5, has_table=true`

**提交模式**（1-2 个查询，精简）：
- Query 1：`"<变更模块> <变更操作> 業務フロー"` — `top_k=3`
- Query 2（按需）：`"<错误码或命令名>"` — `top_k=3, exact=true`

### B-3：调用 RAG（硬性依赖）

```
mcp__ragforge__rag_query(project="xq", query=<query>, top_k=<N>)
```

❌ **MCP 不可用时**：
- **文件模式**：输出错误信息并**终止**整个业务维度审查
- **提交模式**：跳过业务维度，在报告中注明「RAG 不可用，业务对比已跳过」，**继续**其他维度

```
（文件模式报错模板）
❌ RAG 服务不可用，业务审查已终止
请确认：
1. ragForge MCP 已启动：python3 .../ragForge/scripts/rag-mcp.py
2. ~/.mcp.json 已注册 ragforge
3. xq 项目索引已构建：rag-build.py --project xq
```

### B-4：业务逻辑对比审查

| 维度 | 检查点 |
|------|--------|
| 接口契约 | 参数类型/名称与规格表格一致 |
| 状态流转 | 状态机路径覆盖规格 Mermaid 图所有合法转换 |
| 错误码 | 代码处理的错误码与规格枚举匹配 |
| 业务规则 | 超时/重试/幂等逻辑按规格实现 |
| 流程完整性 | 完整业务流程在代码中有体现（提交模式：变更是否引入断层） |

---

## § UI — KMP/Compose UI 审查

> **文件模式**：审查文件完整内容。
> **提交模式**：读取变更文件的完整内容（非仅 diff），进行全面 KMP/Compose 检查。

### 项目探针（提交模式跳过，文件模式执行）

```bash
grep -A 20 "kotlin {" build.gradle.kts 2>/dev/null
grep -r "^expect " --include="*.kt" -l
```

### KMP 架构检查

- `commonMain` 中是否误用平台包（`android.*`、`UIKit` 等）
- 所有 `expect` 声明是否有对应所有 target 的 `actual` 实现
- Kotlin/Native（iOS）是否在非主线程访问 UI 对象

### Compose UI 检查

- Composable 函数单一职责，参数不超过 7 个
- `ViewModel` 只暴露 `StateFlow<UiState>` 只读状态，不暴露 `MutableStateFlow`
- `LazyColumn`/`LazyRow` 的 `items` 提供稳定 `key`
- `LaunchedEffect` key 正确；`DisposableEffect` 有 `onDispose` 清理
- `Flow` 在 UI 层用 `collectAsState()` 而非裸 `collect {}`

### 架构检查

- 清晰的 `presentation` / `domain` / `data` 三层
- `ViewModel` 不直接操作数据库/网络

---

## Phase 3：输出报告

### 报告头（两种模式）

**文件模式头：**
```
# XQ 代码审查报告
来源：文件审查
审查文件：{文件列表}
执行维度：{code | business | ui | all}
审查时间：{时间}
```

**提交模式头：**
```
# XQ 代码审查报告
来源：提交审查
Commit：{SHORT_HASH} — {SUBJECT}
Author：{AUTHOR}  Date：{DATE}
执行维度：{code | business | ui | all}
审查时间：{时间}
```

### 统一摘要与问题列表

```
总体结论：🔴 / 🟠 / ✅

问题统计：
  代码规范   → 🔴 N  🟠 N  🟡 N  🔵 N
  业务逻辑   → 🔴 N  🟠 N  🟡 N  🔵 N  （执行时）
  UI/Compose → 🔴 N  🟠 N  🟡 N  🔵 N  （执行时）

## [代码规范问题]（执行时）
| 级别 | 类别 | 文件 | 行号 | 问题描述 | 证据 | 修复建议 | 置信度 |

## [业务逻辑问题]（执行时）
| 级别 | 类别 | 文件 | 行号 | 问题描述 | 规格依据 | 修复建议 | 置信度 |

## [UI/Compose 问题]（执行时）
| 级别 | 类别 | 文件 | 行号 | 问题描述 | 修复建议 | 置信度 |

## 综合结论
{2-3 句话：核心风险 + 必修问题 + 合入建议}
```

**提交模式额外保存报告：**
```bash
git rev-parse --short <TARGET>
# 保存路径：reviewer/<作者>-<shortHash>-<YYYYMMDD-HHmm>.md
```
