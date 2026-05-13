# spec-codegen 代码模板参考

> 本文件供 `spec-codegen` skill 在生成代码时引用。
> 所有模板遵循 `coding-standards` 规范。

---

## Model 层模板

### API 响应数据类

```kotlin
package com.example.app.feature.<module>.model

/**
 * <Entity> — <来自 API spec 的功能描述>
 * 参考文档：<API spec 章节>
 */
data class <Entity>(
    val <field1>: <Type1>,
    val <field2>: <Type2>?,          // nullable 字段用 ?
    val <listField>: List<<Item>> = emptyList()
)
```

### 错误/状态密封类

```kotlin
package com.example.app.feature.<module>.model

sealed class <Module>Exception : Exception() {
    /** <来自 API spec 的错误说明> */
    data class ConnectionFailed(override val message: String) : <Module>Exception()
    data class LicenseFailed(override val message: String) : <Module>Exception()
    data class BadStatus(override val message: String) : <Module>Exception()
    // TODO: implement - 按 API spec 错误码补充
}

sealed class <Module>Result {
    data class Success(val data: <Entity>) : <Module>Result()
    data class Error(val exception: <Module>Exception) : <Module>Result()
    object Loading : <Module>Result()
}
```

### 请求参数类

```kotlin
data class <Action>Params(
    val <param1>: <Type1>,
    val <param2>: <Type2> = <defaultValue>
)
```

---

## Domain 层模板

### Repository 接口

```kotlin
package com.example.app.feature.<module>.domain

import com.example.app.feature.<module>.model.*

/**
 * <Module>Repository — <功能模块>的数据访问接口
 * 参考文档：<详细设计章节>
 */
interface <Module>Repository {

    /**
     * <方法功能描述>
     * @param <param> <参数说明>
     * @return Result<<ReturnType>> 成功返回数据，失败返回 <Module>Exception
     */
    suspend fun <methodName>(<param>: <Type>): Result<<ReturnType>>

    // TODO: implement - 按详细设计补充所有方法
}
```

### UseCase

```kotlin
package com.example.app.feature.<module>.domain

import com.example.app.feature.<module>.model.*

/**
 * <Action><Module>UseCase — <功能描述>
 * 参考文档：<详细设计章节>
 */
class <Action><Module>UseCase(
    private val repository: <Module>Repository
) {
    /**
     * @param params <参数说明>
     * @return Result<<ReturnType>>
     */
    suspend operator fun invoke(params: <Params>? = null): Result<<ReturnType>> {
        // TODO: implement - 添加业务校验逻辑（如有）
        return repository.<methodName>(params)
    }
}
```

---

## Data 层模板

### Repository 实现（Shimano BLE）

```kotlin
package com.example.app.feature.<module>.data

import com.example.app.feature.<module>.domain.<Module>Repository
import com.example.app.feature.<module>.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * <Module>RepositoryImpl — 通过 Shimano BLE SDK 实现 <Module>Repository
 * 参考文档：<详细设计章节>
 */
class <Module>RepositoryImpl(
    private val bleRepository: BleRepositoryIF,
    private val licenseCheckManager: LicenseCheckManager
) : <Module>Repository {

    override suspend fun <methodName>(<param>: <Type>): Result<<ReturnType>> =
        withContext(Dispatchers.IO) {
            try {
                // Step 1: License 检查（参考详细设计时序）
                val licenseStatus = licenseCheckManager.getLicenseStatus()
                if (!licenseStatus.isAvailable) {
                    return@withContext Result.failure(
                        <Module>Exception.LicenseFailed("License not available")
                    )
                }

                // Step 2: BLE 状态检查
                if (!bleRepository.checkBleEnabled()) {
                    return@withContext Result.failure(
                        <Module>Exception.ConnectionFailed("BLE disabled")
                    )
                }

                // Step 3: 执行 SDK 命令
                // TODO: implement - 按详细设计时序调用 sendCommandWithReply
                val response = bleRepository.sendCommandWithReply(
                    // TODO: validate - 填写正确的命令参数
                )

                // Step 4: 解析响应
                // TODO: implement - 将 SDK 响应转换为领域模型
                Result.success(TODO("parse response"))

            } catch (e: ConnectionException) {
                Result.failure(<Module>Exception.ConnectionFailed(e.message ?: "Connection error"))
            } catch (e: CommonException) {
                Result.failure(<Module>Exception.LicenseFailed(e.message ?: "License error"))
            }
        }
}
```

---

## UI 层模板

### ViewModel

```kotlin
package com.example.app.feature.<module>.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.app.feature.<module>.domain.*
import com.example.app.feature.<module>.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class <Module>ViewModel(
    private val <action>UseCase: <Action><Module>UseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(<Module>UiState())
    val uiState: StateFlow<<Module>UiState> = _uiState.asStateFlow()

    fun <action>() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            <action>UseCase()
                .onSuccess { data ->
                    _uiState.update { it.copy(isLoading = false, data = data) }
                }
                .onFailure { error ->
                    _uiState.update { it.copy(isLoading = false, error = error.message) }
                }
        }
    }
}

data class <Module>UiState(
    val isLoading: Boolean = false,
    val data: <ReturnType>? = null,
    val error: String? = null
)
```

### Composable Screen（骨架）

```kotlin
package com.example.app.feature.<module>.ui

import androidx.compose.runtime.*
import androidx.compose.material3.*

@Composable
fun <Module>Screen(
    viewModel: <Module>ViewModel,
    onNavigateBack: () -> Unit = {}
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.<action>()
    }

    <Module>Content(
        uiState = uiState,
        onRetry = { viewModel.<action>() }
    )
}

@Composable
private fun <Module>Content(
    uiState: <Module>UiState,
    onRetry: () -> Unit
) {
    when {
        uiState.isLoading -> CircularProgressIndicator()
        uiState.error != null -> {
            // TODO: implement - 错误展示 UI
            Text(text = uiState.error)
        }
        uiState.data != null -> {
            // TODO: implement - 数据展示 UI
        }
    }
}
```

---

## DI 模块模板（Koin / Hilt）

### Koin

```kotlin
val <module>Module = module {
    single<<Module>Repository> {
        <Module>RepositoryImpl(get(), get())
    }
    factory { <Action><Module>UseCase(get()) }
    viewModel { <Module>ViewModel(get()) }
}
```

### Hilt

```kotlin
@Module
@InstallIn(ViewModelComponent::class)
object <Module>Module {

    @Provides
    fun provide<Module>Repository(
        bleRepository: BleRepositoryIF,
        licenseCheckManager: LicenseCheckManager
    ): <Module>Repository = <Module>RepositoryImpl(bleRepository, licenseCheckManager)
}
```
