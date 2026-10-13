"""Folder boundary for the semantic index.

Only top-level markdown under FOLDERS is considered (so `raw/` and `.backup/`
stay out). Privacy comes from the folder boundary alone: the protected folder
and symlinked paths are refused, and every read goes through the guard's
NOFOLLOW reader. Frontmatter comes from the same parser the guard and vaultlib
use (privacy_guard.split_header), so a file reads the same here as for agents.
Neither vault-root nor protected-area scans are permitted. System-prefixed files
are out of scope.
"""
from pathlib import PurePosixPath

import vaultlib as V
import privacy_guard as G

FOLDERS = G.CONTENT_ROOT_NAMES


def _relative_path(rel):
    if not isinstance(rel, str) or not rel or '\\' in rel:
        return None
    p = PurePosixPath(rel)
    if (p.is_absolute() or len(p.parts) != 2 or p.as_posix() != rel
            or p.parts[0] not in FOLDERS or not rel.endswith('.md')
            or p.name.startswith(V.SYSTEM_PREFIX)):
        return None
    return V.VAULT / rel


def _outside(path):
    """Protected folder or a symlink anywhere on the path."""
    return G.folder_blocked(path) or G.has_symlink(path)


def cache_permitted(rel):
    """Folder-only cache preflight; deleted sources may be filtered by search.

    A genuinely absent regular path is safe to retain until an update.
    """
    path = _relative_path(rel)
    if path is None:
        return False
    try:
        return not _outside(path) and (not path.exists() or path.is_file())
    except OSError:
        return False


def permitted(rel):
    """True only for an existing, non-symlinked source inside the boundary."""
    path = _relative_path(rel)
    if path is None:
        return False
    try:
        return not _outside(path) and path.is_file()
    except OSError:
        return False


def sources():
    """(rel, path) for every file inside the boundary. Lists only the allowed folders."""
    for folder in FOLDERS:
        root = V.VAULT / folder
        if _outside(root) or not root.is_dir():
            continue
        for path in sorted(root.glob('*.md')):
            rel = f'{folder}/{V.nfc(path.name)}'
            if permitted(rel):
                yield rel, path


def read(rel):
    """(meta, body) for a permitted file, or None. A broken header reads as {}."""
    if not permitted(rel):
        return None
    try:
        return V.read_page(V.VAULT / rel)
    except OSError:
        return None
