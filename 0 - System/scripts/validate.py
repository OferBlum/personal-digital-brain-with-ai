#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — health check + OKF v0.2 conformance. Read-only.

Covers three folders: 7 - Wikipedia, 2 - Notes, 1 - Topics.
Enforces the three axes of SCHEMA.md (subject / type / tags) and the OKF trust layer.

Default: prints and writes a report. With --hook: exits 2 if there are errors.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

REPORT = V.WIKI / "validation_report.md"
SCHEMA = V.SYS / "SCHEMA.md"
HOOK = "--hook" in sys.argv
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUS_VALUES = {"draft", "stable", "deprecated"}
ACTOR_RE = re.compile(r"^(human:|process:|[\w.\-]+/)?[\w.\-]+$")


# ---------- reading SCHEMA.md ----------

def _section(text, header):
    """The text between a `## header` heading and the next ## heading."""
    m = re.search(rf"^##\s+{re.escape(header)}.*?$(.*?)(?=^##\s|\Z)",
                  text, re.M | re.S)
    return m.group(1) if m else ""


def read_schema():
    """Returns (subjects, types, tags) — or Nones if there is no SCHEMA."""
    if not SCHEMA.exists():
        return None, None, None
    text = SCHEMA.read_text(encoding="utf-8")

    # subjects: only list lines `- [[X]] — description`. Blockquote notes don't count.
    subjects = {V.nfc(m.group(1).strip())
                for m in re.finditer(r"^-\s*\[\[([^\]]+)\]\]", _section(text, "subject"), re.M)}

    # type: only list lines `- \`x\` — description`
    types = {m.group(1) for m in re.finditer(r"^-\s*`([^`]+)`", _section(text, "type"), re.M)}

    # tags: everything in backticks in the section, up to the writing-rules subheading
    tags_sec = _section(text, "tags").split("### ")[0]
    tags = {V.nfc(m.group(1).strip()) for m in re.finditer(r"`([^`]+)`", tags_sec)}

    return (subjects or None), (types or None), (tags or None)


# ---------- checks ----------

def check(p, meta, kind, subjects, types, tags_allowed, md_index, errors, warns):
    name = V.nfc(p.stem)

    if not meta:
        errors.append((name, "no frontmatter"))
        return

    # --- type: the one field OKF mandates ---
    t = str(meta.get("type", "")).strip()
    if not t:
        errors.append((name, "missing type (required by OKF)"))
    elif types is not None and t not in types:
        errors.append((name, f"type not in SCHEMA: {t}"))

    # --- subject ---
    topic = meta.get("subject", "")
    if topic:
        inner = V.nfc(re.sub(r"[\[\]\"]", "", str(topic)).strip())
        if subjects is not None and inner and inner not in subjects:
            errors.append((name, f"subject not in SCHEMA: {inner}"))

    # --- tags ---
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(x).strip() for x in tags if str(x).strip()]
    for tg in tags:
        if tg.startswith("#"):
            errors.append((name, f"tag with a leading #: {tg}"))
        elif tags_allowed is not None and V.nfc(tg) not in tags_allowed:
            warns.append((name, f"tag not declared in SCHEMA: {tg}"))

    # --- the OKF trust layer ---
    # generated_by / generated_at are flat, never a nested map: Obsidian Properties
    # renders only flat values, and a nested map disappears into the `generated` row.
    if "generated" in meta:
        errors.append((name, "nested `generated` — split into generated_by and generated_at"))

    by = str(meta.get("generated_by", "") or "").strip()
    at = str(meta.get("generated_at", "") or "").strip()
    if by or at:
        if not by:
            errors.append((name, "generated_at without generated_by"))
        elif not ACTOR_RE.match(by):
            warns.append((name, f"generated_by in an unfamiliar format: {by}"))
        if at and not DATE_RE.match(at[:10]):
            warns.append((name, f"generated_at is not a date: {at}"))

    ver = meta.get("verified")
    if ver is not None and not isinstance(ver, list):
        errors.append((name, "verified must be a list"))

    st = str(meta.get("status", "")).strip()
    if st and st not in STATUS_VALUES:
        errors.append((name, f"invalid status: {st} (draft/stable/deprecated)"))

    # --- wiki-page specific ---
    ws = None
    if kind == "wiki":
        if "wiki" not in tags:
            warns.append((name, "tags without 'wiki'"))
        lc = str(meta.get("last_compiled", ""))
        if not lc:
            errors.append((name, "missing last_compiled"))
        elif not DATE_RE.match(lc):
            errors.append((name, f"invalid date: {lc}"))
        ws = meta.get("wiki_sources", None)
        if ws is None:
            warns.append((name, "no wiki_sources"))
        elif not isinstance(ws, list):
            errors.append((name, "wiki_sources is not a list"))

    # --- broken links (a subject declared in SCHEMA is not "broken") ---
    for entry in ([topic] if topic else []) + (ws if isinstance(ws, list) else []):
        inner = re.sub(r"[\[\]\"]", "", str(entry)).split("|")[0].strip()
        if not inner:
            continue
        short = V.nfc(inner.split("/")[-1])
        if subjects is not None and (V.nfc(inner) in subjects or short in subjects):
            continue
        status, _ = V.resolve_link(inner, md_index)
        if status == "missing":
            warns.append((name, f"broken link: {inner}"))


def main():
    subjects, types, tags_allowed = read_schema()
    md_index = V.all_md_index()
    errors, warns = [], []
    counts = {}

    sources = [("wiki", V.iter_wiki_pages()),
               ("note", V.iter_notes()),
               ("topic", V.iter_topics())]
    for kind, it in sources:
        n = 0
        for p, meta, _ in it:
            n += 1
            check(p, meta, kind, subjects, types, tags_allowed, md_index, errors, warns)
        counts[kind] = n

    scope = f"{counts.get('wiki',0)} wiki · {counts.get('note',0)} notes · {counts.get('topic',0)} topics"
    lines = ["---", "type: report", "subject:", "tags:", "  - report",
             "---", "# Validation report", "",
             f"Generated: {V.today()} · {scope} · 🔴 errors: {len(errors)} · 🟡 warnings: {len(warns)}", ""]
    if errors:
        lines += ["## 🔴 Errors", ""] + [f"- **{n}** — {m}" for n, m in errors] + [""]
    if warns:
        lines += ["## 🟡 Warnings", ""] + [f"- **{n}** — {m}" for n, m in warns] + [""]
    if not errors and not warns:
        lines.append("✅ All clean.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"🔴 errors: {len(errors)} · 🟡 warnings: {len(warns)} · {scope} · 📄 {V.rel(REPORT)}")
    for n, m in errors: print(f"   🔴 {n}: {m}")
    for n, m in warns:  print(f"   🟡 {n}: {m}")

    if HOOK and errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
