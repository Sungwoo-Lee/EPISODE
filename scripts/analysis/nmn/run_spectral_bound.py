#!/usr/bin/env python
"""Sweep every checkpoint of the modulation-site grids and emit method-1 bounds.

Plain-language purpose: for each of the 32 finished training runs, and for each of
the 50 weight snapshots each run saved, work out a ceiling on how far the
neuromodulator could possibly move the network's output. Weights only -- no rollout,
no environment, no GPU. The maths and every assumption behind it live in
``spectral_bound.py``; this file is only the driver.

Usage
-----
    python scripts/analysis/nmn/run_spectral_bound.py \
        --out results/analysis/nmn_representation/spectral_bound

Writes ``bounds.csv`` (one row per run x checkpoint x site) and ``manifest.json``
(what was read, so a reader can see the coverage rather than assume it).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from scripts.analysis.nmn import ckpt_io, spectral_bound   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-root", default="results/JAX_RecurrentPPO")
    ap.add_argument("--out", default="results/analysis/nmn_representation/spectral_bound")
    ap.add_argument("--grids", nargs="+", default=["nmnsite", "nmngaenorm"])
    ap.add_argument("--final-only", action="store_true",
                    help="Only the last checkpoint of each run (a fast smoke pass).")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = ckpt_io.discover_runs(args.results_root, tuple(args.grids))
    print(f"[spectral] {len(runs)} runs discovered under {args.results_root}", flush=True)

    rows: list[dict] = []
    manifest: list[dict] = []
    t0 = time.time()

    for run in runs:
        cfg = ckpt_io.run_config(run.models_dir)
        agent_cfg = cfg["agent"]
        sites = spectral_bound.enabled_sites(agent_cfg)
        steps = ckpt_io.list_steps(run.models_dir)
        used = steps[-1:] if args.final_only else steps
        manifest.append({
            "tag": run.tag, "grid": run.grid, "arm": run.arm,
            "input_slice": run.input_slice, "label": run.label,
            "return_mode": agent_cfg.get("return_mode"),
            "modulation_type": (agent_cfg.get("modulation") or {}).get("type"),
            "sites_enabled": sites,
            "checkpoints_available": len(steps),
            "checkpoints_used": len(used),
            "first_step": steps[0], "last_step": steps[-1],
        })
        if not sites:
            print(f"[spectral] {run.tag}: unmodulated control — no heads to score.",
                  flush=True)
            continue

        for i, step in enumerate(used):
            params = ckpt_io.load_params(run.models_dir, step)
            for r in spectral_bound.checkpoint_bounds(params, agent_cfg):
                r.update(tag=run.tag, grid=run.grid, arm=run.arm,
                         input_slice=run.input_slice or "", step=step,
                         step_index=steps.index(step),
                         frac_of_training=(steps.index(step) + 1) / len(steps))
                rows.append(r)
        print(f"[spectral] {run.tag}: {len(used)} checkpoints x {len(sites)} sites "
              f"({time.time() - t0:.0f}s elapsed)", flush=True)

    if not rows:
        raise SystemExit("no rows produced — every discovered run was unmodulated?")

    lead = ["grid", "arm", "input_slice", "tag", "step", "step_index",
            "frac_of_training", "site"]
    seen: list[str] = []
    for r in rows:                       # sites emit slightly different column sets
        for k in r:                      # (only the encoder carries task_gru_lipschitz)
            if k not in lead and k not in seen:
                seen.append(k)
    cols = lead + seen
    with open(out_dir / "bounds.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(rows)
    with open(out_dir / "manifest.json", "w") as fh:
        json.dump({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results_root": args.results_root,
                   "final_only": args.final_only,
                   "runs": manifest}, fh, indent=2)

    print(f"[spectral] wrote {len(rows)} rows -> {out_dir/'bounds.csv'} "
          f"in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
