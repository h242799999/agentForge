---
name: kmp-cmp-reviewer
description: 对 Kotlin Multiplatform (KMP) 或 Compose Multiplatform (CMP) 代码进行审查时触发。覆盖跨平台架构、Compose UI、Kotlin 惯用法、性能、可测试性五个维度，输出结构化报告。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# KMP/CMP Code Review Skill

> 通过 `/kmp-cmp-reviewer [路径或描述]` 触发，在当前对话上下文中执行 KMP/CMP 专项代码审查，输出结构化报告。

## 触发方式

```
/kmp-cmp-reviewer                                    # 自动扫描当前项目
/kmp-cmp-reviewer src/commonMain/kotlin/             # 指定目录
/kmp-cmp-reviewer HomeViewModel.kt                   # 指定文件
/kmp-cmp-reviewer 只看 Compose UI 和 State 管理部分   # 自然语言描述范围
```

## 执行步骤

### Step 1：确定审查范围

- 若用户指定了路径 → 以该路径为范围
- 若用户未指定 → 自动扫描常见 KMP 源码目录：
  - `**/commonMain/kotlin/`
  - `**/androidMain/kotlin/`
  - `**/iosMain/kotlin/`
  - `**/composeApp/src/`
  - `**/shared/src/`

### Step 2：项目探针

读取构建配置，识别项目类型和 targets：

```bash
# 确认 KMP targets
cat build.gradle.kts 2>/dev/null | grep -A 20 "kotlin {"
cat build.gradle 2>/dev/null | grep -A 20 "kotlin {"

# 扫描 expect 声明（KMP 跨平台接口）
grep -r "^expect " --include="*.kt" -l

# 统计各 source set 文件数
find . -path "*/commonMain/kotlin/*.kt" | wc -l
find . -path "*/androidMain/kotlin/*.kt" | wc -l
find . -path "*/iosMain/kotlin/*.kt" | wc -l
```

### Step 3：五维度审查

按以下顺序逐项检查，重点关注高权重维度。

---

#### 维度 1：KMP 跨平台架构（权重 30%）

**1.1 expect/actual 规范性**
- `expect` 声明是否全部在 `commonMain` 中
- 所有 `actual` 实现是否覆盖所有已声明 target
- 是否使用 `actual typealias` 代替重复实现（Android/JVM 场景）

```kotlin
// ✅ 正确
actual typealias PlatformContext = android.content.Context

// ❌ commonMain 中误用平台包
import android.content.Context  // 不应出现在 commonMain
```

**1.2 Source Set 分层**
- `commonMain` 是否意外引入平台专属依赖（`android.*`、`UIKit` 等）
- 平台专属 UI 是否放入对应 `platformMain`

**1.3 依赖管理**
- `commonMain` 依赖是否使用多平台兼容库（kotlinx-coroutines、Ktor、kotlinx-serialization）
- 版本目录（`libs.versions.toml`）使用是否一致

**1.4 Kotlin/Native 线程（iOS）**
- 新 MM 下是否存在不必要的 freeze 调用
- 是否在非主线程访问 UI 对象

---

#### 维度 2：Compose Multiplatform UI（权重 25%）

**2.1 Composable 函数设计**
- 是否遵循单一职责（一个 Composable 只做一件事）
- 参数列表是否超过 7 个（建议提取数据类）
- 是否避免在 Composable 内直接进行副作用

**2.2 State Hoisting & 单向数据流**
- 是否存在 ViewModel 直接暴露 `MutableState` / `MutableStateFlow` 给 UI

```kotlin
// ❌ 反模式
var count by mutableStateOf(0)

// ✅ 正确
private val _uiState = MutableStateFlow(UiState())
val uiState: StateFlow<UiState> = _uiState.asStateFlow()
```

**2.3 重组性能**
- `LazyColumn` / `LazyRow` 的 `items` 是否提供稳定的 `key`
- 是否使用 `derivedStateOf` 替代计算密集型 `remember`
- `@Stable` / `@Immutable` 注解是否合理使用

```kotlin
// ❌ 缺少 key，重组时列表项顺序错乱
items(list) { item -> ItemRow(item) }

// ✅ 提供稳定 key
items(list, key = { it.id }) { item -> ItemRow(item) }
```

**2.4 副作用管理**
- `LaunchedEffect` 的 key 是否正确设置
- `DisposableEffect` 是否有配套的 `onDispose` 清理
- `Flow` 在 UI 层是否用 `collectAsState()` 而非裸 `collect {}`

**2.5 平台 UI 适配**
- 是否为不同平台提供自适应布局（`WindowSizeClass`）

---

#### 维度 3：Kotlin 惯用法（权重 20%）

**3.1 Null Safety**
- 是否存在不必要的 `!!` 强制解包

**3.2 协程与 Flow**
- 是否避免 `GlobalScope` 使用
- `suspend` 函数是否遵循主线程安全原则

```kotlin
// ❌ 阻塞主线程
fun loadData() = runBlocking { repo.fetch() }

// ✅ 主线程安全
suspend fun loadData() = withContext(Dispatchers.IO) { repo.fetch() }
```

**3.3 数据建模**
- `sealed class` / `sealed interface` 是否用于穷举状态
- 是否避免暴露可变集合（返回 `List` 而非 `MutableList`）

---

#### 维度 4：架构模式（权重 15%）

- 是否清晰分为 `presentation` / `domain` / `data` 三层
- `ViewModel` 是否只持有 UI 状态，不直接操作数据库/网络
- Koin module 是否按功能划分

---

#### 维度 5：可测试性与可维护性（权重 10%）

- `commonMain` 业务逻辑是否有对应 `commonTest`
- 函数长度是否超过 40 行
- 是否存在魔法数字 / 魔法字符串

---

### Step 4：输出报告

按以下模板输出：

```markdown
# KMP/CMP 代码审查报告

**审查范围**：`{路径}`
**审查时间**：`{日期}`
**项目 Targets**：`{android | ios | desktop | web}`

## 总体评级

| 维度 | 评分（1-5） | 状态 |
|------|------------|------|
| KMP 跨平台架构 | ⭐⭐⭐⭐ | 良好 |
| Compose UI 设计 | ⭐⭐⭐ | 需改进 |
| Kotlin 惯用法 | ⭐⭐⭐⭐⭐ | 优秀 |
| 架构模式 | ⭐⭐⭐⭐ | 良好 |
| 可测试性 | ⭐⭐ | 警告 |
| **综合评级** | **⭐⭐⭐⭐** | **良好** |

## 🔴 严重问题（Critical）
> 必须修复，可能导致运行时崩溃、内存泄漏或跨平台兼容性断裂

| # | 文件 | 行号 | 问题描述 | 修复建议 |
|---|------|------|----------|----------|

## 🟠 主要问题（Major）
> 强烈建议修复，影响可维护性、性能或最佳实践

| # | 文件 | 行号 | 问题描述 | 修复建议 |
|---|------|------|----------|----------|

## 🟡 次要问题（Minor）

| # | 文件 | 行号 | 问题描述 | 修复建议 |
|---|------|------|----------|----------|

## 💡 建议（Suggestions）
- ...

## ✅ 亮点（Highlights）
- ...

## 行动计划

### 立即处理（本次 PR 合并前）
1. ...

### 近期规划
1. ...
```

## 快速 Anti-Pattern 扫描清单

执行审查前先快速扫描以下高频问题：

```
[ ] commonMain 中出现 android.* / UIKit 等平台包 import
[ ] expect 声明缺少某个 target 的 actual 实现
[ ] Composable 函数内直接调用 suspend 函数（未用 LaunchedEffect）
[ ] ViewModel 中使用 GlobalScope
[ ] MutableStateFlow / MutableState 直接暴露给 UI 层
[ ] LazyColumn/LazyRow 的 items 没有提供 key
[ ] DisposableEffect 缺少 onDispose 清理
[ ] Kotlin/Native 在非主线程访问 UI 对象
[ ] !! 强解包没有明确的空值不可能说明
[ ] Flow 在 UI 层用 .collect {} 代替 collectAsState()（导致泄漏）
```
