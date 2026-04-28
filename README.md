# agentForge

用于开发和分发 Claude Code Skills / SubAgents 的工作坊项目。

目前包含：

- **kmp-cmp-reviewer** — Kotlin Multiplatform / Compose Multiplatform 专项代码审查 Agent

---

## 安装

### Claude Code

```bash
# 1. 注册 marketplace（一次性）
/plugin marketplace add h242799999/agentForge

# 2. 安装插件
/plugin install agent-forge@agent-forge-marketplace

# 3. 重新加载
/reload-plugins
```

### GitHub Copilot CLI

```bash
# 1. 注册 marketplace（一次性）
copilot plugin marketplace add h242799999/agentForge

# 2. 安装插件
copilot plugin install agent-forge@agent-forge-marketplace
```

> **注意**：marketplace 名称是 `agent-forge-marketplace`（来自 `marketplace.json` 中的 `name` 字段），不是 repo 名 `agentForge`。

---

## 使用

| 工具 | 调用方式 | 来源目录 | 运行上下文 |
|------|---------|---------|-----------|
| Claude Code | `@agent-kmp-cmp-reviewer` | `agents/` | 独立隔离 |
| Copilot / 通用 | `/kmp-cmp-reviewer` | `skills/` | 当前对话 |

---

### `/kmp-cmp-reviewer`（Skill，斜杠命令）

适用于 **GitHub Copilot** 及所有支持斜杠命令的工具：

```
/kmp-cmp-reviewer                                      # 自动扫描当前项目
/kmp-cmp-reviewer src/commonMain/kotlin/               # 指定目录
/kmp-cmp-reviewer HomeViewModel.kt                     # 指定文件
/kmp-cmp-reviewer 只看 Compose UI 和 State 管理部分    # 自然语言描述范围
```

---

### kmp-cmp-reviewer（SubAgent，@ 提及）

适用于 **Claude Code**，运行在独立隔离上下文中，使用 Opus 模型：

#### 方式 1：`@` 提及（推荐，确保一定触发）

在输入框输入 `@`，从弹出列表中选择：

```
@"kmp-cmp-reviewer (agent)" 审查 composeApp/src/commonMain/kotlin/ 目录
```

手动输入语法（不使用 typeahead）：

```
@agent-kmp-cmp-reviewer 审查 composeApp/src/commonMain/kotlin/ 目录
```

插件安装后的完整限定名：

```
@agent-forge:kmp-cmp-reviewer 审查 composeApp/src/commonMain/kotlin/ 目录
```

#### 方式 2：自然语言（Claude 根据描述自动决定是否委派）

```
请用 kmp-cmp-reviewer 审查 composeApp/src/commonMain/kotlin/ 目录
帮我做一下这个 PR 的 KMP/CMP 代码审查
review 一下 ViewModel 层和 Repository 层的代码
```

#### 方式 3：会话级指定（对当前整个会话生效）

```bash
claude --agent kmp-cmp-reviewer
```

#### 常用调用示例

| 场景 | 命令 |
|------|------|
| 审查整个 commonMain | `@agent-kmp-cmp-reviewer 审查 src/commonMain/kotlin/` |
| 只看 Compose UI 部分 | `@agent-kmp-cmp-reviewer 只审查 Compose UI 相关代码，重点看重组性能` |
| PR 合并前审查 | `@agent-kmp-cmp-reviewer 对本次 PR 变更的 KMP 代码做全量 review` |
| 指定单个文件 | `@agent-kmp-cmp-reviewer 审查 HomeViewModel.kt` |

---

### 审查维度

| 维度 | 权重 | 关注点 |
|------|------|--------|
| KMP 跨平台架构 | 30% | `expect/actual` 正确性、source set 分层、Native 内存模型 |
| Compose UI 设计 | 25% | 重组优化、State Hoisting、副作用管理、`LazyList` key |
| Kotlin 惯用法 | 20% | Null Safety、协程/Flow 主线程安全、密封类建模 |
| 架构模式 | 15% | MVVM 分层、Koin DI、类型安全导航 |
| 可测试性 | 10% | `commonTest` 覆盖、ViewModel 可独立测试 |

输出格式参考 [agents/kmp-cmp-reviewer/REPORT_TEMPLATE.md](agents/kmp-cmp-reviewer/REPORT_TEMPLATE.md)。

---

## 本地全局部署（不通过 plugin 安装）

```bash
./scripts/deploy.sh --global
```

将 skills / agents 同步到 `~/.claude/`，在所有项目中生效。

---

## 目录结构

```
agentForge/
├── .claude-plugin/
│   ├── plugin.json          # 插件身份（name、version、author）
│   └── marketplace.json     # marketplace 注册表
├── agents/
│   └── kmp-cmp-reviewer/
│       ├── AGENT.md         # Agent 定义（审查逻辑、维度、执行流程）
│       └── REPORT_TEMPLATE.md  # 输出报告模板
├── skills/
│   └── template/
│       └── SKILL.md
├── scripts/
│   ├── deploy.sh
│   └── sync-copilot.sh
└── CLAUDE.md
```

---

## 更新插件

发布新版本后，用户重新执行安装命令即可更新，或使用：

```bash
/plugin update agent-forge@agent-forge-marketplace
```
