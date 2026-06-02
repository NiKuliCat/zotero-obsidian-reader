#!/usr/bin/env python3
from workspace_config import load_config


def main() -> None:
    config = load_config()
    vault_dir = config.get("vault_dir", "")
    zotero_dir = config.get("zotero_dir", "")
    paper_relative_dir = config.get("paper_relative_dir", "")
    synthesis_relative_dir = config.get("synthesis_relative_dir", "")

    lines = []
    if vault_dir:
        lines.append(f"自动识别到当前的 Obsidian 仓库位置：{vault_dir}")
    if zotero_dir:
        lines.append(f"自动识别到当前的 Zotero 数据目录：{zotero_dir}")
    if paper_relative_dir:
        lines.append(f"单篇笔记默认子目录：{paper_relative_dir}")
    if synthesis_relative_dir:
        lines.append(f"综述笔记默认子目录：{synthesis_relative_dir}")

    if not lines:
        lines.append("当前尚未检测到工作区配置。")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
