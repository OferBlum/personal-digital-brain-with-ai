---
subject: "[[Projects]]"
tags:
  - ai
background: System usage guide — the way of working, how information is added, and knowledge-graph refresh
private: false
created: 2026-07-08
---

> [!ABSTRACT] Background
> The system: one Obsidian vault with agent engines on top (Claude Code, Hermes) + a knowledge graph.

# 🧭 The Three Surfaces

| When | What to open | For what |
|---|---|---|
| Quick question / on the go | **`hermes chat`** in the terminal | assistant on Ollama (free); `/model claude` for quality; quick capture |
| Deep work | **Claude Code** | compiling sources, analysis, editing — on the Pro subscription |
| Writing knowledge | **Obsidian** | my own notes and ideas |

Principle: **I write; the agents read and enrich — they don't write for me.**

# ✍️ How information gets into the vault

1. **My own ideas and notes** → manually in `2 - Notes` (or `1 - Topics`), using templates from `4 - Templates` and frontmatter. Never moved to the wiki automatically.
2. **External sources** (YouTube / articles / PDF) → drop into `7 - Wikipedia/raw/`, then say "compile…" in Claude Code or Hermes → a wiki page.
3. **Quick capture** → in `hermes chat`, ask to jot something down → written to a note in `2 - Notes` (not the journal).
4. **Journal** → `3 - Journal`, fully private, no agent touches it.
5. **Tasks** → a `- [ ]` line with a `📅 date` in any note → picked up by the Tasks plugin.

# 🔒 Privacy
`3 - Journal`, files with `private: true`, and files starting with `_` — blocked for every agent (read/write/memory/graph). Enforced by privacy-guard.

# 🔎 The knowledge graph
- Quick query: `graphify query "..."` in the terminal. Free and instant.
- The graph is a snapshot; it doesn't update itself when notes are added — but new notes count toward the refresh threshold (see below).

## Linking notes ↔ wiki (fixed method, since 2026-07-09)
My notes and the compiled pages are connected in two layers:
- **In the files**: `autolink.py` scans bidirectionally — a mention of a wiki page inside a note becomes a [[link]] and vice versa. Runs after every compile, and at the start of every Claude Code session it offers to connect new mentions.
- **In the graph**: new notes count toward the refresh counter, and every graph refresh must include bridge edges between note concepts and wiki concepts on the same topic.
- **Name collision** (a note and a wiki page with the same name): the wiki page wins — Claude offers to rename the note.
- Private notes (`private: true`) and `_` files stay out of all of this.

## Refreshing the graph
**Policy: never the API, and never Ollama for extraction (too weak).** Both the extraction and the community names are done by **Claude Code on the Pro subscription** — high quality, no cost.

- **Automatic trigger**: after every compile, the number of accumulated new sources is checked (`check_graph_staleness.py`). When it passes **5 sources** (configurable in the script) — Claude Code offers a refresh. Approve → it reads the new pages, extracts nodes/edges itself, merges into the graph (`merge_nodes.py`), clusters (`graphify cluster-only`, free) and names the communities. The counter resets.
- **Manual / on demand**: tell Claude Code *"run graphify"*.
- Fallback only (full rebuild when I'm not in the loop): `bash "0 - System/scripts/refresh_graph.sh"` (Ollama, lower quality).

# ⚡ Quick commands
- `hermes chat` — agent; inside: `/model local|claude|opus`, `/graphify query "..."`, `/exit`.
- `python3 "0 - System/scripts/sync_skills_to_hermes.py" --apply` — sync skills after editing.

