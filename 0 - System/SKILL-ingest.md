# SKILL — Ingest

## When to use
When asked to compile new files from `7 - Wikipedia/raw/`

## Steps

### 0. Read external source (if URL provided)
If the request includes a URL (article, webpage, documentation):
1. Playwright: `browser_navigate` → URL
2. `browser_snapshot` → extract full text
3. Save as a file in `7 - Wikipedia/raw/[descriptive-name]-[date].md`
4. Continue from step 2 (read the source)

⚠️ YouTube — use `youtube-fetch.py` (not Playwright) — the script is better for transcripts.

### 1. Check what's pending
```bash
python3 "0 - System/scripts/build_manifest.py"   # refreshes the manifest from current state
```
Only process new files in `raw/` not yet represented as wiki pages. Skip what's already compiled and unchanged.

### 2. Read the source
Read the raw/ file in full.

### 3. Extract information
From the source, extract:
- Core concepts
- Entities (people, companies, tools)
- Key claims and facts
- Open questions

Leave out noise — don't include every detail.

### 4. Write a concept page
- Read `0 - System/SCHEMA.md`
- Create or update a page in `7 - Wikipedia/` with frontmatter:
```
---
topic: "[[topic-name]]"
tags:
  - wiki
description: "Brief description of the page — this is what will appear in the index"
private: false
wiki_sources:
  - "[[raw/filename]]"
provenance: extracted
last_compiled: YYYY-MM-DD
---
```

- ⚠️ Required: every wikilink in YAML must be inside double quotes `"[[...]]"`.
- `wiki_sources` with more than one source — list, not comma-separated.
- Only use topics/tags that exist in `0 - System/SCHEMA.md`

### 5. Mark provenance
- `extracted` — direct information from the source
- `inferred` — your synthesis
- `ambiguous` — conflicting sources; note the contradiction

### 6. Generate derived files (scripts — not manually)
After all pages are written, run in this order from the vault root:
```bash
python3 "0 - System/scripts/build_manifest.py"   # updates .manifest.json from page frontmatter
python3 "0 - System/scripts/build_index.py"      # updates index.md from page metadata
python3 "0 - System/scripts/fix_frontmatter.py"  # dry-run: normalize frontmatter; add --apply if needed
python3 "0 - System/scripts/append_log.py" --op ingest --title "Source Title" --pages "page-name" --source "raw/filename"
```
Do not edit `.manifest.json`, `index.md`, or `log.md` manually — the scripts handle them and back up to `.backup/`.

### 7. Validate
```bash
python3 "0 - System/scripts/validate.py"
```
Confirm no new errors were introduced by the compilation.

### 8. Run cross-link
After compilation — read `SKILL-crosslink.md` (autolink.py) and connect the new page to the rest of the wiki.

### 9. Run resolve
Read `SKILL-resolve.md` and update existing pages related to the new information.

## YouTube Queue
When asked to compile videos (e.g. "compile the queue"):
1. Run: `python3 "0 - System/youtube-fetch.py"` — downloads transcripts to raw/
2. Wait for the script to finish
3. Compile the new transcript files from raw/ using the standard ingest steps above (including step 6 — generate derived files)
4. The script already moves videos from "Pending" to "Compiled" in youtube_queue.md automatically
