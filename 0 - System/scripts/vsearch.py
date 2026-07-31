#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vsearch.py — semantic search across the vault. Answers "what relates to this meaning",
not "where does this word appear".

This is what wasn't possible before:
    vsearch "volume"          → finds a page that says "Anchored Volume Profile"
    vsearch "vector database" → finds the page even if it's titled in another language
    vsearch "how I learn"     → finds notes in 2 - Notes that the query skill never reached

Usage:
    python3 "0 - System/scripts/vsearch.py" "question"
    python3 "0 - System/scripts/vsearch.py" "question" --k 5 --folder "2 - Notes"
    python3 "0 - System/scripts/vsearch.py" "question" --json      # for programmatic use
    python3 "0 - System/scripts/vsearch.py" "question" --files     # paths only, for reading
"""
import sys, os, json, argparse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V
import numpy as np

OUT    = V.VAULT / "vector-out"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def load():
    meta_p = OUT / "meta.json"
    if not meta_p.exists():
        sys.exit('No semantic index. Run: python3 "0 - System/scripts/embed_index.py"')
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    vecs = np.load(OUT / "vectors.npy")
    recs = [json.loads(l) for l in (OUT / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
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


def search(q, k=8, folder=None, per_file=2):
    meta, vecs, recs = load()
    qv = embed_query(q, meta["model"])
    scores = vecs @ qv                       # normalized → inner product = cosine
    order = np.argsort(-scores)

    hits, seen = [], {}
    for i in order:
        r = recs[i]
        if folder and not r["path"].startswith(folder):
            continue
        if seen.get(r["path"], 0) >= per_file:   # don't flood with every chunk of one page
            continue
        seen[r["path"]] = seen.get(r["path"], 0) + 1
        hits.append({**r, "score": round(float(scores[i]), 4)})
        if len(hits) >= k:
            break
    return hits


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
    if args.files:
        seen = []
        for h in hits:
            if h["path"] not in seen:
                seen.append(h["path"])
        print("\n".join(seen))
        return

    if not hits:
        print("Nothing found.")
        return
    for h in hits:
        head = f" › {h['heading']}" if h["heading"] else ""
        print(f"\n{h['score']:.3f}  [[{h['path'][:-3]}]]{head}")
        if h.get("background"):
            print(f"        {h['background'][:110]}")
        snippet = " ".join(h["text"].split())[:180]
        print(f"        {snippet}…")


if __name__ == "__main__":
    main()
