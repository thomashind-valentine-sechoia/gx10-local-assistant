# Documentation validation

Snapshot: 8 November 2026 (Europe/London, GMT).

- PASS: local files cover architecture, hardware, models, installation, phone setup, knowledge, measurements, security, troubleshooting and roadmap.
- PASS: Docker Compose configuration parsed successfully on the destination workstation; no services deployed there.
- PASS: both shell scripts passed `bash -n`; all Python scripts passed AST syntax checks.
- PASS: relative Markdown links and image-lock JSON checked.
- PASS: content scan found no real tailnet addresses/names, personal usernames, home-directory paths, email addresses, private-key blocks or common credential prefixes.
- PASS: staged-content grep reviewed for tailnet address/name patterns and the words secret, token and key. Matches were placeholders, configuration option names, benchmark token counts, code generating a new runtime secret, or security guidance; no credential values were copied.
- PASS: local-only Git repository, no remote; no GX10 service/settings changes.
- LIMITED: full original transcript/tool logs could not be retrieved; supplied conversation plus live artifacts used.
- PENDING: clean-machine installation, full encyclopedia verification and real Assist tool execution, deep-model measurements, end-to-end voice/device/offline acceptance.

The runtime SearXNG secret remains outside this repository. Commit author identity follows the existing local Git configuration as requested; review Git metadata separately before public release. No licence has been chosen.
