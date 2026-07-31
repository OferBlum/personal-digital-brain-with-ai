#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embed_index.py — builds a local semantic index of the vault.

Why it exists: search in the vault was always lexical — grep, exact title matching,
and trigrams over the graph labels. None of those knows that "volume" and its
translation are the same thing, and none will find an English page from a question
asked in another language. That is what this layer solves.

What it is *not*: not a vector database and not a source of truth. It is a derived,
disposable file — the markdown is the truth. You can delete vector-out/ and rebuild
at any time. At this size (~1,500 chunks) numpy does cosine over everything in under
10ms, so there is no reason to add faiss/chroma.

Privacy — three gates, all of which must pass before a file is even read:
  1. allowlist: only the three content folders. The journal is out of scope
     *structurally*, not by filtering.
  2. V.is_forbidden(): the journal check.
  3. private: true → skip.
And after every build, --audit cross-checks against .graphifyignore and fails if
anything leaked.

NOTE: the resulting vector-out/meta.json records every indexed file path, so the
index is a list of your note titles. It is gitignored for that reason — build it
locally, never publish it.

Usage:
    python3 "0 - System/scripts/embed_index.py"            # incremental build
    python3 "0 - System/scripts/embed_index.py" --rebuild  # from scratch
    python3 "0 - System/scripts/embed_index.py" --audit    # privacy check only
    python3 "0 - System/scripts/embed_index.py" --status   # index state
"""
import sys, os, json, re, time, hashlib, argparse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V
import numpy as np

OUT       = V.VAULT / "vector-out"
VEC_PATH  = OUT / "vectors.npy"
CHUNKS    = OUT / "chunks.jsonl"
META_PATH = OUT / "meta.json"

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL  = os.environ.get("VAULT_EMBED_MODEL", "bge-m3")

# Gate 1 — the allowlist. Nothing outside this list is read, full stop.
ALLOWED_FOLDERS = ["7 - Wikipedia", "2 - Notes", "1 - Topics"]

TARGET_CHARS = 1200          # ~400 tokens
MIN_CHARS    = 80


# ---------- collecting files (privacy) ----------

def collect():
    """Returns [(path, meta, body)] — only what passed all three gates."""
    out = []
    for folder in ALLOWED_FOLDERS:
        root = V.VAULT / folder
        if not root.exists():
            continue
        for p in sorted(root.glob("*.md")):        # not recursive → raw/ stays out
            # Gate 2 — the journal
            if V.is_forbidden(p):
                continue
            # generated system files — noise, not secrets
            if V.nfc(p.name).startswith(V.SYSTEM_PREFIX):
                continue
            meta, body = V.read_page(p)
            # Gate 3 — private
            if str(meta.get("private", "")).lower() == "true":
                continue
            # Catalogs, operation logs and reports are not content — they are
            # navigation over the content.
            tags = meta.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            if str(meta.get("type", "")) in ("index", "log", "report"):
                continue
            if "report" in [str(t).lstrip("#") for t in tags]:
                continue
            if len(body.strip()) < MIN_CHARS:
                continue
            out.append((p, meta, body))
    return out


def assert_private_excluded(paths):
    """Cross-checks against .graphifyignore — the existing list of private files."""
    ign = V.VAULT / ".graphifyignore"
    if not ign.exists():
        return ["⚠️  .graphifyignore does not exist — run gen_graphifyignore.py --apply"]
    private = set()
    for line in ign.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("/") and line.endswith(".md"):
            private.add(V.nfc(line[1:]))
    indexed = {V.nfc(str(Path(p).relative_to(V.VAULT))) for p in paths}
    leaked = sorted(indexed & private)
    problems = [f"🔴 private file in the index: {x}" for x in leaked]
    for x in indexed:
        if V.JOURNAL in x:
            problems.append(f"🔴 journal file in the index: {x}")
        if not any(x.startswith(f + "/") for f in ALLOWED_FOLDERS):
            problems.append(f"🔴 outside the allowlist: {x}")
    return problems


# ---------- chunking ----------

def chunk(meta, body):
    """
    Split on headings, and attach `title · background` from the file to every chunk.
    This is the cheapest cross-language bridge there is: the title and background in
    one language travel with a body in another, so a question in one language finds
    a page written in the other.
    """
    body = re.sub(r"^\s*---\s*$", "", body, flags=re.M)     # horizontal rules
    parts, cur, head = [], [], ""
    for line in body.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            if cur:
                parts.append((head, "\n".join(cur).strip()))
            head = m.group(2).strip()
            cur = []
        else:
            cur.append(line)
    if cur:
        parts.append((head, "\n".join(cur).strip()))

    merged = []
    for h, txt in parts:
        if not txt or len(txt) < MIN_CHARS:
            if txt and merged:
                merged[-1] = (merged[-1][0], merged[-1][1] + "\n" + txt)
            continue
        while len(txt) > TARGET_CHARS * 1.6:
            cut = txt.rfind("\n", 0, TARGET_CHARS)
            cut = cut if cut > MIN_CHARS else TARGET_CHARS
            merged.append((h, txt[:cut].strip()))
            txt = txt[cut:].strip()
        merged.append((h, txt))
    return merged


def embed_text(meta, path, head, txt):
    title = V.nfc(Path(path).stem)
    bg = str(meta.get("background") or "").strip()
    prefix = f"{title} · {bg}" if bg else title
    return f"{prefix}\n{head}\n{txt}" if head else f"{prefix}\n{txt}"


# ---------- Ollama ----------

def embed(texts, batch=16):
    vecs = []
    for i in range(0, len(texts), batch):
        payload = json.dumps({"model": MODEL, "input": texts[i:i + batch]}).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/embed", data=payload,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
        except Exception as e:
            sys.exit(f"🔴 Ollama failed ({OLLAMA}, model {MODEL}): {e}\n"
                     f"   Make sure Ollama is running and the model exists: ollama pull {MODEL}")
        vecs.extend(data["embeddings"])
        print(f"\r   embedding {min(i+batch, len(texts))}/{len(texts)}", end="", flush=True)
    print()
    a = np.asarray(vecs, dtype=np.float32)
    n = np.linalg.norm(a, axis=1, keepdims=True)
    return a / np.clip(n, 1e-9, None)          # normalized → cosine = inner product


def body_hash(body):
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()[:16]


# ---------- building ----------

def build(rebuild=False):
    files = collect()
    problems = assert_private_excluded([p for p, _, _ in files])
    if any(x.startswith("🔴") for x in problems):
        for x in problems:
            print(x)
        sys.exit("🔴 The privacy check failed — no index was built.")

    old = {}
    if not rebuild and CHUNKS.exists() and VEC_PATH.exists():
        vecs_old = np.load(VEC_PATH)
        for i, line in enumerate(CHUNKS.read_text(encoding="utf-8").splitlines()):
            rec = json.loads(line)
            old.setdefault(rec["path"], []).append((rec, vecs_old[i]))

    records, reuse, fresh_texts, fresh_meta = [], [], [], []
    for p, meta, body in files:
        rel, h = V.rel(p), body_hash(body)
        cached = old.get(rel)
        if cached and cached[0][0].get("body_hash") == h:
            for rec, vec in cached:
                records.append(rec); reuse.append(vec)
            continue
        for head, txt in chunk(meta, body):
            fresh_texts.append(embed_text(meta, p, head, txt))
            fresh_meta.append({"path": rel, "title": V.nfc(p.stem), "heading": head,
                               "background": str(meta.get("background") or ""),
                               "type": str(meta.get("type") or ""),
                               "subject": str(meta.get("subject") or ""),
                               "body_hash": h, "text": txt})

    print(f"📚 {len(files)} files · {len(records)} chunks from cache · {len(fresh_texts)} new")
    if fresh_texts:
        new_vecs = embed(fresh_texts)
        records.extend(fresh_meta)
        reuse.extend(list(new_vecs))
    if not records:
        sys.exit("Nothing to index.")

    OUT.mkdir(exist_ok=True)
    mat = np.vstack([np.asarray(v, dtype=np.float32) for v in reuse])
    np.save(VEC_PATH, mat)
    CHUNKS.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
                      encoding="utf-8")
    # Record what was *considered*, not only what produced chunks — otherwise a file
    # that is too short counts as "new" on every check and pins --check to a
    # permanent warning.
    considered = {V.rel(p): body_hash(b) for p, _, b in files}
    META_PATH.write_text(json.dumps({
        "model": MODEL, "dim": int(mat.shape[1]), "chunks": len(records),
        "files": len(files), "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "folders": ALLOWED_FOLDERS, "considered": considered,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    for x in problems:
        print(x)
    print(f"✅ {len(records)} chunks · {mat.shape[1]} dimensions · {mat.nbytes/1e6:.1f}MB · {V.rel(OUT)}")


def status():
    if not META_PATH.exists():
        print('No index. Run: python3 "0 - System/scripts/embed_index.py"')
        return
    m = json.loads(META_PATH.read_text(encoding="utf-8"))
    print(json.dumps(m, ensure_ascii=False, indent=2))
    files = collect()
    have = {json.loads(l)["path"] for l in CHUNKS.read_text(encoding="utf-8").splitlines()}
    now = {V.rel(p) for p, _, _ in files}
    print(f"\nFiles now: {len(now)} · in the index: {len(have)} · "
          f"new: {len(now - have)} · deleted: {len(have - now)}")


def _diff():
    """(added, gone, changed) as sets of paths — disk compared against `considered` in meta.
    If there is no usable index, returns a reason string: "missing" or "legacy"."""
    if not META_PATH.exists():
        return "missing"
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    have = meta.get("considered")
    if have is None:                       # index from an older version
        return "legacy"
    now = {V.rel(p): body_hash(b) for p, _, b in collect()}
    return (set(now) - set(have),
            set(have) - set(now),
            {k for k in set(now) & set(have) if now[k] != have[k]})


def check():
    """Silent if the index is current; one line if it isn't. For SessionStart."""
    d = _diff()
    if d == "missing":
        print('💡 No semantic index — run: python3 "0 - System/scripts/embed_index.py"')
        return
    if d == "legacy":
        print('💡 The semantic index was built by an older version — run: python3 "0 - System/scripts/embed_index.py" --rebuild')
        return
    added, gone, changed = d
    total = len(added) + len(gone) + len(changed)
    if total:
        print(f"💡 The semantic index is {total} files behind "
              f"(+{len(added)} new, -{len(gone)} deleted, ~{len(changed)} changed) — "
              f'run: python3 "0 - System/scripts/embed_index.py"')


def changes():
    """One path per change, line by line. Silent when the index is current — for reindex.sh.
    + new · ~ changed · - deleted. Silent = nothing to do, which is what the script checks."""
    d = _diff()
    if d == "missing":
        print("! no semantic index — it will be built from scratch")
        return
    if d == "legacy":
        print("! the index was built by an older version — it will be rebuilt")
        return
    added, gone, changed = d
    for mark, paths in (("+", added), ("~", changed), ("-", gone)):
        for path in sorted(paths):
            print(f"{mark} {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--check", action="store_true", help="silent unless the index is stale")
    ap.add_argument("--changes", action="store_true", help="one path per changed file, line by line")
    args = ap.parse_args()

    if args.changes:
        return changes()
    if args.check:
        return check()
    if args.status:
        return status()
    if args.audit:
        files = collect()
        problems = assert_private_excluded([p for p, _, _ in files])
        print(f"Checked {len(files)} files slated for indexing.")
        if CHUNKS.exists():
            idx = {json.loads(l)["path"] for l in CHUNKS.read_text(encoding="utf-8").splitlines()}
            problems += assert_private_excluded([V.VAULT / x for x in idx])
            print(f"Checked {len(idx)} files already in the index.")
        hard = [x for x in problems if x.startswith("🔴")]
        for x in problems:
            print(x)
        if hard:
            sys.exit(1)
        print("✅ Clean: no journal, no private: true, everything inside the allowlist.")
        return
    build(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
