# Resolve: correct or extend existing summaries

Use when the owner asks to fix, extend or reconcile summaries against new evidence. Load `source-summaries.md`.

1. **Locate.** Find the requested summaries through the index and a scoped search. Identify the original source, then read the relevant accessible content and the new evidence.
2. **Classify.** Decide which case applies:
   - **A mis-summary of the same source:** fix the representation within scope.
   - **A different source with another position:** it must not overwrite the original author's position or be blended into that summary. Keep it as a separate summary, or as a clearly labelled comparison if one was requested.
3. **`provenance: ambiguous`.** Use it only for a real unresolved interpretive conflict, not for a mere lack of independent corroboration.
4. **Preview and apply.** Preview the exact pages to change. Edit only the requested scope; related notes stay read-only.
5. **Update the metadata:** the body, the real `wiki_sources`, `last_compiled` and `generated_at` (dates from a tool). Keep human verification history, and flag material changes made after a review.
6. **Bookkeeping.** Patch the affected index row and append a log entry, as in `ingest.md`. Do not rebuild the manifest, run a crosslink sweep, or edit notes.
7. **Verify.** Compare the audit before and after. Check fidelity against the accessed source and keep the recap consistent with the detail.

Report the changed files, the unresolved conflicts, and the search index state.
