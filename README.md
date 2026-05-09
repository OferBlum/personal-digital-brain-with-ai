# Agentic Vault — Core Framework

A personal knowledge base managed by an AI agent. The architecture combines the **Karpathy method** for LLM-managed wikis with a modular, lazy-loading skill system inside an Obsidian Vault.

## The Core Idea

Two principles drive the whole system:

**1. The Karpathy method — the wiki as a living database.**
Every piece of external content you want to keep (articles, YouTube videos, podcasts) gets compiled into a structured wiki page in `7 - Wikipedia/`. A `manifest.json` tracks what was ingested, a `log.md` keeps an append-only history, and a `_cache.md` gives the agent instant context at the start of every session — without scanning the entire vault.

**2. Lazy-loading skills — the agent only knows what it needs.**
Instead of loading all rules upfront (which wastes context and causes hallucinations), everything is split into separate skill files. `CLAUDE.md` is just a router: it reads the request and loads only the relevant skill file. This keeps the agent sharp and the system easy to extend.

## Vault Structure

```text
Vault_Root/
├── CLAUDE.md                     # Master prompt — privacy rules + skill router
├── .gitignore
├── 0 - System/                   # Agent config and skill files
│   ├── SCHEMA.md                 # Valid tags and subjects (taxonomy)
│   ├── hooks.json                # Automated session lifecycle hooks
│   ├── SKILL-ingest.md           # How to compile raw sources into wiki pages
│   ├── SKILL-resolve.md          # How to update existing pages after a new ingest
│   ├── SKILL-crosslink.md        # How to interlink pages with [[wikilinks]]
│   ├── SKILL-query.md            # How to answer questions from the wiki
│   ├── SKILL-lint.md             # How to check vault health
│   └── SKILL-status.md           # How to report operation status
├── 1 - Topics/                   # Promoted notes referenced by many pages
├── 2 - Notes/                    # Your own notes and summaries
├── 3 - Journal/                  # Personal diary — completely off-limits to the agent
├── 4 - Templates/                # Obsidian templates
│   ├── Daily_Note.md
│   └── Standard_Note.md
├── 5 - Tables/                   # Dataview tables and aggregations
├── 6 - Images/                   # Image attachments
└── 7 - Wikipedia/                # AI-maintained wiki pages
    ├── index.md                  # Master catalog of all wiki pages
    ├── log.md                    # Append-only operation history
    ├── .manifest.json            # Tracks every ingested source
    ├── _cache.md                 # Hot context from last session
    └── raw/                      # Raw source material waiting to be compiled
        └── youtube_queue.md      # Queue of YouTube videos to ingest
```

## How It Works

### Ingesting new content
Drop any raw source (YouTube transcript, article text, notes) into `7 - Wikipedia/raw/`. Then tell the agent:
> "Compile the new sources"

The agent reads `SKILL-ingest.md`, extracts the key concepts, writes a structured wiki page, updates `index.md`, `log.md`, and `.manifest.json`, then cross-links the new page with existing ones.

### Querying the wiki
Ask any question naturally:
> "What do I know about [topic]?"

The agent reads `SKILL-query.md`, checks the index, reads the relevant pages, and synthesizes an answer with citations.

### The cache — instant session context
At the end of every session the agent updates `_cache.md` with what was done and what pages were touched. At the start of the next session it reads this file first — giving it full context in seconds.

## Adding Your Own Skills

This is a 2-step process. No existing file needs to change except `CLAUDE.md`.

**Step 1 — Create the skill file.**
Add a new file to `0 - System/`, e.g. `SKILL-workout-planner.md`, and describe what the agent should do when this skill is loaded.

**Step 2 — Register the route in CLAUDE.md.**
Under the `Skills — Lazy Loading` section, add one line:
```
- Workout / training / gym → read `0 - System/SKILL-workout-planner.md`
```

That's it. The agent will use the new skill the next time a relevant request comes in.

## Getting Started

1. Clone this repository
2. Open the folder as an Obsidian Vault
3. Initialize Claude Code at the vault root: `claude`
4. The agent reads `CLAUDE.md` automatically and is ready to use

The `3 - Journal/` folder is excluded from git by default — your private diary never leaves your machine.
