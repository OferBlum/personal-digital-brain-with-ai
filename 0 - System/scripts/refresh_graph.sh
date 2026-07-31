#!/bin/bash
# refresh_graph.sh [ollama|claude] — refresh the knowledge graph (Graphify), with privacy exclusions.
#   ollama (default) = free, medium quality, fully local
#   claude           = high quality, costs tokens (API subscription)
# Note: a fresh run generates community names from the model. For high-quality names,
#       ask Claude Code to "run graphify" — it will re-map the names as well.
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"

# Vault root = two levels above this script, so the file works wherever the vault lives.
VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$VAULT" || exit 1
BACKEND="${1:-ollama}"

echo "[1/2] Updating .graphifyignore (journal and private files excluded)..."
python3 "$VAULT/0 - System/scripts/gen_graphifyignore.py" --apply

if [ "$BACKEND" = "claude" ]; then
  export ANTHROPIC_API_KEY="$(grep -m1 '^ANTHROPIC_API_KEY=' "$HOME/.secrets/anthropic.env" | cut -d= -f2- | tr -d '"')"
  MODEL="claude-sonnet-4-6"
else
  MODEL="llama3.1:8b"
fi

echo "[2/2] graphify extract  (backend=$BACKEND model=$MODEL) ..."
graphify extract . --backend "$BACKEND" --model "$MODEL"

# reset the "sources since last build" counter
python3 "$VAULT/0 - System/scripts/check_graph_staleness.py" --mark
echo "Done. The graph: $VAULT/graphify-out/graph.html"
echo "Note: for high-quality community names, ask Claude Code to re-map them (Pro subscription, not the API)."
