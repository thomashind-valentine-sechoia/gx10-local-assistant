# Rollback wyoming-tts (Kokoro Wyoming bridge on 127.0.0.1:10200)

`handler.py` in this directory is a patched copy of `wyoming_openai` from
`ghcr.io/roryeckel/wyoming_openai`. `handler.py.orig` is the unmodified
file taken from the running image before the speech-normaliser hook.

Original handler SHA-256:

  78c6bf855a03dba28c464536fc39a0cabfa3691e3e658ad56f336408f381e613

On the GX10 a second copy is also kept at
`$HOME/gx10-backups/wyoming-tts-handler-20261110-124244/handler.py.orig`.

Recreate the container from the original image with no bind mounts
(keeps name `wyoming-tts`, network `voice`, port `127.0.0.1:10200`,
`unless-stopped`):

  BIND=0 ./run-container.sh

To re-apply the speak_normalize hook:

  BIND=1 ./run-container.sh

Do not edit HA core, ha-llm, Kokoro-FastAPI, or pipeline settings to roll
this back. If the upstream image changes its Python path, adjust the bind
targets in `run-container.sh` before applying.
