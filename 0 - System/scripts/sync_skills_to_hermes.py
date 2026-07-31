#!/usr/bin/env python3
"""
sync_skills_to_hermes.py — generate Hermes-format skills INSIDE the vault:
vault SKILL-*.md  ->  <vault>/0 - System/hermes-skills/<category>/<slug>/SKILL.md

The vault is the single source of truth. Each `0 - System/SKILL-*.md` is converted
into an agentskills.io-format SKILL.md under `0 - System/hermes-skills/`.
Hermes reads that folder LIVE via `skills.external_dirs` in ~/.hermes/config.yaml —
there is no copy in ~/.hermes/skills (a copy there would shadow the live one).

Claude Code keeps reading the original vault skills as-is (lazy-loaded via AGENTS.md);
this script only regenerates the Hermes-format rendition after a vault skill changes.

Privacy: a skill can be marked `skip` so it is never exported to Hermes. Use that for
anything that must stay local / Claude-Code-only rather than routed through Hermes'
gateway — see the `publish` entry below for the pattern.

Note: this script only ever WRITES. It never prunes, so deleting a skill here does not
remove an already-generated folder — delete that by hand.

Usage:
  python3 "0 - System/scripts/sync_skills_to_hermes.py"          # dry-run (default)
  python3 "0 - System/scripts/sync_skills_to_hermes.py" --apply  # write files
"""

import re
import sys
from pathlib import Path

# --- locate the vault (this script lives in <vault>/0 - System/scripts/) ---
SCRIPT_DIR = Path(__file__).resolve().parent
VAULT = SCRIPT_DIR.parent.parent
SKILLS_SRC = VAULT / "0 - System"
HERMES_SKILLS = SKILLS_SRC / "hermes-skills"

# --- per-skill config: slug, category, tags, one-line description, skip? ---
# `desc` is the frontmatter `description` Hermes uses to decide when to invoke a skill.
CONFIG = {
    "SKILL-ingest.md":    {"slug": "wiki-ingest",    "category": "knowledge", "tags": ["wiki", "ingest"],      "desc": "Compile an external source (URL/YouTube/raw file) into a wiki page and update the manifest/index/log."},
    "SKILL-resolve.md":   {"slug": "wiki-resolve",   "category": "knowledge", "tags": ["wiki", "resolve"],     "desc": "Update existing wiki pages for contradictions/reinforcements/additions after an ingest; refreshes last_compiled."},
    "SKILL-crosslink.md": {"slug": "wiki-crosslink", "category": "knowledge", "tags": ["wiki", "crosslink"],   "desc": "Add wikilinks automatically between wiki pages and notes (dry-run, then apply)."},
    "SKILL-query.md":     {"slug": "wiki-query",     "category": "knowledge", "tags": ["wiki", "query"],       "desc": "Answer questions from the wiki with citations, and offer to save newly learned knowledge."},
    "SKILL-vsearch.md":   {"slug": "vault-search",   "category": "knowledge", "tags": ["search", "semantic"],  "desc": "Semantic search across the vault by meaning rather than by keyword — crosses languages and reaches notes and topics too."},
    "SKILL-lint.md":      {"slug": "wiki-lint",      "category": "knowledge", "tags": ["wiki", "lint"],        "desc": "Validate wiki health: frontmatter, broken links, stale pages, missing sources."},
    "SKILL-status.md":    {"slug": "wiki-status",    "category": "knowledge", "tags": ["wiki", "status"],      "desc": "Show the state of the wiki — what is compiled, what is pending, what changed."},
    # Intentionally skipped: publishing performs git operations and a leak audit.
    # That is deep work for Claude Code, not something to route through an ambient agent.
    "SKILL-publish.md":   {"skip": True, "reason": "git + leak audit — Claude Code only, never Hermes."},
}

# Section headings -> the Hermes-recommended structure
HEADER_MAP = {
    "When to use": "When to Use",
    "Steps": "Procedure",
    "Pitfalls": "Pitfalls",
    "Common problems": "Pitfalls",
    "Verification": "Verification",
}

PRIVACY_NOTE = (
    "> Privacy: never touch `3 - Journal` or any file with `private: true`. "
    "The working directory must be the vault root.\n"
)


def strip_leading_title(body: str) -> str:
    """Drop a leading `# SKILL — X` heading; we render our own title."""
    lines = body.lstrip().splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        return "\n".join(lines[1:]).lstrip("\n")
    return body


def remap_headers(body: str) -> str:
    def repl(m):
        hashes, title = m.group(1), m.group(2).strip()
        return f"{hashes} {HEADER_MAP.get(title, title)}"
    return re.sub(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", repl, body, flags=re.MULTILINE)


def yaml_list(items):
    return "[" + ", ".join(items) + "]"


def build_skill_md(cfg: dict, source_body: str) -> str:
    body = remap_headers(strip_leading_title(source_body)).strip()
    desc = cfg["desc"].replace("\\", "\\\\").replace('"', '\\"')
    fm = (
        "---\n"
        f"name: {cfg['slug']}\n"
        f'description: "{desc}"\n'
        "version: 1.0.0\n"
        "platforms: [macos]\n"
        "metadata:\n"
        "  hermes:\n"
        f"    tags: {yaml_list(cfg['tags'])}\n"
        f"    category: {cfg['category']}\n"
        "---\n\n"
    )
    title = f"# {cfg['slug'].replace('-', ' ').title()}\n\n"
    return fm + title + PRIVACY_NOTE + "\n" + body + "\n"


def main():
    apply = "--apply" in sys.argv[1:]
    mode = "APPLY" if apply else "DRY-RUN (use --apply to write)"
    print(f"sync_skills_to_hermes — {mode}")
    print(f"  source: {SKILLS_SRC}")
    print(f"  target: {HERMES_SKILLS}\n")

    written, skipped, missing = 0, 0, 0
    for filename, cfg in CONFIG.items():
        src = SKILLS_SRC / filename
        if cfg.get("skip"):
            print(f"  SKIP    {filename}  — {cfg.get('reason', '')}")
            skipped += 1
            continue
        if not src.exists():
            print(f"  MISSING {filename}  (not found in vault)")
            missing += 1
            continue
        content = build_skill_md(cfg, src.read_text(encoding="utf-8"))
        dest = HERMES_SKILLS / cfg["category"] / cfg["slug"] / "SKILL.md"
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"  WROTE   {dest.relative_to(VAULT)}")
        else:
            print(f"  WOULD   {dest.relative_to(VAULT)}  ({len(content)} bytes)")
        written += 1

    print(f"\nDone. {written} synced, {skipped} skipped, {missing} missing.")
    if not apply:
        print("Re-run with --apply to write the files.")


if __name__ == "__main__":
    main()
