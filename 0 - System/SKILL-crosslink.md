# SKILL — Cross-Link

## When to use
After every ingest — to connect pages that mention each other but lack a wikilink.

## Steps

### 1. Take the new page
Identify the core concepts and entities in the newly created page.

### 2. Search for mentions
Scan all pages in `7 - Wikipedia/` and look for places where:
- The name of the new page is mentioned but not linked
- Concepts from the new page are mentioned but not linked

### 3. Add wikilinks
Wherever you found a match — turn the text into a `[[wikilink]]`.

### 4. Check reverse
In the new page itself — add wikilinks to existing pages that are mentioned in it.

### 5. Update log.md
`## [YYYY-MM-DD] crosslink | [list of updated pages]`
