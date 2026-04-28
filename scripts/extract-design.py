#!/usr/bin/env python3
"""
Shimano SDK API詳細設計書 (.puml) → specs/design/ Markdown 转换器

支持两个版本：
  1.0.0  源：API详细设计书/（按模块分目录）
  1.0.2  源：1.0.2/3.API詳細設計書/（按 ticket 分目录，需推断模块）

用法：
  python3 scripts/extract-design.py                        # 同时提取两个版本
  python3 scripts/extract-design.py --version 1.0.0        # 仅提取 1.0.0
  python3 scripts/extract-design.py --version 1.0.2        # 仅提取 1.0.2
  python3 scripts/extract-design.py --module Auth          # 仅提取指定模块（all版本）

输出：
  specs/design/v1.0.0/<Module>.md
  specs/design/v1.0.2/<Module>.md
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime


SDK_ROOT_DEFAULT = Path.home() / "Desktop/资料/Shimano-资料/SDK"
OUTPUT_DEFAULT = Path(__file__).parent.parent / "specs"

# ── 1.0.0：模块目录名 → 输出文件名 ──────────────────────────
V100_MODULE_MAP = {
    "Activity":      "Activity",
    "Applog":        "Applog",
    "Auth":          "Auth",
    "Connection":    "Connection",
    "Connection_All":"Connection",
    "Customize":     "Customize",
    "LicenseCheck":  "LicenseCheck",
    "Maintenance":   "Maintenance",
    "MyBike":        "MyBike",
    "Queue":         "Queue",
    "Ride":          "Ride",
    "SDKLog":        "SDKLog",
    "Setting":       "Setting",
    "Update":        "Update",
    "行動log":        "Applog",
}

# ── 1.0.2：文件名关键词 → 模块 ──────────────────────────────
# 按优先级排列（更具体的在前）
V102_FILENAME_RULES: list[tuple[str, str]] = [
    # Auth
    ("loginAsGuestUser",            "Auth"),
    ("checkLogin",                  "Auth"),
    ("login",                       "Auth"),
    ("logout",                      "Auth"),
    ("getUser",                     "Auth"),
    # Connection
    ("connect",                     "Connection"),
    ("disableAutoConnect",          "Connection"),
    ("enableAutoConnect",           "Connection"),
    ("getMyBikeLastConnected",      "Connection"),
    ("clearMyBikeInfoLastConnected","Connection"),
    ("scanBLEDevice",               "Connection"),
    ("getStaticBleAddress",         "Connection"),
    ("getUnits",                    "Connection"),
    # MyBike
    ("registerMyBike",              "MyBike"),
    ("pairWirelessSwitchUnit",      "MyBike"),
    ("scanWirelessSwitchUnits",     "MyBike"),
    ("stopScanWirelessSwitchUnits", "MyBike"),
    ("pairPowerMeterUnit",          "MyBike"),
    ("removePowerMeterUnit",        "MyBike"),
    ("compareLocalMyBikeUnits",     "MyBike"),
    ("updateMyBikeUnitsWithConnected","MyBike"),
    ("getBatteryLevels",            "MyBike"),
    ("getShimanoBikeSeriesImageUrl","MyBike"),
    ("getTireCircumference",        "MyBike"),
    ("setTireCircumference",        "MyBike"),
    ("MyBike.",                     "MyBike"),
    # Ride
    ("startRiding",                 "Ride"),
    ("subscribeRideData",           "Ride"),
    ("getRideData",                 "Ride"),
    ("getRideMetrics",              "Ride"),
    ("getSportData",                "Ride"),
    ("startRiding",                 "Ride"),
    # Update
    ("updateFirmware",              "Update"),
    ("getLatestAppVersion",         "Update"),
    # Activity
    ("getGearUsageRateInfo",        "Activity"),
    ("resetGearUsageRateInfo",      "Activity"),
    # Maintenance
    ("adjustCancel",                "Maintenance"),
    ("adjustConfirm",               "Maintenance"),
    ("getFrontAdjustValue",         "Maintenance"),
    ("getRearAdjustValue",          "Maintenance"),
    ("getFrontGearInfo",            "Maintenance"),
    ("getRearGearInfo",             "Maintenance"),
    ("isInAdjustMode",              "Maintenance"),
    ("setFrontAdjustValue",         "Maintenance"),
    ("setRearAdjustValue",          "Maintenance"),
    ("startAdjust",                 "Maintenance"),
    ("getErrorLogInfo",             "Maintenance"),
    ("startZeroOffset",             "Maintenance"),
    ("startOffsetCompensation",     "Maintenance"),
    ("getAutoZeroOffset",           "Maintenance"),
    ("setAutoZeroOffset",           "Maintenance"),
    ("getEnabledCategories_Maintenance", "Maintenance"),
    # Customize
    ("DI2_SHIFTING_MODE",           "Customize"),
    ("NUMBER_OF_REAR_GEARS",        "Customize"),
    ("REAR_GEAR_RANGE",             "Customize"),
    ("SELECTABLE_DI2",              "Customize"),
    ("SYNCRO_SHIFT_PATTERN",        "Customize"),
    ("MULTI_SHIFT_SETTING",         "Customize"),
    ("CS_TEETH_PATTERN",            "Customize"),
    ("FC_TEETH_PATTERN",            "Customize"),
    ("CYCLING_POWER_PROFILE",       "Customize"),
    ("ASSIST_PROFILE",              "Customize"),
    ("WALK_ASSIST_SPEED",           "Customize"),
    ("TIRE_CIRCUMFERENCE",          "Customize"),
    ("registerRearGear",            "Customize"),
    ("getEnabledCategories_Customize","Customize"),
    ("Customize.",                  "Customize"),
]

# 层颜色 → 层名称
LAYER_COLORS = {
    "#F9CCB3": "UI Layer",
    "#CFF1FD": "Domain Layer",
    "#C7F3CC": "Data Layer",
    "#3399FF": "Device（製品）",
    "#FFFF99": "External Service",
}


# ── puml 解析 ────────────────────────────────────────────────

def cell_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def parse_puml(content: str) -> dict:
    result = {
        "name": "",
        "participants": [],
        "notes": [],
        "flow": [],
        "errors": [],
    }
    lines = content.splitlines()

    m = re.search(r'@startuml\s+(\S+)', content)
    if m:
        result["name"] = m.group(1)

    for line in lines:
        m = re.match(r'participant\s+"?([^"#\n]+?)"?\s+(#\w+)', line)
        if not m:
            m = re.match(r'participant\s+(\S+)\s+(#\w+)', line)
        if m:
            pname = m.group(1).strip()
            color = m.group(2).strip()
            result["participants"].append({
                "name": pname,
                "layer": LAYER_COLORS.get(color, ""),
                "color": color,
            })

    in_note = False
    note_lines = []
    note_target = ""
    for line in lines:
        stripped = line.strip()
        if re.match(r'note\s+over\s+', stripped):
            in_note = True
            note_target = re.sub(r'note\s+over\s+', '', stripped).strip()
            note_lines = []
        elif stripped == "end note" and in_note:
            if note_lines:
                result["notes"].append({"target": note_target, "content": "\n".join(note_lines)})
            in_note = False
            note_lines = []
        elif in_note:
            note_lines.append(stripped)

    in_alt = False
    alt_depth = 0
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(x) for x in
               ['skinparam', '<style>', '</style>', 'legend', 'end legend',
                '<back:', '<b>', '@startuml', '@enduml', 'activate', 'deactivate',
                'participant', 'note over', 'end note', "'"]):
            continue

        m_alt = re.match(r'(alt|opt)\s+(.*)', stripped)
        if m_alt:
            in_alt = True
            alt_depth += 1
            result["errors"].append(f"[{m_alt.group(1)}] {m_alt.group(2).strip()}")
            continue
        if stripped == "end" and in_alt:
            alt_depth -= 1
            if alt_depth <= 0:
                in_alt = False
                alt_depth = 0
            continue
        if stripped in ("else", "loop"):
            continue

        m_arrow = re.match(r'(\w[\w\s]*?)\s*(->>?|-->|->|-->>?)\+*\s*(-*)\s*:?\s*(.*)', stripped)
        if m_arrow:
            caller = m_arrow.group(1).strip()
            arrow  = m_arrow.group(2)
            callee = m_arrow.group(3).strip()
            msg    = m_arrow.group(4).strip().replace("\\n", " ")
            is_return = "-->" in arrow or arrow.startswith("--")
            prefix = "↩ " if is_return else "→ "
            error_tag = " ⚠️" if in_alt else ""
            if msg and caller and not caller.startswith("@"):
                result["flow"].append(f"{prefix}`{caller}` → `{callee}` : {msg}{error_tag}")

    return result


def puml_to_markdown(parsed: dict, puml_path: Path) -> str:
    name = parsed["name"] or puml_path.stem
    lines = [f"### `{name}()`", "", f"> 源文件：`{puml_path.name}`", ""]

    if parsed["participants"]:
        by_layer: dict[str, list] = {}
        for p in parsed["participants"]:
            by_layer.setdefault(p["layer"] or "Other", []).append(p["name"])
        lines.append("**参与者（分层）**")
        lines.append("")
        for layer in ["UI Layer", "Domain Layer", "Data Layer", "Device（製品）", "External Service", "Other"]:
            if layer in by_layer:
                lines.append(f"- **{layer}**：{', '.join(f'`{p}`' for p in by_layer[layer])}")
        lines.append("")

    key_notes = [n for n in parsed["notes"]
                 if any(kw in n["content"] for kw in
                        ["data class", "val ", "class ", "params", "パラメータ", "フィールド", "リクエスト"])]
    if key_notes:
        lines += ["**关键参数 / 数据结构**", ""]
        for note in key_notes[:3]:
            lines += [f"*（{note['target']}）*", "```", note["content"], "```", ""]

    if parsed["flow"]:
        lines += ["**调用流程**", ""]
        for f in parsed["flow"][:25]:
            lines.append(f)
        if len(parsed["flow"]) > 25:
            lines.append(f"_...（共 {len(parsed['flow'])} 步，已截断）_")
        lines.append("")

    if parsed["errors"]:
        lines += ["**错误 / 条件分支**", ""]
        for err in parsed["errors"][:8]:
            lines.append(f"- {err}")
        lines.append("")

    lines += ["---", ""]
    return "\n".join(lines)


# ── 模块推断（1.0.2 ticket 目录）────────────────────────────

def infer_module_v102(puml_path: Path) -> str:
    """从路径和文件名推断 1.0.2 puml 所属模块"""
    # 优先：路径中的父目录名（如 SMN-xxx/Maintenance/xxx.puml）
    for part in puml_path.parts:
        if part in V100_MODULE_MAP:
            return V100_MODULE_MAP[part]

    # 其次：文件名关键词匹配
    stem = puml_path.stem
    for keyword, module in V102_FILENAME_RULES:
        if keyword.lower() in stem.lower():
            return module

    return "Other"


# ── 文件收集 ────────────────────────────────────────────────

def collect_v100(sdk_root: Path, module_filter: str = None) -> dict[str, list[Path]]:
    """收集 1.0.0 puml 文件（按模块目录分组）"""
    design_root = sdk_root / "API详细设计书"
    module_files: dict[str, list[Path]] = {}

    for entry in sorted(design_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        module_name = V100_MODULE_MAP.get(entry.name)
        if not module_name:
            continue
        if module_filter and module_name != module_filter:
            continue
        puml_files = [
            f for f in sorted(entry.rglob("*.puml"))
            if "Test" not in f.parts and not f.name.startswith(".")
        ]
        if puml_files:
            module_files.setdefault(module_name, []).extend(puml_files)

    return module_files


def collect_v102(sdk_root: Path, module_filter: str = None) -> dict[str, list[Path]]:
    """收集 1.0.2 puml 文件（ticket 目录，推断模块）"""
    design_root = sdk_root / "1.0.2/3.API詳細設計書"
    module_files: dict[str, list[Path]] = {}

    for puml in sorted(design_root.rglob("*.puml")):
        if ".svn" in puml.parts or puml.name.startswith("."):
            continue
        module = infer_module_v102(puml)
        if module_filter and module != module_filter:
            continue
        module_files.setdefault(module, []).append(puml)

    return module_files


# ── 输出生成 ────────────────────────────────────────────────

def process_module(module: str, puml_files: list[Path],
                   output_dir: Path, version: str) -> int:
    print(f"  {module}（{len(puml_files)} 个）", end="", flush=True)
    md_lines = [
        f"# {module} モジュール 詳細設計 (SDK {version})",
        "",
        f"> SDK バージョン：**{version}**  ",
        f"> 抽出日：{datetime.now().strftime('%Y-%m-%d')}  ",
        f"> API 数：{len(puml_files)}",
        "",
        "> 本文件展示各 API 的跨层调用流程、参数结构、错误处理路径。",
        "",
        "---",
        "",
    ]

    success = 0
    for puml_path in puml_files:
        try:
            content = puml_path.read_text(encoding="utf-8", errors="replace")
            parsed = parse_puml(content)
            md_lines.append(puml_to_markdown(parsed, puml_path))
            success += 1
        except Exception as e:
            md_lines.append(f"### `{puml_path.stem}()`\n\n> ⚠️ 解析失败：{e}\n\n---\n")

    out = output_dir / f"{module}.md"
    out.write_text("\n".join(md_lines), encoding="utf-8")
    print(f" → {out.relative_to(out.parent.parent.parent.parent)} ({success}/{len(puml_files)} OK)")
    return success


def extract_version(version: str, sdk_root: Path, output_base: Path,
                    module_filter: str = None):
    output_dir = output_base / f"v{version}" / "design"
    output_dir.mkdir(parents=True, exist_ok=True)

    if version == "1.0.0":
        module_files = collect_v100(sdk_root, module_filter)
        source_desc = "API详细设计书/"
    else:
        module_files = collect_v102(sdk_root, module_filter)
        source_desc = "1.0.2/3.API詳細設計書/"

    if not module_files:
        print(f"  未找到 puml 文件（{source_desc}）")
        return

    total = sum(len(v) for v in module_files.values())
    print(f"\n── SDK {version}（{total} 个 puml → {output_dir.relative_to(output_base.parent)}）──")
    print(f"   源目录：{source_desc}")

    api_total = 0
    for module in sorted(module_files.keys()):
        api_total += process_module(module, module_files[module], output_dir, version)

    print(f"  共处理 {api_total} 个 API")


# ── 入口 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Shimano puml → Markdown 详细设计提取器")
    parser.add_argument("--sdk-root", default=None,
                        help="SDK 根目录（默认：~/Desktop/资料/Shimano-资料/SDK）")
    parser.add_argument("--output", default=None,
                        help="输出目录（默认：./specs/design）")
    parser.add_argument("--version", choices=["1.0.0", "1.0.2", "all"],
                        default="all", help="提取版本（默认：all）")
    parser.add_argument("--module", default=None,
                        help="仅处理指定模块，如：Auth / Connection / Customize")
    args = parser.parse_args()

    sdk_root   = Path(args.sdk_root) if args.sdk_root else SDK_ROOT_DEFAULT
    output_dir = Path(args.output)   if args.output   else OUTPUT_DEFAULT

    if not sdk_root.exists():
        print(f"错误：SDK 根目录不存在：{sdk_root}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"SDK 根目录：{sdk_root}")
    print(f"输出目录：{output_dir}")

    if args.version in ("1.0.0", "all"):
        extract_version("1.0.0", sdk_root, output_dir, args.module)

    if args.version in ("1.0.2", "all"):
        extract_version("1.0.2", sdk_root, output_dir, args.module)

    print("\n完成！")
    print(f"  specs/v1.0.0/design/  ← SDK 1.0.0 时序设计")
    print(f"  specs/v1.0.2/design/  ← SDK 1.0.2 时序设计")


if __name__ == "__main__":
    main()
