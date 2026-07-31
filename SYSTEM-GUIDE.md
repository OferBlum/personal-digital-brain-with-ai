---
type: note
subject: "[[Projects]]"
tags:
  - ai
background: System usage guide — the way of working, how information is added, retrieval, and knowledge-graph refresh
private: false
created: 2026-07-08
generated_by: human:me
generated_at: 2026-07-08
---

> [!ABSTRACT] Background
> The system: one Obsidian vault with agent engines on top (Claude Code, Hermes) + a knowledge graph.

# 🧭 The Three Surfaces

| When | What to open | For what |
|---|---|---|
| Quick question / on the go | **`hermes chat`** in the terminal | default cloud model via `/model gpt`; `/model local` = on-device Ollama for private content; quick capture. **No Claude inside Hermes** |
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
Exactly two rules, blocked for every agent (read/write/memory/graph/index):
`3 - Journal`, and any file with `private: true`.

Enforced in code by **one** implementation — `0 - System/scripts/privacy_guard.py` — with a
thin wrapper per runtime (`.claude/privacy-guard.py`, `~/.hermes/agent-hooks/privacy-guard.py`).
That matters: when each runtime had its own guard they drifted, and the vault was only as
private as its weakest agent. One file, every agent, same policy.

Honest limit: a Bash or Grep call names no single file, so the `private: true` rule can't be
evaluated there. That gap is covered by the script-level filters (`vaultlib.py`,
`gen_graphifyignore.py`, `embed_index.py --audit`).

Files starting with `_` are **generated, not secret** — skipped when indexing, but readable.

# 🔎 Retrieval: two indexes
Two derived indexes answer different questions. Both are gitignored and fully regenerable —
the markdown is the truth.

| Index | Answers | Reach for it when |
|---|---|---|
| `graphify-out/` | **how things connect** | you want the neighbourhood of a concept, or to see clusters |
| `vector-out/` | **what things mean** | you half-remember something, or wrote it in another language |

- Semantic search: `python3 "0 - System/scripts/vsearch.py" "question"` — crosses languages
  and reaches `2 - Notes/` and `1 - Topics/`, not just the wiki.
- Graph query: `graphify query "..."` in the terminal. Free and instant.
- Neither updates itself. The semantic index is incremental: `/reindex` (or
  `bash "0 - System/scripts/reindex.sh"`) shows what changed and indexes only that.
  The graph is a snapshot; new notes count toward its refresh threshold (see below).

# 📐 OKF v0.2 — the frontmatter standard
Three closed axes on every file: `type` (what kind of object), `subject` (which life domain),
`tags` (what it's for). All three are defined in `0 - System/SCHEMA.md`, and
`validate.py` fails on anything not declared there — so a new subject or tag goes into SCHEMA
*first*.

On top of that, a trust layer that separates *who made this* from *who checked it*:
`generated_by` / `generated_at` versus `verified: [{by, at}]`. Absent `verified` means
unverified, which is the honest default — stamp it with `okf_verify.py` once you've actually
read the page.

## Linking notes ↔ wiki (fixed method, since 2026-07-09)
My notes and the compiled pages are connected in two layers:
- **In the files**: `autolink.py` scans bidirectionally — a mention of a wiki page inside a note becomes a [[link]] and vice versa. Runs after every compile, and at the start of every Claude Code session it offers to connect new mentions.
- **In the graph**: new notes count toward the refresh counter, and every graph refresh must include bridge edges between note concepts and wiki concepts on the same topic.
- **Name collision** (a note and a wiki page with the same name): the wiki page wins — Claude offers to rename the note.
- Private notes (`private: true`) stay out of all of this; `_` files are skipped as generated, not withheld as secret.

## Refreshing the graph
**Policy: never the API, and never Ollama for extraction (too weak).** Both the extraction and the community names are done by **Claude Code on the Pro subscription** — high quality, no cost.

- **Automatic trigger**: after every compile, the number of accumulated new sources is checked (`check_graph_staleness.py`). When it passes **5 sources** (configurable in the script) — Claude Code offers a refresh. Approve → it reads the new pages, extracts nodes/edges itself, merges into the graph (`merge_nodes.py`), clusters (`graphify cluster-only`, free) and names the communities. The counter resets.
- **Manual / on demand**: tell Claude Code *"run graphify"*.
- Fallback only (full rebuild when I'm not in the loop): `bash "0 - System/scripts/refresh_graph.sh"` (Ollama, lower quality).

# ⚡ Quick commands
- `hermes chat` — agent; inside: `/model gpt|local`, `/graphify query "..."`, `/exit`.
- `/reindex` — or `bash "0 - System/scripts/reindex.sh"`: update the semantic index after adding or editing notes.
- `python3 "0 - System/scripts/vsearch.py" "question"` — semantic search across the vault.
- `python3 "0 - System/scripts/validate.py"` — health check + OKF conformance.
- `python3 "0 - System/scripts/okf_verify.py" --pending` — which pages nobody has verified yet.
- `python3 "0 - System/scripts/privacy_guard.py" --selftest` — prove the privacy rules still hold.
- `python3 "0 - System/scripts/publish_check.py"` — what has drifted from the public mirror, and does anything leak.
- `python3 "0 - System/scripts/sync_skills_to_hermes.py" --apply` — regenerate `0 - System/hermes-skills/` after editing a SKILL file (Hermes loads that folder live via `skills.external_dirs`).

# 🧳 Agent portability
Everything an agent needs lives in the vault — swap runtimes without losing anything:
- **Instructions**: `AGENTS.md` at the root is canonical for every agent (`CLAUDE.md` just imports it).
- **Skills**: `0 - System/hermes-skills/` — loaded live by Hermes (`skills.external_dirs`). New skills an agent creates locally should be adopted into the vault periodically.
- **Memory**: `0 - System/memories/` — `~/.hermes/memories` is a symlink into it (see the README there). Keep the folder always-downloaded if the vault is on iCloud.
- **Sub-agents**: `0 - System/agents/` holds the canonical prompts; `.claude/agents/*` are thin pointers.
- **Models**: one alias per provider in `~/.hermes/config.yaml`. Claude is fully disconnected from Hermes; the Anthropic key lives in `~/.secrets/anthropic.env`, used only by `refresh_graph.sh claude`.
