#!/usr/bin/env python3
"""probes.py - the data layer of the probe-scene section (Figure 7) of the Basic Behaviour page.

Pre-stated reading: docs/experiments/active/hypervigilance/SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md,
section "Probe-scene sweep (exploratory) - added 2026-10-02". Exploratory: nothing here feeds a
pre-registered verdict.

    $P scripts/analysis/basic_behaviour/probes.py \
        --sweep-specs configs/eval_sweeps/hvsmell/hvsmell_{two_channel,single_channel,matched_strength}_rppo.yaml \
        --population results/analysis/basic_behaviour/hvsmell/population.json \
        --out-root results/analysis/basic_behaviour/hvsmell [--allow-partial]

Inputs: the dwell-sweep CSVs the three specs wrote, one per (run, scene) with one row per saved
checkpoint (`<output_dir>/<run label>/avoid_<scene>_inj<00|70>.csv`), and, for the training-world
comparison only, the population's `episodes.npz` caches (the same numbers as Figure 1).

Estimator (the level-04 re-measurement's, `studies/basicq2_waves/window_profile.py`, reused, not
copied): a contrast is formed PER CHECKPOINT first (the two scenes' series joined on the checkpoint
step); every series is summarised by the mean of its newest 20 checkpoints with a 95 % t-interval on
the effective sample size 20(1-r)/(1+r), r the lag-1 autocorrelation over those 20 (no correction
when r <= 0). A series with fewer than 20 checkpoints is not computed (rule 9).

Writes to <out-root>/probes/:
  run_summary.csv     one row per run x quantity: mean, lo, hi, ckpt_sd, r1, n_eff, n_ckpt, flags
  series.csv.gz       every per-checkpoint value the figures draw (levels of all 4 measures)
  world_summary.csv   per agent x quantity: seed means per world, the three world contrasts,
                      pooled seed SD, pooled checkpoint SD, between-world share, complete separation
  training_world.csv  per run: training-world bush dwell (share of chosen steps, final checkpoint)
  completeness.json   expected vs found checkpoints per run x scene (refuses to proceed on a gap
                      unless --allow-partial, which marks the outputs as a draft)
  provenance.json     the command and inputs, for the page's "Reproduce" line
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

import numpy as np
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "basicq2_waves"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "eval", "dwell_sweep"))
import window_profile as W                                              # noqa: E402

WINDOW = 20                       # newest checkpoints summarised (pre-stated reading, item 2)
SURVIVAL_FLOOR = 95.0             # late-window survival below this: reported, not interpreted (item 1)
CEILING = 90.0                    # no-animal bush dwell above this: contrasts at ceiling (item 9)

# scene key -> display name. The odour-removed chasing rabbit is odourless in the single-channel
# world (its only odour channel is the one removed) and enters no cross-world reading (item 9).
SCENES = [("none", "no animal"), ("pred", "hunting predator"), ("rabbit", "chasing rabbit"),
          ("rabbit_olfzero", "chasing rabbit, smell removed"), ("rabbitwander", "wandering rabbit"),
          ("rabbitwander_predsmell", "wandering rabbit that smells like a predator")]
SCENE_NAME = dict(SCENES)
INJURIES = ["00", "70"]
INJ_NAME = {"00": "injury 0", "70": "injury 70"}
MEASURES = {"bush_hiding": 100.0, "survival_steps": 1.0, "closest_approach": 1.0, "spatial_spread": 1.0}

# spec world -> population world tag; sweep agent word -> population agent tag
SPEC_WORLD = {"two_channel": "hv2ch", "single_channel": "hv1ch", "matched_strength": "hv1chm"}
SPEC_AGENT = {"ordinary": "t1none", "modulated": "t16quad"}

# Contrasts on bush dwell (pp), each (a - b) formed per checkpoint. Keys are the quantity names the
# figures use; the pre-stated reading's items 3-5.
CONTRASTS = {}
for _i in INJURIES:
    CONTRASTS[f"threat_pred_{_i}"] = ((("pred", _i),), (("none", _i),))
    CONTRASTS[f"threat_chase_{_i}"] = ((("rabbit", _i),), (("none", _i),))
    CONTRASTS[f"rabbit_resp_{_i}"] = ((("rabbitwander", _i),), (("none", _i),))
    CONTRASTS[f"confusion_{_i}"] = ((("rabbitwander_predsmell", _i),), (("rabbitwander", _i),))
# injury shift of the confusion contrast: (ps70 - w70) - (ps00 - w00)
CONTRASTS["confusion_shift"] = ((("rabbitwander_predsmell", "70"), ("rabbitwander", "00")),
                                (("rabbitwander", "70"), ("rabbitwander_predsmell", "00")))
QUANTITY_NAME = {
    **{f"threat_pred_{i}": f"threat discrimination, predator ({INJ_NAME[i]})" for i in INJURIES},
    **{f"threat_chase_{i}": f"chasing rabbit response ({INJ_NAME[i]})" for i in INJURIES},
    **{f"rabbit_resp_{i}": f"wandering rabbit response ({INJ_NAME[i]})" for i in INJURIES},
    **{f"confusion_{i}": f"confusion contrast ({INJ_NAME[i]})" for i in INJURIES},
    "confusion_shift": "injury shift of the confusion contrast (70 − 0)"}
# the quantities the variance budget reads (item 7: "each quantity in 3-5")
BUDGET_QS = ["threat_pred_00", "threat_pred_70", "rabbit_resp_00", "rabbit_resp_70",
             "confusion_00", "confusion_70", "confusion_shift"]
WORLD_CONTRASTS = [("hv1chm", "hv2ch"), ("hv1ch", "hv2ch"), ("hv1ch", "hv1chm")]


def cond(scene, inj):
    return f"avoid_{scene}_inj{inj}"


def load_runs(spec_paths):
    """Every run of every spec, with its CSV series. Labels follow <world>_<agent>_s<seed>."""
    sys.path.insert(0, os.path.join(ROOT, "scripts", "eval", "dwell_sweep"))
    from run_sweep import list_checkpoints, resolve_run_dir
    runs = []
    for sp in spec_paths:
        S = yaml.safe_load(open(sp))
        out = os.path.join(ROOT, S["output_dir"])
        world_key = os.path.basename(os.path.normpath(S["output_dir"]))
        if world_key not in SPEC_WORLD:
            raise SystemExit(f"{sp}: output_dir {S['output_dir']} is not one of {sorted(SPEC_WORLD)}")
        for r in S["runs"]:
            wtag, agent, seed = r["label"].rsplit("_", 2)
            if wtag != SPEC_WORLD[world_key] or agent not in SPEC_AGENT or not seed.startswith("s"):
                raise SystemExit(f"{sp}: run label {r['label']!r} does not parse as <world>_<agent>_s<seed>")
            run_dir = resolve_run_dir(r["path"], S["algo"])
            e = {"sweep_label": r["label"], "world": wtag, "agent": SPEC_AGENT[agent],
                 "seed": int(seed[1:]), "label": f"{wtag}_{SPEC_AGENT[agent]}_{seed}",
                 "run_dir": str(run_dir), "out": out, "spec": os.path.relpath(sp, ROOT),
                 "expected": len(list_checkpoints(S["algo"], run_dir)), "series": {}}
            for scene, _ in SCENES:
                for inj in INJURIES:
                    f = os.path.join(out, r["label"], f"{cond(scene, inj)}.csv")
                    if os.path.exists(f):
                        d = pd.read_csv(f).sort_values("step").reset_index(drop=True)
                        e["series"][(scene, inj)] = d
            runs.append(e)
    return runs


def completeness(runs):
    rows, gaps = [], []
    for e in runs:
        for scene, _ in SCENES:
            for inj in INJURIES:
                d = e["series"].get((scene, inj))
                n = 0 if d is None else int(d["bush_hiding"].notna().sum())
                rows.append({"label": e["label"], "scene": scene, "injury": inj, "found": n,
                             "expected": e["expected"]})
                if n < e["expected"]:
                    gaps.append(f"{e['sweep_label']} {cond(scene, inj)}: {n}/{e['expected']}")
    return rows, gaps


def summarise(values):
    """Late-window mean and lag-1-corrected 95 % CI of one series (oldest -> newest)."""
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    if v.size < WINDOW:
        return None
    p = W.window_profile(v, windows=[WINDOW]).iloc[0]
    return {"mean": p["mean"], "lo": p["lo"], "hi": p["hi"], "ckpt_sd": p["sd"], "r1": p["r1"],
            "n_eff": p["n_eff"], "n_ckpt": int(v.size)}


def contrast_series(e, q):
    """Per-checkpoint contrast series (pp), joined on the checkpoint step. (steps, values)."""
    plus, minus = CONTRASTS[q]
    parts = []
    for sign, terms in ((1.0, plus), (-1.0, minus)):
        for scene, inj in terms:
            d = e["series"].get((scene, inj))
            if d is None:
                return None, None
            parts.append(d[["step", "bush_hiding"]].rename(columns={"bush_hiding": f"{sign}_{scene}_{inj}"}))
    m = parts[0]
    for p in parts[1:]:
        m = m.merge(p, on="step", how="inner")
    m = m.sort_values("step")
    val = np.zeros(len(m))
    for c in m.columns[1:]:
        val += float(c.split("_", 1)[0]) * m[c].to_numpy() * 100.0
    return m["step"].to_numpy(), val


def scenes_of(q):
    plus, minus = CONTRASTS[q]
    return sorted(set(plus) | set(minus))


def run_summary(runs):
    out, series_rows = [], []
    for e in runs:
        late = {}
        for (scene, inj), d in e["series"].items():
            for m, sc in MEASURES.items():
                s = summarise(d[m].to_numpy() * sc)
                for st, v in zip(d["step"], d[m].to_numpy() * sc):
                    series_rows.append({"label": e["label"], "scene": scene, "injury": inj, "measure": m,
                                        "step": int(st), "value": v})
                if s is None:
                    continue
                late[(scene, inj, m)] = s
                out.append({"label": e["label"], "world": e["world"], "agent": e["agent"], "seed": e["seed"],
                            "kind": "level", "quantity": f"{m}:{scene}:{inj}", "scene": scene, "injury": inj,
                            "measure": m, **s})
        # validity: a scene whose late survival is under the floor is reported, not interpreted
        bad = {(s, i) for (s, i, m), v in late.items() if m == "survival_steps" and v["mean"] < SURVIVAL_FLOOR}
        ceil = {i for (s, i, m), v in late.items()
                if s == "none" and m == "bush_hiding" and v["mean"] > CEILING}
        for r in out:
            if r["label"] == e["label"] and r["kind"] == "level":
                r["short_survival"] = (r["scene"], r["injury"]) in bad
        for q in CONTRASTS:
            st, val = contrast_series(e, q)
            if st is None:
                continue
            s = summarise(val)
            if s is None:
                continue
            sc = scenes_of(q)
            out.append({"label": e["label"], "world": e["world"], "agent": e["agent"], "seed": e["seed"],
                        "kind": "contrast", "quantity": q, "scene": "", "injury": "", "measure": "bush_hiding",
                        **s, "short_survival": any(x in bad for x in sc),
                        "at_ceiling": any(i in ceil for (_, i) in sc if ("none", i) in sc)})
    R = pd.DataFrame(out)
    if "at_ceiling" not in R:
        R["at_ceiling"] = False
    R["at_ceiling"] = R["at_ceiling"].fillna(False).astype(bool)
    return R, pd.DataFrame(series_rows)


def world_summary(R):
    """Item 7: three scales side by side, per agent x quantity."""
    rows = []
    C = R[R.kind == "contrast"]
    for agent in sorted(C.agent.unique()):
        for q in BUDGET_QS:
            sub = C[(C.agent == agent) & (C.quantity == q)]
            worlds = {w: sub[sub.world == w] for w in ("hv2ch", "hv1ch", "hv1chm")}
            if any(len(g) < 2 for g in worlds.values()):
                continue
            means = {w: float(g["mean"].mean()) for w, g in worlds.items()}
            seed_sd = float(np.sqrt(np.mean([g["mean"].var(ddof=1) for g in worlds.values()])))
            ckpt_sd = float(np.sqrt(np.mean(sub["ckpt_sd"].to_numpy() ** 2)))
            allv = sub["mean"].to_numpy()
            ss_tot = float(((allv - allv.mean()) ** 2).sum())
            ss_b = float(sum(len(g) * (means[w] - allv.mean()) ** 2 for w, g in worlds.items()))
            r = {"agent": agent, "quantity": q, "seed_sd": seed_sd, "ckpt_sd": ckpt_sd,
                 "share_between": ss_b / ss_tot if ss_tot > 0 else np.nan,
                 "n_runs": int(len(sub)), "flagged_runs": int((sub.short_survival | sub.at_ceiling).sum())}
            for w, m in means.items():
                r[f"mean_{w}"] = m
                r[f"n_{w}"] = int(len(worlds[w]))
            for a, b in WORLD_CONTRASTS:
                va, vb = worlds[a]["mean"].to_numpy(), worlds[b]["mean"].to_numpy()
                r[f"diff_{a}_{b}"] = means[a] - means[b]
                r[f"sep_{a}_{b}"] = bool(va.min() > vb.max() or va.max() < vb.min())
            rows.append(r)
    cols = ["agent", "quantity", "seed_sd", "ckpt_sd", "share_between", "n_runs", "flagged_runs"]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)


def training_world(population, out_root, runs):
    """Training-world bush dwell per run: share of chosen steps, as Figure 1 computes it."""
    M = json.load(open(population))
    cells = {c["label"]: c for c in M["cells"]}
    rows = []
    for e in runs:
        c = cells.get(e["label"])
        if c is None:
            raise SystemExit(f"run {e['label']} (sweep {e['sweep_label']}) is not in {population}")
        if os.path.normpath(os.path.join(ROOT, c["run"])) != os.path.normpath(e["run_dir"]):
            raise SystemExit(f"{e['label']}: sweep run dir {e['run_dir']} != population run {c['run']}")
        f = os.path.join(out_root, e["label"], "episodes.npz")
        if not os.path.exists(f):
            rows.append({"label": e["label"], "bush_dwell": np.nan, "n_episodes": 0, "checkpoint": c["checkpoint"]})
            continue
        z = np.load(f)
        rows.append({"label": e["label"], "bush_dwell": 100.0 * float(z["y__bush_dwell"].sum() / z["n_steps"].sum()),
                     "n_episodes": int(z["n_steps"].size), "checkpoint": int(c["checkpoint"])})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep-specs", nargs="+", required=True)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--allow-partial", action="store_true",
                    help="draft mode: proceed with missing checkpoints (outputs are marked partial)")
    ap.add_argument("--csv-root-override", default=None,
                    help="DEVELOPMENT ONLY: read the sweep CSVs from this root instead of each spec's "
                         "output_dir (<root>/<world>/<run>/...); forces --allow-partial semantics")
    a = ap.parse_args(argv)
    runs = load_runs([os.path.abspath(p) for p in a.sweep_specs])
    if a.csv_root_override:
        for e in runs:
            e["out"] = os.path.join(os.path.abspath(a.csv_root_override), os.path.basename(e["out"]))
            e["series"] = {}
            for scene, _ in SCENES:
                for inj in INJURIES:
                    f = os.path.join(e["out"], e["sweep_label"], f"{cond(scene, inj)}.csv")
                    if os.path.exists(f):
                        e["series"][(scene, inj)] = pd.read_csv(f).sort_values("step").reset_index(drop=True)
    comp, gaps = completeness(runs)
    partial = bool(gaps)
    if gaps and not (a.allow_partial or a.csv_root_override):
        raise SystemExit(f"{len(gaps)} run x scene series are incomplete (first: {gaps[:3]}); the sweep has "
                         f"not finished or a checkpoint crashed - re-run the driver (incremental) "
                         f"or pass --allow-partial for a draft")
    R, S = run_summary(runs)
    WS = world_summary(R)
    TW = training_world(os.path.abspath(a.population), os.path.abspath(a.out_root), runs)
    od = os.path.join(os.path.abspath(a.out_root), "probes")
    os.makedirs(od, exist_ok=True)
    R.to_csv(os.path.join(od, "run_summary.csv"), index=False)
    S.to_csv(os.path.join(od, "series.csv.gz"), index=False)
    WS.to_csv(os.path.join(od, "world_summary.csv"), index=False)
    TW.to_csv(os.path.join(od, "training_world.csv"), index=False)
    json.dump({"partial": partial, "gaps": gaps, "rows": comp,
               "runs": [{k: e[k] for k in ("label", "sweep_label", "world", "agent", "seed", "run_dir", "spec",
                                           "expected")} for e in runs]},
              open(os.path.join(od, "completeness.json"), "w"), indent=1)
    cmd = ("python scripts/analysis/basic_behaviour/probes.py --sweep-specs "
           + " ".join(os.path.relpath(os.path.abspath(p), ROOT) for p in a.sweep_specs)
           + f" --population {os.path.relpath(os.path.abspath(a.population), ROOT)}"
           + f" --out-root {os.path.relpath(os.path.abspath(a.out_root), ROOT)}")
    json.dump({"command": cmd, "written": datetime.datetime.now().isoformat(timespec="seconds"),
               "partial": partial, "csv_root_override": a.csv_root_override,
               "output_dirs": sorted({os.path.relpath(e["out"], ROOT) for e in runs})},
              open(os.path.join(od, "provenance.json"), "w"), indent=1)
    n_found = sum(r["found"] for r in comp)
    n_exp = sum(r["expected"] for r in comp)
    print(f"probes: {len(runs)} runs, {n_found:,} of {n_exp:,} run x scene x checkpoint rows "
          f"({'PARTIAL draft' if partial else 'complete'}); {len(R)} summaries -> {od}")


if __name__ == "__main__":
    main()
