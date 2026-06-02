#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from html import unescape
from pathlib import Path
from typing import Any

from workspace_config import detect_zotero_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Zotero item metadata as JSON from a local Zotero database."
    )
    parser.add_argument("--db", type=Path, help="Path to zotero.sqlite or zotero.sqlite.bak")
    parser.add_argument("--item-id", type=int, help="Exact Zotero itemID")
    parser.add_argument("--item-key", help="Exact Zotero item key, e.g. 6KXCIRFL")
    parser.add_argument(
        "--title-contains",
        help="Case-insensitive title search. Returns a list when multiple items match.",
    )
    parser.add_argument(
        "--include-fulltext",
        action="store_true",
        help="Include .zotero-ft-cache text when available for child attachments.",
    )
    parser.add_argument(
        "--find",
        action="store_true",
        help="Only list matching items with their itemKey and basic metadata.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    if not any([args.item_id, args.item_key, args.title_contains]):
        parser.error("one of --item-id, --item-key, or --title-contains is required")

    return args


def choose_db_path(override: Path | None) -> Path:
    if override:
        return override

    zotero_dir = detect_zotero_dir()
    candidates = [
        zotero_dir / "zotero.sqlite",
        zotero_dir / "zotero.sqlite.bak",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find zotero.sqlite(.bak) under {zotero_dir}")


def open_db(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def strip_html(value: str | None) -> str | None:
    if value is None:
        return None
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def fetch_item_ids(conn: sqlite3.Connection, args: argparse.Namespace) -> list[int]:
    cur = conn.cursor()
    if args.item_id:
        rows = cur.execute(
            "select itemID from items where itemID = ?",
            (args.item_id,),
        ).fetchall()
    elif args.item_key:
        rows = cur.execute(
            "select itemID from items where key = ?",
            (args.item_key,),
        ).fetchall()
    else:
        rows = cur.execute(
            """
            select distinct i.itemID
            from items i
            join itemData d on d.itemID = i.itemID
            join fieldsCombined f on f.fieldID = d.fieldID
            join itemDataValues v on v.valueID = d.valueID
            where f.fieldName = 'title' and lower(v.value) like ?
            order by i.itemID
            """,
            (f"%{args.title_contains.lower()}%",),
        ).fetchall()
    return [row[0] for row in rows]


def fetch_item_summary(conn: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    cur = conn.cursor()
    row = cur.execute(
        """
        select i.itemID, i.key, it.typeName, i.dateAdded, i.dateModified
        from items i
        join itemTypesCombined it on it.itemTypeID = i.itemTypeID
        where i.itemID = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"itemID {item_id} not found")

    title_row = cur.execute(
        """
        select v.value
        from itemData d
        join fieldsCombined f on f.fieldID = d.fieldID
        join itemDataValues v on v.valueID = d.valueID
        where d.itemID = ? and f.fieldName = 'title'
        """,
        (item_id,),
    ).fetchone()

    creators = fetch_creators(conn, item_id)
    return {
        "itemID": row[0],
        "itemKey": row[1],
        "itemType": row[2],
        "dateAdded": row[3],
        "dateModified": row[4],
        "title": title_row[0] if title_row else None,
        "creators": [creator["displayName"] for creator in creators],
    }


def fetch_scalar_metadata(conn: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    cur = conn.cursor()
    row = cur.execute(
        """
        select i.itemID, i.key, i.dateAdded, i.dateModified, i.version, i.synced,
               it.typeName
        from items i
        join itemTypesCombined it on it.itemTypeID = i.itemTypeID
        where i.itemID = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"itemID {item_id} not found")

    return {
        "itemID": row[0],
        "itemKey": row[1],
        "dateAdded": row[2],
        "dateModified": row[3],
        "version": row[4],
        "synced": bool(row[5]),
        "itemType": row[6],
    }


def fetch_fields(conn: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select f.fieldName, v.value
        from itemData d
        join fieldsCombined f on f.fieldID = d.fieldID
        join itemDataValues v on v.valueID = d.valueID
        where d.itemID = ?
        order by f.fieldName
        """,
        (item_id,),
    ).fetchall()

    fields: dict[str, Any] = {}
    for field_name, value in rows:
        if field_name in fields:
            if not isinstance(fields[field_name], list):
                fields[field_name] = [fields[field_name]]
            fields[field_name].append(value)
        else:
            fields[field_name] = value
    return fields


def fetch_creators(conn: sqlite3.Connection, item_id: int) -> list[dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select ct.creatorType, c.firstName, c.lastName, c.fieldMode, ic.orderIndex
        from itemCreators ic
        join creators c on c.creatorID = ic.creatorID
        join creatorTypes ct on ct.creatorTypeID = ic.creatorTypeID
        where ic.itemID = ?
        order by ic.orderIndex
        """,
        (item_id,),
    ).fetchall()
    return [
        {
            "creatorType": row[0],
            "firstName": row[1],
            "lastName": row[2],
            "fieldMode": row[3],
            "orderIndex": row[4],
            "displayName": row[2] if row[3] == 1 else " ".join(part for part in [row[1], row[2]] if part),
        }
        for row in rows
    ]


def fetch_tags(conn: sqlite3.Connection, item_id: int) -> list[dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select t.name, it.type
        from itemTags it
        join tags t on t.tagID = it.tagID
        where it.itemID = ?
        order by lower(t.name)
        """,
        (item_id,),
    ).fetchall()
    return [{"name": row[0], "type": row[1]} for row in rows]


def fetch_notes(conn: sqlite3.Connection, item_id: int) -> list[dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select n.itemID, i.key, n.title, n.note
        from itemNotes n
        join items i on i.itemID = n.itemID
        where n.parentItemID = ?
        order by n.itemID
        """,
        (item_id,),
    ).fetchall()
    return [
        {
            "itemID": row[0],
            "itemKey": row[1],
            "title": row[2],
            "noteHtml": row[3],
            "noteText": strip_html(row[3]),
        }
        for row in rows
    ]


def fetch_annotations(conn: sqlite3.Connection, item_id: int) -> list[dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select a.itemID, i.key, a.type, a.authorName, a.text, a.comment, a.color,
               a.pageLabel, a.sortIndex, a.position, a.isExternal
        from itemAnnotations a
        join items i on i.itemID = a.itemID
        where a.parentItemID in (
            select itemID from itemAttachments where parentItemID = ?
        )
        order by a.pageLabel, a.sortIndex
        """,
        (item_id,),
    ).fetchall()
    return [
        {
            "itemID": row[0],
            "itemKey": row[1],
            "type": row[2],
            "authorName": row[3],
            "text": row[4],
            "comment": row[5],
            "color": row[6],
            "pageLabel": row[7],
            "sortIndex": row[8],
            "position": row[9],
            "isExternal": bool(row[10]),
        }
        for row in rows
    ]


def fetch_collection_paths(conn: sqlite3.Connection, item_id: int) -> list[list[str]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select c.collectionID, c.collectionName, c.parentCollectionID
        from collectionItems ci
        join collections c on c.collectionID = ci.collectionID
        where ci.itemID = ?
        order by c.collectionID
        """,
        (item_id,),
    ).fetchall()
    if not rows:
        return []

    collection_map = {
        row[0]: {"name": row[1], "parent": row[2]}
        for row in cur.execute(
            "select collectionID, collectionName, parentCollectionID from collections"
        ).fetchall()
    }

    paths: list[list[str]] = []
    for collection_id, collection_name, parent_collection_id in rows:
        parts = [collection_name]
        parent_id = parent_collection_id
        while parent_id is not None and parent_id in collection_map:
            parent = collection_map[parent_id]
            parts.append(parent["name"])
            parent_id = parent["parent"]
        paths.append(list(reversed(parts)))
    return sorted(paths, key=lambda path: (len(path), path))


def resolve_attachment_path(zotero_dir: Path, attachment_key: str, stored_path: str | None) -> str | None:
    if not stored_path:
        return None
    if stored_path.startswith("storage:"):
        filename = stored_path.split(":", 1)[1]
        return str(zotero_dir / "storage" / attachment_key / filename)
    return stored_path


def read_text_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def fetch_attachments(
    conn: sqlite3.Connection,
    zotero_dir: Path,
    item_id: int,
    include_fulltext: bool,
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        """
        select ia.itemID, i.key, ia.path, ia.contentType, ia.linkMode,
               ia.syncState, ia.storageModTime, ia.storageHash,
               fi.indexedPages, fi.totalPages, fi.indexedChars, fi.totalChars
        from itemAttachments ia
        join items i on i.itemID = ia.itemID
        left join fulltextItems fi on fi.itemID = ia.itemID
        where ia.parentItemID = ?
        order by ia.itemID
        """,
        (item_id,),
    ).fetchall()

    attachments = []
    for row in rows:
        attachment_key = row[1]
        attachment_path = resolve_attachment_path(zotero_dir, attachment_key, row[2])
        cache_path = zotero_dir / "storage" / attachment_key / ".zotero-ft-cache"
        entry: dict[str, Any] = {
            "itemID": row[0],
            "itemKey": attachment_key,
            "path": row[2],
            "resolvedPath": attachment_path,
            "contentType": row[3],
            "linkMode": row[4],
            "syncState": row[5],
            "storageModTime": row[6],
            "storageHash": row[7],
            "fulltextIndexedPages": row[8],
            "fulltextTotalPages": row[9],
            "fulltextIndexedChars": row[10],
            "fulltextTotalChars": row[11],
            "fulltextCachePath": str(cache_path) if cache_path.exists() else None,
        }
        if include_fulltext:
            entry["fulltextText"] = read_text_file(cache_path)
        attachments.append(entry)
    return attachments


def extract_item(conn: sqlite3.Connection, zotero_dir: Path, item_id: int, include_fulltext: bool) -> dict[str, Any]:
    result = fetch_scalar_metadata(conn, item_id)
    result["fields"] = fetch_fields(conn, item_id)
    result["creators"] = fetch_creators(conn, item_id)
    result["tags"] = fetch_tags(conn, item_id)
    result["collections"] = fetch_collection_paths(conn, item_id)
    result["notes"] = fetch_notes(conn, item_id)
    result["annotations"] = fetch_annotations(conn, item_id)
    result["attachments"] = fetch_attachments(conn, zotero_dir, item_id, include_fulltext)
    result["citationCount"] = None
    result["citationCountSource"] = "Zotero local sqlite does not store citation counts by default"
    return result


def main() -> None:
    args = parse_args()
    db_path = choose_db_path(args.db)
    zotero_dir = db_path.parent
    conn = open_db(db_path)
    try:
        item_ids = fetch_item_ids(conn, args)
        if not item_ids:
            raise SystemExit("No matching items found")

        payload: Any
        if args.find:
            payload = [fetch_item_summary(conn, item_id) for item_id in item_ids]
        elif len(item_ids) == 1:
            payload = extract_item(conn, zotero_dir, item_ids[0], args.include_fulltext)
        else:
            payload = [extract_item(conn, zotero_dir, item_id, args.include_fulltext) for item_id in item_ids]

        print(
            json.dumps(
                {
                    "dbPath": str(db_path),
                    "resultCount": len(item_ids),
                    "items": payload if isinstance(payload, list) else [payload],
                },
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
