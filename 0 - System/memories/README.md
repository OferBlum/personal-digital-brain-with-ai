# Agent memory — lives in the vault, not in the agent

Hermes' persistent memory (`USER.md` — user profile, `MEMORY.md` — working memory) lives **here**, inside the vault, so the memory survives switching agents. Hermes' hardcoded memory path is satisfied with a symlink:

```bash
mv ~/.hermes/memories/USER.md ~/.hermes/memories/MEMORY.md "<vault>/0 - System/memories/"
rmdir ~/.hermes/memories
ln -s "<vault>/0 - System/memories" ~/.hermes/memories
```

Format: Hermes parses these files as `§`-separated cards — do NOT add vault frontmatter. Content limits and toggles are configured under `memory:` in `~/.hermes/config.yaml`; the path itself is not configurable, hence the symlink.

The two files here are **placeholder templates** — the real ones contain personal data and are never committed.

Notes:
- If the vault is on iCloud, keep this folder always-downloaded ("Optimize Mac Storage" can evict files mid-session).
- To swap Hermes for another agent: point (or symlink) the new agent's memory location at this folder.
