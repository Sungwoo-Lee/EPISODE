#!/usr/bin/env python3
"""retention_readout.py - zero-shot retention test of the May double-return replication.

Design: docs/experiments/active/continual_worlds/MAY_DOUBLE_RETURN_REPLICATION.md 5.6 (pre-registered
2026-09-29; user decision 8.1 Q5). Each run's five stage-end checkpoints were played, frozen, in both
worlds (active = hunting predator, passive = harmless) for 2,000 episodes per cell by
scripts/eval/continual_forgetting_matrix.py, once per evaluation policy:
    results/analysis/continual_worlds/retention_mayrep_<short>_<greedy|sampled>.json
(<short> = the manifest tag without `rppo_cw_mayrep_`, e.g. t1none_s42). This script reads those
matrices, never the checkpoints, and never reward.

Per run and policy: A_k = survival of the stage-k-end checkpoint in the active world;
Z_2 = A_2 - A_1, Z_4 = A_4 - A_3; per seed pair ZA_j = Z_j(mod) - Z_j(ord) (positive favours the
modulator). H-zeroshot per j: favourable if ZA_j > 0 in >= 2 of 3 pairs AND mean(Z_j mod) - mean(Z_j ord)
> 2 x SE, SE = between-seed SE floored at 5.1 steps (pilot_readout._agg_rule with MR_FLOOR_G, the same
code that computes the 5.3 verdict); unfavourable is the mirror; else inside noise. A per-pair ZA_j is
"beyond eval noise" when 0 lies outside ZA_j +- 1.96 sqrt(sum of the four cells' SE^2) (the four cells
combined as independent: conservative, since the cells share evaluation seeds). Descriptive: the
passive-world column and A_5 - A_3. Ceiling: the share of evaluation episodes that reached the
500-step cap, per cell.

Own-world diagonal check: each stage-end checkpoint on the world it was trained in, against the
training log (local WandB binary, `Episode/Steps` rows of that stage in the last 20,000 episodes up to
the checkpoint step, weighted by delta Episode/Number as in pilot_readout.Series; the cap share from
`Episode/Term_MaxSteps`). Training plays the policy sampled, so the sampled diagonal should agree with
it within noise; the greedy one need not.

The evaluation policy is not stated in 5.6. The registered command (the driver with no policy flag)
plays each saved config's `behavior_measures.eval_policy_mode`, which is `deterministic` (greedy) in
all six runs, so greedy is the registered reading; sampled is reported beside it.

Writes, per run, results/analysis/continual_worlds/retention_mayrep_<short>.{json,csv} (both policies,
one row per cell) and results/analysis/continual_worlds/retention_mayrep_readout.json (study read-out).

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      scripts/analysis/studies/continual_worlds/retention_readout.py \
      --design-doc docs/experiments/active/continual_worlds/MAY_DOUBLE_RETURN_REPLICATION.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pilot_readout as pr  # noqa: E402  (same folder; the 5.3 rule, manifest and WandB reader)

ROOT = pr.ROOT
OUT_DIR = os.path.join(ROOT, "results", "analysis", "continual_worlds")
POLICIES = {"greedy": "deterministic", "sampled": "stochastic"}
REGISTERED_POLICY = "greedy"
N_EPISODES = 2000                 # 5.6 "2,000 episodes per cell"
N_STAGES = 5
ZS_PAIRS = ((2, 1), (4, 3))       # 5.6 Z_2 = A_2 - A_1, Z_4 = A_4 - A_3 (1-indexed stages)
DIAG_WINDOW = 20_000              # training-log window for the diagonal check (episodes)

# 5.6 rule text that the constants above / pr.MR_* stand for; asserted against the doc.
ZS_PATTERNS = [
    (r"`Z_2` \| `A_2 − A_1`", "ZS_PAIRS (Z_2)"),
    (r"`Z_4` \| `A_4 − A_3`", "ZS_PAIRS (Z_4)"),
    (r"`ZA_j` \(j = 2, 4\) \| `Z_j\(mod\) − Z_j\(ord\)` \| positive favours the modulator", "ZA sign"),
    (r"\*favourable\* if `ZA_j > 0` in \*\*≥ 2 of 3\*\* seed\s+pairs \*\*and\*\* the mean `ZA_j > 2 × SE`",
     "MR_MIN_PAIRS / MR_SE_MULT"),
    (r"floored\s+at 5\.1 steps", "MR_FLOOR_G"),
    (r"2,000 episodes per cell", "N_EPISODES"),
    (r"95 % CIs, combined, do not include 0", "beyond eval noise"),
]


def check_doc(text: str) -> None:
    sec = text.split("### 5.6 Zero-shot retention test", 1)[1].split("## 6.", 1)[0]
    for pat, what in ZS_PATTERNS:
        if not re.search(pat, sec):
            raise AssertionError(f"5.6 text no longer matches {what!r} ({pat}); re-read the design before trusting this")
    pr.check_mayrep_doc(text)       # MR_FLOOR_G, MR_SE_MULT, MR_MIN_PAIRS asserted there
    if (pr.MR_FLOOR_G, pr.MR_SE_MULT, pr.MR_MIN_PAIRS) != (5.1, 2.0, 2):
        raise AssertionError("pilot_readout MR_* constants changed")


def agent_of(tag: str) -> str:
    if "_t1none_" in tag:
        return "ordinary"
    if "_t16quad_" in tag:
        return "modulated"
    raise ValueError(f"{tag}: agent token not recognised")


def short(tag: str) -> str:
    return tag.replace("rppo_cw_mayrep_", "")


def load_matrix(sh: str, label: str) -> dict:
    p = os.path.join(OUT_DIR, f"retention_mayrep_{sh}_{label}.json")
    d = json.load(open(p))
    if d["episodes_per_cell"] != N_EPISODES:
        raise ValueError(f"{p}: {d['episodes_per_cell']} episodes per cell, expected {N_EPISODES}")
    rows = d["rows"]
    if len(rows) != N_STAGES or [r["saved_stage"] for r in rows] != list(range(N_STAGES)):
        raise ValueError(f"{p}: rows {[(r['label'], r['saved_stage']) for r in rows]} are not the 5 stage ends")
    for c in d["cells"]:
        if c["eval_policy_mode"] != POLICIES[label]:
            raise ValueError(f"{p}: cell {c['row']}/{c['world']} played {c['eval_policy_mode']}, expected {POLICIES[label]}")
        if c["n"] != N_EPISODES:
            raise ValueError(f"{p}: cell {c['row']}/{c['world']} has n={c['n']}")
    return d


def cell(d: dict, k: int, world: str) -> dict:
    """Stage-k-end (1-indexed) cell in `world`."""
    lab = d["rows"][k - 1]["label"]
    return next(c for c in d["cells"] if c["row"] == lab and c["world"] == world)


def training_diag(wid: str, d: dict) -> list[dict]:
    rows, _ = pr.scan(pr.wandb_dir(wid))
    bounds = d["schedule"]["episode_boundaries"]
    out = []
    for k in range(N_STAGES):
        r = d["rows"][k]
        step = r["step"]
        start = bounds[k - 1] if k else 0
        stage_rows = [x for x in rows if int(x.get("stage/index", -1)) == k]
        ser = pr.Series(stage_rows, start)
        lo = step - DIAG_WINDOW
        out.append({"stage": k + 1, "checkpoint_step": step, "world": r["trained_through"].split("_", 1)[1],
                    "train_steps_last20k": ser.S(lo, step),
                    "train_capped_last20k": ser.mean("Episode/Term_MaxSteps", lo, step)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--design-doc", required=True)
    ap.add_argument("--no-diag", action="store_true", help="skip the training-log diagonal check")
    args = ap.parse_args()
    text = open(os.path.join(ROOT, args.design_doc) if not os.path.isabs(args.design_doc) else args.design_doc).read()
    check_doc(text)
    man = pr.parse_manifest(text, id_prefix=pr.MR_ID_PREFIX)
    if len(man) != 2 * pr.MR_N_PAIRS:
        raise ValueError(f"expected {2 * pr.MR_N_PAIRS} manifest runs, found {len(man)}")

    runs = []
    for m in man:
        sh = short(m["tag"])
        mats = {lab: load_matrix(sh, lab) for lab in POLICIES}
        if mats["greedy"]["run_dir"] != mats["sampled"]["run_dir"] or m["tag"] not in mats["greedy"]["run_dir"]:
            raise ValueError(f"{m['tag']}: matrices point at {mats['greedy']['run_dir']} / {mats['sampled']['run_dir']}")
        if mats["greedy"]["run_seed"] != m["seed"]:
            raise ValueError(f"{m['tag']}: saved seed {mats['greedy']['run_seed']} != manifest {m['seed']}")
        diag = None if args.no_diag else training_diag(m["wandb_id"], mats["greedy"])
        run = {"run": m["run"], "tag": m["tag"], "short": sh, "agent": agent_of(m["tag"]), "seed": m["seed"],
               "wandb_id": m["wandb_id"], "run_dir": mats["greedy"]["run_dir"],
               "checkpoints": [r["step"] for r in mats["greedy"]["rows"]], "policies": {}}
        flat = []
        for lab, d in mats.items():
            A = [cell(d, k, pr.MR_ACTIVE)["mean"] for k in range(1, N_STAGES + 1)]
            P = [cell(d, k, pr.MR_PASSIVE)["mean"] for k in range(1, N_STAGES + 1)]
            ASE = [cell(d, k, pr.MR_ACTIVE)["se"] for k in range(1, N_STAGES + 1)]
            pol = {"A": A, "A_se": ASE, "P": P,
                   "cap_active": [cell(d, k, pr.MR_ACTIVE)["frac_at_max_steps"] for k in range(1, N_STAGES + 1)],
                   "cap_passive": [cell(d, k, pr.MR_PASSIVE)["frac_at_max_steps"] for k in range(1, N_STAGES + 1)],
                   "Z": {j: A[j - 1] - A[i - 1] for j, i in ZS_PAIRS},
                   "Z_se": {j: math.hypot(ASE[j - 1], ASE[i - 1]) for j, i in ZS_PAIRS},
                   "A5_minus_A3": A[4] - A[2]}
            if diag is not None:
                pol["diag"] = []
                for dg in diag:
                    c = cell(d, dg["stage"], dg["world"])
                    pol["diag"].append({**dg, "eval_mean": c["mean"], "eval_ci95": 1.96 * c["se"],
                                        "eval_capped": c["frac_at_max_steps"],
                                        "eval_minus_train": c["mean"] - dg["train_steps_last20k"]})
            run["policies"][lab] = pol
            for c in d["cells"]:
                flat.append({"policy": lab, **{k: c[k] for k in ("row", "trained_through", "checkpoint_step", "world", "n",
                                                                 "mean", "sd", "se", "ci95_lo", "ci95_hi",
                                                                 "frac_at_max_steps", "max_steps", "eval_policy_mode",
                                                                 "git_commit")}})
        base = os.path.join(OUT_DIR, f"retention_mayrep_{sh}")
        json.dump({"what": "Zero-shot retention matrices (MAY_DOUBLE_RETURN_REPLICATION 5.6), both evaluation "
                           "policies; mean survival steps of the frozen stage-end checkpoints, 2,000 episodes/cell",
                   "source_matrices": {lab: f"results/analysis/continual_worlds/retention_mayrep_{sh}_{lab}.json"
                                       for lab in POLICIES},
                   **run, "cells": flat}, open(base + ".json", "w"), indent=2)
        with open(base + ".csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
            w.writeheader()
            for c in flat:
                w.writerow({k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in c.items()})
        runs.append(run)

    by = {(r["agent"], r["seed"]): r for r in runs}
    seeds = sorted({r["seed"] for r in runs})
    verdicts = {}
    for lab in POLICIES:
        vj = {}
        for j, _i in ZS_PAIRS:
            vals = {a: [by[(a, s)]["policies"][lab]["Z"][j] for s in seeds] for a in ("ordinary", "modulated")}
            pairs = []
            for s in seeds:
                po, pm = by[("ordinary", s)]["policies"][lab], by[("modulated", s)]["policies"][lab]
                za = pm["Z"][j] - po["Z"][j]
                se = math.hypot(pm["Z_se"][j], po["Z_se"][j])
                pairs.append({"seed": s, "Z_ord": po["Z"][j], "Z_mod": pm["Z"][j], "ZA": za, "eval_se": se,
                              "beyond_eval_noise": abs(za) > 1.96 * se})
            rule = pr._agg_rule(vals, [p["ZA"] for p in pairs], floor=pr.MR_FLOOR_G)
            vj[f"ZA_{j}"] = {"pairs": pairs, **rule}
        desc = {}
        for key in ("A5_minus_A3",):
            desc[key] = {a: [by[(a, s)]["policies"][lab][key] for s in seeds] for a in ("ordinary", "modulated")}
        verdicts[lab] = {"H_zeroshot": vj, "descriptive": desc}

    out = {"what": "H-zeroshot read-out (MAY_DOUBLE_RETURN_REPLICATION 5.6)",
           "registered_policy": REGISTERED_POLICY,
           "registered_policy_reason": "5.6 names no policy; the registered command plays the saved configs' "
                                       "behavior_measures.eval_policy_mode = deterministic (greedy). Sampled is reported beside it.",
           "se_floor": pr.MR_FLOOR_G, "se_mult": pr.MR_SE_MULT, "min_pairs": pr.MR_MIN_PAIRS,
           "runs": runs, "verdicts": verdicts}
    json.dump(out, open(os.path.join(OUT_DIR, "retention_mayrep_readout.json"), "w"), indent=2)

    # ---------------------------------------------------------------- print
    for lab in POLICIES:
        print(f"\n=== {lab} ({POLICIES[lab]}) -- active world A_k / passive P_k, mean steps [capped %]")
        for r in sorted(runs, key=lambda r: (r["seed"], r["agent"])):
            p = r["policies"][lab]
            a = "  ".join(f"{v:6.1f}[{c * 100:3.0f}]" for v, c in zip(p["A"], p["cap_active"]))
            q = "  ".join(f"{v:6.1f}[{c * 100:3.0f}]" for v, c in zip(p["P"], p["cap_passive"]))
            print(f"  {r['short']:<13} A: {a}\n  {'':<13} P: {q}")
        for key, v in verdicts[lab]["H_zeroshot"].items():
            print(f"  {key}: pairs " + ", ".join(f"s{p['seed']} {p['ZA']:+.1f}{'*' if p['beyond_eval_noise'] else ''}"
                                             for p in v["pairs"])
                  + f" | mean(mod)-mean(ord) {v['mean_diff']:+.1f}, SE {v['se_raw']:.1f} -> used {v['se']:.1f}"
                  + f" | {v['n_pairs_pos']}/3 pairs > 0 -> {v['verdict']}")
    if not args.no_diag:
        print("\n=== own-world diagonal: eval (greedy / sampled) vs training log last 20k eps (mean steps; capped %)")
        for r in sorted(runs, key=lambda r: (r["seed"], r["agent"])):
            for g, s in zip(r["policies"]["greedy"]["diag"], r["policies"]["sampled"]["diag"]):
                print(f"  {r['short']:<13} st{g['stage']} {g['world']:<7} greedy {g['eval_mean']:6.1f} "
                      f"sampled {s['eval_mean']:6.1f} ±{s['eval_ci95']:.1f} | train {g['train_steps_last20k']:6.1f} "
                      f"| capped g/s/train {g['eval_capped'] * 100:3.0f}/{s['eval_capped'] * 100:3.0f}/"
                      f"{(g['train_capped_last20k'] or float('nan')) * 100:3.0f}")
    print(f"\nwrote {OUT_DIR}/retention_mayrep_<short>.json/.csv and retention_mayrep_readout.json")


if __name__ == "__main__":
    main()
