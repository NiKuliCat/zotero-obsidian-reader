#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

from write_obsidian_note import resolve_output_path, write_text
from workspace_config import (
    default_filename_suffix,
    default_relative_dir,
    detect_vault_dir,
    get_research_profile,
    has_research_profile,
)


DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "templates" / "paper-note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render one Obsidian paper note from extracted Zotero JSON.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--relative-dir")
    parser.add_argument("--filename-suffix")
    parser.add_argument("--item-key")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def choose_item(payload: dict, item_key: str | None) -> dict:
    items = payload.get("items", [])
    if not items:
        raise SystemExit("Input JSON contains no items")
    if item_key:
        for item in items:
            if item.get("itemKey") == item_key:
                return item
        raise SystemExit(f"Could not find itemKey {item_key} in input JSON")
    return items[0]


def strip_year(raw_date: str | None) -> str:
    if not raw_date:
        return ""
    match = re.search(r"(\d{4})", raw_date)
    return match.group(1) if match else ""


def format_authors(item: dict) -> tuple[str, str]:
    creators = item.get("creators", [])
    names = [creator.get("displayName", "").strip() for creator in creators if creator.get("displayName")]
    authors_text = ", ".join(names)
    authors_yaml = ", ".join(f'"{name}"' for name in names)
    return authors_text, authors_yaml


def format_tags(item: dict) -> str:
    tags = [tag.get("name", "").strip() for tag in item.get("tags", []) if tag.get("name")]
    return ", ".join(f'"{tag}"' for tag in tags)


def format_notes_block(item: dict) -> str:
    notes = item.get("notes", [])
    annotations = item.get("annotations", [])
    blocks = []
    for note in notes:
        text = note.get("noteText") or note.get("noteHtml") or ""
        if text:
            blocks.append(f"- 笔记：{text}")
    for annotation in annotations:
        text = annotation.get("text") or ""
        comment = annotation.get("comment") or ""
        page = annotation.get("pageLabel") or ""
        pieces = [piece for piece in [text, comment] if piece]
        if pieces:
            prefix = f"第 {page} 页：" if page else ""
            blocks.append(f"- 批注：{prefix}{' | '.join(pieces)}")
    return "\n".join(blocks) if blocks else "- 暂无 Zotero 笔记或批注。"


def format_attachments_block(item: dict) -> str:
    attachments = item.get("attachments", [])
    if not attachments:
        return "- 暂无子附件信息。"
    lines = []
    for attachment in attachments:
        path = attachment.get("resolvedPath") or attachment.get("path") or ""
        content_type = attachment.get("contentType") or "unknown"
        lines.append(f"- `{content_type}`：{path}")
    return "\n".join(lines)


def build_context(item: dict) -> dict[str, str]:
    fields = item.get("fields", {})
    authors_text, authors_yaml = format_authors(item)
    research_profile = get_research_profile()
    research_domain = research_profile.get("domain") or "未设置。首次正式生成笔记前请先填写研究领域。"
    research_focus = research_profile.get("focus") or "未设置"
    research_keywords = "、".join(research_profile.get("keywords", [])) or "未设置"

    return {
        "title": fields.get("title", "Untitled"),
        "item_key": item.get("itemKey", ""),
        "item_id": str(item.get("itemID", "")),
        "citation_key": fields.get("citationKey", ""),
        "item_type": item.get("itemType", ""),
        "authors_text": authors_text,
        "authors_yaml": authors_yaml,
        "year": strip_year(fields.get("date") or item.get("dateAdded")),
        "tags_yaml": format_tags(item),
        "source": fields.get("publicationTitle") or fields.get("repository") or fields.get("libraryCatalog") or "",
        "url": fields.get("url", ""),
        "doi": fields.get("DOI", ""),
        "abstract": fields.get("abstractNote", "暂无摘要，可在阅读全文后手动补充。"),
        "research_question": "TODO：概括这篇论文试图解决的核心问题，以及它为什么重要。",
        "core_method": "TODO：概括核心方法、技术路线、关键模块或理论思路。",
        "evidence": "TODO：总结实验设置、数据来源、评价指标和主要结果。",
        "contribution": "TODO：用 2-4 条列出这篇工作的主要贡献。",
        "limitations": "TODO：记录局限性、假设条件、适用边界和仍未解决的问题。",
        "research_domain": research_domain,
        "research_focus": research_focus,
        "research_keywords": research_keywords,
        "relevance_score": "TODO：结合当前课题评估为 高 / 中 / 低。",
        "relevance_reason": "TODO：说明这篇论文与当前研究领域、方法路线或应用场景的具体关联。",
        "relevance": "TODO：说明这篇论文与当前研究方向、选题或技术路线的关系。",
        "notes_block": format_notes_block(item),
        "attachments_block": format_attachments_block(item),
        "follow_up": "- TODO：补充后续阅读、引用、复现实验或可继续追踪的问题。",
    }


def infer_relative_dir(item: dict, explicit_relative_dir: str | None) -> str:
    if explicit_relative_dir is not None:
        return explicit_relative_dir

    configured = default_relative_dir("paper")
    if configured:
        return configured

    collections = item.get("collections", [])
    if collections:
        return "/".join(collections[0])
    return ""


def render_template(template: str, context: dict[str, str]) -> str:
    output = template
    for key, value in context.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def main() -> None:
    args = parse_args()
    if not has_research_profile():
        raise SystemExit(
            "Missing research profile. Ask the user for their research domain, current focus, and keywords, "
            "save them with set_research_profile.py, and only then render the note."
        )

    payload = load_payload(args.input)
    item = choose_item(payload, args.item_key)
    context = build_context(item)
    template = args.template.read_text(encoding="utf-8")
    note = render_template(template, context)

    if args.stdout:
        print(note)
        return

    vault_dir = detect_vault_dir(args.output_dir)
    relative_dir = infer_relative_dir(item, args.relative_dir)
    filename_suffix = args.filename_suffix if args.filename_suffix is not None else default_filename_suffix("paper")
    output_path = resolve_output_path(vault_dir, relative_dir, context["title"], filename_suffix)
    write_text(output_path, note, overwrite=args.overwrite)
    print(output_path)


if __name__ == "__main__":
    main()
