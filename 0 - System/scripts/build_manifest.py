#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_manifest.py — generates the single canonical manifest.
Merges three sources so no history is lost:
  1. the existing .manifest.json (array)
  2. the old manifest.json (object.sources)
  3. whatever is derived from the pages' actual wiki_sources
Writes to .manifest.json, and backs up + removes the duplicate manifest.json.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

DOT = V.WIKI / ".manifest.json"          # the live one
OLD = V.WIKI / "manifest.json"           # the old/duplicate one


def get_date(meta):
    return meta.get("last_compiled") or meta.get("updated") or meta.get("created") or V.today()


def add(store, path, page, ingested):
    key = V.nfc(path)
    rec = store.setdefault(key, {"ingested": ingested, "pages": set()})
    if page:
        rec["pages"].add(V.nfc(page))
    # keep the earliest date
    if ingested and ingested < rec["ingested"]:
        rec["ingested"] = ingested


def load_legacy(store):
    if DOT.exists():
        for e in json.loads(DOT.read_text(encoding="utf-8")):
            for pg in e.get("pages_produced", []):
                add(store, e["path"], pg, e.get("ingested", V.today()))
    if OLD.exists():
        data = json.loads(OLD.read_text(encoding="utf-8"))
        for e in data.get("sources", []):
            for pg in e.get("pages_produced", []):
                add(store, e["path"], pg, e.get("ingested", V.today()))


def derive_from_pages(store):
    md_index = V.all_md_index()
    for p, meta, _ in V.iter_wiki_pages():
        srcs = meta.get("wiki_sources", [])
        if isinstance(srcs, str):
            srcs = [srcs]
        ingested = get_date(meta)
        for entry in srcs:
            inner = entry.strip()
            if inner.startswith("[[") and inner.endswith("]]"):
                inner = inner[2:-2].strip()
            status, target = V.resolve_link(inner, md_index)
            if status != "ok":
                continue                      # problems are already in the report
            if V.nfc(str(target)) == V.nfc(str(p)):
                continue                      # self-reference
            tparents = Path(target).parents
            if V.WIKI in tparents and V.RAW not in tparents:
                continue                      # a wiki page, not a real source
            add(store, V.rel(target), p.stem, ingested)


def main():
    store = {}
    load_legacy(store)
    derive_from_pages(store)

    out = [{"path": k,
            "ingested": v["ingested"],
            "pages_produced": sorted(v["pages"])}
           for k, v in sorted(store.items(), key=lambda kv: kv[1]["ingested"])]

    V.backup([DOT, OLD], "manifest")
    DOT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    removed = False
    if OLD.exists():
        OLD.unlink()
        removed = True

    print(f"✅ Wrote canonical manifest: {V.rel(DOT)} ({len(out)} sources)")
    if removed:
        print(f"🗑️  Removed duplicate: {V.rel(OLD)} (backed up to .backup/)")
    print("   Sources:")
    for e in out:
        print(f"     {e['ingested']}  {e['path']}  →  {', '.join(e['pages_produced'])}")


if __name__ == "__main__":
    main()
