#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
subject_candidates.py — finds candidates for promotion to a subject:
a concept that is linked ([[X]]) from ≥N different pages and is not already
a subject in SCHEMA. Solves "I forgot to promote" — the system suggests,
you approve. Read-only.
Usage: python3 subject_candidates.py [N]   (default N=3)
"""
import sys, re
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

REPORT = V.WIKI / "subject_candidates.md"
SCHEMA = V.SYS / "SCHEMA.md"
N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def existing_subjects():
    if not SCHEMA.exists():
        return set()
    return {V.nfc(m.group(1).strip()) for m in LINK_RE.finditer(SCHEMA.read_text(encoding="utf-8"))}


def main():
    subs = existing_subjects()
    refs = defaultdict(set)            # target -> {pages that mention it}
    page_names = set()

    pages = list(V.iter_wiki_pages())
    for p, meta, body in pages:
        page_names.add(V.nfc(p.stem))
        text = body + " " + str(meta.get("subject", ""))
        for m in LINK_RE.finditer(text):
            tgt = V.nfc(m.group(1).split("/")[-1].split("|")[0].strip())
            refs[tgt].add(V.nfc(p.stem))

    cands = []
    for tgt, pgs in refs.items():
        if len(pgs) < N:                       continue
        if tgt in subs:                         continue   # already a subject
        cands.append((len(pgs), tgt, sorted(pgs)))
    cands.sort(reverse=True)

    lines = ["---", "tags: [report]", "private: false", "---",
             "# Subject promotion candidates", "",
             f"Generated: {V.today()} · threshold: ≥{N} mentions · found: {len(cands)}", ""]
    if cands:
        lines.append("> Concepts that recur across many pages but are not a subject in SCHEMA. Add to SCHEMA if you want.")
        lines.append("")
        for cnt, tgt, pgs in cands:
            is_page = "📄 (exists as a page)" if tgt in page_names else "💡 (concept)"
            lines.append(f"- **{tgt}** — {cnt} mentions {is_page} · {', '.join(pgs)}")
    else:
        lines.append("✅ No candidates above the threshold.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"💡 Promotion candidates (≥{N}): {len(cands)} · 📄 {V.rel(REPORT)}")
    for cnt, tgt, _ in cands:
        print(f"   {cnt}×  {tgt}")


if __name__ == "__main__":
    main()
