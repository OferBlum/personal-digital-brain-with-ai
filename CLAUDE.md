# CLAUDE.md — The Vault (Claude Code layer)

The canonical, agent-agnostic instructions live in `AGENTS.md` — that file is the single source of truth for privacy rules, vault structure, frontmatter, skills, and conventions:

@AGENTS.md

## Claude Code specific

- Wiki compile/maintenance operations (ingest, resolve, crosslink, lint, status, YouTube queue) → delegate to the `wiki-librarian` subagent (`.claude/agents/wiki-librarian.md`; canonical prompt: `0 - System/agents/wiki-librarian.md`).
- Privacy is also enforced in code: `.claude/settings.json` registers a PreToolUse hook (`.claude/privacy-guard.py`), which is a thin wrapper around the canonical guard at `0 - System/scripts/privacy_guard.py`. It blocks any tool call touching `3 - Journal`, and any call naming a single file that has `private: true`. The Claude Code wrapper fails **closed** (a guard it cannot load refuses the call); the Hermes wrapper at `~/.hermes/agent-hooks/privacy-guard.py` fails **open**, so an ambient run never deadlocks. There is no `_` rule — `_` files are generated, not secret. Verify with `python3 "0 - System/scripts/privacy_guard.py" --selftest`.
