# SKILL — Status

## When to Use
When asked for the state of the wiki — what's compiled, what's pending, what changed.

**Triggers:** "what's the wiki status?" / "what's pending?"

## Procedure

### 1. Refresh and build the manifest
```bash
python3 "0 - System/scripts/build_manifest.py"
```
The script scans the sources and the pages' frontmatter, and prints the list of every compiled source
(date → pages). It also updates the canonical `7 - Wikipedia/.manifest.json`.

### 2. Check source health
```bash
python3 "0 - System/scripts/wiki_sources_report.py"
```
Shows how many sources resolve and how many have problems (missing targets, etc.).

### 3. Show the report
Respond in the user's language. Summarize from the output:
```
📚 Total wiki pages: X
✅ Compiled sources: X
⚠️ Sources with problems: X
📅 Last compile: YYYY-MM-DD
```
New files in `raw/` that don't appear in the manifest output are candidates for compilation.

### 4. Ask
"Want me to compile the pending sources?"
