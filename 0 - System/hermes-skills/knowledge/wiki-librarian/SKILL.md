---
name: wiki-librarian
description: "Librarian for the source-summary wiki (7 - Wikipedia) and for scoped file organization. Use to summarize/ingest a source, update or correct a summary, add related links, answer from the wiki, audit/status, or rename/move/merge requested notes. Triggers: librarian, compile, summarize this, what do I know about, check the wiki, wiki status, organize files."
version: 0.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wiki, librarian, files, audit]
    related_skills: [vault-search, obsidian]
---

# Wiki Librarian

The single canonical librarian workflow. It does not depend on Claude, a provider, a persona or a subagent, and it does not schedule itself or grant filesystem access. This file holds the policy, boundaries and routing; each task's procedure is in `references/`. Load only the reference the task needs.

## Routing

| Request | Mode | Load |
|---|---|---|
| Summarize a new source ("compile", "summarize this video/article") | Wiki, write | `references/ingest.md` + `references/source-summaries.md` |
| Correct or extend an existing summary, handle a conflict | Wiki, write | `references/resolve.md` + `references/source-summaries.md` |
| Add or repair related links | Wiki, write | `references/crosslink.md` |
| Answer a question or find a source ("what do I know about…") | Read-only | `references/query.md` |
| Health check, status, pending sources, quality review | Read-only | `references/audit.md` (+ `source-summaries.md` for quality) |
| Rename, move, merge, archive or tidy requested files | Files, write | `references/files.md` |

Semantic search is the separate `vault-search` skill. Use it for candidate discovery from any procedure above.

## Source-library policy

- The wiki is the owner's personal library of summaries of material they watched or read. It is not an auto-generated encyclopedia.
- One main summary per source by default. Split a long source only when there is a clear benefit and an approved scope.
- Different sources keep separate summaries and their own attribution. Topic similarity is not duplication. Cross-source synthesis is a separate output that has to be requested.
- Do not create automatic concept pages. Existing concept pages are legacy content: link to them, but do not migrate, rename or delete them unless asked.
- Summaries are written in the owner's language. Do not invent facts, the owner's takeaways, personal applications or tasks.

## Hard boundaries

- **Private folder:** the private folder, including the journal, does not exist for this skill. Do not access, list, index, link or summarize it, and never create daily notes. Running a local model does not waive this rule.
- **Folder-based privacy:** privacy is decided by folder only. The legacy `private:` property is ignored. A malformed header is read as empty metadata and reported, never skipped. Never disclose the names of excluded targets.
- **Search scope:** never scan the vault root and never follow symlinks. Search only explicit, task-specific allowed folders. A link target never expands permissions.
- **Read-only requests:** review, status and query make no writes at all: no log entry, manifest rebuild, report, cache edit or index refresh.
- **Write scope:** each change needs an explicit requested scope: rename, move, merge, archive, delete, schema change, mass edit or system configuration. A wiki request never authorizes editing notes. Finding or linking a target never authorizes changing it.
- **What stays untouched:** existing raw sources are immutable. Preserve human writing, completed tasks and task dates. Notes are never moved into the wiki automatically.
- **Read-only areas:** system, templates, bases and assets are read-only unless their change is requested.
- **Outside the vault:** act only on exact paths the user names. No whole-computer scan and no widening of mounts.

## Running the tools

Run every command from the vault root (for example `/vault` inside a Docker backend). `0 - System/scripts/vault-python.sh` selects an interpreter with PyYAML and numpy for either the host or Docker. On its first run it may create its own venv.

```text
bash "0 - System/scripts/vault-python.sh" -B "0 - System/hermes-skills/knowledge/wiki-librarian/scripts/audit.py" --vault "$PWD"
```

- **`scripts/audit.py`:** the read-only structural auditor. It prints JSON and writes nothing.
- **`scripts/test_*.py`:** synthetic regression tests. Run them with `-B -m unittest` from the `scripts/` folder.
- **Python requirements:** the scripts need POSIX no-follow file operations, so they run on Linux or macOS, not Windows.

## Before any write

1. Check frontmatter before reading a body. Orient from `0 - System/vault-map.md`, `0 - System/SCHEMA.md`, `7 - Wikipedia/index.md` and the relevant dates in `7 - Wikipedia/log.md`.
2. State the exact files you will change. Back them up to `7 - Wikipedia/.backup/<timestamp>-<label>/` before replacing user-authored content or catalogs.
3. Run the audit before and after the change, and compare the issue sets, not just the exit code.

## Known limits

- **Structural only:** the auditor checks structure. It does not check how faithful or good a summary is, external URLs, non-Markdown sources, or scheduled jobs.
- **Legacy report scripts:** `validate.py` and `wiki_sources_report.py` write reports into the vault. They are mutations, not status commands.
- **Manifest:** the legacy `.manifest.json` has no content hashes. It cannot prove that a source is unchanged or that a page still exists.
- **Search index:** it is refreshed only on request. An ordinary lookup never rebuilds it.
- **Hooks and schedulers:** they are separate from this skill. Inspect them per runtime before claiming they are active.

## Output

Report concisely in the owner's language:
- what was checked or changed, with exact paths;
- real counts from tool output;
- open problems;
- what was not tested, including whether the search index was refreshed.
