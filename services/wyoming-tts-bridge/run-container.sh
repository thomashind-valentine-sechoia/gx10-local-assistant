#!/usr/bin/env bash
# Recreate the production Kokoro Wyoming bridge (127.0.0.1:10200).
# Usage:
#   BIND=1 ./run-container.sh    # speak_normalize binds (default)
#   BIND=0 ./run-container.sh    # original image only (rollback)
#
# Does not restart Home Assistant, ha-llm, or Kokoro-FastAPI.
set -euo pipefail
BIND="${BIND:-1}"
IMAGE="${IMAGE:-ghcr.io/roryeckel/wyoming_openai:latest}"
NAME="${NAME:-wyoming-tts}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [[ -f "$REPO_ROOT/scripts/load-env.sh" ]]; then
  # shellcheck source=../../scripts/load-env.sh
  source "$REPO_ROOT/scripts/load-env.sh"
fi
REPO_NORM="$(cd "$SCRIPT_DIR/../wyoming-qwen3-tts" 2>/dev/null && pwd || true)"
SRC_BRIDGE="${SRC_BRIDGE:-$SCRIPT_DIR}"
SRC_NORM="${SRC_NORM:-${REPO_NORM:?speak_normalize.py directory not found; set SRC_NORM}}"

args=(
  -d --name "$NAME" --restart unless-stopped
  --network voice
  -p 127.0.0.1:10200:10300
  -e WYOMING_URI=tcp://0.0.0.0:10300
  -e WYOMING_LANGUAGES=en
  -e TTS_OPENAI_URL=http://kokoro:8880/v1
  -e TTS_MODELS=kokoro
  -e TTS_BACKEND=KOKORO_FASTAPI
  -e TTS_VOICES="bf_emma bm_george bf_isabella bm_lewis"
  -e TTS_STREAMING_VOICES="bf_emma bm_george bf_isabella bm_lewis"
  -e TTS_STREAMING_MIN_WORDS=10
  -e TTS_STREAMING_MODELS=kokoro
  -e TTS_STREAMING_MAX_CHARS=220
  -e PYTHONUNBUFFERED=1
  -e PYTHONDONTWRITEBYTECODE=1
)
if [ "$BIND" = 1 ]; then
  args+=(
    -v "${SRC_BRIDGE}/handler.py:/usr/local/lib/python3.13/site-packages/wyoming_openai/handler.py:ro"
    -v "${SRC_NORM}/speak_normalize.py:/usr/local/lib/python3.13/site-packages/speak_normalize.py:ro"
  )
fi
docker stop "$NAME" >/dev/null 2>&1 || true
docker rm "$NAME" >/dev/null 2>&1 || true
docker run "${args[@]}" "$IMAGE"
