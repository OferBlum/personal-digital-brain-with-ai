---
subject:
tags:
background: Vault navigation map — what's in each folder, what's gated, and where to write what
private: false
created: 2026-07-08
---

# vault-map.md — The Vault Map

> A Layer 2 core file of [[AIOS]]. Lets any AI agent navigate the vault without scanning everything (token savings). Updated when the vault structure or priorities change.

## General — read first

User identity: [[me]]. Full working rules: [[CLAUDE]]. Skill catalog: [[skills-index]].

## Folder map

| Folder | Contents | Permission |
|--------|----------|------------|
| `0 - System/` | config, SCHEMA, skills, scripts, hooks, core files (me/vault-map/skills-index) | Read. **Never modify** config without an explicit request |
| `1 - Topics/` | hub pages for each domain, with dataview | Don't auto-compile into the wiki |
| `2 - Notes/` | the user's notes and ideas, summaries they requested | Their ideas — don't rewrite; requested summaries are saved here |
| `3 - Journal/` | the personal journal (daily notes) | ⛔ **Completely out of bounds** — no read/write/remember/send |
| `4 - Templates/` | templates for creating notes | Don't modify; use as the base for new notes |
| `5 - Tables/` | `.base` (dataview) files per subject | Don't modify |
| `6 - Images/` | image assets | Don't modify |
| `7 - Wikipedia/` | the compiled wiki (pages you write and maintain) | Write/maintain per SKILL-ingest/resolve |
| `7 - Wikipedia/raw/` | raw sources (transcripts, PDFs) | ⛔ Don't change — immutable source |

## Privacy boundaries (above everything)

1. Never enter/read/mention a file inside `3 - Journal`.
2. A file with `private: true` in frontmatter → treat as non-existent.
3. Private subjects in `1 - Topics/` (flagged with `private:`) — respect the flag.

That is the whole list, and it is enforced in code by `0 - System/scripts/privacy_guard.py`
(one implementation, one thin wrapper per runtime).

A filename starting with `_` is a **generated system file, not a secret**: skip it when
indexing or compiling, but it is readable — `_cache.md` is required reading at session start.

## Where to write what (output routing)

- **Compiling an external source** → `7 - Wikipedia/` (+ update index.md, log.md, .manifest.json).
- **A summary the user explicitly requested** → `2 - Notes/`.
- **Quick capture from Hermes/Telegram** → an inbox/capture note in `2 - Notes/` (not the journal, not directly the wiki).
- Every new file → full frontmatter per the conventions in [[CLAUDE]]; subjects and tags only from SCHEMA, otherwise leave empty.

## The wiki's navigation files

- `7 - Wikipedia/index.md` — master catalog of the wiki pages.
- `7 - Wikipedia/log.md` — append-only history.
- `7 - Wikipedia/.manifest.json` — every source that was compiled.
- `7 - Wikipedia/_cache.md` — cache from the last session. Read it at session start (the `_` prefix means "generated", not "off-limits").

## Retrieval indexes (Layer 2, additional)

Two derived indexes sit on top of the markdown — **in addition** to the wiki's
index.md/manifest, not instead of them. Both exclude `3 - Journal` and `private: true`.

| Index | Question it answers | Built by |
|---|---|---|
| `graphify-out/` | **how things connect** — a semantic graph of concepts and their edges | `refresh_graph.sh` (Graphify) |
| `vector-out/` | **what things mean** — meaning-based search that crosses languages and reaches `2 - Notes/` and `1 - Topics/`, not just the wiki | `embed_index.py` (bge-m3 via local Ollama) |

Both are **gitignored and never published**: each one records real note paths, so the index
files are effectively a list of your private note titles. Both are fully regenerable — the
markdown is the source of truth.

Everyday commands: `bash "0 - System/scripts/reindex.sh"` (incremental) and
`python3 "0 - System/scripts/vsearch.py" "question"`.
