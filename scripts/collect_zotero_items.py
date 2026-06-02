#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any

from extract_zotero_item import (
    choose_db_path,
    fetch_creators,
    open_db,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Zotero bibliographic items for batch note generation."
    )
    parser.add_argument("--db", type=Path)
    parser.add_argument("--title-contains")
    parser.add_argument("--tag")
    parser.add_argument("--collection-contains")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--include-abstracts", action="store_true")
    args = parser.parse_args()

    if not any([args.title_contains, args.tag, args.collection_contains]):
        parser.error("one of --title-contains, --tag, or --collection-contains is required")

    return args


def fetch_item_ids(conn, title_contains: str | None, tag: str | None, collection_contains: str | None, limit: int) -> list[int]:
    sql = """
        select distinct i.itemID
        from items i
        left join itemData d on d.itemID = i.itemID
        left join fieldsCombined f on f.fieldID = d.fieldID
        left join itemDataValues v on v.valueID = d.valueID
        left join itemTags it on it.itemID = i.itemID
        left join tags t on t.tagID = it.tagID
        left join collectionItems ci on ci.itemID = i.itemID
        left join collections c on c.collectionID = ci.collectionID
        where i.itemID not in (select itemID from itemAttachments)
          and i.itemID not in (select itemID from itemNotes)
          and i.itemID not in (select itemID from itemAnnotations)
    """

    conditions = []
    params: list[Any] = []

    if title_contains:
        conditions.append("(f.fieldName = 'title' and lower(v.value) like ?)")
        params.append(f"%{title_contains.lower()}%")
    if tag:
        conditions.append("lower(t.name) like ?")
        params.append(f"%{tag.lower()}%")
    if collection_contains:
        conditions.append("lower(c.collectionName) like ?")
        params.append(f"%{collection_contains.lower()}%")

    sql += " and (" + " or ".join(conditions) + ")"
    sql += " order by i.itemID limit ?"
    params.append(limit)
    cur = conn.cursor()
    rows = cur.execute(sql, params).fetchall()
    return [row[0] for row in rows]


def fetch_title(conn, item_id: int) -> str | None:
    cur = conn.cursor()
    row = cur.execute(
        """
        select v.value
        from itemData d
        join fieldsCombined f on f.fieldID = d.fieldID
        join itemDataValues v on v.valueID = d.valueID
        where d.itemID = ? and f.fieldName = 'title'
        """,
        (item_id,),
    ).fetchone()
    return row[0] if row else None


def fetch_field(conn, item_id: int, field_name: str) -> str | None:
    cur = conn.cursor()
    row = cur.execute(
        """
        select v.value
        from itemData d
        join fieldsCombined f on f.fieldID = d.fieldID
        join itemDataValues v on v.valueID = d.valueID
        where d.itemID = ? and f.fieldName = ?
        """,
        (item_id, field_name),
    ).fetchone()
    return row[0] if row else None


def fetch_item_key_and_type(conn, item_id: int) -> tuple[str, str]:
    cur = conn.cursor()
    row = cur.execute(
        """
        select i.key, it.typeName
        from items i
        join itemTypesCombined it on it.itemTypeID = i.itemTypeID
        where i.itemID = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"itemID {item_id} not found")
    return row[0], row[1]


def main() -> None:
    args = parse_args()
    db_path = choose_db_path(args.db)
    conn = open_db(db_path)
    try:
        item_ids = fetch_item_ids(
            conn,
            title_contains=args.title_contains,
            tag=args.tag,
            collection_contains=args.collection_contains,
            limit=args.limit,
        )
        items = []
        for item_id in item_ids:
            item_key, item_type = fetch_item_key_and_type(conn, item_id)
            creators = [creator["displayName"] for creator in fetch_creators(conn, item_id)]
            item = {
                "itemID": item_id,
                "itemKey": item_key,
                "itemType": item_type,
                "title": fetch_title(conn, item_id),
                "creators": creators,
            }
            if args.include_abstracts:
                item["abstractNote"] = fetch_field(conn, item_id, "abstractNote")
            items.append(item)

        print(
            json.dumps(
                {
                    "dbPath": str(db_path),
                    "resultCount": len(items),
                    "items": items,
                },
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
