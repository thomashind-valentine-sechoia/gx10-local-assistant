# Larger sparse MoEs for GX10 — 8 November 2026

**Decision:** Thomas decided to keep the current fast model (Qwen3.6-35B-A3B NVFP4) unchanged.

Web research only. No GX10 access or changes.

## Conclusion
Yes: Qwen3-Next-80B-A3B is precisely the kind of model Thomas describes. But neither it nor the other researched candidates is demonstrably better than the newer Qwen3.6-35B-A3B while keeping its measured 80 tok/s and 0.1-second first token.
Keep Qwen3.6 for production voice. If an experiment is wanted, shortlist (1) gpt-oss-120b, a different reasoning model with approximately 57–69 tok/s tuned single-Spark reports; (2) Qwen3-Next-80B-A3B-Instruct, the exact architectural match but older and weaker on published reasoning tests. Neither is an established upgrade.

## Memory
121 GB − 8 GB other services − 8 GB reserve = 105 GB maximum replacement-server footprint, including weights, KV, graphs and temporary buffers. Keeping the existing 58 GB server leaves only 47 GB for an additional server. These are mainly replacement candidates, not alongside candidates. Decimal GB and GiB differ by 7.4%; below, source units are retained. Runtime estimates are planning estimates, not measurements on Thomas’s GX10. Loading/compilation may peak higher.

## Candidates
### Qwen3-Next-80B-A3B Instruct / Thinking
80B total, 3B active. NVIDIA NVFP4 available for both; Instruct visible tree has ten approximately 5 GB shards plus 0.726 GB, approximately 50.7 GB. Thinking exact bytes unverified. Search synthesis incorrectly called this layout 55.73 GB: use visible arithmetic, not that synthesis.
Apache-2.0; native tool calling, Qwen-Agent documented. Architecture supported by vLLM >=0.10.2. NVIDIA NVFP4 card documents TensorRT-LLM rather than vLLM; exact FP4-vLLM-GB10 speed not established here.
Measured forum comparison: vLLM FP8 43.16 tok/s; DGPP fork NVFP4 + depth-2 draft 76.73 tok/s on ONE Spark, 121.31 on TWO. The 77 figure is NOT vLLM. Fork runtime memory 68.9 GiB, not transferable to vLLM. Fits as replacement; estimate 65–85 GB server at 32–64K initially, with substantial implementation uncertainty. Only 12 full-attention layers; theoretical 64K FP8 KV is approximately 1.5 GiB before recurrent/scheduling overhead. Thinking mandates reasoning and is less suitable for immediate speech.
Sources: https://huggingface.co/nvidia/Qwen3-Next-80B-A3B-Instruct-NVFP4
https://huggingface.co/nvidia/Qwen3-Next-80B-A3B-Instruct-NVFP4/tree/main
https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Thinking
https://forums.developer.nvidia.com/t/qwen3-next-80b-on-dgx-spark-77-tok-s-and-12-s-load-on-one-spark-121-tok-s-and-10-s-load-on-two/385135

### Qwen3-Coder-Next
Approximately 80B/3B. Community gdubicki/Qwen3-Coder-Next-NVFP4-GB10 approximately 43 GB disk; recipe reports 42.7 GiB resident without draft. Apache-2.0 upstream; native coding/tool model. Single-Spark stock vLLM 0.24.0/0.25.1 + CUDA 13 reported; 0.26.0 backend regression reported.
60.8 tok/s baseline, 72.0 with external EAGLE3 draft at 2K prompt, TTFT approximately 0.44 seconds. At 32K: 37.9 tok/s and 6.9-second TTFT. Runtime 58.3 GiB including draft and 8 GiB KV for 262K context; replacement fits comfortably. Not safe to assume fits alongside unchanged current server. Recipe widget says “No measured runs yet” despite extensive measured prose; treat as community report, not independent reproduction. No verified common-harness general-quality improvement over current Qwen; coding specialisation is not household intelligence.
https://howtospark.com/recipes/qwen3-coder-next-nvfp4

### gpt-oss-120b
117B total (name rounded), 5.1B active. Official MXFP4, approximately 65.2 GB checkpoint reported, not freshly byte-audited; model card confirms single-80GB-GPU operation. Apache-2.0; native function calling and structured outputs using Harmony; low/medium/high reasoning.
Real ASUS GX10/Spark vLLM support, but fastest measurements use SM121-specific patches, CUTLASS kernels and extra quantization of dense layers/head (stock checkpoint leaves these BF16). Repository reports 57–60 tok/s single node across 512–8192 prompts. GX10 recipe: 60.4 tok/s at concurrency one; 285.8 is aggregate at concurrency 256, not voice speed. Another six-patch project reports 68.9 tok/s. Plan roughly 80–100 GB server with modest concurrency and 16–64K context, ESTIMATE; maximum 128K fit with the required reserve unverified. Cannot coexist with unchanged 58 GB server. Reasoning first-token vs first-answer latency must be tested.
https://huggingface.co/openai/gpt-oss-120b
https://github.com/christopherowen/spark-vllm-mxfp4-docker/
https://dendro-logic.com/recipes/gpt-oss-120b-gx10-dgx-spark-concurrency-first/
https://gptoss.lukaloehr.com/

### Ling-3.0-flash
124B total/5.1B active. r0b0tlab NVFP4 81.3 GB: routed experts only, other components BF16; MIT per quant card. Native ling3 tools/reasoning, thinking can be disabled. Measured GB10 NVFP4 uses inclusionAI vllm-ling-v3 fork plus TWO SM121 patches, not verified stock drop-in. 21.4 tok/s baseline CUDA graphs, 33.5 with MTP, 24K context. Marginal replacement fit: estimated 95–105 GB at 16–24K and low concurrency; 81.3 GB weights leave only 23.7 GB for all inference overhead. Loading peak and 256K fit unverified.
Important new NVIDIA result (27 October 2026): optimized SGLang MXFP4 gets 53.89 tok/s on full GSM8K, versus 37.81 baseline, mean TTFT 0.214 seconds. Synthetic repetitive test gets 102.88 tok/s; NVIDIA explicitly warns this is NOT representative. This is SGLang, not vLLM. Actual GSM8K accuracy 96.82%; no same-harness Qwen baseline established.
https://huggingface.co/inclusionAI/Ling-3.0-flash
https://huggingface.co/r0b0tlab/Ling-3.0-flash-NVFP4
https://developer.nvidia.com/blog/3-ways-to-boost-moe-inference-on-nvidia-dgx-spark/

### Ling-flash-2.0
Branded 100B total (HF metadata approximately 103B)/6.1B active, 4.8B non-embedding. Found MXFP4_MOE GGUF approximately 56.4 GB, not verified vLLM-ready NVFP4 safetensors. Upstream documents patched vLLM 0.10.0; exact FP4 × GB10 configuration, native structured tools, licence from the fetched card, and GB10 speed unverified. The fetched licence section is empty: do not infer licence from Ling 3. Weight arithmetic suggests replacement fit at 32K but runtime evidence insufficient. 128K uses YaRN. H20 200+ tok/s cannot be transferred to Spark.
https://huggingface.co/inclusionAI/Ling-flash-2.0
https://huggingface.co/noctrex/Ling-flash-2.0-MXFP4_MOE-GGUF

## Quality versus current model
Publisher scores, NOT a common controlled comparison; reasoning budgets, tools and decoding differ.
Current NVIDIA Qwen3.6 NVFP4: MMLU-Pro 85.0; GPQA Diamond 84.8; AIME25 88.8; tau2 telecom 94.7; SciCode 40.6.
Next Instruct NVIDIA NVFP4: MMLU-Pro 81.1; GPQA 72.5; AIME25 62.0.
Next Thinking upstream: MMLU-Pro 82.7; GPQA 77.2; AIME25 87.8 (not quant-specific).
Thus bigger Next is not a published reasoning upgrade over current Qwen.
gpt-oss reported GPQA 80.1 and AIME25 WITH TOOLS 97.9 surfaced in model-card search summaries; PDF figures were not independently extracted. Do not compare tool-assisted AIME directly with Qwen unassisted.
Ling3 quant card: GSM8K 94.5% on only 200 examples; BFCL-v4 multi-turn base 62.0% (76.5 thinking); different tests/harnesses from current Qwen, not proof of superiority. Coder-Next and Ling2 same-harness comparable scores unverified.
https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4
https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf

Artificial Analysis caution: search snippets show Qwen3.6 reasoning 32, Next Thinking 17, Next Instruct 14. Live readable gpt-oss page now says N/A and index versions have changed. Do NOT present snippets as verified current same-version rankings. Search synthesis even incorrectly produced “240” for gpt-oss: discarded.
https://artificialanalysis.ai/models/qwen3-6-35b-a3b/
https://artificialanalysis.ai/models/qwen3-next-80b-a3b-instruct
https://artificialanalysis.ai/models/qwen3-next-80b-a3b-reasoning
https://artificialanalysis.ai/models/gpt-oss-120b

## Requested families outside the desired bigger-A3B–A6B class
* Nemotron 3 Nano: 31.6B/~3B. NVIDIA NVFP4 approximately 21 GB reported; Spark recipe 61.16 tok/s, 28.3 GiB total at full 262K. Native qwen3_coder tools, NVIDIA Nemotron Open Model Licence. Fits easily, but smaller and slower. Comparable quality scores unverified.
* Nemotron 3 Super: 120B/12B. Official NVFP4 approximately 70 GB footprint reported (exact checkpoint bytes unverified). Official Spark vLLM 0.27.1 recipe, native tools, Nemotron Open Model Licence. GPQA NVFP4 79.42 reported. Same-Spark community comparison 15.77 tok/s, 24.02 MTP. Replacement fits with restrained KV; full 1M under reserve unverified. Too active/slow.
* GLM-4.5-Air: 106B/12B, MIT, native glm45 tools. soundsgoodai/GLM-4.5-Air-NVFP4-KV-cache-BF16 reportedly works on NVIDIA Spark vLLM 26.03, 85 GB runtime, 128K, roughly two concurrent. Other NVFP4 builds crash. Exact weight size and single-stream speed unverified. GPQA 71.72 reported. Replacement fit plausible, not near-80-speed evidence.
* GLM Air REAP: 82B/12B pruned, base MIT. Community NVFP4 51 GB disk, vLLM/marlin 89.2 GB runtime at 64K. “158.39 tok/s” is AGGREGATE concurrency 32, median TPOT 192 ms; not voice speed. Quant quality vs current unverified.
* GLM-4.7-Flash: approximately 30B/3B, community Spark AWQ report 23.5 tok/s; FP4 size/config unverified here. Not bigger.
* Llama 4 Scout: 109B/17B; NVIDIA NVFP4 exists. Exact size and single-GB10 vLLM speed unverified; native tools, Llama 4 community licence. Theoretical four-bit weight floor 54.5 GB before scales; replacement fit plausible at modest context. Maverick approximately 400B/17B, four-bit floor 200 GB: does not fit. Neither is low-active enough. Comparable quant quality scores unverified.
* ERNIE4.5: 21B/3B or 300B/47B, Apache-2.0; vLLM architecture guide exists. Validated GB10 FP4 quant/size, native tool integration and speed unverified. 21B smaller; 300B theoretical four-bit floor 150 GB too big. No matching larger/A3–6B family member identified.
* Granite4-H-Small: 32B/9B, Apache-2.0, native enterprise tools. FP8/GGUF available; NVFP4 checkpoint/size and measured single-GB10 vLLM speed not verified. Replacement memory fit plausible at reduced precision, but neither larger nor as sparse. Comparable quality scores unverified.

Sources for exclusions:
https://howtospark.com/recipes/nemotron-3-nano-30b-a3b-nvfp4
https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4
https://dev.classmethod.jp/articles/dgx-spark-qwen3-6-35b-a3b-nvfp4-new-champion/
https://huggingface.co/zai-org/GLM-4.5-Air
https://huggingface.co/Firworks/GLM-4.5-Air-nvfp4/discussions/1
https://gauravmm.github.io/autobench/configs/glm-4-5-air-reap-82b-vllm-nvfp4/
https://developer.nvidia.com/blog/nvidia-accelerates-inference-on-meta-llama-4-scout-and-maverick/
http://ernie.baidu.com/blog/posts/ernie4.5/
https://docs.vllm.ai/projects/recipes/en/stable/Ernie/Ernie4.5.html
https://www.ibm.com/new/announcements/ibm-granite-4-0-hyper-efficient-high-performance-hybrid-models

## Final interpretation
Active parameter count is only a rough speed predictor. Memory traffic from shared/dense layers and output heads, expert shape/routing, layer count, KV, kernels and speculative acceptance all matter. Dormant experts raise resident memory, not guaranteed intelligence. None researched is clearly better while preserving current voice speed/latency. Keeping the existing model is an evidence-based recommendation, not a lack of larger sparse models.
Done check: PASS real candidates, primary cards, GB10 engine distinctions, memory estimates, licences/tools caveats, source links, no device changes. Missing numerical evidence is explicitly unverified rather than invented.
