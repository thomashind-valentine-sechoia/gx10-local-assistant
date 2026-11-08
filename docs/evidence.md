# Evidence and reproducibility notes

## Evidence used

1. The provided 7–8 November 2026 build conversation summary and subsequent Home Assistant/phone/knowledge setup messages.
2. Initial local model-selection research document, dated 7 November 2026: its external benchmark numbers are not reproduced as our measurements.
3. Local knowledge setup report, dated 8 November 2026: archive size/checksum, endpoints, test outcomes and limitations.
4. Read-only inspection of the live GX10: Docker configuration/image digests, fast-model launcher and benchmark, speech benchmark, knowledge YAML, sanitised SearXNG settings, Wikipedia downloader, hardware/toolchain, integration manifest and source revision, cached fast-model revision.

A transcript search was attempted. The transcript surface did not provide the full original lead-agent history; the readable session contained the delegated conversation context rather than the complete original tool logs. Consequently the full original logs, exact benchmark trials and any omitted build commands could not be recovered. This repository explicitly distinguishes inherited observations from current inspection instead of inventing missing evidence.

## Configuration provenance

- `configs/homeassistant/packages/local_knowledge.yaml`: copied from the running host, with no account data.
- `configs/searxng/settings.yml.example`: copied configuration, with generated server secret replaced by a placeholder.
- `scripts/run-llm.sh`, `scripts/bench_llm.py`, `scripts/bench_voice.py`, `scripts/download-wikipedia.sh`: copies of the build artifacts. The LLM launcher avoids automatically deleting an existing container, pins the observed image/model revisions and quotes cache paths; see its header.
- `compose.yaml`: reconstructed from live container settings, using immutable observed registry digests. It is a **reproduction template**, not the original deployment file. No original Compose file for the complete stack was established.
- `configs/images.lock.json`: observed images and upstream source revisions where available, not a dump of full Docker environment or labels.
- `configs/homeassistant/configuration.fragment.yaml`: just the packages include; not the user's private HA configuration.

Only local documentation files were written during this job. GX10 services, settings, accounts and restart policies were not modified or restarted. Image build timestamps/maintainer labels and raw host inventory are intentionally not copied into public-facing files.

## Known reproduction gaps

- Deep-model launcher, binary revision, exact file hashes and speed not captured independently.
- No complete original voice build log/patch record; observed ARM64 image digests are supplied instead. No additional live Kokoro source patch was apparent.
- Exact model asset revisions for speech, asset disk sizes, app/Android versions and model quality scores missing.
- Full Wikipedia completed after the original snapshot: SHA-256 verified 8 Nov 2026 at 13:10 GMT; Kiwix full-archive searches work. Full-archive Assist execution remains unverified.
- Templates were syntax/configuration-checked where available, not installed on a clean second GX10. Download endpoints and registries may change; future upgrades require retesting.

## References

- https://github.com/skye-harris/hass_local_openai_llm
- https://github.com/jxlarrea/homeassistant-voice-recipes
- https://github.com/jxlarrea/wyoming-onnx-asr
- https://github.com/remsky/Kokoro-FastAPI
- https://github.com/roryeckel/wyoming_openai
- https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4
- https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF
- https://www.home-assistant.io/voice_control/exposing_scripts_to_llms/
- https://docs.searxng.org/admin/installation-docker.html
- https://download.kiwix.org/zim/wikipedia/
- https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html

These are provenance links, not a claim their live documentation was re-read during this snapshot collection.
