#!/usr/bin/env python
"""Injury dose-response in a run's own training world, from a trajectory store (run-agnostic).

Plain-language purpose: how does what the agent does change with how injured it is, in ten-point
steps rather than quarters? Three behaviours per decision — being in the bush, choosing Rest, and
choosing a move — plus the BUSH-EXIT rate: of the decisions taken in the bush with no animal within
reach, the share after which the agent is out of the bush (leaving is set by injury if it waits to
heal). Each is split by whether a predator is within reach.

Two readings, never pooled (they answer different questions):
  randomised  binned by the episode's STARTING injury, decisions 2..EARLY only. The start is drawn at
              random in training worlds that randomise it (levels 03+), so this reading is causal.
              Skipped, and said so, when the run's world does not randomise the start.
  felt        binned by the felt injury the agent received for that decision — the interoceptive
              signal reconstructed exactly as `context_dependence.py` does (alpha kernel over the
              injury history, reset row excluded) — over every decision. Observational: a currently
              injured agent has usually just been attacked.

Conventions shared with `context_dependence.py` (imported, not restated): row `t` holds the state at
t and the action that ARRIVED there, so the decision in row t was taken on row t-1's state
(TRAJECTORY_STORE_SCHEMA.md §1); `NEAR_D`, `EARLY`, `MOVE_ACTIONS`, the kernel and the store helpers.
Survival steps, never reward. Writes counts (numerator, denominator) so any later pooling or
checkpoint comparison works from the raw tallies.

  python scripts/analysis/injury_dose_store.py --run results/JAX_RecurrentPPO/<run> \\
      --store-root results/trajectories_basicq2_w2 [--checkpoint STEP] --out <file>.json
"""
from __future__ import annotations
import argparse, json, os, sys, time
import numpy as np, pyarrow.parquet as pq, yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import context_dependence as CD                                   # noqa: E402
from hiding_drivers import slot_layout, find_stores, listcol      # noqa: E402

EDGES = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]     # ten bins: 0-10 ... 90-100
REST_ACTION = 4                                                     # checked against `rested` below
MEASURES = ("bush", "rest", "move", "exit")


def scan(stores, lay, kernel, randomised, verbose=True):
    nb = len(EDGES) + 1
    # tallies[reading][measure] -> (2 predator-near, nb bins, 2 = [numerator, denominator])
    T = {r: {m: np.zeros((2, nb, 2)) for m in MEASURES} for r in ("randomised", "felt")}
    diag = {"rest_code_mismatch": 0, "rows": 0, "episodes": 0}
    na = lay["n_animal"]; P = lay["pred"]
    seed0, act_mask = CD._episode_side(stores, lay)
    files = CD.shard_files(stores, "steps"); t0 = time.time()
    cols = ["episode_seed", "t", "action", "rested", "agent_in_bush", "injury_level",
            "agent_row", "agent_col", "animal_row", "animal_col"]
    for fi, f in enumerate(files):
        tb = pq.read_table(f, columns=cols)
        sd = tb.column("episode_seed").to_numpy(); t = tb.column("t").to_numpy(); N = len(t)
        a = tb.column("action").to_numpy()
        rested = tb.column("rested").to_numpy(zero_copy_only=False)
        bu = tb.column("agent_in_bush").to_numpy(zero_copy_only=False).astype(bool)
        inj = tb.column("injury_level").to_numpy(zero_copy_only=False).astype(np.float64)
        ar = tb.column("agent_row").to_numpy(); ac = tb.column("agent_col").to_numpy()
        st = np.flatnonzero(t == 0); ends = np.append(st[1:], N)
        estart = np.repeat(st, ends - st); idx = np.arange(N)
        sig = np.zeros(N)
        for j in range(1, len(kernel)):
            src = idx - j; ok = src > estart
            sig[ok] += kernel[j] * inj[src[ok]]
        start_inj = np.repeat(inj[st], ends - st)
        AR = listcol(tb.column("animal_row"), na); AC = listcol(tb.column("animal_col"), na)
        near = (np.maximum(np.abs(AR - ar[:, None]), np.abs(AC - ac[:, None])) <= CD.NEAR_D) \
            & act_mask[sd - seed0]
        pred_near = near[:, P].any(1); any_near = near.any(1)

        d = idx[(t >= 1)]                      # decision rows; the state they were taken on is d-1
        s = d - 1
        diag["rest_code_mismatch"] += int(((a[d] == REST_ACTION) != rested[d]).sum())
        diag["rows"] += len(d); diag["episodes"] += len(st)
        vals = {"bush": (bu[s], np.ones(len(d), bool)),
                "rest": (a[d] == REST_ACTION, np.ones(len(d), bool)),
                "move": (np.isin(a[d], CD.MOVE_ACTIONS), np.ones(len(d), bool)),
                "exit": (~bu[d], bu[s] & ~any_near[s])}
        pn = pred_near[s].astype(np.int64)
        for reading, keep, x in (("felt", np.ones(len(d), bool), sig[s]),
                                 ("randomised", (t[d] >= 2) & (t[d] <= CD.EARLY), start_inj[d])):
            if reading == "randomised" and not randomised:
                continue
            b = np.digitize(x, EDGES)
            for m, (num, den) in vals.items():
                k = keep & den
                kk = pn[k] * nb + b[k]
                T[reading][m][..., 0] += np.bincount(kk, weights=num[k], minlength=2 * nb).reshape(2, nb)
                T[reading][m][..., 1] += np.bincount(kk, minlength=2 * nb).reshape(2, nb)
        if verbose and fi % 50 == 0:
            print(f"  shard {fi}/{len(files)} ({time.time() - t0:.0f}s)", flush=True)
    if diag["rest_code_mismatch"]:
        raise SystemExit(f"action {REST_ACTION} disagrees with `rested` on {diag['rest_code_mismatch']} "
                         "rows -- the Rest action code is not the one this script assumes")
    return T, diag


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--store-root", required=True, nargs="+")
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-blocks", type=int, default=None,
                    help="read only the first N blocks of each store (a quick test; recorded in the output)")
    a = ap.parse_args()
    CD._MAX_BLOCKS = a.max_blocks
    cfg = yaml.safe_load(open(f"{a.run}/models/config.yaml"))
    lay = slot_layout(cfg)
    KL = int(cfg["sensory"]["interoceptive_kernel_length"])
    TAU = float(cfg["sensory"]["interoceptive_kernel_tau"])
    k = np.arange(KL, dtype=np.float64); raw = (k / TAU) * np.exp(1.0 - k / TAU)
    kernel = raw / raw.sum()
    randomised = bool(cfg["body"]["random_start_injury"])
    stores = find_stores(a.run, a.checkpoint, a.store_root)
    print(f"run {a.run}\nstores {stores}\nrandomised start injury: {randomised}")
    T, diag = scan(stores, lay, kernel, randomised)
    out = {"run": a.run, "stores": stores, "checkpoint": a.checkpoint, "edges": EDGES,
           "randomised_start": randomised, "early": CD.EARLY, "near_d": CD.NEAR_D,
           "max_blocks": a.max_blocks, "kernel_tau": TAU, "kernel_len": KL, "diag": diag,
           "tallies": {r: {m: v.tolist() for m, v in d.items()} for r, d in T.items()
                       if r == "felt" or randomised},
           "layout": "tallies[reading][measure][predator_near 0/1][bin][numerator, denominator]"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"))
    for r in out["tallies"]:
        for m in MEASURES:
            v = np.asarray(out["tallies"][r][m]); num, den = v[..., 0].sum(0), v[..., 1].sum(0)
            print(f"  {r:10} {m:5} " + " ".join(f"{100 * n / max(dd, 1):5.1f}" for n, dd in zip(num, den)))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
