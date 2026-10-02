#!/usr/bin/env bash
# Baseline template per task: before-snapshot as a fresh single-commit git repo.
set -euo pipefail
B=$(cd "$(dirname "$0")" && pwd)
for t in $(awk '{print $1}' $B/final_tasks.txt); do
  d=$B/tpl/$t/A; rm -rf $d; mkdir -p $(dirname $d); cp -a $B/snap/$t-before $d
  (cd $d && git init -q && git add -A && git -c user.email=bench@local -c user.name=bench commit -qm "base" && echo "$t A: $(git ls-files | wc -l) files")
done
