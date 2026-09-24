#!/usr/bin/env bash
# sandbox.sh <workdir> <homedir> -- cmd...   Run cmd with the NAS hidden, / read-only,
# only <workdir>, <homedir>, a private /tmp and the real OAuth credentials file writable.
W=$1; H=$2; shift 3
mkdir -p "$H/.claude"
[ -f "$H/.claude.json" ] || cp "$HOME/.claude.json" "$H/.claude.json"
touch "$H/.claude/.credentials.json"
exec bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs /dev/shm \
  --tmpfs /media/nas01 \
  --bind "$W" "$W" --bind "$H" "$H" \
  --bind "$HOME/.claude/.credentials.json" "$H/.claude/.credentials.json" \
  --setenv HOME "$H" --setenv DISABLE_AUTOUPDATER 1 --setenv DO_NOT_TRACK 1 \
  --chdir "$W" --die-with-parent -- "$@"
