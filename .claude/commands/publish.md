---
description: Update the public mirror from the vault's system layer — drift report, port, leak audit, staging only
allowed-tools: Bash(python3 "0 - System/scripts/publish_check.py":*), Bash(python3 "0 - System/scripts/publish_port.py":*), Bash(git -C *:*), Read, Edit, Write, Glob, Grep
---

Read `0 - System/SKILL-publish.md` and follow the procedure in it.

Always start with `python3 "0 - System/scripts/publish_check.py"` and report what drifted:
how many files are missing from the mirror, what differs structurally, and whether anything leaks.

**Stop after `git add`.** No commit and no push — the owner pushes.
If `publish_check.py` does not end in `✅ CLEAN`, do not stage at all; report what is blocking.
