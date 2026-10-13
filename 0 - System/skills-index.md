---
type: note
subject:
tags:
  - ai
background: The vault's skill catalog + each skill's trigger — single source of truth for skill registration
private: false
created: 2026-07-08
generated_by: human:me
generated_at: 2026-07-08
---

# skills-index.md — The Skill Catalog

> A Layer 2 core file of [[AIOS]]. Single source of truth for the skill list. The skills themselves (`0 - System/SKILL-*.md`, plus the standalone `wiki-librarian` skill in `0 - System/hermes-skills/knowledge/`) are **lazy-loaded** — only when the request matches (see [[AGENTS]]). When a skill is ported to Hermes, that's the format (SKILL.md) and the source stays here.

## Knowledge & wiki maintenance

| Skill | When to trigger | Role |
|-------|-----------------|------|
| `wiki-librarian` | "compile…", "what do I know about…", "check the wiki", "organize these files" | One skill for the source-summary wiki and scoped file work; routes each task to one file in its `references/` (ingest, resolve, crosslink, query, audit, files) |
| `SKILL-vsearch` | "where did I write about…" / half-remembered phrasing | Meaning-based search across the whole vault; crosses languages; reaches notes and topics |

## Maintenance

| Skill | When to trigger | Role |
|-------|-----------------|------|
| `SKILL-publish` | "update the public repo" / "publish" | Port the system layer to the public mirror: drift report → mechanical port → leak audit → stage. Claude Code only — never exported to Hermes |

## Personal skills live elsewhere

Domain skills (investing, nutrition, styling, journal summarization) are **deliberately not in
this repo**. They are personal by nature, and each lives as its own standalone repo — see
*Companion Repos* in the README. The pattern is what transfers, not the content: one
`SKILL-*.md` file and one row in this table — `AGENTS.md` points every agent here.

## Notes

- MCP routing stays on the Claude Code side; Hermes reads outputs from the vault.
- Never invent subjects or tags not in SCHEMA. If none fits → leave empty.
- Links: [[me]] · [[vault-map]] · [[AGENTS]]
