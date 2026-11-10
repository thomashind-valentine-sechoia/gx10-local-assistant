# Contributing

The purpose of this repository is that a new GX10 owner can clone it, use the Dockerfiles and Compose file, and follow the README on their own machine. Commits must not introduce host-specific or personal details.

## What must not be committed

- Absolute home paths such as `/home/<username>` (use `$HOME`, `~`, or placeholders like `<gx10-user>`)
- Local usernames (including the known ones this hook rejects by name)
- Email addresses, except GitHub `noreply` identities (`*@users.noreply.github.com`, `noreply@github.com`)
- Passwords, API keys, tokens, private keys
- IP addresses and hostnames, including Tailscale CGNAT (`100.64.0.0/10`) and `*.ts.net`
- `secrets.yaml`, `.storage`, model weights, ZIM archives, logs, audio, and voice-clone clips (already gitignored)

Use environment variables and `.env` (see `.env.example`) for anything that varies between machines. Never commit `.env`.

## Git identity

If you commit from a clone of this project, set a GitHub noreply author on that checkout so a work or personal inbox is not written into history:

```sh
git config --local user.name "your-github-handle"
git config --local user.email "ID+your-github-handle@users.noreply.github.com"
```

GitHub shows the noreply address on [the email settings page](https://github.com/settings/emails).

## Privacy hook

`scripts/check-privacy.sh` scans the tree and exits non-zero if it finds the patterns above. The same script runs as a pre-commit hook.

This checkout can use either:

1. The bundled Git hook (no extra packages):

   ```sh
   git config --local core.hooksPath .githooks
   ```

2. Or the [pre-commit](https://pre-commit.com/) framework, which also runs [gitleaks](https://github.com/gitleaks/gitleaks) when that hook is installed:

   ```sh
   pip install pre-commit
   pre-commit install
   ```

`.pre-commit-config.yaml` and `.gitleaks.toml` live at the repository root. If `gitleaks` is on your `PATH`, the bundled hook runs `gitleaks protect --staged` as well.

Run the check yourself before you push:

```sh
./scripts/check-privacy.sh
gitleaks dir --no-banner --config .gitleaks.toml
gitleaks detect --no-banner --config .gitleaks.toml --log-opts='--all'
```

## Tests

```sh
python3 -m unittest tests.test_private_web_search
python3 -m unittest discover -s services/wyoming-qwen3-tts -p 'test_*.py'
```

## Pull requests

Open a PR against `main`. Do not include live host configuration, personal session journals, or secrets. Keep changes reviewable; do not rewrite history on `main`.
