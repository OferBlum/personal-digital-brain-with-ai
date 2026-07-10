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
3. A filename starting with `_` → skip without opening.
4. Private subjects in `1 - Topics/` (flagged with `private:`) — respect the flag.

## Where to write what (output routing)

- **Compiling an external source** → `7 - Wikipedia/` (+ update index.md, log.md, .manifest.json).
- **A summary the user explicitly requested** → `2 - Notes/`.
- **Quick capture from Hermes/Telegram** → an inbox/capture note in `2 - Notes/` (not the journal, not directly the wiki).
- Every new file → full frontmatter per the conventions in [[CLAUDE]]; subjects and tags only from SCHEMA, otherwise leave empty.

## The wiki's navigation files

- `7 - Wikipedia/index.md` — master catalog of the wiki pages.
- `7 - Wikipedia/log.md` — append-only history.
- `7 - Wikipedia/.manifest.json` — every source that was compiled.
- `7 - Wikipedia/_cache.md` — cache from the last session (starts with `_` → read only via hooks at session start).

## Retrieval index (Layer 2, additional)

Graphify builds a local graph index of the vault (excluding `3 - Journal` and `private: true`) in its own separate files — **in addition** to the wiki's index.md/manifest, not instead of them. Used for smart retrieval across a large vault.
