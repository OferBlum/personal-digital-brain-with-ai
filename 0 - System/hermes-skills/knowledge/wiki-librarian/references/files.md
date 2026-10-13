# Files: organize requested notes and files

Use for renaming, moving, merging, archiving or tidying an explicitly requested set of permitted files. For substantial prose edits, also load `personal-note-editing`.

1. **Scope.** State the mode and the exact paths. Inventory only that scope, checking each file's header first.
2. **Preview.** Show a table with the columns original path → new path or action → reason → affected links. Find inbound links within the relevant permitted folders. Do not scan the root or expose excluded targets.
3. **Safety checks.** Check for collisions, target-folder permissions and relative link behaviour. Never overwrite a destination. Never merge similar files without reading both; similarity is only a candidate, not proof of a duplicate.
4. **Approval.** The level of approval depends on the request:
   - **Explicit request** ("rename X to Y"): it authorizes that change plus the disclosed link repairs.
   - **Vague request** ("organize this"): propose a plan first and wait.

   In both cases, back up the exact targets to `7 - Wikipedia/.backup/<timestamp>-<label>/`.
5. **Execute.** Use file tools for content edits. For an actual rename or move, use a filesystem command with the exact old and new paths and no traversal. Preserve the body, metadata, task history, assets and raw sources, and do not rewrite the voice during a structural change.
6. **Repair links.** Repair the approved inbound wikilinks, keeping aliases and anchors and leaving code and unrelated text untouched. Do not add wiki metadata to human notes, and do not move files into the wiki because of their tags.
7. **Verify.** Check that:
   - the new path exists, and for a move the old path is gone;
   - nothing was overwritten;
   - content is preserved where intended;
   - the repaired links resolve.

   Report every changed file and the backup location.
