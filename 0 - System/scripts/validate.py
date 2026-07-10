#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — health check for the wiki pages. Read-only.
Default: prints + writes a report. With --hook: exits with code 2 on errors
(for wiring as a hook).
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

REPORT = V.WIKI / "validation_report.md"
SCHEMA = V.SYS / "SCHEMA.md"
HOOK = "--hook" in sys.argv
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def allowed_subjects():
    if not SCHEMA.exists():
        return None
    subs = set()
    for m in re.finditer(r"\[\[([^\]]+)\]\]", SCHEMA.read_text(encoding="utf-8")):
        subs.add(V.nfc(m.group(1).strip()))
    return subs


def raw_fm_lines(path):
    fm, _ = V.split_frontmatter(Path(path).read_text(encoding="utf-8"))
    return fm or []


def main():
    subs = allowed_subjects()
    md_index = V.all_md_index()
    errors, warns = [], []

    for p, meta, _ in V.iter_wiki_pages():
        name = V.nfc(p.stem)
        if not meta:
            errors.append((name, "no frontmatter")); continue

        # subject
        topic = meta.get("subject", "")
        if topic:
            inner = V.nfc(re.sub(r"[\[\]\"]", "", str(topic)).strip())
            if subs is not None and inner and inner not in subs:
                errors.append((name, f"subject not in SCHEMA: {inner}"))
        # tags includes wiki
        tags = meta.get("tags", [])
        if isinstance(tags, str): tags = [tags]
        if "wiki" not in tags:
            warns.append((name, "tags missing 'wiki'"))
        # last_compiled
        lc = str(meta.get("last_compiled", ""))
        if not lc:
            errors.append((name, "missing last_compiled"))
        elif not DATE_RE.match(lc):
            errors.append((name, f"invalid date: {lc}"))
        # wiki_sources is a list
        ws = meta.get("wiki_sources", None)
        if ws is None:
            warns.append((name, "no wiki_sources"))
        elif not isinstance(ws, list):
            errors.append((name, "wiki_sources is not a list"))
        # quotes around wikilinks in YAML
        for ln in raw_fm_lines(p):
            if "[[" in ln and '"' not in ln:
                errors.append((name, f"unquoted wikilink in YAML: {ln.strip()}"))
        # broken links in subject/sources (a subject that exists in SCHEMA isn't "broken")
        for entry in ([topic] if topic else []) + (ws if isinstance(ws, list) else []):
            inner = re.sub(r"[\[\]\"]", "", str(entry)).split("|")[0].strip()
            if not inner: continue
            short = V.nfc(inner.split("/")[-1])
            if subs is not None and (V.nfc(inner) in subs or short in subs):
                continue
            status, _ = V.resolve_link(inner, md_index)
            if status == "missing":
                warns.append((name, f"broken link: {inner}"))

    lines = ["---", "tags: [report]", "private: false", "---", "# Validation report", "",
             f"Generated: {V.today()} · 🔴 errors: {len(errors)} · 🟡 warnings: {len(warns)}", ""]
    if errors:
        lines += ["## 🔴 Errors", ""] + [f"- **{n}** — {m}" for n, m in errors] + [""]
    if warns:
        lines += ["## 🟡 Warnings", ""] + [f"- **{n}** — {m}" for n, m in warns] + [""]
    if not errors and not warns:
        lines.append("✅ All good.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"🔴 errors: {len(errors)} · 🟡 warnings: {len(warns)} · 📄 {V.rel(REPORT)}")
    for n, m in errors: print(f"   🔴 {n}: {m}")
    for n, m in warns:  print(f"   🟡 {n}: {m}")

    if HOOK and errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
