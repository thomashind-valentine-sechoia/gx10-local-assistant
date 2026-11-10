# Kokoro Wyoming TTS bridge overlay

Production TTS for the Home Assist pipeline is `wyoming-tts`
(`ghcr.io/roryeckel/wyoming_openai`) on `127.0.0.1:10200`, talking to
Kokoro on the Docker `voice` network.

`handler.py` is a patched copy of the image's `wyoming_openai.handler`.
It imports `speak_normalize.normalize_for_speech` (shared with the Qwen3
server) and applies it:

- on a full `Synthesize` after any SSML strip
- to ready sentences in the streaming path, not to isolated chunks
- to leftover accumulator text and non-streamed `full_text` at stop

`handler.py.orig` is the unmodified file from the image, for rollback.
See `ROLLBACK.md`.

```sh
# Apply (default) or roll back; restarts only wyoming-tts
BIND=1 ./run-container.sh
BIND=0 ./run-container.sh
```

The bind-mount path assumes Python 3.13 site-packages as in the observed
image. Rebase the patch if the upstream image changes.
