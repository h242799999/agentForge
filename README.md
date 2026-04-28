# agentForge

用于开发和分发 Claude Code Skills / SubAgents 的工作坊项目。

目前包含：

- **kmp-cmp-reviewer** — Kotlin Multiplatform / Compose Multiplatform 专项代码审查 Agent
- **commit-reviewer** — git commit 增量变更审查 Agent（代码逻辑 / 业务逻辑 / 代码规范）
- **spec-reviewer** — 对照设计文档审查代码实现 Agent

---

## 安装

### 方式一：deploy.sh 一键部署（推荐）

同时部署到 Claude Code 和 JetBrains Copilot：

```bash
git clone https://github.com/h242799999/agentForge.git
cd agentForge
./scripts/deploy.sh --global
```

| 参数 | 部署目标 |
|------|---------|
| `--global` | `~/.claude/`（Claude Code）+ `~/.copilot/skills/`（JetBrains）|
| `--claude` | 仅 `~/.claude/`（Claude Code）|
| `--copilot` | 仅 `~/.copilot/skills/`（JetBrains Copilot）|

部署后 JetBrains IDE 重启即可生效，Claude Code 无需重启。

### 更新

```bash
git pull origin main
./scripts/deploy.sh --global
```

---

### 方式二：Claude Code Plugin（仅 Claude Code）

```bash
# 1. 注册 marketplace（一次性）
/plugin marketplace add h242799999/agentForge

# 2. 安装插件
/plugin install agent-forge@agent-forge-marketplace

# 3. 重新加载
/reload-plugins
```

更新插件：
```bash
/plugin update agent-forge@agent-forge-marketplace
/reload-plugins
```

---

### 方式三：VSCode Copilot Chat（VS Code 1.99+）

VSCode Copilot Chat 使用 `.github/prompts/` 目录中的 `.prompt.md` 文件作为斜杠命令。

在你的项目中执行：

```bash
mkdir -p .github/prompts
curl -o .github/prompts/kmp-cmp-reviewer.prompt.md \
  https://raw.githubusercontent.com/h242799999/agentForge/main/.github/prompts/kmp-cmp-reviewer.prompt.md
curl -o .github/prompts/commit-reviewer.prompt.md \
  https://raw.githubusercontent.com/h242799999/agentForge/main/.github/prompts/commit-reviewer.prompt.md
```

> 需在 VS Code 设置中开启：`chat.promptFiles: true`

---

## 使用

| Agent | Claude Code CLI（@ 提及） | VSCode Copilot Chat（斜杠命令）|
|-------|--------------------------|-------------------------------|
| kmp-cmp-reviewer | `@agent-forge:kmp-cmp-reviewer` | `/kmp-cmp-reviewer` |
| commit-reviewer | `@agent-forge:commit-reviewer` | `/commit-reviewer` |
| spec-reviewer | `@agent-forge:spec-reviewer` | — |

> **Claude Code @ 提及**：输入 `@` 后从弹出列表选择，或直接输入 `@agent-forge:` 前缀。  
> **VSCode 斜杠命令**：在 Copilot Chat 输入框输入 `/`，从弹出列表选择。

---

## commit-reviewer

审查 git commit 的增量变更，覆盖**代码逻辑 / 业务逻辑 / 代码规范**三个维度，只看 diff 变更行。

### 调用方式

**Claude Code（@ 提及）：**

```
@agent-forge:commit-reviewer review HEAD 这笔 commit
@agent-forge:commit-reviewer 审查最近 3 笔 commit
@agent-forge:commit-reviewer HEAD~3..HEAD 有没有问题
```

**斜杠命令（Copilot CLI）：**

```
/commit-reviewer HEAD
/commit-reviewer HEAD~3..HEAD
/commit-reviewer <commitId>
/commit-reviewer --branch feature/xxx
```

### 支持模式

| 模式 | 示例 |
|------|------|
| 单笔 commit | `HEAD` 或具体 commitId |
| 多笔范围 | `HEAD~3..HEAD` 或 `id1..id2` |
| 整个分支 | `--branch feature/xxx`（对比 main）|

### 常用示例

| 场景 | 命令 |
|------|------|
| review 最新一笔 | `@agent-forge:commit-reviewer review HEAD` |
| review 最近 3 笔 | `@agent-forge:commit-reviewer HEAD~3..HEAD` |
| review 整个功能分支 | `@agent-forge:commit-reviewer --branch feature/payment` |
| 指定 commit | `@agent-forge:commit-reviewer abc1234` |

### 审查维度

| 维度 | 关注点 |
|------|--------|
| 代码逻辑 | 空指针、资源泄漏、并发、错误处理缺失、边界条件 |
| 业务逻辑 | 意图对齐、完整性、数据一致性、向后兼容 |
| 代码规范 | 命名、函数长度、魔法数字、可见性修饰符、KDoc |

> 与 `kmp-cmp-reviewer` 互补：commit-reviewer 聚焦**变更视角**，kmp-cmp-reviewer 聚焦 **KMP/CMP 静态规范**。

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

## 更新 Claude Code

```bash
# 更新 Claude Code CLI 本体
npm update -g @anthropic-ai/claude-code

# 查看当前版本
claude --version
```

> Claude Code 通过 npm 全局安装，`update` 会拉取最新版本。如果 `update` 无效，用 `install` 覆盖：
> ```bash
> npm install -g @anthropic-ai/claude-code
> ```

---

## 更新插件（开发者发布流程）

### 第一步：修改内容

在 `skills/` 或 `agents/` 中编辑对应文件：

```
skills/kmp-cmp-reviewer/SKILL.md     ← 斜杠命令逻辑
agents/kmp-cmp-reviewer/AGENT.md     ← SubAgent 逻辑
agents/kmp-cmp-reviewer/REPORT_TEMPLATE.md  ← 报告模板
```

### 第二步：更新版本号

编辑 `.claude-plugin/plugin.json`，递增 `version` 字段：

```json
{
  "version": "1.0.1"
}
```

版本号规则：`major.minor.patch`
- patch（`1.0.0 → 1.0.1`）：修复 bug、优化措辞
- minor（`1.0.0 → 1.1.0`）：新增 skill 或 agent
- major（`1.0.0 → 2.0.0`）：不兼容的接口变更

### 第三步：提交并推送

```bash
git add .
git commit -m "feat: 描述改动内容"
git push origin main
```

### 第四步：本地重新部署（验证）

```bash
./scripts/deploy.sh --global
```

重新部署后，**Claude Code 无需重启**，下次对话自动加载新版本。

---

### 用户侧更新

已通过 `deploy.sh` 部署的用户，重新拉取并执行：

```bash
git pull origin main
./scripts/deploy.sh --global
```

通过 plugin 市场安装的用户：

**Claude Code：**
```bash
/plugin update agent-forge@agent-forge-marketplace
```

**GitHub Copilot CLI：**
```bash
copilot plugin update agent-forge@agent-forge-marketplace
```
