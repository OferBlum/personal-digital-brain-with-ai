# SKILL — Query

## When to use
When asked to answer a question based on the wiki.

## Steps

### 1. Read the hot cache
Read `7 - Wikipedia/_cache.md` for context from the last session.
(Maintenance: if the cache has grown, `python3 "0 - System/scripts/trim_cache.py" 2` keeps the 2 most recent sessions and archives the rest.)

### 2. Read index.md
Scan `7 - Wikipedia/index.md` and find pages relevant to the question.

### 3. Read the relevant pages
Read the pages you identified — no more than needed.

### 4. Synthesize an answer
- Answer in the language the question was asked in
- Cite specific pages as sources: `[[page-name]]`
- Note when information is marked `inferred` or `ambiguous`

### 5. Live data (if relevant)
If the question needs current data the wiki can't provide:
- News / current information → Playwright: navigate to a relevant site

### 6. Offer to save
If the answer is useful and doesn't exist in the wiki yet — offer:
> "Want me to save this as a new wiki page?"

If yes — create a page in `7 - Wikipedia/` with `provenance: inferred`
