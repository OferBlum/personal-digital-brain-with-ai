# SKILL — Lint

## When to use
When asked to run a health check on the wiki.

## Steps

### 1. Run the automatic validation
```bash
python3 "0 - System/scripts/validate.py"
```
The script checks on its own: missing frontmatter, broken links, stale `last_compiled`, and required fields.
It writes a full report to `7 - Wikipedia/validation_report.md` and prints an errors/warnings summary.

### 2. Check sources (wiki_sources)
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Finds `wiki_sources` entries pointing to files/URLs that don't exist → `7 - Wikipedia/wiki_sources_issues.md`.
Note: broken source links that come from an external URL or a YouTube transcript are acceptable — not a bug to fix.

### 3. Candidates for missing concepts (optional)
```bash
python3 "0 - System/scripts/subject_candidates.py" 3
```
Shows concepts linked from ≥3 pages that could become a subject in SCHEMA. **Display only — the user decides.**

### 4. Show a summary and ask
Show the error/warning counts from the reports, then ask: "Want me to handle any of them?"
