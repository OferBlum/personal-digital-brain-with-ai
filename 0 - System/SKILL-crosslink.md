# SKILL — Cross-Link

## When to use
After every ingest — to connect pages that mention each other but lack a wikilink.

## Steps

### 1. Preview (dry-run)
```bash
python3 "0 - System/scripts/autolink.py"
```
The script scans all pages in `7 - Wikipedia/`, identifies mentions of page titles that are not yet linked,
and prints how many links will be added and in which pages. **Does not write anything.**

### 2. Apply
After reviewing the preview and it looks reasonable:
```bash
python3 "0 - System/scripts/autolink.py" --apply
```
The script backs up to `.backup/` then writes the links.

### 3. Update log.md
```bash
python3 "0 - System/scripts/append_log.py" --op crosslink --title "Auto-link" --pages "page-a,page-b"
```
