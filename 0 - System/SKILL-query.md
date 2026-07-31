# SKILL — Query

## When to use
When asked to answer a question from the vault — **the whole vault**, not just the wiki.

## Steps

### 1. Read the hot cache
Read `7 - Wikipedia/_cache.md` for context from the last session.
(Maintenance: if the cache has grown, `python3 "0 - System/scripts/trim_cache.py" 2` keeps
the 2 most recent sessions and archives the rest.)

### 2. Semantic search — the entry point
```bash
python3 "0 - System/scripts/vsearch.py" "<the user's question>" --k 8
```
Returns the most relevant passages by **meaning**, with path, sub-heading and score.

Why this comes before index.md:
- `index.md` covers only `7 - Wikipedia/`. Semantic search also reaches `2 - Notes/` and
  `1 - Topics/` — which this skill simply never got to before.
- It crosses languages: a question in one language finds a page written in another.
- It is cheaper: read 3–5 focused pages instead of loading a whole index table for every question.

Useful flags: `--folder "2 - Notes"` to narrow, `--files` for paths only, `--json` for processing.

> If `vsearch` reports "No semantic index" — run `python3 "0 - System/scripts/embed_index.py"` and continue.
> If the results are weak (scores < 0.35) — fall back to scanning `7 - Wikipedia/index.md`.

### 3. Read the relevant pages
Read **only down to the drop in scores** — in practice 1–3 files, even with `--k 8`.
Below the drop it's noise. The returned snippet is usually enough; read a full page only
when a detail is missing.
**No scanner of your own after `vsearch`** — no grep over the vault, no scanning script.

### 4. Synthesize the answer
- Answer in the language the question was asked in
- Cite specific pages as sources: `[[page-name]]`
- Note if information is marked `inferred` or `ambiguous`
- **State the confidence level**: a page with `verified` was checked and approved by a human;
  a page with only `generated_by: process:ingest` was compiled automatically and nobody has
  verified it.
- The ideas in `2 - Notes/` and `1 - Topics/` are the user's own — cite them, don't rephrase
  them as if they were external knowledge.

### 5. Live data (if relevant)
If the question needs current information the wiki cannot provide:
- news / current information → Playwright: navigate to a relevant site

### 6. Offer to save
If the answer is useful and isn't in the wiki yet — offer:
> "Want me to save this as a new wiki page?"

If yes — create a page in `7 - Wikipedia/` with `provenance: inferred`
