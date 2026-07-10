# SKILL — Status

## When to use
When asked to show the wiki's state — what was compiled, what's pending, what changed.

## Steps

### 1. Refresh and build the manifest
```bash
python3 "0 - System/scripts/build_manifest.py"
```
The script scans the sources and the pages' frontmatter, and prints the list of all compiled sources (date → pages).
It also updates the canonical `7 - Wikipedia/.manifest.json`.

### 2. Check source health
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Shows how many sources are valid and how many have problems (missing targets etc.).

### 3. Show a report
Summarize from the output:
```
📚 Total wiki pages: X
✅ Compiled sources: X
⚠️ Sources with problems: X
📅 Last compile: YYYY-MM-DD
```
New files in `raw/` that don't appear in the manifest output are candidates for compilation.

### 4. Ask
"Want me to compile the pending sources?"
