---
name: zotero-obsidian-reader
description: Use when the user wants Codex to read Zotero items, extract metadata/fulltext/annotations, deeply read one paper or a batch of papers, and generate Obsidian Markdown notes or synthesis notes inside the local vault.
---

# Zotero Obsidian Reader

Use this skill for Zotero-driven research workflows in this workspace.

Default workspace assumptions:

- Zotero data is discovered dynamically
- The Obsidian vault is discovered dynamically

## Zotero data discovery

This skill must not hardcode the Zotero data directory.

Priority order:

1. if `.zotero-obsidian-reader.json` exists and contains `zotero_dir`, use it
2. otherwise prefer a workspace directory that contains `zotero.sqlite` or `zotero.sqlite.bak`
3. when multiple candidates exist, prefer the one that looks most like a complete Zotero data root, such as directories containing `storage`, `translators`, or `better-bibtex`
4. after auto-discovery, write the discovered Zotero root back into `.zotero-obsidian-reader.json`

## Vault discovery

This skill must not hardcode the Obsidian output path.

Priority order:

1. if `.zotero-obsidian-reader.json` exists and contains `vault_dir`, use it
2. otherwise search the workspace for directories containing `.obsidian`
3. after auto-discovery, write the discovered vault path into `.zotero-obsidian-reader.json`
4. if multiple vaults are found, prefer a vault under a `note` directory and then the shallowest path

If no paper directory config exists, default single-paper notes should inherit the first Zotero collection path for that item. If the item has no collection, fall back to the vault root.

After the first successful auto-discovery and config bootstrap, explicitly tell the user what was detected. Use concise Chinese wording such as:

`自动识别到当前的 Obsidian 仓库位置：...`

and also report the detected Zotero data root if it was auto-configured in the same flow.

If the user asks for:

- a single paper note
- batch note generation for a collection/tag/topic
- a synthesis note across multiple papers

then use this skill.

## Source priority

1. If a Zotero MCP tool is available in the current session, use it first for search, metadata, notes, annotations, and fulltext.
2. If Zotero MCP is unavailable, incomplete, or blocked, use the bundled local scripts in `scripts/`.
3. Keep outputs deterministic: write Markdown notes into the Obsidian vault rather than returning only prose when the user clearly wants notes generated.

## Modes

Choose one mode before doing detailed work:

- `single`: one paper -> one detailed Obsidian note
- `batch`: many papers -> one note per paper
- `synthesis`: many papers -> one cross-paper synthesis note

Read the matching reference file before heavy work:

- `references/mode-single.md`
- `references/mode-batch.md`
- `references/mode-synthesis.md`

Also read:

- `references/zotero-query-rules.md` when locating items
- `references/obsidian-output-rules.md` before writing notes
- `references/reading-rubric.md` before generating analytical sections
- `references/frontmatter-rules.md` before filling analytical frontmatter fields

## Workflow

### 0. Run workspace preflight first

Before locating any paper, fetching any Zotero content, or writing any note, run a workspace preflight.

Use:

- `scripts/preflight_workspace.py`

The required behavior is:

1. first load local workspace config
2. auto-detect and persist `vault_dir` / `zotero_dir` if missing
3. if the paths were auto-detected for the first time, tell the user the detected paths immediately
4. check whether the research profile already exists
5. if `research_domain` is missing, stop before reading papers, stop before writing notes, and ask the user for their research field first
6. only after the research profile has been saved may the workflow continue into Zotero item lookup

This preflight is mandatory for:

- single paper notes
- batch note generation
- synthesis notes

### 1. Locate target items

Prefer this order:

1. exact item key
2. exact title
3. title contains
4. tag / collection / topic search

If a query is ambiguous, list candidates first instead of guessing.

For local fallback:

- `scripts/extract_zotero_item.py` for one item
- `scripts/collect_zotero_items.py` for many items

### 2. Fetch research material

Collect as much as is available:

- bibliographic metadata
- abstract
- creators
- tags
- child notes
- annotations
- attachment list
- fulltext cache when available

### 2.5. Respect the preflight gate

At this stage, the research profile should already have been checked in step 0.

Do not defer the research-profile check until after papers have been fetched.
If the profile is missing, the workflow should already have paused before any serious reading or note generation began.

### 3. Analyze

Apply the rubric in `references/reading-rubric.md`.

Before filling analytical frontmatter fields in the paper note template, apply `references/frontmatter-rules.md`.

For single-paper notes, extract:

- problem
- method
- data / experiment setup
- main findings
- limitations
- relevance to the user's research

For synthesis notes, compare:

- research questions
- methods
- datasets or scenarios
- recurring strengths
- recurring limitations
- gaps and opportunities

### 4. Render Markdown

Use templates from `assets/templates/`:

- `paper-note.md`
- `paper-note-brief.md`
- `synthesis-note.md`

Render with:

- `scripts/render_paper_note.py`
- `scripts/render_synthesis_note.py`

### 5. Write to Obsidian

Use `scripts/write_obsidian_note.py` helpers or equivalent logic.

Default destinations:

- if config provides `paper_relative_dir` or `synthesis_relative_dir`, use them
- otherwise single-paper notes inherit the Zotero collection path
- otherwise synthesis notes write into the discovered vault root

## Script map

- `scripts/extract_zotero_item.py`: local Zotero item extractor
- `scripts/collect_zotero_items.py`: batch locator for title/tag/collection workflows
- `scripts/render_paper_note.py`: render one paper note from extracted JSON
- `scripts/render_synthesis_note.py`: render one synthesis note from many extracted items
- `scripts/preflight_workspace.py`: mandatory upfront workspace and research-profile check
- `scripts/set_research_profile.py`: persist the user's research domain, focus, and keywords
- `scripts/normalize_filename.py`: Windows-safe filenames
- `scripts/write_obsidian_note.py`: output path and write helpers

## Important behavior

- Prefer writing note files when the user asks to "generate notes".
- Do not overwrite existing notes unless the user asked for regeneration or overwrite.
- If the user asks for "deep reading", do not stop at metadata extraction. Generate analytical sections using the rubric.
- If Zotero metadata is sparse, still produce a note shell with clear "needs manual review" markers rather than failing silently.
- Do not start serious paper reading or note generation when the research profile is missing. Run the preflight first, pause immediately, ask the user for research-profile information, save it, and only then continue.
- When vault or Zotero paths are auto-detected for the first time, report the final detected configuration to the user instead of silently proceeding.
