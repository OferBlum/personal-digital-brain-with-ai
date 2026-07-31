---
name: vault-search
description: "Semantic search across the vault by meaning rather than by keyword — crosses languages and reaches notes and topics too."
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [search, semantic]
    category: knowledge
---

# Vault Search

> Privacy: never touch `3 - Journal` or any file with `private: true`. The working directory must be the vault root.

## When to Use
When you need to find something in the vault **by meaning** rather than by exact word:
"where did I write about…", "what do I have on…", "find me the note that…".
Also when you don't remember the phrasing, or the language you wrote it in.

This is also the engine behind step 2 of `SKILL-query` — there it is the entry point
for every question.

## Why it exists
All the other search in the vault is lexical: `grep`, exact title matching in
`autolink`, and trigrams over the graph labels. None of them knows that a word and
its translation are the same concept, and none of them will find a page written in
one language from a question asked in another. A vault that mixes languages — with
technical terms in English in the middle of a sentence — is exactly the case that
falls through.

## Usage

```bash
python3 "0 - System/scripts/vsearch.py" "question or description"
python3 "0 - System/scripts/vsearch.py" "question" --k 5
python3 "0 - System/scripts/vsearch.py" "question" --folder "2 - Notes"
python3 "0 - System/scripts/vsearch.py" "question" --files    # paths only
python3 "0 - System/scripts/vsearch.py" "question" --json     # for programmatic use
```

Each result returns: similarity score, path, sub-heading, `background`, and a text snippet.

## After the search
1. **Read only down to the drop in scores** — in practice 1–3 files, even with `--k 8`.
   Below the drop it's noise. (0.35 is a floor, not the decision rule.)
2. **The returned snippet is usually enough.** Read the full page only when a detail is missing.
3. **No scanner of your own after `vsearch`** — no grep over the vault, no scanning script.
   If it wasn't found, it probably doesn't exist.
4. Cite as `[[page-name]]`.
5. State the confidence level: a page with `verified` was reviewed by a human; a page with
   only `generated_by: process:ingest` was compiled automatically and is unverified.
6. Answer in the language the question was asked in.

## Maintenance
The index **does not update itself**. After adding or editing notes, the everyday command is:

```bash
bash "0 - System/scripts/reindex.sh"      # or the /reindex slash command
```

It prints which files were added (`+`), changed (`~`) or deleted (`-`), then indexes only
those. When there is nothing to update it says so and does nothing.

Underneath, the direct calls:

```bash
python3 "0 - System/scripts/embed_index.py"            # incremental — only what changed
python3 "0 - System/scripts/embed_index.py" --changes  # which files are behind (one path per line)
python3 "0 - System/scripts/embed_index.py" --check    # one summary line (for hooks)
python3 "0 - System/scripts/embed_index.py" --status   # index state
python3 "0 - System/scripts/embed_index.py" --rebuild  # from scratch
```

The index is derived from the markdown — you can delete `vector-out/` and rebuild at any time.

## Privacy
The index contains **only** `7 - Wikipedia/` (without raw/), `2 - Notes/` and `1 - Topics/`,
and only files that are not `private: true`. The journal is outside the allowlist
*structurally* — it isn't filtered out, it is simply never read. To verify:

```bash
python3 "0 - System/scripts/embed_index.py" --audit
```

The check fails (exit 1) if a private file, a journal file, or anything outside the three
folders reached the index. It runs automatically at the end of every build.

`vector-out/` is gitignored: its `meta.json` records every indexed file path, which makes
it a list of your note titles.
