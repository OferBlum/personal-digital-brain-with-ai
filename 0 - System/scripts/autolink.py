#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autolink.py — automatically links exact page-title mentions into [[wikilink]]s.
Bidirectional: scans both the wiki pages (7 - Wikipedia) and the notes (2 - Notes),
and links mentions of titles from either corpus. On a name collision (a note and a
wiki page with the same name) the wiki page wins, and the collision is reported so
you can rename the note.
Deliberately conservative: skips frontmatter, headings (#), code blocks, text that
is already linked, and titles shorter than 3 characters. Only the fuzzy conceptual
links are left for the agent.

Default: dry-run. With --apply: backs up, then writes.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

APPLY = "--apply" in sys.argv
MIN_LEN = 3

# An existing [[...]] span — neutralized before linking so a substring inside it
# doesn't get wrapped a second time.
EXISTING_LINK = re.compile(r"\[\[[^\]]*\]\]")

# Word-boundary class. \w already covers Latin, digits and underscore; the explicit
# U+0590-U+05FF range adds the Hebrew block, written as escapes so this file stays
# pure ASCII. Add your own script's block here if you write in another one.
WORD_CHAR = r"[\w\u0590-\u05ff]"


def link_body(body, targets, self_name):
    """targets: a list of (title, prefix) sorted longest-first."""
    changed = 0
    out_lines, in_code = [], False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            out_lines.append(line); continue
        if in_code or line.lstrip().startswith("#") or not line.strip():
            out_lines.append(line); continue

        # Split the line into existing [[...]] spans (left as-is) and plain text spans (linked)
        parts, last = [], 0
        for m in EXISTING_LINK.finditer(line):
            parts.append((line[last:m.start()], False))
            parts.append((m.group(0), True))
            last = m.end()
        parts.append((line[last:], False))

        new_parts = []
        for text, is_link in parts:
            if is_link or not text:
                new_parts.append(text); continue
            new = text
            for t, prefix in targets:
                if t == self_name or len(t) < MIN_LEN:
                    continue
                # Replace an occurrence that isn't part of a longer word
                pattern = re.compile(
                    r"(?<!" + WORD_CHAR + r")" + re.escape(t) + r"(?!" + WORD_CHAR + r")"
                )
                def repl(m):
                    nonlocal changed
                    changed += 1
                    return f"[[{prefix}/{t}]]"
                new = pattern.sub(repl, new)
            new_parts.append(new)
        out_lines.append("".join(new_parts))
    return "\n".join(out_lines), changed


def main():
    pages = list(V.iter_wiki_pages())
    notes = list(V.iter_notes())
    wiki_titles = {V.nfc(p.stem) for p, _, _ in pages}
    note_titles = {V.nfc(p.stem) for p, _, _ in notes}

    # Name collision: the wiki page wins — the note stays out of the link space and is reported
    collisions = sorted(wiki_titles & note_titles)
    if collisions:
        print("⚠️ Name collisions (the wiki page wins — consider renaming the note):")
        for c in collisions:
            print(f"   ⛔ {c}")
        note_titles -= wiki_titles

    targets = sorted(
        [(t, "7 - Wikipedia") for t in wiki_titles]
        + [(t, "2 - Notes") for t in note_titles],
        key=lambda x: len(x[0]), reverse=True,
    )

    planned, touched = [], []
    for p, meta, body in pages + notes:
        new_body, n = link_body(body, targets, V.nfc(p.stem))
        if n:
            planned.append((p, n, meta, new_body))
            touched.append(p)

    if not planned:
        print("✅ No unlinked mentions."); return

    total = sum(n for _, n, _, _ in planned)
    print(f"{'🟢 writing' if APPLY else '🔍 dry-run'} — {total} links across {len(planned)} pages:")
    for p, n, _, _ in planned:
        print(f"   📄 {V.rel(p)}: {n} links")

    if not APPLY:
        print("\nℹ️  Nothing was written. To run for real: python3 autolink.py --apply"); return

    dest = V.backup(touched, "autolink")
    for p, _, meta, new_body in planned:
        p.write_text(V.render_page(meta, new_body), encoding="utf-8")
    print(f"\n✅ Wrote {len(planned)} pages. Backup: {V.rel(dest)}")


if __name__ == "__main__":
    main()
