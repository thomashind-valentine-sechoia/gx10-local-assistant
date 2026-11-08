# Android phone access, wake word and dashboard

## Connect over Tailscale

1. Connect the GX10 and phone to the same authorised tailnet; ensure access policy permits the phone to the GX10 on TCP 8123. Do not open router ports.
2. In the phone browser, enter `http://<GX10_TAILSCALE_IP>:8123` with the explicit `http://` prefix. MagicDNS is optional, not required. Use your own address; no real tailnet identifiers are included in this repository.
3. Install the official Home Assistant Companion app and enter the same server URL; sign in with the account you created locally. Grant the microphone permission when requested.

### The work/personal profile gotcha (actual cause here)

Tailscale originally ran in the Android **work profile**, while the browser was personal. Both the GX10 and a second server appeared unreachable from personal Chrome. Work Chrome reached them. Later the user moved the setup to the **personal profile**, resolving default-assistant/wake-word issues too.

Keep **Tailscale, Home Assistant and the browser used for setup in the same Android profile**. A VPN in one profile does not imply the other profile is routed. A work-profile Home Assistant app may not be selectable/recognised as the personal default assistant. Check the briefcase badge and policy restrictions rather than assuming server firewall failure.

## Wake word

1. Android Settings → Apps → Default apps → Digital assistant app: choose the **same personal-profile Home Assistant app**.
2. Home Assistant Settings → Companion app → Assist: choose the intended local assistant, enable supported wake-word detection and select a supported word (the working setup used “Hey Jarvis”). Exact labels/options depend on app version and device policy.
3. Allow microphone access; check battery/background restrictions if detection stops with the screen off. Always-on listening can increase battery consumption. App/version and screen-off endurance were not recorded here.
4. If the switch is grey: check the default assistant **and profile match** first, then permissions. Selecting a different-profile app can leave the current app believing no default is set.

Wake-word detection happens on the phone; the configured local Assist pipeline handles subsequent audio. No accuracy or battery benchmark was performed.

## Why browser microphone failed

Chrome generally restricts microphone access to secure contexts. A remote plain-HTTP HA page can display Assist text but refuse the microphone. Use the native Companion app or correctly configured HTTPS; do not weaken browser security flags.

## Put Assist on a dashboard

Use an editable user dashboard (Settings → Dashboards → Add dashboard → new dashboard from scratch, if needed). Add a Button card, choose a microphone icon/name, and configure Tap action → Assist → the local pipeline → Start listening. An entity is not required when using the YAML form:

```yaml
type: button
name: Assist
icon: mdi:microphone
tap_action:
  action: assist
  start_listening: true
```

Without a pipeline identifier this uses the preferred pipeline. Star the local assistant as preferred first. Set the dashboard as your default if desired. Dashboard menu placement varies with Home Assistant frontend version; look for Assist in the overflow menu if no top-level icon appears. Actual final card configuration was not captured.
