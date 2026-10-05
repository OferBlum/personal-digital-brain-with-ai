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

Before this existed, each runtime had its own copy of the policy and protection
depended on which model was running. That is the opposite of a model-proof vault,
and this file is the fix.

THE POLICY IS EXACTLY ONE RULE — THE BOUNDARY IS A FOLDER, NOTHING ELSE:
  1. `3 - Journal` — the private folder (journal in `journal/` + every private file).
     Blocked anywhere it appears in the tool payload. Its contents are never read,
     and it is never even LISTED: every vault scan goes through iter_vault_files(),
     which prunes the folder before descending, so no script maps its filenames.

There is NO content-based rule. `private: true` in frontmatter is retired (2026-10-05):
it meant opening a file to learn whether you were allowed to open it, and it could
not be enforced on Bash/Grep at all. Anything private belongs in the private folder.

There is NO `_` rule either. `_`-prefixed files are generated system files, not
secrets: `0 - System/_cache.md` is required reading at session start.

KNOWN LIMIT — state it, don't paper over it: a recursive shell command started at the
vault root (find, grep -r) would descend into the folder without naming it. Agents must
start scans at a content folder or exclude it (`--exclude-dir='3 *'`); the vault-root
`.ignore` file makes ripgrep-based tools (Claude Code's Grep/Glob) skip it on their own.

Usage (reads the tool-call JSON payload on stdin):
    python3 privacy_guard.py --mode claude    # stderr + exit 2 to block; exit 0 to allow
    python3 privacy_guard.py --mode hermes    # {"decision":"block",...} / {}; always exit 0
    python3 privacy_guard.py --selftest       # run the built-in test matrix
"""
import sys, os, json, argparse, unicodedata
from pathlib import Path

PRIVATE_DIR = "3 - Journal"
BLOCKED_DIRS = (PRIVATE_DIR,)

# The vault is two levels above this script (<vault>/0 - System/scripts/privacy_guard.py).
# VAULT_ROOT overrides it, which is what the test matrix uses.
VAULT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def is_blocked(path):
    s = nfc(str(path))
    return any(nfc(d) in s for d in BLOCKED_DIRS)


def iter_vault_files(root=None, suffix=".md", prune=()):
    """Every file under `root` (default: the vault), sorted, never entering a blocked dir.

    Use this instead of Path.rglob(): rglob lists the private folder's filenames before
    any filter can drop them. os.walk top-down lets us remove the folder from `dirs`
    BEFORE it is scanned, so it is never opened, read, or mapped. `prune` adds
    non-private directory names to skip (noise like .git) the same way.
    """
    root = Path(root or VAULT)
    if is_blocked(root):
        return
    skip = {nfc(d) for d in (*BLOCKED_DIRS, *prune)}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if nfc(d) not in skip and not is_blocked(d))
        for name in sorted(files):
            if suffix is None or name.endswith(suffix):
                yield Path(dirpath) / name


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


def check(strings):
    """Returns a block reason, or None to allow. Folder rule only — never opens a file."""
    for s in strings:
        for d in BLOCKED_DIRS:
            if nfc(d) in nfc(s):
                return f"'{d}' is off-limits (privacy rule)"
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
    """Fails OPEN: Hermes runs ambient, and a hard stop there deadlocks the agent."""
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
        (tmp / PRIVATE_DIR / "journal").mkdir(parents=True)
        (tmp / PRIVATE_DIR / "journal" / "day.md").write_text("---\n---\nsecret\n", encoding="utf-8")
        (tmp / "notes").mkdir()
        flagged = tmp / "notes" / "flagged.md"
        flagged.write_text("---\ntype: note\nprivate: true\n---\nlegacy flag\n", encoding="utf-8")
        pub = tmp / "notes" / "public.md"
        pub.write_text("---\ntype: note\n---\nfine\n", encoding="utf-8")
        cache = tmp / "_cache.md"
        cache.write_text("---\n---\ncache\n", encoding="utf-8")

        global VAULT
        VAULT = tmp

        cases = [
            ("journal path",            {"tool_input": {"file_path": str(tmp / PRIVATE_DIR / "journal" / "day.md")}}, True),
            ("private dir in bash",     {"tool_input": {"command": f'ls "{PRIVATE_DIR}"'}},          True),
            ("private dir nested edit", {"tool_input": {"edits": [{"file_path": str(tmp / PRIVATE_DIR / "x.md")}]}}, True),
            ("legacy flag is not a rule",{"tool_input": {"file_path": str(flagged)}},                False),
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

        # The walker must never list the private folder — not even its filenames.
        listed = []
        real_scandir = os.scandir
        def spy(path=".", *a, **kw):
            listed.append(str(path))
            return real_scandir(path, *a, **kw)
        os.scandir = spy
        try:
            found = list(iter_vault_files(tmp))
        finally:
            os.scandir = real_scandir
        unmapped = (not any(is_blocked(p) for p in listed)
                    and not any(is_blocked(p) for p in found) and pub in found)
        print(f"  [{'PASS' if unmapped else 'FAIL'}] walker never lists private dir")
        ok &= unmapped

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
