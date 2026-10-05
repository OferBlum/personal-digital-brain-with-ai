---
name: wiki-lint
description: "Validate wiki health: frontmatter, broken links, stale pages, missing sources."
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [wiki, lint]
    category: knowledge
---

# Wiki Lint

> Privacy: never read or list the private folder (folder-only rule; Docker does not mount it). The working directory must be the vault root.

## When to Use
When asked to run a health check on the wiki.

**Triggers:** "check health" / "health check"

## Procedure

### 1. Run the automated check
```bash
python3 "0 - System/scripts/validate.py"
```
The script checks on its own: missing frontmatter, broken links, stale `last_compiled`, and required
fields. It writes a full report to `7 - Wikipedia/validation_report.md` and prints an error/warning summary.

### 2. Check sources (wiki_sources)
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Finds `wiki_sources` pointing at files/URLs that don't exist → `7 - Wikipedia/wiki_sources_issues.md`.
Note: broken source links that come from an external URL or a YouTube transcript are expected — not a
bug to fix.

### 3. Candidates for missing concepts (optional)
```bash
python3 "0 - System/scripts/subject_candidates.py" 3
```
Shows concepts linked from ≥3 pages that could become a subject in SCHEMA. **Display only — the user decides.**

### 4. Show a summary and ask
Show the error/warning counts from the reports, then ask: "Want me to handle any of them?"

## Output
Respond in the user's language.
