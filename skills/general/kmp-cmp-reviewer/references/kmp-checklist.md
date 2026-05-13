# KMP/CMP 审查清单

> 由 `/kmp-cmp-reviewer` 在 Step 0 加载，作为审查的领域知识补充。
> 每项为独立检查点，使用 `[ ]` 标记便于扩展。

---

## KMP 跨平台架构

### expect/actual

- [ ] `expect` 声明是否全部位于 `commonMain`
- [ ] 每个已声明的 `expect` 是否在所有 target（android / ios / desktop / wasmJs）都有对应 `actual`
- [ ] `actual` 实现是否引入了不必要的平台专属 API（污染共享层）
- [ ] Android/JVM target 是否能用 `actual typealias` 代替重复实现
- [ ] `expect` 的 KDoc 是否说明了各平台行为差异

### Source Set 分层

- [ ] `commonMain` 是否出现 `android.*` / `UIKit` / `Foundation` 等平台包的 import
- [ ] 平台专属的 UI 代码是否放在对应 `platformMain`（不应放在 `commonMain`）
- [ ] 中间 source set（`nativeMain`、`appleMain`）是否合理利用，避免 iOS/macOS 代码重复
- [ ] `androidMain` 是否仅含 Android 平台差异，不含可以上提到 `commonMain` 的逻辑

### 依赖管理

- [ ] `commonMain` 的依赖是否全部为多平台兼容库
  - 协程：`kotlinx-coroutines-core`（不能用 `-android`）
  - 网络：`ktor-client-core`
  - 序列化：`kotlinx-serialization-json`
  - DI：`koin-core`（不能用 `koin-android`）
- [ ] 版本是否统一维护在 `libs.versions.toml`，无硬编码版本号
- [ ] 是否有重复依赖（`commonMain` 和 `androidMain` 同时引用同一库的不同变体）

### Kotlin/Native 内存与线程（iOS）

- [ ] 新内存模型（Kotlin 1.7.20+）下是否有不必要的 `freeze()` 调用
- [ ] `@SharedImmutable` / `@ThreadLocal` 的使用场景是否正确
- [ ] Kotlin Native 是否在非主线程访问 UI 对象（会崩溃）
- [ ] iOS 侧 Swift 互调时，`suspend` 函数是否通过 `@ObjCName` 或 wrapper 正确暴露

---

## Compose Multiplatform UI

### Composable 设计

- [ ] 每个 Composable 是否遵循单一职责（超过 50 行考虑拆分）
- [ ] 参数超过 7 个时是否提取为数据类
- [ ] 函数名是否大驼峰（PascalCase）
- [ ] 是否在 Composable 内直接调用 `suspend` 函数（应使用 `LaunchedEffect`）
- [ ] 是否在 Composable 内直接调用 `Flow.collect`（应使用 `collectAsState()`）

### State Hoisting

- [ ] `ViewModel` 是否直接暴露 `MutableStateFlow` 或 `mutableStateOf`
- [ ] State 提升层级是否合理（不过度提升，不内聚在叶节点）
- [ ] 页面级 State 是否封装为 `UiState` 数据类，而非多个零散 StateFlow

### 重组性能

- [ ] `LazyColumn` / `LazyRow` 的每个 item 是否提供了稳定的 `key`
- [ ] 计算密集的派生值是否使用 `derivedStateOf { }` 包裹
- [ ] 不变的 Lambda 参数是否用 `remember { }` 稳定（防止每次重组创建新实例）
- [ ] 数据类或自定义类是否添加 `@Stable` / `@Immutable` 注解（已确认不可变时）
- [ ] 是否在重组函数中执行 IO / 网络 / 数据库操作

### 副作用

- [ ] `LaunchedEffect` 的 key 是否正确（key 变化 = 重启协程，`Unit` = 只启动一次）
- [ ] `DisposableEffect` 是否有配套的 `onDispose { }` 清理资源
- [ ] `rememberCoroutineScope` 是否只用于事件回调（不用于初始化）
- [ ] `SideEffect` 是否只用于将 Compose State 同步给非 Compose 系统

### 平台适配

- [ ] 是否使用 `WindowSizeClass` 区分手机 / 平板 / 桌面布局
- [ ] Desktop 平台是否适配键盘快捷键和鼠标右键菜单
- [ ] iOS 平台是否适配安全区域（`safeContentPadding` / `WindowInsets`）

---

## 架构模式

### 分层架构

- [ ] 是否清晰分为 `presentation` / `domain` / `data` 三层，无跨层直接调用
- [ ] `ViewModel` 是否只持有 UI State，不直接操作 Repository / 网络 / 数据库
- [ ] `UseCase` / `Interactor` 是否单一职责（一个 UseCase 只做一件事）
- [ ] `Repository` 是否作为数据来源的单一入口，封装 local / remote 选择逻辑

### 依赖注入（Koin）

- [ ] Koin module 是否按功能模块划分（不是一个超大 `AppModule`）
- [ ] 是否存在循环依赖（A 依赖 B，B 依赖 A）
- [ ] `commonMain` 中的 DI 定义是否与平台解耦（不在 common module 中出现 Android Context）

### Navigation

- [ ] 路由定义是否类型安全（`@Serializable` data object / data class）
- [ ] 是否存在深层嵌套的 back stack 导致内存积压
- [ ] 跨平台导航状态（deep link、进程死亡恢复）是否能正确处理

---

## 可测试性

- [ ] `commonMain` 的业务逻辑是否有对应 `commonTest`
- [ ] `ViewModel` 是否可在不依赖 Android 框架的情况下测试（使用 `TestCoroutineDispatcher`）
- [ ] 关键 Composable 是否有 `ComposeUiTest` 覆盖主要交互路径
- [ ] `expect/actual` 的 `actual` 实现是否有各平台的单独测试
