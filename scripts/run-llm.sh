#!/bin/bash
# Sanitised from the live launcher. Safety change: do not automatically remove
# an existing container. Stop/remove it deliberately only when you intend to.
# Reproducibility change: explicitly select the observed cached model revision.
# Paths come from the environment or $HOME defaults (see .env.example).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=load-env.sh
source "$SCRIPT_DIR/load-env.sh"
HF_HOME="${HF_HOME:-$HOME/models/hf}"
VLLM_CACHE_DIR="${VLLM_CACHE_DIR:-$HOME/models/vllm-cache}"
docker run -d --name ha-llm --restart unless-stopped --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 127.0.0.1:8000:8000 -e HF_HUB_OFFLINE=1 -e VLLM_USE_FLASHINFER_MOE_FP4=0 \
  -v "$HF_HOME:/root/.cache/huggingface" -v "$VLLM_CACHE_DIR:/root/.cache/vllm" \
  nvcr.io/nvidia/vllm@sha256:94e21552f644e0c1627464ba89d2f7a4ce7442e196f72afa0bb5d7fba23cbb03 \
  vllm serve nvidia/Qwen3.6-35B-A3B-NVFP4 --served-model-name qwen3.6-35b-a3b \
  --revision 1355db6a052410cfd62085d94b58866fd0f2c3c5 \
  --host 0.0.0.0 --port 8000 --trust-remote-code \
  --kv-cache-dtype fp8 --attention-backend flashinfer --moe-backend marlin \
  --gpu-memory-utilization 0.5 --max-model-len 65536 --max-num-seqs 4 \
  --max-num-batched-tokens 8192 --enable-chunked-prefill --async-scheduling --enable-prefix-caching \
  --speculative-config "{\"method\":\"mtp\",\"num_speculative_tokens\":2,\"moe_backend\":\"triton\"}" \
  --reasoning-parser qwen3 --tool-call-parser qwen3_xml --enable-auto-tool-choice \
  --default-chat-template-kwargs "{\"enable_thinking\":false}"
