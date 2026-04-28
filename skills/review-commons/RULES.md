---
name: review-commons
description: 通用代码审查规则库。包含代码逻辑、Kotlin 惯用法、代码规范三个维度的检查项与输出格式标准。由所有 reviewer 工具在 Step 0 显式加载，不单独触发。
tools: Read
user-invocable: false
---

# 通用代码审查规则库

> 本文件由所有 review 工具在执行前 **显式 Read** 加载，不可单独触发。
> 各专项 reviewer 只需编写自身特有逻辑，通用部分统一引用此文件。

---

## 维度 A：代码逻辑

### A.1 空指针 / 崩溃风险

- `!!` 强解包：必须有明确的「此处不可能为 null」注释，否则标记为 Major
- 未处理的 null case：函数返回可空类型时，调用方是否完整处理了 null 路径
- 数组/集合越界：访问下标前是否有边界检查

### A.2 资源泄漏

- 协程未取消：`launch` / `async` 是否绑定了正确的 scope（`viewModelScope` / `lifecycleScope`），避免 `GlobalScope`
- Flow 未关闭：UI 层是否用 `collectAsState()` 而非裸 `collect {}`（后者在 Compose 中会泄漏）
- 文件 / 网络流：是否在 `finally` 块或 `use {}` 中关闭

### A.3 并发问题

- 共享可变状态：多线程/多协程访问的变量是否有适当的同步（`Mutex`、`StateFlow`、`Atomic*`）
- 非线程安全集合：`ArrayList`、`HashMap` 等在多协程场景下是否换成线程安全版本

### A.4 错误处理

- 吞异常：`catch (e: Exception) {}` 空块，或只打 log 不处理
- 协程内异常：`launch` 块内的异常是否有 `CoroutineExceptionHandler` 或 `try/catch` 覆盖
- `Result<T>` / 密封类：error case 是否穷举处理（`when` 表达式不遗漏分支）

### A.5 边界条件

- 空集合、空字符串、0、负数、Int.MAX_VALUE 等极端值
- 列表操作：`first()` / `last()` / `[]` 前是否检查 `isEmpty()`（应改用 `firstOrNull()`）

### A.6 逻辑缺陷

- 永远为 true/false 的条件分支（死代码）
- `if/else` / `when` 遗漏分支（非穷举的 `when` 且没有 `else`）
- 循环内 IO / 数据库查询（N+1 问题）

---

## 维度 B：Kotlin 惯用法

### B.1 Null Safety

```kotlin
// ❌ 不安全
val name = user!!.name

// ✅ 安全
val name = user?.name ?: "Unknown"
val name = requireNotNull(user) { "user must not be null" }.name
```

### B.2 协程与 Flow

```kotlin
// ❌ 阻塞主线程
fun load() = runBlocking { repo.fetch() }

// ✅ 主线程安全
suspend fun load() = withContext(Dispatchers.IO) { repo.fetch() }

// ❌ 热流暴露可变状态
var _state = MutableStateFlow(UiState())
val state = _state  // 外部可强转回 Mutable

// ✅ 只读暴露
private val _state = MutableStateFlow(UiState())
val state: StateFlow<UiState> = _state.asStateFlow()
```

### B.3 数据建模

- 优先 `data class` 做值语义建模
- 用 `sealed class` / `sealed interface` 穷举状态（`Result<T>`、`UiState`、Loading/Success/Error）
- 公共 API 返回 `List<T>` 而非 `MutableList<T>`

### B.4 作用域函数

- `apply`：对同一对象连续调用多个方法时使用
- `let`：可空值的非空分支处理（`value?.let { ... }`）
- `run`：需要返回值的代码块
- `also`：链式调用中做副作用（如日志）
- `with`：对同一对象进行多次读操作（无需返回值）

---

## 维度 C：代码规范

### C.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类 / 接口 / 枚举 | 大驼峰（PascalCase） | `PaymentViewModel` |
| 函数 / 变量 / 参数 | 小驼峰（camelCase） | `submitOrder()` |
| 常量（`const val` / `object`内） | 全大写下划线 | `MAX_RETRY_COUNT` |
| 文件名 | 与主类同名或大驼峰 | `PaymentScreen.kt` |
| 包名 | 全小写，点分隔 | `com.example.payment` |

### C.2 函数长度与复杂度

- 单个函数超过 **40 行**：建议拆分
- 单个文件超过 **300 行**：建议按职责拆分
- 嵌套层级超过 **3 层**：考虑提取子函数或使用 early return

### C.3 魔法数字 / 字符串

```kotlin
// ❌
delay(3000)
if (code == 404) { ... }

// ✅
const val NETWORK_TIMEOUT_MS = 3000L
const val HTTP_NOT_FOUND = 404
```

### C.4 可见性修饰符

- 能用 `private` 就不用 `internal`，能用 `internal` 就不用 `public`
- 不需要外部访问的类成员必须显式标 `private`
- `ViewModel` 的状态字段：`private val _state`，对外只暴露只读版本

### C.5 文档注释（KDoc）

- 所有 `public` / `internal` 函数和类：必须有 KDoc（`/** */`）
- 参数和返回值：复杂参数需要 `@param` / `@return` 说明
- `expect` 声明：必须在 KDoc 中说明各平台的行为差异

### C.6 测试覆盖

- 新增业务逻辑函数：是否有对应的单元测试
- 新增公共 API：是否有集成测试或 UI 测试覆盖主要路径

---

## 输出格式标准

### 严重程度（5 级）

| 级别 | 图标 | 定义 | 处理建议 |
|------|------|------|---------|
| Blocker | 🔴 | 必须修复，可能导致崩溃 / 数据丢失 / 安全漏洞 / 行为错误 | 合入前必须修复 |
| High | 🟠 | 存在明确缺陷或高风险路径，强烈建议修复 | 本迭代内修复 |
| Medium | 🟡 | 特定条件下可触发，或影响可维护性 | 下一迭代处理 |
| Low | 🔵 | 最佳实践偏差，直接风险较低 | 按需处理 |
| Info | ⚪ | 值得注意但不构成缺陷，或优秀实践 | 无需处理 |

**总体结论由最高等级驱动**：有 🔴 则结论为「阻断合入」，有 🟠 则为「需修改后合入」，全 🟡 以下则为「可合入」。

### 置信度

每条发现必须标注置信度，避免虚假告警：

| 置信度 | 含义 |
|-------|------|
| 高 | 有明确代码证据，路径可复现 |
| 中 | 有间接证据，需人工确认 |
| 低 | 基于模式推断，可能是误报 |

> 置信度为「低」的发现降一个等级处理（🔴→🟠，🟠→🟡）。

### 问题表格格式

```markdown
| 级别 | 类别 | 文件 | 行号 | 问题描述 | 证据 | 修复建议 | 置信度 |
|------|------|------|------|----------|------|---------|-------|
| 🔴 | 资源泄漏 | `Foo.kt` | L42 | 协程未绑定 scope | `GlobalScope.launch {}` | 改用 `viewModelScope` | 高 |
```

### 自验证步骤（所有 reviewer 在输出前必须执行）

在生成最终报告前，对每条候选发现执行以下检查：

```
1. 重新阅读相关代码（换一个视角）
2. 问自己："这在实际执行路径上真的会触发吗？"
3. 检查是否有框架层、基类或中间件已经处理了这个问题
4. 确认是否有明确的代码证据（文件路径 + 行号），没有则降级或丢弃
5. 确认最终严重等级与置信度是否匹配
```

> 无法用代码证据支撑的发现，标注置信度「低」或直接丢弃，不输出到报告。
