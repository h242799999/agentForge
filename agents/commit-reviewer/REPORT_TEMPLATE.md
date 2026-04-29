# Commit Review 报告

**报告文件**：`reviewer/<作者>-<commitId前8位>-<YYYY-MM-DD-HHmm>.md`
**Commit(s)**：`{commitId 或 id1..id2 或 branch}`
**模式**：`{single / range / branch}`
**审查时间**：`{YYYY-MM-DD HH:mm}`
**覆盖文件**：`{X / Y 个文件（跳过 Z 个低优先级文件）}`

---

## Commit 元信息

| 字段 | 内容 |
|------|------|
| Commit ID | `abc1234ef` |
| Author | name \<email\> |
| Date | YYYY-MM-DD HH:mm |
| Message | `"fix: ..."` |
| 变更统计 | +N 行 / -M 行，涉及 K 个文件 |

> 多笔 commit 时展示 commit 列表：
> - `abc1234` — "feat: add payment flow"
> - `def5678` — "fix: null check on checkout"

---

## 结论

**`✅ Approve`** / **`🔄 Request Changes`** / **`💬 Comment`** — {核心原因一句话}

---

## 变更意图对齐

- **推断意图**：`{bugfix / feature / refactor / performance / chore}`
- **功能模块**：`{payment / auth / profile / order / ...}`
- **意图一致性**：`[一致 / 部分偏离 / 偏离]`
- **偏离说明**：（若有）此 commit 同时包含了未在 message 中声明的 XXX

---

## 影响范围分析

- **直接修改模块**：...
- **跨平台影响**：`Android only / iOS only / 共享层 / 全平台`
- **破坏性变更**：`[是 / 否]`（原因：...）
- **关联 issue**：`#123`（若 commit message 中有引用）

---

## 问题列表（按严重程度排序）

| 级别 | 类别 | 文件 | 行号 | 问题描述 | 修复建议 | 置信度 |
|------|------|------|------|----------|---------|-------|
| 🔴 | 代码逻辑 | `PaymentViewModel.kt` | L42 | `!!` 强解包可能在网络失败时崩溃 | 改用 `?: return` 或 `requireNotNull` | 高 |
| 🟠 | 资源泄漏 | `OrderRepository.kt` | L87 | 协程在 catch 块中未取消 | 在 finally 块中调用 `job.cancel()` | 高 |
| 🟡 | 代码规范 | `PaymentUtils.kt` | L15 | 魔法数字 `3000`，含义不明 | 提取为常量 `PAYMENT_TIMEOUT_MS` | 高 |

> 无问题时填写：「未发现问题」

---

## 业务逻辑分析

> 基于提供的上下文分析。若用户跳过，标注：「用户跳过业务逻辑 review」

| 检查项 | 状态 | 说明 | 置信度 |
|--------|------|------|-------|
| 意图对齐 | ✅ 一致 | commit message 准确描述了变更内容 | 高 |
| 逻辑完整性 | ⚠️ 待确认 | 缺少对空购物车场景的处理 | 中 |
| 数据一致性 | ✅ 正常 | cache 和 DB 同步逻辑完整 | 高 |
| 回退安全性 | ✅ 可回滚 | 无数据迁移，回滚无风险 | 高 |
| 向后兼容 | ⚠️ 注意 | `checkout()` 新增了必填参数，下游需同步更新 | 高 |

---

## ✅ 亮点

- 错误处理使用了 `Result<T>` 封装，调用方可安全处理异常
- 新增逻辑有对应的单元测试覆盖核心路径
- commit message 清晰，关联了 issue #123

---

## 合入建议

- **必须修复**：（🔴 P0 问题列表）
- **建议修复**：（🟠 P1 问题列表）
- **拆分建议**：（若 commit 混合了多个目的，建议如何拆分）

---

## PR Review 摘要（可直接粘贴）

> {适合粘贴到 PR comment 的简洁摘要，包含主要发现和结论。技术术语保留英文，描述用中文。}

---

## 后续跟进

> 若包含 `.kt` 文件时展示此区块

检测到 Kotlin 文件变更（N 个 `.kt` 文件）。建议后续运行：
- Claude Code：`@kmp-cmp-reviewer 审查 {变更涉及的目录}`
- Copilot：`/kmp-cmp-reviewer {变更涉及的目录}`

---

*由 commit-reviewer 生成 | Claude Code*
*⚠️ 本报告仅供参考，未自动应用任何变更，未执行 git commit。*
