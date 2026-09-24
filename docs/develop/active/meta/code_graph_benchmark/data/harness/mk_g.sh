#!/usr/bin/env bash
# Graft templates, chronological cache chain. Usage: mk_g.sh
set -uo pipefail
B=$(cd "$(dirname "$0")" && pwd); N=$HOME/.local/node/bin
export PATH=$N:$HOME/.local/bin:$PATH DO_NOT_TRACK=1
declare -A NEW=([T3]="_blur_on" [T2]="MC_FIXED validate_return_mode" [T8]="GAE_NORM MC_RAW" [T1]="warming_rate_scale cooling_rate_scale" [T7]="MAP_GAP_PX" [T6]="")
prev=""
for t in T3 T2 T8 T1 T7 T6; do
  d=$B/tpl/$t/G; rm -rf $d; cp -a $B/tpl/$t/A $d
  [ -n "$prev" ] && cp -a $B/tpl/$prev/G/graft $d/graft
  s=$(date +%s)
  (cd $d && GRAFT_RELAY_MODEL=sonnet GRAFT_RELAY_LOG=$B/tpl/$t/graft_relay.jsonl timeout 10800 graft-deep > $B/tpl/$t/graft_build.log 2>&1); rc=$?
  echo "$t deep build rc=$rc $(( $(date +%s)-s ))s: $(tail -1 $B/tpl/$t/graft_build.log)"
  (cd $d && graft init --agents claude --no-global --no-statusline > $B/tpl/$t/graft_init.log 2>&1)
  sed -i "s|\"command\": \"node \\\\\"|\"command\": \"$N/node \\\\\"|" $d/.claude/settings.json
  printf '{"mcpServers":{"graft":{"command":"%s/node","args":["%s/../lib/node_modules/@nanonets/graft/dist/cli.js","mcp"],"env":{"DO_NOT_TRACK":"1"}}}}\n' $N $N > $d/.mcp.json
  for w in ${NEW[$t]}; do n=$(grep -rlw "$w" $d/graft 2>/dev/null | wc -l); echo "   leak-grep $w in graft/: $n files"; done
  (cd $d && git add -A && git -c user.email=bench@local -c user.name=bench commit -qm "graft wiring" && echo "   committed")
  prev=$t
done
