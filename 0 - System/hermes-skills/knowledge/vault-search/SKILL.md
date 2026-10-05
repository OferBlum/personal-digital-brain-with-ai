---
name: vault-search
description: "Semantic search across the vault by meaning rather than by keyword — crosses languages and reaches notes and topics too."
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [search, semantic]
    category: knowledge
---

# Vault Search

> Privacy: never read or list the private folder (folder-only rule; Docker does not mount it). The working directory must be the vault root.

## When to Use
When you need to find something in the vault **by meaning** rather than by exact word:
"where did I write about…", "what do I have on…", "find me the note that…".
Also when you don't remember the phrasing or the language you wrote it in.

This is also the engine behind step 2 of `SKILL-query` — there it is the entry point for every question.

## Why This Exists
All the other search in the vault is lexical: `grep`, exact title matching in `autolink`. None of them
knows that a Hebrew term, `volume` and its Hebrew synonym are the same concept, and none of them will find an
English-language page from a Hebrew question. The vault is 63% Hebrew with English technical terms
mid-sentence — exactly the case that falls through.

## Usage

```bash
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question or description"
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question" --k 5
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question" --folder "2 - Notes"
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question" --files    # paths only
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/vsearch.py" "question" --json     # for programmatic use
```

Each result returns: similarity score, path, sub-heading, `background`, and a text excerpt.

## Python and Docker

Use `vault-python.sh`, not bare `python3`. It keeps a small Python environment
with pinned NumPy/PyYAML under the persistent Workspace; it creates/rebuilds
that environment automatically if it is absent or incompatible. Inside Docker,
it also points Ollama at `host.docker.internal:11434` (an explicit `OLLAMA_HOST`
overrides this). The vault root is resolved from the script location, or from
`VAULT_ROOT` when testing an isolated fixture. Do not install Python packages
globally or rely on the macOS Hermes venv inside Docker.

## After the Search
1. **Read only down to the score cliff** — in practice 1–3 files, even with `--k 8`. Below the cliff is noise.
   (0.35 is a floor, not the decision rule.)
2. **The returned excerpt is usually enough.** Read a full page only when a detail is missing.
3. **No scanner of your own after `vsearch`** — no grep over the vault, no scan script. If it wasn't
   found, it probably doesn't exist.
4. Cite as `[[page-name]]`.
5. State the confidence level: a page with `verified` was approved by the owner; a page with only
   `generated_by: process:ingest` was compiled automatically and was never verified.
6. Answer in the language the question was asked in.

## Maintenance
The index **does not update itself**. Once the Day 10 privacy gate is complete,
the everyday command after adding or editing non-sensitive notes will be:

```bash
reindex        # or: bash "0 - System/scripts/reindex.sh"
```

It prints which files were added (`+`), changed (`~`) or deleted (`-`), then indexes only those.
When there's nothing to update it says so and does nothing.

Underneath it, the direct calls:

```bash
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/embed_index.py"            # incremental — only what changed
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/embed_index.py" --changes  # which files are stale (path per line)
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/embed_index.py" --check    # one summary line (for hooks)
bash "0 - System/scripts/vault-python.sh" "0 - System/scripts/embed_index.py" --status   # index state
bash "0 - System/scripts/reindex.sh" --rebuild  # reset, after privacy review
```

The index is derived from the markdown — you can delete `vector-out/` and rebuild at any time.

## Privacy
The index contains **only** `7 - Wikipedia/` (without raw/), `2 - Notes/` and `1 - Topics/`, minus `_` system
files. Privacy is folder-only: the private folder is outside the allowlist structurally — it isn't
filtered out, it is never read or even listed. To verify:

```bash
bash "0 - System/scripts/reindex.sh" --audit
```

The indexer skips paths already listed in `.graphifyignore` *before* opening
them. Do not run a full real-vault reindex until the privacy-first checks in
Day 10 are completed: a newly flagged note missing from that list could still
be opened by the current indexer. Day 8's indexing test uses only a disposable,
non-sensitive fixture vault.
