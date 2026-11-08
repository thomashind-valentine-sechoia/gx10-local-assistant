# Models and serving choices

| Role | Selected configuration | Why / caveat |
|---|---|---|
| Fast conversation | `nvidia/Qwen3.6-35B-A3B-NVFP4`, served as `qwen3.6-35b-a3b` | MoE, GB10-friendly NVFP4, broad knowledge and tool use; measured fast in short warm tests |
| Server | `nvcr.io/nvidia/vllm:26.05.post1-py3` | ARM64/GB10 serving; FP8 KV cache, FlashInfer attention, Marlin MoE, MTP with two speculative steps using Triton |
| STT | `nemo-parakeet-tdt-0.6b-v2` via Wyoming ONNX-ASR GPU | Local English recognition; fast warm component results; accent/name accuracy not benchmarked |
| TTS | Kokoro-82M / Kokoro-FastAPI GPU + Wyoming OpenAI bridge | British voices `bf_emma`, `bm_george`, `bf_isabella`, `bm_lewis`; first two suggested during onboarding |
| Deep questions, optional | `unsloth/Qwen3.8-Flash-Next-GGUF`, `UD-Q4_K_XL`, about 125B-A6B, optional mmproj | Already set up separately according to build conversation; larger capacity, on-demand only; no deep-model performance result recorded |

The name “Flash MLX” was used conversationally for the deep model. **MLX is for Apple hardware; the GX10 setup uses GGUF with llama.cpp/CUDA**, not MLX. Existing llama-server was reported to use `-ngl 999`, flash attention, 65,536 context, loopback port 8080 and `/v1`. Its exact binary revision, full launch command, chat-template/Jinja option and projector compatibility still need capture. Do not assume a launch recipe from another llama.cpp version works. The 27B / very-large-family discussion initially missed Flash Next; this repository does not repeat that incomplete model catalogue as fact.

Fast model Hugging Face cached `main` revision observed: `1355db6a052410cfd62085d94b58866fd0f2c3c5`.
Local OpenAI LLM integration: **v1.15.0**, source revision `e59dccdfd4eb728dc77c7cb6588963383f54e075`. Home Assistant image reports **2026.11.0**. Immutable observed image references are in [images.lock.json](../configs/images.lock.json).

## Alternatives considered, not locally benchmarked here

- `gpt-oss-120b` MXFP4: harder-question alternative with GB10 community results; larger memory footprint. Not the chosen deep model.
- Qwen3.5-35B FP8: conservative earlier-generation MoE alternative with independent GB10 reports.
- `gpt-oss-20b`: small fallback considered; reasoning can delay visible output, so not automatically faster for voice. No fallback deployed because local HA intents handle simple commands.
- Whisper large-v3-turbo: STT alternative; ARM64 CUDA packaging needs care. Long-recording benchmark speed is not short-command latency.
- Piper `en_GB-alan-medium`: simpler, lower-resource CPU speech fallback, not installed in this snapshot.
- Kiwix nopic archive / curated manuals: smaller offline knowledge alternatives; actual download is all/maxi.
- Native HA MCP client plus an offline Wikipedia MCP server was explored initially. The deployed knowledge layer instead uses native HA scripts with fixed local REST endpoints, avoiding another integration and accidental online Wikipedia access.

Do not mix community benchmark numbers with our measurements. Sources from the initial selection: [GB10 benchmark survey](https://ctala.github.io/local-llm-agentic-workflows/benchmarks/), [Qwen3.6 independent tests](https://devsnack-blog.vercel.app/benchmarks/models/qwen3-6-35b-a3b), [GPT-OSS GB10 tests](https://gptoss.lukaloehr.com/), and [GB10 voice recipes](https://github.com/jxlarrea/homeassistant-voice-recipes). These informed choices; this repository has not revalidated their live contents.

The initial research anticipated a patched Kokoro ARM64 build. Live inspection found a published ARM64 image (digest locked here), with no additional application-source patch apparent in container changes. No extra patch is assumed or invented; if that digest stops working, capture the precise build fix before claiming reproducibility.
