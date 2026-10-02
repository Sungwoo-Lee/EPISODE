#!/usr/bin/env bash
B=$(cd "$(dirname "$0")" && pwd); mkdir -p $B/gate
for t in T1 T2 T3 T4 T5 T6; do for s in before after; do
  bash "$B/run_hidden.sh" "$B/validate/$t-$s" "$B/validate/$t.tests" "$B/gate/$t-$s" &
done; done; wait
for t in T1 T2 T3 T4 T5 T6; do for s in before after; do
  printf '%s-%-6s rc=%s  %s\n' $t $s "$(cat $B/gate/$t-$s.rc)" "$(grep -E 'passed|failed|error' $B/gate/$t-$s.log | tail -1 | cut -c1-120)"
done; done
