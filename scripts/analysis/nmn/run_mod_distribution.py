#!/usr/bin/env python
"""Method 2 driver — replay every modulated arm and describe its gains and offsets.

Every arm is replayed on the SAME fixed episode set, so the arms are paired and the
comparison between them is not confounded by which worlds each happened to see.

    python scripts/analysis/nmn/run_mod_distribution.py --episodes 128 \
        --out results/analysis/nmn_representation/mod_distribution

Writes `distributions.csv` (one row per arm x site), `histograms.json`,
`per_unit_means.npz` (each site's per-unit time-averaged gain and offset -- the
quantity method 3 freezes) and `manifest.json`.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from scripts.analysis.nmn import ckpt_io, mod_distribution as md, replay  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-root", default="results/JAX_RecurrentPPO")
    ap.add_argument("--out", default="results/analysis/nmn_representation/mod_distribution")
    ap.add_argument("--episodes", type=int, default=128)
    ap.add_argument("--seed-base", type=int, default=90_000)
    ap.add_argument("--grids", nargs="+", default=["nmnsite", "nmngaenorm"])
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these run tags")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = replay.episode_seeds(args.episodes, args.seed_base)

    runs = ckpt_io.discover_runs(args.results_root, tuple(args.grids))
    if args.only:
        runs = [r for r in runs if r.tag in set(args.only)]

    rows: list[dict] = []
    hists: dict = {}
    per_unit: dict = {}
    survival: list[dict] = []
    t0 = time.time()

    for run in runs:
        agent = replay.load_agent(run.models_dir)
        out = replay.rollout(agent, seeds)
        valid = out["valid"]
        lengths = out["lengths"]

        survival.append({
            "tag": run.tag, "grid": run.grid, "arm": run.arm,
            "input_slice": run.input_slice or "", "step": agent.step,
            "modulated": run.modulated,
            "mean_survival_steps": float(lengths.mean()),
            "median_survival_steps": float(np.median(lengths)),
            "n_episodes": len(seeds),
            "n_truncated_at_max_steps": int((lengths >= out["max_steps"]).sum()),
        })

        if out["mod_h"] is not None:
            # Cross-check on method 1's assumption A1: the modulator's state cannot
            # leave the unit cube. Measured, not re-derived.
            #
            # The comparison is against 1.0 INCLUSIVE. In exact arithmetic the state
            # is strictly inside the cube, but in float32 `tanh` saturates to exactly
            # 1.0 for arguments beyond about 9, and the update gate saturates to
            # exactly 0.0 or 1.0, so a corner is attainable numerically. Method 1's
            # bound is stated on the CLOSED cube (swing = 2 * sum of absolute column
            # weights, i.e. two states at opposite corners), so a measured 1.0
            # confirms the bound rather than breaking it -- but anything ABOVE 1
            # would mean the convexity argument itself is wrong, and every method-1
            # number with it.
            h_max = float(np.abs(out["mod_h"][valid]).max())
            if h_max > 1.0:
                raise AssertionError(
                    f"{run.tag}: modulator hidden state reached |h| = {h_max} > 1, "
                    f"which contradicts the GRU convexity argument the method-1 bound "
                    f"rests on. Method 1's numbers would be invalid.")
        else:
            h_max = float("nan")

        for site in sorted(out["gamma"]):
            g, b = out["gamma"][site], out["beta"][site]
            r = md.summarise_site(g, b, valid)
            r.update(grid=run.grid, arm=run.arm, input_slice=run.input_slice or "",
                     tag=run.tag, site=site, step=agent.step,
                     mean_survival_steps=float(lengths.mean()),
                     mod_h_max_abs=h_max)
            rows.append(r)
            key = f"{run.grid}/{run.arm}_{run.input_slice}/{site}"
            hists[key] = {"gamma": md.histogram(g, valid, lo=-4.0, hi=4.0),
                          "beta": md.histogram(b, valid, lo=-6.0, hi=6.0)}
            per_unit[f"{key}/gamma_mean"] = g[valid].mean(axis=0)
            per_unit[f"{key}/beta_mean"] = b[valid].mean(axis=0)

        print(f"[dist] {run.tag}: {len(out['gamma'])} site(s), "
              f"survival {lengths.mean():.1f} steps, |h|max {h_max:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    if not rows:
        raise SystemExit("no modulated arms matched")

    lead = ["grid", "arm", "input_slice", "tag", "site", "step"]
    cols = lead + [k for k in rows[0] if k not in lead]
    with open(out_dir / "distributions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(rows)
    with open(out_dir / "histograms.json", "w") as fh:
        json.dump(hists, fh)
    np.savez_compressed(out_dir / "per_unit_means.npz", **per_unit)
    with open(out_dir / "manifest.json", "w") as fh:
        json.dump({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "n_episodes": len(seeds), "seed_base": args.seed_base,
                   "seeds_first": seeds[0], "seeds_last": seeds[-1],
                   "policy": "greedy (argmax); perceptual noise off in these runs",
                   "survival": survival}, fh, indent=2)
    print(f"[dist] wrote {len(rows)} rows -> {out_dir/'distributions.csv'} "
          f"in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
