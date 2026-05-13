---
name: rag-query
description: Use when the user wants to search, query, or look up information in the ragForge RAG knowledge base for any project.
tools: Bash
---

# rag-query：查询 RAG 知识库

## 调用语法

```
/rag-query <project_id> <查询关键词> [选项]
```

## 执行步骤

收到调用后，直接运行：

```bash
python3 /Users/xiao/Desktop/Projects/ragForge/scripts/rag-query.py \
  --project <project_id> --query "<关键词>" [其余参数]
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `<project_id>` | 项目 ID，对应 `config/<project_id>.json`（如 `xq`） |
| `<查询关键词>` | 自然语言或符号名称，支持中文/日文/英文 |
| `--exact` | 精确匹配模式（FTS + 行匹配，跳过向量搜索） |
| `--has-mermaid` | 只返回含时序图的内容 |
| `--has-table` | 只返回含表格的内容 |
| `--top-k N` | 返回结果数（默认 3） |
| `--types spec,protocol` | 限定文档类型 |
| `--file <关键词>` | 按文件名过滤 |

## 示例

```bash
# 语义搜索
python3 /Users/xiao/Desktop/Projects/ragForge/scripts/rag-query.py \
  --project xq --query "BLE断线后的状态恢复" --top-k 5

# 精确匹配符号/函数名
python3 /Users/xiao/Desktop/Projects/ragForge/scripts/rag-query.py \
  --project xq --query "GetDevicePropValue" --exact

# 查找含时序图的流程说明
python3 /Users/xiao/Desktop/Projects/ragForge/scripts/rag-query.py \
  --project xq --query "認証フロー" --has-mermaid
```

## 输出格式化

结果包含以下字段，展示时需突出：
- **文件名** + **section_path**：定位原文位置
- **相关度**：相似度分数
- **匹配类型**：vector（语义）/ fts（全文）/ exact_row（精确行）
- **内容摘要**：超过 800 字符自动截断
