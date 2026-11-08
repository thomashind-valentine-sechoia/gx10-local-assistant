# Installation: fresh GX10

This captures the build, not an unattended installer. Read [security](../SECURITY.md) first. Do not run the examples over the working installation without planning backups and container-name conflicts. The documentation collection itself changed no GX10 services.

## 1. Prerequisites

Use ARM64 Ubuntu, a working GB10 NVIDIA driver, Docker Engine, NVIDIA Container Toolkit and Compose with GPU support. The observed versions are in [hardware](hardware.md). Install them using the vendors' supported instructions; no original host-provisioning command log was available. Validate `nvidia-smi`, `docker version` and `docker compose version`. Configure the NVIDIA container runtime as required by the toolkit. Docker-group access is root-equivalent.

Place this repository on the GX10 (copy the local checkout; no public remote exists yet). From its root:

```sh
mkdir -p "$HOME/models/hf" "$HOME/models/vllm-cache" \
  "$HOME/models/onnx-asr/data" "$HOME/models/onnx-asr/cache" \
  "$HOME/homeassistant" "$HOME/kiwix" "$HOME/searxng/config" "$HOME/searxng/data"
docker compose config --quiet
```

All image references in the template are observed ARM64 registry digests, not moving `latest` tags. See [images.lock.json](../configs/images.lock.json) for original names and revisions. Updating these is a deliberate retest task.

## 2. Cache fast model while online

Use a temporary Python virtual environment with `huggingface_hub` installed, then download the observed snapshot into the mounted cache (public model; no account credential is included or required here):

```sh
python3 -m venv /tmp/gx10-hf-download
/tmp/gx10-hf-download/bin/pip install huggingface_hub
HF_HOME="$HOME/models/hf" /tmp/gx10-hf-download/bin/python - <<'PYCODE'
from huggingface_hub import snapshot_download
snapshot_download("nvidia/Qwen3.6-35B-A3B-NVFP4", revision="1355db6a052410cfd62085d94b58866fd0f2c3c5")
PYCODE
```

The copied launcher adds the observed `--revision` explicitly so the offline loader can resolve that cached snapshot without relying on a mutable `main` reference. The running host originally relied on its cached `main`. `HF_HUB_OFFLINE=1` is retained; do not enable network fallback to conceal a missing cache.

## 3. Start the fast LLM

```sh
bash scripts/run-llm.sh
docker logs -f ha-llm
# In another terminal, once ready:
curl -fsS http://127.0.0.1:8000/v1/models
```

The script preserves the live serving options: 65,536 context, max 4 sequences, 8,192 batch tokens, FP8 KV, FlashInfer attention, Marlin MoE, chunked prefill, async scheduling, prefix cache, MTP k=2 with Triton, `qwen3` reasoning parser, `qwen3_xml` tool parser, automatic tool selection, thinking false. Host binding is **127.0.0.1:8000**, even though the service listens on all container interfaces. Startup took about 226 s in one recorded test.

Unlike the original launcher, this copy pins the observed model revision and image digest, quotes cache paths, and does not automatically remove an existing `ha-llm` container. A name conflict intentionally stops the new launch; inspect existing state rather than blindly deleting it. It still records the current `unless-stopped` policy; coordination with a deep model is pending.

## 4. Start Home Assistant and speech

```sh
docker compose up -d homeassistant wyoming-stt kokoro wyoming-tts
```

Allow first-run model downloads while online. The STT data/cache volumes persist; Kokoro model assets are supplied by its image/runtime. An actual disconnected restart test is still needed. For build alternatives see the upstream GB10 voice recipes, but do not assume an x86 image will run on ARM64.

| Service | Host port → container port | Network |
|---|---|---|
| Fast LLM | `127.0.0.1:8000` → 8000 | bridge |
| Home Assistant | 8123, host interfaces | **host** |
| Parakeet Wyoming STT | `127.0.0.1:10300` → 10300 | bridge |
| Kokoro API | `127.0.0.1:8880` → 8880 | voice |
| Wyoming TTS bridge | `127.0.0.1:10200` → **10300** | voice |
| SearXNG (later) | `127.0.0.1:8888` → 8080 | bridge |
| Kiwix (later) | `127.0.0.1:8090` → 8080 | bridge |
| Deep llama.cpp (optional) | `127.0.0.1:8080` | host process; not started here |

## 5. Install Local OpenAI custom integration

Use upstream `skye-harris/hass_local_openai_llm` **v1.15.0**, recorded revision `e59dccdfd4eb728dc77c7cb6588963383f54e075`. The build used a source checkout; this public recipe can use its archive instead:

```sh
curl -fL 'https://github.com/skye-harris/hass_local_openai_llm/archive/e59dccdfd4eb728dc77c7cb6588963383f54e075.tar.gz' -o /tmp/local-openai-source.tgz
mkdir -p /tmp/gx10-local-openai-source
tar -xzf /tmp/local-openai-source.tgz -C /tmp/gx10-local-openai-source
mkdir -p "$HOME/homeassistant/custom_components"
cp -a /tmp/gx10-local-openai-source/hass_local_openai_llm-*/custom_components/local_openai "$HOME/homeassistant/custom_components/"
# Restart only during setup or an agreed maintenance window:
docker restart homeassistant
```

Review upstream code/licences before installing. The custom integration is not bundled into this repository.

## 6. Home Assistant onboarding

1. Open `http://<GX10_LAN_IP>:8123` on the trusted LAN, or `http://<GX10_TAILSCALE_IP>:8123` over your authorised tailnet. Create your own account and set location privately. No names, password, address or account database belongs in this repo.
2. Settings → Devices & services → Add integration → **Wyoming Protocol**. Host `127.0.0.1`, port **10300**, for STT. Add Wyoming again with port **10200**, for TTS.
3. Add **Local OpenAI LLM**, server type **vLLM**, base URL `http://127.0.0.1:8000/v1`, blank API key. Generic OpenAI-compatible is only a fallback if vLLM is not offered.
4. Add/configure the conversation agent:

| Setting | Value |
|---|---|
| Model | `qwen3.6-35b-a3b` |
| System prompt | Keep the default HA voice-assistant template; append knowledge instructions later |
| Control Home Assistant | Assist / Device control provider |
| Parallel tool calling | **Off** (known parser issue) |
| Temperature | **0.6** |
| Max previous conversation rounds | **10** |
| vLLM Thinking mode | Leave empty in the tested UI (no Off option); server defaults thinking false |
| Thinking token budget | Leave unset |
| Other optional fields | Defaults / blank unless required by your version |

Do not treat an empty UI dropdown as a general rule across versions; verify server request defaults after upgrades.

## 7. Create the Assist pipeline

Settings → Voice assistants → Add assistant:

- Choose a name, e.g. Home.
- Conversation agent: your Local OpenAI agent.
- Turn on **Prefer handling commands locally**. Normal supported controls should not wait for an LLM.
- Speech-to-text: Wyoming / Parakeet, English.
- Text-to-speech: Wyoming / Kokoro; pick `bf_emma` or `bm_george` (other installed British voices are available).
- Save and set as preferred (star / overflow menu, depending on frontend).

Test a typed general question in Assist first. Expose only needed entities to Assist; this snapshot had no verified physical-device control test. Then configure the [phone](phone.md) and [knowledge services](knowledge.md).

## 8. Verify before relying on it

Inspect local binds, confirm `/v1/models`, test STT/TTS independently with the historical harnesses, and test one real Assist turn. After downloads complete, test on LAN without internet. See the [acceptance checklist](roadmap.md). `docker compose config --quiet` validates the template but does not prove image availability, GPU compatibility or complete deployment on another host.
