---
name: coding-standards
description: 查看或应用 KMP + Compose 编码规范。当需要了解代码生成约定、层架构规则、包结构规范时触发。也被 spec-codegen 在生成代码前自动加载。用法：/coding-standards 或 /coding-standards --layer ui
tools: Read
---

# coding-standards：KMP + Compose 编码规范

> 本规范分两部分：
> - **Part A**：通用 Kotlin 代码质量规则（来自 `review-commons/RULES.md`，显式 Read 加载）
> - **Part B**：代码生成专用约定（本文件内联）

---

## 加载通用规则

```bash
# Step 0：加载 review-commons 规则
# Read: skills/review-commons/RULES.md
```

执行：**Read `skills/review-commons/RULES.md`**，加载所有 Kotlin 代码质量规则（维度 A/B/C）。

---

## Part B：代码生成专用约定

### B-1 包结构

```
com.example.<app>/
├── feature/
│   └── <module>/            # 按功能模块划分（auth、connection、customize…）
│       ├── model/           # 数据模型（data class、sealed class、enum）
│       ├── domain/          # 业务逻辑（UseCase、Repository interface）
│       ├── data/            # 数据层实现（RepositoryImpl、数据源）
│       └── ui/              # UI 层（ViewModel、UiState、Composable）
├── core/
│   ├── network/             # 网络基础设施
│   ├── ble/                 # BLE / Shimano SDK 封装
│   └── di/                  # 依赖注入模块
```

### B-2 文件命名规则

| 层 | 命名模式 | 示例 |
|---|---|---|
| Model | `<Entity>.kt` | `DeviceUnit.kt` |
| Domain Repository | `<Module>Repository.kt`（接口） | `AuthRepository.kt` |
| Domain UseCase | `<Action><Module>UseCase.kt` | `GetConnectedUnitsUseCase.kt` |
| Data Repository | `<Module>RepositoryImpl.kt` | `AuthRepositoryImpl.kt` |
| ViewModel | `<Module>ViewModel.kt` | `ConnectionViewModel.kt` |
| UiState | `<Module>UiState.kt`（或内联在 ViewModel 文件） | `ConnectionUiState.kt` |
| Composable Screen | `<Module>Screen.kt` | `ConnectionScreen.kt` |

### B-3 层间依赖规则（严格单向）

```
UI 层 (ViewModel)
    ↓ 只依赖
Domain 层 (UseCase / Repository interface)
    ↑ 依赖注入（不直接引用）
Data 层 (RepositoryImpl)
    ↓ 只依赖
外部数据源（Shimano SDK / BLE / Network）
```

**禁止**：
- ViewModel 直接引用 RepositoryImpl（只能用 interface）
- Data 层引用 ViewModel 或 UseCase
- Model 层引用任何上层类

### B-4 生成代码标记约定

生成的骨架代码使用统一标记，方便后续搜索填充：

```kotlin
// TODO: implement - <说明实现要点>
// TODO: validate - <说明需要验证的边界条件>
// TODO: error-handling - <说明需要处理的异常场景>
```

### B-5 Shimano SDK 专用模式

> 详细规则见 `shimano-sdk-guard` skill。以下为代码生成时的关键约束：

- **SDK 调用必须是 `suspend fun`**，在 `withContext(Dispatchers.IO)` 中执行
- **异常处理**：SDK 抛出 `ConnectionException` / `CommonException`，必须在 Repository 层 catch 并转为领域异常
- **BLE 状态检查**：所有 SDK 调用前检查连接状态（`BLEConnectStatus.READY`）
- **不要 mock SDK 对象**：BLE 设备状态依赖真实硬件，测试用 fake Repository

```kotlin
// ✅ 标准 Repository 实现模式（Shimano）
class AuthRepositoryImpl(
    private val bleRepository: BleRepositoryIF
) : AuthRepository {

    override suspend fun login(params: LoginParams): Result<Unit> =
        withContext(Dispatchers.IO) {
            try {
                bleRepository.sendCommandWithReply(/* ... */)
                Result.success(Unit)
            } catch (e: ConnectionException) {
                Result.failure(DomainException.ConnectionFailed(e.message))
            } catch (e: CommonException) {
                Result.failure(DomainException.LicenseFailed(e.message))
            }
        }
}
```

### B-6 ViewModel 标准模式

```kotlin
class <Module>ViewModel(
    private val <action>UseCase: <Action>UseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(<Module>UiState())
    val uiState: StateFlow<<Module>UiState> = _uiState.asStateFlow()

    fun <action>(<params>) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            <action>UseCase(<params>)
                .onSuccess { result ->
                    _uiState.update { it.copy(isLoading = false, data = result) }
                }
                .onFailure { error ->
                    _uiState.update { it.copy(isLoading = false, error = error.message) }
                }
        }
    }
}

data class <Module>UiState(
    val isLoading: Boolean = false,
    val data: <ResultType>? = null,
    val error: String? = null
)
```

---

## 调用方式

```
/coding-standards                  # 展示完整规范（加载 RULES.md + 本文件）
/coding-standards --layer ui       # 只展示 UI 层规范（B-3 + B-6）
/coding-standards --layer domain   # 只展示 Domain 层规范（B-3 + UseCase 模式）
/coding-standards --layer data     # 只展示 Data 层规范（B-3 + B-5）
```

收到 `--layer` 参数时，只读取并展示对应节的内容，跳过其他层，减少输出量。
