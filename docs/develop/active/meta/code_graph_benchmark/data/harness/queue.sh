#!/usr/bin/env bash
# queue.sh <jobfile> <parallel>  — each line "task arm trial"; skips runs that already have a score.
B=$(cd "$(dirname "$0")" && pwd)
grep -v '^#' "$1" | while read t a k; do [ -f $B/runs/$t-$a-$k/score.json ] || echo "$t $a $k"; done \
  | xargs -P "$2" -L 1 bash -c 'bash '"$B"'/run_one.sh $0 $1 $2 > '"$B"'/runs/log-$0-$1-$2.txt 2>&1; echo "$(date +%T) done $0 $1 $2"'
