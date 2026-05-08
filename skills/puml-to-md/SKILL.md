---
name: puml-to-md
description: Use when converting PlantUML sequence diagram files (.puml) to structured Markdown documentation. Triggers when user asks to extract, convert, summarize, or document .puml files, or mentions "puml to md", "puml 转 md", "提炼 puml", "puml 文档化".
tools: Read, Bash, Write, Glob
---

# puml-to-md：PlantUML 转 Markdown 技能

## 概述

将 PlantUML 时序图（`.puml`）转换为结构化的 Markdown 文档。

**输出语言要求：生成的 MD 文档必须使用中文编写。** 所有标题、说明、注释、表格内容均用中文，技术术语（类名、方法名、异常名等代码标识符）保持原文不变。

---

## 工作流（三步，全自动）

```
第一步：用脚本生成骨架 MD（无 token，纯解析）
第二步：读取骨架 MD（小文件，少 token）
第三步：补全 [AI补全] 标记 + 校验完整性（最小 AI 工作量）
```

---

## 第一步：运行脚本生成骨架

```bash
python3 ~/.claude/scripts/puml2md.py <目标目录或单个.puml文件>
```

脚本自动完成（零 token）：
- 提取参与者和层级（颜色 → UI层/Domain层/Data层）
- 生成时序概览（调用链）
- 列出 opt/alt/loop 流程块
- 提取所有 throw/return 错误条件
- 生成骨架 MD，含 `<!-- [AI补全] -->` 标记

如果脚本不存在（`~/.claude/scripts/puml2md.py`），跳到【生成模式】。

---

## 第二步：读取骨架 MD

```bash
find <目标目录> -name "*.md" ! -name "INDEX.md"
```

读取所有生成的骨架 MD 文件。

---

## 第三步：补全 + 校验

### 补全 [AI补全] 标记

替换骨架 MD 中的所有 `<!-- [AI补全] -->` 标记（**用中文**）：

| 标记位置 | 补全内容 |
|---|---|
| 概述 | 一句话说明功能用途（e.g., "获取已连接的 BLE 设备单元列表"） |
| 返回值说明 | 中文解释返回类型含义 |
| 参考文档说明 | 中文说明被引用文档的作用 |

### 校验完整性（与 .puml 对比）

快速扫描对应的 .puml 文件，检查以下内容：

| 检查项 | 验证方式 |
|---|---|
| 错误分支是否完整 | .puml 中的 opt/alt 块 vs MD 错误表格行数 |
| 主流程是否遗漏 | .puml 主干箭头数量 vs MD 主要流程条目 |
| 参考文档是否齐全 | .puml 中 `*.pumlを参照` 数量 vs MD 参考文档表行数 |

如发现差异，直接修改 MD 文件补充遗漏内容。

### 写回文件

用修改后的内容覆写 MD 文件（Write 工具）。

---

## 【生成模式】— 脚本不可用时（原流程）

此模式大幅节省 token：读取体积小的骨架 MD，仅补全 AI 标记部分。

### 步骤 1：读取骨架 MD

```bash
find <目录> -name "*.md" -newer "$(find <目录> -name '*.puml' | head -1)"
```

读取骨架 MD 文件（含 `<!-- [AI补全] -->` 标记）。

### 步骤 2：读取对应 .puml 进行比对

```bash
find <目录> -name "*.puml"
```

逐一读取 .puml 文件，与骨架 MD 对比，检查以下内容：

| 检查项 | 方法 |
|---|---|
| 错误分支是否完整 | 对比 .puml 中的 opt/alt 块 vs MD 中的错误表格 |
| 返回值类型是否正确 | 对比 .puml 末尾的 return vs MD 返回值节 |
| 主要流程是否遗漏重要步骤 | 扫描 .puml 主干箭头 vs MD 主要流程 |
| 参考文档是否齐全 | 检查 .puml 中所有 *.pumlを参照 引用 |

### 步骤 3：补全 [AI补全] 标记

替换骨架 MD 中的所有 `<!-- [AI补全] -->` 标记：

- **概述**：用一句中文说明功能用途（e.g., "获取已连接的 BLE 设备单元列表"）
- **返回值说明**：用中文解释返回类型的含义
- **参考文档说明**：用中文说明被引用文档的作用

### 步骤 4：修复缺失内容

如发现骨架 MD 与 .puml 有差异，直接修改 MD 文件：
- 补充遗漏的错误分支
- 修正错误的返回类型
- 添加 .puml 中有但 MD 中没有的流程节点

### 步骤 5：写回文件

用修改后的内容覆写骨架 MD 文件。

---

## 【生成模式】— 无骨架 MD 时（原流程）

### 第一步：读取文件

列出目标目录下的所有 `.puml` 文件并逐一读取。

```bash
find <目录> -name "*.puml"
```

### 第二步：提取信息

| 提取项 | PlantUML 对应位置 |
|---|---|
| 功能名称 | `@startuml <名称>` 或 legend 中的 `<b>` 标签 |
| 层级构成 | legend 颜色定义（`#F9CCB3`=UI、`#CFF1FD`=Domain 等） |
| 参与者列表 | `participant` 声明 |
| 正常流程 | `->` / `-->` 时序（`alt`/`opt` 块外侧） |
| 错误分支 | `alt`/`opt` 块内的时序 |
| 日志消息 | `note over` 中的 `logMessage:` |
| 返回值 | `return` 的类型 |
| 参考文档 | `note` 中的 `〜.pumlを参照` |

### 第三步：Markdown 结构模板（中文）

```markdown
# <功能名> API 详细设计

## 概述
（功能的一句话说明）

## 层级构成
| 层级 | 组件 |
|---|---|
| UI层 | ... |
| Domain层 | ... |

---

## 获取：<方法名>（读取类）

### 时序概览
（用箭头展示调用流程）

### 前置处理（可选）
（存在 opt 块时记录）

### 错误分支
| 条件 | 日志消息 | 返回值 |
|---|---|---|

### 数据获取逻辑
（alt/else 分支逐块描述）

### 返回值
| 类型 | 说明 |
|---|---|

---

## 设置：<方法名>（写入类）

### 错误分支
（区分 throw 和 return 分别记录）

### 正常结束流程

### 提交流程
（commitSettingValue 等向设备发送的流程）

---

## 异常一览
| 异常 | 类别 | 触发条件 |
|---|---|---|

---

## 参考文档
| 文档 | 内容 |
|---|---|
```

### 第四步：注意事项

- **输出语言**：MD 文档全部使用中文，类名/方法名/异常名等代码标识符保持原文
- `throw` 与 `return` 必须区分记录（`NOT_LOGIN` 类为 `throw`，其余为 `return`）
- `opt` 块作为"前置处理（可选）"单独成节
- 同一功能的多个 `.puml`（get/set）合并为**一个 MD 文件**
- 文件名使用功能名（例：`WALK_ASSIST_SPEED.md`）
- 输出到与 `.puml` 相同的目录

### 第五步：层级颜色代码（Shimano SDK 通用）

| 颜色代码 | 层级 |
|---|---|
| `#F9CCB3` | UI层 |
| `#CFF1FD` | Domain层 |
| `#C7F3CC` | Data层 |
| `#3399FF` | 设备（BLE Device） |
