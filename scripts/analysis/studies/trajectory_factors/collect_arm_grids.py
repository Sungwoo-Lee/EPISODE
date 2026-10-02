#!/usr/bin/env python3
"""collect_arm_grids.py - run Figures 12 and 13's cross-tabs across all ten rest-premium agents.

Figures 12 and 13 are computed for a01 alone, by two separate scripts that each scan the store and
print to stdout:

    supplementary/injdeep.py   nociception(t-1) x prior-hit-count      -> Figure 12
    supplementary/timectrl.py  elapsed-step bin x injury bin           -> Figure 13

Both are hardcoded to `*_a01_*`. This runs the same two grids over every arm, in ONE pass per store
rather than two, and writes JSON instead of printing - so the question "does a01's pattern hold in
the other nine?" can be asked at all.

THE DEFINITIONS ARE COPIED, NOT REINVENTED. Bin edges, masks, the nociception kernel, the t-1 shift
and the predator-near test are taken from those two scripts line for line, because the point is to
compare arms on one measure rather than to improve the measure. `--gate` checks that: it recomputes
a01 and compares against the grids already embedded in the published page. If a01 does not
reproduce, this script is wrong and its other nine numbers mean nothing.
"""
from __future__ import annotations
import glob, json, os, re, sys, time
import numpy as np
import pyarrow.parquet as pq

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
OUT = "results/analysis/trajectory_factors/arm_grids"

KL, TAU = 12, 3.0                              # injdeep.py: interoceptive kernel
_k = np.arange(KL, dtype=np.float64)
KER = ((_k / TAU) * np.exp(1.0 - _k / TAU))
KER = KER / KER.sum()
PE = [1e-9, 8, 18, 32, 50]                     # 6 nociception bins   (injdeep)
HB = [1, 2, 3, 5]                              # 5 prior-hit bins     (injdeep)
TB = [0, 10, 25, 50, 100, 200, 500]            # 6 elapsed-step bins  (timectrl)
IBE = [1e-9, 25.0, 50.0]                       # 4 injury bins        (timectrl)
PRED, NEAR = [0, 1], 2                         # injdeep: predator slots, Chebyshev radius


def store_for(arm: str) -> str:
    hits = sorted(glob.glob(f"results/trajectories/*_{arm}_*/*/*/"))
    if not hits:
        raise SystemExit(f"no trajectory store for {arm}")
    return hits[0]


def one_arm(arm: str, limit: int | None = None) -> dict:
    S = store_for(arm)
    ep = pq.read_table(sorted(glob.glob(S + "episodes_*.parquet")),
                       columns=["episode_seed", "animal_active"])
    seeds = ep.column("episode_seed").to_numpy()
    order = np.argsort(seeds)
    AACT = np.array(ep.column("animal_active").to_pylist(), bool)[order]
    SEED0 = int(seeds.min())                   # derived, not assumed to be 1,000,000

    g1n = np.zeros((6, 5)); g1b = np.zeros((6, 5))
    g2n = np.zeros((6, 4)); g2b = np.zeros((6, 4))

    def L2(c, w):
        ch = c.chunks if hasattr(c, "chunks") else [c]
        return np.concatenate([x.flatten().to_numpy(zero_copy_only=False)
                               for x in ch]).reshape(-1, w)

    files = sorted(glob.glob(S + "steps_*.parquet"))
    if limit:
        files = files[:limit]
    t0 = time.time()
    for fi, f in enumerate(files):
        tb = pq.read_table(f, columns=["episode_seed", "t", "agent_in_bush", "injury_level",
                                       "damage", "agent_row", "agent_col",
                                       "animal_row", "animal_col"])
        sd = tb.column("episode_seed").to_numpy()
        t = tb.column("t").to_numpy(); N = len(t)
        inj = tb.column("injury_level").to_numpy(zero_copy_only=False).astype(np.float64)
        bu = tb.column("agent_in_bush").to_numpy(zero_copy_only=False).astype(np.float64)
        dmg = tb.column("damage").to_numpy(zero_copy_only=False).astype(np.float64)
        st = np.flatnonzero(t == 0); ends = np.append(st[1:], N)
        estart = np.repeat(st, ends - st); idx = np.arange(N)

        # --- grid 1, Figure 12 -------------------------------------------------------------
        noci = np.zeros(N)
        for j in range(1, KL):
            src = idx - j; ok = src > estart
            noci[ok] += KER[j] * inj[src[ok]]
        nprev = np.zeros(N); nprev[1:] = noci[:-1]; nprev[idx == estart] = 0.0
        hit = dmg > 0
        cs = np.cumsum(hit); base = np.where(estart > 0, cs[estart - 1], 0)
        nhits = cs - base
        nprevhits = np.zeros(N, np.int64); nprevhits[1:] = nhits[:-1]
        nprevhits[idx == estart] = 0
        ar = tb.column("agent_row").to_numpy(); ac = tb.column("agent_col").to_numpy()
        AR = L2(tb.column("animal_row"), 4); AC = L2(tb.column("animal_col"), 4)
        pn = ((np.maximum(np.abs(AR - ar[:, None]), np.abs(AC - ac[:, None])) <= NEAR)
              & AACT[sd - SEED0])[:, PRED].any(1)
        m1 = (t >= 2) & (~pn)
        k1 = np.digitize(nprev[m1], PE) * 5 + np.digitize(nprevhits[m1], HB)
        g1n += np.bincount(k1, minlength=30).reshape(6, 5)
        g1b += np.bincount(k1, weights=bu[m1], minlength=30).reshape(6, 5)

        # --- grid 2, Figure 13 -------------------------------------------------------------
        m2 = t >= 1
        tbin = np.clip(np.digitize(t[m2], TB[1:-1]), 0, 5)
        k2 = tbin * 4 + np.digitize(inj[m2], IBE)
        g2n += np.bincount(k2, minlength=24).reshape(6, 4)
        g2b += np.bincount(k2, weights=bu[m2], minlength=24).reshape(6, 4)

        if fi % 50 == 0:
            print(f"    {arm} shard {fi}/{len(files)} ({time.time()-t0:.0f}s)", flush=True)

    pct = lambda b, n: (100.0 * b / np.maximum(n, 1)).round(3).tolist()
    return {"arm": arm, "store": S, "shards": len(files),
            "noci_by_hits": {"pct": pct(g1b, g1n), "n": g1n.tolist()},
            "inj_by_time":  {"pct": pct(g2b, g2n), "n": g2n.tolist()}}


PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"


def gate(limit=None):
    """Recompute a01 and compare against the grids already published on the page.

    This is the only thing standing between "ten arms compared on one measure" and "ten arms
    compared on a measure I invented while porting". If a01 does not reproduce, the other nine
    numbers are meaningless.
    """
    import re as _re
    html = open(PAGE, encoding="utf-8").read()
    D = json.loads(_re.search(r"const D=(\{.*?\});\n", html, _re.S).group(1))
    got = one_arm("a01", limit=limit)

    # A partial run is a smoke test, not a gate: with a fraction of the shards the percentages
    # carry sampling noise and the counts are simply smaller. Loosen the one and skip the other,
    # and say so, rather than reporting a failure that is really "you asked for less data".
    partial = limit is not None
    tol = 1.5 if partial else 0.05
    if partial:
        print(f"  PARTIAL RUN ({limit} of 200 shards) - smoke test only, tolerance {tol} pp, "
              f"counts not checked")
    ok = True
    want1 = np.array(D["hits"]["hide"], float)
    mine1 = np.array(got["noci_by_hits"]["pct"], float)
    d1 = np.abs(want1 - mine1).max()
    print(f"  Figure 12 grid: largest cell difference {d1:.3f} pp")
    if d1 > tol:
        ok = False
        print("    published:", want1.round(1).tolist())
        print("    recomputed:", mine1.round(1).tolist())

    want2 = np.array(D["timectrl"]["inj"], float)
    mine2 = np.array(got["inj_by_time"]["pct"], float)
    d2 = np.abs(want2 - mine2).max()
    print(f"  Figure 13 grid: largest cell difference {d2:.3f} pp")
    if d2 > tol:
        ok = False
        print("    published:", want2.round(1).tolist())
        print("    recomputed:", mine2.round(1).tolist())

    # the step counts the page stores are per-episode; 1e6 episodes -> absolute steps
    if not partial:
        want_n = np.array(D["hits"]["n"], float) * 1e6
        mine_n = np.array(got["noci_by_hits"]["n"], float)
        rel = np.abs(want_n - mine_n) / np.maximum(want_n, 1)
        print(f"  Figure 12 counts: largest relative difference {rel.max()*100:.2f}%")
        if rel.max() > 0.01:
            ok = False

    print("\n  GATE PASSED" if ok else "\n  GATE FAILED - do not trust the other arms")
    return ok, got


def main():
    args = sys.argv[1:]
    limit = None
    for a in args:
        if a.startswith("--shards="):
            limit = int(a.split("=")[1])
    if "--gate" in args:
        ok, got = gate(limit)
        if ok and limit is None:
            os.makedirs(OUT, exist_ok=True)
            json.dump(got, open(f"{OUT}/a01.json", "w"), indent=1)
            print(f"  wrote {OUT}/a01.json")
        sys.exit(0 if ok else 1)

    arms = [a for a in args if re.fullmatch(r"a\d\d", a)] or \
           [f"a{i:02d}" for i in range(1, 11)]
    os.makedirs(OUT, exist_ok=True)
    for arm in arms:
        p = f"{OUT}/{arm}.json"
        if os.path.exists(p) and "--force" not in args:
            print(f"  {arm}: already collected, skipping"); continue
        t0 = time.time()
        got = one_arm(arm, limit=limit)
        json.dump(got, open(p, "w"), indent=1)
        print(f"  {arm}: wrote {p} ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
