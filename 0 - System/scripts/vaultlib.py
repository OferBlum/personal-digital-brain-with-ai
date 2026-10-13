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

# Shared privacy: the protected folder and symlinks only; frontmatter is never a privacy signal.
# PRIVATE_DIR = the private folder (journal + every private file) — never touched, never mapped.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacy_guard import (PRIVATE_DIR, is_blocked, iter_vault_files,
                           read_public_page, PrivacyDenied, HEADER_FENCE)  # noqa: E402
JOURNAL = PRIVATE_DIR  # alias kept for backward compatibility

# `_` files are generated system files (not content, not secrets) — we neither
# index nor compile them. This is *not* a privacy rule; the protected folder is
# enforced separately.
SYSTEM_PREFIX = "_"

PREFERRED_KEYS = ["type", "subject", "tags", "background", "private", "status",
                  "wiki_sources", "provenance", "last_compiled",
                  "generated_by", "generated_at", "verified"]


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def is_forbidden(path):
    """Exclude the protected folder and symlinks; frontmatter never excludes."""
    return is_blocked(path)


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
    """Excluded files are nonexistent; a malformed header reads as {} and stays in the body."""
    meta, body = read_public_page(path)
    return {k: _none_to_empty(v) for k, v in meta.items()}, body


def has_broken_header(meta, body):
    """True for a page whose malformed header was kept, unparsed, at the top of the body."""
    return not meta and HEADER_FENCE.match(body) is not None


def render_page(meta, body):
    # New metadata above a malformed header would create two headers — fix it by hand first.
    if meta and HEADER_FENCE.match(body):
        raise ValueError("Malformed frontmatter must be fixed by hand before adding fields.")
    return dump_fm(meta) + "\n" + body if meta else body


# ---------- page discovery (privacy-aware) ----------

# System files inside 7 - Wikipedia/ that are not content pages.
# index.md / log.md are generated catalogs; WIKI-GUIDE.md is hand-written docs about
# the folder itself. None of them is a compiled page, so none carries page provenance.
NON_CONTENT = {"index.md", "log.md", "WIKI-GUIDE.md"}


def _top_level_pages(root):
    if is_forbidden(root) or not root.is_dir():
        return
    for path in sorted(root.glob('*.md')):
        if not nfc(path.name).startswith(SYSTEM_PREFIX) and not is_forbidden(path):
            yield path


def iter_wiki_pages():
    """Content pages in 7 - Wikipedia/ only (no raw/, no system files, no _)."""
    for p in _top_level_pages(WIKI):
        name = nfc(p.name)
        if name in NON_CONTENT:
            continue
        if name.startswith("_"):          # system files (_cache etc.) are not content pages
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if "report" in tags:              # auto-generated report files
            continue
        yield p, meta, body


def iter_notes():
    """Notes in 2 - Notes/ (no _) — the same filters as iter_wiki_pages."""
    for p in _top_level_pages(NOTES):
        if nfc(p.name).startswith("_"):
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        yield p, meta, body


def iter_topics():
    """Topic pages in 1 - Topics/ — the same filters as iter_notes."""
    for p in _top_level_pages(TOPICS):
        if nfc(p.name).startswith(SYSTEM_PREFIX):
            continue
        if is_forbidden(p):
            continue
        meta, body = read_page(p)
        yield p, meta, body


def all_md_index():
    """Index public stems under explicit allowed roots, never the vault root."""
    idx = {}
    for root in (WIKI, NOTES, TOPICS, SYS):
        for p in iter_vault_files(root, prune=('.backup', 'graphify-out')):
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
    def visible(path):
        p = Path(path)
        try:
            relative = p.relative_to(VAULT)
        except ValueError:
            return False
        if not relative.parts or relative.parts[0] not in {WIKI.name, NOTES.name, TOPICS.name, SYS.name}:
            return False
        if '..' in relative.parts or is_forbidden(p):
            return False
        return p.is_file()

    if '/' in cand or '\\' in cand:
        if '\\' in cand or Path(cand).is_absolute() or '..' in Path(cand).parts:
            return ('missing', None)
        p = VAULT / (cand + '.md')
        return ('ok', p) if visible(p) else ('missing', None)
    md_index = all_md_index() if md_index is None else md_index
    matches = [p for p in md_index.get(nfc(cand), []) if visible(p)]
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
    paths = [Path(p) for p in paths]
    if not re.fullmatch(r'[\w-]+', label):
        raise PrivacyDenied()
    # Reject the whole batch before creating output or copying any body.
    for p in paths:
        try:
            relative = p.relative_to(VAULT)
        except ValueError:
            raise PrivacyDenied() from None
        if '..' in relative.parts or is_forbidden(p):
            raise PrivacyDenied()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = WIKI / ".backup" / f"{stamp}-{label}"
    if is_forbidden(dest):
        raise PrivacyDenied()
    for p in paths:
        if not p.exists():
            continue
        target = dest / p.relative_to(VAULT)
        if is_forbidden(p) or is_forbidden(target):
            raise PrivacyDenied()
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_forbidden(p) or is_forbidden(target):
            raise PrivacyDenied()
        shutil.copy2(p, target)
    return dest
