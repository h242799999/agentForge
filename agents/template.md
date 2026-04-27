---
name: template-agent
description: [必填] 描述何时使用此 SubAgent。主 Claude 实例根据此描述决定是否委派任务。例如："专门用于安全审查的 agent，当用户请求安全分析或涉及 auth/payment 代码时使用"。
tools: Read, Grep, Glob
# model: sonnet                   # opus（最强）/ sonnet（均衡）/ haiku（最快）
---

# Template Agent

> 简短说明这个 SubAgent 的专项职责（1-2 句话）。

## 职责范围

此 Agent 专注于：
- ...
- ...

**不处理**：（明确边界，防止职责蔓延）
- ...

## 分析框架

### 检查维度 1：[名称]

- 检查项 A
- 检查项 B

### 检查维度 2：[名称]

- 检查项 C
- 检查项 D

## 输出格式

```markdown
## [Agent 名称] 分析报告

### 总体评分：[优秀 / 良好 / 需改进 / 警告]

### 发现的问题

| 严重程度 | 位置 | 描述 | 建议 |
|----------|------|------|------|
| 高 | file.ts:42 | ... | ... |

### 建议操作

1. 立即处理：...
2. 计划处理：...

### 通过项
- ...
```

## 使用示例

主 Claude 调用此 Agent 的方式：
> "请用 template-agent 分析 src/ 目录下的代码"

用户直接调用：
> Agent tool with subagent_type="template-agent"
