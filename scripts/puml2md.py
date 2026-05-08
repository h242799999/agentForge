#!/usr/bin/env python3
"""
puml2md.py — PlantUML 時序図 → 骨架 Markdown 转换器（零 token）

用法:
  python scripts/puml2md.py <目录路径>   # 递归处理目录下所有 .puml
  python scripts/puml2md.py <file.puml>  # 处理单个文件

输出:
  骨架 .md 文件，与 .puml 同目录
  含 <!-- [AI补全] --> 标记，供 /puml-to-md skill 补全语义内容
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

# ── 层级颜色映射 ────────────────────────────────────────────────
LAYER_MAP = {
    "#F9CCB3": "UI层",
    "#CFF1FD": "Domain层",
    "#C7F3CC": "Data层",
    "#3399FF": "製品（BLE）",
}

# ── 工具函数 ────────────────────────────────────────────────────

def clean_msg(s: str) -> str:
    """清理消息文本：去除 \n 换行、多余空格"""
    return re.sub(r'\s+', ' ', s.replace('\\n', ' ').replace('\n', ' ')).strip()


def strip_activation(s: str) -> str:
    """去除 ++ / -- 激活标记"""
    return re.sub(r'\s*[\+\-]{2}\s*$', '', s).strip()


# ── 主解析器 ────────────────────────────────────────────────────

class PumlParser:
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.feature_name = ""
        self.participants: list[tuple[str, str]] = []  # (name, layer)
        self.refs: list[str] = []
        self.events: list[dict] = []
        self._parse()

    def _parse(self):
        lines = self.lines
        i = 0
        skip_block = None  # 'legend' | 'style' | 'note'

        while i < len(lines):
            raw = lines[i]
            s = raw.strip()

            # ── 跳过空行、注释 ──
            if not s or s.startswith("'") or s.startswith("//"):
                i += 1
                continue

            # ── 跳过 style 块 ──
            if s.startswith("<style>"):
                while i < len(lines) and "</style>" not in lines[i]:
                    i += 1
                i += 1
                continue

            # ── 跳过 legend 块，但从中提取功能名 ──
            if re.match(r'^legend\b', s):
                while i < len(lines):
                    ls = lines[i].strip()
                    m = re.search(r'<b><size:\d+>([^<]+)</size></b>', ls)
                    if m:
                        self.feature_name = m.group(1).strip()
                    if ls == "end legend":
                        break
                    i += 1
                i += 1
                continue

            # ── @startuml ──
            m = re.match(r'@startuml\s*(\S*)', s)
            if m:
                if not self.feature_name:
                    self.feature_name = m.group(1)
                i += 1
                continue

            # ── participant ──
            m = re.match(r'participant\s+(\S+)(?:\s+as\s+\S+)?\s*(#[A-Fa-f0-9]+)?', s)
            if m:
                name = m.group(1)
                color = (m.group(2) or "").upper()
                layer = LAYER_MAP.get(color, "その他")
                self.participants.append((name, layer))
                i += 1
                continue

            # ── 跳过 skinparam / autonumber / activate / deactivate ──
            if re.match(r'^(skinparam|autonumber|activate|deactivate|@enduml)', s):
                i += 1
                continue

            # ── note / rnote ──
            if re.match(r'^r?note\b', s):
                content_lines, i = self._read_note(lines, i)
                note_text = clean_msg(" ".join(content_lines))
                if "pumlを参照" in note_text:
                    for ref in re.findall(r'(\S+\.puml)', note_text):
                        if ref not in self.refs:
                            self.refs.append(ref)
                else:
                    self.events.append({"type": "note", "content": note_text})
                continue

            # ── opt / alt / loop / group ──
            m = re.match(r'^(opt|alt|loop|group)\b\s*(.*)', s)
            if m:
                btype = m.group(1)
                cond = clean_msg(m.group(2))
                block, i = self._read_block(lines, i + 1, btype, cond)
                self.events.append(block)
                continue

            # ── return（独立行）──
            m = re.match(r'^return\s+(.*)', s)
            if m:
                self.events.append({"type": "return", "value": clean_msg(m.group(1))})
                i += 1
                continue

            # ── 箭头：A -> B++ : msg ──
            arrow = self._parse_arrow(s)
            if arrow:
                self.events.append(arrow)
                # 检查 throw/return in message
                msg = arrow["msg"]
                rm = re.search(r'(\S+\.puml)を参照', msg)
                if rm and rm.group(1) not in self.refs:
                    self.refs.append(rm.group(1))
                i += 1
                continue

            i += 1

    def _read_note(self, lines, i):
        """读取 note / rnote 块，返回 (内容行列表, 下一个 i)"""
        s = lines[i].strip()
        # 单行 inline note: note right of X: text
        m = re.match(r'^r?note\s+(?:right\s+of|over)\s+\S+\s*:\s*(.+)', s)
        if m:
            return [m.group(1)], i + 1

        # 多行 note
        i += 1
        content = []
        while i < len(lines):
            ls = lines[i].strip()
            if re.match(r'^end\s*r?note', ls):
                return content, i + 1
            content.append(ls)
            i += 1
        return content, i

    def _read_block(self, lines, i, btype, cond):
        """读取 opt/alt/loop 块，处理 else 分支，返回 (block_dict, 下一个 i)"""
        branches = [{"cond": cond, "events": []}]
        depth = 1

        while i < len(lines):
            s = lines[i].strip()

            if re.match(r'^(opt|alt|loop|group)\b', s):
                depth += 1
            elif s == "end":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            elif re.match(r'^else\b', s) and depth == 1:
                else_cond = clean_msg(s[4:].strip()) or "else"
                branches.append({"cond": else_cond, "events": []})
                i += 1
                continue

            # 递归处理内部内容（仅处理 depth==1 的行）
            if depth == 1:
                arrow = self._parse_arrow(s)
                if arrow:
                    branches[-1]["events"].append(arrow)
                elif re.match(r'^r?note\b', s):
                    note_lines, i = self._read_note(lines, i)
                    note_text = clean_msg(" ".join(note_lines))
                    if note_text and "pumlを参照" not in note_text:
                        branches[-1]["events"].append({"type": "note", "content": note_text})
                    continue
                elif re.match(r'^(opt|alt|loop|group)\b', s):
                    # 递归（已在上面 depth++ 处理，但需要收集子块）
                    pass
            i += 1

        return {"type": btype, "cond": cond, "branches": branches}, i

    def _parse_arrow(self, s: str) -> dict | None:
        """解析箭头行，返回 arrow dict 或 None"""
        # 先按第一个 ' : ' 分割，提取 lhs 和 message
        colon_idx = s.find(' : ')
        if colon_idx == -1:
            # 尝试 ': ' (无前置空格)
            colon_idx = s.find(': ')
            if colon_idx == -1:
                return None
        lhs = s[:colon_idx].strip()
        msg = clean_msg(s[colon_idx + 3:] if ' : ' in s[:colon_idx + 3] else s[colon_idx + 2:])

        # 解析 lhs: SRC ARROW DST[++/--]
        m = re.match(r'^(\S+)\s*(-+>+|-+>>+)\s*(.+?)(?:\s*[\+\-]{2})?$', lhs)
        if not m:
            return None
        src = m.group(1)
        arrow = m.group(2)
        dst = strip_activation(m.group(3).strip())
        is_return = arrow.startswith("--")

        throw_m = re.match(r'throw\s+(\S+)', msg)
        return_m = re.match(r'return\s+(.*)', msg)

        return {
            "type": "arrow",
            "src": src,
            "dst": dst,
            "msg": msg,
            "is_return": is_return,
            "is_throw": bool(throw_m),
            "throw_val": throw_m.group(1) if throw_m else None,
            "return_val": clean_msg(return_m.group(1)) if return_m else None,
        }


# ── MD 渲染 ────────────────────────────────────────────────────

def render_events(events: list, indent: int = 0) -> list[str]:
    """将 events 列表渲染为 Markdown 行"""
    out = []
    pad = "  " * indent

    for ev in events:
        t = ev["type"]

        if t == "arrow":
            if ev.get("is_return") or ev.get("is_throw"):
                continue  # 在错误章节单独处理
            out.append(f"{pad}- `{ev['src']}` → `{ev['dst']}`: {ev['msg']}")

        elif t == "note":
            content = ev.get("content", "")
            if content:
                out.append(f"{pad}  > _{content}_")

        elif t in ("opt", "alt", "loop", "group"):
            branches = ev.get("branches", [])
            main_cond = ev.get("cond", "")
            type_label = {"opt": "opt", "alt": "alt", "loop": "loop", "group": "group"}[t]

            if t == "loop":
                out.append(f"{pad}- **[{type_label}]** {main_cond}")
                for branch in branches:
                    out.extend(render_events(branch["events"], indent + 1))

            elif t == "opt":
                out.append(f"{pad}- **[opt]** `{main_cond}`")
                for branch in branches:
                    out.extend(render_events(branch["events"], indent + 1))

            elif t == "alt":
                for branch in branches:
                    out.append(f"{pad}- **[alt]** `{branch['cond']}`")
                    out.extend(render_events(branch["events"], indent + 1))

        elif t == "return":
            pass  # 在返回值章节处理

    return out


def collect_errors(events: list) -> list[tuple[str, str, str]]:
    """收集所有 throw/return error，返回 [(condition, kind, value)]"""
    errors = []
    for ev in events:
        t = ev["type"]
        if t == "arrow":
            if ev.get("is_throw") and ev.get("throw_val"):
                errors.append(("", "throw", ev["throw_val"]))
            elif ev.get("return_val") and _is_error(ev["return_val"]):
                errors.append(("", "return", ev["return_val"]))
        elif t in ("opt", "alt", "loop", "group"):
            for branch in ev.get("branches", []):
                cond = branch.get("cond") or ev.get("cond", "")
                for inner in branch["events"]:
                    if inner["type"] == "arrow":
                        if inner.get("is_throw") and inner.get("throw_val"):
                            errors.append((cond, "throw", inner["throw_val"]))
                        elif inner.get("return_val") and _is_error(inner["return_val"]):
                            errors.append((cond, "return", inner["return_val"]))
                # 递归
                errors.extend(_collect_errors_inner(branch["events"], cond))
    return errors


def _collect_errors_inner(events, parent_cond):
    errors = []
    for ev in events:
        t = ev["type"]
        if t in ("opt", "alt", "loop", "group"):
            for branch in ev.get("branches", []):
                cond = branch.get("cond") or parent_cond
                for inner in branch["events"]:
                    if inner["type"] == "arrow":
                        if inner.get("is_throw") and inner.get("throw_val"):
                            errors.append((cond, "throw", inner["throw_val"]))
                        elif inner.get("return_val") and _is_error(inner["return_val"]):
                            errors.append((cond, "return", inner["return_val"]))
                errors.extend(_collect_errors_inner(branch["events"], cond))
    return errors


def _is_error(val: str) -> bool:
    return any(k in val for k in ("Exception", "Error", "FAILED", "DISABLED", "BAD_STATUS"))


def get_final_return(events: list) -> str:
    """找最后一个非错误的 return 值"""
    for ev in reversed(events):
        if ev["type"] == "return":
            if not _is_error(ev["value"]):
                return ev["value"]
        if ev["type"] == "arrow" and ev.get("is_return") and ev.get("return_val"):
            val = ev["return_val"]
            if not _is_error(val):
                return val
    return ""


def get_call_chain(events: list) -> list[str]:
    """提取主流程参与者链（去重，保持顺序）"""
    seen: list[str] = []
    for ev in events:
        if ev["type"] == "arrow" and not ev.get("is_return"):
            for actor in [ev["src"], ev["dst"]]:
                if actor not in seen:
                    seen.append(actor)
    return seen


# ── MD 生成 ────────────────────────────────────────────────────

def generate_md(parsers: list["PumlParser"]) -> str:
    if not parsers:
        return ""

    # 取第一个的 feature_name 作为文档标题
    feature_name = parsers[0].feature_name or "Unknown"

    lines: list[str] = []
    lines.append(f"# {feature_name} API 详细设计\n")

    # 概述
    lines.append("## 概述\n")
    lines.append("<!-- [AI补全] 请在此补充功能的一句话说明 -->\n")

    # 层级构成（来自第一个文件的参与者）
    all_participants = parsers[0].participants
    if all_participants:
        layer_groups: dict[str, list[str]] = defaultdict(list)
        for name, layer in all_participants:
            if name not in layer_groups[layer]:
                layer_groups[layer].append(name)

        lines.append("## 层级构成\n")
        lines.append("| 层级 | 组件 |")
        lines.append("|---|---|")
        for lname in ["UI层", "Domain层", "Data层", "製品（BLE）", "その他"]:
            if lname in layer_groups:
                comps = "、".join(layer_groups[lname])
                lines.append(f"| {lname} | {comps} |")
        lines.append("")

    lines.append("---\n")

    # 每个方法
    for parser in parsers:
        fname = parser.feature_name or "unknown"
        events = parser.events

        lines.append(f"## {fname}\n")

        # 时序概览
        chain = get_call_chain(events)
        if chain:
            display = chain[:7]
            overview = " → ".join(f"`{p}`" for p in display)
            if len(chain) > 7:
                overview += " → ..."
            lines.append("### 时序概览\n")
            lines.append(overview + "\n")

        # 主要流程
        flow = render_events(events)
        if flow:
            lines.append("### 主要流程\n")
            lines.extend(flow)
            lines.append("")

        # 错误/异常一览
        errors = collect_errors(events)
        # 去重
        seen_errors: set[tuple] = set()
        unique_errors = []
        for e in errors:
            key = (e[1], e[2])
            if key not in seen_errors:
                seen_errors.add(key)
                unique_errors.append(e)

        if unique_errors:
            lines.append("### 错误/异常一览\n")
            lines.append("| 条件 | 类型 | 返回值/异常 |")
            lines.append("|---|---|---|")
            for cond, kind, val in unique_errors:
                lines.append(f"| {cond} | {kind} | `{val}` |")
            lines.append("")

        # 返回值
        ret = get_final_return(events)
        if ret:
            lines.append("### 返回值\n")
            lines.append("| 类型 | 说明 |")
            lines.append("|---|---|")
            lines.append(f"| `{ret}` | <!-- [AI补全] --> |")
            lines.append("")

        # 参考文档
        if parser.refs:
            lines.append("### 参考文档\n")
            lines.append("| 文档 | 内容 |")
            lines.append("|---|---|")
            for ref in parser.refs:
                lines.append(f"| {ref} | <!-- [AI补全] --> |")
            lines.append("")

        lines.append("---\n")

    lines.append("<!-- 由 scripts/puml2md.py 自动生成骨架 -->")
    lines.append("<!-- 使用 /puml-to-md 补全 [AI补全] 标记并校验完整性 -->")

    return "\n".join(lines)


# ── 入口 ────────────────────────────────────────────────────────

def process_directory(dir_path: Path):
    puml_files = sorted(dir_path.glob("*.puml"))
    if not puml_files:
        return

    # 按 feature 根名分组（去掉 get/set/update 等动词前缀）
    def base_name(stem: str) -> str:
        return re.sub(r'^(get|set|update|delete|create|start|stop|resume|cancel|pause)', '',
                      stem, flags=re.IGNORECASE) or stem

    groups: dict[str, list[Path]] = defaultdict(list)
    for f in puml_files:
        groups[base_name(f.stem)].append(f)

    for base, files in groups.items():
        parsers = []
        for f in sorted(files):
            try:
                text = f.read_text(encoding="utf-8")
                parsers.append(PumlParser(text))
            except Exception as e:
                print(f"  警告: 读取 {f} 失败: {e}")

        if not parsers:
            continue

        # 输出文件名：使用第一个文件的 feature_name 或 stem
        out_name = parsers[0].feature_name or files[0].stem
        out_path = dir_path / f"{out_name}.md"
        md = generate_md(parsers)
        out_path.write_text(md, encoding="utf-8")
        src_list = ", ".join(f.name for f in files)
        print(f"  ✓ {out_path.name}  ←  {src_list}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = Path(sys.argv[1]).expanduser()

    if target.is_file() and target.suffix == ".puml":
        text = target.read_text(encoding="utf-8")
        parser = PumlParser(text)
        out_name = parser.feature_name or target.stem
        out_path = target.parent / f"{out_name}.md"
        md = generate_md([parser])
        out_path.write_text(md, encoding="utf-8")
        print(f"✓ {out_path}")

    elif target.is_dir():
        # 递归处理每个子目录
        dirs_processed = set()
        for puml_file in sorted(target.rglob("*.puml")):
            d = puml_file.parent
            if d not in dirs_processed:
                dirs_processed.add(d)
                print(f"\n📁 {d.relative_to(target) if d != target else '.'}")
                process_directory(d)
    else:
        print(f"错误：路径不存在或不是 .puml 文件/目录: {target}")
        sys.exit(1)

    print("\n完成！运行 /puml-to-md 可补全 [AI补全] 标记、校验完整性。")


if __name__ == "__main__":
    main()
