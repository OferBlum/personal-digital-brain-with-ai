# Query: answer from the library (read-only)

Use to find a source the owner watched or read, recall its summary, or answer a question from permitted wiki, notes or subject pages.

1. **Pick the corpus.** For wiki questions, start from `7 - Wikipedia/index.md`. For the owner's own writing, search notes and subjects. Never scan the vault.
2. **Find candidates.** Use `vault-search`, which returns paths only. Use exact title, source or ID lookup when identity matters. If the index or the service is unavailable, fall back to a narrow filename or text search. Never rebuild the index or create a second cache.
3. **Read and attribute.** Read the relevant summaries and, for material claims, the accessible original. Attribute each claim to its source. Keep these separate:
   - the source's position;
   - the summary text;
   - your own inference;
   - the owner's own writing.

   State partial coverage. `verified` is review history, not proof of current truth.
4. **Answer** in the owner's language. Cite exact wiki paths or wikilinks, and name missing evidence instead of filling gaps.
5. **Live data.** Use external sources only when the question needs live data, and label them as external.
6. **No writes.** A comparison can be answered with per-source attribution and no writes. Saving an answer, a synthesis or a new page is a separate requested write: follow `ingest.md` bookkeeping, and keep it separate from the individual source summaries.

Grounding check: the answer comes from sources that were actually read, no excluded target is disclosed, and nothing was written.
