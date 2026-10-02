#!/usr/bin/env bash
B=$(cd "$(dirname "$0")" && pwd); R=/media/nas01/projects/Interoceptive-AI/grid_world_pain
chk() { t=$1; h=$(awk -v t=$t '$1==t{print $2}' $B/final_tasks.txt); RUN=$B/gradercheck/$t; rm -rf $RUN; mkdir -p $RUN
  cp -a $B/snap/$t-after $RUN/work; grep -rlI -E "$B/snap/[A-Za-z0-9]+-(before|after)" $RUN/work | xargs -r sed -i -E "s#$B/snap/[A-Za-z0-9]+-(before|after)#$RUN/work#g"
  git -C $R show --name-only --format= $h > $RUN/changed_files.txt; echo 0 > $RUN/wall_s; : > $RUN/stream.tsv
  bash $B/grade.sh $t $RUN > /dev/null 2>&1
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python -c "import json;d=json.load(open('$RUN/score.json'));print('$t', 'correct=',d['correct'], 'f2p', d['f2p_passed'], 'p2p_broken', d['p2p_broken'], '/', d['p2p_total'], 'recall', d['ref_recall'])"; }
export -f chk; export B R
awk '{print $1}' $B/final_tasks.txt | xargs -P 6 -I{} bash -c 'chk {}'
