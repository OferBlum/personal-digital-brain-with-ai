# Source summaries: writing and quality contract

The wiki is a library of summaries of things the owner watched or read. The goal is to find a source, recall its ideas and return to useful explanations, not to grow a concept encyclopedia. Permissions in `SKILL.md`, `AGENTS.md` and the vault map stay binding.

## Unit of work

- One main summary per source: a video, article, lecture, book, or an explicitly defined chapter.
- A long source may get a main summary plus linked parts only if there is a clear benefit and an approved scope. Do not split every concept into its own page.
- Summaries of different sources stay separate even when they share a topic. A synthesis or comparison is a separate, requested output with explicit attribution.
- Existing concept pages are not deleted, changed or converted automatically. They can be useful link targets.

## Source identity and duplicates

1. Read the real source details: title, author or creator, URL or path, and publication date if known. Do not guess missing details.
2. Search the index and permitted summaries by source identity, title and creator. Read the candidates' `wiki_sources`. Keep identifiers exactly as given. Do not rewrite a failing URL or ID.
3. Two copies or formats of the same content are candidates for one summary. Topic similarity alone is not duplication.
4. If a summary of the same source exists, update it within the requested scope instead of creating a competing copy. Renames, merges and historical duplicates need explicit scope.
5. Choose a title that identifies the source and is easy to search. Add the creator only when needed to tell sources apart. Do not rename existing files in passing.

## Reading the source and declaring coverage

- Write only from source content that was actually read. Do not write from a search snippet, a title or general knowledge.
- If only a chapter, excerpt or partial transcript was read, state the coverage explicitly. Never present it as a full summary.
- If retrieval fails, report the gap. Never invent a transcript, examples or a plausible-looking summary.
- Publication, processing and human review are different events. A processing date is not a publication date, and unknown details stay empty.
- Existing raw files are never edited. Saving new raw material needs authorization under the vault map.

## Recommended structure

Use two layers: a quick recap, then a useful detailed summary. Adapt the headings and length to the source; this is not a rigid template. Page text follows the owner's language.

```markdown
# <source title>

Source: creator / author, source type, link or reference
Coverage: only if the source was read partially

## In short
The central idea and what is worth remembering.

## Summary
The ideas, arguments, explanations and important examples.
Replace this heading with source-appropriate headings if useful.

## Related
Links to relevant pages, only when the connection is useful.
```

- **Source details:** they can sit in the opening line or in a short section.
- **`## Related`:** it is optional. Never leave it empty.
- **Metadata:** use the existing fields (`type: wiki-page`, `wiki_sources`, `background`, plus subjects and tags from SCHEMA). Do not invent new types, tags or keys to fit this structure.

### Frontmatter

```yaml
---
type: wiki-page
subject:
tags: [wiki]
background: "short description"
wiki_sources:
  - "[[7 - Wikipedia/raw/actual-source.md]]"
provenance: extracted
last_compiled: YYYY-MM-DD
generated_by: process:ingest
generated_at: YYYY-MM-DD
---
```

- **`wiki_sources`:** it is always a list. Use full vault-relative paths with the real extension, a quoted wikilink in YAML, or a plain URL.
- **Dates:** get today's date from a tool.
- **Subjects and tags:** use only values from SCHEMA. If nothing fits, leave the field empty.
- **Fields to leave alone:** never set `verified`, and keep existing human verification history.
- **`provenance`:** `extracted` means direct from the source, `inferred` means a synthesis, and `ambiguous` means a genuinely unresolved conflict.

## Fidelity and depth

- Present what the creator claims. A claim is not an independently verified fact.
- Keep the line of explanation: claim, reasoning, example and caveat, where they matter for understanding. A list of generic headings is not enough.
- Write in your own words, with selected examples. Do not reproduce large parts of the source. A short source stays short, and a rich source is not compressed until the explanation is lost.
- Do not add outside knowledge as if it came from the source. Agent context or interpretation, if requested, goes in a separate, attributed place.
- Do not invent what the owner learned, thinks or will apply. Personal insights go in only if the owner supplied them.
- No automatic tasks or forced action section. Tasks that were explicitly requested go at the end, and existing task history is kept.
- When updating, a new source never erases the original source's position. Comparisons and disagreements are attributed to the separate sources.

## Links

Use `vault-search` for candidates across wiki, notes and subjects, then read each target and choose links with a reason. The link rules are in `crosslink.md`. A link is worth adding when the target is a continuation, a helpful explanation, a direct shared topic, a different angle, or a contradiction. Links have no quota.

## Read-only quality review

`audit.py` checks structure only. For each summary in an authorized sample, check:

- **Source:** can the source be identified and found?
- **Coverage:** is the reading coverage declared and not overstated?
- **Content:** is the recap useful, and does the summary keep the important arguments, examples and caveats?
- **Accuracy:** does it contain claims missing from the source, mixed sources, or invented personal attributions?
- **Usefulness:** could someone return to it later and understand the main points without re-consuming the source?
- **Links and duplicates:** are the links useful, and is there no duplicate summary of the same source?

Report each finding with:
- the location in both the source and the summary;
- its impact;
- a proposed fix.

If the source is inaccessible, say that fidelity was not verified. Never grade a summary on structure alone. Do not rewrite a summary as part of a review.

## Verification before reporting a write

- **Before saving:** confirm real sources, correct attribution and coverage, no unsupported additions, permitted links, and no competing copy of the same source.
- **After saving:** verify the file, the relevant navigation, and the change list. Then state what was written, what was read only partially, and what could not be verified.
- **Tests:** instruction-contract tests do not prove the quality of summaries a model writes later.
