#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vsearch.py — semantic search over the vault. Answers "what relates to this meaning",
not "where is this word".

What this makes possible that wasn't before:
    vsearch "<the word in another language>" → finds a page that says "Anchored Volume Profile" in English
    vsearch "vector database"                → finds the page titled in the vault's other language
    vsearch "how do I learn"                 → finds notes in 2 - Notes, which the query skill never reached

Usage:
    python3 "0 - System/scripts/vsearch.py" "question"
    python3 "0 - System/scripts/vsearch.py" "question" --k 5 --folder "2 - Notes"
    python3 "0 - System/scripts/vsearch.py" "question" --json      # a JSON array of paths only
    python3 "0 - System/scripts/vsearch.py" "question" --files     # compatibility: paths only
"""
import sys, os, json, argparse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V
import numpy as np
import safe_input as S
import embed_index as I

OUT    = V.VAULT / "vector-out"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def load():
    # Legacy indexes are opaque; only the current schema is read.
    base, meta = I.active()
    if not base:
        sys.exit('No semantic index. Run: python3 "0 - System/scripts/embed_index.py"')
    vecs = np.load(base / 'vectors.npy', allow_pickle=False)
    recs = [json.loads(l) for l in (base / 'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(recs) != len(vecs):
        sys.exit('Corrupt index')
    keep = [i for i, r in enumerate(recs) if S.permitted(r['path'])
            and r.get('body_hash') == meta.get('considered', {}).get(r['path'])]
    vecs = vecs[keep]
    recs = [recs[i] for i in keep]
    return meta, vecs, recs


def embed_query(q, model):
    payload = json.dumps({"model": model, "input": [q]}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embed", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            v = np.asarray(json.loads(r.read())["embeddings"][0], dtype=np.float32)
    except Exception as e:
        sys.exit(f"🔴 Ollama failed ({OLLAMA}, model {model}): {e}")
    return v / max(float(np.linalg.norm(v)), 1e-9)


def search(q, k=8, folder=None):
    meta, vecs, recs = load()
    if not recs:
        return []
    qv = embed_query(q, meta["model"])
    scores = vecs @ qv                       # normalized → inner product = cosine
    order = np.argsort(-scores)

    hits, seen = [], set()
    for i in order:
        r = recs[i]
        if folder and not r["path"].startswith(folder):
            continue
        if r['path'] in seen:
            continue
        seen.add(r['path'])
        hits.append(r['path'])
        if len(hits) >= k:
            break
    # Re-check at output time; only paths cross the search API boundary.
    return [path for path in hits if S.permitted(path)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--folder", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--files", action="store_true")
    args = ap.parse_args()

    hits = search(args.query, args.k, args.folder)

    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return
    if not hits and not args.files:
        print("Nothing found.")
        return
    print("\n".join(hits))


if __name__ == "__main__":
    main()
