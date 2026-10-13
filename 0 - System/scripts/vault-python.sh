#!/usr/bin/env bash
# Run vault Python tools without automatic setup; use --setup explicitly to prepare dependencies.
set -euo pipefail
SETUP=false
if [ "${1:-}" = "--setup" ]; then
  SETUP=true
  shift
fi
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="$SCRIPT_DIR/vault-search-requirements.txt"

if [ -f /.dockerenv ]; then
  VENV=/workspace/.venv-vault-search-docker
  export OLLAMA_HOST="${OLLAMA_HOST:-http://host.docker.internal:11434}"
else
  VENV="${HOME}/Hermes-workspace/.venv-vault-search-host"
fi

# Normal execution checks readiness only: no directories, installs or repairs.
if [ ! -r "$REQ" ]; then
  printf 'Vault Python requirements file is unavailable: %s\n' "$REQ" >&2
  exit 2
fi
if [ ! -x "$VENV/bin/python" ] || ! cmp -s "$REQ" "$VENV/.requirements.txt" || \
   ! "$VENV/bin/python" -B -c 'import numpy, yaml' >/dev/null 2>&1; then
  if [ "$SETUP" != true ]; then
    printf 'Vault Python environment is missing or not ready: %s\n' "$VENV" >&2
    printf 'Setup requires explicit approval. Run: bash %q --setup\n' "$SCRIPT_DIR/vault-python.sh" >&2
    exit 2
  fi
  printf 'Preparing the vault search Python environment in %s\n' "$VENV" >&2
  mkdir -p "$(dirname "$VENV")"
  python3 -m venv --clear "$VENV"
  "$VENV/bin/python" -B -m pip install --disable-pip-version-check -r "$REQ" >&2
  "$VENV/bin/python" -B -c 'import numpy, yaml'
  cp "$REQ" "$VENV/.requirements.txt"
fi
if [ "$SETUP" = true ] && [ "$#" -eq 0 ]; then
  printf 'Vault Python environment is ready: %s\n' "$VENV" >&2
  exit 0
fi
exec "$VENV/bin/python" -B "$@"
