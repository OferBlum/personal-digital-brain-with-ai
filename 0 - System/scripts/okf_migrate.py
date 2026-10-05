#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
okf_migrate.py — one-time migration of the frontmatter to the OKF v0.2 standard.

Adds to every content page:
  type       — the new axis (required by OKF). Values are defined in SCHEMA.md
  generated_by / generated_at — who produced the file and when (the OKF trust layer)

And straightens out what drifted over time:
  • tags with a leading `#` → without one (Bases treats `ai` and `#ai` as two different tags)
  • scattered creation dates (created / date created / Updated / date updated) → `created`
  • subjects that don't exist in SCHEMA → see SUBJECT_REMAP below

Does not touch: `status` (the OKF default is `stable`) or `verified` (absent = unverified).
Those are written only when they genuinely differ from the default — see okf_verify.py.

*** Touches frontmatter only, never the body of the file. ***
That is what preserves graphify's semantic cache: it keys on the body alone, so
re-indexing after the migration costs zero LLM calls.

Usage:
    python3 "0 - System/scripts/okf_migrate.py"           # dry-run (the default)
    python3 "0 - System/scripts/okf_migrate.py" --apply   # write, after a backup

Set OKF_ACTOR to your own identity (default: human:me).
"""
import os, sys, re, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

ACTOR = os.environ.get("OKF_ACTOR", "human:me")

# --- type mapping ------------------------------------------------------------

# `4 - Templates/` is deliberately absent: a template's frontmatter *is* what gets
# copied into the new file, so a template must carry the type it produces (note),
# not `template`. Templates are edited by hand.
FOLDER_TYPE = {
    "7 - Wikipedia": "wiki-page",
    "2 - Notes":     "note",
    "1 - Topics":    "topic-hub",
}

# Subjects that pointed at something not in SCHEMA → where they move to.
# Add your own entries here: the right-hand side should be the subject that the
# equivalent note already uses, so the remap is a correction rather than a guess.
# The two entries below are structural — `index.md` and `log.md` are catalogs,
# not content about a life domain, so they carry `type` and no subject at all.
SUBJECT_REMAP = {
    "[[Wiki Index]]": "",
    "[[Wiki Log]]":   "",
}

DATE_ALIASES = ["created", "Created", "date created", "Updated", "date updated"]


def page_type(path, meta):
    name = V.nfc(path.name)
    if path.parent == V.WIKI:
        if name == "index.md":
            return "index"
        if name == "log.md":
            return "log"
        if name in V.NON_CONTENT:
            return None      # hand-written docs in the wiki folder — not a compiled page
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if "report" in [str(t).lstrip("#") for t in tags]:
            return "report"
        return "wiki-page"
    for folder, t in FOLDER_TYPE.items():
        if (V.VAULT / folder) == path.parent:
            return t
    return None


def generated_for(path, meta, ptype):
    """Who produced it and when. We don't invent a model name we don't know —
    the compile pipeline is `process:ingest`.

    Returns (by, at) as two flat values, not a nested map: Obsidian Properties
    renders only flat values, and a map like generated: {by, at} shows `by` and
    `at` inside the `generated` row instead of each on its own line.
    """
    if ptype in ("index", "log", "report", "template", "checklist"):
        return None                      # produced by a script that writes its own header
    if ptype == "wiki-page":
        at = str(meta.get("last_compiled") or "").strip()
        return ("process:ingest", at) if at else None
    # note / topic-hub — your own ideas
    at = ""
    for k in DATE_ALIASES:
        if meta.get(k):
            at = str(meta[k]).strip()[:10]
            break
    # Without a date the trust layer is incomplete — better no field than half a field
    return (ACTOR, at) if at else None


def iter_targets():
    for folder in list(FOLDER_TYPE):
        root = V.VAULT / folder
        if not root.exists():
            continue
        for p in sorted(root.glob("*.md")):        # not recursive — raw/ is immutable
            if V.is_forbidden(p) or V.nfc(p.name).startswith(V.SYSTEM_PREFIX):
                continue
            meta, body = V.read_page(p)
            if not meta:
                continue                           # a file with no frontmatter — leave it alone
            yield p, meta, body


def migrate(meta, path):
    """Returns (new_meta, [change descriptions])."""
    meta = dict(meta)
    changes = []

    ptype = page_type(path, meta)
    if ptype and meta.get("type") != ptype:
        if meta.get("type"):
            changes.append(f"type: {meta['type']} → {ptype}")
        else:
            changes.append(f"type: + {ptype}")
        meta["type"] = ptype

    # tags: strip a leading #, no duplicates, no empties
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    clean, seen = [], set()
    for t in tags:
        t = str(t).strip().lstrip("#").strip()
        if t and t not in seen:
            seen.add(t)
            clean.append(t)
    if clean != [str(t) for t in tags]:
        stripped = [str(t) for t in tags if str(t).strip().startswith("#")]
        if stripped:
            changes.append(f"tags: stripped # from {', '.join(stripped)}")
        elif len(clean) != len(tags):
            changes.append("tags: removed empty/duplicate values")
    if clean or "tags" in meta:
        meta["tags"] = clean

    # a subject that doesn't exist in SCHEMA
    subj = str(meta.get("subject") or "").strip()
    if subj in SUBJECT_REMAP:
        new = SUBJECT_REMAP[subj]
        changes.append(f"subject: {subj} → {new or '(empty)'}")
        meta["subject"] = new

    # creation dates → a single `created`
    extra = [k for k in DATE_ALIASES[1:] if k in meta]
    if extra:
        if not meta.get("created"):
            meta["created"] = meta[extra[0]]
        for k in extra:
            meta.pop(k, None)
        changes.append(f"dates: consolidated into `created` (removed {', '.join(extra)})")

    meta.pop("generated", None)          # the old nested form, if any survived
    gen = generated_for(path, meta, ptype)
    if gen:
        by, at = gen
        if (meta.get("generated_by"), meta.get("generated_at")) != (by, at):
            changes.append(f"generated_by/at: + {by}")
            meta["generated_by"], meta["generated_at"] = by, at

    if ptype == "index" and meta.get("okf_version") != "0.2":
        meta["okf_version"] = "0.2"
        changes.append("okf_version: + 0.2")

    return meta, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write (otherwise dry-run)")
    args = ap.parse_args()

    planned, untouched = [], 0
    for p, meta, body in iter_targets():
        new_meta, changes = migrate(meta, p)
        if not changes:
            untouched += 1
            continue
        planned.append((p, new_meta, body, changes))

    print(f"🔍 {'writing' if args.apply else 'preview (dry-run)'} — "
          f"{len(planned)} files to change, {untouched} already conformant\n")
    for p, _, _, changes in planned:
        print(f"  📄 {V.rel(p)}")
        for c in changes:
            print(f"     • {c}")

    if not args.apply:
        print(f"\nℹ️  Nothing was written. For a real run: --apply")
        return

    if not planned:
        return
    dest = V.backup([p for p, _, _, _ in planned], "okf")
    for p, new_meta, body, _ in planned:
        p.write_text(V.render_page(new_meta, body), encoding="utf-8")
    print(f"\n✅ Wrote {len(planned)} files. Backup: {V.rel(dest)}")


if __name__ == "__main__":
    main()
