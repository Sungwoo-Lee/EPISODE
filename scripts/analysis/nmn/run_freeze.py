#!/usr/bin/env python
"""Method 3 driver — replay each arm under four conditions and pair the episodes.

    live           gain live,   offset live
    freeze_gain    gain at its per-unit time-mean, offset live
    freeze_offset  gain live,   offset at its per-unit time-mean
    freeze_both    both at their per-unit time-means

Every condition replays the SAME episodes from the SAME seeds, so the result is a
distribution of per-episode paired differences in survival steps rather than a
difference of two means. The per-unit means are computed from this arm's own live
pass over exactly those episodes.

The weight-edit equivalence is verified on the first modulated arm before any
condition is replayed, and the frozen signal is re-checked for constancy inside
every frozen rollout. A failure of either aborts the sweep: every number the method
produces rests on that identity.

    python scripts/analysis/nmn/run_freeze.py --episodes 128 \
        --out results/analysis/nmn_representation/freeze_at_mean
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

from scripts.analysis.nmn import ckpt_io, freeze, replay   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-root", default="results/JAX_RecurrentPPO")
    ap.add_argument("--out", default="results/analysis/nmn_representation/freeze_at_mean")
    ap.add_argument("--episodes", type=int, default=128)
    ap.add_argument("--seed-base", type=int, default=90_000)
    ap.add_argument("--slices", nargs="+", default=["ALL"],
                    help="modulator input slices to include (the control has none)")
    ap.add_argument("--grids", nargs="+", default=["nmnsite", "nmngaenorm"])
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = replay.episode_seeds(args.episodes, args.seed_base)
    wanted = set(args.slices)

    runs = [r for r in ckpt_io.discover_runs(args.results_root, tuple(args.grids))
            if (not r.modulated) or (r.input_slice in wanted)]
    print(f"[freeze] {len(runs)} runs "
          f"({sum(r.modulated for r in runs)} modulated + "
          f"{sum(not r.modulated for r in runs)} controls), "
          f"{len(seeds)} paired episodes", flush=True)

    rows: list[dict] = []
    lengths_out: dict[str, np.ndarray] = {}
    equivalence: dict = {}
    t0 = time.time()

    for run in runs:
        agent = replay.load_agent(run.models_dir)
        live = replay.rollout(agent, seeds)
        live_len = live["lengths"]
        lengths_out[f"{run.tag}/live"] = live_len

        base = dict(grid=run.grid, arm=run.arm, input_slice=run.input_slice or "",
                    tag=run.tag, step=agent.step, label=run.label,
                    modulated=run.modulated,
                    sites=";".join(sorted(live["gamma"])))
        rows.append({**base, "condition": "live",
                     **freeze.paired_differences(live_len, live_len)})

        if not run.modulated:
            print(f"[freeze] {run.tag}: control, survival {live_len.mean():.1f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
            continue

        means = freeze.per_unit_time_means(live)

        # --- the load-bearing check, once, on the first modulated arm -------------
        if not equivalence:
            equivalence = freeze.verify_freeze_equivalence(
                lambda: replay.load_agent(run.models_dir), means, sorted(means))
            equivalence["arm"] = run.tag
            print(f"[freeze] weight-edit equivalence verified on {run.tag}: "
                  f"worst deviation {equivalence['worst_deviation']}", flush=True)

        for cond, (fg, fo) in (("freeze_gain", (True, False)),
                               ("freeze_offset", (False, True)),
                               ("freeze_both", (True, True))):
            fa = replay.load_agent(run.models_dir)        # fresh weights every time
            edited = freeze.apply_freeze(fa.model, means, freeze_gain=fg,
                                         freeze_offset=fo)
            out = replay.rollout(fa, seeds)

            # In-sweep constancy check: whatever was frozen must be bit-constant in
            # the REPLAY, not merely in a probe. Catches an edit that failed to take.
            v = out["valid"]
            for site in out["gamma"]:
                for what, arr, on in (("gamma", out["gamma"][site], fg),
                                      ("beta", out["beta"][site], fo)):
                    if not on:
                        continue
                    spread = float(np.ptp(arr[v], axis=0).max())
                    if spread != 0.0:
                        raise AssertionError(
                            f"{run.tag}/{cond}: frozen {what} at site {site} still "
                            f"varies during the replay (max range {spread}). The "
                            f"weight edit did not take.")
                    dev = float(np.abs(arr[v] - means[site][what][None, :]).max())
                    if dev != 0.0:
                        raise AssertionError(
                            f"{run.tag}/{cond}: frozen {what} at {site} is constant "
                            f"but not at the requested mean (deviation {dev}).")

            lengths_out[f"{run.tag}/{cond}"] = out["lengths"]
            rows.append({**base, "condition": cond, "n_params_edited": len(edited),
                         **freeze.paired_differences(live_len, out["lengths"])})

        r = {x["condition"]: x for x in rows if x["tag"] == run.tag}
        print(f"[freeze] {run.tag}: live {live_len.mean():.1f} | "
              f"dgain {r['freeze_gain']['mean_diff']:+.2f} "
              f"({r['freeze_gain']['frac_episodes_changed']:.0%} changed) | "
              f"doffset {r['freeze_offset']['mean_diff']:+.2f} "
              f"({r['freeze_offset']['frac_episodes_changed']:.0%}) | "
              f"dboth {r['freeze_both']['mean_diff']:+.2f} "
              f"({r['freeze_both']['frac_episodes_changed']:.0%}) "
              f"({time.time() - t0:.0f}s)", flush=True)

    lead = ["grid", "arm", "input_slice", "tag", "condition", "modulated", "sites"]
    seen: list[str] = []
    for r in rows:
        for k in r:
            if k not in lead and k not in seen:
                seen.append(k)
    with open(out_dir / "paired_differences.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=lead + seen, restval="")
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(out_dir / "episode_lengths.npz", **lengths_out)
    with open(out_dir / "manifest.json", "w") as fh:
        json.dump({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "n_episodes": len(seeds), "seed_base": args.seed_base,
                   "slices": sorted(wanted), "grids": args.grids,
                   "conditions": list(freeze.CONDITIONS),
                   "metric": "survival steps (argmax(done) + 1); never cumulative reward",
                   "policy": "greedy (argmax); perceptual noise off in these runs",
                   "equivalence_check": equivalence,
                   "runs": [r.tag for r in runs]}, fh, indent=2)
    print(f"[freeze] wrote {len(rows)} rows -> {out_dir/'paired_differences.csv'} "
          f"in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
