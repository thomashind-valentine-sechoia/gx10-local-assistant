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
- [ ] Pick a licence, review upstream/model/data terms and attribution, scan content and author metadata, then explicitly approve any publication.

## Safe deep-model switching

Stop the fast vLLM service before loading Qwen3.8-Flash-Next; never run both at once on current memory. Build an exclusive lock/state machine, queue requests, wait for readiness, handle failure and restore the fast model after idle timeout. Coordinate restart policies so a reboot cannot auto-load competing models. Current `ha-llm` remains `unless-stopped`; documentation did not change it. Capture the existing deep launcher, llama.cpp revision, template support and model/projector hashes; measure speed, start time and round-trip swap cost before selecting defaults.

## “Ask Claude” / Grok Bot: research only, not implemented

The earlier conversation suggested invoking the official Claude Code CLI for explicit “Hey Jarvis, ask Claude…” requests. **This is not an approved or validated integration design.** Before proceeding, verify current Anthropic subscription/authentication terms and whether this automated third-party use is permitted. Official CLI login does not by itself establish permission to wrap subscription OAuth in Home Assistant. Do not extract/reuse OAuth credentials or assume subscription usage is a supported general API. A supported API route may require separate billing. Any cloud route must be explicit opt-in, disclose what leaves the GX10, and not become silent fallback. No login, subscription change or installation was performed for this documentation task.

No verified direct Home Assistant → Grok Bot messaging interface was established. Investigate supported interfaces rather than promising one.

## Hardware and future integrations

- Zigbee ZBT-2 coordinator and first bulb: pair, name, place in areas, expose minimally, test local intent path.
- Home Assistant Voice Preview Edition: add satellite and evaluate wake word/acoustics against phone experience.
- Blinds, door/window sensors, speakers/music and per-socket energy.
- Bambu P1S, kettle/coffee/toaster, garage door and cameras only with suitable safety rules and confirmations.

These are desired future capabilities, not installed/working claims.
