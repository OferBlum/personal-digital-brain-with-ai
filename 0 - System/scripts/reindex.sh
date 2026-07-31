#!/bin/bash
# reindex.sh — update the semantic index after adding or editing files in the vault.
#   With no arguments: shows exactly which files changed, and indexes only those (incremental).
#   With arguments:    passes them straight through to embed_index.py (--status / --audit / --rebuild).
# The index itself is derived from the markdown and can be deleted and rebuilt at any time.
set -euo pipefail

# Vault root = two levels above this script, so the file works wherever the vault lives.
VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INDEXER="$VAULT/0 - System/scripts/embed_index.py"
OLLAMA="${OLLAMA_HOST:-http://localhost:11434}"

cd "$VAULT"

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
  exec python3 "$INDEXER" "$@"
fi

changes="$(python3 "$INDEXER" --changes)"
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
exec python3 "$INDEXER"
