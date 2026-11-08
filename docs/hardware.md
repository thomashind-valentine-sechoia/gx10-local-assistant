# Hardware and storage

## Tested host

- ASUS GX10 with NVIDIA GB10, ARM64 (`aarch64`), unified CPU/GPU memory.
- Approximately **121 GiB OS-visible unified RAM** (often loosely called “121 GB” in the build discussion); live `free -b` reported 130,595,995,648 bytes, about 121.63 GiB / 130.60 GB. Do not confuse this with a discrete GPU VRAM figure.
- About **273 GB/s memory bandwidth** is the platform figure used for selection, not a bandwidth benchmark performed here.
- Ubuntu 24.04.4 LTS; NVIDIA driver 580.159.03; Docker 29.2.1; Compose v5.0.2; NVIDIA Container Toolkit 1.19.1 observed.
- Root filesystem: about 982.8 GB usable filesystem capacity; about 537.8 GB available at inspection. These are a transient filesystem snapshot, not a minimum requirement.
- Phone tested: Nothing Phone (1), Android Home Assistant Companion app. Exact Android/app versions were not captured.

## Why MoE

Large dense decoders must move many weights for every generated output step. At this platform's memory bandwidth, a mixture-of-experts model with only a small active subset is attractive: broad capacity with less active computation/weight traffic per step. Qwen3.6-35B-A3B has roughly 35B total / 3B active parameters; the optional deep model is roughly 125B total / 6B active. **All experts still occupy memory**: small active parameter count does not mean small residency. Quantisation, kernels, context length and scheduling matter; MoE is not a universal speed guarantee.

## Storage planning

- SSD space for OS, Docker layers, Hugging Face cache, compiled vLLM cache, ASR data and Kokoro assets. Their individual final sizes were not measured.
- Full selected Wikipedia: **127,418,087,648 bytes** (127.4 GB / 118.7 GiB), `wikipedia_en_all_maxi_2026-08.zim`.
- Allow this space before downloading. The `.part` is renamed on successful checksum verification, not copied, but backups or newer snapshots need additional room.
- Optional deep GGUF and vision projector require further SSD space; exact file sizes were not independently captured. Runtime memory was reported as over 80 GB.
- A smaller/no-picture ZIM is an alternative, not the archive actually selected. Changing archive names requires updating the download, server and HA book identifiers together.

## Memory planning

The voice LLM is capped by `--gpu-memory-utilization 0.5` with a 65,536-token maximum context. The earlier working estimate was about 60 GB for its runtime, with over 80 GB for the deep model. Do not load both together on this host. A live whole-host snapshot and its interpretation are in [performance](performance.md).

An earlier planning budget allowed 5 GiB STT, 2 GiB TTS, 8 GiB OS/HA, 4 GiB retrieval/cache, plus reserve. These were **budget estimates**, not per-service measurements. Kiwix uses its SSD archive and working cache; it does not need to load the complete encyclopedia into RAM.
