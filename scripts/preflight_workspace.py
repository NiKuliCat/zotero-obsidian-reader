#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from workspace_config import detect_vault_dir, detect_zotero_dir, get_research_profile, load_config


def build_human_lines(result: dict) -> list[str]:
    lines: list[str] = []
    vault_dir = result.get("vault_dir") or ""
    zotero_dir = result.get("zotero_dir") or ""
    status = result.get("status") or ""
    detected_now = result.get("detected_now") or {}
    profile = result.get("research_profile") or {}

    if detected_now.get("vault_dir") and vault_dir:
        lines.append(f"自动识别到当前的 Obsidian 仓库位置：{vault_dir}")
    elif vault_dir:
        lines.append(f"当前 Obsidian 仓库位置：{vault_dir}")

    if detected_now.get("zotero_dir") and zotero_dir:
        lines.append(f"自动识别到当前的 Zotero 数据目录：{zotero_dir}")
    elif zotero_dir:
        lines.append(f"当前 Zotero 数据目录：{zotero_dir}")

    if status == "missing_research_profile":
        lines.append("当前尚未设置研究画像，已暂停文献读取与写笔记。")
        lines.append("请先告诉我你的研究领域；当前关注问题和关键词可以选填。")
    elif status == "ready":
        domain = profile.get("domain") or ""
        if domain:
            lines.append(f"当前研究领域：{domain}")
        lines.append("工作区预检查已完成，可以开始读取文献并生成笔记。")
    else:
        for error in result.get("errors", []):
            lines.append(error)

    return lines


def main() -> None:
    before = load_config()
    errors: list[str] = []

    vault_dir: Path | None = None
    zotero_dir: Path | None = None

    try:
        vault_dir = detect_vault_dir()
    except FileNotFoundError as exc:
        errors.append(str(exc))

    try:
        zotero_dir = detect_zotero_dir()
    except FileNotFoundError as exc:
        errors.append(str(exc))

    after = load_config()
    profile = get_research_profile(after)

    if errors:
        status = "missing_paths"
        exit_code = 1
    elif not profile["domain"]:
        status = "missing_research_profile"
        exit_code = 2
    else:
        status = "ready"
        exit_code = 0

    result = {
        "status": status,
        "vault_dir": str(vault_dir or after.get("vault_dir") or ""),
        "zotero_dir": str(zotero_dir or after.get("zotero_dir") or ""),
        "research_profile": profile,
        "detected_now": {
            "vault_dir": bool((after.get("vault_dir") or "") and not before.get("vault_dir")),
            "zotero_dir": bool((after.get("zotero_dir") or "") and not before.get("zotero_dir")),
        },
        "errors": errors,
    }

    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n".join(build_human_lines(result)))

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
