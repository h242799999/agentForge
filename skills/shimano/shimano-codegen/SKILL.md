---
name: shimano-codegen
description: Shimano 项目代码生成 Skill。按模块和层生成符合三层架构的 KMP 代码骨架，区分 SDK v1.0.0 和 v1.0.2 API，通过 RAG 获取业务规格，生成后自动执行 shimano-review 验证。当用户需要为 Shimano 项目生成代码、添加新功能模块时触发。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# Shimano 代码生成（shimano-codegen）

> 基于 SDK 接口 + RAG 业务规格 + 现有项目模式，生成符合三层架构的 Shimano 功能代码。
> 生成后自动触发 `shimano-review` 进行代码验证。

---

## 调用语法

```
/shimano-codegen <module> [--sdk 1.0.0|1.0.2] [--layer model|domain|data|ui|all] [--project <path>] [--preview]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<module>` | 目标模块（connection / auth / mybike / customize / riding / maintenance / unit） | 必填 |
| `--sdk` | 目标 SDK 版本 | `1.0.2` |
| `--layer` | 生成层（model / domain / data / ui / all） | `all` |
| `--project` | 应用项目根路径 | 当前目录 |
| `--preview` | 仅输出代码预览，不写文件 | — |

---

## SDK 接口根路径（硬编码）

```
/Users/xiao/Desktop/Projects/shimano-mobile-sdk/sdk/src/commonMain/kotlin/com/shimano/sdk/interfaces/
```

---

## Phase 1：解析参数 & 确认环境

### 1-A：参数解析

| 参数 | 值 | 备注 |
|------|-----|------|
| MODULE | 用户输入 | 必填，不能为空 |
| SDK_VERSION | `--sdk` 值，默认 `1.0.2` | 只接受 `1.0.0` 或 `1.0.2` |
| LAYER | `--layer` 值，默认 `all` | model / domain / data / ui / all |
| PROJECT_ROOT | `--project` 值，默认当前目录 | — |
| PREVIEW | 是否有 `--preview` flag | — |

### 1-B：环境验证

```bash
# 验证目标项目存在
ls <PROJECT_ROOT>/src 2>/dev/null || echo "ERROR_NO_PROJECT"

# 验证 SDK 模块存在
ls /Users/xiao/Desktop/Projects/shimano-mobile-sdk/sdk/src/commonMain/kotlin/com/shimano/sdk/interfaces/<MODULE>/ 2>/dev/null || echo "ERROR_NO_MODULE"
```

**若模块不存在**，列出可用模块后终止：

```bash
ls /Users/xiao/Desktop/Projects/shimano-mobile-sdk/sdk/src/commonMain/kotlin/com/shimano/sdk/interfaces/
```

输出：`❌ 模块 '<MODULE>' 不存在。可用模块：{列表}`

---

## Phase 2：加载基础规范（必须，不可跳过）

```
Read ~/.claude/skills/coding-standards/SKILL.md
```

提取并记住：
- 三层架构规则（presentation → domain → data → SDK）
- 包结构约定（`com.example.<app>/feature/<module>/`）
- 命名规范（Repository、UseCase、ViewModel、UiState 命名模式）
- Shimano SDK 专用约束（suspend/非suspend 调用规则，异常在 data 层 catch）

```
Read ~/.claude/skills/shimano-sdk-guard/SKILL.md
```

提取并记住：
- suspend vs 非-suspend API 完整清单（防止错误调用）
- 幻觉 API 黑名单（不存在的方法名）
- 异常类型及错误码前缀（CommonException/NetworkException/ConnectionException 等）
- SDK 调用必须在 `withContext(Dispatchers.IO)` 中执行

---

## Phase 3：版本感知 — 加载 SDK 接口

### 3-A：查找模块接口文件

```bash
find /Users/xiao/Desktop/Projects/shimano-mobile-sdk/sdk/src/commonMain/kotlin/com/shimano/sdk/interfaces/<MODULE>/ -name "*.kt" | sort
```

逐一读取所有接口文件，提取：
- 接口/数据类/枚举的完整签名
- 方法名、参数类型、返回类型
- `suspend` 标注（有无）

### 3-B：版本特定处理

**SDK v1.0.0 特有**：

| 类 | v1.0.0 行为 |
|----|------------|
| `CustomizeSettingConfig` | 存在，作为 CustomizePickSetting/CustomizeRangeSetting/CustomizeTextSetting 构造参数 |
| `CustomizePickSetting` 构造 | `CustomizePickSetting(currentValue, config: CustomizeSettingConfig<T>, valueList)` |
| `AssistCarryOver` | 仅 SHORT(0) / MIDDLE(1) / LONG(2) |
| `MaintenanceCategory` | 仅 ADJUST_STATUS / ERROR_LOG |

**SDK v1.0.2 特有（相比 v1.0.0 的变化）**：

| 类 / 方法 | v1.0.2 变化 |
|-----------|------------|
| `CustomizeSettingConfig` | **已删除**，不可使用 |
| `CustomizePickSetting` 构造 | 扁平化 8 参数：`(name, currentValue, defaultValue, changeable, isRelation, valueUnit, valid, valueList)` |
| `CustomizeRangeSetting` 构造 | 同样扁平化，包含 minValue / maxValue / stepValue |
| `CustomizeTextSetting` 构造 | 同样扁平化 |
| `AssistCarryOver` | 新增 `EXTRA_LONG(3)` |
| `MaintenanceCategory` | 新增 FRONT_ADJUST / REAR_ADJUST / GEAR_USAGE_RATE |
| `Maintenance` 新接口 | `suspend fun getGearUsageRateInfo(): GearUsageRateInfo` |
| `Maintenance` 新接口 | `suspend fun resetGearHistory()` |
| `MaintenanceException` | 新增 3 个错误码（E-7001-0004/0005/0008） |

**v1.0.2 额外读取（仅 maintenance 模块）**：

```bash
find /Users/xiao/Desktop/Projects/shimano-mobile-sdk/sdk/src/commonMain/kotlin/com/shimano/sdk/interfaces/maintenance/ -name "AdjustValue.kt" -o -name "GearInfo.kt" -o -name "GearUsageRate*.kt" | sort
```

逐一读取上述数据类文件。

---

## Phase 4：探索当前项目已有实现（模式匹配）

### 4-A：找同模块现有文件

```bash
find <PROJECT_ROOT>/src -name "*.kt" | xargs grep -l "<Module>\|<module>" 2>/dev/null | head -20
```

读取现有同模块文件，提取：
- **包名约定**（如 `com.shimano.myapp.feature.connection`）
- **DI 框架**（`@HiltViewModel` / `@KoinViewModel` 等）
- **基类继承**（ViewModel 是否有基类）
- **命名风格**（PascalCase 确认）

### 4-B：检查是否存在低版本实现（仅 --sdk 1.0.2 时执行）

```bash
find <PROJECT_ROOT>/src -name "<Module>RepositoryImpl.kt" -o -name "<Module>Repository.kt" | head -5
```

**若低版本实现存在**：
- 读取 `<Module>RepositoryImpl.kt` 全文
- 生成策略切换为**扩展模式**：
  - Data 层：继承现有 RepositoryImpl 或新增方法，**不重写已有代码**
  - Domain 层：只新增 UseCase，不删除已有 UseCase
  - 在生成摘要中注明："发现 v1.0.0 实现，已采用扩展模式"

### 4-C：识别 DI 框架

```bash
grep -r "hilt\|koin\|dagger" <PROJECT_ROOT>/build.gradle.kts <PROJECT_ROOT>/app/build.gradle.kts 2>/dev/null | head -5
```

记住 DI 框架，代码生成时使用对应注解。

---

## Phase 5：RAG 业务规格查询

对每个 MODULE 执行 2-3 个查询：

**Query 1 — 模块业务流程**：
```
mcp__ragforge__rag_query(
  project="shimano",
  query="<MODULE> 機能仕様 業務フロー 状態機",
  top_k=5
)
```

**Query 2 — API 接口规格**：
```
mcp__ragforge__rag_query(
  project="shimano",
  query="<MODULE> API インターフェース パラメータ 戻り値",
  top_k=5
)
```

**Query 3 — 错误码（按需，模块涉及异常处理时）**：
```
mcp__ragforge__rag_query(
  project="shimano",
  query="<MODULE> エラーコード 例外処理",
  top_k=5,
  has_table=true
)
```

❌ **RAG 不可用时**：
- 不终止流程，继续基于 SDK 接口和现有代码生成
- 在生成摘要头部注明：
  ```
  ⚠️ RAG 降级模式：业务规格查询失败，代码基于 SDK 接口和现有实现生成，置信度降低
  ```

整理 RAG 结果：
- 按来源文档（metadata.file）和章节（metadata.section_path）分组
- 格式化引用标记：`[来源: <file_basename> > <section_path>]`
- 提取状态机（含 mermaid 的 chunk）、参数表（含 table 的 chunk）

---

## Phase 6：按层生成代码

根据 `--layer` 参数生成对应层。所有生成代码遵循 Phase 2 加载的规范。

**包路径约定**（基于 Phase 4-A 探索结果）：
```
<discovered_package>.feature.<module>.model.<Class>.kt
<discovered_package>.feature.<module>.domain.<Class>.kt
<discovered_package>.feature.<module>.data.<Class>.kt
<discovered_package>.feature.<module>.ui.<Class>.kt
```

---

### § Model 层

生成文件：`<module>/model/<Module>.kt`

```kotlin
// [来源: <RAG 引用> 或 SDK 接口 <文件名>]
package <package>.feature.<module>.model

data class <Module>Info(
    val <field>: <Type>,  // <RAG/SDK 说明>
    // TODO: validate - 根据规格补充字段约束
)

sealed class <Module>State {
    data object Idle : <Module>State()
    data class Success(val data: <Module>Info) : <Module>State()
    data class Error(val cause: <Module>Error) : <Module>State()
}

sealed class <Module>Error {
    data class SdkError(val code: String, val message: String) : <Module>Error()
    data object NotConnected : <Module>Error()
    // TODO: error-handling - 根据 SDK 异常类型补充错误分支
}
```

---

### § Domain 层

生成文件：
- `<module>/domain/<Module>Repository.kt`（接口）
- `<module>/domain/<Action><Module>UseCase.kt`（按 RAG/SDK 操作数量生成多个）

```kotlin
// <Module>Repository.kt
package <package>.feature.<module>.domain

interface <Module>Repository {
    suspend fun get<Module>Info(): Result<<Module>Info>
    // TODO: implement - 根据规格补充所有 Repository 方法
}
```

```kotlin
// Get<Module>InfoUseCase.kt
package <package>.feature.<module>.domain

class Get<Module>InfoUseCase(
    private val repository: <Module>Repository
) {
    suspend operator fun invoke(): Result<<Module>Info> =
        repository.get<Module>Info()
}
```

---

### § Data 层

生成文件：`<module>/data/<Module>RepositoryImpl.kt`

**标准模式（无已有 v1.0.0 实现）**：

```kotlin
package <package>.feature.<module>.data

import com.shimano.sdk.interfaces.ShimanoLoader
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class <Module>RepositoryImpl(
    private val shimanoLoader: ShimanoLoader
) : <Module>Repository {

    override suspend fun get<Module>Info(): Result<<Module>Info> =
        withContext(Dispatchers.IO) {
            try {
                // SDK v<SDK_VERSION> API — 根据 shimano-sdk-guard 规则调用
                val sdk<Module> = shimanoLoader.get<Module>()
                // TODO: implement - 调用正确的 SDK 方法
                Result.success(<Module>Info(/* ... */))
            } catch (e: <SDK>Exception) {
                // TODO: error-handling - 按错误码前缀分类处理
                Result.failure(<Module>Error.SdkError(e.code, e.message ?: ""))
            }
        }
}
```

**扩展模式（检测到已有 v1.0.0 实现时，仅 --sdk 1.0.2）**：

```kotlin
// 基于现有 <Module>RepositoryImpl 扩展，新增 v1.0.2 API
// 不重写已有方法

// 新增方法（v1.0.2 新接口）
override suspend fun get<NewFeature>(): Result<<NewEntity>> =
    withContext(Dispatchers.IO) {
        try {
            shimanoLoader.get<Module>().<newMethod>()
            // TODO: implement
        } catch (e: <SDK>Exception) {
            Result.failure(...)
        }
    }
```

**customize 模块版本差异**：

```kotlin
// v1.0.0 — 使用 CustomizeSettingConfig
val setting = CustomizePickSetting(
    currentValue = ...,
    config = CustomizeSettingConfig(name = ..., defaultValue = ..., ...),
    valueList = listOf(...)
)

// v1.0.2 — 扁平化参数，CustomizeSettingConfig 已删除
val setting = CustomizePickSetting(
    name = ...,
    currentValue = ...,
    defaultValue = ...,
    changeable = true,
    isRelation = false,
    valueUnit = null,
    valid = true,
    valueList = listOf(...)
)
```

---

### § UI 层

生成文件：
- `<module>/ui/<Module>UiState.kt`
- `<module>/ui/<Module>ViewModel.kt`

```kotlin
// <Module>UiState.kt
package <package>.feature.<module>.ui

data class <Module>UiState(
    val isLoading: Boolean = false,
    val <data>: <Module>Info? = null,
    val error: String? = null
)
```

```kotlin
// <Module>ViewModel.kt
package <package>.feature.<module>.ui

// 根据 DI 框架（Phase 4-C）使用对应注解
@HiltViewModel  // 或 @KoinViewModel
class <Module>ViewModel @Inject constructor(  // 或 constructor(
    private val get<Module>InfoUseCase: Get<Module>InfoUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(<Module>UiState())
    val uiState: StateFlow<<Module>UiState> = _uiState.asStateFlow()

    fun load<Module>() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            get<Module>InfoUseCase()
                .onSuccess { info ->
                    _uiState.update { it.copy(isLoading = false, <data> = info) }
                }
                .onFailure { error ->
                    _uiState.update { it.copy(isLoading = false, error = error.message) }
                }
        }
    }
}
```

---

## Phase 7：输出生成摘要 & 自动 Review

### 7-A：生成摘要

```
## 生成摘要

SDK 版本：{SDK_VERSION}
目标模块：{MODULE}
生成层：{LAYER}
生成模式：{全新生成 | 扩展模式（基于 v1.0.0 实现）}
规格来源：{RAG（N 条 chunk，来自 M 个章节）| 降级（RAG 不可用）}

生成文件：
  - {路径1}
  - {路径2}
  - ...

（--preview 模式：以上为预览，未写入文件）
```

### 7-B：自动调用 shimano-review

对生成的文件执行：

```
/shimano-review <生成文件路径列表> --code --ui
```

若 RAG 查询成功（有规格来源），追加业务审查：

```
/shimano-review <生成文件路径列表> --business
```

Review 报告直接输出到当前响应，无需用户手动触发。

---

## 版本差异速查（Phase 3 & Phase 6 参考）

| API / 类 | v1.0.0 | v1.0.2 |
|----------|--------|--------|
| `CustomizeSettingConfig` | 存在 | **已删除** |
| `CustomizePickSetting` 构造 | 3 参数（currentValue, config, valueList） | 8 参数（name 开头的扁平化参数） |
| `AssistCarryOver` | SHORT / MIDDLE / LONG | +EXTRA_LONG |
| `MaintenanceCategory` | ADJUST_STATUS / ERROR_LOG | +FRONT_ADJUST / REAR_ADJUST / GEAR_USAGE_RATE |
| `Maintenance.getGearUsageRateInfo()` | 不存在 | `suspend fun`，返回 `GearUsageRateInfo` |
| `Maintenance.resetGearHistory()` | 不存在 | `suspend fun` |
| `MaintenanceException` 错误码数量 | 3 个 | 6 个 |

---

## 可用模块列表

```
connection   — BLE 连接管理（StatusListener、BLEDeviceStatus）
auth         — 用户认证（Auth、Continent、Country）
mybike       — 自行车管理（MyBikeInfo、BikeCableConnectionListener）
customize    — 自定义配置（CustomizeSetting 体系，注意 v1.0.2 Breaking Change）
riding       — 骑行数据（RidingAssistMode、RidingProfileType）
maintenance  — 保养提醒（Maintenance、MaintenanceAlertListener，v1.0.2 新增齿轮功能）
unit         — 外设管理（SwitchUnit、WirelessSwitchUnit、WirelessBatteryLevel）
```
