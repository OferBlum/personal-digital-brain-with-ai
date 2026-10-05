#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
embed_index.py — builds a local semantic index of the vault.

Why this exists: search in the vault was always lexical — grep, exact title matching,
and trigrams over graph labels. None of them knows that a word, its English
translation and its synonym are the same thing, and none will find an English page
from a question asked in another language. That is what this layer solves.

What it is *not*: not a vector database and not a source of truth. It is a derived,
disposable file — the markdown is the truth. You can delete vector-out/ and rebuild
at any moment. At this size (~1,500 chunks) numpy does cosine over everything in
under 10ms, so there is no reason to add faiss/chroma.

Privacy: the boundary is folder-only (safe_input.py). Only top-level .md files of the
allowlisted folders are read; the private folder is never read nor mapped. There is
no frontmatter flag.

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
import safe_input as S
import uuid

OUT       = V.VAULT / "vector-out"
VEC_PATH  = OUT / "vectors.npy"
CHUNKS    = OUT / "chunks.jsonl"
META_PATH = OUT / "meta.json"

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL  = os.environ.get("VAULT_EMBED_MODEL", "bge-m3")

# The allowlist. Nothing outside this list is read or scanned, period.
ALLOWED_FOLDERS = list(S.FOLDERS)

TARGET_CHARS = 1200          # ~400 tokens of Hebrew text
MIN_CHARS    = 80


# ---------- collecting files (privacy) ----------

def collect():
    """Every file inside the folder boundary (safe_input.sources)."""
    out = []
    for rel, p in S.sources():
        got = S.read(rel)
        if got is None:
            continue
        meta, body = got
        # Catalogues and tiny pages do not create embeddings.
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
    return ["🔴 path outside the indexing boundary" for x in paths if not S.permitted(V.rel(x))]

def active():
    """Legacy indexes are never read or displayed."""
    try:
        pointer = json.loads((OUT / 'active.json').read_text(encoding='utf-8'))
        generation = pointer['generation']
        if not re.fullmatch(r'[0-9a-f]{32}', generation):
            raise ValueError('invalid generation')
        base = OUT / generation
        meta = json.loads((base / 'meta.json').read_text(encoding='utf-8'))
        if meta.get('schema') != 3:
            raise ValueError('legacy index')
        return base, meta
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None, None


# ---------- chunking ----------

def chunk(meta, body):
    """
    Split on headings, and prefix every chunk with the file's `title · background`.
    This is the cheapest cross-language bridge there is: a title and background in one
    language travel with a body in another, so a question in one language finds a
    page written in the other.
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
    rk = str(meta.get("background") or "").strip()
    prefix = f"{title} · {rk}" if rk else title
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


# ---------- build ----------

def build(rebuild=False):
    files = collect()
    problems = assert_private_excluded([p for p, _, _ in files])
    if any(x.startswith("🔴") for x in problems):
        for x in problems:
            print(x)
        sys.exit("🔴 Privacy check failed — no index was built.")

    old = {}
    base, old_meta = active()
    if not rebuild and base:
        vecs_old = np.load(base / 'vectors.npy', allow_pickle=False)
        for i, line in enumerate((base / 'chunks.jsonl').read_text(encoding="utf-8").splitlines()):
            rec = json.loads(line)
            if S.permitted(rec['path']) and rec['path'] in old_meta.get('considered', {}):
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
    OUT.mkdir(exist_ok=True)
    generation = uuid.uuid4().hex
    dest = OUT / generation
    dest.mkdir()
    mat = np.vstack([np.asarray(v, dtype=np.float32) for v in reuse]) if records else np.empty((0, 0), dtype=np.float32)
    np.save(dest / 'vectors.npy', mat)
    (dest / 'chunks.jsonl').write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
                      encoding="utf-8")
    # Store what was *considered*, not just what produced chunks — otherwise a file
    # that's too short would count as "new" on every check and pin --check on a
    # permanent alert.
    considered = {V.rel(p): body_hash(b) for p, _, b in files}
    (dest / 'meta.json').write_text(json.dumps({
        "schema": 3, "model": MODEL, "dim": int(mat.shape[1]), "chunks": len(records),
        "files": len(files), "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "folders": ALLOWED_FOLDERS, "considered": considered,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    pointer = OUT / ('.active-' + generation)
    pointer.write_text(json.dumps({'generation': generation}), encoding='utf-8')
    os.replace(pointer, OUT / 'active.json')

    for x in problems:
        print(x)
    print(f"✅ {len(records)} chunks · {mat.shape[1]} dims · {mat.nbytes/1e6:.1f}MB · {V.rel(OUT)}")


def status():
    base, m = active()
    if not base:
        print("No index. Run: python3 \"0 - System/scripts/embed_index.py\"")
        return
    visible = {k: v for k, v in m.items() if k != 'considered'}
    visible['considered_count'] = len(m.get('considered', {}))
    print(json.dumps(visible, ensure_ascii=False, indent=2))
    files = collect()
    have = {json.loads(l)["path"] for l in (base / 'chunks.jsonl').read_text(encoding="utf-8").splitlines()}
    now = {V.rel(p) for p, _, _ in files}
    print(f"\nFiles now: {len(now)} · in index: {len(have)} · "
          f"new: {len(now - have)} · deleted: {len(have - now)}")


def _diff():
    """(added, gone, changed) as sets of paths — disk compared with `considered` in meta.
    If there is no usable index, returns a reason string: "missing" or "legacy"."""
    base, meta = active()
    if not base:
        return "missing"
    have = meta.get("considered")
    if have is None:                       # index from an old version
        return "legacy"
    now = {V.rel(p): body_hash(b) for p, _, b in collect()}
    return (set(now) - set(have),
            set(have) - set(now),
            {k for k in set(now) & set(have) if now[k] != have[k]})


def check():
    """Silent if the index is current; one line if not. For SessionStart."""
    d = _diff()
    if d == "missing":
        print("💡 No semantic index — run: python3 \"0 - System/scripts/embed_index.py\"")
        return
    if d == "legacy":
        print('💡 The semantic index was built by an old version — run: python3 "0 - System/scripts/embed_index.py" --rebuild')
        return
    added, gone, changed = d
    total = len(added) + len(gone) + len(changed)
    if total:
        print(f"💡 The semantic index is {total} files behind "
              f"(+{len(added)} new, -{len(gone)} deleted, ~{len(changed)} changed) — "
              f'run: python3 "0 - System/scripts/embed_index.py"')


def changes():
    """One path per change, line by line. Silent when the index is current — for reindex.sh.
    + new · ~ changed · - deleted. Silence = nothing to do, which is what the script checks."""
    d = _diff()
    if d == "missing":
        print("! No semantic index — will build from scratch")
        return
    if d == "legacy":
        print("! The index was built by an old version — will rebuild")
        return
    added, gone, changed = d
    for mark, paths in (("+", added), ("~", changed)):
        for path in sorted(paths):
            print(f"{mark} {path}")
    for path in sorted(gone):
        print(f"- {path}")

def audit():
    files = collect()
    base, _ = active()
    problems = assert_private_excluded([p for p, _, _ in files])
    if base:
        for line in (base / 'chunks.jsonl').read_text(encoding='utf-8').splitlines():
            if not S.permitted(json.loads(line)['path']):
                problems.append('🔴 found a chunk outside the indexing boundary')
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(1)
    print(f'✅ Checked {len(files)} files; everything is inside the folder boundary, no chunk outside it.')


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
        return audit()
    build(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
