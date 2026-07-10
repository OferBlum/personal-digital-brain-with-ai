# CLAUDE.md — The Vault

## Privacy Rules — ABSOLUTE, NO EXCEPTIONS

1. Never enter, read, or reference any file inside `3 - Journal`
2. If a file has `private: true` in frontmatter → treat as non-existent
3. If a filename starts with `_` → skip without opening

These rules override everything else, always.

## Core Files — AIOS Layer 2 (read for context, do not duplicate)

These files hold the portable identity, navigation, and skill catalog. Point to them; don't restate their contents here.

- `0 - System/me.md` — who the user is, how they think, how they want AI to work with them.
- `0 - System/vault-map.md` — folder map, privacy gates, output routing.
- `0 - System/skills-index.md` — catalog of all skills + each trigger (single source of truth).

## Vault Structure

- `0 - System/` — system config files. Never modify.
- `1 - Topics/` — promoted notes with many references. Do not auto-compile.
- `2 - Notes/` — the user's notes and summaries they explicitly requested.
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

- `subject:` — wikilink to the note's topic. Only use subjects defined in SCHEMA.md. If none fits → leave empty.
- `tags:` — purpose of the file. Use only existing tags.
- `background:` — quick description of what the file is about
- `private:` — if true, the file does not exist as far as you are concerned.
- `created:` — creation date (YYYY-MM-DD)
- Language of frontmatter values: follow the user's language in the request.

## Skills — Lazy Loading

Do NOT pre-load skill files. Read the relevant skill only when the request requires it:

- Ingest new sources → read `0 - System/SKILL-ingest.md`
- Resolve and update existing pages → read `0 - System/SKILL-resolve.md`
- Answer questions → read `0 - System/SKILL-query.md`
- Health check → read `0 - System/SKILL-lint.md`
- Check status → read `0 - System/SKILL-status.md`
- Cross-link pages → read `0 - System/SKILL-crosslink.md`
- Summarize journal → read `0 - System/SKILL-journal-summary.md`
- Investments / portfolio / stocks / market → read `0 - System/SKILL-investment-agent.md`
- Styling / clothes / outfits → read `0 - System/SKILL-personal-stylist.md`
- Food, nutrition → read `0 - System/SKILL-Nutrition-Advisor.md`

If no skill matches the request → proceed with general judgment and note the absence.

## Output Rules

- Compiling external sources → `7 - Wikipedia/`
- A summary explicitly requested → `2 - Notes/`
- Every created file gets full frontmatter (see Frontmatter Convention).

## Session Rules

**At session start — read only these files:**

1. `0 - System/hooks.json` — required for automated session behavior
2. `7 - Wikipedia/_cache.md` — recent context from last session

Do NOT read other files in `0 - System/` unless a specific skill or operation requires them.

**At session end:**

- Update `7 - Wikipedia/_cache.md` with a summary of what was done.

## Conventions

- Use [[wikilinks]] for all internal links
- Language: follow the user's language in the request
- The user's own ideas stay in Notes and Topics — never move them to Wikipedia
- Never create new subjects not defined in SCHEMA.md
- Never invent new tags
- If no suitable tag or subject exists → leave the field empty

## Context Health
- If the conversation exceeds ~80 messages or you feel uncertain about earlier context, say: "⚠️ Context may be degrading — consider /clear"
- When asked about something from early in the session, say explicitly: "Based on what I can see in context..."
- Never invent details about files or decisions not currently visible
