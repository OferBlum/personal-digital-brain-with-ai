#!/bin/bash
# refresh_graph.sh [ollama|claude] — refresh the knowledge graph (Graphify), privacy-aware.
#   ollama (default) = free, medium quality, local
#   claude           = high quality, costs tokens (API subscription)
# Note: a fresh run generates community names from the model; for high-quality
#       names, ask Claude Code to "run graphify" and it will also remap the names.
# This script is a FALLBACK for a full rebuild — the normal path is the
# Claude Code refresh described in SKILL-ingest step 10.
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
# vault root = two levels above this script (0 - System/scripts/)
VAULT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$VAULT" || exit 1
BACKEND="${1:-ollama}"

echo "[1/2] Updating .graphifyignore (journal and private files excluded)..."
python3 "$VAULT/0 - System/scripts/gen_graphifyignore.py" --apply

if [ "$BACKEND" = "claude" ]; then
  export ANTHROPIC_API_KEY="$(grep -m1 '^ANTHROPIC_API_KEY=' "$HOME/.hermes/.env" | cut -d= -f2- | tr -d '"')"
  MODEL="claude-sonnet-4-6"
else
  MODEL="llama3.1:8b"
fi

echo "[2/2] graphify extract  (backend=$BACKEND model=$MODEL) ..."
graphify extract . --backend "$BACKEND" --model "$MODEL"

# reset the "sources since last build" counter
python3 "$VAULT/0 - System/scripts/check_graph_staleness.py" --mark
echo "Done. The graph: $VAULT/graphify-out/graph.html"
echo "Note: for high-quality community names — ask Claude Code to remap them (Pro subscription, not API)."
