#!/bin/bash
# reindex.sh — update the semantic index after adding or editing files in the vault.
#   With no arguments: shows exactly which files changed, and indexes only those (incremental).
#   With arguments:    passes them straight through to embed_index.py (--status / --audit / --rebuild).
# The index itself is derived from the markdown and can be deleted and rebuilt at any time.
set -euo pipefail

# Vault root = VAULT_ROOT, or two levels above this script, so the file works wherever the vault lives.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${VAULT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
INDEXER="$SCRIPT_DIR/embed_index.py"
PYTHON="$SCRIPT_DIR/vault-python.sh"
if [ -f /.dockerenv ]; then
  export OLLAMA_HOST="${OLLAMA_HOST:-http://host.docker.internal:11434}"
fi
OLLAMA="${OLLAMA_HOST:-http://localhost:11434}"

cd "$VAULT"

# The indexing boundary is folder-only (safe_input.py) — the private folder is never read nor mapped.

# embed_index.py only discovers that Ollama is down inside embed(), after it has already
# read and chunked every file. Better to fail here, in the first second, with a message
# that says what to do.
require_ollama() {
  if ! curl -s -m 3 -o /dev/null "$OLLAMA/api/tags"; then
    echo "🔴 Ollama is not running ($OLLAMA) — start Ollama and try again." >&2
    exit 1
  fi
}

if [ $# -gt 0 ]; then
  # --status and --audit generate no embeddings; only --rebuild needs Ollama.
  case " $* " in *" --rebuild "*) require_ollama ;; esac
  exec bash "$PYTHON" "$INDEXER" "$@"
fi

changes="$(bash "$PYTHON" "$INDEXER" --changes)"
if [ -z "$changes" ]; then
  echo "✅ The semantic index is up to date — nothing to do."
  exit 0
fi

new=$(printf '%s\n' "$changes" | grep -c '^+ ' || true)
mod=$(printf '%s\n' "$changes" | grep -c '^~ ' || true)
del=$(printf '%s\n' "$changes" | grep -c '^- ' || true)
echo "🔎 $new new · $mod changed · $del deleted"
printf '%s\n\n' "$changes"

require_ollama
exec bash "$PYTHON" "$INDEXER"
