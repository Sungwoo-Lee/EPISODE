#!/usr/bin/env bash
# Before = git archive <h>^ without docs/; after = before + the commit's own diff (minus docs/).
set -uo pipefail
B=$(cd "$(dirname "$0")" && pwd); R=/media/nas01/projects/Interoceptive-AI/grid_world_pain; S=$B/snap; mkdir -p $S
mk() { t=$1; h=$2
  rm -rf $S/$t-before $S/$t-after; mkdir -p $S/$t-before
  timeout 900 git -C $R archive --format=tar $h^ -- . ':(exclude)docs' | tar -x -C $S/$t-before || { echo "$t archive FAILED"; return; }
  cp -a $S/$t-before $S/$t-after
  git -C $R diff --binary $h^ $h -- . ':(exclude)docs' > $S/$t.patch
  (cd $S/$t-after && git apply --whitespace=nowarn $S/$t.patch) || echo "$t APPLY FAILED"
  git -C $R show --name-only --format= $h | grep -E '^tests/.*\.py$' | tr '\n' ' ' > $S/$t.tests
  for f in $(cat $S/$t.tests); do mkdir -p "$(dirname $S/$t-before/$f)"; git -C $R show $h:$f > $S/$t-before/$f.hidden; done
  echo "$t $h done"; }
while read t h; do mk $t $h & sleep 2; done < $B/tasks2.txt; wait
