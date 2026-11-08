# Ask Claude integration handoff — 8 November 2026, GMT

## Completed
- Connected as `halead` to the GX10 through Tailscale nc ProxyCommand. Plain SSH failed.
- Confirmed Home Assistant uses host networking, so bridge binds only `127.0.0.1:8765`.
- Confirmed an active `claude` process belongs to `sechoia`. `/home/sechoia` is mode 750 and cannot be traversed by halead. Therefore installation path and authentication status are not independently verified. No Claude credential files were read, copied, or extracted; no API key was used.
- Installed `/config/packages/ask_claude.yaml`, defining `rest_command.ask_claude` (120-second timeout) and `script.ask_claude`, alias **Ask Claude**, with a required `question` field and returned answer mapping.
- Appended `ask_claude_bridge_token` to `/config/secrets.yaml` (mode 600). This is a newly generated bridge-only shared secret, not Claude authentication.
- Private HA copy of that new bridge token: `/config/claude_bridge/token` (mode 600).
- Backup made before configuration changes: `/config/backups/before-ask-claude-20261108-173155.tgz` (mode 600).
- Configuration check passed; HA restarted; HA HTTP returned 200 and recent logs showed no Ask Claude or configuration setup errors.

## Bridge design
Prepared setup files on GX10 at `/var/tmp/gx10-ask-claude-setup/`: `bridge.py`, `install.sh`, `test_live.py`, plus `token` owned by sechoia with mode 600. The code/setup files contain no authentication credentials. Installation copies the bridge/token to `~/.local/share/ask-claude/` as sechoia and creates `~/.config/systemd/user/ask-claude.service`.

The official CLI runs as the signed-in user with `claude -p --output-format text`, an empty built-in tool list, MCP disabled, no permission bypass, no hooks, no project/user settings, no persisted conversations, and a speech-specific system prompt. Questions go through stdin, not shell interpolation. It strips inherited API/OAuth token environment variables and relies only on the user's normal CLI login. Each invocation is stateless. It uses the CLI's default model, not a hard-coded model.

POST `/ask` requires `X-Bridge-Token`. Questions are limited to 4000 characters, one request runs at a time, and the CLI process group is killed after 90 seconds. Failures return honest unavailable/timeout messages. Questions/answers/headers are not logged by the bridge. GET `/health` is a non-authenticated liveness probe only, not proof that Claude authentication works.

## Exact user action
Run these in the GX10 SSH session **as sechoia**, not on the workstation:

```bash
bash /var/tmp/gx10-ask-claude-setup/install.sh
sudo loginctl enable-linger sechoia
```

The first command finds the installed CLI, checks version and authentication using official `claude auth status --text`, installs/starts the user service, and makes one live speech-answer test, printing the answer and measured bridge latency. It stops rather than copying credentials or starting a login flow if authentication is unavailable. The second command enables the user service after reboot without an interactive login. Current linger state was `no`.

Then expose **Ask Claude** under **Settings > Voice assistants > Expose**. If the existing local agent instructions restrict tools to the three knowledge scripts, append:

> When I explicitly say “ask Claude”, call the Ask Claude script with my question and read its returned answer back. Do not send ordinary local questions, private home state or conversation history to Claude automatically. If Claude is unavailable, say so and keep local functions available.

Voice test: “Hey Jarvis, ask Claude why a local AI and cloud AI complement each other.” Send back the install test answer/latency if verification is needed.

## Verification status
PASS: configuration validation, HA restart/HTTP health, loopback networking choice, account isolation, shared-secret file permissions, installer shell syntax.
PASS (mock CLI only): authenticated request, unauthorized denial, malformed/oversized body rejection, stdin/no flag injection, no built-in/MCP tools, exclusion of inherited API/token environment auth, busy response, graceful CLI failure.
PENDING: real CLI flags/authentication under sechoia, first live response, measured bridge latency, Assist exposure, end-to-end spoken response. No real Claude latency has been measured and no claim of full working integration should be made yet. The local assistant is still up.

## Proposed documentation text (not pushed)
### Optional cloud reasoning: Ask Claude
Local control and knowledge remain available without internet. For explicit “ask Claude” requests, an authenticated loopback bridge invokes the official Claude Code CLI under the user's signed-in account, using their Claude subscription rather than an API key. Answers are short and speech-friendly; Claude has no file, shell, web or home-control tools. This path requires internet and is subject to the subscription's availability and usage limits. Expose the Ask Claude script to Assist after installing the user service. Bridge timeout is 90 seconds and HA timeout is 120 seconds. Live latency and full voice verification are pending the first user-run startup test. Never publish the bridge token, HA secrets, CLI credentials or private machine details.
