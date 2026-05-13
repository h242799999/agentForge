---
name: spec-codegen
description: 根据式样书/详细设计生成 KMP + Compose 代码骨架。当用户需要基于规格文档自动生成 ViewModel、Repository、UseCase、Model 等代码时触发。调用前需先完成 /svn-fetch + /spec-indexer。用法：/spec-codegen <模块名> [--layer model|domain|data|ui] [--preview]
tools: Read, Bash, Write, Glob
---

# spec-codegen：从规格书生成 KMP + Compose 代码

## 前置条件检查

```bash
# 确认索引文件存在
ls specs/INDEX.md 2>/dev/null || echo "ERROR: 请先运行 /spec-indexer 生成索引"
```

若 `specs/INDEX.md` 不存在，提示用户依次运行：
1. `/svn-fetch` — 拉取规格文档
2. `/spec-indexer` — 生成索引

---

## Step 0：加载规范

Read `skills/coding-standards/SKILL.md`（加载代码生成约定和层架构规则）。

---

## Step 1：定位文档章节

```bash
# 从 INDEX.md 找目标模块相关文档
grep -n "<模块名>" specs/INDEX.md
```

读取 `specs/INDEX.md`，找到目标模块对应的：
- API spec 文档路径 + 章节行号
- 详细设计文档路径 + 章节行号

---

## Step 2：精确加载规格内容

按 INDEX.md 中的行号范围加载文档（只加载相关章节，控制 token 消耗）：

```bash
# 示例：加载 API spec 第 42-120 行
# Read file with offset=42, limit=78
```

需要加载的内容：
- **API spec**：接口定义（方法名、参数、返回值、异常）
- **详细设计**：时序流程（调用链、错误分支）

---

## Step 3：按层生成代码

根据 `--layer` 参数决定生成哪些层（默认全栈）：

### Model 层（`--layer model`）

参照 API spec 中的数据结构定义，生成：

```kotlin
// specs/参考：<API spec 文档>§<章节>

data class <Entity>(
    val <field>: <Type>,        // <来自 API spec 的字段说明>
    // TODO: implement - 根据 API spec 补充所有字段
)

sealed class <Module>Exception : Exception() {
    data class <ErrorType>(val message: String) : <Module>Exception()
    // TODO: implement - 根据 API spec 补充所有错误类型
}
```

### Domain 层（`--layer domain`）

参照详细设计中的调用链，生成：

```kotlin
interface <Module>Repository {
    // TODO: implement - 根据详细设计补充所有方法签名
    suspend fun <methodName>(<params>): Result<<ReturnType>>
}

class <Action><Module>UseCase(
    private val repository: <Module>Repository
) {
    // TODO: implement - 根据详细设计补充业务逻辑
    suspend operator fun invoke(<params>): Result<<ReturnType>> {
        return repository.<methodName>(<params>)
    }
}
```

### Data 层（`--layer data`）

参照详细设计中的 Data 层调用，生成：

```kotlin
class <Module>RepositoryImpl(
    private val bleRepository: BleRepositoryIF
) : <Module>Repository {

    override suspend fun <methodName>(<params>): Result<<ReturnType>> =
        withContext(Dispatchers.IO) {
            try {
                // TODO: implement - 按详细设计时序实现 SDK 调用
                TODO("Not yet implemented")
            } catch (e: ConnectionException) {
                Result.failure(DomainException.ConnectionFailed(e.message))
            } catch (e: CommonException) {
                Result.failure(DomainException.LicenseFailed(e.message))
            }
        }
}
```

### UI 层（`--layer ui`）

参照 API 返回值和业务流程，生成：

```kotlin
class <Module>ViewModel(
    private val <action>UseCase: <Action><Module>UseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(<Module>UiState())
    val uiState: StateFlow<<Module>UiState> = _uiState.asStateFlow()

    fun <action>() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            // TODO: implement - 根据详细设计补充参数
            <action>UseCase()
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
    val data: <ReturnType>? = null,
    val error: String? = null
)
```

---

## Step 4：输出

### `--preview` 模式（默认）

直接在对话中输出生成的代码，每个文件用代码块展示，用户确认后再写入。

### 写入模式（加 `--write` 参数）

按包结构写入文件：

```bash
# 输出目录结构（示例，实际路径由用户项目决定）
src/main/kotlin/
└── com/example/app/feature/<module>/
    ├── model/
    │   └── <Entity>.kt
    ├── domain/
    │   ├── <Module>Repository.kt
    │   └── <Action><Module>UseCase.kt
    ├── data/
    │   └── <Module>RepositoryImpl.kt
    └── ui/
        ├── <Module>ViewModel.kt
        └── <Module>Screen.kt        # Composable 骨架
```

提示用户确认输出目录（若项目中存在 `src/` 目录则自动推断）。

---

## 调用方式

```
/spec-codegen Auth                        # Auth 模块全栈预览
/spec-codegen Connection --layer domain   # 只生成 Domain 层（预览）
/spec-codegen WalkAssist --layer model    # 只生成数据模型（预览）
/spec-codegen Auth --write                # 全栈生成并写入文件
/spec-codegen Auth --layer data --write   # 只写入 Data 层
```

---

## 参考文件

- `skills/coding-standards/SKILL.md` — 代码规范（Step 0 加载）
- `skills/spec-codegen/TEMPLATES.md` — 各层详细代码模板
- `specs/INDEX.md` — 模块 ↔ 文档章节映射
