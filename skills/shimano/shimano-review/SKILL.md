---
name: shimano-review
description: Shimano 项目完整代码审查入口。--commit 选择内容来源（提交 diff），--code/--business/--ui/--all 选择审查维度，两者可自由组合。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# Shimano 代码审查

> Shimano 项目审查统一入口。`--commit` 决定**看什么**（文件 vs 提交 diff），维度 flag 决定**怎么审**。
> **业务维度前置条件**：`specs/INDEX.md` 已生成（运行 `/spec-indexer`）。RAG 接入后升级为 RAG 模式。

---

## 调用语法

```
# ── 文件模式（指定文件或目录）──────────────────────────────
/shimano-review <target>                   # 默认：code + business
/shimano-review <target> --code            # 仅代码规范
/shimano-review <target> --business        # 仅业务逻辑（规格文档）
/shimano-review <target> --ui              # 仅 KMP/Compose UI
/shimano-review <target> --all             # 全量：code + business + ui

# ── 提交模式（以 commit diff 为审查对象）───────────────────
/shimano-review --commit                   # HEAD，默认：code + business
/shimano-review --commit <id>              # 指定 commit，默认：code + business
/shimano-review --commit --code            # HEAD，仅代码规范
/shimano-review --commit <id> --business   # 指定 commit，仅业务逻辑
/shimano-review --commit --ui              # HEAD，仅 KMP/Compose UI
/shimano-review --commit <id> --all        # 指定 commit，全量
```

---

## Phase 1：解析参数 & 加载内容

### 1-A：确定来源和维度

| 参数 | 作用 |
|------|------|
| `--commit [id]` | 来源 = 提交 diff；TARGET = id 或 HEAD |
| `<target>`（无 --commit） | 来源 = 文件路径 |
| `--code` | 审查维度：代码规范 |
| `--business` | 审查维度：业务逻辑（规格文档） |
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

# 变更统计 + diff
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
> **提交模式**：聚焦 diff 新增行（`+` 开头），删除行不报告问题。

### KMP 分层规范检查

| 层 | 检查点 |
|----|--------|
| **presentation** | ViewModel 只持有 UI State；不直接调用 Repository |
| **domain** | UseCase 参数/返回为 domain model，不含平台类型 |
| **data** | Repository 依赖注入；Shimano SDK 调用封装在此层 |
| **通用** | KDoc；命名规范；函数 < 40 行；嵌套 < 3 层 |

### 代码逻辑检查（维度 A）

| 项目 | 检查点 |
|------|--------|
| A.1 空指针 | `!!` 强解包、未处理 null 路径 |
| A.2 资源泄漏 | 协程 scope 未关闭、Shimano SDK 监听器未移除 |
| A.3 并发 | 共享可变状态；BLE 回调在主线程外访问 UI |
| A.4 错误处理 | SDK 异常是否按类型正确分类处理 |
| A.5 边界条件 | 空集合、设备未连接时调用 SDK |
| A.6 逻辑缺陷 | 死代码、遗漏分支、循环内 IO |

---

## § BUSINESS — 业务逻辑审查

> ⚠️ **当前状态**：使用本地 `specs/INDEX.md`。RAG 接入后此节将升级为 RAG 检索模式。
>
> **文件模式**：完整规格对比。
> **提交模式**：只检查变更行是否与规格一致，不做全量规格审查。

### B-1：验证规格索引

```bash
ls specs/INDEX.md 2>/dev/null || echo "NOT_FOUND"
```

若不存在：
- **文件模式**：输出错误并终止业务维度审查
- **提交模式**：跳过业务维度，注明缺失，继续其他维度

```
❌ 未找到规格文档索引。
请先运行 /spec-indexer 生成索引，或等待 RAG 接入后重新使用本模式。
```

### B-2：读取代码，匹配规格章节

Read `specs/INDEX.md`

根据文件路径/类名在索引中匹配相关规格条目：
- `src/auth/` → Auth 模块规格
- `src/connection/` → Connection 模块规格
- `src/mybike/` → MyBike 模块规格
- 提交模式：仅匹配**变更文件**对应的规格

### B-3：按节加载规格文档

精确加载对应章节，不加载整个文档：

```bash
grep -n "^## " specs/<doc>.md   # 定位章节行号
# 用 Read offset/limit 只读该章节
```

### B-4：业务逻辑对比审查

| 维度 | 检查点 |
|------|--------|
| API 契约 | 函数签名、参数类型与 API spec 一致 |
| 状态流转 | 连接/骑行状态机与状态图一致 |
| SDK 调用 | suspend/非 suspend 使用符合规范；异常类型正确 |
| 业务规则 | 权限检查、设备绑定、数据同步规则 |
| 提交模式 | 变更是否引入状态流转断层或 API 不一致 |

---

## § UI — KMP/Compose UI 审查

> **文件模式**：审查文件完整内容。
> **提交模式**：读取变更文件完整内容（非仅 diff），进行全面 KMP/Compose 检查。

### 项目探针（仅文件模式执行）

```bash
grep -A 20 "kotlin {" build.gradle.kts 2>/dev/null
grep -r "^expect " --include="*.kt" -l
```

### KMP 架构检查

- `commonMain` 中是否误用平台包（`android.*`、`UIKit` 等）
- 所有 `expect` 声明是否有对应所有 target 的 `actual` 实现
- Shimano SDK 的平台差异是否通过 `expect/actual` 正确隔离

### Compose UI 检查

- Composable 函数单一职责，参数不超过 7 个
- `ViewModel` 只暴露 `StateFlow<UiState>` 只读状态
- `LazyColumn`/`LazyRow` 的 `items` 提供稳定 `key`
- `LaunchedEffect` key 正确；`DisposableEffect` 有 `onDispose` 清理
- SDK 事件监听器（BLE 回调等）在 `DisposableEffect` 中注册和注销

### 架构检查

- 清晰的 `presentation` / `domain` / `data` 三层
- Shimano SDK 调用封装在 `data` 层，不出现在 ViewModel 或 UI 层

---

## Phase 3：输出报告

### 报告头（两种模式）

**文件模式头：**
```
# Shimano 代码审查报告
来源：文件审查
审查文件：{文件列表}
规格模式：本地 specs/INDEX.md（待升级 RAG）
执行维度：{code | business | ui | all}
审查时间：{时间}
```

**提交模式头：**
```
# Shimano 代码审查报告
来源：提交审查
Commit：{SHORT_HASH} — {SUBJECT}
Author：{AUTHOR}  Date：{DATE}
规格模式：本地 specs/INDEX.md（待升级 RAG）
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
