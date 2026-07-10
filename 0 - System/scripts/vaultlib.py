#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vaultlib — shared helpers for all vault scripts.
Centralizes the privacy rules, forgiving frontmatter parsing, unicode
normalization (NFC), wikilink resolution, and backups. Every other
script imports from here.
"""
import os, re, json, shutil, unicodedata
from pathlib import Path
from datetime import datetime

# Vault root: from VAULT_ROOT (for tests), or two levels above scripts/.
VAULT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
WIKI  = VAULT / "7 - Wikipedia"
RAW   = WIKI / "raw"
NOTES = VAULT / "2 - Notes"
SYS   = VAULT / "0 - System"

JOURNAL = "3 - Journal"           # never touched, ever
ALLOW_UNDERSCORE = {"_cache.md", "_cache-archive.md"}  # exception to the _ rule

PREFERRED_KEYS = ["subject", "tags", "background", "private",
                  "wiki_sources", "last_compiled", "provenance"]


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def is_forbidden(path):
    """The absolute privacy rule: the journal."""
    return JOURNAL in nfc(str(path))


def today():
    return datetime.now().strftime("%Y-%m-%d")


# ---------- frontmatter ----------

def _strip_quotes(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    return v


def split_frontmatter(text):
    """Returns (fm_lines | None, body)."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, text
    return lines[1:end], "\n".join(lines[end + 1:])


def parse_fm(fm_lines):
    """Forgiving parser — survives unquoted [[wikilinks]] (which pyyaml chokes on)."""
    meta, i, n = {}, 0, len(fm_lines)
    while i < n:
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([^:#][^:]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        if val == "":
            items, j = [], i + 1
            while j < n and re.match(r"^\s*-\s+", fm_lines[j]):
                items.append(_strip_quotes(re.sub(r"^\s*-\s+", "", fm_lines[j])))
                j += 1
            if items:
                meta[key] = items
                i = j
                continue
            meta[key] = ""
            i += 1
            continue
        # inline list: [a, b]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [_strip_quotes(x) for x in inner.split(",")] if inner else []
        else:
            meta[key] = _strip_quotes(val)
        i += 1
    return meta


def _emit_val(v):
    s = str(v)
    if "[[" in s and not (s.startswith('"') and s.endswith('"')):
        return f'"{s}"'
    return s


def dump_fm(meta):
    keys = [k for k in PREFERRED_KEYS if k in meta] + \
           [k for k in meta if k not in PREFERRED_KEYS]
    out = ["---"]
    for k in keys:
        v = meta[k]
        if isinstance(v, list):
            out.append(f"{k}:")
            for it in v:
                out.append(f"  - {_emit_val(it)}")
        else:
            out.append(f"{k}: {_emit_val(v)}" if v != "" else f"{k}:")
    out.append("---")
    return "\n".join(out)


def read_page(path):
    text = Path(path).read_text(encoding="utf-8")
    fm_lines, body = split_frontmatter(text)
    meta = parse_fm(fm_lines) if fm_lines is not None else {}
    return meta, body


def render_page(meta, body):
    return dump_fm(meta) + "\n" + body if meta else body


# ---------- page discovery (privacy-aware) ----------

# system files in 7 - Wikipedia/ that are not content pages
NON_CONTENT = {"index.md", "log.md"}


def iter_wiki_pages(include_private=False):
    """Content pages in 7 - Wikipedia/ only (no raw/, no system files, no _ , no private)."""
    for p in sorted(WIKI.glob("*.md")):
        name = nfc(p.name)
        if name in NON_CONTENT:
            continue
        if name.startswith("_"):          # system files (_cache etc.) are not content pages
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        if not include_private and str(meta.get("private", "")).lower() == "true":
            continue
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "report" in tags:              # auto-generated report files
            continue
        yield p, meta, body


def iter_notes(include_private=False):
    """Notes in 2 - Notes/ (no _ , no private) — same filters as iter_wiki_pages."""
    for p in sorted(NOTES.glob("*.md")):
        if nfc(p.name).startswith("_"):
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        if not include_private and str(meta.get("private", "")).lower() == "true":
            continue
        yield p, meta, body


def all_md_index():
    """Dict nfc(stem) -> [paths] for the whole vault except the journal.
    Resolves wikilinks without depending on filesystem normalization."""
    idx = {}
    for p in VAULT.rglob("*.md"):
        if is_forbidden(p):
            continue
        idx.setdefault(nfc(p.stem), []).append(p)
    return idx


def resolve_link(inner, md_index=None):
    """
    Returns (status, path_or_none):
      status = 'ok' | 'missing' | 'ambiguous'
    inner = the content inside [[...]], possibly with |alias and possibly a path.
    """
    inner = nfc(inner.split("|")[0].strip())
    cand = inner[:-3] if inner.endswith(".md") else inner
    if "/" in cand:                       # full path
        p = VAULT / (cand + ".md")
        return ("ok", p) if p.exists() else ("missing", None)
    # bare name → search the vault
    md_index = md_index or all_md_index()
    matches = md_index.get(nfc(cand), [])
    if len(matches) == 1:
        return ("ok", matches[0])
    if len(matches) == 0:
        return ("missing", None)
    return ("ambiguous", None)


def rel(path):
    return nfc(str(Path(path).relative_to(VAULT)))


# ---------- backups ----------

def backup(paths, label):
    """Copies the files to 7 - Wikipedia/.backup/<timestamp-label>/ before changing them."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = WIKI / ".backup" / f"{stamp}-{label}"
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        target = dest / p.relative_to(VAULT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    return dest
