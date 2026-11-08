# shellcheck shell=bash
# Shared helpers for bin/* scripts — source this file, don't execute it.
# Written for bash 3.2 (macOS default): no mapfile, no ${var,,}, no empty-array expansion.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC2034  # used by the scripts that source this file
INBOX="$REPO_ROOT/inbox"
# shellcheck disable=SC2034
LIBRARY="$REPO_ROOT/library"
# shellcheck disable=SC2034
PYLIB="$REPO_ROOT/bin/lib"

die() { echo "error: $*" >&2; exit 1; }
log() { echo "==> $*"; }

# show_help — print the calling script's header comment (everything after the
# shebang up to the first non-comment line), so --help never drifts from the docs.
show_help() {
  awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

# set_input <arg> — accept exactly one positional argument (stored in INPUT).
set_input() {
  if [[ -n "${INPUT:-}" ]]; then
    die "only one input allowed (got '$INPUT' and '$1').
       Source context like '— speaker: ...' goes in a <file>.meta.json sidecar,
       or after the input in the /wisdom-ingest call — not here."
  fi
  INPUT="$1"
}

# need <command> [package] — fail early with an install hint instead of a cryptic error later.
need() {
  command -v "$1" >/dev/null 2>&1 \
    || die "'$1' not found. Install it (macOS: brew install ${2:-$1}; Debian/Ubuntu: apt install ${2:-$1})"
}

# load_env — make MISTRAL_API_KEY available: environment first, then ~/.vibe/.env, then ./.env (gitignored).
load_env() {
  local f
  for f in "$HOME/.vibe/.env" "$REPO_ROOT/.env"; do
    [[ -n "${MISTRAL_API_KEY:-}" ]] && return 0
    # shellcheck disable=SC1090  # the user's own .env file, path known only at runtime
    if [[ -f "$f" ]]; then set -a; source "$f"; set +a; fi
  done
  return 0
}

# sanitize <string> — filesystem-safe ASCII base name, max 80 chars.
# Long names keep their start AND end (where "Part 2" or a video id usually is) plus a
# checksum of the full name, so two different inputs can never map to the same file.
sanitize() {
  local s sum
  s="$(printf '%s' "$1" | LC_ALL=C sed -e 's/[^A-Za-z0-9._-]/_/g' -e 's/__*/_/g' -e 's/^[_.]*//' -e 's/_*$//')"
  if [[ ${#s} -gt 80 ]]; then
    sum="$(printf '%s' "$1" | cksum | cut -d' ' -f1)"
    s="${s:0:44}_${s: -24}_${sum}"
  fi
  printf '%s' "$s"
}

# sidecar_for <path> — print "<dir>/<name>.meta.json" if it exists next to the input file.
sidecar_for() {
  local f="${1%.*}.meta.json"
  [[ -f "$f" ]] && printf '%s' "$f"
  return 0
}
