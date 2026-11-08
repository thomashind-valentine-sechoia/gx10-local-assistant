# Measured performance, not promises

These approximate **local component results were recorded during the 7–8 November 2026 build**. They are not vendor/community benchmarks. Original complete run logs and distributions were not available in this documentation run; values below are carried from the build conversation summary. Tests were not rerun while collecting documentation, to avoid disturbing the live assistant.

| Measurement | Recorded result | Scope / limitation |
|---|---|---|
| Fast LLM first output | ~85 ms | Warm short prompts; benchmark timer caveat below; not phone-to-answer latency |
| Fast LLM decode | ~75–100 output tokens/s | Short replies; not a long-context or concurrent-load benchmark |
| LLM tool-call generation | ~0.5–0.75 s | Generating the call, not physically changing a device |
| TTS first audio | 89–237 ms | Local Wyoming → Kokoro path; not network delivery or phone playback |
| Warm STT | 40–83 ms | After audio-stop, using generated test audio; excludes speaking duration, VAD and endpoint detection |
| Stop fast LLM | ~3 s | One recorded stop, not a distribution |
| Start fast vLLM server | ~226 s | One recorded startup; compile/cache/download conditions incompletely captured |
| Whole-host memory in original report | ~77 GB used / ~44 GB available | Original units were informal; not model weights or GPU-only residency |

## Reproduction scripts and timing traps

- [bench_llm.py](../scripts/bench_llm.py) is the copied local test: a warm-up, five short general questions and two synthetic home-control schemas. It requests up to 200 output tokens and temperature 0.6. It does **not** execute HA services.
- That script starts its clock **after `urllib.request.urlopen` returns response headers**. Its printed TTFT excludes request setup and potentially processing before headers. It is therefore not a rigorously measured full request-to-first-token latency; the ~85 ms must be read in that context.
- Its decode formula is completion tokens divided by elapsed-after-first-output, an approximate estimator rather than a calibrated throughput tool. It includes all completion usage, possibly special/reasoning tokens.
- [bench_voice.py](../scripts/bench_voice.py) sends short Kokoro-generated WAVs to Parakeet. TTS timing starts before synthesize; STT starts at audio-stop, after uploading the complete WAV. This tests neither real microphone acoustics nor user accent, and is not an end-to-end Assist pipeline test.
- Both scripts are historical minimal harnesses with no request/socket timeout; a missing service can hang them. Run manually on the GX10, in a controlled test window; interrupt if stalled. The voice harness writes disposable `/tmp/s*.wav` files.

## Live memory snapshot during documentation

Read-only inspection on 8 November 2026 (Europe/London, GMT): `free -b` reported **83,570,540,544 bytes used** (~77.83 GiB), **47,025,455,104 available** (~43.80 GiB), and **130,595,995,648 total** (~121.63 GiB). Cache and memory accounting mean “used” is not simply all resident model allocations. Some swap was in use; pressure behaviour was not benchmarked.

## Not measured / acceptance work

No validated end-to-end wake-word-to-spoken-response latency, real device action latency, p50/p95, cold STT/TTS series, UK-accent error rate, full 64K prompt performance, many-user concurrency, energy use, deep model speed/start/swap time, full encyclopedia response latency, or reboot recovery benchmark exists here. No claim that the complete stack has passed an internet-disconnected test is made.

Future runs should capture full request timing before connection, software/model revisions, context length, warm/cold conditions, prompt/output lengths, raw logs without personal data, repeated trials and p50/p95. Preserve component versus user-perceived latency separately.
