# Audit: health check, status and quality review (read-only)

Use for "check the wiki", "wiki status", "what's pending", lint, or a quality review. The whole procedure is read-only.

## Structural check

1. Run the auditor from the vault root (see `SKILL.md` → Running the tools). It prints JSON and writes nothing.
2. Report these separately:
   - actual page count and index coverage;
   - structural errors;
   - unavailable body or source targets;
   - other warnings.

   Count actual accepted pages, not manifest history. The page total is not a count of distinct sources or of verified summaries.
3. An unavailable target may be non-Markdown, excluded or out of scope. Do not remove or "fix" it blindly. Many `[[raw/…]]` source warnings come from a known resolver quirk and are acceptable.
4. Do not run `validate.py` or `wiki_sources_report.py` for a review, because they write report files. Generating a report is a separate, requested write.

## Status and pending sources

1. If pending work is requested, inspect only the permitted raw metadata, the public manifest and the YouTube queue, using explicit folders.
2. A source missing from the manifest is a candidate, not proof that it was never summarized. Check source identity and the actual `wiki_sources` first.
3. The manifest has no content hashes, so source changes cannot be detected from dates. State that limit.
4. Ask whether to process specific candidates. Never fetch, compile, mark queue rows, refresh the index or trim the cache on your own.

## Quality review

On request, follow `source-summaries.md` → Read-only quality review for a scoped sample, comparing each summary against its accessible source. A single-source summary, or a missing optional `## Related` section, is not a defect. If the original is unavailable, fidelity is unverified.

## Output

Report:
- real counts from the audit;
- findings with public paths, severity and evidence;
- the untested scope;
- proposed scoped fixes with a rollback plan.

Never perform the fixes during a review.
