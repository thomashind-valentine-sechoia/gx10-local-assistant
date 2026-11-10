# Local Home Assistant voice assistant for the ASUS GX10

A self-hosted Home Assistant stack for an [ASUS Ascent GX10](https://www.asus.com/) (ARM64, NVIDIA GB10): a local LLM, offline Wikipedia, private web search, and on-device speech. Anyone can clone this repository, copy the Compose file and Dockerfiles, and follow this guide on their own GX10. Nothing in the tree is tied to a particular host, username, or network.

The published files are templates and packages. Private runtime state (`secrets.yaml`, `.storage`, model weights, ZIM archives, logs, and any voice recordings) stays on your machine and is listed in `.gitignore`.

## What you get

- Home Assistant, bound in host networking, with packages for:
  - offline Wikipedia (Kiwix)
  - private web search (SearXNG), including a fallback when the engine returns no results
  - an optional “Ask Claude” script that calls a local CLI bridge
- A fast local LLM (vLLM, `nvidia/Qwen3.6-35B-A3B-NVFP4`) started with `scripts/run-llm.sh`
- Speech-to-text (Parakeet via Wyoming) and two text-to-speech paths:
  - Kokoro FastAPI behind a Wyoming OpenAI bridge (port 10200)
  - optional Qwen3-TTS with a spoken-text normaliser (port 10201)
- A spoken-text normaliser so lists, units, and temperatures read naturally
- Backup and update scripts that never overwrite live Home Assistant state

Services that do not need to be reached from other machines bind to `127.0.0.1`. After a service is stable, Compose and the launchers use `restart: unless-stopped`.

## Prerequisites

On the GX10 (Ubuntu, aarch64):

- Docker Engine and the NVIDIA Container Toolkit, with a working GPU in containers
- Enough free memory to keep the LLM, Home Assistant, and the voice stack resident (leave tens of gigabytes of `MemAvailable` in reserve)
- Git
- Outbound HTTPS for the first image and model pull; afterwards the LLM can run offline (`HF_HUB_OFFLINE=1`)

You will also need:

- A Hugging Face-accessible copy of `nvidia/Qwen3.6-35B-A3B-NVFP4` (see [docs/models.md](docs/models.md))
- Optionally, a Kiwix `*.zim` encyclopedia under `$HOME/kiwix` (see [docs/knowledge.md](docs/knowledge.md))

These steps assume you are logged in as the user who will own the data directories. Commands use `$HOME`; you do not need to hard-code a username.

## 1. Clone and configure

```sh
git clone https://github.com/thomashind-valentine-sechoia/gx10-local-assistant.git
cd gx10-local-assistant
cp .env.example .env
# Edit .env if your directories differ from the $HOME defaults
```

Create the data directories (Compose and the launchers will use them):

```sh
mkdir -p "$HOME/homeassistant" \
  "$HOME/models/hf" "$HOME/models/vllm-cache" \
  "$HOME/models/onnx-asr/data" "$HOME/models/onnx-asr/cache" \
  "$HOME/searxng/config" "$HOME/searxng/data" \
  "$HOME/kiwix" \
  "$HOME/gx10-backups"
```

## 2. Fast LLM

Download or copy the pinned model revision into `$HOME/models/hf` (details in [docs/models.md](docs/models.md) and [docs/install.md](docs/install.md)). Then:

```sh
./scripts/run-llm.sh
```

The script binds `127.0.0.1:8000`, uses `restart: unless-stopped`, and does **not** delete an existing `ha-llm` container. Stop and remove that container yourself if you intend to recreate it. Confirm it is healthy before continuing.

## 3. Compose services

From the repository root:

```sh
docker compose up -d
```

This starts Home Assistant, Parakeet STT (`127.0.0.1:10300`), Kokoro (`127.0.0.1:8880`), the Wyoming TTS bridge (`127.0.0.1:10200`), SearXNG (`127.0.0.1:8888`), and Kiwix (`127.0.0.1:8090`). Image digests are pinned in `compose.yaml`.

Search needs a secret that is **not** in this repository. Create `$HOME/searxng/config/settings.local.yml` (or your `SEARXNG_CONFIG_DIR`) with a unique `secret_key` as described in [docs/knowledge.md](docs/knowledge.md).

Home Assistant itself uses `secrets.yaml` under `$HA_CONFIG_DIR`. Keep that file off Git.

## 4. Home Assistant packages and the conversation prompt

Merge the snippet in `configs/homeassistant/configuration.fragment.yaml` into your `configuration.yaml` so packages are loaded from a `packages/` directory. Copy the YAML packages:

```sh
mkdir -p "$HOME/homeassistant/packages"
cp configs/homeassistant/packages/*.yaml "$HOME/homeassistant/packages/"
```

Do not overwrite a live package until you have hashed the current file and confirmed `check_config` (see [docs/knowledge.md](docs/knowledge.md)). The packages expect Local LLM Conversation to expose these tool names exactly:

- `script__offline_wikipedia_search`
- `script__offline_wikipedia_article`
- `script__private_web_search`
- `homeassistant__GetLiveContext`
- `script__ask_claude` (only if you enable the optional Claude bridge)

Copy `configs/homeassistant/agent-prompt.txt` into the Local LLM Conversation agent prompt. The file already uses the exact tool names, including `script__private_web_search` for web search (an earlier alias, `script__web_search`, will not be issued by the model). Prefix spoken Claude replies with `Claude says:` as in the prompt.

Create `secrets.yaml` entries referenced by the packages (`wikipedia_base_url`, `searxng_base_url`, `ask_claude_bridge_token`, and so on). Use placeholders in any file you might later commit; never put real tokens in this repo.

Restart Home Assistant or reload scripts only after `check_config` passes.

## 5. Voice pipeline

In Home Assistant, create an Assist pipeline that uses:

- STT: the Wyoming Parakeet service on `127.0.0.1:10300`
- TTS: either the Kokoro Wyoming bridge on `127.0.0.1:10200` (voices such as `bm_george`) or the optional Qwen3-TTS service on `127.0.0.1:10201`

### Speech normaliser (recommended)

The normaliser expands numbered lists, units, and temperatures so Kokoro and Qwen3 read them clearly. It lives in `services/wyoming-qwen3-tts/speak_normalize.py`.

For **Kokoro**, rebuild the Wyoming OpenAI bridge with the overlay so the patch survives container recreation:

```sh
./services/wyoming-tts-bridge/run-container.sh
```

Read `services/wyoming-tts-bridge/ROLLBACK.md` before you do this on a machine that already has a working TTS container. The script bind-mounts `handler.py` and `speak_normalize.py` from this repository; it does not edit files inside the image.

For **Qwen3-TTS**, see `services/wyoming-qwen3-tts/README.md`, then:

```sh
./services/wyoming-qwen3-tts/run-container.sh
```

Point `HF_DIR` at your Qwen3-TTS cache if it is not `$HOME/models/qwen3-tts`.

More context: [docs/voice.md](docs/voice.md).

### Optional voice cloning

The Qwen3-TTS container can load **your** reference clips if you set `TTS_CLONE_VOICES_DIR` in `.env` to a directory of your own recordings. Do not commit clips, transcripts of private speech, or clone artefacts; `.gitignore` already excludes `clone-voices/`, audio, and model weight patterns. Start with a dummy or empty directory if you only want the built-in speaker.

## 6. Backups

On the GX10:

```sh
./scripts/backup.sh
```

Archives land in `$HOME/gx10-backups` (override with `BACKUP_ROOT`). They can contain secrets if those files are readable, so the script uses mode `0600`. Never commit an archive. Details: [docs/backups.md](docs/backups.md).

To update a checkout later:

```sh
./scripts/pull-latest.sh        # fetch and show status
./scripts/pull-latest.sh --ff   # fast-forward the current branch
```

The updater prints hash-gated copy steps; it does not overwrite live Home Assistant, secrets, or `.storage`.

## Tests

From the repository root, with PyYAML and Jinja2 available for the search tests:

```sh
python3 -m unittest tests.test_private_web_search
python3 -m unittest discover -s services/wyoming-qwen3-tts -p 'test_*.py'
```

The speak_normalize suite is 23 tests.

## Publishing and privacy

This repository must stay free of host paths, usernames, emails, passwords, API keys, IPs, and hostnames. Before you commit:

```sh
./scripts/check-privacy.sh
```

Install the Git hook (once per checkout) as described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Further documentation

- [docs/architecture.md](docs/architecture.md) — how the pieces fit together
- [docs/hardware.md](docs/hardware.md) — GX10 notes
- [docs/models.md](docs/models.md) — model pins and sizing
- [docs/install.md](docs/install.md) — detailed first-time install
- [docs/knowledge.md](docs/knowledge.md) — Wikipedia, web search, and the optional Claude bridge
- [docs/voice.md](docs/voice.md) — STT/TTS pipelines
- [docs/phone.md](docs/phone.md) — phone client notes
- [docs/performance.md](docs/performance.md) — example measurements
- [docs/troubleshooting.md](docs/troubleshooting.md)
- [docs/roadmap.md](docs/roadmap.md)
- [docs/evidence.md](docs/evidence.md)

This project is licensed under the MIT Licence. See [LICENSE](LICENSE).
