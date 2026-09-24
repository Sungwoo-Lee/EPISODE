#!/usr/bin/env bash
# queue2.sh <jobfile> <parallel> — like queue.sh, but a G job waits until its Graft template is committed.
B=$(cd "$(dirname "$0")" && pwd); P=$2
ready() { [ "$2" != G ] || git -C $B/tpl/$1/G log --oneline 2>/dev/null | grep -q "graft wiring"; }
mapfile -t JOBS < <(grep -v '^#' "$1")
declare -A started
while :; do
  left=0
  for j in "${JOBS[@]}"; do set -- $j; key="$1-$2-$3"
    [ -f $B/runs/$key/score.json ] && continue
    [ -d $B/runs/$key ] && [ -z "${started[$key]:-}" ] && { started[$key]=1; left=1; continue; }
    left=1; [ -n "${started[$key]:-}" ] && continue
    ready $1 $2 || continue
    while [ $(jobs -rp | wc -l) -ge $P ]; do sleep 10; done
    started[$key]=1
    ( bash $B/run_one.sh $1 $2 $3 > $B/runs/log-$key.txt 2>&1; echo "$(date +%T) done $key" ) &
  done
  [ $left = 0 ] && break
  sleep 30
done
wait; echo "ALL DONE"
