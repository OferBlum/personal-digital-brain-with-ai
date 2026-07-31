---
description: Update the semantic index after adding or editing files in the vault
allowed-tools: Bash(bash "0 - System/scripts/reindex.sh":*)
---

Run `bash "0 - System/scripts/reindex.sh"`.

Report briefly: which files were added (`+`), changed (`~`) or deleted (`-`) — by name,
exactly as the script printed them — and how many chunks are now in the index.

If the script said the index is up to date, say so in one line and run nothing else.
If it failed because Ollama isn't running, pass the message through as-is and don't try
to work around it.
