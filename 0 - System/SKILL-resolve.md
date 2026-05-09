# SKILL — Resolve

## When to use
After every ingest — to update existing pages in light of new information.

## Steps

### 1. Find related pages
Read `7 - Wikipedia/index.md` and find pages related to the topic just compiled.

### 2. For each related page — check
- Does the new information **contradict** existing information?
  - If yes — add a note in the page: `> ⚠️ Conflict: [new source] claims X while [old source] claims Y`
  - Update provenance to `ambiguous`
- Does the new information **reinforce** existing information?
  - If yes — update the page and add the new source to `wiki_sources`
- Does the new information **add to** existing information?
  - If yes — add a new section to the page

### 3. Update last_compiled
On every page you touch — update `last_compiled` to today's date.

### 4. Update log.md
`## [YYYY-MM-DD] resolve | [list of updated pages]`
