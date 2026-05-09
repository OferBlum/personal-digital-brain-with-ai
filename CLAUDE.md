# CLAUDE.md — AI Agent Vault Rules

## Privacy Rules — ABSOLUTE, NO EXCEPTIONS

1. Never enter, read, or reference any file inside `3 - Journal`
2. If a file has `private: true` in its frontmatter → treat as non-existent
3. If a filename starts with `_` → skip without opening

These rules override everything else, always.

## Vault Structure

- `0 - System/` — system config files. Never modify.
- `1 - Topics/` — promoted notes with many references. Do not auto-compile.
- `2 - Notes/` — User's notes and summaries explicitly requested.
- `3 - Journal/` — completely off limits. Never touch.
- `4 - Templates/` — templates only. Do not modify.
- `5 - Tables/` — do not modify.
- `6 - Images/` — do not modify.
- `7 - Wikipedia/raw/` — raw source material. Never modify these files.
- `7 - Wikipedia/` — compiled wiki pages. You write and maintain these.
- `7 - Wikipedia/index.md` — master catalog. Update after every ingest.
- `7 - Wikipedia/log.md` — append-only history. Log every operation.
- `7 - Wikipedia/.manifest.json` — tracks every ingested source.
- `7 - Wikipedia/_cache.md` — hot cache from last session. Read at start, update at end.
- `7 - Wikipedia/raw/youtube_queue.md` — YouTube videos queue for compilation. Updated automatically after each ingest.

## Frontmatter Convention

Every file has:

- `topic:` — wikilink to the note's topic. Only use subjects defined in SCHEMA.md. If none fits → leave empty.
- `tags:` — purpose of the file. Only use tags defined in SCHEMA.md. If none fits → leave empty.
- `private:` — if true, file does not exist as far as you are concerned.
- `created:` — creation date (YYYY-MM-DD)

## Skills — Lazy Loading

Do NOT pre-load skill files. Read the relevant skill only when the request requires it:

- Ingest new sources → read `0 - System/SKILL-ingest.md`
- Resolve and update existing pages → read `0 - System/SKILL-resolve.md`
- Answer questions → read `0 - System/SKILL-query.md`
- Health check → read `0 - System/SKILL-lint.md`
- Check status → read `0 - System/SKILL-status.md`
- Cross-link pages → read `0 - System/SKILL-crosslink.md`

<!-- Add your own skills here — see README for instructions -->

If no skill matches the request → proceed with general judgment and note the absence.

## Output Rules

- External sources compilation → `7 - Wikipedia/`
- Explicitly requested summaries → `2 - Notes/`
- Every newly created file gets full frontmatter (see Frontmatter Convention).

## Session Rules

**At session start — read only these three files:**

1. `0 - System/SCHEMA.md` — required to know valid tags and subjects
2. `0 - System/hooks.json` — required for automated session behavior
3. `7 - Wikipedia/_cache.md` — recent context from last session

Do NOT read other files in `0 - System/` unless a specific skill or operation requires them.

**At session end:**

- Update `7 - Wikipedia/_cache.md` with a summary of what was done.

## Conventions

- Use [[wikilinks]] for all internal links
- User's own ideas stay in 2 - Notes and Topics — never move them to Wikipedia
- Never create new tags or subjects not defined in SCHEMA.md
- If no suitable tag or subject exists → leave the field empty
