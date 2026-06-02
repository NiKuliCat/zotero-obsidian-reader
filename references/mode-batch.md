# Batch Mode

Use batch mode when the user requests a collection, tag, topic, or "all papers under X".

Expected output:

- one note per paper under `论文笔记/Papers/`

Recommended behavior:

- run workspace preflight before locating the batch target
- if the research profile is missing, stop before reading any paper in the batch
- list matches first if the target set is ambiguous
- preserve stable filenames
- skip existing notes unless the user asks for overwrite
- continue on per-paper failure and report failures at the end

For large batches, create momentum:

- produce notes in a deterministic order
- keep progress updates concise
- record which papers were skipped, created, or updated
