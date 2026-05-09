# SKILL — Lint

## When to use
When asked to do a health check on the wiki.

## Steps

### 1. Orphaned pages
Find pages in `7 - Wikipedia/` that have no incoming wikilinks from other pages.

### 2. Broken links
Find `[[wikilinks]]` that point to non-existent pages.

### 3. Outdated information
Find pages where `last_updated` is older than 30 days and their `wiki_sources` have changed.

### 4. Contradictions
Find pages with `provenance: ambiguous` that haven't been resolved yet.

### 5. Missing concepts
Find concepts that are mentioned in pages but don't have their own dedicated page.

### 6. Missing frontmatter
Find pages in `7 - Wikipedia/` that are missing frontmatter fields.

### 7. Report
Show summary:
```
✅ Healthy pages: X
⚠️ Orphaned pages: X
🔗 Broken links: X
📅 Outdated information: X
❓ Missing concepts: X
```

Then ask: "Would you like me to fix each of these?"
