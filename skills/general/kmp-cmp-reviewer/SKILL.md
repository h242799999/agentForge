---
name: kmp-cmp-reviewer
description: 对 Kotlin Multiplatform (KMP) 或 Compose Multiplatform (CMP) 代码进行审查时触发。覆盖跨平台架构、Compose UI 设计、架构模式三个 KMP/CMP 专项维度，通用代码规范由 review-commons 提供。
tools: Read, Grep, Glob, Bash, Write
disable-model-invocation: true
---

# KMP/CMP Code Review Skill

> 通过 `/kmp-cmp-reviewer [路径或描述]` 触发。
> **通用规则**（代码逻辑、Kotlin 惯用法、命名规范）由 `review-commons/RULES.md` 统一提供，本 Skill 只编写 KMP/CMP 专项内容。

---

## 触发方式

```
/kmp-cmp-reviewer                                    # 自动扫描当前项目
/kmp-cmp-reviewer src/commonMain/kotlin/             # 指定目录
/kmp-cmp-reviewer HomeViewModel.kt                   # 指定文件
/kmp-cmp-reviewer 只看 Compose UI 和 State 管理部分   # 自然语言描述范围
```

---

## 执行步骤

### Step 0：加载规则与清单

Read `skills/review-commons/RULES.md`（代码逻辑 + Kotlin 惯用法 + 代码规范 + 输出格式）

Read `skills/kmp-cmp-reviewer/references/kmp-checklist.md`（KMP/CMP 专项检查清单）

> ⚠️ 以上文件内容**仅供内部参考，禁止输出到 chat**。

---

### Step 1：确定审查范围 & 项目探针

```bash
# 确认 KMP targets
grep -A 20 "kotlin {" build.gradle.kts 2>/dev/null

# 扫描 expect 声明
grep -r "^expect " --include="*.kt" -l

# 各 source set 文件数
find . -path "*/commonMain/kotlin/*.kt" | wc -l
find . -path "*/androidMain/kotlin/*.kt" | wc -l
find . -path "*/iosMain/kotlin/*.kt" | wc -l
```

---

### Step 2：KMP/CMP 专项审查

#### 专项 1：KMP 跨平台架构（权重 30%）

**expect/actual 规范性**
- `expect` 声明是否全部在 `commonMain` 中
- 所有 `actual` 实现是否覆盖所有已声明 target
- 是否使用 `actual typealias` 代替重复实现（Android/JVM 场景）

```kotlin
// ✅ 正确：typealias 复用
actual typealias PlatformContext = android.content.Context

// ❌ commonMain 中误用平台包
import android.content.Context
```

**Source Set 分层**
- `commonMain` 是否意外引入平台专属依赖（`android.*`、`UIKit` 等）
- 平台专属 UI 是否放入对应 `platformMain`
- `commonMain` 依赖是否使用多平台兼容库（kotlinx-coroutines、Ktor、kotlinx-serialization）
- 版本目录（`libs.versions.toml`）使用是否一致

**Kotlin/Native 线程（iOS）**
- 新 MM 下是否存在不必要的 freeze 调用
- 是否在非主线程访问 UI 对象

---

#### 专项 2：Compose Multiplatform UI（权重 25%）

**Composable 函数设计**
- 是否遵循单一职责（一个 Composable 只做一件事）
- 参数列表是否超过 7 个（建议提取数据类）
- 是否避免在 Composable 内直接进行副作用（IO、网络请求）

**State Hoisting & 单向数据流**
- 是否存在 ViewModel 直接暴露 `MutableState` / `MutableStateFlow` 给 UI

```kotlin
// ❌ 反模式：暴露可变状态
var count by mutableStateOf(0)

// ✅ 只读暴露
private val _uiState = MutableStateFlow(UiState())
val uiState: StateFlow<UiState> = _uiState.asStateFlow()
```

**重组性能**
- `LazyColumn` / `LazyRow` 的 `items` 是否提供稳定的 `key`
- 是否使用 `derivedStateOf` 替代计算密集型 `remember`
- `@Stable` / `@Immutable` 注解是否合理使用

```kotlin
// ❌ 缺少 key
items(list) { item -> ItemRow(item) }

// ✅ 提供稳定 key
items(list, key = { it.id }) { item -> ItemRow(item) }
```

**副作用管理**
- `LaunchedEffect` 的 key 是否正确设置
- `DisposableEffect` 是否有配套的 `onDispose` 清理
- `Flow` 在 UI 层是否用 `collectAsState()` 而非裸 `collect {}`

**平台 UI 适配**
- 是否为不同平台提供自适应布局（`WindowSizeClass`）

---

#### 专项 3：架构模式（权重 15%）

- 是否清晰分为 `presentation` / `domain` / `data` 三层
- `ViewModel` 是否只持有 UI 状态，不直接操作数据库/网络
- Koin module 是否按功能划分，避免循环依赖
- Navigation 是否使用类型安全的路由（Kotlin Serialization + Navigation 3 / Decompose）

---

### Step 3：应用通用规则

- 应用 RULES.md「维度 A」对所有审查文件做代码逻辑检查
- 应用 RULES.md「维度 B」检查 Kotlin 惯用法
- 应用 RULES.md「维度 C」检查代码规范

---

### Step 4：输出报告并【必须执行】保存

使用 RULES.md 中定义的**输出格式标准**生成报告：

```markdown
# KMP/CMP 代码审查报告

**审查范围**：`{路径}`
**审查时间**：`{日期}`
**项目 Targets**：`{android | ios | desktop | web}`

## 总体结论

> `🔴 阻断合入` / `🟠 需修改后合入` / `✅ 可合入` — {核心原因一句话}

## 各维度摘要

| 维度 | 最高等级 | 发现数 |
|------|---------|-------|
| KMP 跨平台架构 | 🟡 | 2 |
| Compose UI 设计 | 🔴 | 1 |
| 架构模式 | ⚪ | 0 |
| 通用代码质量 | 🟠 | 3 |

## 问题列表（按严重程度排序）

| 级别 | 类别 | 文件 | 行号 | 问题描述 | 修复建议 | 置信度 |
|------|------|------|------|----------|---------|-------|
| 🔴 | Compose副作用 | `HomeScreen.kt` | L87 | ... | ... | 高 |

## ✅ 亮点

## 行动计划
### 必须修复（合入前）
### 近期规划
```

### 【必须执行】保存报告

> ⚠️ **此步骤不可省略**，无论是否发现问题，均须写入文件。

```bash
git config user.name
date +"%Y%m%d-%H%M"
mkdir -p reviewer
```

命名规则（取审查路径最后一级目录名或文件名）：
```
reviewer/<git-user-name>-<target-basename>-<YYYYMMDD-HHmm>.md
```

将上方完整报告内容写入对应路径的 `.md` 文件（使用 Write 工具）。写入后输出：

```
💾 报告已保存：reviewer/<filename>
```

> ⚠️ 禁止自动执行 `git add` / `git commit`。

---

## KMP/CMP 快速扫描清单

```
[ ] commonMain 中出现 android.* / UIKit 等平台包 import
[ ] expect 声明缺少某个 target 的 actual 实现
[ ] Composable 函数内直接调用 suspend 函数（未用 LaunchedEffect）
[ ] ViewModel 中使用 GlobalScope
[ ] MutableStateFlow / MutableState 直接暴露给 UI 层
[ ] LazyColumn/LazyRow 的 items 没有提供 key
[ ] DisposableEffect 缺少 onDispose 清理
[ ] Kotlin/Native 在非主线程访问 UI 对象
```
