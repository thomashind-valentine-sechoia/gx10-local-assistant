# shellcheck shell=bash
# Source from other scripts:  # shellcheck source=load-env.sh
#   REPO_ROOT=... source "$REPO_ROOT/scripts/load-env.sh"
# Loads repo .env if present. Does not override variables already set.
if [[ -z "${REPO_ROOT:-}" ]]; then
  echo "load-env.sh: REPO_ROOT is not set" >&2
  return 1 2>/dev/null || exit 1
fi
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi
