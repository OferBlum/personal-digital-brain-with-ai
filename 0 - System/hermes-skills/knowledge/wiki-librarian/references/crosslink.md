# Crosslink: add or repair useful links

Use for links from requested pages to related permitted pages, or for link repair after a scoped file operation. This is never automatic housekeeping.

## Scope

- **Two lists.** Keep the editable files (the requested pages only) separate from the candidate targets.
- **Candidate folders.** Targets can be in `7 - Wikipedia`, `2 - Notes` and `1 - Topics`. Other permitted files can also be targets if the owner names them.
- **Linking is not editing.** Linking to a note never authorizes editing it, moving it into the wiki, or adding a backlink.

## Procedure

1. **Search.** Find candidates with `vault-search`, querying the main idea and, optionally, a distinct secondary idea. Do not add a wiki-only filter. If the index or the embedding service is unavailable, fall back to a targeted filename or text search inside the permitted folders.
2. **Read before choosing.** Read each candidate before choosing it; semantic similarity is not evidence of a useful link. Good reasons are: a continuation, a helpful explanation, a direct shared topic, a contrasting view, or a conflict between sources.
3. **Name collisions.** If a note and a wiki page share a name, use the full vault-relative path with a display alias, for example `[[7 - Wikipedia/X.md|X]]`. Nothing wins by default, and nothing gets renamed to resolve it.
4. **Preview.** Show each link and why it helps. Use a natural inline link or the optional `## Related` section, never an empty section. Preserve frontmatter, existing links, aliases, anchors, headings, code, URLs and the author's wording.
5. **Apply.** Apply only the approved patches with file tools. Back up first when the change is substantial.
6. **Log and verify.** For a wiki write, append one log entry; for a review, write nothing. Recheck the changed links and compare the audit.

## Rules

- **No forced linking:** no link quota, no new concept pages created as targets, no reciprocal edits.
- **No bulk autolinking:** the old corpus-wide autolinker was retired. Bulk linking needs its own design, scope and tests.
