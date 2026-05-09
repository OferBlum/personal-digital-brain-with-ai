# SKILL — Ingest

## When to use
When asked to compile new files from `7 - Wikipedia/raw/`

## Steps

### 1. Check manifest
Read `7 - Wikipedia/.manifest.json`.
Skip files already compiled that haven't changed.
Process only new or modified files since the last compilation.

### 2. Read the source
Read the raw file in full.

### 3. Extract information
From the source, extract:
- Core concepts
- Entities (people, companies, tools)
- Key claims and facts
- Open questions

Leave out noise — don't include every detail.

### 4. Write a concept page
Create or update a page in `7 - Wikipedia/` with frontmatter:
```
---
topic: [[]]
tags: [wiki]
private: false
wiki_sources: [[raw/filename]]
provenance: extracted
last_compiled: YYYY-MM-DD
---
```

### 5. Mark provenance
- `extracted` — direct information from the source
- `inferred` — your synthesis
- `ambiguous` — conflicting sources; note the contradiction

### 6. Update index.md
Add a row to the table in `7 - Wikipedia/index.md`

### 7. Update manifest
Add to `7 - Wikipedia/.manifest.json`:
```json
{
  "path": "7 - Wikipedia/raw/filename",
  "ingested": "YYYY-MM-DD",
  "pages_produced": ["page-name"]
}
```

### 8. Update log.md
Append a line to `7 - Wikipedia/log.md`:
`## [YYYY-MM-DD] ingest | [source title]`

### 9. Run cross-link
After compilation — read SKILL-crosslink.md and connect the new page to the rest of the wiki.

### 10. Run resolve
Read SKILL-resolve.md and update existing pages that relate to the new information.

## YouTube Queue
When asked to compile videos (e.g. "compile the queue"):
1. Run: `python3 "0 - System/youtube-fetch.py"` — downloads transcripts to raw/
2. Wait for the script to finish
3. Compile the new transcript files from raw/ using the standard ingest steps above
4. The script already moves videos from "Pending" to "Compiled" in youtube_queue.md automatically
