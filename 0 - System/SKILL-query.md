# SKILL — Query

## When to Use
When asked to answer a question from the vault — **the whole vault**, not just the wiki.

## Procedure

### 1. Read the hot cache
Read `0 - System/_cache.md` for context from the last session.
(Maintenance: if the cache has bloated, `python3 "0 - System/scripts/trim_cache.py" 2` keeps the last 2
sessions and archives the rest.)

### 2. Semantic search — the entry point
```bash
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "<the user's question>" --k 8
```
Returns the most relevant passages by **meaning**, with path, sub-heading and score.

Why this comes before index.md:
- `index.md` covers only `7 - Wikipedia/`. Semantic search also reaches `2 - Notes/` and `1 - Topics/` — which this skill simply never reached before.
- It crosses languages: a Hebrew question finds a page written in English and vice versa (e.g. a Hebrew term ↔ `volume` ↔ a Hebrew synonym).
- Cheaper: you read 3–5 targeted pages instead of loading a whole index table for every question.

Useful flags: `--folder "2 - Notes"` to narrow, `--files` for paths only, `--json` for processing.

> If `vsearch` reports a missing index, do not rebuild the real vault automatically.
> Until Day 10's privacy-first gate is complete, report the blocker and use targeted
> filename/lexical lookup in allowed directories instead.
> If the results are weak (scores < 0.35) — fall back to scanning `7 - Wikipedia/index.md`.

### 3. Read the relevant pages
Read **only down to the score cliff** — in practice 1–3 files, even with `--k 8`. Below the cliff is noise.
The returned passage is usually enough; read a full page only when a detail is missing.
**No scanner of your own after `vsearch`** — no grep over the vault, no scan script.

### 4. Synthesize an answer
- Answer in the language the question was asked in
- Cite specific pages as sources: `[[page-name]]`
- Note if information is marked `inferred` or `ambiguous`
- **State the confidence level**: a page with `verified` was reviewed and approved by the owner; a page with
  only `generated_by: process:ingest` was compiled automatically and nobody verified it.
- The ideas in `2 - Notes/` and `1 - Topics/` are the owner's — quote them, don't rephrase them as if they
  were external knowledge.

### 5. Live data (if relevant)
If the question needs current data the wiki can't provide:
- News / current information → Playwright: navigate to a relevant site

### 6. Offer to save
If the answer is useful and doesn't exist in the wiki yet — offer:
> "Want me to save this as a new wiki page?"

If yes — create a page in `7 - Wikipedia/` with `provenance: inferred`
