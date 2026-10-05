---
name: wiki-ingest
description: "Compile an external source (URL/YouTube/raw file) into a wiki page and update the manifest/index/log."
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [wiki, ingest]
    category: knowledge
---

# Wiki Ingest

> Privacy: never read or list the private folder (folder-only rule; Docker does not mount it). The working directory must be the vault root.

## When to Use
When asked to compile new files from `7 - Wikipedia/raw/`.

**Triggers:** "compile…" / a new source (URL, YouTube, raw)

## Procedure

### 0. Read an external source (if a URL was provided)
If the request includes a URL (article, web page, documentation):
1. Playwright: `browser_navigate` → URL
2. `browser_snapshot` → extract the full text
3. Save as a file in `7 - Wikipedia/raw/[descriptive-name]-[date].md`
4. Continue from step 2 (read the source)

⚠️ YouTube — use `youtube-fetch.py` (not Playwright) — the script is better for transcripts.

### 1. Check what's pending
```bash
python3 "0 - System/scripts/build_manifest.py"   # refreshes the manifest from the current state
```
Process only new files in `raw/` that aren't yet represented in wiki pages. Skip anything already
compiled and unchanged.

### 2. Read the source
Read the raw/ file in full.

### 3. Extract information
From the source, extract:
- Key concepts
- Entities (people, companies, tools)
- Key claims and facts
- Open questions
Leave out the noise — don't include every detail.

### 4. Write a concept page
- Read `0 - System/SCHEMA.md`
- Create or update a page in `7 - Wikipedia/` with frontmatter:
```
---
type: wiki-page
subject: "[[subject-name]]"
tags:
  - wiki
background: "Short description of the page — this is what appears in the index"
private: false
wiki_sources:
  - "[[7 - Wikipedia/raw/file-name.md]]"
provenance: extracted
last_compiled: YYYY-MM-DD
generated_by: process:ingest
generated_at: YYYY-MM-DD
---
```

- ⚠️ Required: every wikilink in YAML must be inside double quotes `"[[...]]"`.
- ⚠️ For files under `7 - Wikipedia/raw/`, use the full vault-relative path **and include the real extension** (for example `"[[7 - Wikipedia/raw/video.md]]"`). Extensionless `[[raw/...]]` links may render in Obsidian but are not resolved by `build_manifest.py`, `validate.py`, or `wiki_sources_report.py`.
- **`type` is the only field OKF mandates** — `validate.py` fails without it. For a compiled wiki page
  the value is always `wiki-page` (full values in SCHEMA.md).
- `generated_by` and `generated_at` are **two flat keys**, never a nested map named `generated:` —
  Obsidian Properties renders only flat values, and a map swallows both rows.
  `generated_at` = the same date as `last_compiled`.
- **Don't write `verified`.** Its absence means "unverified", which is the honest state for a page
  compiled automatically that nobody has read yet. The owner marks it later via `okf_verify.py`.
- **Don't write `status`.** The OKF default is `stable`; writing it is noise.
- The order above is the order `vaultlib.dump_fm` produces (`PREFERRED_KEYS`) — keep it so a script
  that rewrites the page doesn't produce a phantom diff.
- `wiki_sources` with more than one source — a list, not comma-separated.
- Use only subjects/tags/type that exist in `0 - System/SCHEMA.md`
- Don't use `- [ ]` — those are reserved for the owner's one-off tasks

### 5. Mark provenance
- `extracted` — information directly from the source
- `inferred` — your synthesis
- `ambiguous` — conflicting sources; state the conflict

### 6. Generate derived files (scripts — not by hand)
After all pages are written, run in this order from the vault root:
```bash
python3 "0 - System/scripts/build_manifest.py"   # updates .manifest.json from the pages' frontmatter
python3 "0 - System/scripts/build_index.py"      # updates index.md from the pages' metadata
python3 "0 - System/scripts/fix_frontmatter.py"  # dry-run: frontmatter normalization; add --apply if needed
python3 "0 - System/scripts/append_log.py" --op ingest --title "Source title" --pages "page-name" --source "raw/file-name"
```
Don't edit `.manifest.json`, `index.md` or `log.md` by hand — the scripts handle them and back up to
`.backup/`.

### 7. Validate
```bash
python3 "0 - System/scripts/validate.py"
```
Confirm the compilation added no new errors.

### 8. Run cross-link
After compiling — read `SKILL-crosslink.md` (autolink.py) and connect the new page to the rest of the wiki.

### 9. Run resolve
Read `SKILL-resolve.md` and update existing pages related to the new information.

### 10. Update the semantic index
```bash
bash "0 - System/scripts/reindex.sh"
```
Incremental, local and free — indexes only what changed, and regenerates `.graphifyignore` first.
A page that was compiled but not indexed simply doesn't exist as far as search is concerned, so this
is the step that closes the compilation.

> **The knowledge graph was removed (2026-07-31).** `graphify-out/` was deleted and it stays
> deleted. There is no more `check_graph_staleness.py`, no graph refresh, and no bridge relations to
> extract — **don't offer to rebuild a graph.** The link between notes and wiki is now maintained two
> ways: `autolink.py` at the file level, and the semantic index which spans both folders anyway.

## YouTube Queue
When asked to compile videos (e.g. "compile the videos", "compile the queue"):
1. Run: `python3 "0 - System/youtube-fetch.py"` — downloads transcripts to raw/
2. Wait for the script to finish
3. Compile the new transcript files from raw/ using the standard ingest steps above (including step 6 —
   generating derived files)
4. The script already moves videos from "Pending" to "Compiled" in youtube_queue.md automatically — as a
   valid table row at the top of the table, with the placeholder `[[⚠️ update page name]]` in the page
   column. After compiling, replace the placeholder with a link to the wiki page that was created.

## Output
Respond in the user's language.
