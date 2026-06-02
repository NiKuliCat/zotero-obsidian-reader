#!/usr/bin/env python3
import argparse
from pathlib import Path

from normalize_filename import normalize_filename
from workspace_config import default_filename_suffix, default_relative_dir, detect_vault_dir


def resolve_output_path(vault_dir: Path, relative_dir: str, title: str, filename_suffix: str = "") -> Path:
    safe_title = normalize_filename(f"{title}{filename_suffix}")
    if relative_dir:
        return vault_dir / relative_dir / f"{safe_title}.md"
    return vault_dir / f"{safe_title}.md"


def write_text(path: Path, text: str, overwrite: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing note: {path}")
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Markdown content into an Obsidian vault.")
    parser.add_argument("--vault-dir", type=Path)
    parser.add_argument("--relative-dir")
    parser.add_argument("--mode", choices=["paper", "synthesis"], default="paper")
    parser.add_argument("--filename-suffix")
    parser.add_argument("--title", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    vault_dir = detect_vault_dir(args.vault_dir)
    relative_dir = args.relative_dir if args.relative_dir is not None else default_relative_dir(args.mode)
    filename_suffix = args.filename_suffix if args.filename_suffix is not None else default_filename_suffix(args.mode)
    output_path = resolve_output_path(vault_dir, relative_dir, args.title, filename_suffix)
    text = args.input.read_text(encoding="utf-8")
    write_text(output_path, text, overwrite=args.overwrite)
    print(output_path)


if __name__ == "__main__":
    main()
