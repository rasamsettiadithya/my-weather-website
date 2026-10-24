#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a
source "$ROOT/.env"
set +a
URL="$1"
VAR_NAME="$2"
TOKEN="${(P)VAR_NAME}"
if [[ -z "${TOKEN}" ]]; then
  echo "Missing ${VAR_NAME} in ${ROOT}/.env" >&2
  exit 1
fi
exec /usr/local/bin/npx -y mcp-remote "$URL" --header "Authorization: Bearer ${TOKEN}"
