# Digital Brain — An Agentic Obsidian Vault

A personal knowledge base ("digital brain") that gets smarter every day, managed together by me and AI agents. One Obsidian vault, a lazy-loading skill system, an AI-maintained wiki (the **Karpathy method**), a semantic knowledge graph built with [graphify](https://github.com/sponsors/safishamsi), and hard privacy enforcement.

> **The core principle: I write; the agents read and enrich — they don't write for me.**

## The Core Idea

Two mechanisms drive the whole system:

**1. The Karpathy method — the wiki as a living database.**
Every external source I want to keep (YouTube videos, articles, PDFs) gets compiled into a structured concept page in `7 - Wikipedia/`. A `.manifest.json` tracks what was ingested, `log.md` keeps an append-only history, `index.md` is the master catalog, and `_cache.md` gives the agent instant context at the start of every session — without scanning the entire vault.

**2. Lazy-loading skills — the agent only knows what it needs.**
Instead of loading all rules upfront (which wastes context and causes hallucinations), everything is split into separate skill files under `0 - System/SKILL-*.md`. `CLAUDE.md` is just a router: it reads the request and loads only the relevant skill. `skills-index.md` is the single source of truth for what exists. This keeps the agent sharp and the system easy to extend — adding a capability = adding one SKILL file and one router line.

## Privacy — declared AND enforced

The vault holds my whole life, including things no AI should ever see. Privacy is a three-layer model, and each layer is **enforced by code**, not just written in a prompt:

| Layer | Rule | Enforcement |
|-------|------|-------------|
| **The journal** | `3 - Journal/` is completely off-limits — no read, write, memory, or graph | `.claude/privacy-guard.py` — a PreToolUse hook that **blocks any tool call** (Bash/Read/Grep/…) whose path, command, or pattern mentions the journal folder |
| **Private flag** | Any file with `private: true` in frontmatter is treated as non-existent | Every script filters on it (`vaultlib.py` is the shared privacy-aware library); `gen_graphifyignore.py` auto-generates a `.graphifyignore` so the knowledge graph never indexes flagged files |
| **Underscore files** | Any filename starting with `_` is skipped without opening | Same script-level filters + graph ignore patterns |

Extra rules on top:
- Journal processing (weekly summaries) runs **local-only via Ollama** (`journal-summary.py`) — journal text never reaches a cloud model.
- The `wiki-librarian` sub-agent is forbidden from vault-wide searches, so a stray `grep` can't surface journal content.
- The privacy rules sit at the very top of `CLAUDE.md` and override everything else.

## Managing the Vault — Folder by Folder

```text
Vault_Root/
├── CLAUDE.md            # Master prompt — privacy rules + skill router
├── SYSTEM-GUIDE.md      # The human-facing operating manual
├── 0 - System/          # The engine room (see below)
├── 1 - Topics/          # Hub pages per life domain
├── 2 - Notes/           # My own notes and ideas
├── 3 - Journal/         # Private diary — agents blocked by hook
├── 4 - Templates/       # Obsidian note templates
├── 5 - Tables/          # Dataview/Bases table definitions
├── 6 - Images/          # Attachments
└── 7 - Wikipedia/       # The AI-maintained wiki
```

Each folder has a clear owner and routing rule (full map in `0 - System/vault-map.md`):

- **`0 - System/`** — config, SCHEMA, all SKILL files, scripts, hooks, and the three "Layer 2" core files (`me.md` identity, `vault-map.md` navigation, `skills-index.md` catalog). Agents read it; they never modify it without an explicit request.
- **`1 - Topics/`** — promoted hub notes, one per life domain, referenced by many files. Never auto-compiled.
- **`2 - Notes/`** — *my* ideas and explicitly-requested summaries. Agents never rewrite them. Quick captures from Hermes land here.
- **`3 - Journal/`** — daily private notes. Blocked at the tool level.
- **`4 - Templates/`** — `Daily_Note.md` / `Standard_Note.md` scaffolds used for every new note.
- **`5 - Tables/` / `6 - Images/`** — data views and assets; read-only for agents.
- **`7 - Wikipedia/`** — the only folder the agent *writes* in. `raw/` inside it is the immutable inbox: transcripts and articles land there and are compiled into pages next to it.

Frontmatter convention on every file: `subject:` (wikilink into SCHEMA's controlled vocabulary), `tags:` (from the existing tag list only — `list_tags.sh` prints it), `background:` (one-line description), `private:` (the flag above), `created:`. Agents may never invent new subjects or tags — `SCHEMA.md` is the controlled vocabulary, and `subject_candidates.py` *suggests* promotions that only I approve.

## Everything Is Connected

The point of the system is that no piece of knowledge stays an island:

```
capture (Hermes/Obsidian) ──► 2 - Notes ─┐
                                          ├─► autolink.py ◄─► [[wikilinks]] both ways
drop source / URL / video ─► raw/ ─ingest─► 7 - Wikipedia ─┘
                                          │
                                          ├─► index.md / .manifest.json / log.md   (wiki bookkeeping)
                                          ├─► graphify graph + bridge edges        (semantic layer)
                                          └─► _cache.md                            (session memory)
```

- **File layer:** `autolink.py` scans notes and wiki pages *bidirectionally* — an unlinked mention of any page title becomes a `[[wikilink]]`. On a name collision the wiki page wins and the note gets renamed. Runs after every compile and at every session start.
- **Frontmatter layer:** every file's `subject:` ties it to a topic hub, so Dataview tables and topic pages aggregate automatically.
- **Graph layer:** [graphify](https://github.com/sponsors/safishamsi) builds a semantic knowledge graph of the whole vault (minus private surfaces) into `graphify-out/`. Every refresh must add **bridge edges** between note concepts and wiki concepts on the same topic — the two corpora stay one brain. `check_graph_staleness.py` counts new sources and triggers a refresh offer at 5.
- **Session layer:** `hooks.json` closes the loop automatically — at session start the agent reads `_cache.md`, checks for pending sources and unlinked mentions, and offers to act; at session end it updates the cache and `trim_cache.py` archives old sessions.

Graph refresh policy: extraction and community naming are done **by Claude Code on the Pro subscription** — never the raw API, and never a weak local model for extraction. `merge_nodes.py` merges Claude-authored nodes into the graph; `graphify cluster-only` (free, no LLM) re-clusters; `refresh_graph.sh` exists only as an Ollama fallback.

## How I Use Claude Code and Hermes

Two agent runtimes share the same vault and the same skills — each with a job:

### Claude Code — the deep-work engine
Run `claude` at the vault root. `CLAUDE.md` routes the request and lazy-loads exactly one skill:

- *"Compile this URL / the video queue"* → `SKILL-ingest` — fetches (Playwright or `youtube-fetch.py`), extracts concepts, writes the page, then runs the bookkeeping scripts (`build_manifest.py`, `build_index.py`, `append_log.py`, `validate.py`) and the crosslink/resolve follow-ups.
- *"What do I know about X?"* → `SKILL-query` — answers from the wiki with citations.
- *"Run graphify"* → graph refresh, with Claude itself doing the semantic extraction.
- Session lifecycle is automated via `hooks.json`, and wiki work is delegated to the `wiki-librarian` sub-agent (`.claude/agents/wiki-librarian.md`) — a Sonnet agent that owns the pipeline and can only write inside `7 - Wikipedia/`.

Used for: compiling, analysis, cross-linking, graph extraction, health checks. Quality-critical work on the Pro subscription.

### Hermes — the ambient agent
`hermes chat` in the terminal, running on local Ollama by default (free), with `/model claude` to escalate when quality matters:

- **Quick capture:** "jot this down" → a note in `2 - Notes` (never the journal, never directly the wiki).
- **Quick answers:** `/graphify query "..."` hits the knowledge graph instantly and free.
- **Same skills, no duplication:** `sync_skills_to_hermes.py --apply` converts the vault's SKILL files into Hermes (agentskills.io) format one-way — the vault stays the single source of truth. The journal-summary skill is deliberately never synced.

Rule of thumb: **Hermes for anything under a minute, Claude Code for anything that changes the vault.** Obsidian itself stays the writing surface for my own thinking.

## The Scripts

All in `0 - System/scripts/` (plus `youtube-fetch.py` / `journal-summary.py` / `list_tags.sh` in `0 - System/`). Shared rules: `vaultlib.py` centralizes privacy filters and frontmatter parsing; every writing script is dry-run by default (`--apply` to write) and backs up to `.backup/` first.

| Script | Role |
|--------|------|
| `vaultlib.py` | shared helpers: privacy rules, frontmatter, wikilink resolution, backups |
| `autolink.py` | bidirectional note↔wiki auto-linking |
| `build_index.py` / `build_manifest.py` | regenerate `index.md` / `.manifest.json` from page frontmatter |
| `append_log.py` | append-only `log.md` entries |
| `fix_frontmatter.py` | normalize dates, backgrounds, required fields |
| `validate.py` / `wiki_sources_report.py` | health checks: broken links, schema violations, bad sources |
| `subject_candidates.py` | suggest concepts worth promoting to a SCHEMA subject |
| `gen_graphifyignore.py` | generate the privacy-safe graph ignore file |
| `check_graph_staleness.py` / `merge_nodes.py` / `refresh_graph.sh` | graph refresh pipeline |
| `sync_skills_to_hermes.py` | one-way skill sync to Hermes |
| `trim_cache.py` | session-cache rotation |
| `youtube-fetch.py` | download YouTube transcripts into `raw/` from a queue file |
| `journal-summary.py` | local-only (Ollama) journal summaries |

## Getting Started

1. Clone into a new Obsidian vault (or copy the folders into an existing one).
2. Fill in `0 - System/me.md` (identity template) and replace the example subjects in `0 - System/SCHEMA.md` with your own domains.
3. Run `claude` at the vault root — the privacy guard and session hooks are wired via `.claude/`.
4. Drop a source into `7 - Wikipedia/raw/` (or add a YouTube URL to `raw/youtube_queue.md`) and say *"compile the new sources"*.
5. Optional: install [graphify](https://github.com/sponsors/safishamsi) for the knowledge graph, and [Hermes](https://github.com/NousResearch/hermes-agent) for the ambient agent.

Python 3.8+; `pip install youtube-transcript-api` for the YouTube pipeline; [Ollama](https://ollama.com) only if you use the local journal summaries or the graph fallback.

## Companion Repos

Pieces of this system also live as standalone repos:

- [llm-wiki-youtube-transcript](https://github.com/OferBlum/llm-wiki-youtube-transcript) — the YouTube → transcript → wiki ingestion pipeline
- [Investment-Agent](https://github.com/OferBlum/Investment-Agent) — the investing skill family (IBKR + Playwright)
- [personal-stylist-agent](https://github.com/OferBlum/personal-stylist-agent) — the wardrobe/stylist skill
- [automated-private-journaling-agent](https://github.com/OferBlum/automated-private-journaling-agent) — local-only journal summarization

## License

MIT — see [LICENSE](LICENSE).
