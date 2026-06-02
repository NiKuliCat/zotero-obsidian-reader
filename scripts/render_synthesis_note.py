#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path

from write_obsidian_note import resolve_output_path, write_text
from workspace_config import default_filename_suffix, default_relative_dir, detect_vault_dir


DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "templates" / "synthesis-note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render one synthesis note from many Zotero items.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--relative-dir")
    parser.add_argument("--filename-suffix")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def load_items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload.get("items", [])


def extract_year(item: dict) -> str:
    fields = item.get("fields", {})
    raw_date = fields.get("date") or item.get("dateAdded") or ""
    match = re.search(r"(\d{4})", raw_date)
    return match.group(1) if match else ""


def format_title(item: dict) -> str:
    return item.get("fields", {}).get("title") or item.get("title") or "Untitled"


def format_authors(item: dict) -> str:
    if item.get("creators") and isinstance(item["creators"][0], dict):
        names = [creator.get("displayName", "") for creator in item["creators"] if creator.get("displayName")]
    else:
        names = [name for name in item.get("creators", []) if name]
    return ", ".join(names)


def build_table(items: list[dict]) -> str:
    lines = [
        "| Title | Year | Authors | Key |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {format_title(item)} | {extract_year(item)} | {format_authors(item)} | `{item.get('itemKey', '')}` |"
        )
    return "\n".join(lines)


def count_tags(items: list[dict]) -> Counter:
    counter: Counter = Counter()
    for item in items:
        for tag in item.get("tags", []):
            name = tag.get("name")
            if name:
                counter[name] += 1
    return counter


def build_common_themes(items: list[dict]) -> str:
    counter = count_tags(items)
    if not counter:
        return "- No Zotero tags were available, so themes need manual synthesis."
    return "\n".join(f"- {tag}: {count}" for tag, count in counter.most_common(10))


def build_method_clusters(items: list[dict]) -> str:
    lines = []
    for item in items:
        abstract = item.get("fields", {}).get("abstractNote", "")
        title = format_title(item)
        snippet = abstract[:220].replace("\n", " ").strip()
        if snippet:
            lines.append(f"- **{title}**: {snippet}...")
        else:
            lines.append(f"- **{title}**: TODO: summarize the method manually.")
    return "\n".join(lines) if lines else "- No items were available."


def render_template(template: str, context: dict[str, str]) -> str:
    output = template
    for key, value in context.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def main() -> None:
    args = parse_args()
    items = load_items(args.input)
    if not items:
        raise SystemExit("Input JSON contains no items")

    context = {
        "title": args.title,
        "topic": args.topic or args.title,
        "paper_count": str(len(items)),
        "scope": f"This synthesis note covers {len(items)} Zotero items for topic `{args.topic or args.title}`.",
        "included_papers_table": build_table(items),
        "common_themes": build_common_themes(items),
        "method_clusters": build_method_clusters(items),
        "strengths": "- TODO: Compare recurring strengths across the included papers.",
        "limitations": "- TODO: Compare recurring limitations, assumptions, and blind spots.",
        "gaps": "- TODO: Record unresolved research gaps and opportunities.",
        "next_reading": "- TODO: Add the next most relevant papers to read or reproduce.",
    }
    template = args.template.read_text(encoding="utf-8")
    note = render_template(template, context)

    if args.stdout:
        print(note)
        return

    vault_dir = detect_vault_dir(args.output_dir)
    relative_dir = args.relative_dir if args.relative_dir is not None else default_relative_dir("synthesis")
    filename_suffix = args.filename_suffix if args.filename_suffix is not None else default_filename_suffix("synthesis")
    output_path = resolve_output_path(vault_dir, relative_dir, args.title, filename_suffix)
    write_text(output_path, note, overwrite=args.overwrite)
    print(output_path)


if __name__ == "__main__":
    main()
