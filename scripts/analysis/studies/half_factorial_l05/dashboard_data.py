#!/usr/bin/env python3
"""dashboard_data.py - the data behind the Figure 5 dashboard (random layout every episode).

Reads the eight random-layout test sets (healing on/off x food/no food x sampled/greedy actions; 4 animals x
starting injury 0-70; 100 episodes per checkpoint, newest 20 checkpoints per run) written by
scripts/eval/dwell_sweep/run_sweep.py with configs/eval_sweeps/lookalike_hf_random_layout/*.yaml, and writes one
compact JSON the page script reads. Every number is bush dwell in percent; the page forms the contrasts per
checkpoint and averages them, so this file holds the per-checkpoint values, not summaries.

A run resumed under the same WandB run has one result folder per session (<label>, <label>_resumed<k>); they are
merged on the checkpoint step (the later session wins a shared step), then the newest 20 steps are kept. A run with
fewer than 20 tested checkpoints in any scene of a set is left out of that set and listed in "incomplete".

Layout error ("lay"): every scene of a set reuses the same 100 episode seeds, so the same 100 layouts, at every
checkpoint and in every run. Where the set's per-episode table exists (extract_episodes.py), the 95 % interval of each
row's value (world x agent, seeds pooled) over WHICH 100 layouts were drawn is estimated by resampling the 100 seeds
with replacement, the same draw for every scene, checkpoint and run of the row (B = 2,000), so the contrasts keep
their pairing. Half-width in points; it does not include seed-to-seed variation, which the page shows separately.

    $P scripts/analysis/studies/half_factorial_l05/dashboard_data.py --out <file.json>
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BASE = os.path.join(ROOT, "results", "eval", "avoidance", "metrics_history_rppo_lookalike_hf_random_layout")
SETS = [f"heal{h}_{f}_{a}" for h in ("off", "on") for f in ("food", "nofood") for a in ("sampled", "greedy")]
ANIMALS = ("none", "rabbitwander", "rabbit", "pred")
INJ = ("00", "10", "20", "30", "50", "70")
NEWEST = 20
BOOT = 2000
SAME_CKPT = 10_000   # steps; checkpoints are ~200,000 steps apart
EPISODES = 100
LABEL = re.compile(r"^(l05ref|lookalike|hf_w(\d+))_(ordinary|modulated)_s(\d+)(_resumed\d*)?$")
# setting groups at their new value per world (design doc, tables "The eight worlds" and "The other eight")
NEW = {0: None, 1: "", 2: "AD", 3: "BD", 4: "AB", 5: "CD", 6: "AC", 7: "BC", 8: "ABCD",
       9: "A", 10: "B", 11: "C", 12: "D", 13: "ABC", 14: "ABD", 15: "ACD", 16: "BCD"}


def world_of(m):
    return 0 if m.group(1) == "l05ref" else 1 if m.group(1) == "lookalike" else int(m.group(2))


def read_set(s):
    """{(world, agent, seed): {scene: DataFrame(step -> bush %)}} for one set, folders merged."""
    runs = {}
    for d in sorted(glob.glob(os.path.join(BASE, s, "*"))):
        m = LABEL.match(os.path.basename(d))
        if not m or not os.path.isdir(d):
            continue
        key = (world_of(m), m.group(3), int(m.group(4)))
        sess = 0 if m.group(5) is None else int(m.group(5)[len("_resumed"):] or 1)
        for a in ANIMALS:
            for i in INJ:
                p = os.path.join(d, f"avoid_{a}_inj{i}.csv")
                if os.path.exists(p):
                    t = pd.read_csv(p, usecols=["step", "bush_hiding"]).assign(_s=sess)
                    runs.setdefault(key, {}).setdefault(f"{a}_{i}", []).append(t)
    out = {}
    for key, sc in runs.items():
        out[key] = {}
        for name, parts in sc.items():
            t = pd.concat(parts).sort_values(["step", "_s"])
            # a resumed session can save the checkpoint it resumed from under a slightly different step (e.g.
            # 8200036 and 8200088): steps within SAME_CKPT of each other are one checkpoint, the later session's
            # row kept (plan review 2026-10-18, M3)
            t["_ck"] = (t["step"].diff().fillna(SAME_CKPT + 1) > SAME_CKPT).cumsum()
            t = t.sort_values(["_ck", "_s", "step"]).groupby("_ck").tail(1)
            out[key][name] = t.set_index("step")["bush_hiding"].astype(float) * 100.0
    return out


def measures():
    """(id, function of a dict scene -> array) for every value the page shows; ids match the page script's
    ('d:<animal>:<inj>' dwell; 'inj:<animal>@<inj>', 'c:r0', 'c:r1@<inj>', 'c:rxi@<inj>' contrasts)."""
    out = [(f"d:{a}:{i}", (lambda a, i: lambda X: X[f"{a}_{i}"])(a, i)) for a in ANIMALS for i in INJ]
    for i in INJ[1:]:
        for a in ANIMALS:
            out.append((f"inj:{a}@{i}", (lambda a, i: lambda X: X[f"{a}_{i}"] - X[f"{a}_00"])(a, i)))
        r = lambda X, i: X[f"rabbitwander_{i}"] - X[f"none_{i}"]
        out.append((f"c:r1@{i}", (lambda i: lambda X: r(X, i))(i)))
        out.append((f"c:rxi@{i}", (lambda i: lambda X: r(X, i) - r(X, "00"))(i)))
    out.append(("c:r0", lambda X: X["rabbitwander_00"] - X["none_00"]))
    return out


def layout_error(s, chosen):
    """{row 'world|agent': {measure id: 95 % half-width}} for one set, or None without its per-episode table.
    `chosen`: {rid: steps used} for the runs kept in this set."""
    p = os.path.join(BASE, s, "_episodes", "episodes.parquet")
    if not os.path.exists(p):
        return None
    e = pd.read_parquet(p, columns=["run", "cond", "step", "episode_index", "bush_hiding"])
    rng = np.random.default_rng(20261018)
    W = rng.multinomial(EPISODES, np.full(EPISODES, 1 / EPISODES), size=BOOT).T / EPISODES   # (100, B)
    rows = {}
    for run, g in e.groupby("run"):
        m = LABEL.match(run)
        key = (world_of(m), m.group(3), int(m.group(4)))
        rid = "%d|%s|%d" % key
        if rid not in chosen:
            continue
        g = g[g["step"].isin(chosen[rid])]
        X = {}
        for cond, h in g.groupby("cond"):
            name = cond[len("avoid_"):].replace("_inj", "_")
            t = h.pivot_table(index="step", columns="episode_index", values="bush_hiding")
            assert t.shape == (NEWEST, EPISODES), (s, rid, cond, t.shape)
            X[name] = t.to_numpy().mean(axis=0) * 100.0          # per layout, mean over the 20 checkpoints
        rows.setdefault("%d|%s" % key[:2], []).append(X)
    out = {}
    for row, Xs in rows.items():
        out[row] = {}
        for mid, f in measures():
            per_run = np.stack([f(X) for X in Xs])               # (runs, 100)
            b = (per_run @ W).mean(axis=0)                       # (B,) row value under each resampled layout set
            lo, hi = np.percentile(b, [2.5, 97.5])
            out[row][mid] = round(float((hi - lo) / 2), 2)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    scenes = [f"{an}_{i}" for an in ANIMALS for i in INJ]
    runs, data, incomplete = {}, {}, []
    for s in SETS:
        if not os.path.isdir(os.path.join(BASE, s)):
            continue
        data[s] = {}
        for key, sc in read_set(s).items():
            lens = {n: len(sc.get(n, ())) for n in scenes}
            if min(lens.values()) < NEWEST:
                incomplete.append({"set": s, "run": list(key), "fewest_checkpoints": min(lens.values())})
                continue
            # the newest 20 steps common to every scene of this run (they are the same set when complete)
            steps = sorted(set.intersection(*(set(sc[n].index) for n in scenes)))[-NEWEST:]
            assert len(steps) < 2 or min(b - a for a, b in zip(steps, steps[1:])) > SAME_CKPT, (s, key, steps)
            if len(steps) < NEWEST:
                incomplete.append({"set": s, "run": list(key), "fewest_checkpoints": len(steps)})
                continue
            rid = "%d|%s|%d" % key
            runs[rid] = {"world": key[0], "agent": key[1], "seed": key[2]}
            data[s][rid] = {"steps": [int(x) for x in steps],
                            "v": {n: [round(float(sc[n][x]), 2) for x in steps] for n in scenes}}
    data = {s: v for s, v in data.items() if v}   # a set still being collected has no complete run yet
    lay = {}
    for s in data:
        le = layout_error(s, {rid: r["steps"] for rid, r in data[s].items()})
        if le is not None:
            lay[s] = le
    meta = {"sets": list(data), "layout_error_sets": list(lay), "boot": BOOT, "animals": ANIMALS, "injuries": INJ, "newest": NEWEST, "episodes": EPISODES,
            "new_groups": NEW, "incomplete": incomplete,
            "source": os.path.relpath(BASE, ROOT)}
    with open(a.out, "w") as fh:
        json.dump({"meta": meta, "runs": runs, "data": data, "lay": lay}, fh, separators=(",", ":"))
    n = {s: len(v) for s, v in data.items()}
    print(f"wrote {a.out}: runs per set {n}; incomplete {len(incomplete)}")


if __name__ == "__main__":
    main()
