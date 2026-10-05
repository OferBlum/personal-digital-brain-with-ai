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

1. Never enter/read/mention a file inside `3 - Journal` (the journal + every private file).
2. Never **map** it either: no listing, globbing or recursing into it. Scans start at a content
   folder; scripts use `privacy_guard.iter_vault_files()`, which prunes it before descending.

The boundary is the folder, and only the folder — the old `private: true` flag is retired and
grants nothing. Enforced in code by `0 - System/scripts/privacy_guard.py` (one implementation,
one thin wrapper per runtime).

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
- `0 - System/_cache.md` — cache from the last session. Read it at session start (the `_` prefix means "generated", not "off-limits").

## Retrieval index (Layer 2, additional)

One derived index sits on top of the markdown — **in addition** to the wiki's
index.md/manifest, not instead of it. It reads only a positive folder allowlist
(`safe_input.py`), so the private folder is never reached.

| Index | Question it answers | Built by |
|---|---|---|
| `vector-out/` | **what things mean** — meaning-based search that crosses languages and reaches `2 - Notes/` and `1 - Topics/`, not just the wiki | `embed_index.py` (bge-m3 via local Ollama) |

It is **gitignored and never published**: it records real note paths, so the index files are
effectively a list of your private note titles. It is fully regenerable — the markdown is the
source of truth. (The graphify knowledge graph that used to sit here was removed.)

Everyday commands: `bash "0 - System/scripts/reindex.sh"` (incremental) and
`bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question"`.
