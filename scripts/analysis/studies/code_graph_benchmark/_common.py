"""_common.py - shared data access, statistics and colour map for the code-graph benchmark page.

WHAT THE STUDY IS. Six real past multi-file commits of this repo, replayed as coding tasks, each
attempted three times by three groups of sandboxed Claude Code (Sonnet) sessions: plain (A), with
Graft (G), with Graphify (F). Every attempt was graded by the commit's own tests. Write-up:
docs/develop/active/meta/code_graph_benchmark/CODE_GRAPH_BENCHMARK_RESULTS.md.

WHY ONE MODULE. The figures and the page quote the same numbers (per-task medians, task-paired
ratios, bootstrap intervals, tool-use counts). Computing them here, once, is what stops the page
text and a figure from drifting apart (format register F15).

DATA. data/runs/<task>-<arm>-<trial>/score.json (grader output) and tool_use.json (counts
extracted from the run's event stream); data/excluded_runs.json names attempts outside the 54.
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))   # three levels below scripts/: four ".." (dependency-map depth hazard)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house  # noqa: E402

DOC = os.path.join(ROOT, "docs", "develop", "active", "meta", "code_graph_benchmark")
DATA = os.path.join(DOC, "data")
OUT = os.environ.get("CODE_GRAPH_FIG_ROOT", os.path.join(DOC, "figures"))

ARMS = ["A", "G", "F"]
ARM_NAME = {"A": "Plain Claude Code", "G": "With Graft", "F": "With Graphify"}
# Colour -> meaning, fixed once for every figure on the page (guide 10b item 39). Grey is the
# baseline because it is the reference, not a treatment. Blue and orange are the two tools: the
# house pair that survives the common colour-vision deficiencies. Because blue and orange are spent
# on data, the page must not also use them as chrome (register F11); its template says how.
ARM_COLOUR = {"A": house.INK_2, "G": house.BLUE, "F": house.ORANGE}

TASKS = ["T1", "T2", "T3", "T6", "T7", "T8"]
TASK_NAME = {
    "T1": "Thermal warming / cooling speeds",
    "T2": "MC_FIXED return mode",
    "T3": "Blur settings conditional-mandatory",
    "T6": "Dashboard never refuses a range",
    "T7": "Panel width matches the painter",
    "T8": "GAE_NORM and MC_RAW return modes",
}
TRIALS = ["1", "2", "3"]


def load_runs() -> dict:
    """{run_name: score dict + tool_use dict + total_in}. Refuses an incomplete grid."""
    runs = {}
    for f in sorted(glob.glob(os.path.join(DATA, "runs", "*", "score.json"))):
        name = os.path.basename(os.path.dirname(f))
        d = json.load(open(f))
        d.update(json.load(open(os.path.join(os.path.dirname(f), "tool_use.json"))))
        d["total_in"] = d["input_tokens"] + d["cache_read"] + d["cache_write"]
        runs[name] = d
    want = {f"{t}-{a}-{k}" for t in TASKS for a in ARMS for k in TRIALS}
    missing = sorted(want - set(runs))
    if missing:
        raise SystemExit(f"code_graph_benchmark: missing graded runs {missing}")
    extra = sorted(set(runs) - want)
    if extra:
        raise SystemExit(f"code_graph_benchmark: unexpected runs {extra}")
    return runs


def excluded() -> list:
    return json.load(open(os.path.join(DATA, "excluded_runs.json")))["excluded"]


def cell(runs, task, arm, key):
    return [runs[f"{task}-{arm}-{k}"][key] for k in TRIALS]


def paired_ratios(runs, key, arm, n_boot=4000, seed=0):
    """Task-paired ratio of arm vs A for one metric.

    Per task: median of the arm's three attempts / median of the baseline's three. Across tasks:
    the geometric mean of those six ratios (a ratio of 2 and a ratio of 0.5 average to 1, as they
    should). Interval: resample the three attempts within each task-and-group cell with
    replacement, recompute, repeat n_boot times, take the 2.5th and 97.5th percentiles.
    Returns (point, low, high, per_task_ratios).
    """
    ratios = [statistics.median(cell(runs, t, arm, key)) / statistics.median(cell(runs, t, "A", key))
              for t in TASKS]
    point = math.exp(statistics.mean(math.log(r) for r in ratios))
    rnd, boots = random.Random(seed), []
    for _ in range(n_boot):
        logs = []
        for t in TASKS:
            xa = [runs[f"{t}-A-{rnd.choice(TRIALS)}"][key] for _ in TRIALS]
            xb = [runs[f"{t}-{arm}-{rnd.choice(TRIALS)}"][key] for _ in TRIALS]
            logs.append(math.log(statistics.median(xb) / statistics.median(xa)))
        boots.append(math.exp(statistics.mean(logs)))
    boots.sort()
    return point, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1], ratios


def data_statement(stem: str, rows: list[dict]) -> None:
    """Write <stem>.data.txt: used / available / percentage per subset, with a reason (guide 11b)."""
    parts = []
    for r in rows:
        pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
        parts.append(f"{r['what']}: {r['used']} of {r['total']} ({pct:.0f}%) &mdash; {r['note']}")
    with open(os.path.join(OUT, f"{stem}.data.txt"), "w") as fh:
        fh.write(" ".join(p.rstrip(".") + "." for p in parts) + "\n")
