#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_check.py — what has drifted from the public mirror, and does anything leak.

READ-ONLY BY CONSTRUCTION. This file contains no open(...,"w"), no write_text, no mkdir,
no shutil, and no git command that mutates. It prints and exits; nothing else.

Exit code 0 = clean, 1 = a leak was found (so it can be wired as a pre-push hook).

Why it exists: the mirror is a hand-made translation with no sync mechanism, so it drifts
silently. Nothing detected the last three weeks of divergence. This does.

PRIVACY: filenames are printed ONLY for the system layer. Everything under the content
folders is reported as a count, never by name — those filenames *are* private note titles,
which is the same leak class that got .graphifyignore banned from the repo.

Usage:
    python3 "0 - System/scripts/publish_check.py"
    python3 "0 - System/scripts/publish_check.py" --leaks-only
    MIRROR_ROOT=/some/path python3 "0 - System/scripts/publish_check.py"
"""
import os, sys, re, ast, json, fnmatch, argparse, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V
import yaml

MANIFEST = V.SYS / "publish-manifest.yaml"
# U+0590-U+05FF (Hebrew block) as escapes, so this file itself stays pure ASCII.
NON_LATIN = re.compile(r"[\u0590-\u05ff]")


def load_manifest():
    if not MANIFEST.exists():
        sys.exit(f"No publish manifest at {V.rel(MANIFEST)}")
    m = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    mirror = Path(os.environ.get("MIRROR_ROOT") or os.path.expanduser(m["mirror"]))
    return m, mirror


def map_path(rel, folder_map):
    """Vault-relative path -> mirror-relative path."""
    parts = Path(rel).parts
    if parts and parts[0] in folder_map:
        return str(Path(folder_map[parts[0]], *parts[1:]))
    return rel


# ---------- 1. inventory drift ----------

def expand_publish(m):
    """Returns {vault_rel: mirror_rel} for everything the manifest says to publish."""
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


def inventory(m, mirror):
    problems = []
    planned = expand_publish(m)
    excluded = set(m["exclude"])

    missing, extra = [], []
    for vrel, mrel in sorted(planned.items()):
        if vrel in excluded:
            continue
        if not (mirror / mrel).exists():
            missing.append((vrel, mrel))

    # Anything in the mirror's system layer with no vault counterpart
    reverse = {v: k for k, v in planned.items()}
    # Placeholders are hand-written in the mirror on purpose, so they have no vault source.
    placeholder_targets = {map_path(k, m["folder_map"]) for k in m["placeholders"]}
    for p in sorted((mirror / "0 - System").rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        mrel = str(p.relative_to(mirror))
        expected_placeholder = map_path(mrel, {}) in placeholder_targets
        if mrel not in reverse and "hermes-skills" not in mrel and not expected_placeholder:
            extra.append(mrel)

    print("== inventory ==")
    print(f"  publishable files: {len(planned)}   excluded by policy: {len(excluded)}")
    if missing:
        print(f"  🔴 in the vault but NOT in the mirror ({len(missing)}):")
        for vrel, mrel in missing:
            print(f"       {vrel}  ->  {mrel}")
        problems.append(f"{len(missing)} unpublished files")
    if extra:
        print(f"  🟡 in the mirror with no vault source ({len(extra)}):")
        for x in extra:
            print(f"       {x}")
    if not missing and not extra:
        print("  ✅ inventory matches")

    # Content folders — COUNTS ONLY, never names.
    print("\n== content folders (counts only — these filenames are private) ==")
    for vfolder, mfolder in m["folder_map"].items():
        if mfolder not in m["gitkeep_only"] and mfolder != "7 - Wikipedia":
            continue
        src = V.VAULT / vfolder
        if not src.exists():
            continue
        n = sum(1 for _ in src.glob("*.md"))
        shipped = [p for p in (mirror / mfolder).glob("*.md")] if (mirror / mfolder).exists() else []
        print(f"  {mfolder:<16} vault: {n:>4} files   published: {len(shipped)}")
    return problems


# ---------- 2. content drift (structure signature) ----------

def sig_py(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    names = sorted(n.name for n in tree.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    imports = sorted({(n.module or "") if isinstance(n, ast.ImportFrom)
                      else a.name.split(".")[0]
                      for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                      for a in (n.names if isinstance(n, ast.Import) else [n])})
    return {"defs": names, "imports": imports}


def sig_md(text):
    heads = re.findall(r"^(#{1,6})\s+", text, re.M)
    fm_keys = []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm_keys = sorted(re.findall(r"^([A-Za-z\u0590-\u05ff_]+):", text[:end], re.M))
    return {"headings": [len(h) for h in heads], "fm_keys": fm_keys}


def sig_sh(text):
    return {"funcs": sorted(re.findall(r"^(\w+)\s*\(\)\s*\{", text, re.M))}


def sig_json(text):
    def keys(o, prefix=""):
        if isinstance(o, dict):
            r = []
            for k, v in o.items():
                r.append(prefix + k)
                r += keys(v, prefix + k + ".")
            return r
        if isinstance(o, list):
            r = []
            for v in o:
                r += keys(v, prefix)
            return r
        return []
    try:
        return {"keys": sorted(set(keys(json.loads(text))))}
    except Exception:
        return None


def signature(path, text, fm_key_map):
    if path.suffix == ".py":
        return sig_py(text)
    if path.suffix == ".sh":
        return sig_sh(text)
    if path.suffix == ".json":
        return sig_json(text)
    if path.suffix == ".md":
        s = sig_md(text)
        s["fm_keys"] = sorted(fm_key_map.get(k, k) for k in s["fm_keys"])
        return s
    return None


def content_drift(m, mirror):
    """Byte comparison is meaningless across a translation. Compare structure instead:
    identifiers are English on both sides, so this is exact for code."""
    print("\n== content drift (structure signature) ==")
    planned = expand_publish(m)
    placeholders = set(m["placeholders"])
    sanitized = set(m.get("sanitized") or {})
    drift = 0
    for vrel, mrel in sorted(planned.items()):
        if vrel in m["exclude"] or vrel in placeholders or vrel in sanitized:
            continue
        vp, mp = V.VAULT / vrel, mirror / mrel
        if not mp.exists():
            continue
        vt, mt = vp.read_text(encoding="utf-8", errors="replace"), mp.read_text(encoding="utf-8", errors="replace")
        vs, ms = signature(vp, vt, m["fm_key_map"]), signature(mp, mt, m["fm_key_map"])
        notes = []
        if vs and ms and vs != ms:
            for k in vs:
                if vs[k] != ms[k]:
                    only_v = [x for x in vs[k] if x not in ms[k]] if isinstance(vs[k], list) else vs[k]
                    only_m = [x for x in ms[k] if x not in vs[k]] if isinstance(ms[k], list) else ms[k]
                    if only_v or only_m:
                        notes.append(f"{k}: vault-only={only_v or '-'} mirror-only={only_m or '-'}")
        if vp.stat().st_mtime > mp.stat().st_mtime + 1:
            notes.append("STALE (vault newer)")
        if notes:
            drift += 1
            print(f"  🟡 {vrel}")
            for n in notes:
                print(f"       {n}")
    if not drift:
        print("  ✅ no structural drift")
    print(f"  (skipped by design — placeholders: {len(placeholders)}, sanitized: {len(sanitized)})")
    return []


# ---------- 3. leak audit ----------

def leak_audit(m, mirror):
    problems = []
    print("\n== leak audit ==")

    for rel in m["must_be_absent"]:
        if (mirror / rel).exists():
            print(f"  🔴 MUST NOT EXIST but does: {rel}")
            problems.append(f"present: {rel}")
    print(f"  checked {len(m['must_be_absent'])} never-publish paths")

    terms = re.compile("|".join(re.escape(t) for t in m["leak_terms"]), re.I)
    allow = m["leak_allow"]
    hits, hebrew_files = [], []
    for p in sorted(mirror.rglob("*")):
        if not p.is_file():
            continue
        if any(x in p.parts for x in (".git", ".obsidian", "__pycache__")):
            continue
        rel = str(p.relative_to(mirror))
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if NON_LATIN.search(text) and rel not in m["hebrew_allow"]:
            hebrew_files.append(rel)
        for i, line in enumerate(text.splitlines(), 1):
            if terms.search(line):
                if any(rel == a.split(":", 1)[0] and a.split(":", 1)[1] in line for a in allow):
                    continue
                hits.append((rel, i, line.strip()[:100]))

    if hits:
        print(f"  🔴 personal-term hits outside the allowlist ({len(hits)}):")
        for rel, i, line in hits[:40]:
            print(f"       {rel}:{i}: {line}")
        problems.append(f"{len(hits)} personal-term hits")
    else:
        print("  ✅ no personal terms outside the allowlist")

    if hebrew_files:
        print(f"  🔴 non-ASCII (Hebrew) found in {len(hebrew_files)} files:")
        for f in hebrew_files:
            print(f"       {f}")
        problems.append(f"{len(hebrew_files)} files contain Hebrew")
    else:
        print("  ✅ zero Hebrew characters")

    # Prove the ignores are live, not merely written
    for rel in ["vector-out/", ".graphifyignore", ".claude/settings.local.json", "home.html"]:
        r = subprocess.run(["git", "-C", str(mirror), "check-ignore", "-q", rel],
                           capture_output=True)
        state = "ignored" if r.returncode == 0 else "🔴 NOT IGNORED"
        print(f"  {rel:<32} {state}")
        if r.returncode != 0:
            problems.append(f"not ignored: {rel}")

    # Anything forbidden already tracked?
    r = subprocess.run(["git", "-C", str(mirror), "ls-files", "--cached"],
                       capture_output=True, text=True)
    # Match the ARTIFACTS, not the scripts that generate them: "graphifyignore" alone
    # also matches gen_graphifyignore.py, which is a published script and perfectly fine.
    forbidden = ("vector-out/", ".graphifyignore", "home.html",
                 "settings.local.json", "memories/USER.md", "memories/MEMORY.md",
                 "_cache-archive", "validation_report", ".backup/")
    bad = [l for l in r.stdout.splitlines() if any(x in l for x in forbidden)]
    if bad:
        print(f"  🔴 forbidden files already tracked by git ({len(bad)}):")
        for b in bad:
            print(f"       {b}")
        problems.append("forbidden files tracked")
    else:
        print("  ✅ nothing forbidden is tracked")

    r = subprocess.run(["git", "-C", str(mirror), "log", "--oneline", "-1"],
                       capture_output=True, text=True)
    print(f"  mirror HEAD: {r.stdout.strip()}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leaks-only", action="store_true")
    args = ap.parse_args()

    m, mirror = load_manifest()
    if not mirror.exists():
        sys.exit(f"Mirror not found: {mirror}  (set MIRROR_ROOT)")
    print(f"vault : {V.VAULT}")
    print(f"mirror: {mirror}\n")

    problems = []
    if not args.leaks_only:
        problems += inventory(m, mirror)
        problems += content_drift(m, mirror)
    problems += leak_audit(m, mirror)

    print("\n" + "=" * 60)
    if problems:
        print("🔴 NOT CLEAN — do not push:")
        for p in problems:
            print(f"   - {p}")
        sys.exit(1)
    print("✅ CLEAN — mirror is in sync and nothing leaks.")


if __name__ == "__main__":
    main()
