---
name: svn-fetch
description: 从 SVN 拉取式样书/详细设计到本地 specs/ 目录，自动转换格式（xlsx/puml/docx→Markdown），并更新 spec 索引。当用户需要同步 SVN 规格文档、更新式样书、或首次初始化 specs 目录时触发。
tools: Bash, Read, Write
---

# svn-fetch：从 SVN 拉取规格书

## 前置检查

```bash
# 检查 svn 是否可用
which svn || echo "ERROR: svn not installed. Run: brew install subversion"

# 检查配置文件
ls specs/svn-config.json 2>/dev/null || echo "WARN: svn-config.json not found"

# 检查环境变量
echo "SVN_USER=${SVN_USER:-(未设置)}"
echo "SVN_PASS=${SVN_PASS:-(未设置)}"
```

如果 `svn-config.json` 不存在，执行【初始化流程】。
如果 `SVN_USER` 或 `SVN_PASS` 未设置，提示用户：

```
export SVN_USER=your_username
export SVN_PASS=your_password
```

---

## 初始化流程（首次使用）

如果 `specs/svn-config.json` 不存在，创建模板文件并提示用户填写：

```json
{
  "svn_url": "svn://your.server/path/to/specs/",
  "username_env": "SVN_USER",
  "password_env": "SVN_PASS",
  "mappings": [
    {
      "svn_path": "api-spec/",
      "local": "specs/api/",
      "type": "xlsx",
      "description": "API 接口式样书"
    },
    {
      "svn_path": "design/",
      "local": "specs/design/",
      "type": "puml",
      "description": "详细设计时序图"
    },
    {
      "svn_path": "standards/",
      "local": "specs/std/",
      "type": "docx",
      "description": "编码规范文档"
    }
  ]
}
```

> 填写完 `specs/svn-config.json` 后再次运行 `/svn-fetch`。

---

## 主流程

```bash
# 零 token 直接执行（推荐）
python3 ~/.claude/scripts/svn_fetch.py

# 带参数执行
python3 ~/.claude/scripts/svn_fetch.py --module Auth     # 只拉 Auth 模块
python3 ~/.claude/scripts/svn_fetch.py --check           # 检查版本，不下载
python3 ~/.claude/scripts/svn_fetch.py --force           # 强制重新下载（忽略缓存）
python3 ~/.claude/scripts/svn_fetch.py --mapping api-spec # 只拉指定 mapping
```

脚本自动完成：
1. 读取 `specs/svn-config.json` 中的 mappings
2. 对每个 mapping，用 `svn info` 检查远端 revision
3. 若 revision 有变化（或 `--force`），执行 `svn export`
4. 按 type 调用对应转换器（xlsx/puml/docx）
5. 输出拉取摘要

---

## 拉取完成后

完成后提示运行索引更新：

```
✅ 规格书已同步，建议更新索引：
   /spec-indexer
```

---

## 调用方式

```
/svn-fetch                          # 拉取全部（按 svn-config.json 配置）
/svn-fetch --module Auth            # 只拉 Auth 相关规格
/svn-fetch --check                  # 检查 SVN 版本，显示哪些需要更新
/svn-fetch --force                  # 强制重新拉取（忽略缓存）

! python3 ~/.claude/scripts/svn_fetch.py          # 零 token 直接执行
! python3 ~/.claude/scripts/svn_fetch.py --check  # 零 token 版本检查
```
