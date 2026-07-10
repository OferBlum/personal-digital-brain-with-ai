# SKILL — Cross-Link

## When to use
After every ingest, and at session start if the hook reports unlinked mentions — connect pages and notes that mention each other but have no wikilink between them.

## Steps

### 1. Preview (dry-run)
```bash
python3 "0 - System/scripts/autolink.py"
```
The script scans **bidirectionally**: all pages in `7 - Wikipedia/` plus the notes in `2 - Notes/`
(non-private, no `_`), finds unlinked mentions of titles from both corpora,
and prints how many links would be added and in which pages. **Writes nothing.**

⚠️ Name collision (a note and a wiki page with the same name): the wiki page wins — the script
reports the collision and doesn't link the name to the note. Offer to rename the note
(and update existing wikilinks that point to it).

### 2. Apply
After reviewing the preview and it looks right:
```bash
python3 "0 - System/scripts/autolink.py" --apply
```
The script backs up to `.backup/` and then writes the links.

### 3. Update log.md
```bash
python3 "0 - System/scripts/append_log.py" --op crosslink --title "Automatic linking" --pages "Page A,Page B"
```
