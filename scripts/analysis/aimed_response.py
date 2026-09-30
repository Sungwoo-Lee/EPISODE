#!/usr/bin/env python
"""Is the extra hiding caused by a predator-like rabbit scent AIMED at that rabbit? (study S3)

Run-agnostic successor of the archived `supplementary/falsealarm.py`, which hard-coded the a01
store, its slots and its seed base. Everything here is derived from the run's own saved config.

WHICH EPISODES. Exactly one predator and exactly one rabbit (`animal_active`), so the rabbit's
randomised scent is unambiguous and the predator count is held fixed. The rabbit's scent is turned
into evidence (log-likelihood ratio "predator vs rabbit", nats) with `core/env.scent_spec`, which
works for the three odour layouts the hypervigilance study uses. Two groups:
    rabbit-like      LLR <  RABBIT_LIKE_BELOW_NATS (0)
    predator-like    LLR >= PREDATOR_LIKE_AT_NATS  (2/3 nat; the study's ">= +0.67", and exactly
                     a01's `x1 - x2 >= 0.3` in the two-channel world: 0.3 * 0.4 / 0.18 = 2/3)
The thresholds actually applied in statistic space are written to the output.

WHICH STEPS. Chosen steps (t >= 1). Each is filed into one of three states, predator first (a01's
precedence): a live predator within NEAR squares (Chebyshev) -> "predator near"; else a live rabbit
within NEAR -> "rabbit near"; else "nothing near". Computed twice in the one sweep:
    prev_row  distances on the row the action was chosen from (t-1)  -- PRIMARY (study Revision 3)
    same_row  distances on row t, as a01's falsealarm.py did        -- sensitivity + a01 reproduction

USAGE (from the repo root)
    python scripts/analysis/aimed_response.py --run results/JAX_RecurrentPPO/<run> \\
        --store-root results/trajectories --out <file.json> [--checkpoint N]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "core"))
from hiding_drivers import find_stores          # noqa: E402
import env as ENV                               # noqa: E402
import store as STORE                           # noqa: E402
import scan as SCAN                             # noqa: E402

NEAR = 2
RABBIT_LIKE_BELOW_NATS = 0.0
PREDATOR_LIKE_AT_NATS = 2.0 / 3.0
STATES = ["nothing near", "predator near", "rabbit near"]
GROUPS = ["rabbit-like", "predator-like"]
EP_COLS = ["episode_seed", "length", "animal_active", "animal_property_sampled"]
STEP_COLS = ["episode_seed", "t", "agent_in_bush", "agent_row", "agent_col",
             "animal_row", "animal_col"]


def statistic_threshold(spec, nats: float) -> float:
    """The statistic value at which the evidence equals `nats`.

    Rounded to 10 decimals so the two-channel threshold is a01's 0.3 exactly rather than
    0.30000000000000004 -- a one-ulp difference that would move episodes sitting on the boundary.
    """
    return round(spec.midpoint + nats / spec.llr_scale, 10)


def classify_state(near_pred: np.ndarray, near_rab: np.ndarray) -> np.ndarray:
    """0 nothing near, 1 predator near, 2 rabbit near (predator takes precedence)."""
    return np.where(near_pred, 1, np.where(near_rab, 2, 0))


def summarise(C: np.ndarray, B: np.ndarray) -> dict:
    """Counts C[group, state] and bush steps B[group, state] -> shares, differences, time shares."""
    share = 100 * B / np.maximum(C, 1)
    return {"steps": C.tolist(), "bush_steps": B.tolist(), "bush_share_pct": share.tolist(),
            "difference_pp": (share[1] - share[0]).tolist(),
            "time_share_pct": (100 * C / np.maximum(C.sum(1, keepdims=True), 1)).tolist()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--store-root", nargs="+", required=True)
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = yaml.safe_load(open(f"{a.run}/models/config.yaml"))
    lay = ENV.slot_layout(cfg)
    spec = ENV.scent_spec(cfg)
    P, R, na = lay["pred"], lay["neutral"], lay["n_animal"]
    if not P or not R:
        raise SystemExit("this world lacks predator or rabbit slots -- the aimed split is undefined")
    stores = find_stores(a.run, a.checkpoint, a.store_root)
    st = STORE.open_run(stores, EP_COLS)
    act = st.episode_list("animal_active", na).astype(bool)
    # float64 BEFORE the statistic, as hiding_drivers.aggregate does (a01 grouped on that value)
    prop = st.episode_property("animal_property_sampled", na).astype(np.float64)
    n_pred, n_rab = act[:, P].sum(1), act[:, R].sum(1)
    rb = act[:, R]
    stat = np.where(rb.sum(1) > 0, (spec.statistic(prop[:, R]) * rb).sum(1) / np.maximum(rb.sum(1), 1),
                    np.nan)
    thr_rab = statistic_threshold(spec, RABBIT_LIKE_BELOW_NATS)
    thr_pred = statistic_threshold(spec, PREDATOR_LIKE_AT_NATS)
    sub = (n_pred == 1) & (n_rab == 1) & np.isfinite(stat)
    grp = np.full(st.n_episodes, -1, np.int8)
    grp[sub & (stat < thr_rab)] = 0
    grp[sub & (stat >= thr_pred)] = 1

    acc = {k: {"C": np.zeros((2, 3)), "B": np.zeros((2, 3))} for k in ("prev_row", "same_row")}

    def on_shard(fr, _acc, _fi):
        g_row = grp[fr.episode_id]
        ar, ac = fr.raw("agent_row"), fr.raw("agent_col")
        AR = fr.list_raw("animal_row", na).astype(np.float64)
        AC = fr.list_raw("animal_col", na).astype(np.float64)
        near = (np.maximum(np.abs(AR - ar[:, None]), np.abs(AC - ac[:, None])) <= NEAR) \
            & act[fr.episode_id]
        pn, rn = near[:, P].any(1), near[:, R].any(1)
        state = classify_state(pn, rn & ~pn)
        rows = fr.step_rows
        g = g_row[rows]
        keep = g >= 0
        y = fr.raw("agent_in_bush")[rows][keep]
        for key, src in (("prev_row", fr.prev), ("same_row", rows)):
            k = g[keep].astype(np.int64) * 3 + state[src][keep]
            acc[key]["C"] += np.bincount(k, minlength=6).reshape(2, 3)
            acc[key]["B"] += np.bincount(k, weights=y, minlength=6).reshape(2, 3)

    t0 = time.time()
    SCAN.sweep(st, STEP_COLS, on_shard, label=os.path.basename(a.run.rstrip("/")))
    out = {"run": a.run, "stores": stores, "n_episodes": int(st.n_episodes),
           "seed_range": [int(st.seeds.min()), int(st.seeds.max())], "near": NEAR,
           "scent": spec.as_dict(), "states": STATES, "groups": GROUPS,
           "thresholds": {"rabbit_like_below_nats": RABBIT_LIKE_BELOW_NATS,
                          "predator_like_at_nats": PREDATOR_LIKE_AT_NATS,
                          "rabbit_like_below_statistic": thr_rab,
                          "predator_like_at_statistic": thr_pred},
           "group_episodes": [int((grp == 0).sum()), int((grp == 1).sum())],
           "primary": "prev_row",
           "accounting": [
               {"what": "episodes with exactly one predator and one rabbit", "used": int(sub.sum()),
                "total": int(st.n_episodes), "pct": 100 * float(sub.mean()),
                "reason": "the rabbit's scent is unambiguous and the predator count is fixed"},
               {"what": "of those, in a scent group", "used": int((grp >= 0).sum()),
                "total": int(sub.sum()), "pct": 100 * float((grp >= 0).sum() / max(sub.sum(), 1)),
                "reason": "evidence between 0 and 2/3 nat belongs to neither group"}],
           "seconds": round(time.time() - t0, 1)}
    for key in ("prev_row", "same_row"):
        out[key] = summarise(acc[key]["C"], acc[key]["B"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"written: {a.out}")
    for key in ("prev_row", "same_row"):
        d = out[key]["difference_pp"]
        print(f"  {key:9} predator-like minus rabbit-like (pp): "
              + "  ".join(f"{s} {v:+.1f}" for s, v in zip(STATES, d)))


if __name__ == "__main__":
    main()
