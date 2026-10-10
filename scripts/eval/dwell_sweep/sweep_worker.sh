#!/usr/bin/env bash
# Per-node behaviour-test sweep worker: play the test episodes into NODE-LOCAL staging, then
# archive + score each cell on this node (finish_cells.py), so the shared disk receives ONE
# archive per checkpoint x scene cell plus one small rows table per worklist line, instead of
# ~64 small files and 5 directories per cell. Plan:
# docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md (F5).
#
# Both algorithms go through the SAME call to scripts/eval/eval_rollout.py --batched --device cpu
# --record --config-list; they differ only in --checkpoint form (rPPO: <run>/models/<step>,
# Dreamer: <run>/checkpoints/<episode>) and Dreamer's extra --agent_config (+ optional --episode).
#
# CHECKPOINT-granularity worklist (one line = one checkpoint + ALL its pending scenes, evaluated
# in ONE eval_rollout.py process -- the model is built and the checkpoint restored once).
#
# run_sweep.py launches a COPY of this file (and of finish_cells.py / cell_measures.py) stored in
# <output_dir>/_provenance/<launch_id>/worker/, so a later edit of the repo's copy can never reach
# a running worker. The repo root is therefore passed in (argument 6, mandatory): it cannot be
# derived from this file's location (plan-review N1).
#
# Usage: sweep_worker.sh <worklist_file> <node_id> <npar> <n_episodes> <launch_id> <repo_root>
#   worklist line format: CHECKPOINT|AGENT_CONFIG_OR_-|EPISODE_OR_-|CFG1,CELL1;CFG2,CELL2;...
#   (CELL = <scratch>/<run_label>/<cond>/<step>; the archive is written to CELL.zip)
#
# Markers in <scratch>/_run_markers/ (read by run_sweep.py poll_done / --status):
#   started_<node>   host, pid, start time               npar_<node>   settings line
#   alive_<node>     "<epoch> <lines finished>", rewritten every 60 s while this script lives
#   lines_<node>     one line appended per finished worklist line
#   fail_<node>      "FAIL <stage> <line>" per failed line (staging kept in /tmp for recovery)
#   prog_<node>      summary line;  done_<node>  normal end;  exit_<node>  "rc=<rc> <epoch>" (EXIT trap)
# Rows: <scratch>/_rows/<launch_id>/<node>/<line hash>.csv, concatenated at the end into
#   <scratch>/_rows/<launch_id>/rows_<node>.csv.
# Logs: <scratch>/_logs/<launch_id>/eval_<node>.log (eval_rollout stderr), finish_<node>.log.
set -uo pipefail

if [ "$#" -ne 6 ]; then
  echo "usage: sweep_worker.sh <worklist> <node> <npar> <n_episodes> <launch_id> <repo_root> (got $# args)" >&2
  exit 2
fi
WL="$1"; NODE="$2"; NPAR="$3"; NEP="$4"; LAUNCH_ID="$5"; R="$6"
[ -f "$WL" ] || { echo "sweep_worker.sh: worklist not found: $WL" >&2; exit 1; }
[ -f "$R/scripts/eval/eval_rollout.py" ] || { echo "sweep_worker.sh: repo root $R has no scripts/eval/eval_rollout.py" >&2; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FINISH="$SCRIPT_DIR/finish_cells.py"
[ -f "$FINISH" ] || { echo "sweep_worker.sh: $FINISH not found next to the worker" >&2; exit 1; }
cd "$R"
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
export PYTHONUNBUFFERED=1

# --- Tuning baked in from the CPU-bound eval-sweep diagnosis (see README.md) ---
export JAX_PLATFORMS=cpu
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TF_NUM_INTRAOP_THREADS=1 TF_NUM_INTEROP_THREADS=1

# Per-node persistent XLA compile cache (shape-only dependence: eval #2..N skip the compile).
export JAX_COMPILATION_CACHE_DIR="/tmp/jaxcache_dwellsweep_$NODE"
export JAX_PERSISTENT_CACHE_MIN_ENTRY_SIZE_BYTES=0 JAX_PERSISTENT_CACHE_MIN_COMPILE_TIME_SECS=0
mkdir -p "$JAX_COMPILATION_CACHE_DIR"

# Worklist lives at <scratch>/_worklists/worklist_<node>.txt.
SCR="$(dirname "$(dirname "$WL")")"
MARK="$SCR/_run_markers"; ROWS="$SCR/_rows/$LAUNCH_ID"; LOGD="$SCR/_logs/$LAUNCH_ID"
mkdir -p "$MARK" "$ROWS/$NODE" "$LOGD"
rm -f "$MARK/done_$NODE" "$MARK/exit_$NODE" "$MARK/lines_$NODE" "$MARK/alive_$NODE"
echo "NODE=$NODE NPAR=$NPAR NEP=$NEP LAUNCH=$LAUNCH_ID $(date)" > "$MARK/npar_$NODE"
echo "host=$(hostname) pid=$$ $(date +%s) launch=$LAUNCH_ID" > "$MARK/started_$NODE"
: > "$MARK/lines_$NODE"

STAGE_ROOT="/tmp/dwellsweep_${LAUNCH_ID}_${NODE}_$$"
mkdir -p "$STAGE_ROOT"

# Heartbeat tied to THIS process: exits as soon as the worker is gone (review M4a).
WPID=$$
( while kill -0 "$WPID" 2>/dev/null; do
    echo "$(date +%s) $(wc -l < "$MARK/lines_$NODE" 2>/dev/null || echo 0)" > "$MARK/alive_$NODE.tmp" \
      && mv -f "$MARK/alive_$NODE.tmp" "$MARK/alive_$NODE"
    sleep 60
  done ) &
HB=$!
# The trap never deletes staging (review M3): leftovers are listed for recovery.
trap 'rc=$?; kill $HB 2>/dev/null; { echo "rc=$rc $(date +%s)"; ls -d "$STAGE_ROOT"/* 2>/dev/null; } > "$MARK/exit_$NODE"' EXIT

export PY NEP MARK NODE ROWS LOGD FINISH STAGE_ROOT R
runeval() {
  IFS='|' read -r ckpt agent ep cfg_out_list <<<"$1"
  extra=""
  [ "$agent" != "-" ] && extra="--agent_config $agent"
  [ "$ep" != "-" ] && extra="$extra --episode $ep"

  stage="$(mktemp -d -p "$STAGE_ROOT")"
  cl_file="$stage/config_list.tsv"
  finish_pairs=()
  IFS=';' read -ra pairs <<< "$cfg_out_list"
  k=0
  for pair in "${pairs[@]}"; do
    pcfg="${pair%%,*}"
    pcell="${pair#*,}"
    mkdir -p "$stage/$k" "$(dirname "$pcell")"
    printf '%s\t%s\n' "$pcfg" "$stage/$k" >> "$cl_file"
    finish_pairs+=("$stage/$k=$pcell")
    k=$((k + 1))
  done

  hash="$(printf '%s' "$1" | md5sum | cut -c1-16)"
  if "$PY" scripts/eval/eval_rollout.py --config-list "$cl_file" $extra --checkpoint "$ckpt" \
       --eval-n-episodes "$NEP" --record --record-n-episodes "$NEP" \
       --device cpu --quiet --batched --seed 0 >/dev/null 2>>"$LOGD/eval_$NODE.log" \
     && "$PY" "$FINISH" --repo-root "$R" --pairs "${finish_pairs[@]}" \
       --rows-piece "$ROWS/$NODE/$hash.csv" --episodes "$NEP" --log "$LOGD/finish_$NODE.log"; then
    rm -rf "$stage"
  else
    echo "FAIL $stage $1" >> "$MARK/fail_$NODE"
  fi
  echo "$hash" >> "$MARK/lines_$NODE"
}
export -f runeval

t0=$(date +%s)
n=$(wc -l < "$WL")
xargs -P "$NPAR" -I@ bash -c 'runeval "$1"' _ @ < "$WL"
xrc=$?

# Concatenate the line pieces into one rows table per node (header once).
out="$ROWS/rows_$NODE.csv"; tmpo="$out.tmp"; first=1; : > "$tmpo"
for f in "$ROWS/$NODE"/*.csv; do
  [ -f "$f" ] || continue
  if [ $first -eq 1 ]; then cat "$f" >> "$tmpo"; first=0; else tail -n +2 "$f" >> "$tmpo"; fi
done
mv -f "$tmpo" "$out"
rmdir "$STAGE_ROOT" 2>/dev/null
echo "[$NODE] done $n lines in $(( $(date +%s)-t0 ))s xargs_rc=$xrc $(date +%H:%M:%S)" >> "$MARK/prog_$NODE"
touch "$MARK/done_$NODE"
