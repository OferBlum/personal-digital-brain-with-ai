---
subject:
tags:
  - wiki
background: Usage guide — how to operate and maintain the wiki correctly (compiling, queries, health, scripts)
private: false
last_compiled: 2026-06-30
provenance: inferred
created: 2026-06-30
---

# Wiki Usage Guide

How to work correctly with the knowledge base in `7 - Wikipedia/`. Every operation is triggered in natural language —
just tell Claude what you want, and it loads the right skill and runs the scripts behind the scenes.

---

## What the wiki is

A system that compiles **raw sources** (articles, YouTube videos, notes, web pages) into clean, linked,
maintained **concept pages**. You drop in a source → Claude extracts the essence → a page is created with
frontmatter, internal links, and an entry in the manifest and log.

- **Raw sources** live in `7 - Wikipedia/raw/` — never touched.
- **Compiled pages** live in `7 - Wikipedia/` — these are what Claude writes and maintains.
- **Your own ideas** stay in `2 - Notes/` and `1 - Topics/` — never moved into the wiki.

---

## The main operations — what to say

| What you want | What to write (example) | What happens |
|---------------|--------------------------|--------------|
| **Compile a new source** | "compile file X" / "compile this URL" / "compile the videos" | extraction → new page + automatic index/manifest/log update |
| **Ask a question** | "what do I know about [[topic]]?" | Claude reads the index + relevant pages and answers with sources |
| **See status** | "what's the wiki status?" / "what's pending?" | how many pages, what was compiled, what's pending |
| **Health check** | "run a wiki health check" | runs validate + an errors/warnings report |
| **Link pages** | "cross-link the pages" / happens automatically after a compile | adds [[links]] between pages that mention each other |
| **Update existing pages** | "update pages related to the new information" | finds contradictions/reinforcements/additions and updates |

> Most of the time saying "compile this" is enough — the linking and update steps run automatically afterwards.

---

## Compiling a new source (from your point of view)

1. Put the source in `7 - Wikipedia/raw/` (or give a URL / ask to compile the YouTube queue).
2. Say: **"compile [source name]"**.
3. Claude: reads the source → extracts concepts → writes a page with full frontmatter.
4. Automatically: `index.md`, `.manifest.json`, `log.md` are updated, and crosslink + validation run.
5. You get a summary of what was created and where.

---

## The scripts behind the scenes

They live in `0 - System/scripts/`. You don't need to run them manually — Claude does — but it's good to know what exists:

| Script | Role |
|--------|------|
| `validate.py` | checks frontmatter, broken links, stale data → `validation_report.md` |
| `wiki_sources_report.py` | verifies every `wiki_sources` points to an existing source → `wiki_sources_issues.md` |
| `autolink.py` | adds internal links automatically (dry-run, then `--apply`) |
| `build_index.py` | regenerates `index.md` from the pages' metadata |
| `build_manifest.py` | regenerates the canonical `.manifest.json` |
| `fix_frontmatter.py` | normalizes frontmatter (dates, background, required fields) |
| `append_log.py` | appends a line to `log.md` |
| `subject_candidates.py` | suggests concepts worth becoming a subject in SCHEMA |
| `trim_cache.py` | archives old sessions in `_cache.md` |

> Every script that writes backs up first to `7 - Wikipedia/.backup/`. The default mode is always dry-run; writing only with `--apply`.

---

## Routine maintenance — how often

- **After a compile:** happens by itself (crosslink + validate). Nothing to do.
- **Occasionally:** "run a health check" — to catch broken links or missing background.
- **When sources pile up:** "what's pending?" and then "compile the pending ones".
- **Subject promotion:** if a concept is linked from many pages, Claude will suggest adding it to SCHEMA — **the decision is yours**, Claude never adds subjects on its own.

---

## Privacy rules (always apply)

- `3 - Journal/` — absolutely out of bounds. The wiki never touches the journal.
- A file with `private: true` — treated as non-existent.
- A file whose name starts with `_` — skipped.

---

## Important points

- **Subjects and tags:** only what exists in `0 - System/SCHEMA.md`. No inventing new ones without approval. If none fits → leave empty.
- **Broken source links** that come from an external URL or a YouTube transcript are acceptable — not a bug to fix.
- **`provenance`** on every page states where the information came from: `extracted` (direct), `inferred` (synthesis), `ambiguous` (conflicting sources).
