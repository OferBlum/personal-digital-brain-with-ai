# SKILL — Vector Search

## When to Use
Find permitted vault content by meaning: "where did I write about…", "what do I have on…", or related-link candidates for the librarian. The index is a locator, not a source of truth.

## Boundaries
Follow AGENTS.md and the vault map:
- **Private folder:** it does not exist for this skill. Never access, list, index or link it.
- **Folder-based privacy:** privacy is decided by folder only, and the legacy `private:` property is ignored.
- **Scanning and links:** never scan the vault root or follow symlinks.
- **Read-only search:** searching is read-only. Finding a file never authorizes editing it.

## Usage
Run from the vault root. `vault-python.sh` picks the interpreter and, inside Docker, the Ollama host:
```text
bash "0 - System/scripts/vault-python.sh" -B "0 - System/scripts/vsearch.py" "question" --json --k 8
```
`--json` returns a JSON array of permitted paths only, with no excerpts or scores. The default corpus is top-level Markdown in `7 - Wikipedia`, `2 - Notes` and `1 - Topics`. Use `--folder "<folder>"` only when the user asks to restrict the search. Related-link discovery stays cross-folder.

## Procedure
1. **Search** the main idea and, when useful, a distinct secondary idea. The shared index in `vector-out/` (generation `folder-boundary-v1`) checks folder and source-path boundaries before reading cached text. Older generations are never used.
2. **Read** the relevant candidates before answering or linking. Semantic similarity is not source identity or proof of a duplicate; exact title, author, IDs and `wiki_sources` decide identity.
3. **Fall back.** If the index or the local embedding service is unavailable, state the blocker and fall back to a targeted filename or text search inside the permitted folders. Never build a second cache or rebuild automatically. Weak or empty results do not prove that nothing exists, so try another phrasing.
4. **Cite** real files and distinguish the owner's writing from compiled summaries. For same-name files, use full vault-relative paths.

## Index maintenance
Refresh the index only when asked, or as an approved step of a content update. Use the existing `embed_index.py` / `reindex.sh` after reviewing their current code. Keep embeddings local and report the coverage and refresh status. There is only one shared index; no wiki-only copy.
