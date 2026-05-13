---
name: xq-code-reviewer
description: Use when reviewing XQ project code for code standards compliance and basic logic correctness, covering naming conventions, function length, null safety, resource leaks, concurrency, and error handling
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# XQ 代码规范审查

> 审查 XQ 项目代码的规范合规性与基本逻辑正确性。
> 不依赖业务文档，可独立使用。

---

## 调用语法

```
/xq-code-reviewer <文件或目录>         # 审查指定文件/目录
/xq-code-reviewer src/payment/        # 审查整个模块
/xq-code-reviewer PaymentViewModel.kt # 审查单文件
```

---

## 执行步骤

### Step 0：加载通用规则库

```
Read ~/.claude/skills/review-commons/RULES.md
```

加载完成后获得：
- **维度 A**：代码逻辑检查项（A.1-A.6）
- **维度 B**：Kotlin 惯用法检查项（B.1-B.4）
- **维度 C**：代码规范检查项（C.1-C.6）
- **输出格式标准**：5 级严重度 + 置信度 + 问题表格格式

---

### Step 1：读取待审查代码

```bash
# 若是目录，列出所有 .kt 文件
find <目标路径> -name "*.kt" -not -path "*/build/*" | sort

# 逐文件读取
Read <文件路径>
```

---

### Step 2：执行代码逻辑审查（维度 A）

对照 RULES.md 维度 A，逐项检查：

| 检查项 | 关注点 |
|-------|--------|
| A.1 空指针/崩溃 | `!!` 强解包、未处理 null path |
| A.2 资源泄漏 | 协程 scope、Flow collect、文件流关闭 |
| A.3 并发 | 共享可变状态、非线程安全集合 |
| A.4 错误处理 | 吞异常、协程内异常、Result 穷举 |
| A.5 边界条件 | 空集合、`first()`/`last()` 前检查 |
| A.6 逻辑缺陷 | 死代码、遗漏分支、循环内 IO |

---

### Step 3：执行代码规范审查（维度 C）

对照 RULES.md 维度 C，逐项检查：

| 检查项 | 关注点 |
|-------|--------|
| C.1 命名规范 | 类/函数/常量/文件/包名大小写 |
| C.2 函数长度 | >40 行建议拆分；>3 层嵌套提取子函数 |
| C.3 魔法数字 | 硬编码数字/字符串应提取为常量 |
| C.4 可见性 | 最小可见性原则；ViewModel 状态字段 |
| C.5 KDoc | public/internal 函数必须有 KDoc |
| C.6 测试覆盖 | 新增业务逻辑是否有对应单元测试 |

---

### Step 4：输出审查报告

使用 RULES.md 定义的表格格式输出：

**报告标题**：`# XQ 代码规范审查报告`

**执行摘要**：
```
审查文件：{文件列表}
审查时间：{时间}
总体结论：🔴 阻断合入 / 🟠 需修改后合入 / ✅ 可合入
问题统计：🔴 N 个  🟠 N 个  🟡 N 个  🔵 N 个
```

**问题列表**（按严重度排序）：

| 级别 | 类别 | 文件 | 行号 | 问题描述 | 证据 | 修复建议 | 置信度 |
|------|------|------|------|----------|------|---------|-------|
| 🔴 | 空指针 | `Foo.kt` | L42 | `!!` 强解包无注释 | `user!!.name` | 改用 `user?.name ?: return` | 高 |

**结论**：总结主要问题，给出合入建议。
