---
name: testcase-gen
description: 基于 RAG 规格库生成テスト設計書（Excel 格式）。当用户需要根据业务规格自动生成测试用例文档时触发。
tools: Read, Grep, Glob, Bash, Write
disable-model-invocation: true
---

# テスト設計書 生成 Skill

> 通过 RAG 查询业务规格，生成符合テスト設計書格式的 Excel 文件。

---

## 调用语法

```
/testcase-gen --project <project> --feature <功能名>
/testcase-gen --project xq --feature "AndroidAutoMAP表示機能"
/testcase-gen --project shimano --feature "Connection" --req-no "SHIMANO-001"
/testcase-gen --project xq --feature "ホーム画面" --output testcases/home.xlsx
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--project <name>` | ✅ | RAG 项目名（xq / shimano / ...） |
| `--feature <name>` | ✅ | 功能名（用于 RAG 查询 + Excel 标题） |
| `--req-no <no>` | ❌ | 変連番号前缀（如 `HENREN-13F2G-043`），省略时自动推断 |
| `--output <path>` | ❌ | 输出路径，默认 `testcases/<feature>_<YYYYMMDD-HHmm>.xlsx` |

---

## 执行步骤

### Step 1：解析参数

从用户输入提取：
- `PROJECT` = `--project` 值
- `FEATURE` = `--feature` 值
- `REQ_NO` = `--req-no` 值（可选）
- `OUTPUT` = `--output` 值，未指定时构造为 `testcases/<FEATURE>_<YYYYMMDD-HHmm>.xlsx`

---

### Step 2：RAG 查询规格（MCP 优先，自动降级）

执行 **2～3 次**查询，覆盖主流程、状态机、异常场景。

**每次查询前输出**：`🔎 RAG 查询 {1/N}："{query 内容}"`

推荐 Query 策略：
- Query 1（主流程）：`"<FEATURE> 機能 処理フロー 仕様"` — `top_k=5`
- Query 2（状態/条件）：`"<FEATURE> 状態 条件 切替"` — `top_k=5`
- Query 3（異常/エラー、按需）：`"<FEATURE> エラー 異常 例外"` — `top_k=3`

#### ① 优先：MCP 调用

```
mcp__ragforge__rag_query(project="<PROJECT>", query=<query>, top_k=<N>)
# 含表格时追加 has_table=true
```

- ✅ 成功 → 使用返回结果，跳过②③
- ❌ 工具不存在 / 调用失败 → 进入②

#### ② 自动注册 MCP（仅当①失败时执行一次）

```bash
RAGFORGE="$(dirname "$(git rev-parse --show-toplevel)")/ragForge"
bash "$RAGFORGE/setup.sh" 2>&1 | grep -E "✅|⚠️|❌" | head -10
```

输出：
```
⚙️ MCP 未响应，已自动运行 setup.sh 注册配置
⚠️ MCP 将在下次重启 IDE 后生效，当前会话使用脚本查询（功能等价）
```

#### ③ 脚本降级（当前会话立即可用）

```bash
RAGFORGE="$(dirname "$(git rev-parse --show-toplevel)")/ragForge"
python3 "$RAGFORGE/scripts/rag-query.py" \
  --project <PROJECT> \
  --query "<查询文本>" \
  --top-k <N> \
  --json
# 含表格时追加 --has-table
```

**每次查询完成后输出**：`✅ RAG 查询 {N} 完成：命中 {X} 条，来自文档：{文件名列表}`

❌ **脚本也失败时**：终止并提示：
```
❌ RAG 不可用，请确认 <PROJECT> 项目索引已构建：
  python3 "$RAGFORGE/scripts/rag-build.py" --project <PROJECT>
```

---

### Step 3：分析规格 → 构建测试用例层级结构

基于 RAG 返回的规格内容，按以下维度拆解每条规格：

| 字段 | 填写规则 |
|------|----------|
| 仕向け | 固定 `日本`（多仕向けの場合は複数行） |
| 実施環境 | 固定 `ベンチ` |
| 要件No | `<REQ_NO>_<3位連番>`（如 `HENREN-001_001`） |
| 大分類 L1 | 功能模块名（来自规格标题或 FEATURE） |
| 中分類 L2 | 子功能名（来自规格子章节） |
| 小分類 L3 | 规格条目文本（原文引用） |
| 小分類 L4 | **具体测试场景**（正常系 / 異常系 / 境界値） |
| 小分類 L5～L7 | 进一步细分（若规格有多层条件） |
| 理由（説明） | 测试该场景的理由（若有明显省略则留空） |
| 担保内容 | 验证标准：「〇〇であること」形式 |

**每条规格至少生成以下场景**：
- 正常系（基本動作確認）
- 境界値（状態遷移の境界、数値上下限等）
- 異常系（エラー・未接続・タイムアウト等）

> ⚠️ 所有 `担保内容` 必须以「〇〇であること」结尾。

---

### Step 4：生成 JSON 中间数据

将 Step 3 构建好的测试用例写入临时文件：

```bash
mkdir -p testcases
```

将以下格式的 JSON 写入 `testcases/.testcase_tmp.json`（使用 Write 工具）：

```json
{
  "feature": "<FEATURE>",
  "req_no": "<REQ_NO>",
  "testcases": [
    {
      "仕向け": "日本",
      "実施環境": "ベンチ",
      "要件No": "HENREN-001_001",
      "大分類": "HOME画面地図ウィジェット",
      "中分類": "AndroidAutoMAP表示機能",
      "小分類L3": "HOME画面の地図ウィジェットにAndroidAutoMAPを表示できること。",
      "小分類L4": "ウィジェット追加／大サイズ表示（AA有効・Native非案内）",
      "小分類L5": "",
      "小分類L6": "",
      "小分類L7": "",
      "理由": "",
      "担保内容": "HOME画面にて地図ウィジェットを大サイズに設定し、AndroidAuto接続時にAndroidAutoMAPが表示されること"
    }
  ]
}
```

---

### Step 5：生成 Excel

```bash
SCRIPT_DIR="$(dirname "$(git rev-parse --show-toplevel)")/agentForge/scripts"
python3 "$SCRIPT_DIR/testcase_gen.py" \
  --input testcases/.testcase_tmp.json \
  --output "<OUTPUT>"
```

スクリプト실행後、출력：

```
📊 Excel 生成中...
✅ テスト設計書保存完了：<OUTPUT>（計 {N} 件）
```

❌ 失敗時：
```
❌ Excel 生成失敗：<エラー内容>
確認事項：pip install openpyxl
```

---

### Step 6：后处理

1. 删除临时文件：
```bash
rm -f testcases/.testcase_tmp.json
```

2. 输出摘要：
```
📋 テスト設計書 生成完了

機能：<FEATURE>
合計テストケース数：<N> 件
  - 正常系：<X> 件
  - 異常系：<Y> 件
  - 境界値：<Z> 件

💾 出力先：<OUTPUT>
```

> ⚠️ 禁止自动执行 `git add` / `git commit`。
