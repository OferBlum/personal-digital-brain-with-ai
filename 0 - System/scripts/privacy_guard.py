#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
privacy_guard.py — THE canonical privacy guard for this vault.

One implementation, shared by every agent runtime. Each runtime's pre-tool hook is a
thin wrapper that calls this file with the right --mode:

    Claude Code   .claude/privacy-guard.py                 --mode claude
    Hermes        ~/.hermes/agent-hooks/privacy-guard.py   --mode hermes
    Codex         reached through Hermes (provider openai-codex) — inherits the above
    anything new  point its hook here too

This matters more than it looks. Before it was unified, each runtime shipped its own
guard, and they had drifted: one enforced both rules, the other only matched the
journal folder name and never opened a file — so `private: true` was not enforced
there at all. Protection depended on which model happened to be running. A vault whose
privacy is only as strong as its weakest agent is not a private vault.

THE POLICY IS EXACTLY TWO RULES:
  1. `3 - Journal`  — the journal. Blocked anywhere it appears in the tool payload.
  2. `private: true` — blocked for any tool call that names a single resolvable file.

There is NO `_` rule. `_`-prefixed files are generated system files, not secrets:
`7 - Wikipedia/_cache.md` is required reading at session start. Blocking them
contradicted the session rules and broke the ambient agent.

KNOWN LIMIT — state it, don't paper over it: a Bash or Grep invocation names no single
file, so rule 2 cannot be evaluated there. Those calls are covered by rule 1 plus the
script-level filters (vaultlib.py, gen_graphifyignore.py, embed_index.py --audit).

Usage (reads the tool-call JSON payload on stdin):
    python3 privacy_guard.py --mode claude    # stderr + exit 2 to block; exit 0 to allow
    python3 privacy_guard.py --mode hermes    # {"decision":"block",...} / {}; always exit 0
    python3 privacy_guard.py --selftest       # run the built-in test matrix
"""
import sys, os, json, argparse, unicodedata
from pathlib import Path

JOURNAL = "3 - Journal"
PRIVATE_KEY = "private"

# The vault is two levels above this script (<vault>/0 - System/scripts/privacy_guard.py).
# VAULT_ROOT overrides it, which is what the test matrix uses.
VAULT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])

FM_LIMIT = 4000          # only ever read the frontmatter block, never a whole file


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def collect_strings(obj, out):
    """Every string anywhere in the payload, at any nesting depth.

    Deliberately exhaustive rather than a fixed key list: a fixed list misses
    payload shapes like MultiEdit's per-edit dicts.
    """
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_strings(v, out)


def is_private_md(raw):
    """True if `raw` points at an existing vault .md file flagged `private: true`.

    Fails open on anything unexpected: a path that doesn't exist is a file being
    created, and an unreadable file is not evidence of privacy. Rule 1 is the hard gate.
    """
    try:
        s = str(raw).strip().strip('"').strip("'")
        if not s.endswith(".md"):
            return False
        p = Path(s)
        if not p.is_absolute():
            p = VAULT / s
        p = p.resolve()
        if not str(p).startswith(str(VAULT.resolve())) or not p.is_file():
            return False
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(FM_LIMIT)
        if not head.startswith("---"):
            return False
        end = head.find("\n---", 3)
        fm = head[:end] if end != -1 else head
        for line in fm.splitlines():
            if line.strip().replace(" ", "") == f"{PRIVATE_KEY}:true":
                return True
    except Exception:
        return False
    return False


def check(strings):
    """Returns a block reason, or None to allow."""
    # Rule 1 — the journal, checked against every string first and unconditionally.
    for s in strings:
        if nfc(JOURNAL) in nfc(s):
            return f"'{JOURNAL}' is off-limits (privacy rule 1)"
    # Rule 2 — private-flagged files.
    for s in strings:
        if is_private_md(s):
            return f"the file is marked '{PRIVATE_KEY}: true' and is not accessible (privacy rule 2)"
    return None


def evaluate(payload):
    strings = []
    collect_strings(payload.get("tool_input"), strings)
    return check(strings)


# ---------- runtime adapters ----------

def run_claude(stdin_text):
    """Fails CLOSED: a payload we cannot parse is refused, because a human can retry."""
    try:
        payload = json.loads(stdin_text)
    except Exception:
        print("BLOCKED: privacy-guard could not parse tool input", file=sys.stderr)
        return 2
    reason = evaluate(payload)
    if reason:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 2
    return 0


def run_hermes(stdin_text):
    """Fails OPEN: an ambient agent must not deadlock on a guard it cannot load."""
    try:
        payload = json.loads(stdin_text)
    except Exception:
        print("{}")
        return 0
    reason = evaluate(payload)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    else:
        print("{}")
    return 0


def selftest():
    """Exercises the policy against a throwaway fixture vault. Prints a pass/fail matrix."""
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp(prefix="pg-selftest-"))
    try:
        (tmp / JOURNAL).mkdir(parents=True)
        (tmp / JOURNAL / "day.md").write_text("---\n---\nsecret\n", encoding="utf-8")
        (tmp / "notes").mkdir()
        priv = tmp / "notes" / "private.md"
        priv.write_text(f"---\ntype: note\n{PRIVATE_KEY}: true\n---\nsecret\n", encoding="utf-8")
        pub = tmp / "notes" / "public.md"
        pub.write_text("---\ntype: note\n---\nfine\n", encoding="utf-8")
        cache = tmp / "_cache.md"
        cache.write_text("---\n---\ncache\n", encoding="utf-8")

        global VAULT
        VAULT = tmp

        cases = [
            ("journal path",            {"tool_input": {"file_path": str(tmp / JOURNAL / "day.md")}}, True),
            ("journal in bash command", {"tool_input": {"command": f'ls "{JOURNAL}"'}},               True),
            ("private: true file",      {"tool_input": {"file_path": str(priv)}},                    True),
            ("private nested MultiEdit",{"tool_input": {"edits": [{"file_path": str(priv)}]}},       True),
            ("normal file",             {"tool_input": {"file_path": str(pub)}},                     False),
            ("_cache.md is readable",   {"tool_input": {"file_path": str(cache)}},                   False),
            ("non-existent path",       {"tool_input": {"file_path": str(tmp / "nope.md")}},         False),
        ]
        ok = True
        for name, payload, want_block in cases:
            got = evaluate(payload) is not None
            mark = "PASS" if got == want_block else "FAIL"
            ok &= got == want_block
            print(f"  [{mark}] {name:<26} block={got} (want {want_block})")

        # stdin-parse behavior differs per adapter, on purpose
        c = run_claude("not json")
        h = run_hermes("not json")
        print(f"  [{'PASS' if c == 2 else 'FAIL'}] malformed stdin -> claude fails closed (exit {c})")
        print(f"  [{'PASS' if h == 0 else 'FAIL'}] malformed stdin -> hermes fails open  (exit {h})")
        ok &= (c == 2 and h == 0)
        print("\nSELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["claude", "hermes"], default="claude")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    stdin_text = sys.stdin.read()
    sys.exit(run_claude(stdin_text) if args.mode == "claude" else run_hermes(stdin_text))


if __name__ == "__main__":
    main()
