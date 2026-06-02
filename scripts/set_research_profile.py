#!/usr/bin/env python3
import argparse

from workspace_config import get_research_profile, update_research_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set or update the persisted research profile used by Zotero Obsidian notes."
    )
    parser.add_argument("--domain", help="Primary research domain")
    parser.add_argument("--focus", default="", help="Current research focus or thesis topic")
    parser.add_argument("--keywords", default="", help="Comma-separated research keywords")
    return parser.parse_args()


def prompt_if_missing(value: str | None, prompt: str) -> str:
    if value and value.strip():
        return value.strip()
    return input(prompt).strip()


def main() -> None:
    args = parse_args()
    current = get_research_profile()
    domain = prompt_if_missing(args.domain or current["domain"], "研究领域：")

    if args.focus:
        focus = args.focus.strip()
    elif current["focus"]:
        focus = current["focus"]
    else:
        focus = input("当前研究重点（可留空）：").strip()

    if args.keywords:
        keywords_raw = args.keywords
    elif current["keywords"]:
        keywords_raw = ",".join(current["keywords"])
    else:
        keywords_raw = input("研究关键词（逗号分隔，可留空）：").strip()

    keywords = [part.strip() for part in keywords_raw.split(",") if part.strip()]
    path = update_research_profile(domain=domain, focus=focus, keywords=keywords)
    print(path)


if __name__ == "__main__":
    main()
