# SKILL — Status

## When to use
When asked to check the wiki's status — what's compiled, what's pending, what changed.

## Steps

### 1. Refresh and build the manifest
```bash
python3 "0 - System/scripts/build_manifest.py"
```
The script scans sources and page frontmatter, and prints a list of all compiled sources (date → pages).
This also updates the canonical `7 - Wikipedia/.manifest.json`.

### 2. Check source health
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Shows how many sources are healthy and how many have issues (missing targets, etc.).

### 3. Show report
Summarize from the output:
```
📚 Total wiki pages: X
✅ Compiled sources: X
⚠️ Sources with issues: X
📅 Last compiled: YYYY-MM-DD
```
New files in `raw/` that don't appear in the manifest output are candidates for compilation.

### 4. Ask
"Do you want me to compile the pending sources?"
