# Obsidian Output Rules

Default vault root:

- read from `.zotero-obsidian-reader.json` when available
- otherwise auto-detect the first Obsidian vault in the workspace and write that path back into `.zotero-obsidian-reader.json`

Default directories:

- use `paper_relative_dir` and `synthesis_relative_dir` from config when present
- otherwise paper notes inherit the Zotero collection path
- otherwise synthesis notes write directly to the vault root

Filename rules:

- use Windows-safe filenames
- prefer `Title_精读笔记.md` for paper notes
- prefer `Topic_综述.md` for synthesis notes

Write behavior:

- create missing directories automatically
- do not overwrite existing files unless explicitly requested
- preserve UTF-8 output
