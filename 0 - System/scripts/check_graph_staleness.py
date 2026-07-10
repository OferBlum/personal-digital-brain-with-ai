#!/usr/bin/env python3
"""
check_graph_staleness.py — how many sources were compiled since the last graph build.

Counts entries in the wiki manifest and compares to the count stored at the last
graph build. If the delta reaches THRESHOLD, it's time to refresh the graph.

  python3 check_graph_staleness.py         # report delta + whether a refresh is due
  python3 check_graph_staleness.py --mark  # record current count (call after a build)

Refresh policy: both extraction and community naming are done by Claude Code on
the Pro subscription — never the raw API, and never Ollama for extraction (too
weak). refresh_graph.sh (Ollama) is a full-rebuild fallback only.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vaultlib as V

THRESHOLD = 5  # number of new sources that triggers a graph refresh — change here

MANIFEST = V.WIKI / ".manifest.json"
COUNT_FILE = V.VAULT / "graphify-out" / ".graph_source_count"


def source_count() -> int:
    # wiki sources (manifest) + non-private notes — a new note counts toward
    # the refresh threshold just like a source
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        wiki = len(m) if isinstance(m, list) else len(m.get("sources", m))
    except Exception:
        wiki = 0
    try:
        notes = sum(1 for _ in V.iter_notes())
    except Exception:
        notes = 0
    return wiki + notes


def stored_count() -> int:
    try:
        return int(COUNT_FILE.read_text().strip())
    except Exception:
        return 0


def main():
    cur = source_count()
    if "--mark" in sys.argv[1:]:
        COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
        COUNT_FILE.write_text(str(cur), encoding="utf-8")
        print(f"marked graph build at {cur} sources")
        return
    delta = cur - stored_count()
    due = delta >= THRESHOLD
    print(json.dumps({"sources": cur, "since_last_build": delta,
                      "threshold": THRESHOLD, "refresh_due": due}, ensure_ascii=False))
    if due:
        print(f"⚠️ {delta} new sources since the last graph build (threshold {THRESHOLD}) — consider refreshing the graph.")


if __name__ == "__main__":
    main()
