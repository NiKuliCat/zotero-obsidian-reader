# Zotero Query Rules

Prefer exact identifiers when available:

1. item key
2. exact title
3. title contains
4. tag
5. collection name

If a query returns multiple plausible papers:

- list candidates with `itemKey`, title, and creators
- ask for disambiguation only when needed

For local fallback scripts:

- `extract_zotero_item.py --find` is the fastest way to discover candidate item keys
- `collect_zotero_items.py` is the default batch locator
- the Zotero root is read from `.zotero-obsidian-reader.json` when present, otherwise auto-discovered from the workspace
- auto-discovery uses Zotero-like directory structure, not a hardcoded folder name
