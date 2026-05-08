#!/usr/bin/env python3
"""
svn_fetch.py — 从 SVN 拉取规格书并自动转换格式
用法：
  python3 svn_fetch.py                      # 拉取全部（按 svn-config.json）
  python3 svn_fetch.py --module Auth        # 只拉 Auth 模块
  python3 svn_fetch.py --mapping api-spec   # 只拉指定 mapping
  python3 svn_fetch.py --check              # 检查版本，不下载
  python3 svn_fetch.py --force              # 强制重新下载（忽略缓存）
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# 版本缓存文件（记录每个 mapping 最后拉取的 SVN revision）
REVISION_CACHE = ".svn-revisions.json"

# 转换器映射：文件类型 → 处理函数名
CONVERTERS = {
    "xlsx": "_convert_xlsx",
    "puml": "_convert_puml",
    "docx": "_convert_docx",
    "md":   "_copy_direct",
    "txt":  "_copy_direct",
}


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"ERROR: 配置文件不存在: {config_path}")
        print("请先创建 specs/svn-config.json，参考 /svn-fetch skill 中的模板。")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def load_revision_cache(cache_path: str) -> dict:
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    return {}


def save_revision_cache(cache_path: str, cache: dict):
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def get_credentials(config: dict) -> tuple[str, str]:
    user_env = config.get("username_env", "SVN_USER")
    pass_env = config.get("password_env", "SVN_PASS")
    username = os.environ.get(user_env, "")
    password = os.environ.get(pass_env, "")
    if not username or not password:
        print(f"WARNING: 凭据环境变量未设置 ({user_env}, {pass_env})")
        print("请运行：")
        print(f"  export {user_env}=your_username")
        print(f"  export {pass_env}=your_password")
    return username, password


def svn_get_revision(url: str, username: str, password: str) -> str | None:
    """获取 SVN URL 的当前 revision。"""
    cmd = ["svn", "info", "--non-interactive", url]
    if username:
        cmd += ["--username", username, "--password", password, "--no-auth-cache"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  SVN info 失败: {result.stderr.strip()}")
            return None
        for line in result.stdout.splitlines():
            if line.startswith("Last Changed Rev:") or line.startswith("Revision:"):
                return line.split(":")[-1].strip()
    except subprocess.TimeoutExpired:
        print(f"  SVN info 超时: {url}")
    except FileNotFoundError:
        print("ERROR: svn 命令未找到。请安装 subversion: brew install subversion")
        sys.exit(1)
    return None


def svn_export(url: str, local_path: str, username: str, password: str) -> bool:
    """从 SVN 导出文件到本地目录。"""
    os.makedirs(local_path, exist_ok=True)
    cmd = [
        "svn", "export", "--force", "--non-interactive",
        url, local_path
    ]
    if username:
        cmd += ["--username", username, "--password", password, "--no-auth-cache"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  SVN export 失败: {result.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  SVN export 超时: {url}")
        return False


def _convert_xlsx(local_path: str, mapping: dict):
    """xlsx → Markdown（调用 extract-specs.py）。"""
    script = Path(__file__).parent / "extract-specs.py"
    if not script.exists():
        script = Path.home() / ".claude/scripts/extract-specs.py"
    if not script.exists():
        print(f"  WARNING: extract-specs.py 未找到，跳过 xlsx 转换")
        return
    print(f"  转换 xlsx → Markdown ...")
    result = subprocess.run(
        [sys.executable, str(script), "--input-dir", local_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  xlsx 转换失败: {result.stderr.strip()}")
    else:
        print(f"  xlsx 转换完成")


def _convert_puml(local_path: str, mapping: dict):
    """puml → Markdown（调用 puml2md.py）。"""
    script = Path(__file__).parent / "puml2md.py"
    if not script.exists():
        script = Path.home() / ".claude/scripts/puml2md.py"
    if not script.exists():
        print(f"  WARNING: puml2md.py 未找到，跳过 puml 转换")
        return
    print(f"  转换 puml → Markdown ...")
    result = subprocess.run(
        [sys.executable, str(script), local_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  puml 转换失败: {result.stderr.strip()}")
    else:
        print(f"  puml 转换完成")


def _convert_docx(local_path: str, mapping: dict):
    """docx → Markdown（调用 pandoc）。"""
    pandoc = subprocess.run(["which", "pandoc"], capture_output=True, text=True)
    if pandoc.returncode != 0:
        print(f"  WARNING: pandoc 未安装，跳过 docx 转换。安装：brew install pandoc")
        return
    docx_files = list(Path(local_path).glob("**/*.docx"))
    if not docx_files:
        print(f"  没有找到 .docx 文件")
        return
    print(f"  转换 {len(docx_files)} 个 docx → Markdown ...")
    for docx in docx_files:
        out_md = docx.with_suffix(".md")
        result = subprocess.run(
            ["pandoc", str(docx), "-o", str(out_md), "--wrap=none"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  {docx.name} 转换失败: {result.stderr.strip()}")
        else:
            print(f"  ✓ {docx.name} → {out_md.name}")


def _copy_direct(local_path: str, mapping: dict):
    """md/txt 直接使用，无需转换。"""
    print(f"  Markdown/文本文件已就位，无需转换")


def process_mapping(mapping: dict, svn_base_url: str, username: str, password: str,
                    revision_cache: dict, force: bool, check_only: bool) -> str | None:
    """处理单个 mapping，返回新的 revision（如果拉取了）。"""
    svn_path = mapping["svn_path"]
    local_path = mapping["local"]
    file_type = mapping.get("type", "md")
    desc = mapping.get("description", svn_path)
    full_url = svn_base_url.rstrip("/") + "/" + svn_path.lstrip("/")

    print(f"\n📁 {desc} ({svn_path})")
    print(f"   SVN: {full_url}")
    print(f"   本地: {local_path}")

    # 检查远端 revision
    remote_rev = svn_get_revision(full_url, username, password)
    if remote_rev is None:
        print(f"  ⚠️  无法获取 SVN revision，跳过")
        return None

    cached_rev = revision_cache.get(svn_path)
    print(f"   Revision: 远端={remote_rev}, 本地缓存={cached_rev or '(无)'}")

    if check_only:
        if remote_rev != cached_rev:
            print(f"   🔄 有更新（{cached_rev} → {remote_rev}）")
        else:
            print(f"   ✅ 已是最新")
        return None

    if not force and remote_rev == cached_rev and os.path.exists(local_path):
        print(f"   ✅ 已是最新，跳过下载")
        return None

    # 执行拉取
    print(f"   ⬇️  正在拉取...")
    success = svn_export(full_url, local_path, username, password)
    if not success:
        return None

    print(f"   ✅ 拉取完成")

    # 格式转换
    converter_name = CONVERTERS.get(file_type, "_copy_direct")
    converter = globals()[converter_name]
    converter(local_path, mapping)

    return remote_rev


def main():
    parser = argparse.ArgumentParser(description="从 SVN 拉取规格书")
    parser.add_argument("--config", default="specs/svn-config.json", help="配置文件路径")
    parser.add_argument("--module", help="只拉取包含此关键词的 mapping")
    parser.add_argument("--mapping", help="只拉取指定 svn_path 的 mapping")
    parser.add_argument("--check", action="store_true", help="只检查版本，不下载")
    parser.add_argument("--force", action="store_true", help="强制重新下载（忽略缓存）")
    args = parser.parse_args()

    config = load_config(args.config)
    username, password = get_credentials(config)
    svn_base_url = config["svn_url"]
    mappings = config.get("mappings", [])

    # 过滤 mappings
    if args.mapping:
        mappings = [m for m in mappings if args.mapping in m["svn_path"]]
    if args.module:
        keyword = args.module.lower()
        mappings = [m for m in mappings
                    if keyword in m.get("svn_path", "").lower()
                    or keyword in m.get("description", "").lower()]

    if not mappings:
        print("没有匹配的 mapping，请检查 --module / --mapping 参数或 svn-config.json")
        sys.exit(0)

    # 加载 revision 缓存
    revision_cache = load_revision_cache(REVISION_CACHE)

    print(f"SVN 基础 URL: {svn_base_url}")
    print(f"处理 {len(mappings)} 个 mapping")

    updated = 0
    for mapping in mappings:
        new_rev = process_mapping(
            mapping, svn_base_url, username, password,
            revision_cache, args.force, args.check
        )
        if new_rev:
            revision_cache[mapping["svn_path"]] = new_rev
            updated += 1

    # 保存缓存
    if updated > 0:
        save_revision_cache(REVISION_CACHE, revision_cache)

    print(f"\n{'─'*50}")
    if args.check:
        print("检查完成（未下载任何文件）")
    else:
        print(f"完成！更新了 {updated} 个 mapping")
        if updated > 0:
            print("\n建议更新规格索引：")
            print("  /spec-indexer")


if __name__ == "__main__":
    main()
