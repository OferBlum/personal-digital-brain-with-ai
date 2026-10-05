# SKILL — Resolve

## When to Use
After every ingest — to update existing pages in light of the new information.

## Procedure

### 1. Find related pages
Read `7 - Wikipedia/index.md` and find pages related to the topic just compiled.

### 2. For each related page — check (human judgment)
- Does the new information **contradict** existing information?
  - If yes — add a note on the page: `> ⚠️ Contradiction: [new source] claims X while [old source] claims Y`
  - Set provenance to `ambiguous`
- Does the new information **reinforce** existing information?
  - If yes — update the page and add the new source to `wiki_sources`
- Does the new information **add to** existing information?
  - If yes — add a new section to the page

### 3. Update last_compiled
On every page you touched — set `last_compiled` to today's date.

### 4. Log and validate (scripts)
```bash
python3 "0 - System/scripts/append_log.py" --op resolve --title "Update related pages" --pages "Page A,Page B"
python3 "0 - System/scripts/validate.py"          # confirm no links broke, and catch provenance: ambiguous
python3 "0 - System/scripts/wiki_sources_report.py"   # if you added sources — check they resolve
```

## Output
Respond in the user's language.
