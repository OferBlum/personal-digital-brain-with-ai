"""Input boundary for the semantic index: folder-only.

Privacy in this vault is a folder rule and nothing else (privacy_guard.py): the private
folder is never read and never listed. Everything the indexer may read is defined
POSITIVELY, before any file is opened, by FOLDERS below — top-level .md files in those
folders, minus `_` system files. No frontmatter flag, approval manifest or snapshot is
consulted; nothing outside FOLDERS is ever opened or listed.

FOLDERS is a scope choice (what counts as knowledge), not a privacy rule — the privacy
rule is enforced independently by is_blocked() on every path, including symlink targets.
"""
from pathlib import Path, PurePosixPath

import vaultlib as V

FOLDERS = ('7 - Wikipedia', '2 - Notes', '1 - Topics')


def permitted(rel):
    """True if `rel` (vault-relative, posix) is inside the index boundary and still exists."""
    if not isinstance(rel, str) or not rel or '\\' in rel:
        return False
    p = PurePosixPath(rel)
    if (p.is_absolute() or len(p.parts) != 2 or p.parts[0] not in FOLDERS
            or not rel.endswith('.md') or p.name.startswith(V.SYSTEM_PREFIX)
            or V.is_forbidden(rel)):
        return False
    path = V.VAULT / rel
    try:
        # A symlink could point anywhere — including the private folder. Refuse them.
        return path.is_file() and not path.is_symlink() and not V.is_forbidden(path.resolve())
    except OSError:
        return False


def sources():
    """(rel, path) for every file inside the boundary. Lists only the allowed folders."""
    for folder in FOLDERS:
        root = V.VAULT / folder
        if not root.is_dir():
            continue
        for path in sorted(root.glob('*.md')):
            rel = f'{folder}/{V.nfc(path.name)}'
            if permitted(rel):
                yield rel, path


def read(rel):
    """(meta, body) for a permitted file, or None."""
    if not permitted(rel):
        return None
    try:
        content = (V.VAULT / rel).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    fm, body = V.split_frontmatter(content)
    meta = V.parse_fm(fm) if fm is not None else {}
    return meta, body
