---
name: template-skill
description: [必填] 描述何时触发此 Skill。Claude 根据此描述判断是否自动调用。写清楚触发条件，例如："当用户需要生成 API 文档时" 或 "当用户请求代码审查时"。
tools: Read, Grep, Glob
# disable-model-invocation: true   # 取消注释 → 仅用户可通过 /template-skill 调用
# user-invocable: false            # 取消注释 → 仅 Claude 自动调用（背景知识类）
# context: fork                    # 取消注释 → 在独立上下文中运行（有副作用的操作）
---

# Template Skill

> 简短说明这个 Skill 做什么（1-2 句话）。

## 触发条件

- 当用户 ... 时
- 当需要 ... 时

## 执行步骤

### Step 1：收集上下文

```bash
# 示例：分析项目结构
ls -la src/ 2>/dev/null
cat package.json 2>/dev/null | head -30
```

### Step 2：核心逻辑

在这里描述 Skill 的主要工作流程。

### Step 3：输出结果

描述输出格式和预期结果。

## 输出模板

```markdown
## [Skill 名称] 结果

### 发现
- ...

### 建议
- ...
```

## 注意事项

- 此 Skill 是只读的 / 会修改文件（按实际情况选择）
- 需要的权限：...
