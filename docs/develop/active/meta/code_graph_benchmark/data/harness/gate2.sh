#!/usr/bin/env bash
B=$(cd "$(dirname "$0")" && pwd); S=$B/snap; G=$B/gate2; mkdir -p $G; R=/media/nas01/projects/Interoceptive-AI/grid_world_pain
one() { t=$1
  dirs=$(for f in $(cat $S/$t.tests); do dirname $f; done | sort -u | tr '\n' ' ')
  gb=$G/$t-before; rm -rf $gb; cp -a $S/$t-before $gb
  (cd $S/hidden/$t && find . -type f) | while read f; do f=${f#./}; mkdir -p $gb/$(dirname $f); sed "s#$R#$gb#g" $S/hidden/$t/$f > $gb/$f; done
  bash $B/lib/pytest_in.sh $gb $G/$t-before.xml $G/home-$t-b $dirs > $G/$t-before.tail 2>&1
  bash $B/lib/pytest_in.sh $S/$t-after $G/$t-after.xml $G/home-$t-a $dirs > $G/$t-after.tail 2>&1
  echo "$t done: $dirs"; }
export -f one; export B S G R
awk '{print $1}' $B/tasks2.txt | xargs -P 7 -I{} bash -c 'one {}'
