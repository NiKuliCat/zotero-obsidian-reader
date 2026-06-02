#!/usr/bin/env python3
import re


INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


def normalize_filename(name: str, max_length: int = 120) -> str:
    value = re.sub(INVALID_CHARS, "_", name).strip()
    value = re.sub(r"\s+", " ", value)
    value = value.rstrip(". ")
    if not value:
        value = "untitled"
    if len(value) > max_length:
        value = value[:max_length].rstrip(" ._")
    return value or "untitled"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize a Windows-safe filename.")
    parser.add_argument("name")
    args = parser.parse_args()
    print(normalize_filename(args.name))
