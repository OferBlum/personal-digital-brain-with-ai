#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autolink.py — automatically turn exact page-title mentions into [[wikilinks]].
Bidirectional: scans both the wiki pages (7 - Wikipedia) and the notes
(2 - Notes), linking title mentions from both corpora. On a name collision
(a note and a wiki page with the same name) the wiki page wins, and the
collision is reported so the note can be renamed.
Deliberately conservative: skips frontmatter, headings (#), code blocks,
already-linked text, and titles shorter than 3 characters. Only the fuzzy
conceptual links are left to the agent.

Default: dry-run. With --apply: back up, then write.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

APPLY = "--apply" in sys.argv
MIN_LEN = 3

# An existing [[...]] segment — neutralized before linking so a substring
# inside it doesn't get wrapped again
EXISTING_LINK = re.compile(r"\[\[[^\]]*\]\]")


def link_body(body, targets, self_name):
    """targets: list of (title, prefix) sorted longest-first."""
    changed = 0
    out_lines, in_code = [], False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            out_lines.append(line); continue
        if in_code or line.lstrip().startswith("#") or not line.strip():
            out_lines.append(line); continue

        # Split the line into existing [[...]] segments (kept as-is) and
        # plain-text segments (linked)
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
                # Replace occurrences that aren't part of a longer word
                # (word boundary for Latin/Hebrew/digits)
                pattern = re.compile(
                    r"(?<![\wא-ת])" + re.escape(t) + r"(?![\wא-ת])"
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

    # Name collision: the wiki page wins — the note is removed from the
    # link namespace and reported
    collisions = sorted(wiki_titles & note_titles)
    if collisions:
        print("⚠️ Name collisions (wiki page wins — consider renaming the note):")
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
    print(f"{'🟢 writing' if APPLY else '🔍 dry-run'} — {total} links in {len(planned)} pages:")
    for p, n, _, _ in planned:
        print(f"   📄 {V.rel(p)}: {n} links")

    if not APPLY:
        print("\nℹ️  Nothing written. To apply: python3 autolink.py --apply"); return

    dest = V.backup(touched, "autolink")
    for p, _, meta, new_body in planned:
        p.write_text(V.render_page(meta, new_body), encoding="utf-8")
    print(f"\n✅ Wrote {len(planned)} pages. Backup: {V.rel(dest)}")


if __name__ == "__main__":
    main()
