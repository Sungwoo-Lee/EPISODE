#!/usr/bin/env python3
"""collect.py - late-training bush dwell per experiment-test scene, for every run that has one.

The "Figure 7b across runs" page (docs/experiments/active/hypervigilance/f7b_across_runs/) shows the
Basic Behaviour page's Figure 7b view -- bush dwell in each fixed test scene, at starting injury 0
and 70, averaged over the newest 20 saved checkpoints -- for as many trained agents as have
experiment-test sweeps. Exploratory: nothing here is a test.

Inputs: the dwell-sweep CSVs (scripts/eval/dwell_sweep/run_sweep.py), one per (run, scene, start
injury), one row per checkpoint. The run list comes from the sweep specs under configs/eval_sweeps/
(REGISTRY below), plus the two July network-size sweeps whose specs were never committed (found by
run name). Every run found is either selected or written to the dropped table with a reason.

Estimator: probes.summarise -- the mean of the newest 20 checkpoints with a 95 % t-interval on the
effective sample size 20(1-r)/(1+r), r the lag-1 autocorrelation (the Basic Behaviour page's).
The injury effect (injury 70 minus injury 0) is formed PER CHECKPOINT first, then summarised the
same way; so is each scene's injury effect minus the no-animal scene's injury effect (scene
"<scene>-minus-none"), the part of the injury effect that the animal adds. A series with fewer than 20 checkpoints is not computed (dropped, reason recorded).

    $P scripts/analysis/studies/f7b_across_runs/collect.py --out results/analysis/f7b_across_runs

Writes <out>/levels.csv, <out>/injury_effect.csv, <out>/runs.csv, <out>/dropped.csv, <out>/provenance.json.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "basic_behaviour"))
import probes as P  # noqa: E402  (summarise, SCENES, WINDOW)

AV = "results/eval/avoidance"
SCENES = [s for s, _ in P.SCENES]
INJ = ["00", "70"]

# Scene sets: what differs between the fixed test-scene batteries. Never pooled.
SCENE_SETS = {
    "july": "July set: bush hides the agent, animals can walk into it; no temperature system",
    "core": "Core set: bush hides the agent and blocks animals; no campfire",
    "thermal": "Temperature set: core scenes in a level-05/06 body, one of 8 fire/ambient variants",
    "injgrid": "Injury-grid set: only 3 scenes (no animal, hunting predator, wandering rabbit)",
    "world": "Training-world set: scenes built on the agent's own training world, campfire beside the bush",
}

# (spec glob, family, scene set, setting-description function of the run label)
REGISTRY = [
    ("configs/eval_sweeps/basic04_variants_rppo.yaml", "July level-04 variants", "july",
     lambda l: {"v01_slowmove": "slower movement", "v02_shortjump": "shorter jump", "v03_lowdmg": "lower damage",
                "v04_allcomb": "all three combined", "v05_asr030": "animal speed 0.30", "v06_asr070": "animal speed 0.70",
                "v07_comb030": "combined + speed 0.30", "v08_comb070": "combined + speed 0.70"}[l]),
    ("configs/eval_sweeps/basic_gae_rppo.yaml", "July GAE return", "july",
     lambda l: f"level 0{l[2]}, GAE return estimate"),
    ("configs/eval_sweeps/basic_nmn_g32_rppo.yaml", "July early modulator", "july",
     lambda l: f"level 0{l[2]}, early modulator design, {l.split('_')[1].upper()} return"),
    ("configs/eval_sweeps/basicq2_wave1_rppo.yaml", "Curriculum wave 1", "core",
     lambda l: f"level 0{l[4]}"),
    ("configs/eval_sweeps/basicq2_wave2_rppo.yaml", "Curriculum wave 2", "core",
     lambda l: f"level 0{l[4]}"),
    ("configs/eval_sweeps/basicq2_wave2_blocking_bush_rppo.yaml", "Blocking-bush training", "core",
     lambda l: f"level 0{l[4]}, bush blocks animals in training"),
    ("configs/eval_sweeps/injury_grid/injurygrid_*_rppo.yaml", "Blocking-bush training", "injgrid", None),
    ("configs/eval_sweeps/thermal_probes/thermalprobe_*_rppo.yaml", "Blocking-bush training", "thermal", None),
    ("configs/eval_sweeps/hvsmell/hvsmell_*_rppo.yaml", "Smell study (level 05)", "world",
     lambda l: {"hv2ch": "two-channel smell (control)", "hv1ch": "single-channel smell",
                "hv1chm": "matched-strength smell"}[l.split("_")[0]]),
    ("configs/eval_sweeps/l05body/l05body_w*_rppo.yaml", "Body rules (level 05)", "world", None),
    ("configs/eval_sweeps/thirst/thirst_*_rppo.yaml", "Thirst task", "world", None),
]
BODY_BITS = ["hunger slows healing", "healing costs food", "warmth costs food", "scarcer food"]


def body_setting(w):
    on = [n for b, n in zip(w[1:], BODY_BITS) if b == "1"]
    return f"{w}: " + (", ".join(on) if on else "no extra body rule")


def thirst_setting(c):
    m = re.match(r"g(\d+)s(\w)", c)
    sm = {"W": "smell carries across the map", "5": "smell range 5", "3": "smell range 3"}[m.group(2)]
    return f"{m.group(1)}x{m.group(1)} map, {sm}"


def agent_of(run_dir):
    n = os.path.basename(run_dir)
    if "t16quad" in n or "_nmn_" in n:
        return "modulated"
    return "ordinary"


def seed_of(run_dir):
    m = re.search(r"_s(\d+)$", os.path.basename(run_dir))
    return int(m.group(1)) if m else 42


def candidates():
    """Every (run, sweep folder) the registry knows about, with its metadata."""
    out = []
    for pat, fam, sset, desc in REGISTRY:
        for sp in sorted(glob.glob(os.path.join(ROOT, pat))):
            S = yaml.safe_load(open(sp))
            name = S["name"]
            for r in S["runs"]:
                lab, path = r["label"], r["path"]
                if desc is not None:
                    setting = desc(lab)
                elif name.startswith("injurygrid_") or name.startswith("thermalprobe_"):
                    variant = name.split("_", 1)[1]
                    setting = f"level 0{lab[4]}; scene variant {variant.replace('_', ' ')}"
                elif name.startswith("l05body_"):
                    setting = body_setting(name.split("_")[1])
                else:
                    setting = thirst_setting(name.split("_")[1])
                if fam == "Blocking-bush training" and sset == "core":
                    pass
                out.append({"family": fam, "scene_set": sset, "setting": setting, "spec": os.path.relpath(sp, ROOT),
                            "sweep": name, "label": lab, "run_dir": path, "agent": agent_of(path),
                            "seed": seed_of(path), "leaf": os.path.join(S["output_dir"], lab)})
    for lvl, size_tag in (("03", "basic03_size"), ("04", "basic04_size")):
        for leaf in sorted(glob.glob(os.path.join(ROOT, AV, f"metrics_history_rppo_{size_tag}", "sz*"))):
            sz = os.path.basename(leaf)
            m = sorted(glob.glob(os.path.join(ROOT, "results/JAX_RecurrentPPO", f"*_rppo_b{lvl}_{sz}_n*")))
            out.append({"family": "July network size", "scene_set": "july",
                        "setting": f"level {lvl}, network size {sz[2:]}", "spec": "(none committed; found by run name)",
                        "sweep": size_tag, "label": sz, "run_dir": os.path.relpath(m[0], ROOT) if m else "",
                        "agent": "ordinary", "seed": 42, "leaf": os.path.relpath(leaf, ROOT)})
    return out


def read(leaf, scene, inj):
    f = os.path.join(ROOT, leaf, f"avoid_{scene}_inj{inj}.csv")
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    if "bush_dwell" in d.columns and "bush_hiding" not in d.columns:
        # July sweeps (pre-promotion tmp/ pipeline) wrote the same measure -- share of the episode's
        # steps on the bush cell -- under its older name (tmp/plot_metrics_summary.py: "bush_dwell").
        d = d.rename(columns={"bush_dwell": "bush_hiding"})
    if "bush_hiding" not in d.columns or d.empty:   # a sweep still writing its CSVs
        return None
    return d.sort_values("step").reset_index(drop=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    runs, dropped, levels, effects = [], [], [], []
    for c in candidates():
        rid = f"{c['sweep']}/{c['label']}"
        series = {(s, i): read(c["leaf"], s, i) for s in SCENES for i in INJ}
        have = {k: v for k, v in series.items() if v is not None}
        if not have:
            dropped.append({**c, "id": rid, "reason": "no experiment-test results on disk"})
            continue
        n_ck = min(int(v["bush_hiding"].notna().sum()) for v in have.values())
        if n_ck < P.WINDOW:
            dropped.append({**c, "id": rid, "reason": f"only {n_ck} checkpoints tested (need {P.WINDOW})"})
            continue
        scenes_present = sorted({s for (s, _) in have}, key=SCENES.index)
        runs.append({**c, "id": rid, "n_ckpt": n_ck, "scenes": ",".join(scenes_present),
                     "last_step_M": round(max(float(v["step"].max()) for v in have.values()) / 1e6, 2)})
        for (s, i), d in have.items():
            v = summarise_safe(d["bush_hiding"].to_numpy() * 100.0)
            surv = summarise_safe(d["survival_steps"].to_numpy())
            if v:
                levels.append({"id": rid, "scene": s, "injury": i, **v,
                               "survival_mean": surv["mean"] if surv else np.nan})
        for s in scenes_present:
            if (s, "00") in have and (s, "70") in have:
                m = have[(s, "70")][["step", "bush_hiding"]].merge(
                    have[(s, "00")][["step", "bush_hiding"]], on="step", suffixes=("_70", "_00"))
                v = summarise_safe((m["bush_hiding_70"] - m["bush_hiding_00"]).to_numpy() * 100.0)
                if v:
                    effects.append({"id": rid, "scene": s, **v})
        # Scene-specific part: a scene's injury effect minus the no-animal scene's, per checkpoint.
        if all(("none", i) in have for i in INJ):
            base = have[("none", "70")][["step", "bush_hiding"]].merge(
                have[("none", "00")][["step", "bush_hiding"]], on="step", suffixes=("_n70", "_n00"))
            for s in scenes_present:
                if s == "none" or not all((s, i) in have for i in INJ):
                    continue
                m = have[(s, "70")][["step", "bush_hiding"]].merge(
                    have[(s, "00")][["step", "bush_hiding"]], on="step", suffixes=("_70", "_00")).merge(base, on="step")
                d = (m["bush_hiding_70"] - m["bush_hiding_00"]) - (m["bush_hiding_n70"] - m["bush_hiding_n00"])
                v = summarise_safe(d.to_numpy() * 100.0)
                if v:
                    effects.append({"id": rid, "scene": f"{s}-minus-none", **v})
    R = pd.DataFrame(runs)
    R.to_csv(os.path.join(a.out, "runs.csv"), index=False)
    pd.DataFrame(dropped).to_csv(os.path.join(a.out, "dropped.csv"), index=False)
    pd.DataFrame(levels).to_csv(os.path.join(a.out, "levels.csv"), index=False)
    pd.DataFrame(effects).to_csv(os.path.join(a.out, "injury_effect.csv"), index=False)
    json.dump({"command": " ".join(sys.argv), "written": datetime.datetime.now().isoformat(timespec="seconds"),
               "window": P.WINDOW, "selected": len(runs), "dropped": len(dropped)},
              open(os.path.join(a.out, "provenance.json"), "w"), indent=1)
    print(f"selected {len(runs)}  dropped {len(dropped)}")


def summarise_safe(v):
    s = P.summarise(v)
    return None if s is None else {k: float(x) for k, x in s.items()}


if __name__ == "__main__":
    main()
