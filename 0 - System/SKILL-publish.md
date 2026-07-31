# SKILL — Publish

## When to use
When asked to update the public repo: "update the git repo", "publish", `/publish`.

The public repo is a **translated, sanitized mirror of the system layer only** — never the
content. Its working copy lives outside the vault.

## Why this skill exists
There was no sync mechanism: every update was a hand translation, and the mirror drifted
silently for weeks before anyone noticed. The policy now lives in
`0 - System/publish-manifest.yaml` as **data**, two scripts read it, and this skill is only
the procedure around them.

## Hard rules
1. **Allowlist.** Nothing is published unless it matches `publish:` in the manifest. The
   content folders are absent from that list by construction, so they cannot leak through an
   oversight.
2. **Never commit, never push.** Finish at `git add` and report. The owner pushes.
3. **No non-Latin script in the mirror.** Regex ranges are written as `\uXXXX` escapes
   (see `autolink.py`, `merge_nodes.py`) or built from bytes (`list_tags.sh`).
4. **`placeholders:` and `sanitized:` are never overwritten.** They are hand-written on purpose.
5. **The audit is the gate.** If `publish_check.py` doesn't end in CLEAN, don't stage anything.

## Steps

### 1. What drifted
```bash
python3 "0 - System/scripts/publish_check.py"
```
Prints three sections: inventory gaps, structural drift (an `ast` signature for code;
headings + frontmatter keys for markdown), and the leak audit. Filenames are printed **only**
for the system layer — content folders report a count, because those filenames are private
note titles.

### 2. Mechanical port
```bash
python3 "0 - System/scripts/publish_port.py"           # dry-run
python3 "0 - System/scripts/publish_port.py" --apply   # only files missing from the mirror
```
Creates **new files only**. A file that already exists in the mirror holds hand-translated
prose, so the script reports it rather than clobbering it. `--overwrite` exists but is almost
never right.

### 3. Manual translation — the part the script won't do
For every `NEEDS-TRANSLATION` line and every file in the "differ, NOT overwritten" list:
translate comments, docstrings and output strings. Unreviewed machine translation should not
ship to a public repo.

### 4. Prose and docs
If a capability changed and not just code, update `README.md`, `SYSTEM-GUIDE.md`, `AGENTS.md`,
`skills-index.md` and `vault-map.md`. The README's script table must cover every published script.

### 5. The gate
```bash
python3 "0 - System/scripts/publish_check.py"
```
Must end in `✅ CLEAN`. Zero leaks, zero non-Latin characters, zero forbidden files.

### 6. Stage only
```bash
git add -A
git status --short
git diff --cached --stat
```
One `git add -A` at the very end, so a single `git reset` restores the baseline. Read the full
diff for `SCHEMA.md`, `me.md`, `memories/` and `privacy_guard.py`.

**Stop here.** Report what changed and what passed the audit. **No commit, no push.**

## Pitfalls
- **A small diff hides a semantic rewrite.** `append_log.py` differed by 16 lines but had
  changed the frontmatter it writes. Always re-derive from the vault; never patch the mirror.
- **`vector-out/` and `.graphifyignore` enumerate real note paths.** They are gitignored for a
  privacy reason, not just because they're derived. Never run `embed_index.py` inside the mirror.
- **`sync_skills_to_hermes.py` never prunes.** Deleted a skill? Confirm the generated folder is
  gone too.
- **`validate.py` writes `validation_report.md`.** Gitignored, but delete it after a run and
  re-check `git status`.
- **The guard will block you.** Writing a file that contains the journal folder name as a literal
  string is refused by `privacy_guard.py` — correct behaviour, not a bug. Don't write that string.

## Verification
`publish_check.py` ends CLEAN · `git log --oneline -1` still points at the previous commit
(nothing was committed) · `git ls-files --cached` contains no path from `must_be_absent`.
