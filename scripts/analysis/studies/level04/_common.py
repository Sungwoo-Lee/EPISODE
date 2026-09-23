"""Shared data access for the level-04 re-measurement figures.

Two fixes separate this from the level-04 analysis published on 2026-09-22, and both are enforced
here rather than remembered. Every probe number is a MEAN OVER THE LAST 20 SAVED CHECKPOINTS, never
the final one, because checkpoint-to-checkpoint policy variation is four to ten times the sampling
error of the thirty episodes behind any one checkpoint. And every probe number comes from the sweep
run on the BLOCKING bush -- the earlier sweep's bush let a predator walk onto the hiding square, which
never happens in the world these agents trained in.
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "basicq2_waves"))
import house                                    # noqa: E402
import window_profile as W                      # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, legend_below, COLUMN_PX)

EV = os.path.join(ROOT, "results/eval/avoidance")
W2 = os.path.join(EV, "metrics_history_rppo_basicq2_wave2_blocking_bush")
#: Wave 1's probe sweep predates the bush fix. Only its no-animal conditions are ever read, where a
#: permeable bush cannot matter because there is nothing to walk in.
W1 = os.path.join(EV, "metrics_history_rppo_basicq2_wave1")
CTX = {"W1": os.path.join(ROOT, "results/analysis/basicq2_w1/context"),
       "W2": os.path.join(ROOT, "results/analysis/basicq2_w1/context_w2")}
FIG = os.path.join(ROOT, "docs/experiments/active/level04_remeasured/figures")
ARMS = [("lvl04_control", "ordinary agent", house.BLUE),
        ("lvl04_modulated", "neuromodulated agent", house.ORANGE)]
WIN = 20

#: Probe scenes, ordered from nothing in the world to a hunting predator.
THREATS = [("avoid_none_inj00", "nothing"),
           ("avoid_rabbitwander_inj00", "rabbit,\nwandering"),
           ("avoid_rabbitwander_predsmell_inj00", "rabbit wandering\n+ predator smell"),
           ("avoid_rabbit_inj00", "rabbit,\nchasing"),
           ("avoid_pred_inj00", "predator")]


def windowed(out_dir, run, cond, w=WIN):
    """(final, windowed mean, lo, hi, n checkpoints) for one run x probe condition, in percent."""
    _, v = W.read_series(out_dir, run, cond)
    if v is None:
        return None
    p = W.window_profile(v).query(f"window=={w}").iloc[0]
    return float(v[-1]), float(p["mean"]), float(p["lo"]), float(p["hi"]), len(v)


def causal_rows(wave, arm):
    d = json.load(open(os.path.join(CTX[wave], f"lvl04_{arm}.json")))
    return [r for r in d["randomised_early"]["rows"] if r["n_calm"] > 1000]


def record_samples(stem, rows):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")
