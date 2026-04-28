#!/usr/bin/env python3
"""
Shimano SDK xlsx → specs/ Markdown 转换器

用法：
  python3 scripts/extract-specs.py <xlsx_dir> [output_dir]

默认：
  xlsx_dir   = ~/Desktop/资料/Shimano-资料/SDK/API接口式样书
  output_dir = ./specs

示例：
  python3 scripts/extract-specs.py
  python3 scripts/extract-specs.py "/path/to/API接口式样书" "./specs"
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

try:
    import openpyxl
except ImportError:
    print("错误：需要 openpyxl。运行：pip3 install openpyxl")
    sys.exit(1)


# ── 列索引常量（基于实际 xlsx 结构）────────────────────────
COL_LABEL = 2      # 字段标签（API定義 / 概要 / パラメータ 等）
COL_VALUE = 5      # 主要值
COL_VALUE2 = 6     # 副值（Exception 类名 / 参数补充）
COL_TYPE = 8       # 参数类型
COL_DIRECTION = 11 # 参数方向（：In / ：Out）
COL_DESC = 13      # 参数描述 / ExceptionType
COL_EXC_DESC = 22  # Exception 描述

# 标识一个 API 块开始的标签
API_START_LABEL = "API定義"

# 需要跳过的 sheet 名（变更历史、图表等）
SKIP_SHEETS = {"変更履歴", "API一覧", "WpsReserved_CellImgList",
               "CustomizeCategory関連性の星取表", "connect status"}

# 包含 API 规格的 sheet 标识（列 C 含这些标签）
API_SHEET_LABELS = {"API定義", "概要", "パラメータ", "戻り値"}

# 包含类结构的 sheet 标识
CLASS_SHEET_KEYWORDS = ["クラス構成", "クラス構成 ", "構成"]


def cell_str(value) -> str:
    """将单元格值转换为可读字符串"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def get_row_values(row: tuple) -> dict:
    """从一行数据提取各列值"""
    def get(idx):
        if idx < len(row):
            return cell_str(row[idx])
        return ""
    return {
        "label": get(COL_LABEL),
        "value": get(COL_VALUE),
        "value2": get(COL_VALUE2),
        "type": get(COL_TYPE),
        "direction": get(COL_DIRECTION),
        "desc": get(COL_DESC),
        "exc_desc": get(COL_EXC_DESC),
    }


def is_api_sheet(ws) -> bool:
    """判断 sheet 是否包含 API 规格（列 C 中有 API定義）"""
    for row in ws.iter_rows(max_row=200, values_only=True):
        if len(row) > COL_LABEL and cell_str(row[COL_LABEL]) == API_START_LABEL:
            return True
    return False


def is_class_sheet(sheet_name: str) -> bool:
    """判断 sheet 是否为类结构说明"""
    return any(kw in sheet_name for kw in CLASS_SHEET_KEYWORDS)


def parse_api_sheet(ws) -> list[dict]:
    """解析 API 规格 sheet，返回 API 列表"""
    apis = []
    current = None
    in_exception = False
    in_params = False

    for row in ws.iter_rows(values_only=True):
        rv = get_row_values(row)
        label = rv["label"]

        if label == API_START_LABEL:
            # 保存上一个 API
            if current:
                apis.append(current)
            current = {
                "definition": rv["value"],
                "id": "",
                "summary": "",
                "params": [],
                "exceptions": [],
                "returns": "",
                "visibility": "",
                "require_login": "",
                "require_online": "",
                "category": "",
            }
            in_exception = False
            in_params = False

        elif current is None:
            continue

        elif label == "API ID":
            current["id"] = rv["value"]

        elif label == "概要":
            current["summary"] = rv["value"]

        elif label == "パラメータ":
            in_exception = False
            in_params = True
            if rv["value"] and rv["value"] != "なし":
                param = {
                    "name": rv["value"],
                    "type": rv["type"],
                    "direction": rv["direction"].replace("：", "").strip(),
                    "desc": rv["desc"],
                }
                current["params"].append(param)

        elif label == "Exception":
            in_exception = True
            in_params = False

        elif label == "戻り値":
            in_exception = False
            in_params = False
            ret = rv["value"]
            if rv["value2"]:
                ret = f"{ret} {rv['value2']}"
            current["returns"] = ret

        elif label == "公開範囲":
            current["visibility"] = rv["value"]
            in_exception = False
            in_params = False

        elif label == "SHIMANO IDログイン必須":
            current["require_login"] = rv["value"]

        elif label == "オンライン必須":
            current["require_online"] = rv["value"]

        elif label == "カテゴリ":
            current["category"] = rv["value"]

        else:
            # 续行处理
            if in_exception and rv["value2"] and rv["value2"] != "ExceptionClass":
                exc = {
                    "class": rv["value2"],
                    "type": rv["desc"],
                    "desc": rv["exc_desc"],
                }
                current["exceptions"].append(exc)

            elif in_params and rv["value"] and label == "":
                # 多参数行（追加参数）
                param = {
                    "name": rv["value"],
                    "type": rv["type"],
                    "direction": rv["direction"].replace("：", "").strip(),
                    "desc": rv["desc"],
                }
                current["params"].append(param)

    if current:
        apis.append(current)

    return apis


def parse_class_sheet(ws) -> list[dict]:
    """解析类结构 sheet，返回类定义列表"""
    classes = []
    current_class = None

    for row in ws.iter_rows(values_only=True):
        rv = get_row_values(row)
        label = rv["label"]

        # 检测类定义行（格式："XxxClass の構成："）
        if label and re.search(r'の構成[：:]', label):
            if current_class:
                classes.append(current_class)
            current_class = {
                "name": label,
                "fields": [],
            }

        elif label == "クラス定義":
            if current_class is None:
                current_class = {"name": rv["value"], "fields": []}
            else:
                current_class["definition"] = rv["value"]

        elif label == "説明" and current_class:
            current_class["description"] = rv["value"]

        elif current_class and rv["value"] and label == "":
            # 字段行（第一列空，第二列字段名/类型）
            field_name = rv["value"]
            field_type = rv["type"] or rv["value2"]
            field_desc = rv["desc"] or rv["exc_desc"]
            if field_name and field_name not in ("フィールド名", "Field Name", "名前"):
                current_class["fields"].append({
                    "name": field_name,
                    "type": field_type,
                    "desc": field_desc,
                })

    if current_class:
        classes.append(current_class)

    return classes


def api_to_markdown(api: dict) -> str:
    """将单个 API 转为 Markdown 文本块"""
    lines = []

    # 函数签名
    defn = api["definition"]
    api_id = f" _(ID: {api['id']})_" if api["id"] else ""
    lines.append(f"### `{defn}`{api_id}")
    lines.append("")

    # 概要
    if api["summary"]:
        lines.append(f"**概要**：{api['summary']}")
        lines.append("")

    # 元数据行
    meta = []
    if api["visibility"]:
        meta.append(f"公開範囲：{api['visibility']}")
    if api["require_login"]:
        meta.append(f"SHIMANO IDログイン：{api['require_login']}")
    if api["require_online"]:
        meta.append(f"オンライン：{api['require_online']}")
    if api["category"]:
        meta.append(f"カテゴリ：{api['category']}")
    if meta:
        lines.append(f"_{' ｜ '.join(meta)}_")
        lines.append("")

    # 参数
    params = [p for p in api["params"] if p["name"] and p["name"] != "なし"]
    if params:
        lines.append("**パラメータ**")
        lines.append("")
        lines.append("| 名前 | 型 | 方向 | 説明 |")
        lines.append("|------|-----|------|------|")
        for p in params:
            name = p["name"]
            typ = p["type"] or "-"
            direction = p["direction"] or "In"
            desc = p["desc"] or "-"
            lines.append(f"| `{name}` | `{typ}` | {direction} | {desc} |")
        lines.append("")
    elif not params:
        lines.append("**パラメータ**：なし")
        lines.append("")

    # 戻り値
    ret = api["returns"]
    if ret:
        lines.append(f"**戻り値**：`{ret}`")
        lines.append("")

    # Exception
    excs = [e for e in api["exceptions"] if e["class"]]
    if excs:
        lines.append("**Exception**")
        lines.append("")
        lines.append("| ExceptionClass | ExceptionType | 概要 |")
        lines.append("|---------------|--------------|------|")
        for e in excs:
            lines.append(f"| `{e['class']}` | `{e['type']}` | {e['desc']} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def classes_to_markdown(classes: list[dict]) -> str:
    """将类结构列表转为 Markdown"""
    lines = []
    for cls in classes:
        lines.append(f"### {cls['name']}")
        lines.append("")
        if cls.get("description"):
            lines.append(f"{cls['description']}")
            lines.append("")
        if cls.get("fields"):
            lines.append("| フィールド | 型 | 説明 |")
            lines.append("|-----------|-----|------|")
            for f in cls["fields"]:
                name = f["name"]
                typ = f["type"] or "-"
                desc = f["desc"] or "-"
                lines.append(f"| `{name}` | `{typ}` | {desc} |")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def process_xlsx(xlsx_path: Path, output_dir: Path):
    """处理单个 xlsx 文件，生成对应 Markdown 文件"""
    # 从文件名提取模块名（e.g. "SHIMANO Mobile SDK_API仕様書_Auth.xlsx" → "Auth"）
    name = xlsx_path.stem
    match = re.search(r'仕様書_(.+)$', name)
    module = match.group(1) if match else name

    print(f"  处理：{xlsx_path.name} → specs/api-spec-{module}.md")

    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)

    md_lines = []
    md_lines.append(f"# {module} モジュール API 仕様")
    md_lines.append("")
    md_lines.append(f"> 自動抽出元：`{xlsx_path.name}`  ")
    md_lines.append(f"> 抽出日：{datetime.now().strftime('%Y-%m-%d')}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    api_count = 0
    class_count = 0

    for sheet_name in wb.sheetnames:
        if sheet_name in SKIP_SHEETS:
            continue

        ws = wb[sheet_name]

        # 跳过空 sheet
        has_data = any(
            any(c is not None for c in row)
            for row in ws.iter_rows(max_row=5, values_only=True)
        )
        if not has_data:
            continue

        if is_api_sheet(ws):
            apis = parse_api_sheet(ws)
            if apis:
                md_lines.append(f"## {sheet_name}")
                md_lines.append("")
                for api in apis:
                    md_lines.append(api_to_markdown(api))
                api_count += len(apis)

        elif is_class_sheet(sheet_name):
            classes = parse_class_sheet(ws)
            if classes:
                md_lines.append(f"## {sheet_name}（クラス構成）")
                md_lines.append("")
                md_lines.append(classes_to_markdown(classes))
                class_count += len(classes)

    output_path = output_dir / f"api-spec-{module}.md"
    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"    ✓ {api_count} 个 API，{class_count} 个类 → {output_path}")


def main():
    # 路径参数
    default_xlsx_dir = Path.home() / "Desktop/资料/Shimano-资料/SDK/API接口式样书"
    default_output_dir = Path(__file__).parent.parent / "specs"

    xlsx_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_xlsx_dir
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output_dir

    if not xlsx_dir.exists():
        print(f"错误：xlsx 目录不存在：{xlsx_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集需要处理的 xlsx 文件（排除备份/临时文件）
    xlsx_files = [
        f for f in sorted(xlsx_dir.glob("*.xlsx"))
        if not f.name.startswith("~$")
        and "副本" not in f.name
        and "formatted" not in f.name
        and "merge" not in f.name
        # 排除合并总表（避免和分模块文件重复）
        and "_API仕様書.xlsx" not in f.name
    ]

    print(f"发现 {len(xlsx_files)} 个 xlsx 文件，开始转换...")
    print(f"输出目录：{output_dir}")
    print()

    for xlsx_file in xlsx_files:
        try:
            process_xlsx(xlsx_file, output_dir)
        except Exception as e:
            print(f"  ✗ {xlsx_file.name} 处理失败：{e}")

    print()
    print(f"完成！已生成 {len(xlsx_files)} 个 Markdown 文件到 {output_dir}/")


if __name__ == "__main__":
    main()
