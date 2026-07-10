#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, json, unicodedata

JOURNAL = "3 - Journal"

def norm(s):
    return unicodedata.normalize("NFC", s or "")

try:
    data = json.load(sys.stdin)
except Exception:
    print("BLOCKED: privacy-guard could not parse tool input", file=sys.stderr)
    sys.exit(2)

ti = data.get("tool_input", {}) or {}
candidates = [
    ti.get("file_path"),
    ti.get("path"),
    ti.get("command"),   # Bash
    ti.get("pattern"),   # Grep / Glob
    ti.get("glob"),
]
blob = norm(" ".join(c for c in candidates if c))

if norm(JOURNAL) in blob:
    print(f"BLOCKED: '{JOURNAL}' is off-limits (privacy rule)", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
