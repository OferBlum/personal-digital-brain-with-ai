# SKILL — Publish

## When to Use
When asked to update the public repo: "update the git repo", "publish", `/publish`.

The public repo is a **English-translated, sanitized mirror** of the system layer only:
the repo and its working copy (outside the vault) are set in `publish-manifest.yaml`.

## Why This Skill Exists
There was no sync mechanism — every update was a manual translation, and the mirror silently drifted
for three weeks. The policy itself now lives in `0 - System/publish-manifest.yaml` as **data**, and two
scripts read it. This skill is only the procedure around them.

## Hard Rules
1. **Allowlist.** Nothing is published unless it's under `publish:` in the manifest. The content
   folders (topics, notes, the journal, tables, images) aren't there in the first place, so they
   can't leak by accident.
2. **Never commit and never push.** Finish at `git add` and report. The owner pushes.
3. **No Hebrew in the mirror.** Zero Hebrew characters in the public repo. Regex ranges are written as
   `\uXXXX` (see `autolink.py`, `merge_nodes.py`) or built from bytes (`list_tags.sh`).
4. **`placeholders:` and `sanitized:` are never overwritten.** They were written by hand on purpose.
5. **The audit is the gate.** If `publish_check.py` doesn't return CLEAN — don't stage.

## Procedure

### 1. What changed
```bash
python3 "0 - System/scripts/publish_check.py"
```
Prints three parts: inventory gaps, structural drift (`ast` signature for code, headings + frontmatter
keys for markdown), and a leak audit. Filenames are printed **only** for the system layer; the content
folders are reported as a count only, because the names there are private note titles.

### 2. Mechanical port
```bash
python3 "0 - System/scripts/publish_port.py"           # dry-run
python3 "0 - System/scripts/publish_port.py" --apply   # only files missing from the mirror
```
Creates **new files only**. A file that already exists in the mirror contains hand-translated prose —
the script reports it and does not overwrite it. `--overwrite` exists but is almost always wrong.

### 3. Manual translation — the part the script doesn't do
For every file in the `NEEDS-TRANSLATION` list and every file in the "differ, NOT overwritten" list:
translate comments, docstrings and output strings to English. Machine translation nobody read doesn't
go to a public repo.
Remember the frontmatter keys in `fm_key_map` (subject, background, private) and all the folder names.

### 4. Prose and documents
If a capability changed and not just code — update `README.md`, `SYSTEM-GUIDE.md`, `AGENTS.md`,
`skills-index.md`, `vault-map.md` in the mirror. The scripts table in the README must cover every
published script.

### 5. The gate
```bash
python3 "0 - System/scripts/publish_check.py"
```
Must end with `✅ CLEAN`. If not — fix and repeat. Zero leaks, zero Hebrew, zero forbidden files.

### 6. Staging only
```bash
cd <mirror working copy>
git add -A
git status --short
git diff --cached --stat
```
`git add -A` once at the end, so a single `git reset` undoes everything.
Read the full diff of `SCHEMA.md`, `me.md`, `memories/`, and `privacy_guard.py`.

**Stop here.** Report what was edited and what passed the audit. **No commit, no push.**

## Pitfalls
- **A small diff can hide a semantic rewrite.** `append_log.py` differed by only 16 lines but changed
  the frontmatter it writes. Always re-derive from the vault; don't patch the mirror.
- **`vector-out/` and `.graphifyignore` enumerate real note paths.** They're in `.gitignore` for
  privacy reasons, not just because they're generated. Don't run `embed_index.py` inside the mirror.
- **`sync_skills_to_hermes.py` doesn't delete.** Deleted a skill? Make sure the generated folder was
  deleted too.
- **`validate.py` writes `validation_report.md`.** It's gitignored, but delete it after a run and
  check `git status` again.
- **The guard blocks you too.** Writing a file that contains the journal folder's name as a string
  will be blocked by `privacy_guard.py` — that's correct behavior, not a bug. Just don't write that
  string.

## Verification
`publish_check.py` ends with CLEAN · `git log --oneline -1` in the mirror still points at the previous
commit (no commit was made) · `git ls-files --cached` contains no path from `must_be_absent`.

## Output
Respond in the user's language.
