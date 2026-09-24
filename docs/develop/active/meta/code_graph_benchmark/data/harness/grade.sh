#!/usr/bin/env bash
# grade.sh <task> <run_dir> — overlay the commit's tests on the agent's result, run, score.
B=$(cd "$(dirname "$0")" && pwd); t=$1; RUN=$2; W=$RUN/work; R=/media/nas01/projects/Interoceptive-AI/grid_world_pain
(cd $B/snap/hidden/$t && find . -type f) | while read f; do f=${f#./}; mkdir -p "$W/$(dirname $f)"; sed "s#$R#$W#g" "$B/snap/hidden/$t/$f" > "$W/$f"; done
dirs=$(/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -c "import json;print(' '.join(json.load(open('$B/grading.json'))['$t']['test_dirs']))")
bash $B/lib/pytest_in.sh "$W" "$RUN/grade.xml" "$RUN/grade_home" $dirs > "$RUN/grade.tail" 2>&1
/home/vncuser/miniconda3/envs/grid_world_pain/bin/python $B/lib/score.py "$t" "$RUN" > "$RUN/score.json"
cat "$RUN/score.json"
