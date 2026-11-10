# Qwen3-TTS Wyoming server

A Wyoming TTS frontend around Qwen3-TTS (0.6B CustomVoice / Base), used on
the GX10 as an additional voice path on `127.0.0.1:10201` (container 10200).
The production Home pipeline stays on the Kokoro bridge at port 10200.

`server.py` buffers Home Assistant streaming chunks (`SynthesizeStart` /
`SynthesizeChunk` / `SynthesizeStop`, plus a backwards-compatible full
`Synthesize`) and runs `speak_normalize.normalize_for_speech` on complete
utterances only, so list markers such as `1.` and units such as `225g` are
not split mid-token. Isolated chunks are not normalised.

## Build

The live image tag is locally built:

`wyoming-qwen3-tts:6531f86-cu130-torch2.11.0-f0.5.4-tf5.18.0-compat`

Typical stack, from this directory, ARM64 + CUDA 13:

```sh
docker build -t wyoming-qwen3-tts:base -f Dockerfile .
docker build -t wyoming-qwen3-tts:tf518 -f Dockerfile.tf518 .
# Apply Dockerfile.compat / mimi-fix as needed for the recorded tag.
```

Model weights are not in this repository. Download the public Qwen3-TTS
0.6B CustomVoice and Base snapshots into a local Hugging Face cache and
point `HF_DIR` at it. Optional speaker clones live in a directory outside
the repo and must not be committed (see `.gitignore`).

## Run

```sh
./run-container.sh
```

Restart policy is `unless-stopped`. The script bind-mounts `server.py` and
`speak_normalize.py` read-only so the hook survives container recreation.
It does not restart Home Assistant, ha-llm, or Kokoro.

## Tests

```sh
python3 -m unittest test_speak_normalize.py
```

`synth_client.py` can write a WAV from a running server for a manual listen
test. Do not commit WAVs or private reference clips.
