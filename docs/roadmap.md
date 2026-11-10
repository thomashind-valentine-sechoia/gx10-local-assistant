# Roadmap and acceptance checklist

## Before calling this tested or publishing

- [x] Complete and checksum-verify full English Wikipedia (8 Nov 2026, 13:10 GMT); Kiwix full-archive search working.
- [ ] Test real Assist search → article → cited answer and confirm web-search grounding retest.
- [ ] Verify real Assist web-tool execution after exposure; user confirmation of configuration is not evidence of every tool succeeding.
- [ ] Measure microphone → wake word → STT → local intent/LLM → TTS → phone playback, including p50/p95 and screen-off behaviour.
- [ ] Test unsupported questions, unavailable tools and parser failures without fabricated success.
- [ ] Test with internet disconnected on the LAN, including model and speech restarts after asset caching.
- [ ] Validate actual light/socket/blind devices, aliases, areas, confirmation rules and physical outcome.
- [ ] Record final installed asset sizes, exact app versions, ASR/Kokoro model revisions and original benchmark logs.
- [ ] Reboot recovery test; add a reliable downloader service if wanted.
- [x] Project licence is MIT; see [LICENSE](../LICENSE).
- [ ] Review upstream/model/data terms and attribution, scan content and author metadata, then explicitly approve any publication.

## Safe deep-model switching

Stop the fast vLLM service before loading Qwen3.8-Flash-Next; never run both at once on current memory. Build an exclusive lock/state machine, queue requests, wait for readiness, handle failure and restore the fast model after idle timeout. Coordinate restart policies so a reboot cannot auto-load competing models. Current `ha-llm` remains `unless-stopped`; documentation did not change it. Capture the existing deep launcher, llama.cpp revision, template support and model/projector hashes; measure speed, start time and round-trip swap cost before selecting defaults.

## “Ask Claude”

An opt-in `script.ask_claude` package is in use on the GX10. It is for explicit “ask Claude” requests only, prefixes answers with “Claude says:”, and must not become a silent fallback. Keep reviewing Anthropic subscription/authentication terms for this wrapped CLI use. Do not extract or reuse OAuth credentials. A supported API route may require separate billing.

No verified direct Home Assistant → Grok Bot messaging interface was established. Investigate supported interfaces rather than promising one.

## Hardware and future integrations

- Zigbee ZBT-2 coordinator and first bulb: pair, name, place in areas, expose minimally, test local intent path.
- Home Assistant Voice Preview Edition: add satellite and evaluate wake word/acoustics against phone experience.
- Blinds, door/window sensors, speakers/music and per-socket energy.
- Bambu P1S, kettle/coffee/toaster, garage door and cameras only with suitable safety rules and confirmations.

These are desired future capabilities, not installed/working claims.
