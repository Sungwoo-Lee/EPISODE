#!/usr/bin/env python
"""Summarise `bounds.csv` from `run_spectral_bound.py` into readable tables.

Two tables, because the question has two halves:

1. **Final checkpoint** — one row per run per site: the reachable swing of the gain
   and the offset, the modulator's Lipschitz bound, and the ceiling on the change in
   the policy's logits / the critic's value.
2. **Trajectory** — how each run's headline bound moved across its 50 checkpoints:
   first value, minimum, maximum, last value, and last/first as a ratio.

Nothing here decides anything. It prints what was computed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

#: The single number per (run, site) used for the trajectory table. The gain's
#: mean reachable swing is chosen over the output-change bound because it is the
#: tightest link in the chain (exact, given only that the modulator state lies in
#: the open unit cube) and is on a directly interpretable scale: a gain is a
#: multiplier, so a swing of 10 means "this unit's multiplier can differ by 10
#: between two contexts".
HEADLINE = "gamma_swing_mean"


def _fmt(df: pd.DataFrame) -> str:
    return df.to_string(index=False, float_format=lambda v: f"{v:,.3f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="results/analysis/nmn_representation/"
                                     "spectral_bound/bounds.csv")
    ap.add_argument("--out", default=None, help="write the tables here as well as stdout")
    args = ap.parse_args()

    d = pd.read_csv(args.csv)
    d["input_slice"] = d["input_slice"].fillna("")
    n_ck = d.groupby("tag")["step"].nunique()

    lines: list[str] = []
    lines.append(f"source: {args.csv}")
    lines.append(f"{d.tag.nunique()} modulated runs x {int(n_ck.min())}-{int(n_ck.max())} "
                 f"checkpoints x site(s) = {len(d)} rows")
    lines.append("")

    # --- Table 1: final checkpoint ------------------------------------------------
    last = d.loc[d.groupby(["tag", "site"])["step"].idxmax()].copy()
    cols = ["grid", "arm", "input_slice", "site",
            "gamma_swing_mean", "gamma_swing_max", "gamma_const_mean",
            "beta_swing_mean", "beta_const_mean",
            "lipschitz_gamma", "bound_dlogits", "bound_dvalue"]
    lines.append("=" * 100)
    lines.append("TABLE 1 -- final checkpoint (step ~10,000,000)")
    lines.append("  gamma_swing_*   width of the reachable interval of ONE gain unit "
                 "(dimensionless multiplier)")
    lines.append("  *_const_mean    the context-independent part (a gauge quantity -- "
                 "absorbable into the layer)")
    lines.append("  lipschitz_gamma bound on ||d gamma / d observation||, carry fixed "
                 "(Marquis reports 3.73-28.38)")
    lines.append("  bound_d*        worst-case change in the policy logits / critic value "
                 "over ALL reachable states")
    lines.append("=" * 100)
    lines.append(_fmt(last[cols].sort_values(["grid", "arm", "input_slice", "site"])))
    lines.append("")

    # --- Table 2: trajectory ------------------------------------------------------
    rows = []
    for (tag, site), g in d.sort_values("step").groupby(["tag", "site"]):
        v = g[HEADLINE].to_numpy()
        r0 = g.iloc[0]
        rows.append({
            "grid": r0.grid, "arm": r0.arm, "input_slice": r0.input_slice, "site": site,
            "n_ckpt": len(v), "first": v[0], "min": v.min(), "max": v.max(),
            "last": v[-1], "last/first": v[-1] / v[0],
            "argmin_frac": float(g.frac_of_training.to_numpy()[int(v.argmin())]),
            "monotone_up": bool(np.all(np.diff(v) > 0)),
        })
    traj = pd.DataFrame(rows).sort_values(["grid", "arm", "input_slice", "site"])
    lines.append("=" * 100)
    lines.append(f"TABLE 2 -- trajectory of `{HEADLINE}` across all checkpoints")
    lines.append("  argmin_frac = where in training the minimum fell (0 = start, 1 = end)")
    lines.append("=" * 100)
    lines.append(_fmt(traj))
    lines.append("")

    # --- The screening question this method exists to answer ----------------------
    lines.append("=" * 100)
    lines.append("SCREEN: is any run's modulation bounded near zero?")
    lines.append("=" * 100)
    worst = last.nsmallest(5, "gamma_swing_mean")[
        ["grid", "arm", "input_slice", "site", "gamma_swing_mean", "gamma_const_mean"]]
    lines.append("five smallest final gain swings:")
    lines.append(_fmt(worst))
    floor = float(last.gamma_swing_mean.min())
    lines.append("")
    lines.append(f"smallest mean reachable gain swing anywhere in the grid: {floor:.3f}")
    lines.append("A swing of 0 would mean the gain cannot vary with context at all.")

    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n")
        print(f"\n[report] written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
