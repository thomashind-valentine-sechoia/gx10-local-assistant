# Backups and updating the checkout

These scripts are for the GX10 host. They are not an unattended installer. Paths are taken from the environment or `$HOME`; set variables in `.env` (see `.env.example`) if you do not use the defaults.

## `scripts/backup.sh`

A read-only (toward running services) configuration archive. It copies
Home Assistant, SearXNG, launcher and related config trees, plus redacted
`docker inspect` metadata, into a timestamped `.tar.gz` under
`${BACKUP_ROOT:-$HOME/gx10-backups}/`. Model weights, ZIM archives, caches, databases and
audio are skipped. The newest 14 archives are kept.

The archive layout uses `home/<gx10-user>/...`, where `<gx10-user>` is
`${GX10_USER:-$(id -un)}` on the machine you run the script on.

If you use the optional Ask Claude CLI bridge from another account, set
`ASK_CLAUDE_HOME` to that account's home directory so the script can copy
the unit and bridge files when they are readable. If the path is unset, that
step is skipped.

Archives **may contain secrets** (for example `secrets.yaml` or HA
`.storage` if those paths are readable). The script sets mode `0600` on
the tarball and `0700` on the backup directory. Never commit an archive,
its `.sha256` file, or a copy of `secrets.yaml`.

## `scripts/pull-latest.sh`

Updates a git checkout of this repository (`--ff` for a fast-forward pull)
and prints the hash-gated steps to copy packages or TTS overlays onto a
running machine. It does **not** overwrite live Home Assistant, secrets,
or `.storage`.

```sh
./scripts/pull-latest.sh        # fetch and show status
./scripts/pull-latest.sh --ff   # fast-forward the current branch
```

Package updates still follow the same rules as [knowledge.md](knowledge.md):
confirm the live file hash, copy the live file outside `packages/`, copy
the artifact, `check_config`, then `script.reload` only.
