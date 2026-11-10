#!/usr/bin/env bash
# Repeatable GX10 production-config backup. Read-only toward running services.
# Paths come from the environment or $HOME defaults (see .env.example).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/load-env.sh" ]]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  # shellcheck source=load-env.sh
  source "$SCRIPT_DIR/load-env.sh"
fi

BACKUP_ROOT="${BACKUP_ROOT:-${HOME}/gx10-backups}"
GX10_USER="${GX10_USER:-$(id -un)}"
HA_CONFIG_DIR="${HA_CONFIG_DIR:-${HOME}/homeassistant}"
SEARXNG_CONFIG_DIR="${SEARXNG_CONFIG_DIR:-${HOME}/searxng/config}"
KIWIX_DIR="${KIWIX_DIR:-${HOME}/kiwix}"
KEEP=14
TS="$(date -u +%Y%m%d-%H%M%S)"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/gx10-backup.XXXXXX")"
ARCHIVE_NAME="gx10-production-configs-${TS}.tar.gz"
ARCHIVE_PATH="${BACKUP_ROOT}/${ARCHIVE_NAME}"
SHA_PATH="${ARCHIVE_PATH}.sha256"
MANIFEST="${STAGE}/metadata/MANIFEST.txt"
FILELIST="${STAGE}/metadata/file-list.txt"
SKIPLIST="${STAGE}/metadata/skipped.txt"
DOCKER_META="${STAGE}/metadata/docker"

cleanup() { rm -rf "${STAGE}"; }
trap cleanup EXIT

mkdir -p "${BACKUP_ROOT}" "${STAGE}/files" "${STAGE}/metadata" "${DOCKER_META}"
chmod 0700 "${BACKUP_ROOT}" "${STAGE}" "${STAGE}/files" "${STAGE}/metadata" "${DOCKER_META}"

umask 077
: > "${FILELIST}"
: > "${SKIPLIST}"
{
  echo "created_utc=${TS}"
  echo "host=$(hostname)"
  echo "user=$(id -un)"
  echo "note=Configuration-only. No model weights, ZIM, caches, DBs, container images."
  echo "note=Secrets may be present; keep archives 0600 and directory 0700. Never commit archives or SHA files."
} > "${MANIFEST}"

# Production containers for inspect metadata only (no exec that changes state).
PROD_CONTAINERS=(ha-llm homeassistant kokoro wyoming-stt wyoming-tts wyoming-qwen3-tts searxng kiwix)
for c in "${PROD_CONTAINERS[@]}"; do
  if docker inspect "$c" >"${DOCKER_META}/${c}.inspect.json" 2>/dev/null; then
    # Drop Env from inspect to avoid leaking secrets into the archive if present.
    python3 - "${DOCKER_META}/${c}.inspect.json" <<'PY' || true
import json,sys
p=sys.argv[1]
with open(p) as f: data=json.load(f)
def scrub(obj):
  if isinstance(obj, dict):
    out={}
    for k,v in obj.items():
      if k in ("Env","env","Environment","Password","password","Token","token","Secret","secret","AuthConfig"):
        out[k]="[REDACTED]"
      else:
        out[k]=scrub(v)
    return out
  if isinstance(obj, list):
    return [scrub(x) for x in obj]
  return obj
with open(p,"w") as f: json.dump(scrub(data), f, indent=2)
PY
    echo "docker_inspect=${c}:ok" >>"${MANIFEST}"
  else
    echo "docker_inspect=${c}:missing" >>"${MANIFEST}"
    echo "docker inspect missing: ${c}" >>"${SKIPLIST}"
  fi
done
docker ps -a --format '{{.Names}} {{.Status}} {{.Image}}' >"${DOCKER_META}/ps-a.txt" || true
docker info --format '{{.ServerVersion}} {{.Driver}} {{.LoggingDriver}}' >"${DOCKER_META}/info-summary.txt" 2>/dev/null || echo "docker info unavailable" >"${DOCKER_META}/info-summary.txt"

copy_tree() {
  local src="$1" dest_rel="$2" mode="$3"
  if [[ ! -e "$src" ]]; then
    echo "missing:${src}" >>"${SKIPLIST}"
    return 0
  fi
  if [[ ! -r "$src" ]] && [[ ! -d "$src" ]]; then
    echo "unreadable:${src}" >>"${SKIPLIST}"
    return 0
  fi
  # Directory readability check
  if [[ -d "$src" ]] && ! ls "$src" >/dev/null 2>&1; then
    echo "unreadable_dir:${src}" >>"${SKIPLIST}"
    return 0
  fi
  local target="${STAGE}/files/${dest_rel}"
  mkdir -p "$(dirname "$target")"
  if [[ -f "$src" || -L "$src" ]]; then
    cp -a --no-preserve=ownership "$src" "$target" 2>>"${SKIPLIST}" || { echo "copy_fail:${src}" >>"${SKIPLIST}"; return 0; }
    echo "${dest_rel}" >>"${FILELIST}"
    return 0
  fi
  mkdir -p "$target"
  # Find config-ish files; exclude large/ephemeral patterns.
  # mode=all: copy most files under exclusions
  # mode=deploy: only compose/Dockerfile/sh/env/wy.py
  while IFS= read -r -d '' f; do
    local rel="${f#"${src}"/}"
    local base
    base="$(basename "$f")"
    # Skip excluded directory segments
    case "/$rel/" in
      */.git/*|*/__pycache__/*|*/.cache/*|*/cache/*|*/caches/*|*/node_modules/*|*/.venv/*|*/venv/*|*/deps/*|*/media/*|*/tts/*|*/work/*|*/data/*|*/models/*|*/hf/*|*/vllm-cache/*)
        continue ;;
    esac
    # Skip backups dir content inside HA config (large tarballs) but keep packages
    case "/$rel/" in
      */backups/*) continue ;;
    esac
    case "$base" in
      *.db|*.db-*|*.sqlite|*.sqlite3|*.log|*.log.*|*.zim|*.zim.*|*.gguf|*.safetensors|*.onnx|*.bin|*.pt|*.pth|*.ckpt|*.tar|*.tar.gz|*.tgz|*.wav|*.mp3|*.mp4|*.pyc|*.pid|*.lock|.ha_run.lock)
        continue ;;
    esac
    # Skip tmp storage junk
    if [[ "$rel" == .storage/tmp* ]]; then continue; fi
    # Size cap 16MiB
    local sz
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    if [[ "$sz" -gt $((16*1024*1024)) ]]; then
      echo "too_large:${src}/${rel}:${sz}" >>"${SKIPLIST}"
      continue
    fi
    if [[ "$mode" == "deploy" ]]; then
      local keep=0
      [[ "$base" == "wy.py" ]] && keep=1
      [[ "$base" == ".env" || "$base" == *.env ]] && keep=1
      [[ "$base" == Dockerfile* ]] && keep=1
      [[ "$base" == *.sh ]] && keep=1
      [[ "$base" == *compose*.yml || "$base" == *compose*.yaml || "$base" == docker-compose.yml || "$base" == docker-compose.yaml ]] && keep=1
      [[ "$keep" -eq 0 ]] && continue
    fi
    local out="${target}/${rel}"
    mkdir -p "$(dirname "$out")"
    if cp -a --no-preserve=ownership "$f" "$out" 2>>"${SKIPLIST}"; then
      echo "${dest_rel}/${rel}" >>"${FILELIST}"
    else
      echo "copy_fail:${src}/${rel}" >>"${SKIPLIST}"
    fi
  done < <(find "$src" -type f -o -type l 2>/dev/null | tr '\n' '\0')
}

# Config trees under $HOME. The archive prefix is home/${GX10_USER}/...
copy_tree "${HOME}/ha-llm" "home/${GX10_USER}/ha-llm" all
copy_tree "${HA_CONFIG_DIR}" "home/${GX10_USER}/homeassistant" all
copy_tree "${SEARXNG_CONFIG_DIR}" "home/${GX10_USER}/searxng/config" all
copy_tree "${HOME}/voice" "home/${GX10_USER}/voice" deploy
copy_tree "${HOME}/homeassistant-voice-recipes" "home/${GX10_USER}/homeassistant-voice-recipes" deploy
# Kiwix: scripts only, not the ZIM
if [[ -d "${KIWIX_DIR}" ]]; then
  mkdir -p "${STAGE}/files/home/${GX10_USER}/kiwix"
  for f in "${KIWIX_DIR}/"*; do
    [[ -e "$f" ]] || continue
    base="$(basename "$f")"
    case "$base" in
      *.zim|*.zim.*) echo "excluded_zim:${f}" >>"${SKIPLIST}"; continue ;;
      *.log|*.pid) continue ;;
    esac
    if [[ -f "$f" ]]; then
      sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
      if [[ "$sz" -gt $((16*1024*1024)) ]]; then
        echo "too_large:${f}" >>"${SKIPLIST}"; continue
      fi
      cp -a --no-preserve=ownership "$f" "${STAGE}/files/home/${GX10_USER}/kiwix/${base}"
      echo "home/${GX10_USER}/kiwix/${base}" >>"${FILELIST}"
    fi
  done
fi

# Optional Ask Claude CLI files from another account, if ASK_CLAUDE_HOME is set
# and the paths are readable. /etc/docker/daemon.json is included when readable.
OPTIONAL_PATHS=()
if [[ -n "${ASK_CLAUDE_HOME:-}" ]]; then
  OPTIONAL_PATHS+=(
    "${ASK_CLAUDE_HOME}/.config/systemd/user/ask-claude.service"
    "${ASK_CLAUDE_HOME}/.local/share/ask-claude/bridge.py"
    "${ASK_CLAUDE_HOME}/.local/share/ask-claude/token"
    "${ASK_CLAUDE_HOME}/.local/share/ask-claude/claude-path"
  )
fi
OPTIONAL_PATHS+=(/etc/docker/daemon.json)
for p in "${OPTIONAL_PATHS[@]}"; do
  if [[ -r "$p" ]]; then
    rel="${p#/}"
    mkdir -p "${STAGE}/files/$(dirname "$rel")"
    cp -a --no-preserve=ownership "$p" "${STAGE}/files/${rel}"
    echo "$rel" >>"${FILELIST}"
  else
    echo "unreadable_optional:${p}" >>"${SKIPLIST}"
  fi
done

# Current-user systemd user units if any
if [[ -d "${HOME}/.config/systemd/user" ]]; then
  copy_tree "${HOME}/.config/systemd/user" "home/${GX10_USER}/.config/systemd/user" all
fi

# Build archive from stage
(
  cd "${STAGE}"
  tar -czf "${ARCHIVE_PATH}" metadata files
)
chmod 0600 "${ARCHIVE_PATH}"

# Hash
HASH="$(sha256sum "${ARCHIVE_PATH}" | awk '{print $1}')"
printf '%s  %s\n' "${HASH}" "${ARCHIVE_NAME}" >"${SHA_PATH}"
chmod 0600 "${SHA_PATH}"

# Verify archive lists and hash matches
tar -tzf "${ARCHIVE_PATH}" >/dev/null
CHECK="$(sha256sum "${ARCHIVE_PATH}" | awk '{print $1}')"
if [[ "${CHECK}" != "${HASH}" ]]; then
  echo "ERROR: hash mismatch after write" >&2
  exit 1
fi
# Re-read SHA file
READ_HASH="$(awk '{print $1}' "${SHA_PATH}")"
if [[ "${READ_HASH}" != "${HASH}" ]]; then
  echo "ERROR: sha256 file mismatch" >&2
  exit 1
fi

# Prune: keep newest 14 archives matching gx10-production-configs-*.tar.gz
mapfile -t OLD < <(ls -1t "${BACKUP_ROOT}"/gx10-production-configs-*.tar.gz 2>/dev/null || true)
if ((${#OLD[@]} > KEEP)); then
  for old in "${OLD[@]:${KEEP}}"; do
    rm -f -- "$old" "${old}.sha256"
  done
fi

BYTES="$(stat -c%s "${ARCHIVE_PATH}")"
echo "ARCHIVE=${ARCHIVE_PATH}"
echo "SHA256=${HASH}"
echo "BYTES=${BYTES}"
echo "FILES=$(wc -l <"${FILELIST}" | tr -d ' ')"
echo "SKIPPED=$(wc -l <"${SKIPLIST}" | tr -d ' ')"
