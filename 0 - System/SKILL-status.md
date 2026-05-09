# SKILL — Status

## When to use
When asked to check the wiki's status — what's compiled, what's pending, what changed.

## Steps

### 1. Read manifest
Read `7 - Wikipedia/.manifest.json`

### 2. Scan raw/
List all files in `7 - Wikipedia/raw/`

### 3. Calculate delta
- Files already compiled ← in the manifest
- New files not yet compiled ← in raw/ but not in the manifest
- Files changed since compile ← modified date > ingest date in manifest

### 4. Show report
```
📚 Total wiki pages: X
✅ Compiled sources: X
🆕 Pending compilation: X
🔄 Changed since compile: X
📅 Last compiled: YYYY-MM-DD
```

### 5. Ask
"Do you want me to compile the pending sources?"
