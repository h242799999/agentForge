# Spec Index

> 维护代码模块与设计文档章节的映射关系。
> `spec-reviewer` 根据此文件定位相关规格章节，按节加载文档内容，无需加载整个文档。

**最后更新**：（运行 `/spec-indexer` 自动更新）
**文档目录**：`specs/`

---

## 文档清单

| 文档ID | 文件路径 | 描述 |
|--------|---------|------|
| API | specs/api-design.md | REST API / 接口设计文档 |
| UI | specs/ui-spec.md | UI 様式书 / 交互设计 |
| DD | specs/detailed-design/ | 各模块详细设计文档目录 |
| DM | specs/data-model.md | 数据模型 / ER 图说明 |

> 根据实际情况修改文档路径和描述。

---

## 模块映射表

> 路径支持 glob 匹配：`**/payment/**` 匹配任意层级下的 payment 目录

| 代码路径 / 关键词 | 文档ID | 章节 / 文件 | 检查重点 |
|-----------------|--------|------------|---------|
| `**/payment/**` | API | §3 支付接口 | 接口参数、错误码、认证方式 |
| `**/auth/**` | API | §2 认证接口 | Token 格式、过期处理、刷新逻辑 |
| `**/order/**` | API | §4 订单接口 | 下单流程、状态流转 |
| `**ViewModel**` | DD | detailed-design/{模块名}.md | 状态机、业务流程步骤 |
| `**Screen**` | UI | §5.x 对应页面章节 | 组件规范、交互行为、空状态 |
| `**/data/**` | DM | §2 实体定义 | 字段类型、必填约束、关联关系 |

---

## 章节行号索引

> 用于大型文档（> 200 页）的精确按节加载。
> 运行 `/spec-indexer` 自动提取，也可手动维护。

### api-design.md

| 章节ID | 标题 | 起始行 | 结束行 |
|--------|------|-------|-------|
| §1 | Overview | 1 | 44 |
| §2 | 认证接口 | 45 | 119 |
| §3 | 支付接口 | 120 | 210 |
| §4 | 订单接口 | 211 | 320 |

### ui-spec.md

| 章节ID | 标题 | 起始行 | 结束行 |
|--------|------|-------|-------|
| §1 | 设计规范总览 | 1 | 60 |
| §5 | 首页 | 240 | 310 |
| §6 | 支付页 | 311 | 400 |

---

## 远程文档同步说明

对于存储在 Google Drive / Confluence 等远程系统的文档，
需先下载到 `specs/` 目录后，`spec-reviewer` 才能读取。

推荐命名规范：
```
specs/
├── INDEX.md
├── api-design.md          # 从 Google Drive 下载的 API 设计文档
├── ui-spec.md             # 从 Confluence 下载的 UI 规范
└── detailed-design/
    ├── payment.md
    └── auth.md
```
