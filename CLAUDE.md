# skill-workshop

用于开发 Claude Code Skills 和 SubAgents 的工作坊项目。

## 项目目标

- 开发可复用的 Claude Code Skills（技能）
- 开发 SubAgents（子智能体）
- 打包为 Plugin 供团队使用
- 兼容 GitHub Copilot 自定义指令

## 目录结构

```
skill-workshop/
├── skills/
│   ├── xq/               # XQ 项目专项 Skills
│   │   ├── xq-review/
│   │   ├── xq-business-reviewer/   # 依赖 ragForge MCP (project="xq")
│   │   └── xq-code-reviewer/
│   ├── shimano/          # Shimano 项目专项 Skills
│   │   ├── shimano-sdk-guard/
│   │   ├── shimano-review/
│   │   ├── shimano-codegen/  # 代码生成，区分 SDK v1.0.0/v1.0.2，依赖 ragForge MCP (project="shimano")
│   │   ├── coding-standards/
│   │   ├── spec-codegen/
│   │   ├── spec-indexer/
│   │   └── svn-fetch/
│   └── general/          # 通用 Skills
│       ├── commit-reviewer/
│       ├── kmp-cmp-reviewer/
│       ├── spec-reviewer/
│       ├── rag-query/
│       ├── puml-to-md/
│       ├── list-skills/
│       ├── review-commons/   # 共享规则库（非独立 skill）
│       └── template/         # Skill 开发模板
├── agents/               # SubAgent 定义
│   ├── commit-reviewer/
│   ├── kmp-cmp-reviewer/
│   ├── spec-reviewer/
│   └── template.md
├── scripts/              # 部署和工具脚本
│   └── deploy.sh         # 一键同步到 ~/.claude/（自动处理两级嵌套）
├── .github/
│   └── copilot-instructions.md   # Copilot 兼容层
└── CLAUDE.md             # 本文件
```

## Skill 开发规范

### Skill 元数据字段

```yaml
---
name: skill-name                    # 唯一标识，用于 /skill-name 调用
description: 何时触发（Claude 自动判断用）
tools: Read, Glob, Grep, Bash       # 允许的工具
disable-model-invocation: true      # true = 仅用户调用；false/省略 = Claude 也可调用
user-invocable: false               # false = 仅 Claude 调用；省略 = 两者都可
context: fork                       # fork = 隔离上下文运行
---
```

### 调用方式矩阵

| 场景               | disable-model-invocation | user-invocable | 说明              |
|--------------------|--------------------------|----------------|-------------------|
| 用户和 Claude 都可  | 省略                     | 省略           | 默认              |
| 仅用户手动触发      | true                     | 省略           | 有副作用的操作    |
| 仅 Claude 自动调用  | 省略                     | false          | 背景知识/规范     |
| 完全隔离运行        | 省略                     | 省略           | context: fork     |

## SubAgent 开发规范

SubAgent 是独立运行的 Claude 实例，适合并行的专项分析。

```yaml
---
name: agent-name
description: 触发场景描述
tools: Read, Grep, Glob             # 建议审查类 agent 只给只读权限
model: sonnet                       # opus/sonnet/haiku
---
```

## 部署方式

### 方式 1：本地项目部署（项目级）

```bash
# 复制到当前项目的 .claude 目录
./scripts/deploy.sh --project /path/to/your/project
```

### 方式 2：全局部署（用户级）

```bash
# 同步到 ~/.claude/
./scripts/deploy.sh --global
```

### 方式 3：打包为 Plugin（团队共享）

```bash
# 发布到 GitHub，团队成员用 /plugin install 安装
./scripts/deploy.sh --package
```

## Copilot 兼容

`.github/copilot-instructions.md` 会被 GitHub Copilot 自动读取。
Skills 和 Agents 的核心逻辑会被同步提取到该文件，实现跨工具复用。

运行 `./scripts/sync-copilot.sh` 自动同步。

## 快速开始

```bash
# 创建新通用 skill
cp -r skills/general/template skills/general/my-new-skill

# 创建新 XQ 专项 skill
cp -r skills/general/template skills/xq/xq-my-skill

# 创建新 Shimano 专项 skill
cp -r skills/general/template skills/shimano/my-skill

# 创建新 agent
cp agents/template.md agents/my-new-agent.md

# 部署到全局（自动处理 xq/shimano 两级嵌套）
./scripts/deploy.sh --global
```
