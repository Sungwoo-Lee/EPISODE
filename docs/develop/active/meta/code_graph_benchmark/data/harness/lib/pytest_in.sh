#!/usr/bin/env bash
# pytest_in.sh <copy_dir> <junit_out> <home_dir> <test paths...> — run pytest on a copy, sandboxed.
C=$1; J=$2; H=$3; shift 3
L=$(dirname "$0")
bash "$L/sandbox.sh" "$C" "$H" -- bash -c "cd '$C' && JAX_PLATFORMS=cpu XLA_PYTHON_CLIENT_PREALLOCATE=false timeout 2400 \
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest -q -p no:cacheprovider --no-header --continue-on-collection-errors -rN \
  --junitxml=/tmp/j.xml $* > /tmp/p.log 2>&1; cp /tmp/j.xml '$C/.junit.xml' 2>/dev/null; tail -3 /tmp/p.log"
mv "$C/.junit.xml" "$J" 2>/dev/null
