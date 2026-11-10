#!/usr/bin/env bash
# Fail if the working tree (or listed files) contains host/personal details
# that must not be committed. Used by the pre-commit hook and CI-style checks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Files to scan: staged files when in a hook, otherwise tracked + unstaged + untracked
# (excluding ignored paths).
collect_files() {
  if [[ "${1:-}" == "--staged" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git diff --cached --name-only -z --diff-filter=ACMR
    return
  fi
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files -z --cached --others --exclude-standard
  else
    find . -type f -not -path './.git/*' -print0
  fi
}

# Allow GitHub noreply identities only.
# Disallow other emails, /home/<name> (but not /home/<placeholder>), CGNAT
# Tailscale IPs, MagicDNS, and known local usernames as standalone words.
python3 - "$REPO_ROOT" "${1:-}" <<'PY'
import os, re, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
mode = sys.argv[2] if len(sys.argv) > 2 else ""
os.chdir(root)

def nul_list(args):
    out = subprocess.check_output(args)
    return [p.decode() for p in out.split(b"\0") if p]

if mode == "--staged":
    files = nul_list(["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"])
else:
    files = nul_list(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"])

# Skip this checker itself and hook/docs that mention the forbidden strings as examples
# in a clearly meta way? Better: the checker and CONTRIBUTING must mention them.
# Allowlist paths where the banned usernames may appear as *examples of what to reject*.
META = {
    "scripts/check-privacy.sh",
    ".gitleaks.toml",
    ".pre-commit-config.yaml",
    "CONTRIBUTING.md",
}

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
EMAIL_OK = re.compile(r"(?i)(?:^noreply@github\.com$|@users\.noreply\.github\.com$)" )

HOME_PATH = re.compile(r"/home/([A-Za-z0-9._-]+)")
# placeholders: <gx10-user>, <workstation-user>, USER, you
HOME_OK = re.compile(r"^(?:<[A-Za-z0-9._-]+>|[A-Z][A-Z0-9_]*)$")

# 100.64.0.0/10
TS_IP = re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
MAGICDNS = re.compile(r"(?i)\b[\w.-]+\.ts\.net\b")

# Standalone local usernames, not inside thomashind-valentine-sechoia or SECHOIA LTD
USERNAMES = [
    ("halead", re.compile(r"(?i)(?<![A-Za-z0-9_-])halead(?![A-Za-z0-9_-])")),
    ("sechoia", re.compile(r"(?<![A-Za-z0-9_-])sechoia(?![A-Za-z0-9_-])")),  # case-sensitive: allow SECHOIA
    ("thind", re.compile(r"(?<![A-Za-z0-9_-])thind(?![A-Za-z0-9_-])")),
]

TOKENISH = [
    ("private-key-block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("github-pat", re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("openai-sk", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("hf-token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("tailscale-key", re.compile(r"\btskey-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("assigned-secret", re.compile(r"(?i)(?:api[_-]?key|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]

hits = []
for rel in files:
    if not rel or rel.endswith("/"):
        continue
    path = root / rel
    if not path.is_file():
        continue
    try:
        data = path.read_bytes()
    except OSError:
        continue
    if b"\0" in data:
        continue
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", "replace")

    in_meta = rel in META
    for i, line in enumerate(text.splitlines(), 1):
        for m in EMAIL.finditer(line):
            addr = m.group(0)
            if EMAIL_OK.search(addr):
                continue
            hits.append((rel, i, "email", addr.split("@")[0][:1] + "***@" + addr.split("@", 1)[1]))
        if not in_meta:
            for m in HOME_PATH.finditer(line):
                name = m.group(1)
                if HOME_OK.match(name) or name.startswith("<"):
                    continue
                hits.append((rel, i, "home-path", f"/home/{name}"))
            for m in TS_IP.finditer(line):
                hits.append((rel, i, "tailscale-ip", m.group(0)))
            for m in MAGICDNS.finditer(line):
                hits.append((rel, i, "magicdns", "*.ts.net"))
            for label, pat in USERNAMES:
                if pat.search(line):
                    hits.append((rel, i, "username", label))
        for label, pat in TOKENISH:
            if pat.search(line):
                hits.append((rel, i, label, "[redacted]"))

if hits:
    print("PRIVACY CHECK FAILED: host or personal details must not be committed:", file=sys.stderr)
    for rel, i, kind, snippet in hits:
        print(f"  {rel}:{i}: {kind}: {snippet}", file=sys.stderr)
    sys.exit(1)
print(f"privacy check passed ({len(files)} files)")
PY
