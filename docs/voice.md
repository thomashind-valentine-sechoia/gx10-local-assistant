# Voice pipeline

Speech stays on the GX10. Home Assistant talks Wyoming; nothing in this
path is sent to a cloud TTS or STT vendor.

## Ports and services

| Role | Service | Host bind | Notes |
|---|---|---|---|
| Speech-to-text | `wyoming-stt` (Parakeet) | `127.0.0.1:10300` | Unchanged |
| Home / Kokoro TTS | `wyoming-tts` → Kokoro | `127.0.0.1:10200` → 10300, Kokoro `127.0.0.1:8880` on Docker network `voice` | British stock voices `bf_emma`, `bm_george`, `bf_isabella`, `bm_lewis` |
| Additional Qwen3 TTS | `wyoming-qwen3-tts` | `127.0.0.1:10201` → 10200 | Locally built image; optional Assist pipeline |

The Home Assist pipeline uses the Kokoro bridge and a British stock voice
such as `bm_george`. A second pipeline can point Wyoming TTS at port 10201
for Qwen3-TTS (built-in speakers such as `Ryan`, or optional local clones).
Reference clips, transcripts and private clone directories are **not** in
this repository.

## Speech normalisation

Both TTS frontends run `speak_normalize.normalize_for_speech` on complete
utterances immediately before synthesis. Displayed/typed text in Assist is
unchanged. The normaliser expands recipe and list forms for speech, for
example:

- numbered and bulleted lists (`1.` → “First,”, `-` → “Next,”)
- units after numbers (`tsp`, `tbsp`, `oz`, `g`, `kg`, `ml`, `°C` / `°F`, …)
- simple fractions and numeric ranges, without treating ISO dates as ranges

Home Assistant can split `1.` or `225g` across streaming Wyoming chunks, so
neither server normalises an isolated chunk. The Qwen3 server buffers until
end of utterance. The Kokoro bridge normalises full `Synthesize` text and
ready sentences / leftover text at stop, matching that buffering rule.

Sources:

- Qwen3: `services/wyoming-qwen3-tts/` (`server.py`, `speak_normalize.py`, tests, Dockerfiles, `run-container.sh`)
- Kokoro overlay: `services/wyoming-tts-bridge/` (patched `handler.py`, `handler.py.orig`, `run-container.sh`, `ROLLBACK.md`)

Apply or roll back only the matching container; see those READMEs. Do not
restart Home Assistant, ha-llm, or Kokoro-FastAPI for a normaliser change.

```sh
python3 -m unittest discover -s services/wyoming-qwen3-tts -p 'test_*.py'
```
