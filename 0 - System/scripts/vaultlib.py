#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vaultlib — shared helpers for every vault script.
Centralizes the privacy rules, forgiving frontmatter parsing, unicode
normalization (NFC), wikilink resolution, and backups. Every other
script imports from here.
"""
import os, re, json, shutil, unicodedata
import yaml
from pathlib import Path
from datetime import datetime

# Vault root: from VAULT_ROOT (for tests), or two levels above scripts/.
VAULT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
WIKI  = VAULT / "7 - Wikipedia"
RAW   = WIKI / "raw"
NOTES = VAULT / "2 - Notes"
TOPICS = VAULT / "1 - Topics"
SYS   = VAULT / "0 - System"

JOURNAL = "3 - Journal"        # never touched, ever

# `_` files are generated system files (not content, not secrets) — we neither
# index nor compile them. This is *not* a privacy rule: the privacy rules are
# the journal and `private: true`, and nothing else.
SYSTEM_PREFIX = "_"

PREFERRED_KEYS = ["type", "subject", "tags", "background", "private", "status",
                  "wiki_sources", "provenance", "last_compiled",
                  "generated_by", "generated_at", "verified"]


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


# Frontmatter delimiter — a line that is exactly `---` (what graphify expects).
_FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def split_frontmatter(text):
    """Returns (fm_lines | None, body).

    Slices the original string rather than going through splitlines/join, so the
    file's trailing newline survives (long-standing bug: every write ate one \\n
    off the end).
    """
    if not text.startswith("---"):
        return None, text
    m = _FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1).splitlines(), text[m.end():]


def _without_timestamps(cls):
    """Resolver map minus dates — so dates stay strings and need no quoting."""
    return {
        ch: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
        for ch, resolvers in cls.yaml_implicit_resolvers.items()
    }


class VaultLoader(yaml.SafeLoader):
    """SafeLoader without automatic date detection — last_compiled/created stay strings."""


VaultLoader.yaml_implicit_resolvers = _without_timestamps(yaml.SafeLoader)


class VaultDumper(yaml.SafeDumper):
    """SafeDumper that quotes [[wikilinks]] and writes an empty value as `key:`, not `key: null`."""

    def increase_indent(self, flow=False, indentless=False):
        # List items indented by two spaces — the style already used across the vault.
        return super().increase_indent(flow, False)


def _repr_str(dumper, data):
    # `[[` and `#` break YAML as a bare value (flow list / start of a comment) — quote them.
    style = '"' if ("[[" in data or data.lstrip().startswith("#")) else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


def _repr_none(dumper, _data):
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")


VaultDumper.add_representer(str, _repr_str)
VaultDumper.add_representer(type(None), _repr_none)
# No date resolver on write either — otherwise pyyaml quotes every 2026-07-11.
VaultDumper.yaml_implicit_resolvers = _without_timestamps(yaml.SafeDumper)

# Bare values YAML misreads:
#   [[link]]  → parsed as a nested flow list
#   #tag      → parsed as a comment, and the value is lost
_UNSAFE_VALUE = r'(\[\[|#)'
_UNSAFE_SCALAR = re.compile(r'^(\s*[^:\n]+:[ \t]+)(' + _UNSAFE_VALUE + r'.*)$')
_UNSAFE_ITEM   = re.compile(r'^(\s*-[ \t]+)(' + _UNSAFE_VALUE + r'.*)$')


def _quote_unsafe_scalars(fm_text):
    """Quote bare values starting with [[ or # before handing them to yaml."""
    out = []
    for line in fm_text.splitlines():
        m = _UNSAFE_SCALAR.match(line) or _UNSAFE_ITEM.match(line)
        if m:
            val = m.group(2).rstrip()
            if not (val.startswith('"') or val.startswith("'")):
                line = m.group(1) + '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"'
        out.append(line)
    return "\n".join(out)


def _none_to_empty(v):
    """Keeps the old contract: an empty value reaches readers as "", not None."""
    if v is None:
        return ""
    if isinstance(v, list):
        return [_none_to_empty(x) for x in v]
    if isinstance(v, dict):
        return {k: _none_to_empty(x) for k, x in v.items()}
    return v


def _empty_to_none(v):
    if v == "":
        return None
    if isinstance(v, list):
        return [_empty_to_none(x) for x in v]
    if isinstance(v, dict):
        return {k: _empty_to_none(x) for k, x in v.items()}
    return v


def _parse_fm_legacy(fm_lines):
    """The old parser — a safety net for files yaml chokes on (e.g. ': ' inside a value)."""
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
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [_strip_quotes(x) for x in inner.split(",")] if inner else []
        else:
            meta[key] = _strip_quotes(val)
        i += 1
    return meta


def parse_fm(fm_lines):
    """Parse frontmatter into a dict. Full YAML (nested values included), with a forgiving fallback."""
    text = _quote_unsafe_scalars("\n".join(fm_lines))
    try:
        data = yaml.load(text, Loader=VaultLoader)
    except yaml.YAMLError:
        return _parse_fm_legacy(fm_lines)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return _parse_fm_legacy(fm_lines)
    return {str(k): _none_to_empty(v) for k, v in data.items()}


def dump_fm(meta):
    keys = [k for k in PREFERRED_KEYS if k in meta] + \
           [k for k in meta if k not in PREFERRED_KEYS]
    ordered = {k: _empty_to_none(meta[k]) for k in keys}
    body = yaml.dump(
        ordered,
        Dumper=VaultDumper,
        allow_unicode=True,     # non-ASCII as-is, no \uXXXX escapes
        sort_keys=False,        # PREFERRED_KEYS order is preserved
        default_flow_style=False,
        width=10 ** 6,          # no line wrapping — a long background stays on one line
    )
    return "---\n" + body.rstrip("\n") + "\n---"


def read_page(path):
    text = Path(path).read_text(encoding="utf-8")
    fm_lines, body = split_frontmatter(text)
    meta = parse_fm(fm_lines) if fm_lines is not None else {}
    return meta, body


def render_page(meta, body):
    return dump_fm(meta) + "\n" + body if meta else body


# ---------- page discovery (privacy-aware) ----------

# System files inside 7 - Wikipedia/ that are not content pages.
# index.md / log.md are generated catalogs; WIKI-GUIDE.md is hand-written docs about
# the folder itself. None of them is a compiled page, so none carries page provenance.
NON_CONTENT = {"index.md", "log.md", "WIKI-GUIDE.md"}


def iter_wiki_pages(include_private=False):
    """Content pages in 7 - Wikipedia/ only (no raw/, no system files, no _ , no private)."""
    for p in sorted(WIKI.glob("*.md")):
        name = nfc(p.name)
        if name in NON_CONTENT:
            continue
        if name.startswith(SYSTEM_PREFIX):   # system files (_cache etc.) are not content pages
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        if not include_private and str(meta.get("private", "")).lower() == "true":
            continue
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "report" in tags:                 # auto-generated report files
            continue
        yield p, meta, body


def iter_notes(include_private=False):
    """Notes in 2 - Notes/ (no _ , no private) — the same filters as iter_wiki_pages."""
    for p in sorted(NOTES.glob("*.md")):
        if nfc(p.name).startswith(SYSTEM_PREFIX):
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        if not include_private and str(meta.get("private", "")).lower() == "true":
            continue
        yield p, meta, body


def iter_topics(include_private=False):
    """Topic pages in 1 - Topics/ — the same filters as iter_notes."""
    for p in sorted(TOPICS.glob("*.md")):
        if nfc(p.name).startswith(SYSTEM_PREFIX):
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        if not include_private and str(meta.get("private", "")).lower() == "true":
            continue
        yield p, meta, body


def all_md_index():
    """Map nfc(stem) -> [paths] for the whole vault except the journal.
    Resolves wikilinks without depending on filesystem unicode normalization."""
    idx = {}
    for p in VAULT.rglob("*.md"):
        if is_forbidden(p):
            continue
        # Backups are not real files — without this filter every backup makes
        # every link ambiguous.
        if ".backup" in p.parts or "graphify-out" in p.parts:
            continue
        idx.setdefault(nfc(p.stem), []).append(p)
    return idx


def resolve_link(inner, md_index=None):
    """
    Returns (status, path_or_none):
      status = 'ok' | 'missing' | 'ambiguous'
    inner = whatever is inside [[...]], possibly with |alias and possibly a path.
    """
    inner = nfc(inner.split("|")[0].strip())
    cand = inner[:-3] if inner.endswith(".md") else inner
    if "/" in cand:                       # full path
        p = VAULT / (cand + ".md")
        return ("ok", p) if p.exists() else ("missing", None)
    # Name only → search the vault
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
    """Copies the files to 7 - Wikipedia/.backup/<timestamp-label>/ before modifying them."""
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
