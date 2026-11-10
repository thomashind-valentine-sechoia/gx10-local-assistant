# Documentation validation

The checks below are what a maintainer should re-run before publishing or merging to `main`.

- PASS expected: relative Markdown links resolve; `docker compose config` parses; `bash -n` on the shell scripts; Python files parse.
- PASS expected: `./scripts/check-privacy.sh` and `gitleaks dir --config .gitleaks.toml` are clean on the current tree.
- PASS expected: no real tailnet addresses, home-directory paths, non-noreply emails, private-key blocks, or credential values in tracked files.
- PENDING on a new machine: a clean-machine install from the README, encyclopedia verification, Assist tool execution, and end-to-end voice acceptance.

History on `main` may still contain older documentation that predates these rules. New commits must pass the hook. See [CONTRIBUTING.md](../CONTRIBUTING.md).

The runtime SearXNG secret and Home Assistant `secrets.yaml` remain outside this repository.

## Speech normaliser and search-package tests

From the repository root, with PyYAML and Jinja2 available for the search tests:

```sh
python3 -m unittest tests.test_private_web_search
python3 -m unittest discover -s services/wyoming-qwen3-tts -p 'test_*.py'
```

The speak_normalize suite is 23 tests, including a Victoria sponge recipe.
