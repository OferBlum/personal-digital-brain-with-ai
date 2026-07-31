#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_port.py — port the MECHANICAL part of the vault into the public mirror.

Dry-run by default; --apply writes, after backing up whatever it would overwrite.

Scope, deliberately narrow. This handles only what is deterministic:
  • copy each file the manifest lists under `publish:`
  • rewrite folder names via folder_map and frontmatter keys via fm_key_map
  • delete anything in the mirror that the manifest now marks `exclude:`

It does NOT translate prose. Comments, docstrings and Markdown bodies containing
non-ASCII text are reported as NEEDS-TRANSLATION with file:line, and that list is the
agent's worklist. Machine-translated English shipping to a public repo unreviewed is
worse than no automation at all — the honest split is: scripts move bytes, humans and
agents move meaning.

It also refuses to touch anything in `placeholders:` or `sanitized:`. Those are
hand-written on purpose; overwriting them from the vault is precisely the leak this
whole pipeline exists to prevent.

Usage:
    python3 "0 - System/scripts/publish_port.py"           # dry-run
    python3 "0 - System/scripts/publish_port.py" --apply   # write
"""
import os, sys, re, shutil, argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V
import yaml

MANIFEST = V.SYS / "publish-manifest.yaml"
NON_ASCII = re.compile(r"[^\x00-\x7F]")
# Emoji and typographic punctuation are fine in a published file; letters are not.
ALLOWED_NON_ASCII = re.compile(r"[‐-‧‰-⁞←-⇿⌀-➿"
                               r"\U0001F000-\U0001FAFF·× •✓⚠️]")


def load():
    m = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    mirror = Path(os.environ.get("MIRROR_ROOT") or os.path.expanduser(m["mirror"]))
    return m, mirror


def map_path(rel, folder_map):
    parts = Path(rel).parts
    if parts and parts[0] in folder_map:
        return str(Path(folder_map[parts[0]], *parts[1:]))
    return rel


def translate(text, m):
    """Mechanical substitutions only: folder names and frontmatter keys."""
    for heb, eng in m["folder_map"].items():
        text = text.replace(heb, eng)
    for heb, eng in m["fm_key_map"].items():
        text = re.sub(rf"^(\s*){re.escape(heb)}:", rf"\1{eng}:", text, flags=re.M)
        text = text.replace(f'meta.get("{heb}"', f'meta.get("{eng}"')
        text = text.replace(f"meta.get('{heb}'", f"meta.get('{eng}'")
    return text


def needs_translation(text):
    """Line numbers still holding non-ASCII letters after the mechanical pass."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = ALLOWED_NON_ASCII.sub("", line)
        if NON_ASCII.search(stripped):
            out.append((i, line.strip()[:90]))
    return out


def expand(m):
    out = {}
    for entry in m["publish"]:
        if "->" in entry:
            src, dst = [x.strip() for x in entry.split("->", 1)]
            if (V.VAULT / src).is_file():
                out[src] = dst
            continue
        for p in sorted(V.VAULT.glob(entry)):
            if p.is_file():
                rel = str(p.relative_to(V.VAULT))
                out[rel] = map_path(rel, m["folder_map"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write (otherwise dry-run)")
    ap.add_argument("--overwrite", action="store_true",
                    help="also rewrite files that already exist in the mirror. "
                         "DESTRUCTIVE: replaces hand-translated prose with mechanical "
                         "substitution. Almost never what you want.")
    args = ap.parse_args()

    m, mirror = load()
    if not mirror.exists():
        sys.exit(f"Mirror not found: {mirror}  (set MIRROR_ROOT)")

    protected = set(m["placeholders"]) | set(m.get("sanitized") or {})
    excluded = set(m["exclude"])
    planned = expand(m)

    writes, todo, skipped, deletions, review = [], [], [], [], []

    for vrel, mrel in sorted(planned.items()):
        if vrel in excluded:
            continue
        if vrel in protected:
            skipped.append((vrel, "protected: " + (m["placeholders"].get(vrel)
                                                   or (m.get("sanitized") or {}).get(vrel, ""))))
            continue
        src = V.VAULT / vrel
        dst = mirror / mrel
        new = translate(src.read_text(encoding="utf-8", errors="replace"), m)
        if dst.exists():
            # The mirror copy has already been translated by hand, and that prose is
            # better than anything mechanical substitution produces. Overwriting it
            # would silently re-introduce Hebrew comments into a public repo.
            # So an existing file is only ever REPORTED, never rewritten, unless the
            # operator explicitly asks with --overwrite.
            if dst.read_text(encoding="utf-8", errors="replace") != new:
                review.append((vrel, mrel))
            if not args.overwrite:
                continue
        writes.append((vrel, mrel, new))
        for ln, txt in needs_translation(new):
            todo.append((mrel, ln, txt))

    for erel in excluded:
        target = mirror / map_path(erel, m["folder_map"])
        if target.exists():
            deletions.append(str(target.relative_to(mirror)))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"publish_port — {mode}")
    print(f"  vault : {V.VAULT}")
    print(f"  mirror: {mirror}\n")

    print(f"== new files to create ({len(writes)}) ==")
    for vrel, mrel, _ in writes:
        print(f"  {vrel}  ->  {mrel}")
    if not writes:
        print("  (none — every publishable file already exists in the mirror)")

    if review:
        print(f"\n== differ from the vault, NOT overwritten ({len(review)}) ==")
        print("  These already exist in the mirror and hold hand-translated prose.")
        print("  Port real changes into them by hand; publish_check.py reports the structural delta.")
        for vrel, mrel in review:
            print(f"  {mrel}")

    print(f"\n== protected, not touched ({len(skipped)}) ==")
    for vrel, why in skipped:
        print(f"  {vrel}\n       {why}")

    if deletions:
        print(f"\n== excluded but present in the mirror ({len(deletions)}) ==")
        for d in deletions:
            print(f"  {d}")

    if todo:
        print(f"\n== NEEDS-TRANSLATION ({len(todo)} lines) ==")
        print("  Mechanical substitution cannot handle these — translate them by hand:")
        for mrel, ln, txt in todo[:60]:
            print(f"  {mrel}:{ln}: {txt}")
        if len(todo) > 60:
            print(f"  … and {len(todo) - 60} more")

    if not args.apply:
        print("\nℹ️  Nothing was written. For a real run: --apply")
        if review and not args.overwrite:
            print("    (existing files are never rewritten without --overwrite)")
        print("    Then translate the NEEDS-TRANSLATION lines and re-run publish_check.py.")
        return

    if writes:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = mirror / ".publish-backup" / stamp
        for _, mrel, _ in writes:
            cur = mirror / mrel
            if cur.exists():
                b = backup / mrel
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cur, b)
        for _, mrel, new in writes:
            dst = mirror / mrel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(new, encoding="utf-8")
        print(f"\n✅ Wrote {len(writes)} files. Backup: .publish-backup/{stamp}")
    if deletions:
        print(f"⚠️  {len(deletions)} excluded files still present — remove them deliberately, "
              f"this script will not delete for you.")
    print("\nNext: translate any NEEDS-TRANSLATION lines, then run publish_check.py as the gate.")


if __name__ == "__main__":
    main()
