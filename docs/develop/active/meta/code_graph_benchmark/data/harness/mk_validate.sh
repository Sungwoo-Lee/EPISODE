#!/usr/bin/env bash
set -euo pipefail
B=$(dirname "$0"); R=/media/nas01/projects/Interoceptive-AI/grid_world_pain; cd $R
while read t h; do
  for side in before after; do d=$B/validate/$t-$side; rm -rf $d; mkdir -p $d
    ref=$h; [ $side = before ] && ref=$h^
    timeout 600 git archive --format=tar $ref -- . ":(exclude,glob)docs/project/references/*/sources/**" | tar -x -C $d; done
  tests=$(git show --name-only --format= $h | grep -E '^tests/.*\.py$' | tr '\n' ' ')
  echo "$tests" > $B/validate/$t.tests
  for f in $tests; do mkdir -p $(dirname $B/validate/$t-before/$f); git show $h:$f > $B/validate/$t-before/$f; done
  echo "$t $h tests: $tests"
done < $B/tasks.txt
