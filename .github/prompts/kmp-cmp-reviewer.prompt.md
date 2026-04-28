---
mode: agent
description: KMP/CMP 专项代码审查 - 审查 Kotlin Multiplatform / Compose Multiplatform 代码
---

对以下代码进行 KMP/CMP 专项代码审查，覆盖以下维度：

1. **KMP 跨平台架构**（30%）：expect/actual 规范性、source set 分层、Native 线程安全
2. **Compose UI 设计**（25%）：重组性能、State Hoisting、副作用管理、LazyList key
3. **Kotlin 惯用法**（20%）：Null Safety、协程/Flow 主线程安全、密封类建模
4. **架构模式**（15%）：MVVM 分层、Koin DI、类型安全导航
5. **可测试性**（10%）：commonTest 覆盖、ViewModel 可独立测试

审查范围：${input:target:src/commonMain/kotlin/}

输出结构化报告，包含：总体结论（🔴阻断/🟠需修改/✅可合入）、各维度问题列表（文件+行号+修复建议）、亮点、行动计划。
