# SKILL — Lint

## When to use
When asked to do a health check on the wiki.

## Steps

### 1. Run automated check
```bash
python3 "0 - System/scripts/validate.py"
```
The script checks on its own: missing frontmatter, broken links, outdated `last_compiled`, and required fields.
It writes a full report to `7 - Wikipedia/validation_report.md` and prints an error/warning summary.

### 2. Check sources (wiki_sources)
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Identifies `wiki_sources` pointing to files/URLs that don't exist → `7 - Wikipedia/wiki_sources_issues.md`.
Note: broken source links originating from external URLs or YouTube transcripts are acceptable — not a bug to fix.

### 3. Missing concept candidates (optional)
```bash
python3 "0 - System/scripts/subject_candidates.py" 3
```
Shows concepts linked from ≥3 pages that could become a topic in SCHEMA. **Display only — Ofer decides.**

### 4. Show summary and ask
Show the error/warning counts from the reports, then ask: "Would you like me to handle each of these?"
