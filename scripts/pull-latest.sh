#!/usr/bin/env bash
# Update a checkout of this repository (fast-forward only) and print the
# hash-gated steps to copy packages or TTS overlays onto a running GX10.
# This script does not overwrite live Home Assistant, secrets, or .storage.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -d .git ]]; then
  echo "ERROR: $REPO_ROOT is not a git checkout" >&2
  exit 1
fi

echo "REPO=$REPO_ROOT"
echo "BRANCH=$(git branch --show-current)"
echo "HEAD=$(git rev-parse --short HEAD)"
git status --short
git fetch origin
DEFAULT_BRANCH="$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo origin/main)"
DEFAULT_BRANCH="${DEFAULT_BRANCH#origin/}"
CURRENT="$(git branch --show-current)"

if [[ "${1:-}" == "--ff" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: working tree is not clean; refusing to pull" >&2
    exit 1
  fi
  git pull --ff-only origin "${CURRENT:-$DEFAULT_BRANCH}"
  echo "HEAD=$(git rev-parse --short HEAD)"
else
  echo "Fetched. Working tree was left unchanged."
  echo "Fast-forward this branch with: $0 --ff"
  git log --oneline --decorate -1 HEAD
  git log --oneline --decorate -1 "origin/${CURRENT:-$DEFAULT_BRANCH}" || true
fi

PKG="$REPO_ROOT/configs/homeassistant/packages/local_knowledge.yaml"
if [[ -f "$PKG" ]]; then
  echo "PACKAGE_SHA256=$(sha256sum "$PKG" | awk '{print $1}')"
fi

cat <<'HINT'

Next steps (manual; not run by this script):

  1. Configuration-only backup first: scripts/backup.sh
     Archives may contain secrets. Keep them mode 0600 and never commit them.

  2. Home Assistant packages (hash-gated):
       sha256sum "$HOME/homeassistant/packages/local_knowledge.yaml"
       # Copy the live file to a timestamped path *outside* packages/
       # then copy configs/homeassistant/packages/*.yaml into packages/.
       docker exec homeassistant python -m homeassistant --script check_config --config /config
       # On success, Developer tools → Actions → script.reload (no data).
       # Do not restart Home Assistant or ha-llm unless you planned to.

  3. ask_claude.yaml needs !secret ask_claude_bridge_token already in
     secrets.yaml. Do not copy secrets.yaml from anywhere into git.

  4. Conversation agent prompt is not a package file. Paste
     configs/homeassistant/agent-prompt.txt into the Local OpenAI
     conversation-agent options if you want the recorded wording.

  5. TTS overlays, after the files are on the GX10:
       services/wyoming-qwen3-tts/run-container.sh
       services/wyoming-tts-bridge/run-container.sh
     Each restarts only its own container.

  6. Tests, from the repo root:
       python3 -m unittest tests.test_private_web_search
       python3 -m unittest discover -s services/wyoming-qwen3-tts -p 'test_*.py'
HINT
