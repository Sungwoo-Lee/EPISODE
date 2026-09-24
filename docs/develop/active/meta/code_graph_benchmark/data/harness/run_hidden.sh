#!/usr/bin/env bash
# run_hidden.sh <snapshot_dir> <tests_file> <out_prefix>
d=$1; tf=$2; out=$3
cd "$d" && JAX_PLATFORMS=cpu XLA_PYTHON_CLIENT_PREALLOCATE=false timeout 1800 \
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest -q -p no:cacheprovider $(cat "$tf") \
  > "$out.log" 2>&1; echo $? > "$out.rc"
