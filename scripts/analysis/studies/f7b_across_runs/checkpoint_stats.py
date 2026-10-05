#!/usr/bin/env python3
"""checkpoint_stats.py - checkpoint-wise bush-dwell statistics, alongside whole-training summaries.

collect.py reduces each run to the newest 20 checkpoints. That hides what the per-checkpoint
figures (FIG_bush_hiding.png) show: whether a scene's line is stable or swings, whether an injury
or animal effect is present at nearly every checkpoint or only on average, and whether all scenes
rise and fall together (the whole policy swinging) or each scene behaves on its own.

For every run in <data>/runs.csv this writes:

  ckpt_long.csv   one row per (run, checkpoint, quantity): the per-checkpoint value itself.
                  Quantities: level <scene>@<inj>; injury <scene> (inj 70 - inj 0);
                  animal <scene> (scene - no animal, inj 0); pred-vs-rabbit (inj 0).
  ckpt_summary.csv one row per (run, quantity, window) with window "all" (the matched step range
                  --from-M..--to-M, default 2-10 M, on a common checkpoint grid every --spacing-M,
                  default 0.2 M: the measured checkpoint nearest each grid point, within a quarter
                  spacing; nothing interpolated) and "late20" (the newest 20 checkpoints as tested,
                  collect.py's window -- must equal its levels.csv / injury_effect.csv):
                  mean and lag-1-corrected 95 % interval (window_profile, the Basic Behaviour
                  estimator), SD across checkpoints, mean absolute change between neighbouring
                  checkpoints, share of checkpoints above zero (contrasts only), n checkpoints.
  ckpt_dropped.csv runs left out of the "all" window, with the reason (tested checkpoints end
                  before --min-end-M, default 8 M; injury-grid rows of runs also tested in the core or
                  temperature set, whose injury 0 / 70 tests they repeat -- the level 02 / 03 runs,
                  tested only in the injury-grid set, are kept).
  ckpt_comove.csv  per (run, window, scene): correlation across checkpoints between the no-animal
                  level and that scene's level, both at injury 0. High = the scenes move together.

Neighbouring checkpoints are not independent; the "share above zero" is a description, and the
interval uses the lag-1 effective sample size, not the raw checkpoint count.

    $P scripts/analysis/studies/f7b_across_runs/checkpoint_stats.py --data results/analysis/f7b_across_runs
    (defaults: --from-M 2 --to-M 10 --spacing-M 0.2 --min-end-M 8; user decisions 2026-10-05)
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect as C  # noqa: E402  (read, SCENES, INJ; C.P = probes, C.P.W = window_profile)



def series(c):
    """{(scene, inj): Series of bush dwell (pp) indexed by checkpoint step} for one run."""
    out = {}
    for s in C.SCENES:
        for i in C.INJ:
            d = C.read(c["leaf"], s, i)
            if d is not None:
                out[(s, i)] = d.set_index("step")["bush_hiding"].astype(float) * 100.0
    return out


def quantities(S):
    """{name: (kind, Series)} of per-checkpoint quantities, aligned on shared steps."""
    q = {}
    for (s, i), v in S.items():
        q[f"level {s}@{i}"] = ("level", v)
    for s in C.SCENES:
        if (s, "70") in S and (s, "00") in S:
            q[f"injury {s}"] = ("contrast", (S[(s, "70")] - S[(s, "00")]).dropna())
        if s != "none" and (s, "00") in S and ("none", "00") in S:
            q[f"animal {s}"] = ("contrast", (S[(s, "00")] - S[("none", "00")]).dropna())
    if ("pred", "00") in S and ("rabbit", "00") in S:
        q["pred-vs-rabbit"] = ("contrast", (S[("pred", "00")] - S[("rabbit", "00")]).dropna())
    return q


def on_grid(v, lo, hi, spacing):
    """Measured checkpoints nearest each grid point lo, lo+spacing, ..., hi (within spacing/4)."""
    if v.empty:
        return v
    steps = v.index.to_numpy(dtype=float)
    keep = []
    for g in np.arange(lo, hi + spacing / 2, spacing) * 1e6:
        j = int(np.argmin(np.abs(steps - g)))
        if abs(steps[j] - g) <= spacing * 1e6 / 4 and (not keep or keep[-1] != j):
            keep.append(j)
    return v.iloc[keep]


def describe(v, kind):
    v = v.dropna()
    if len(v) < 3:
        return None
    p = C.P.W.window_profile(v.to_numpy(), windows=[len(v)]).iloc[0]
    out = {"mean": p["mean"], "lo": p["lo"], "hi": p["hi"], "r1": p["r1"], "n_eff": p["n_eff"],
           "ckpt_sd": float(v.std(ddof=1)), "mean_abs_step": float(v.diff().abs().mean()), "n_ckpt": len(v)}
    out["share_pos"] = float((v > 0).mean()) if kind == "contrast" else np.nan
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="collect.py output folder (runs.csv)")
    ap.add_argument("--from-M", type=float, default=2.0, help="matched window start, million steps")
    ap.add_argument("--to-M", type=float, default=10.0, help="matched window end, million steps")
    ap.add_argument("--spacing-M", type=float, default=0.2, help="common checkpoint grid spacing, million steps")
    ap.add_argument("--min-end-M", type=float, default=8.0,
                    help="runs whose tested checkpoints end before this are left out of the matched window")
    a = ap.parse_args(argv)
    runs = pd.read_csv(os.path.join(a.data, "runs.csv"))
    long, summ, como, dropped = [], [], [], []
    tested_elsewhere = set(runs.loc[runs.scene_set != "injgrid", "run_dir"])
    for c in runs.to_dict("records"):
        if c["scene_set"] == "injgrid" and c["run_dir"] in tested_elsewhere:
            dropped.append({"id": c["id"], "reason": "injury-grid scene set: repeats the core / temperature sets' "
                            "injury 0 and 70 tests on the same runs (identical values)"})
            continue
        S = series(c)
        if not S:
            continue
        end_M = max(v.index.max() for v in S.values()) / 1e6
        matched = end_M >= a.min_end_M
        if not matched:
            dropped.append({"id": c["id"], "reason": f"tested checkpoints end at {end_M:.2f} M steps, "
                            f"before {a.min_end_M:g} M (matched window {a.from_M:g}-{a.to_M:g} M)"})
        for name, (kind, v) in quantities(S).items():
            v = v.sort_index()
            for step, x in v.items():
                long.append({"id": c["id"], "step_M": step / 1e6, "quantity": name, "value": x})
            wins = [("late20", v.iloc[-C.P.WINDOW:])]
            if matched:
                wins.insert(0, ("all", on_grid(v, a.from_M, a.to_M, a.spacing_M)))
            for win, vv in wins:
                d = describe(vv, kind)
                if d:
                    summ.append({"id": c["id"], "agent": c["agent"], "family": c["family"], "setting": c["setting"],
                                 "seed": c["seed"], "scene_set": c["scene_set"], "quantity": name, "kind": kind,
                                 "window": win, **d})
        if ("none", "00") in S:
            base = S[("none", "00")]
            for s in C.SCENES[1:]:
                if (s, "00") not in S:
                    continue
                m = pd.concat([base, S[(s, "00")]], axis=1, join="inner").dropna().sort_index()
                wins = [("late20", m.iloc[-C.P.WINDOW:])]
                if matched:
                    g = on_grid(m.iloc[:, 0], a.from_M, a.to_M, a.spacing_M).index
                    wins.insert(0, ("all", m.loc[g]))
                for win, mm in wins:
                    if len(mm) >= 5 and mm.iloc[:, 0].std() > 0 and mm.iloc[:, 1].std() > 0:
                        como.append({"id": c["id"], "agent": c["agent"], "window": win, "scene": s,
                                     "corr_with_none": float(np.corrcoef(mm.iloc[:, 0], mm.iloc[:, 1])[0, 1]),
                                     "n_ckpt": len(mm)})
    pd.DataFrame(long).to_csv(os.path.join(a.data, "ckpt_long.csv"), index=False)
    pd.DataFrame(summ).to_csv(os.path.join(a.data, "ckpt_summary.csv"), index=False)
    pd.DataFrame(como).to_csv(os.path.join(a.data, "ckpt_comove.csv"), index=False)
    pd.DataFrame(dropped).to_csv(os.path.join(a.data, "ckpt_dropped.csv"), index=False)
    print(f"runs {runs.shape[0]}  left out of matched window {len(dropped)}  checkpoint rows {len(long)}  summary rows {len(summ)}  co-movement rows {len(como)}")


if __name__ == "__main__":
    main()
