#!/usr/bin/env bash
# Recreate the trial/additional Qwen3-TTS Wyoming server on 127.0.0.1:10201.
# The image is built locally (see README.md); this script does not pull it.
# Voice reference clips are optional and are never part of this repository.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [[ -f "$REPO_ROOT/scripts/load-env.sh" ]]; then
  # shellcheck source=../../scripts/load-env.sh
  source "$REPO_ROOT/scripts/load-env.sh"
fi
NAME="${NAME:-wyoming-qwen3-tts}"
IMAGE="${IMAGE:-wyoming-qwen3-tts:6531f86-cu130-torch2.11.0-f0.5.4-tf5.18.0-compat}"
HF_DIR="${HF_DIR:-${HOME}/models/qwen3-tts}"
CLONE_DIR="${TTS_CLONE_VOICES_DIR:-}"
SRC="${SRC:-$SCRIPT_DIR}"
# Observed public model snapshots used on the GX10 (Qwen3-TTS 0.6B).
CUSTOM_SNAP="${CUSTOM_SNAP:-85e237c12c027371202489a0ec509ded67b5e4b5}"
BASE_SNAP="${BASE_SNAP:-5d83992436eae1d760afd27aff78a71d676296fc}"
SPEAKER="${SPEAKER:-Ryan}"
TZ="${TZ:-Europe/London}"

args=(
  -d --name "$NAME" --restart unless-stopped
  --gpus all
  -p 127.0.0.1:10201:10200
  -e HF_HOME=/data/huggingface
  -e HF_HUB_DISABLE_TELEMETRY=1
  -e PYTHONUNBUFFERED=1
  -e TZ="$TZ"
  -v "${HF_DIR}:/data/huggingface"
  -v "${SRC}/server.py:/app/server.py:ro"
  -v "${SRC}/speak_normalize.py:/app/speak_normalize.py:ro"
)
if [[ -n "$CLONE_DIR" && -d "$CLONE_DIR" ]]; then
  # Optional local clones; this repo does not ship reference audio.
  args+=(-v "${CLONE_DIR}:/data/clone-voices:ro")
fi

docker stop "$NAME" >/dev/null 2>&1 || true
docker rm "$NAME" >/dev/null 2>&1 || true
docker run "${args[@]}" "$IMAGE" \
  --uri tcp://0.0.0.0:10200 \
  --model "/data/huggingface/hub/models--Qwen--Qwen3-TTS-12Hz-0.6B-CustomVoice/snapshots/${CUSTOM_SNAP}" \
  --base-model "/data/huggingface/hub/models--Qwen--Qwen3-TTS-12Hz-0.6B-Base/snapshots/${BASE_SNAP}" \
  --speaker "$SPEAKER"
