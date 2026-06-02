# Workflow Overview

This skill supports three output shapes:

- single paper note
- batch paper notes
- synthesis note

The high-level flow is:

1. run workspace preflight and load local config first
2. auto-detect and persist the Obsidian vault / Zotero root when missing
3. if the research profile is missing, stop immediately and ask the user before reading papers
4. locate Zotero targets
5. fetch metadata, notes, annotations, and fulltext
6. analyze with the reading rubric
7. render Markdown
8. write into the Obsidian vault

Use Zotero MCP first when available. Use local scripts as fallback or for deterministic rendering.
The local fallback scripts auto-discover both the Obsidian vault and the Zotero data root and persist them into workspace config.
On the first auto-discovery pass, report the detected vault path and Zotero root back to the user before continuing.
