#!/usr/bin/env python3
"""
merge_nodes.py — merge Claude-authored nodes/edges into the Graphify graph.

Used when Claude Code (Pro subscription) does the semantic extraction of newly
compiled pages itself — high quality, NO API, NO weak local model. Claude writes
a small JSON of nodes+edges; this merges them into graphify-out/graph.json.
Then run:  graphify cluster-only . --no-label   (re-cluster, free)  →  relabel.

Input JSON (authored by Claude):
{
  "nodes": [
    {"label": "Node name", "source_file": "7 - Wikipedia/Page.md",
     "type": "concept",
     "edges": [{"to": "existing or new node", "relation": "relates_to"}]}
  ]
}

Usage:  python3 merge_nodes.py <nodes.json>
"""
import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
GRAPH = VAULT / "graphify-out" / "graph.json"


def slug(label):
    s = re.sub(r"\s+", "_", label.strip())
    s = re.sub(r"[^\w֐-׿_-]", "", s)  # keep word chars + Hebrew
    return "c_" + s.lower()[:60]


def main():
    if len(sys.argv) < 2:
        print("usage: merge_nodes.py <nodes.json>"); sys.exit(1)
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes, links = g["nodes"], g.get("links", [])

    # index existing nodes by label and norm_label -> id
    by_label = {}
    ids = set()
    for n in nodes:
        ids.add(n.get("id"))
        for key in (n.get("label"), n.get("norm_label")):
            if key:
                by_label[key.strip().lower()] = n["id"]

    def resolve_or_create(label):
        k = label.strip().lower()
        if k in by_label:
            return by_label[k]
        nid = slug(label)
        base, i = nid, 2
        while nid in ids:
            nid = f"{base}_{i}"; i += 1
        ids.add(nid)
        by_label[k] = nid
        nodes.append({"label": label, "file_type": "doc", "source_file": "",
                      "source_location": "", "_origin": "claude", "community": -1,
                      "norm_label": label.lower(), "id": nid, "community_name": ""})
        return nid

    added_n = added_e = 0
    for item in new.get("nodes", []):
        nid = resolve_or_create(item["label"])
        # attach source file to the (possibly new) node
        for n in nodes:
            if n["id"] == nid and item.get("source_file"):
                n["source_file"] = item["source_file"]
                if n["_origin"] == "claude":
                    added_n += 1
                break
        for e in item.get("edges", []):
            tgt = resolve_or_create(e["to"])
            links.append({"relation": e.get("relation", "relates_to"),
                          "context": "claude", "confidence": "EXTRACTED",
                          "source_file": item.get("source_file", ""), "weight": 1.0,
                          "confidence_score": 0.9, "source": nid, "target": tgt})
            added_e += 1

    g["nodes"], g["links"] = nodes, links
    GRAPH.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    print(f"merged: +{added_n} new nodes, +{added_e} edges. total nodes={len(nodes)}, links={len(links)}")
    print("next: graphify cluster-only . --no-label   then re-label (Claude), then mark counter")


if __name__ == "__main__":
    main()
