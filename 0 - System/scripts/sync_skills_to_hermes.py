#!/usr/bin/env python3
"""
sync_skills_to_hermes.py — generate Hermes-format skills INSIDE the vault:
vault SKILL-*.md  ->  <vault>/0 - System/hermes-skills/<category>/<slug>/SKILL.md

The vault is the single source of truth. The explicitly configured SKILL sources
are converted into agentskills.io-format files under `0 - System/hermes-skills/`.
Standalone skills in that directory are not rewritten by this script.
Hermes reads that folder LIVE via `skills.external_dirs` in ~/.hermes/config.yaml —
there is no copy in ~/.hermes/skills anymore (a copy there would shadow the live one).

Claude Code keeps reading the original vault skills as-is (lazy-loaded via AGENTS.md);
this script only regenerates the Hermes-format rendition after a vault skill changes.

Privacy: a skill can be marked `skip` so it is never exported to Hermes. Use that for
anything that must stay local / Claude-Code-only rather than routed through Hermes'
gateway — see the `publish` entry below for the pattern. Sources and destinations are
read through the shared no-follow reader (symlinks are refused); frontmatter is
never a reason to refuse. Excluded entries are never opened.

Usage:
  python3 "0 - System/scripts/sync_skills_to_hermes.py"          # dry-run (default)
  python3 "0 - System/scripts/sync_skills_to_hermes.py" --check  # exit 1 on drift, 2 on errors
  python3 "0 - System/scripts/sync_skills_to_hermes.py" --apply  # write files

Before --apply, reconcile generated-only edits back to their source. Unchanged
outputs are not rewritten; preflight errors prevent all planned writes.
"""

import argparse
import re
import sys
from pathlib import Path
import yaml

# --- locate the vault (this script lives in <vault>/0 - System/scripts/) ---
SCRIPT_DIR = Path(__file__).resolve().parent
VAULT = SCRIPT_DIR.parent.parent
SKILLS_SRC = VAULT / "0 - System"
HERMES_SKILLS = SKILLS_SRC / "hermes-skills"

# --- per-skill config: slug, category, tags, one-line description, skip? ---
# description is the frontmatter `description` Hermes uses to decide when to invoke.
CONFIG = {
    "SKILL-vsearch.md":   {"slug": "vault-search",   "category": "knowledge", "tags": ["search", "semantic"],  "desc": "Find permitted vault files by meaning with the shared local index — crosses languages and reaches notes and topics too."},
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
    "> Privacy: follow AGENTS.md. The private folder is off limits; privacy is folder-based. "
    "Local processing does not waive these restrictions. "
    "The working directory must be the vault root.\n"
)


def strip_leading_title(body: str) -> str:
    """Drop leading YAML frontmatter and a leading `# SKILL — X` heading.

    We render our own frontmatter and title, so a source that carries either
    (some do) would otherwise emit a duplicate
    block in the middle of the generated document.
    """
    body = body.lstrip()
    if body.startswith("---\n"):
        end = body.find("\n---", 3)
        if end != -1:
            body = body[end + 4:].lstrip("\n")
    lines = body.splitlines()
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


def read_permitted_text(path):
    """The no-follow reader shared with the vault pipeline."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from privacy_guard import read_public_text
    try:
        return read_public_text(path)
    except (OSError, ValueError):
        raise ValueError('Unavailable file') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare or regenerate vault-managed Hermes skills.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true", help="Write changed generated skills after reviewing drift.")
    modes.add_argument("--check", action="store_true", help="Read-only check: exit 1 on drift, 2 on errors.")
    parser.add_argument('--only', nargs='+', metavar='SKILL', help='Limit checks/writes to exact configured slugs or source filenames.')
    args = parser.parse_args(argv)
    selection = set(args.only or [])
    known = set(CONFIG) | {cfg['slug'] for cfg in CONFIG.values() if 'slug' in cfg}
    if selection - known:
        print('ERROR: unknown skill selection; no files read or written.')
        return 2
    mode = "APPLY" if args.apply else "CHECK" if args.check else "DRY-RUN"
    print(f"sync_skills_to_hermes — {mode}")
    print(f"  source: {SKILLS_SRC}")
    print(f"  target: {HERMES_SKILLS}\n")

    plans = []
    skipped = errors = 0
    for filename, cfg in CONFIG.items():
        if selection and filename not in selection and cfg.get('slug') not in selection:
            continue
        if cfg.get("skip"):
            skipped += 1
            continue
        src = SKILLS_SRC / filename
        try:
            source_body = read_permitted_text(src)
        except (OSError, UnicodeError, ValueError):
            print('  ERROR   unavailable source; no excluded identifier disclosed')
            errors += 1
            continue
        content = build_skill_md(cfg, source_body)
        dest = HERMES_SKILLS / cfg["category"] / cfg["slug"] / "SKILL.md"
        try:
            if any(part.is_symlink() for part in (dest, *dest.parents)):
                raise ValueError("Unavailable file")
            existing = read_permitted_text(dest) if dest.exists() else None
        except (OSError, UnicodeError, ValueError):
            print('  ERROR   unavailable destination; no excluded identifier disclosed')
            errors += 1
            continue
        plans.append((cfg["slug"], dest, content, existing != content))

    changed = sum(plan[3] for plan in plans)
    current = len(plans) - changed
    written = 0
    for slug, dest, content, differs in plans:
        if args.apply and differs and not errors:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            if dest.read_text(encoding="utf-8") != content:
                raise RuntimeError(f"Write verification failed for {slug}")
            written += 1
            label = "WROTE"
        else:
            label = "DRIFT" if differs else "CURRENT"
        print(f"  {label:7} {slug}")

    print(f"\nChecked {len(plans)}: {current} current, {changed} different, {skipped} excluded, {errors} errors; {written} written.")
    if errors:
        print("No planned writes applied because preflight failed.")
        return 2
    if not args.apply and changed:
        print("Preserve generated-only edits in the source before using --apply.")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
