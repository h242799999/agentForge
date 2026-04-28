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

### kmp-cmp-reviewer

对指定目录进行 KMP/CMP 代码审查：

```
请用 kmp-cmp-reviewer 审查 composeApp/src/commonMain/kotlin/ 目录
```

或在 PR review 时：

```
帮我 review 这个 PR 的 KMP 部分
```

审查覆盖五个维度（权重从高到低）：

| 维度 | 权重 |
|------|------|
| KMP 跨平台架构（expect/actual、source set 分层） | 30% |
| Compose UI 设计（重组优化、State Hoisting、副作用） | 25% |
| Kotlin 惯用法（Null Safety、协程/Flow、数据建模） | 20% |
| 架构模式（MVVM 分层、Koin DI、导航） | 15% |
| 可测试性与可维护性 | 10% |

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
