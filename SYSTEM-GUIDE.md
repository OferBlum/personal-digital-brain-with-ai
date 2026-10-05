---
type: note
subject: "[[Projects]]"
tags:
  - ai
background: System usage guide — the way of working, how information is added, retrieval, and privacy
generated_by: human:me
generated_at: 2026-07-08
---

> [!ABSTRACT] Background
> The system: one Obsidian vault with agent engines on top (Claude Code, Hermes) + a local semantic index.

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
Exactly one rule, and it is a folder: `3 - Journal` (the journal + every private file) is blocked
for every agent — read, write, memory, index — and is never even **listed**. The old
`private: true` flag is retired and grants nothing; anything private moves into the folder.

Enforced in code by **one** implementation — `0 - System/scripts/privacy_guard.py` — with a
thin wrapper per runtime (`.claude/privacy-guard.py` fails closed,
`~/.hermes/agent-hooks/privacy-guard.py` fails open). That matters: when each runtime had its own
guard they drifted, and the vault was only as private as its weakest agent. One file, every
agent, same policy.

Why a folder: its name can be checked in any tool payload — Bash and Grep included — without
opening a file. A frontmatter flag can't: checking it means reading the file, which is the leak.
Scripts prune the folder before descending (`iter_vault_files()`), the semantic index reads only a
positive folder allowlist (`safe_input.py`), and the vault-root `.ignore` keeps Grep/Glob out.

Files starting with `_` are **generated, not secret** — skipped when indexing, but readable.

# 🔎 Retrieval: the semantic index
One derived index, gitignored and fully regenerable — the markdown is the truth.

| Index | Answers | Reach for it when |
|---|---|---|
| `vector-out/` | **what things mean** | you half-remember something, or wrote it in another language |

- Semantic search: `bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question"` —
  crosses languages and reaches `2 - Notes/` and `1 - Topics/`, not just the wiki. Returns paths; read
  only the files above the score cliff.
- It doesn't update itself. It is incremental: `/reindex` (or
  `bash "0 - System/scripts/reindex.sh"`) shows what changed and indexes only that.

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
- **In meaning**: the semantic index holds notes, topics and wiki pages in one space, so a search finds my note and the compiled knowledge about it together.
- **Name collision** (a note and a wiki page with the same name): the wiki page wins — Claude offers to rename the note.
- The private folder stays out of all of this; `_` files are skipped as generated, not withheld as secret.

*The knowledge graph that used to sit here (graphify, with its own refresh policy) was removed — the two layers above cover what it was used for. Don't rebuild it.*

# ⚡ Quick commands
- `hermes chat` — agent; inside: `/model gpt|local`, `/exit`.
- `/reindex` — or `bash "0 - System/scripts/reindex.sh"`: update the semantic index after adding or editing notes.
- `python3 "0 - System/scripts/vsearch.py" "question"` — semantic search across the vault.
- `python3 "0 - System/scripts/validate.py"` — health check + OKF conformance.
- `python3 "0 - System/scripts/okf_verify.py" --pending` — which pages nobody has verified yet.
- `python3 "0 - System/scripts/privacy_guard.py" --selftest` — prove the privacy rule still holds.
- `python3 -m unittest discover -s "0 - System/scripts" -p "test_*.py"` — prove the semantic index never lists or opens the private folder.
- `python3 "0 - System/scripts/publish_check.py"` — what has drifted from the public mirror, and does anything leak.
- `python3 "0 - System/scripts/sync_skills_to_hermes.py" --apply` — regenerate `0 - System/hermes-skills/` after editing a SKILL file (Hermes loads that folder live via `skills.external_dirs`).

# 🧳 Agent portability
Everything an agent needs lives in the vault — swap runtimes without losing anything:
- **Instructions**: `AGENTS.md` at the root is canonical for every agent (`CLAUDE.md` just imports it).
- **Skills**: `0 - System/hermes-skills/` — loaded live by Hermes (`skills.external_dirs`). New skills an agent creates locally should be adopted into the vault periodically.
- **Memory**: `0 - System/memories/` — `~/.hermes/memories` is a symlink into it (see the README there). Keep the folder always-downloaded if the vault is on iCloud.
- **Sub-agents**: `0 - System/agents/` holds the canonical prompts; `.claude/agents/*` are thin pointers.
- **Models**: one alias per provider in `~/.hermes/config.yaml`. Claude is fully disconnected from Hermes; Anthropic credentials are kept outside `~/.hermes` entirely.
