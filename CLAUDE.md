# CLAUDE.md — The Vault (Claude Code layer)

The canonical, agent-agnostic instructions live in `AGENTS.md` — that file is the single source of truth for privacy rules, vault structure, frontmatter, skills, and conventions:

@AGENTS.md

## Claude Code specific

- Wiki compile/maintenance operations (ingest, resolve, crosslink, lint, status, YouTube queue) → delegate to the `wiki-librarian` subagent (`.claude/agents/wiki-librarian.md`; canonical prompt: `0 - System/agents/wiki-librarian.md`).
- Privacy is enforced in code by ONE canonical guard: `0 - System/scripts/privacy_guard.py`. `.claude/settings.json` registers a PreToolUse hook (`.claude/privacy-guard.py`) that is a thin wrapper around it (`--mode claude`, fails closed); `~/.hermes/agent-hooks/privacy-guard.py` is the same wrapper for Hermes (`--mode hermes`, fails open). Exactly one rule, folder-only: the private folder's name anywhere in a tool payload is blocked; the folder is never read nor listed (no Glob/`ls`/recursive scan of it — the vault-root `.ignore` keeps Grep/Glob out). The `private: true` flag is retired and grants nothing. **There is no `_` rule** — `_` files are generated, not secret. Verify with `python3 "0 - System/scripts/privacy_guard.py" --selftest`.
