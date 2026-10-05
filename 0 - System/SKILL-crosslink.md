# SKILL — Cross-Link

## When to Use
After every ingest, and at session start if the hook reports unlinked mentions — to connect pages and
notes that mention each other but have no wikilink between them.

## Procedure

### 1. Preview (dry-run)
```bash
python3 "0 - System/scripts/autolink.py"
```
The script scans **bidirectionally**: all pages in `7 - Wikipedia/` and also the notes in `2 - Notes/`
(non-private, non-`_`), finds unlinked mentions of titles from both corpora, and prints how many links
would be added and in which pages. **Writes nothing.**

⚠️ Name collision (a note and a wiki page with the same name): the wiki page wins — the script reports
the collision and does not link the name to the note. Suggest renaming the note (and updating
existing wikilinks pointing at it).

### 2. Apply
Once you've seen the preview and it looks right:
```bash
python3 "0 - System/scripts/autolink.py" --apply
```
The script backs up to `.backup/` and then writes the links.

### 3. Update log.md
```bash
python3 "0 - System/scripts/append_log.py" --op crosslink --title "Automatic linking" --pages "Page A,Page B"
```

## Output
Respond in the user's language.
