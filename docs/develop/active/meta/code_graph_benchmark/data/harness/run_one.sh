#!/usr/bin/env bash
# run_one.sh <task> <arm A|G|F> <trial>  — one sandboxed Claude Code attempt, then grading.
set -uo pipefail
B=$(cd "$(dirname "$0")" && pwd); t=$1; arm=$2; k=$3
RUN=$B/runs/$t-$arm-$k; W=$RUN/work; H=$RUN/home
rm -rf "$RUN"; mkdir -p "$RUN"; cp -a "$B/tpl/$t/$arm" "$W"
# Point every absolute path baked into the copy (snapshot / template paths) at this run's copy.
grep -rlI --exclude-dir=.git -E "$B/(snap/[A-Za-z0-9]+-before|tpl/[A-Za-z0-9]+/[AGF])" "$W" 2>/dev/null \
  | xargs -r sed -i -E "s#$B/(snap/[A-Za-z0-9]+-before|tpl/[A-Za-z0-9]+/[AGF])#$W#g"
(cd "$W" && git add -A && git -c user.email=bench@local -c user.name=bench commit -qm "run base" --allow-empty)
BASE=$(git -C "$W" rev-parse HEAD)

# PATH: identical for all arms except the tool itself.
SHIM=$RUN/shim; mkdir -p $SHIM; ln -s $HOME/.local/node/bin/node $SHIM/node
[ $arm = G ] && ln -s $HOME/.local/node/bin/graft $SHIM/graft
[ $arm = F ] && ln -s /home/vncuser/miniconda3/envs/grid_world_pain/bin/graphify $SHIM/graphify
P="$SHIM:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

PROMPT=$(/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -c "import json,sys;print(json.load(open('$B/prompts.json'))['$t'])")
PROMPT="$PROMPT

(Benchmark run: implement this change in the current directory and make sure the relevant tests pass. Use /home/vncuser/miniconda3/envs/grid_world_pain/bin/python for Python. Do not update the diary, LLM wiki or memory, do not commit, do not launch training, and do not spawn sub-agents.)"
TOOLS=(Bash Read Grep Glob Edit Write Skill); EXTRA=()
[ $arm = G ] && { TOOLS+=("mcp__graft"); EXTRA=(--mcp-config "$W/.mcp.json"); }

start=$(date +%s)
bash $B/lib/sandbox.sh "$W" "$H" -- env PATH="$P" JAX_PLATFORMS=cpu XLA_PYTHON_CLIENT_PREALLOCATE=false \
  timeout 2700 /home/vncuser/.local/bin/claude -p "$PROMPT" --model sonnet \
  --output-format stream-json --verbose --permission-mode acceptEdits \
  --allowedTools "${TOOLS[@]}" --disallowedTools Agent "${EXTRA[@]}" \
  2> "$RUN/stderr.log" | awk '{print systime() "\t" $0; fflush()}' > "$RUN/stream.tsv"
echo $(( $(date +%s) - start )) > "$RUN/wall_s"

# Save the agent's change (graph caches are gitignored), then grade on the same copy.
(cd "$W" && git add -A && git diff --cached $BASE --stat > "$RUN/diffstat.txt" && git diff --cached $BASE > "$RUN/agent.patch" \
  && git diff --cached $BASE --name-only > "$RUN/changed_files.txt")
bash $B/grade.sh "$t" "$RUN"
