---
name: xq-review
description: Use when doing a full XQ project code review covering both code standards and business logic simultaneously, producing a unified report with combined findings
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# XQ 完整代码审查（代码规范 + 业务逻辑）

> 同时执行代码规范审查（`xq-code-reviewer`）和业务逻辑审查（`xq-business-reviewer`），
> 输出统一的汇总报告。
>
> **前置条件**：业务逻辑审查需要 ragForge MCP 已启动，且 `xq` 项目向量索引已构建。
> 若 RAG 服务不可用，业务审查将报错终止，代码规范审查仍正常执行（使用 `--code-only` 可跳过业务部分）。

---

## 调用语法

```
/xq-review <文件或目录>           # 完整双维度审查
/xq-review src/payment/          # 审查整个模块
/xq-review PaymentViewModel.kt   # 审查单文件
/xq-review --code-only <目标>    # 仅代码规范，跳过业务审查
/xq-review --business-only <目标> # 仅业务逻辑，跳过代码规范
```

---

## 执行步骤

### Step 0：加载通用规则库与格式标准

```
Read ~/.claude/skills/review-commons/RULES.md
```

---

### Step 1：代码规范审查

按 `xq-code-reviewer` 的完整流程执行，审查维度 A（代码逻辑）和维度 C（代码规范）。

详见：`~/.claude/skills/xq-code-reviewer/SKILL.md`（Step 1 到 Step 3）

将结果暂存为「代码规范问题列表」。

---

### Step 2：业务逻辑审查

按 `xq-business-reviewer` 的完整流程执行，包括：
读取代码 → 提取业务概念 → 调用 RAG → 整理规格片段 → 对比审查

详见：`~/.claude/skills/xq-business-reviewer/SKILL.md`（Step 1 到 Step 6）

若 RAG 服务不可用，**报错终止业务审查**（不降级跳过），在报告中标注：
```
❌ 业务逻辑审查已终止（RAG 服务不可用）
  请参考 /xq-business-reviewer 的错误提示完成 ragForge MCP 配置后重试
```

将结果暂存为「业务逻辑问题列表」。

---

### Step 3：合并输出统一报告

**报告标题**：`# XQ 代码审查报告`

#### 执行摘要

```
审查文件：{文件列表}
RAG 检索：{查询次数} 次查询，命中 {N} 条规格片段（或"❌ RAG 不可用"）
审查时间：{时间}

总体结论：🔴 阻断合入 / 🟠 需修改后合入 / ✅ 可合入

问题统计：
  代码规范  →  🔴 N  🟠 N  🟡 N  🔵 N
  业务逻辑  →  🔴 N  🟠 N  🟡 N  🔵 N
  合计      →  🔴 N  🟠 N  🟡 N  🔵 N
```

#### 代码规范问题

| 级别 | 类别 | 文件 | 行号 | 问题描述 | 证据 | 修复建议 | 置信度 |
|------|------|------|------|----------|------|---------|-------|
| ... |

#### 业务逻辑问题

| 级别 | 类别 | 文件 | 行号 | 问题描述 | 文档依据 | 修复建议 | 置信度 |
|------|------|------|------|----------|---------|---------|-------|
| ... |

#### 综合结论

用 2-3 句话总结最高优先级的问题，给出明确的合入建议。
如有 🔴 级问题，逐一列出必须修复的内容。
