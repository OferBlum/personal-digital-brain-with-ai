#!/usr/bin/env bash
# Run vault Python tools with durable, isolated dependencies in the workspace.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="$SCRIPT_DIR/vault-search-requirements.txt"

if [ -f /.dockerenv ]; then
  VENV=/workspace/.venv-vault-search-docker
  export OLLAMA_HOST="${OLLAMA_HOST:-http://host.docker.internal:11434}"
else
  VENV="${HOME}/Hermes-workspace/.venv-vault-search-host"
fi

# A /workspace bind mount survives Hermes' ephemeral Docker containers.
mkdir -p "$(dirname "$VENV")"
if [ ! -x "$VENV/bin/python" ] || ! cmp -s "$REQ" "$VENV/.requirements.txt" || \
   ! "$VENV/bin/python" -c 'import numpy, yaml' >/dev/null 2>&1; then
  echo "Preparing the vault search Python environment in $VENV" >&2
  python3 -m venv --clear "$VENV"
  "$VENV/bin/python" -m pip install --disable-pip-version-check -r "$REQ" >&2
  cp "$REQ" "$VENV/.requirements.txt"
fi
exec "$VENV/bin/python" "$@"
