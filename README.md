# Digital Brain — An Agentic Obsidian Vault

A personal knowledge base ("digital brain") that gets smarter every day, managed together by me and AI agents. One Obsidian vault, a lazy-loading skill system, an AI-maintained wiki (the **Karpathy method**), a semantic knowledge graph built with [graphify](https://github.com/sponsors/safishamsi), and hard privacy enforcement.

> **The core principle: I write my ideas; the agents read and enrich.**

## The Core Idea

Three mechanisms drive the whole system:

**1. The Karpathy method — the wiki as a living database.**
Every external source I want to keep (YouTube videos, articles, PDFs) gets compiled into a structured concept page in `7 - Wikipedia/`. A `.manifest.json` tracks what was ingested, `log.md` keeps an append-only history, `index.md` is the master catalog, and `_cache.md` gives the agent instant context at the start of every session — without scanning the entire vault.

**2. Lazy-loading skills — the agent only knows what it needs.**
Instead of loading all rules upfront (which wastes context and causes hallucinations), everything is split into separate skill files under `0 - System/SKILL-*.md`. `CLAUDE.md` is just a router: it reads the request and loads only the relevant skill. `skills-index.md` is the single source of truth for what exists. This keeps the agent sharp and the system easy to extend — adding a capability = adding one SKILL file and one router line.

**3. My own ideas — written by me, wired in by the system.**
The wiki holds the world's knowledge; `2 - Notes/` holds *mine*. I write ideas, thoughts, and summaries as plain notes (quick captures from Hermes land there too), and agents are forbidden from rewriting them — they only enrich and connect. The wiring happens on three levels without me doing anything: every note's `subject:` frontmatter attaches it to a topic hub in `1 - Topics/`; `autolink.py` scans bidirectionally after every compile, so a note that mentions a wiki page gets a `[[wikilink]]` and vice versa; and every graph refresh must add bridge edges between my note concepts and the wiki concepts on the same topic. New notes even count toward the graph-refresh threshold, exactly like external sources. The result: an idea I jot down today is automatically linked to everything I've ever learned about it — my thinking and the compiled knowledge become one connected brain, while staying clearly separated on disk (mine vs. compiled) so the agent always knows what it may touch.

## Privacy — declared AND enforced

The vault holds my whole life, including things no AI should ever see. The policy is
**exactly two rules**, and both are enforced by code rather than by a prompt:

| Rule | Meaning | Enforced by |
|------|---------|-------------|
| **The journal** | `3 - Journal/` is completely off-limits — no read, write, memory, graph, or index | The pre-tool hook. Blocked wherever the folder name appears in a tool payload, for every tool |
| **The private flag** | Any file with `private: true` in frontmatter is treated as non-existent | The same hook, for any call naming a single resolvable file (it reads that file's frontmatter); plus `vaultlib.py`, `gen_graphifyignore.py` and `embed_index.py --audit` for the bulk paths a hook can't see |

**One guard, every agent.** The policy lives in exactly one file —
`0 - System/scripts/privacy_guard.py` — and each runtime's hook is a thin wrapper around it
(`.claude/privacy-guard.py`, `~/.hermes/agent-hooks/privacy-guard.py`; a Codex-backed agent
reaches the vault through Hermes and inherits the same hook). This is the part worth copying:
when each runtime shipped its own guard they silently drifted, and a vault is only as private
as its weakest agent. `privacy_guard.py --selftest` runs the whole policy matrix against a
throwaway fixture vault so the guarantee stays testable.

**What it does not cover, stated plainly:** a Bash or Grep invocation names no single file, so
the `private: true` rule cannot be evaluated for those calls. They are covered by the journal
rule plus the script-level filters. Better to write that down than to imply a guarantee the
code doesn't make.

**`_` files are not secret.** A leading underscore marks a *generated* file — skipped when
indexing or compiling, but readable. (An earlier version of this system did treat `_` as a
privacy rule; it contradicted "read `_cache.md` at session start" and broke the ambient agent.)

Two more habits on top:
- Both derived indexes (`graphify-out/`, `vector-out/`) are gitignored, because each one records
  real note paths — the index files would themselves be a list of private note titles.
- The `wiki-librarian` sub-agent is forbidden from vault-wide searches, so a stray `grep` can't
  surface journal content.

## Managing the Vault — Folder by Folder

```text
Vault_Root/
├── AGENTS.md            # Canonical agent instructions — privacy rules + skill router (any agent)
├── CLAUDE.md            # Thin Claude Code layer — imports AGENTS.md
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

Frontmatter convention on every file: `type:`, `subject:`, `tags:`, `background:` (a one-line
description), `private:`, `created:`, plus the OKF trust keys below. Agents may never invent new
subjects, tags or types — `SCHEMA.md` is the controlled vocabulary, and `subject_candidates.py`
*suggests* promotions that only I approve.

## The OKF standard (v0.2)

Every file is tagged on **three closed axes**, each answering exactly one question:

| Axis | Question | Values |
|------|----------|--------|
| `type` | what kind of object is this | 8 values: `wiki-page`, `note`, `topic-hub`, `template`, `checklist`, `report`, `index`, `log` |
| `subject` | which area of life it belongs to | only what SCHEMA declares; **empty is a valid answer** — a page about HNSW indexing is not a life domain |
| `tags` | what the file is for | only what SCHEMA declares, never with a leading `#` |

The extension rule is the whole point: **a new subject or tag goes into `SCHEMA.md` first, and
only then gets used.** Invent one inline and `validate.py` fails — which is the behaviour I want,
because a controlled vocabulary that drifts is just tags again.

On top sits a **trust layer** that separates two things most systems conflate:

- `generated_by` / `generated_at` — *who produced this*: `human:me`, `process:ingest`, or `agent/version`.
- `verified: [{by, at}]` — *who read it and confirmed it*. **Absent means unverified**, which is
  the honest state for a page an agent compiled and nobody has checked. `okf_verify.py --pending`
  lists exactly those, and stamping one is a deliberate act.
- `status:` — `draft` / `stable` / `deprecated`. Absent = `stable`.

Two flat keys, never a nested `generated:` map — Obsidian Properties only renders flat scalars,
and a nested map swallows both rows. `okf_migrate.py` migrates an existing vault (dry-run by
default), `validate.py` enforces the result.

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

## Two retrieval indexes

The graph was never enough on its own. Every other kind of search here is *lexical* — `grep`,
exact title matching, trigrams over graph labels — and none of those knows that a word and its
translation are the same concept. In a vault that mixes languages mid-sentence, that is the case
that falls through constantly. So there are two indexes, answering different questions:

| Index | Answers | How |
|-------|---------|-----|
| `graphify-out/` | **how things connect** | concepts and edges, community detection |
| `vector-out/` | **what things mean** | bge-m3 embeddings via local Ollama, cosine over numpy |

`vsearch.py "question"` returns the most relevant passages by meaning, crossing languages and
reaching `2 - Notes/` and `1 - Topics/` — which the old keyword path never touched. It is also
step 2 of `SKILL-query`, so every question starts there.

Deliberately not a vector database: at this size numpy does cosine over everything in under 10ms,
so faiss/chroma would be dependencies bought for nothing. The index is derived and disposable —
delete `vector-out/` and rebuild. `reindex.sh` is incremental: it prints which files were added,
changed or deleted, then embeds only those, and `embed_index.py --check` nudges at session start
when the index falls behind.

Privacy here is structural, not a filter: the indexer's allowlist contains three content folders,
so the journal isn't excluded — it is never reachable. `embed_index.py --audit` re-proves that
after every build and exits non-zero if anything slipped in. And `vector-out/` is gitignored,
because its metadata records every indexed path.

Graph refresh policy: extraction and community naming are done **by Claude Code on the Pro subscription** — never the raw API, and never a weak local model for extraction. `merge_nodes.py` merges Claude-authored nodes into the graph; `graphify cluster-only` (free, no LLM) re-clusters; `refresh_graph.sh` exists only as an Ollama fallback.

## How I Use Claude Code and Hermes

Two agent runtimes share the same vault and the same skills — each with a job:

### Claude Code — the deep-work engine
Run `claude` at the vault root. `CLAUDE.md` routes the request and lazy-loads exactly one skill:

- *"Compile this URL / the video queue"* → `SKILL-ingest` — fetches (Playwright or `youtube-fetch.py`), extracts concepts, writes the page, then runs the bookkeeping scripts (`build_manifest.py`, `build_index.py`, `append_log.py`, `validate.py`) and the crosslink/resolve follow-ups.
- *"What do I know about X?"* → `SKILL-query` — semantic search first, then answers with citations and a confidence level (verified vs merely compiled).
- *"Where did I write about…"* → `SKILL-vsearch` — meaning-based search across the whole vault.
- *"Run graphify"* → graph refresh, with Claude itself doing the semantic extraction.
- Session lifecycle is automated via `hooks.json`, and wiki work is delegated to the `wiki-librarian` sub-agent (`.claude/agents/wiki-librarian.md`) — a Sonnet agent that owns the pipeline and can only write inside `7 - Wikipedia/`.

Used for: compiling, analysis, cross-linking, graph extraction, health checks. Quality-critical work on the Pro subscription.

### Hermes — the ambient agent
`hermes chat` in the terminal. Model switching is one alias per provider in `~/.hermes/config.yaml` — e.g. `/model gpt` (cloud) or `/model local` (on-device Ollama for anything private). Claude never runs inside Hermes (subscription ToS); the Anthropic key lives outside `~/.hermes` entirely.

- **Quick capture:** "jot this down" → a note in `2 - Notes` (never the journal, never directly the wiki).
- **Quick answers:** `/graphify query "..."` hits the knowledge graph instantly and free.
- **Same skills, zero copies:** `0 - System/hermes-skills/` (generated from the vault's SKILL files by `sync_skills_to_hermes.py --apply`) is registered as `skills.external_dirs` in Hermes' config — Hermes loads the vault's skills *live*, nothing is copied into `~/.hermes`. A skill can be marked `skip` so it is never exported: publishing is, because it does git operations and a leak audit.

Rule of thumb: **Hermes for anything under a minute, Claude Code for anything that changes the vault.** Obsidian itself stays the writing surface for my own thinking.

## Agent Portability — everything the agent needs lives in the vault

"File over AI" applies to the agents themselves. Every piece of agent state is a portable markdown file inside the vault, so swapping runtimes (Hermes → anything else, Claude Code → Codex) is a pointer change, not a migration:

| What | Where | How the runtime finds it |
|------|-------|--------------------------|
| Instructions | `AGENTS.md` (canonical) | Codex & most agents read it natively; `CLAUDE.md` just imports it |
| Skills | `0 - System/hermes-skills/` | Hermes `skills.external_dirs` (live, no sync) |
| Memory | `0 - System/memories/` | `~/.hermes/memories` is a **symlink** into the vault (see the README there) |
| Sub-agent prompts | `0 - System/agents/` | `.claude/agents/*` are thin pointers to the canonical prompts |

To adopt a new agent runtime: point it at `AGENTS.md` and those three folders. Done.

## The Scripts

All in `0 - System/scripts/` (plus `youtube-fetch.py` and `list_tags.sh` in `0 - System/`). Shared rules: `vaultlib.py` centralizes privacy filters and frontmatter parsing; every writing script is dry-run by default (`--apply` to write) and backs up to `.backup/` first.

| Script | Role |
|--------|------|
| `vaultlib.py` | shared helpers: privacy rules, frontmatter, wikilink resolution, backups |
| `privacy_guard.py` | **the** privacy policy — one implementation, one thin wrapper per runtime; `--selftest` proves it |
| `autolink.py` | bidirectional note↔wiki auto-linking |
| `build_index.py` / `build_manifest.py` | regenerate `index.md` / `.manifest.json` from page frontmatter |
| `append_log.py` | append-only `log.md` entries |
| `fix_frontmatter.py` | normalize dates, backgrounds, required fields |
| `validate.py` / `wiki_sources_report.py` | health checks: broken links, schema violations, bad sources |
| `okf_migrate.py` / `okf_verify.py` | migrate frontmatter to OKF v0.2; stamp and audit the `verified` trust layer |
| `embed_index.py` / `vsearch.py` / `reindex.sh` | build, query and incrementally update the semantic index |
| `subject_candidates.py` | suggest concepts worth promoting to a SCHEMA subject |
| `gen_graphifyignore.py` | generate the privacy-safe graph ignore file |
| `check_graph_staleness.py` / `merge_nodes.py` / `refresh_graph.sh` | graph refresh pipeline |
| `sync_skills_to_hermes.py` | regenerate `hermes-skills/` (agentskills.io format) from the SKILL files |
| `publish_check.py` / `publish_port.py` | detect drift against the public mirror and port the mechanical parts; leak audit |
| `trim_cache.py` | session-cache rotation |
| `list_tags.sh` | print the tags actually in use, for comparison against SCHEMA |
| `youtube-fetch.py` | download YouTube transcripts into `raw/` from a queue file |

## Getting Started

1. Clone into a new Obsidian vault (or copy the folders into an existing one).
2. Fill in `0 - System/me.md` (identity template) and replace the example subjects and tags in `0 - System/SCHEMA.md` with your own domains.
3. Run `claude` at the vault root — the privacy guard and session hooks are wired via `.claude/`.
   Sanity-check the guard first: `python3 "0 - System/scripts/privacy_guard.py" --selftest`.
4. Build the semantic index once: `bash "0 - System/scripts/reindex.sh"`.
5. Drop a source into `7 - Wikipedia/raw/` (or add a YouTube URL to `raw/youtube_queue.md`) and say *"compile the new sources"*.
6. Optional: install [graphify](https://github.com/sponsors/safishamsi) for the knowledge graph, and [Hermes](https://github.com/NousResearch/hermes-agent) for the ambient agent.

Requirements: Python 3.8+, `pip install pyyaml numpy`, and [Ollama](https://ollama.com) with
`ollama pull bge-m3` for semantic search (everything embedding-related runs on-device).
`pip install youtube-transcript-api` for the YouTube pipeline.

Already have a vault with frontmatter? `python3 "0 - System/scripts/okf_migrate.py"` shows what
OKF v0.2 would change without writing anything.

## Companion Repos

This repo is the **engine**: the knowledge pipeline, the retrieval layer, the privacy model and
the schema. The personal-domain skills that run on top of it are deliberately not here — they
encode someone's actual portfolio, wardrobe and diet, which is exactly the content this system
exists to keep private. Each lives on its own:

- [llm-wiki-youtube-transcript](https://github.com/OferBlum/llm-wiki-youtube-transcript) — the YouTube → transcript → wiki ingestion pipeline
- [Investment-Agent](https://github.com/OferBlum/Investment-Agent) — the investing skill family (IBKR + Playwright)
- [personal-stylist-agent](https://github.com/OferBlum/personal-stylist-agent) — the wardrobe/stylist skill
- [automated-private-journaling-agent](https://github.com/OferBlum/automated-private-journaling-agent) — local-only journal summarization

Adding one back is three edits: a `SKILL-*.md` file, a row in `skills-index.md`, and a route in
`AGENTS.md`. That is the whole extension model.

## License

MIT — see [LICENSE](LICENSE).
