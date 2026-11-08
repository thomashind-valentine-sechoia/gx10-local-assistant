# Approved temporary fast-memory reduction — completed and fully restored

**Decision:** The test was not adopted. The fast model was restored to its original config, and the deep model is stopped.

**8 November 2026, 19:44–20:17 Europe/London. This is the latest result and supersedes the earlier blocked/failed deployment summaries below.**

## Decision summary
The downloaded deep model **works safely alongside a temporarily reduced fast model**, including real generation, tools on fast, and long-context smoke tests. However, it is **not a clear quality upgrade on the five requested household questions**, even with reasoning enabled, and simultaneous deep generation slows the fast model roughly fourfold. **Do not keep the reduced setup on this evidence.**

**Restoration completed and verified:** `ha-deep` is stopped; `ha-llm` is the exact preserved original container object, with its original 0.5 memory setting, 65,536 context, four sequences, 8,192 batched prefill, FP8 KV and MTP-2. Original `~/ha-llm/run.sh` was never edited; byte comparison and SHA-256 match. Fast generation and structured tool calls work again at original speed. Thomas has not been switched permanently to the test configuration.

## Authorization, original record and rollback
Thomas's quoted answer to question card t89s301 was: “Temporarily reduce the fast model's memory so we can test the deep model”. The approved scope was a temporary test followed by exact restoration regardless of whether deep won.

Original configuration was recorded before changing anything in `fast-original-config-20261108-1943.txt`: complete run.sh, Docker command/entrypoint, mounts, runtime/device requests, restart policy and memory/network limits. Original run.sh SHA-256 is `4233c785c3f04d5f45e564438390a1c73a895b8fecac64e31b4419cc80d78910`.

Rather than reconstruct the original container, it was stopped and temporarily renamed `ha-llm-original-test`. A separate temporary `ha-llm` ran the test. Restoration stopped that temporary container, retained it as `ha-llm-reduced-test`, renamed the preserved original back to `ha-llm`, and started it. Original/restored container ID is `014a0bdd68a5e14d009dd60e8c45512f39f00dcd337f564e8c534bf03189999b`. The original image, environment, mounts, ports and all Docker settings therefore remain its own original settings. A restoration timer was staged as a safety net; see lifecycle issue below. It has now been cancelled, with zero matching timers remaining.

## Configurations and memory
All GiB/MiB below are binary units. NVIDIA process memory is unified-memory allocation telemetry, not a separate discrete-VRAM budget; do not add it to system RAM usage. Cgroup figures also must not be added to NVIDIA figures.

| Setting/measurement | Original fast, restored | Temporary fast | Deep during test |
|---|---:|---:|---:|
| Model | Qwen3.6-35B-A3B NVFP4 | same | unsloth/Qwen3.8-27B-NVFP4 |
| GPU memory utilization | 0.5 | 0.30 | 0.24 |
| Context | 65,536 | **32,768** | **8,192** |
| Maximum sequences | 4 | 1 | 1 |
| Maximum batched tokens | 8,192 | 4,096 | 1,024 |
| EngineCore allocation, nvidia-smi | **58.43GiB** | **33.89GiB** | **29.84GiB** |
| Runtime model-loading allocation | 21.94GiB | 21.94GiB | 20.44GiB |
| KV allocation reported by logs | 34.20GiB on restore (34.14 original boot) | 9.76GiB | 7.67GiB final load |

The fast reduction released approximately **24.54GiB (26.35GB decimal)** of EngineCore allocation. Different profiling states caused small allocation variations despite identical restored flags.

System observations:
- Reduced fast alone, deep stopped: **72.82GiB available**, 6.38GiB swap occupied at that point.
- Both resident and answering: **39.24GiB available**; about 6.38GiB swap occupied.
- Minimum available during the final deep cold load and all subsequent tests: **28.49GiB**. The 9GiB advance safety threshold never tripped; the required 8GiB reserve was comfortably maintained.
- After original restoration: **46.88GiB available**, about 5.10GiB swap occupied. Available-memory snapshots differ with page cache and swapped inactive host pages; they are not interchangeable with model allocation deltas.
- Deep cgroup peak: **22.71GiB**, current approximately 4.05GiB at measurement; `memory.events` showed zero limit hits, zero OOMs and zero OOM kills. CUDA unified allocations are not necessarily fully represented by cgroup accounting; NVIDIA allocation and host reserve were measured separately.

## Deep runtime and cold-load measurements
Pinned checkpoint remains `unsloth/Qwen3.8-27B-NVFP4` at `f0b7c9e722f5565102fff8481c99e4d86ae099c7`, 23,417,592,488 safetensors bytes, in `/home/halead/deep-brain/qwen38-27b`. Runtime is separate `vllm/vllm-openai:v0.31.0-aarch64`, text-only, eager execution, FP8 KV, no MTP, `qwen3` reasoning parser and community-recipe `qwen3_xml` tool parser; model endpoint is loopback-only `127.0.0.1:8001`.

**Cache permission issue fixed:** deep runs as UID/GID 1001:1001, with its halead-owned persistent cache mounted at `/cache`; HOME, XDG_CACHE_HOME, HF_HOME, VLLM_CACHE_ROOT, TRITON_CACHE_DIR and FLASHINFER_WORKSPACE_BASE point into that writable location. A write/read/remove probe passed. All subsequent starts reached real inference without cache permission errors.

The isolated controller on loopback 8767 guards pre-load memory, serializes its answers-only requests and monitors available RAM every 250ms, stopping only `ha-deep` below 9GiB. Its on-demand cold request returned a real answer. Latest measured **cold readiness 198.726 seconds**, then **2.287 seconds** for a 21-token response. A preceding successful unloaded-model start measured 177.062 seconds plus 9.301 seconds for the first response, including cold inference kernel work. Thus allow roughly **3–3.3 minutes to load** under these tests, not an instant voice response. Filesystem/runtime caches were populated; this is cold model residency, not a freshly booted/offline machine test.

Warm non-reasoning, five practical questions:
- Full HTTP request-to-first-spoken-token: **206–218ms**.
- Decode: **10.55–10.64 tok/s** (median 10.58).
- Complete concise answers: **8.20–13.10 seconds**.

Reasoning enabled, same five questions and concise-answer instructions:
- First internal reasoning token: **189–225ms**, **not user-facing answer latency**.
- First spoken answer content: **24.02–45.51 seconds**.
- Complete answers: **32.52–55.36 seconds**.
- Generation including reasoning tokens: median **10.48 tok/s**, range 8.34–10.50; the first response overlapped the fast concurrency benchmark.
- All five produced completed spoken answers within the 1536-token cap; recorded reasoning counts were 247–472 tokens. Raw reasoning text was not retained.

## Fast performance and tool checks
Five identical short prompts, temperature zero, streaming timer started **before the HTTP request**, so TTFT includes response headers but not STT/TTS or the full voice pipeline. Decode uses completion tokens divided by first-token-to-end elapsed time, consistent across these rows, with a slight first-token numerator bias. These are smoke measurements, not repeated controlled statistical benchmarks; answer lengths and wording varied.

| Condition | TTFT range | Decode range | Median decode |
|---|---:|---:|---:|
| Original immediately before approved changes | 107–114ms | 78.4–86.2 tok/s | **80.84** |
| Reduced fast alone, after stopping deep | 101–110ms | 75.7–85.8 tok/s | **83.11** |
| Reduced fast, deep resident but idle | 103–119ms | 81.2–85.3 tok/s | **83.92** |
| Reduced fast during deep reasoning generation | **254–270ms** | **19.7–22.6 tok/s** | **21.80** |
| Exact original restored | **94–109ms** | **76.8–82.1 tok/s** | **80.97** |

Structured tool-call smoke tests passed in the original, reduced, both-loaded, simultaneous-generation and restored conditions. Each correctly emitted `get_temperature` with JSON `{"room":"kitchen"}` instead of inventing a temperature. This was a synthetic API tool test, not an actual device action or end-to-end Home Assistant voice test. Restored tool-call response completed in 0.965 seconds (a full-response timing, not streamed tool TTFT).

Long-context smoke tests with both models resident also passed:
- Deep: **7,039 prompt tokens**, correct `READY` response, 3.69 seconds total.
- Reduced fast: **30,039 prompt tokens**, correct `READY` response, 6.66 seconds total.

These establish usable configured context capacity for a single simple request, not difficult long-context reasoning or multi-user load.

## Five-question quality verdict
**No clear deep-model win.** Testing both non-reasoning and reasoning avoided judging the deep model solely in its fast/no-thinking mode. It was sometimes more specific, but still made unsupported or unreliable practical claims. This is a five-question exploratory judgement, not an externally graded model ranking.

| Topic | Comparison |
|---|---|
| Bleeding a radiator | Both gave broadly useful cool-system/quarter-turn/check-pressure advice. Deep did not show a material improvement over the approved-run fast answers. |
| Compression tap | **Deep was better** at focusing on the rubber washer and checking a damaged valve seat. Fast repeatedly conflated a traditional compression tap with a ceramic cartridge, sometimes recommending replacing the entire tap unnecessarily. Deep's concise disassembly instructions were still incomplete. |
| Broad beans in Cornwall | Deep without reasoning invented a need for a “bean fly”-resistant variety. With reasoning it substituted a questionable pea-moth benefit and unusually early September timing. Fast also overgeneralised autumn preference and occasionally misstated pest trade-offs. Neither supplied consistently trustworthy local gardening advice. |
| Sourdough starter | Deep supplied useful temperature/feeding detail, but its non-reasoning answer treated the float test as definitive, which it is not. Even reasoning mode still suggested binning a flat starter too readily; fast also varied in its diagnosis. No robust deep win. |
| UK ceiling light | Both warned to isolate, identify wiring and get an electrician if unsure. Deep's non-reasoning answer specifically suggested a multimeter for proving dead rather than a proper safe-isolation procedure. Its reasoning answer was more cautious but generic. Neither demonstrated a decisive safety/diagnostic advantage or a complete safe working procedure. |

## Viability and final state
**Memory coexistence is technically demonstrated at fast 32K/one sequence and deep 8K/one sequence**, with at least 28.49GiB observed available through startup and these tests. This is short-run viability, not a permanent-service or day-long stability certification. Fast speed is essentially unchanged when deep is merely resident, but active simultaneous generation reduces fast throughput by about **74%** and increases TTFT. The slow deep spoken response and inconsistent quality do not justify changing Thomas's fast setup permanently on this evidence. A 64K reduced-fast configuration may be feasible from logged KV capacity, but it was **not tested and is not the validated recommendation**.

Final state verified at about **20:17 Europe/London**:
- Original fast container restored, running, same container ID and launcher checksum, original flags and image; model readiness, text speed and API tools verified.
- `ha-deep` stopped, no automatic restart policy. Temporary reduced fast containers remain stopped as diagnostic artifacts; no model files were deleted.
- Test controller service stopped/disabled, temporary rollback timer stopped, halead linger restored to **no**.
- Original `ha-deep-brain` container on 8766 remains unchanged and still guards against the old oversized GGUF. The validated experimental controller is staged on disk, **not switched into live HA routing**.
- Home Assistant and its prompt were not changed or restarted during this approved test. **Ask Deep Brain remains unexposed to Assist.** No GitHub/repository changes were made.

Lifecycle defects discovered and corrected during the experiment:
1. A temporary fast prefill cap of 2048 failed because hybrid Mamba block size was 2128; changed only the test launcher to 4096. The corrected 32K fast setup passed.
2. vLLM health returns an empty HTTP 200 body, not llama.cpp JSON; controller readiness probe was corrected to `/v1/models`, then successful cold readiness was timed.
3. With halead linger disabled, its user service and transient timer were stopped after the last SSH session. Linger was temporarily enabled and a new persistent-session restoration timer armed before the final stable test, then reverted after manual restoration. This was not a model or memory failure. Ten-minute idle unload remains implemented but **was not timed end-to-end in this run**; explicit guarded unload was verified several times.

## Acceptance checklist
- Original configuration recorded before change: PASS.
- Temporary lower fast allocation, usable 32K context and synthetic tool calls: PASS.
- Writable FlashInfer caches and real deep inference: PASS.
- 8GiB reserve/safety stop retained, no OOM during approved coexistence: PASS.
- Cold/warm performance, both-resident and concurrent regression, five questions in two deep modes: PASS.
- Deep clearly superior: **NO**.
- Stop deep and restore original exactly, verify original speed and tools: PASS.
- Persistent production HA integration / ten-minute live idle test / permanent reduced setup: NOT ENABLED; Thomas decides on any future change.

Raw results: `approved-test-results.json`, `both-final-memory.txt`, `restored-final-state.txt`, `approved-deep-load.log`, `approved-fast-reduced.log` alongside this report on the box. JSON result files, launchers and controller also remain in `~/deep-brain/` on GX10.

---

# Earlier runs — historical findings, superseded where noted above

# Final deployment result — downloaded; unsafe load aborted, not enabled

8 November 2026, 18:45–19:41 Europe/London. This section supersedes the transfer-in-progress section below.

## Outcome and hard-rule compliance
- Download PASS: `unsloth/Qwen3.8-27B-NVFP4`, pinned revision `f0b7c9e722f5565102fff8481c99e4d86ae099c7`, completed successfully after about 43 minutes. Two safetensors total **23,417,592,488 bytes (21.81 GiB)**, matching index metadata: main 22,568,192,096 bytes, MTP 849,400,392 bytes. GX10 path `/home/halead/deep-brain/qwen38-27b`. Hugging Face emitted non-fatal permission-setting warnings; downloader exit status zero and `DOWNLOAD_COMPLETE` verified.
- Recipe runtime PASS: pulled `vllm/vllm-openai:v0.31.0-aarch64`; checked version and supported `qwen3_xml` parser and text-only flag. Existing NVIDIA image is vLLM 0.21 development and was not changed.
- Simultaneous safe deployment **FAIL / STOPPED**: a guarded reduced-settings test hit the emergency reserve threshold during loading. No deep answer was generated, so there is no evidence this model is better than the fast model. No NVIDIA fallback or additional model load was attempted after the reserve trip.
- **`ha-llm` was never stopped, restarted or reconfigured.** It still reports its original start time 7 November 2026 14:29:30 Europe/London and restart count zero.

## Actual reduced test configuration
Container `ha-deep`, loopback `127.0.0.1:8001`, 8192 context, one sequence, 1024 maximum batched prefill tokens, FP8 KV, `gpu-memory-utilization=0.24`, eager execution, text-only, no MTP speculative decoding, `qwen3` reasoning parser and `qwen3_xml` tools parser. Network disabled at model-library level with HF/Transformers offline flags. No request-content logging. Container memory/swap limit 32GiB/32GiB (no container swap allowance), dropped capabilities, no-new-privileges; model mount read-only.

A separate test controller on loopback 8767 used the existing answers-only interface, a weights-plus-8GiB preflight allowance, 30GiB maximum load budget, ten-minute idle policy, and an independent 250ms monitor that stops **only `ha-deep`** below 9GiB available (1GiB advance margin over the required 8GiB reserve). Five mocked safety/lifecycle unit tests passed; this is not validation of actual cold readiness or ten-minute live unload.

First launch failed before model loading because vLLM 0.31 replaced `--disable-log-requests` with `--no-enable-log-requests`; corrected only the newly created deep container. The second launch ran from **19:37:32 to 19:40:37 Europe/London**, loaded the checkpoint shards in **135.55 seconds**, but never reached API readiness. It also logged a concrete runtime-cache write error: `PermissionError: /root/.cache/flashinfer` (and `/root/.cache/vllm`), because the capability-dropped container's cache identity was not aligned with the halead-owned mount. This is a separate configuration defect; fixing it alone would not prove safe coexistence. No third attempt was made.

## Memory and performance measurements
- Available memory immediately before the cold test: **45,280,145,408 bytes = 42.17GiB**.
- Minimum monitored available memory: **9,470,525,440 bytes = 8.82GiB**; the 9GiB safety trip fired, deep was stopped, and the 8GiB reserve was not observed breached. Incremental loss of available memory about **33.35GiB**, not an isolated GPU/process peak measurement.
- System swap increased from about **1.14GiB** before testing to about **11.79GiB** at failure; about **11.69GiB** remained occupied after stopping. The deep container itself had no swap allowance, so host/service memory pressure was substantial despite the available-memory reserve. Do not treat swap as inference capacity or force swapoff.
- At 19:41 Europe/London available memory recovered to about **52.83GiB**; this exceeds the original figure because inactive host memory remains swapped out, not because the fast allocation was reduced.
- Valid cold readiness, deep TTFT, deep decode rate and process/GPU peak: **not measurable — server never became ready**. Failed elapsed startup was about 184 seconds, not a successful cold-load time. The controller request correctly returned unavailability, not a fabricated answer.

Fast-model five-question streaming baseline and post-test measurements (HTTP request timer includes response headers; excludes speech pipeline):

| Metric | Before | After stopped deep test |
|---|---|---|
| TTFT | 95–427ms | first request 1327ms, following four 117–142ms |
| Decode rate | 79.1–92.1 tok/s | 76.5–93.0 tok/s |
| Median decode rate | 86.4 tok/s | 86.6 tok/s |

Decode throughput is comparable in this short smoke test. **Do not claim latency was completely unchanged**: the first recovery request was slower and the host retains substantial swap usage. There was no successful simultaneous deep-inference/fast-inference regression test. Five questions were asked of fast before and after; deep could answer none, so the requested head-to-head comparison is incomplete. Full questions/answers are in `fast-before.json` and `fast-after.json` alongside this report and on GX10 under `~/deep-brain/`.

## Quality observations, not a deep-vs-fast verdict
The fast baseline made avoidable errors: said steam rather than air when bleeding a cool radiator, conflated a compression tap's rubber washer with a ceramic cartridge, overgeneralised autumn broad-bean sowing, and suggested discarding a sluggish sourdough starter too readily. Its electrical answer warned against guessing and recommended an electrician, but was not a complete safe-isolation procedure. These observations motivate a better tested deep model; they do not establish that the downloaded model is better. Post-test fast answers varied despite temperature zero, so a five-item comparison would be exploratory rather than a robust quality evaluation.

## Final installed state and next decision
- `ha-deep` exists **stopped**, with no restart policy to auto-load it. Download and runtime caches are retained for a controlled future investigation.
- Test service `ha-deep-brain-vllm.service` is **stopped and disabled**. Its files remain staged in `~/deep-brain/`; no active HA routing points at port 8767. User linger was temporarily enabled for persistence investigation, then restored to its original **no** state.
- Original **`ha-deep-brain` on 8766 is still running unchanged**, guarded against the old oversize GGUF. Its health truthfully reports it cannot fit. Integration was deliberately **not switched** to a failed new server.
- Home Assistant was not restarted or modified during this attempt. `script.ask_deep_brain` remains unexposed; its prompt was not changed.
- No repository edits or push.

Do not enable routing now. A future attempt needs a loading strategy with demonstrably lower transient host-memory pressure and correct writable-cache ownership, or explicit approval for a controlled fast-KV reconfiguration. This run makes no such changes and stops at the safety boundary.

Exact **future-only** Assist prompt line, after a deep backend passes acceptance testing and the tool is exposed:

> For complex practical questions, or when I say “think harder” or “ask the big model”, call Ask Deep Brain (script.ask_deep_brain) with my full question, wait for its answer, and relay it clearly; if it reports unavailable, say so and never pretend the deep model answered.

## Acceptance checklist
- Pinned download and parser/runtime check: PASS.
- 8GiB reserve protected and fast container untouched: PASS (emergency stop).
- Safe working deep inference, real TTFT/tok/s and deep quality comparison: FAIL / NOT AVAILABLE.
- Live on-demand/ten-minute integration and Assist routing: NOT ENABLED because inference failed.
- Fast availability/post-test smoke measurements: PASS with latency/swap caveats.
- Final safe state, diagnostic preservation, report: PASS.

---

# Deployment resumed — transfer in progress

8 November 2026, 18:45–19:13 Europe/London.

SSH is working again. Fast container remains untouched (started 7 November 14:29:30 Europe/London; restart count zero). Fresh available memory initially 42.09 GiB, disk 416 GiB available.

Started durable `ha-deep-download` container as halead UID 1001, downloading public `unsloth/Qwen3.8-27B-NVFP4` pinned to `f0b7c9e722f5565102fff8481c99e4d86ae099c7`, repository files total 23,444,511,852 bytes. Target `/home/halead/deep-brain/qwen38-27b`. At 19:13 Europe/London approximately 14 GiB has downloaded. Harmless huggingface permission-setting warnings occurred; completion is not yet verified.

Community recipe image `vllm/vllm-openai:v0.31.0-aarch64` is pulling. Existing NVIDIA image is only vLLM 0.21.0 development; not assumed compatible. No model has loaded yet and existing controller/HA remain unchanged.

Five fast-model baseline answers saved remotely as `~/deep-brain/fast-before.json`; full end-to-end HTTP streamed TTFT 95–427ms, decode 79.1–92.1 tok/s. Unlike previous report this timer includes HTTP headers. Not comparable directly to the old header-excluding benchmark. Quality problems in baseline: mentions steam instead of air when bleeding a cool radiator; confuses compression-tap washer with ceramic cartridge; overgeneralises autumn sowing; suggests discarding sluggish sourdough too readily. No deep quality verdict yet.

Prepared but NOT installed a host-user controller variant for fixed-name `ha-deep` start/stop only, with 8GiB reserve, pre-load weights-plus-8GiB guard, independent emergency unload at below 9GiB available, ten-minute idle unload. Five mocked unit tests pass. Pending actual image help/compatibility, safe model load, performance, persistence, and HA integration. `halead` user systemd works but linger currently disabled. Assist remains unexposed.

---

# Qwen3.8-27B NVFP4 follow-up — blocked before download

8 November 2026, 18:42–18:44 Europe/London.

Thomas approved deploying `unsloth/Qwen3.8-27B-NVFP4` without stopping or modifying `ha-llm`. The public community recipe was read successfully at https://ctala.github.io/local-llm-agentic-workflows/recipes/.

**Current blocker:** all three permitted SSH attempts using the supplied Tailscale ProxyCommand and ConnectTimeout=20 failed during banner exchange. The inspection/download prerequisite command never reached a shell. No model was downloaded, no download container was started, and no remote configuration was changed during this follow-up. The previous controller and HA groundwork below remain the last verified state, not a newly verified current status.

## Recipe findings, not GX10 measurements
The community base recipe reports 11.0 tok/s, approximately 47.0 GB unified memory and 6.6-minute loading at 131072 context, four sequences, FP8 KV, gpu-memory-utilization=0.4, max-num-batched-tokens=16384, prefix caching and vLLM v0.31.0-aarch64. It uses `VLLM_TARGET_DEVICE=cuda`, `VLLM_FLOAT32_MATMUL_PRECISION=high`, `CUTE_DSL_ARCH=sm_121a`, reasoning parser `qwen3`, and tool parser `qwen3_xml` (not the requested `qwen3_coder`). Image limit is two and video zero. These are source-reported results, not performance measured here.

Those exact settings cannot simply be copied: 47 GB exceeds the previously available approximately 42 GiB once the required at-least-8GB reserve is included. A deployment must first verify fresh available RAM/disk, actual checkpoint bytes and local vLLM support; reduce context/concurrency/prefill, consider text-only mode and eager execution if appropriate, and enforce a conservative load/peak-memory budget. It must remain separate on loopback port 8001, with no modifications to the fast container. No reduced-memory configuration has yet been validated, so coexistence is **not confirmed**.

## Remaining acceptance tests
- Durable background download to a halead-owned path, with enough disk and a recorded pinned checkpoint revision.
- Separate on-demand vLLM container and controller lifecycle integration, ten-minute idle unloading, minimum 8GB system reserve and safe rollback of the deep service only.
- Actual cold readiness, warm first-token latency, generation rate, peak memory and OOM checks, plus simultaneous fast-model regression checks.
- Five deep-vs-fast practical answers and safety/accuracy review.
- Leave `script.ask_deep_brain` unexposed until deep inference is genuinely working; only then provide the final routing prompt and exposure instructions.

No user installation commands or claims of a successful model change are appropriate yet. Working GX10 SSH reachability is needed to continue. Do not reset the shared box's Tailscale connection blindly or request passwords.

---

# GX10 deep local brain — implementation and capacity report

8 November 2026, approximately 18:23–18:29 Europe/London.

## Outcome
Controller and Home Assistant tool groundwork are installed and tested. **The existing deep model cannot safely coexist with the fast model, and has NOT been loaded.** No changes were made to `ha-llm`, its flags, startup script, or model. It remained up for 28 hours throughout. No repository was modified or pushed.

The crucial correction is that the downloaded deep GGUF is **111,334,654,784 bytes (111.33 GB / 103.69 GiB), not approximately 80 GB**. Lowering the fast model's KV allocation alone will not make this particular file fit.

## Actual inspection
### System
- Physical memory: 130,595,995,648 bytes = 121.63 GiB.
- Initial available memory: 45,205,114,880 bytes = 42.10 GiB, including reclaimable cache. Final available memory was approximately 42.04 GiB.
- Initial used memory: 85,390,880,768 bytes = 79.53 GiB.
- Swap: 16 GiB total; approximately 1.14 GiB already occupied. Swap is not safe inference headroom, and page cache must not be added again to MemAvailable.
- Home Assistant uses host networking, so its localhost can reach the controller's loopback endpoint.

### Fast model — unchanged
`nvidia/Qwen3.6-35B-A3B-NVFP4`, alias `qwen3.6-35b-a3b`, in `ha-llm`:
- `--gpu-memory-utilization 0.5`
- `--max-model-len 65536`, `--max-num-seqs 4`
- `--max-num-batched-tokens 8192`, FP8 KV cache, MTP speculative decoding, thinking disabled.
- Existing vLLM startup logs report **21.94 GiB model-loading allocation**, **34.14 GiB available KV allocation**, approximately **0.20 GiB actual CUDA graph pool**, and **2,330,338 KV token capacity**. Those are runtime logs from the existing startup, not new load measurements.
- Parent-provided process telemetry: approximately 60.5 GB GPU for EngineCore, 3.6 GB Kokoro, 1.3 GB Parakeet; exact GB/GiB convention in that telemetry was not independently established.

### Deep model — actual files and identity
Model directory:
`/home/sechoia/.cache/huggingface/hub/models--unsloth--Qwen3.8-Flash-Next-GGUF/snapshots/766911a6b7369840a91dbcd95f9f997acaab6cd6/UD-Q4_K_XL/`

| Shard | Bytes |
|---|---:|
| 00001 | 10,946,624 |
| 00002 | 49,859,583,136 |
| 00003 | 49,376,141,504 |
| 00004 | 12,087,983,520 |
| **Total** | **111,334,654,784** |

Allocated disk blocks closely match the file sizes: this is not an apparent-size/sparse-file artefact. The separate 907,542,944-byte multimodal projector is not included or needed for voice text answers.

GGUF metadata says `general.architecture=qwen4exp`, `general.name=Qwen3.8 Flash Next`, description `A Preview of the Qwen4 Architecture`, size label `512x56B`, 512 experts, 10 selected experts, 48 blocks, 262,144 native context. The four tensor tables contain **176,943,899,520 tensor elements** in total. This does not match the brief's 125B-A6B description; tensor-element count should not be casually equated to independently verified trainable/active parameter counts. Verify which model is actually intended before selecting another quantization.

Binary: `/home/sechoia/llama.cpp/build/bin/llama-server`, version **0.7.0-dev, build 11909, commit caa8191df1**, GNU 13.3.0 Linux aarch64. Version and needed flags were checked inside the existing NVIDIA image with GPU runtime and explicit library path, without loading weights. Actual model-architecture compatibility during loading is still untested.

`halead` cannot traverse `/home/sechoia` directly. A narrowly mounted, read-only Docker volume works; the controller runs as UID/GID 1000 (sechoia), not root. No password or Claude credential was accessed.

## Capacity options — before any fast-model changes
1. **Keep fast exactly as it is (implemented safety policy).** Approximately 42.1 GiB available. Reserving 8 GiB for other services and an 8 GiB provisional deep runtime/workspace allowance leaves about **26 GiB for deep weights**. A smaller model could be evaluated within this budget; no download was initiated.
2. **Reduce fast allocation to roughly 28–32 GiB (NOT applied).** The weights already account for approximately 21.94 GiB, so a much smaller KV pool/context/concurrency is a plausible optimization, but the exact minimum needs a controlled restart and validation. Interpreting the reported 60.5 footprint as GiB gives approximately **70.6–74.6 GiB available** after reduction. Subtracting the same two 8 GiB allowances gives approximately **54.6–58.6 GiB for deep weights**; conservatively choose roughly 50 GiB or less until measured. An actual 80 GB decimal GGUF is 74.5 GiB, so even that would leave little/no runtime room, not a safe default.
3. **Existing deep GGUF plus existing fast weights:** 103.69 + 21.94 = **125.63 GiB**, already above the machine's **121.63 GiB total**, before KV, workspaces, speech, HA and OS. Even reclaiming the entire logged 34.14 GiB fast KV allocation would increase available memory only to about 76.2 GiB, still approximately 27.5 GiB short of the deep weight files alone. Reducing context cannot fix that weight budget.
4. **Swap fast out (NOT done; not recommended for seamless voice).** This would violate the instruction not to stop `ha-llm`, remove the voice planner while deep runs, and incur the previously reported approximately 226-second fast restart. Deep-alone capacity/performance has not been tested either.

Recommendation: confirm the intended model identity, then choose a substantially smaller deep model/quantization. If a larger secondary model is desired, obtain approval for a later controlled fast-KV reduction. Do not promise simultaneous operation of the existing GGUF merely by reducing context.

## Installed infrastructure
### Controller
- Container: `ha-deep-brain`, Docker restart policy `unless-stopped`; restart tested successfully.
- Files on GX10: `~/deep-brain/controller.py`, `run-controller.sh`, `ask_deep_brain.yaml`.
- Endpoint: `127.0.0.1:8766`; managed llama.cpp port would be `127.0.0.1:8081` to avoid the user's separate 8080 setup.
- `GET /health` reports real model bytes, available memory, safe budget and loaded status.
- `POST /ask` accepts JSON `question` (1–4000 characters), requires `X-Deep-Brain` (shared header value omitted), rejects browser Origin headers, serializes requests and returns answer JSON.
- Entirely local answers-only path; no cloud, tools, shell actions, home control, or question/access logs.
- Read-only container/files/model mounts, dropped capabilities, no-new-privileges, sechoia UID, no swap allowance, 36 GiB container limit, 128 PID limit.
- Memory guard runs **before launching llama.cpp**, counts all shards, reserves 8 GiB for the host plus an 8 GiB provisional runtime allowance. The 36 GiB deployment cap is deliberate for the current fast allocation; a later larger-model deployment needs explicit re-budgeting, not just a model-path change. Cgroup limits are defense-in-depth, not a guarantee that every CUDA driver allocation is charged identically.
- Planned load settings: 8192 context, one parallel slot, GPU offload; 600-second load limit, 120-second answer limit, 384 answer tokens, concise practical British-English instructions and safety caveats.
- Idle monitor unloads only its own llama.cpp subprocess after ten idle minutes; no code stops/restarts any other service. Busy requests are not interrupted by idle unload.
- Idle footprint measured at **13.46 MiB**.

Real endpoint test returned HTTP 503 immediately: model files 103.7 GiB, safe budget approximately 34.0–34.1 GiB, `loaded=false`, with a clear explanation and no model launch. This was tested from both the host and inside Home Assistant. It is an intentional refusal, not a working deep-model answer.

### Home Assistant
- Added `/config/packages/ask_deep_brain.yaml`, script entity **`script.ask_deep_brain`**, alias **Ask Deep Brain**.
- Pattern follows existing REST-command/script tools; question field, response variable, status, and explicit truthful unavailability fallback. The returned answer is reference text, never instructions to execute tools.
- Description suggests long practical questions or explicit “think harder” / “ask the big model”; notes the potential multi-minute first-load delay.
- Full config check passed. Home Assistant restarted and returned HTTP 200; entity exists and no matching startup/config errors were found.
- Backup: `/config/backups/before-deep-brain-20261108-182614/` (Europe/London), containing configuration.yaml and the prior packages directory.
- **Not exposed in Assist, and the fast-agent prompt was not changed**, because the current model cannot fit. Avoid automatically routing useful questions to an intentionally unavailable model.
- Once a viable model is installed and benchmarked, expose **Ask Deep Brain** under Settings → Voice assistants → Expose. No new user install or sudo commands are needed for the installed groundwork.

Optional read-only checks on GX10:
```sh
curl -s http://127.0.0.1:8766/health
docker ps --filter name=ha-deep-brain
docker ps --filter name=ha-llm
```

## Tests and performance
- **13/13 controller unit/HTTP tests pass:** memory refusal never launches a subprocess, readiness/reuse, owned-process cleanup, answer mapping, timeout cleanup, ten-minute idle unload, active-request protection, input validation, origin/header checks, busy handling and HTTP refusal/answer mapping. Positive deep loading/generation are mocked in these tests, not real-model measurements.
- Real guarded request from HA: HTTP 503, `loaded=false`.
- Controller restart/persistence: pass.
- Home Assistant full configuration validation/startup/entity presence: pass.
- Full Assist voice tool invocation: not tested; entity deliberately unexposed.
- Deep cold readiness / warm first token / tokens-per-second / peak memory: **not measured**, because a test load would be unsafe under the stated constraint.

Existing fast benchmark, five short questions:
| Metric | Before | After controller + HA restart |
|---|---|---|
| Streamed TTFT | 89–97 ms | 89–91 ms |
| Reported decode rate | 78.9–88.4 tok/s | 71.3–93.1 tok/s |
| Tool TTFT | 236–238 ms | 236–242 ms |

These are the existing `~/ha-llm/bench.py` measurements: its TTFT timer starts after HTTP response headers, so **not full end-to-end voice/request latency**. Decode timing includes the first token in the numerator. Answers and token counts varied, and HA had just restarted, so this is a brief smoke/regression check, not a statistically controlled performance comparison. Fast readiness remained HTTP 200 and the fast container never restarted.

## Ready-to-adapt repository documentation (do not push yet)
### models.md
The deep local brain is intended for longer practical explanations while the fast local model remains responsible for everyday voice requests. A loopback-only controller and Home Assistant `Ask Deep Brain` script provide an answers-only interface, with a ten-minute idle-unload policy. The first request may require a substantial cold load. On the current GX10, the downloaded Qwen3.8 Flash Next UD-Q4_K_XL split GGUF occupies 103.69 GiB, so the controller refuses to load it alongside the fast model rather than risk the working assistant. A smaller model or quantization must be selected and measured before enabling this tool in Assist; reducing context alone does not remove the weight-memory requirement.

### performance.md
GX10 capacity inspection on 8 November 2026 found 121.63 GiB physical RAM and approximately 42.1 GiB available with the fast assistant running. Existing vLLM logs report 21.94 GiB for model loading and 34.14 GiB allocated to KV cache. The downloaded deep GGUF totals 111,334,654,784 bytes (103.69 GiB), excluding its unused multimodal projector. No deep-model load or throughput benchmark was attempted because its weights plus the fast weights already exceed physical RAM. The guarded controller idles at approximately 13.46 MiB and returns explicit unavailability without stopping the fast model. A brief fast-model regression check found streamed first-token timings of 89–91 ms and tool first-token timings of 236–242 ms; these exclude HTTP-header and voice-pipeline latency and are not deep-model benchmarks.

## Done-list
- Inspect actual memory, model paths, binary, ownership, vLLM flags: PASS.
- Report real capacity options before stopping/reconfiguring fast: PASS; fast untouched.
- Controller and HA script groundwork, validation, persistence, truthful failure: PASS.
- Usable deep model / cold and warm deep measurements: BLOCKED by actual model size, no unsafe attempt.
- Assist exposure/automatic routing: DEFERRED until a viable model works.
- Fast-model readiness/regression smoke check: PASS with timing caveats above.
- Repository documentation supplied without pushing: PASS, in this report.
