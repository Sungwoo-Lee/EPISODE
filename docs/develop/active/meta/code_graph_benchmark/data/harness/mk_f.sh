#!/usr/bin/env bash
set -uo pipefail
B=$(cd "$(dirname "$0")" && pwd); SK=$(dirname $B)/graphify_SKILL.md
for t in $(awk '{print $1}' $B/final_tasks.txt); do
  d=$B/tpl/$t/F; rm -rf $d; cp -a $B/tpl/$t/A $d; H=$B/tpl/home-f-$t; rm -rf $H
  bash $B/lib/sandbox.sh $d $H -- bash -c 'G=/home/vncuser/miniconda3/envs/grid_world_pain/bin/graphify; s=$(date +%s); $G update . >/dev/null 2>&1; echo "update $(( $(date +%s)-s ))s"; $G claude install >/dev/null 2>&1' > $B/tpl/$t/graphify_build.log 2>&1
  mkdir -p $d/.claude/skills/graphify; cp $SK $d/.claude/skills/graphify/SKILL.md
  (cd $d && git add -A && git -c user.email=bench@local -c user.name=bench commit -qm "graphify wiring")
  echo "$t F: $(cat $B/tpl/$t/graphify_build.log) nodes=$(grep -oE '[0-9]+ nodes' $d/graphify-out/GRAPH_REPORT.md | head -1) section=$(grep -c '^## graphify' $d/CLAUDE.md) hook=$(grep -c PreToolUse $d/.claude/settings.json)"
done
