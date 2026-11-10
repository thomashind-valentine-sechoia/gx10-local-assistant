# Troubleshooting

## Model/tool problems

- **Several tool calls fail:** the observed `qwen3_xml` parsing issue affects multiple calls in a response. Disable **Parallel tool calling** in Local OpenAI. This reduces risk but is not a proof that the parser can never emit multiple calls. Test tool names/arguments and serial actions before trusting home controls.
- **Reasoning latency / no “off” dropdown:** server defaults include `{"enable_thinking":false}`. The integration did not present an explicit Off option in this setup; leave its Thinking mode dropdown empty and do not select an enabling option. Verify actual request behaviour after upgrades; an empty UI is not a universal guarantee of thinking being off.
- **Wrong server URL:** HA is host-networked; use `http://127.0.0.1:8000/v1`, server type vLLM (generic OpenAI-compatible only if vLLM is absent), served name `qwen3.6-35b-a3b`, no API key. A bridge-network HA container would resolve loopback to itself and needs a different networking design.
- **Server startup takes minutes:** recorded vLLM start was ~226 s. Inspect `docker logs ha-llm`; do not repeatedly restart it or load the deep model concurrently.
- **Fast/deep conflict after reboot:** `ha-llm` still has `unless-stopped`; safe switching/restart coordination is pending. Check resident processes before starting any 80 GB+ model.

## Phone/network

- Reachable from another tailnet peer but not phone: verify Android work/personal profile alignment first. Then check split-tunnel excluded apps, other VPNs, exit node and tailnet policy. Reconnect Tailscale if appropriate; no MagicDNS requirement.
- The build experienced a temporary TCP interruption while Tailscale ping/relay connectivity still worked. A ping is not proof that application TCP is healthy. Test HA locally and from the intended phone profile.
- Chrome mic blocked on plain HTTP: native Companion app or HTTPS; see [phone](phone.md).
- Wake-word toggle disabled despite “default assistant” selected: likely different app profiles; ensure the personal app is both the configured default and the one whose settings you opened.

## Speech / Home Assistant logs

- Confirm Wyoming services at `127.0.0.1:10300` (STT) and `127.0.0.1:10200` (TTS). The TTS bridge listens internally on 10300; mapping 10200→10300 is deliberate.
- Kokoro bridge must use `http://kokoro:8880/v1` on the shared `voice` Docker network, not container loopback.
- Existing Home Assistant Bluetooth scanner/permission errors predated knowledge setup. These are log noise for this voice path, not evidence the LLM/STT failed. No Bluetooth privilege change was made. If Bluetooth devices are required later, configure the supported HA Bluetooth/DBus permissions deliberately rather than granting broad privilege merely to silence logs.
- Stock ARM64/CUDA speech images are not interchangeable. Use the observed digests and compare upstream GB10 recipes when rebuilding; do not assume an x86 image works.

## Knowledge tools

- Archive absent: Kiwix container can say “running” while its wrapper waits for the verified ZIM. Check `~/kiwix/download.log` and final filename; port 8090 may not answer yet.
- Download interrupted/rebooted: rerun `~/kiwix/download-wikipedia.sh`; `wget --continue` resumes. The detached downloader is not itself a boot service. Checksum failure intentionally prevents final rename.
- SearXNG engine CAPTCHA: one upstream failed while other engines returned results; this is not necessarily a total outage. Check JSON output and engine errors, not just HTTP status.
- SearXNG HTTP 200 with `results: []` is not a live lookup. Private Web Search must say there is no live evidence. Unresponsive engines, timeouts, HTTP errors and malformed bodies are unavailable, not empty matches. Offline Wikipedia Search is only an offer; the web script does not call it.
- Assistant invents a lookup: expose all three scripts, retain Device control tool provider, append the knowledge instructions to the **system prompt**, start a new conversation, and inspect real tool results. Pasting instructions into Assist chat is not persistent configuration.
- Validate configuration before a manual HA restart: `docker exec homeassistant python -m homeassistant --script check_config --config /config`. Back up privately first; never put that backup in this repo.


## The assistant says it cannot search, or adds a shopping-list item instead

The valid web-search tool name is `script__private_web_search`. Aliases such as
“Private Web Search” are not callable. Use the prompt in
`configs/homeassistant/agent-prompt.txt`, which also forbids unasked list
changes. Weather and device state should use `homeassistant__GetLiveContext`
once those entities are exposed.

## Recipes or numbered lists sound wrong (“number one” then a click)

Spoken output should pass through `speak_normalize` on both TTS ports. If a
voice is suddenly reading raw `1.` or `225g`, check that the bind mounts on
`wyoming-tts` and `wyoming-qwen3-tts` are still present after a recreate
(`docker inspect` → Binds) and that the unit tests still pass. Roll back only
the affected container; see `services/wyoming-tts-bridge/ROLLBACK.md`.
