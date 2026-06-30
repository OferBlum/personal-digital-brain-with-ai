# SKILL — Query

## When to use
When asked to answer a question based on the wiki.

## Steps

### 1. Read hot cache
Read `7 - Wikipedia/_cache.md` for context from the last session.
(Maintenance: if the cache has grown large, `python3 "0 - System/scripts/trim_cache.py" 2` keeps the last 2 sessions and archives the rest.)

### 2. Read index.md
Scan `7 - Wikipedia/index.md` and find pages relevant to the question.

### 3. Read relevant pages
Read the pages you identified — no more than what is necessary.

### 4. Synthesize an answer
- Answer in the language the question was asked
- Cite specific pages as sources: `[[page-name]]`
- Note if information is marked as `inferred` or `ambiguous`

### 5. Live data (if relevant)
If the question requires an up-to-date figure the wiki cannot provide:
- Question about news / current information → Playwright: navigate to a relevant site

### 6. Offer to save
If the answer is helpful and doesn't exist in the wiki yet — offer:
> "Would you like me to save this as a new wiki page?"

If yes — create a page in `7 - Wikipedia/` with `provenance: inferred`
