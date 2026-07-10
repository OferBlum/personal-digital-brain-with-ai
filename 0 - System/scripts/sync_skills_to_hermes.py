#!/usr/bin/env python3
"""
sync_skills_to_hermes.py — one-way sync: vault SKILL-*.md  ->  ~/.hermes/skills/

The vault is the single source of truth. Each `0 - System/SKILL-*.md` is converted
into a Hermes-compatible SKILL.md (agentskills.io format) under
`~/.hermes/skills/<category>/<slug>/SKILL.md`.

Claude Code keeps reading the original vault skills as-is (lazy-loaded via CLAUDE.md);
this script only produces the Hermes copy. Editing the vault skill + re-running sync
keeps Hermes up to date — no duplicate maintenance.

Privacy: journal-summary is intentionally NOT synced (it touches the personal journal
and must stay local/Claude-Code-only, never routed through Hermes' Telegram gateway).

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
HERMES_SKILLS = Path.home() / ".hermes" / "skills"

# --- per-skill config: slug, category, tags, one-line description, skip? ---
# description is the frontmatter `description` Hermes uses to decide when to invoke.
CONFIG = {
    "SKILL-ingest.md":                 {"slug": "wiki-ingest",             "category": "knowledge", "tags": ["wiki", "ingest"],           "desc": "Compile an external source (URL/YouTube/raw) into a wiki page + update manifest/index/log."},
    "SKILL-resolve.md":                {"slug": "wiki-resolve",            "category": "knowledge", "tags": ["wiki", "resolve"],          "desc": "Update existing wiki pages for contradictions/reinforcements/additions after an ingest; updates last_compiled."},
    "SKILL-crosslink.md":              {"slug": "wiki-crosslink",          "category": "knowledge", "tags": ["wiki", "crosslink"],        "desc": "Automatically add wikilinks between wiki pages (dry-run then apply)."},
    "SKILL-query.md":                  {"slug": "wiki-query",              "category": "knowledge", "tags": ["wiki", "query"],            "desc": "Answer questions from the wiki with citations and offer to save new knowledge."},
    "SKILL-lint.md":                   {"slug": "wiki-lint",               "category": "knowledge", "tags": ["wiki", "lint"],             "desc": "Wiki health validation: frontmatter, broken links, stale pages, missing sources."},
    "SKILL-status.md":                 {"slug": "wiki-status",             "category": "knowledge", "tags": ["wiki", "status"],           "desc": "Show the wiki's state — what was compiled, what's pending, what changed."},
    "SKILL-investment-agent.md":       {"slug": "investment-agent",        "category": "investing", "tags": ["investing", "agent"],       "desc": "Investment desk head: quick-check on a ticker, sizing, and routing to sub-skills (IBKR + Playwright)."},
    "SKILL-investment-fundamental.md": {"slug": "investment-fundamental",  "category": "investing", "tags": ["investing", "fundamental"], "desc": "Deep hedge-fund-style fundamental research: 5 layers, 26 dimensions."},
    "SKILL-investment-graph.md":       {"slug": "investment-graph",        "category": "investing", "tags": ["investing", "technical"],   "desc": "Quantitative technical analysis: EMA, ATR, RSI, MACD, volume and chart patterns."},
    "SKILL-investment-stop-loss.md":   {"slug": "investment-stop-loss",    "category": "investing", "tags": ["investing", "risk"],        "desc": "Precise stop-loss calculation from EMA150/ATR/Swing-Lows: Stop = Anchor − 1.5×ATR."},
    "SKILL-investment-deep-analyze.md":{"slug": "investment-deep-analyze", "category": "investing", "tags": ["investing", "orchestrator"],"desc": "Full analysis: runs fundamental+technical+stop and synthesizes with a 14-point entry checklist."},
    "SKILL-Nutrition-Advisor.md":      {"slug": "nutrition-advisor",       "category": "personal",  "tags": ["nutrition"],                "desc": "Nutrition coach based on the profile, macro targets and the food bank."},
    "SKILL-personal-stylist.md":       {"slug": "personal-stylist",        "category": "personal",  "tags": ["style"],                    "desc": "Outfit advice from the existing wardrobe; spots gaps and considers the weather."},
    # Intentionally skipped for privacy — journal stays local, never in Hermes:
    "SKILL-journal-summary.md":        {"skip": True, "reason": "Touches the personal journal — stays local Ollama/Claude-Code, never routed through Hermes/Telegram."},
}

# Legacy section headers -> Hermes-recommended structure
HEADER_MAP = {
    "When to use": "When to Use",
    "Steps": "Procedure",
    "Common problems": "Pitfalls",
}

PRIVACY_NOTE = (
    "> Privacy: never touch `3 - Journal` or `private: true` files. "
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
        rel = dest.relative_to(Path.home())
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"  WROTE   ~/{rel}")
        else:
            print(f"  WOULD   ~/{rel}  ({len(content)} bytes)")
        written += 1

    print(f"\nDone. {written} synced, {skipped} skipped, {missing} missing.")
    if not apply:
        print("Re-run with --apply to write the files.")


if __name__ == "__main__":
    main()
