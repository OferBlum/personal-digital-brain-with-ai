# SKILL — Ingest

## When to use
When asked to compile new files from `7 - Wikipedia/raw/`

## Steps

### 0. Fetch the external source (if a URL was provided)
If the request includes a URL (article, web page, documentation):
1. Playwright: `browser_navigate` → URL
2. `browser_snapshot` → pull the full text
3. Save as a file in `7 - Wikipedia/raw/[descriptive-name]-[date].md`
4. Continue from step 2 (read the source)

⚠️ YouTube — use `youtube-fetch.py` (not Playwright) — the script is better for transcripts.

### 1. Check what's pending
```bash
python3 "0 - System/scripts/build_manifest.py"   # refreshes the manifest from current state
```
Process only new files in `raw/` that aren't yet represented by wiki pages. Skip anything already compiled and unchanged.

### 2. Read the source
Read the raw/ file in full.

### 3. Extract information
From the source extract:
- Key concepts
- Entities (people, companies, tools)
- Central claims and facts
- Open questions
Leave the noise out — don't include every detail.

### 4. Write a concept page
- Read `0 - System/SCHEMA.md`
- Create or update a page in `7 - Wikipedia/` with frontmatter:
```
---
subject: "[[subject-name]]"
tags:
  - wiki
background: "Short description of the page — this is what appears in the index"
private: false
wiki_sources:
  - "[[raw/file-name]]"
provenance: extracted
last_compiled: YYYY-MM-DD
---
```

- ⚠️ Mandatory: every wikilink in YAML must be wrapped in double quotes `"[[...]]"`.
- `wiki_sources` with more than one source — a list, not comma-separated.
- Use only subjects/tags that exist in `0 - System/SCHEMA.md`

### 5. Mark provenance
- `extracted` — information taken directly from the source
- `inferred` — your synthesis
- `ambiguous` — contradicting sources; state the contradiction

### 6. Generate derived files (scripts — never by hand)
After all pages are written, run in this order from the vault root:
```bash
python3 "0 - System/scripts/build_manifest.py"   # updates .manifest.json from the pages' frontmatter
python3 "0 - System/scripts/build_index.py"      # updates index.md from the pages' metadata
python3 "0 - System/scripts/fix_frontmatter.py"  # dry-run: frontmatter normalization; add --apply if needed
python3 "0 - System/scripts/append_log.py" --op ingest --title "Source title" --pages "Page-name" --source "raw/file-name"
```
Never edit `.manifest.json`, `index.md` or `log.md` by hand — the scripts handle them and back up to `.backup/`.

### 7. Validate
```bash
python3 "0 - System/scripts/validate.py"
```
Make sure the compile didn't introduce new errors.

### 8. Run cross-link
After compiling — read `SKILL-crosslink.md` (autolink.py) and connect the new page to the rest of the wiki.

### 9. Run resolve
Read `SKILL-resolve.md` and update existing pages related to the new information.

### 10. Check whether the knowledge graph needs a refresh
```bash
python3 "0 - System/scripts/check_graph_staleness.py"
```
If `"refresh_due": true` — offer: "X new sources have accumulated — refresh the graph?". The counter also counts new (non-private) notes in `2 - Notes`, not just wiki sources. If approved, **do it yourself (Claude Code, Pro subscription — not the API, not Ollama)**:
1. Identify the pages compiled since the last build (from log.md / manifest) **plus new/changed notes in `2 - Notes` that aren't in the graph** (compare against `source_file` in graph.json), and read them.
2. Extract with quality: for each page/note — nodes (concepts/entities) and edges to existing nodes. Write JSON per the `merge_nodes.py` schema. **Mandatory — bridge edges between layers:** every note concept related to a topic covered in the wiki gets an edge to a matching wiki node (and vice versa) — notes must not remain closed islands.
3. `python3 "0 - System/scripts/merge_nodes.py" <nodes.json>` — merges into the graph.
4. `graphify cluster-only . --no-label` — re-cluster (free, no LLM).
5. **Map community names yourself** — carry over the existing names by majority vote (`community_name` first) and name new communities. Apply and refresh the report/HTML: `graphify label . --missing-only --backend ollama` (doesn't call the LLM when all names exist).
6. `python3 "0 - System/scripts/check_graph_staleness.py" --mark` — reset the counter. And delete the temporary backup: `rm -rf graphify-out/20*`.

**Never:** graphify with a Claude API backend, and never Ollama for extraction (too weak). The extraction and the names — that's you. `refresh_graph.sh` (Ollama) is only a fallback for a full rebuild when you're not in the loop.

## YouTube Queue
When asked to compile videos (e.g. "compile the videos", "compile the queue"):
1. Run: `python3 "0 - System/youtube-fetch.py"` — downloads transcripts to raw/
2. Wait for the script to finish
3. Compile the new transcript files from raw/ using the standard ingest steps above (including step 6 — generating derived files)
4. The script already moves videos from "Pending" to "Compiled" in youtube_queue.md automatically — as a valid table row at the top of the table, with a `[[⚠️ update page name]]` placeholder in the page column. After compiling, replace the placeholder with a link to the wiki page that was created.
