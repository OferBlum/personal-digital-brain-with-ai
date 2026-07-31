#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code adapter for the vault's canonical privacy guard.

The policy itself lives in the vault, in ONE place, shared by every runtime:
    0 - System/scripts/privacy_guard.py
This file only wires it to Claude Code's PreToolUse contract (stderr + exit 2).
Do not put policy here — edit the canonical file instead, and every agent inherits it.

Fails CLOSED: if the canonical guard cannot be found or loaded (e.g. the vault lives in
a cloud-synced folder and is currently offline), the tool call is refused rather than
silently allowed.
"""
import sys, importlib.util
from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[1] / "0 - System" / "scripts" / "privacy_guard.py"


def fail_closed(msg):
    print(f"BLOCKED: {msg}", file=sys.stderr)
    sys.exit(2)


if not CANONICAL.is_file():
    fail_closed(f"canonical privacy guard not found at {CANONICAL}")

try:
    spec = importlib.util.spec_from_file_location("privacy_guard", CANONICAL)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
except Exception as e:
    fail_closed(f"canonical privacy guard failed to load: {e}")

sys.exit(guard.run_claude(sys.stdin.read()))
