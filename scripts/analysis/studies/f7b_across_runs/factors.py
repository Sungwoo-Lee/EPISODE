#!/usr/bin/env python3
"""factors.py - which training or test factor moves two targets the most, from matched pairs of runs.

Targets (percentage points of bush dwell, newest 20 checkpoints, experiment tests):
  T1  hides more when injured, wandering rabbit present: wandering rabbit at injury 70 minus at injury 0
  T2  treats the wandering rabbit as a threat when injured: wandering rabbit minus no animal, both at injury 70
  S   state dependence (for reference): no animal, injury 70 minus injury 0
Each factor is a set of PAIRS of runs (or of tests of the same run) that differ in that factor and as little
else as the existing runs allow; the effect is the mean paired difference (after minus before) with the range
over pairs. Pairs whose either side is hollow (agent died early in a scene used) are counted but flagged.
Exploratory: no tests.

    $P scripts/analysis/studies/f7b_across_runs/factors.py --data results/analysis/f7b_across_runs
Writes <data>/factors.csv (one row per factor) and <data>/factor_pairs.csv (one row per pair).
"""
import argparse
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "basic_behaviour"))
import figures as FX  # noqa: E402
import probes as PR  # noqa: E402

AV = os.path.join(ROOT, "results/eval/avoidance")


def leaf_targets(leaf):
    """T1, T2, S for a sweep folder that is not in collect.py's tables (formed per checkpoint, newest 20)."""
    def ser(c):
        d = pd.read_csv(os.path.join(AV, leaf, f"avoid_{c}.csv"))
        col = "bush_hiding" if "bush_hiding" in d.columns else "bush_dwell"
        return d[["step", col]].rename(columns={col: c})
    m = ser("rabbitwander_inj70")
    for c in ("rabbitwander_inj00", "none_inj70", "none_inj00"):
        m = m.merge(ser(c), on="step")
    m = m.sort_values("step")
    f = lambda a, b: PR.summarise(((m[a] - m[b]) * 100).to_numpy())["mean"]
    return {"T1": f("rabbitwander_inj70", "rabbitwander_inj00"), "T2": f("rabbitwander_inj70", "none_inj70"),
            "S": f("none_inj70", "none_inj00"), "hollow": False}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    R, L, E, X = FX.load(a.data)
    lv = L.pivot_table(index="id", columns=["scene", "injury"], values="mean")
    d = R.set_index("id").copy()
    d["T1"] = lv[("rabbitwander", "70")] - lv[("rabbitwander", "00")]
    d["T2"] = lv[("rabbitwander", "70")] - lv[("none", "70")]
    d["S"] = lv[("none", "70")] - lv[("none", "00")]
    d["hollow"] = d.index.isin(FX.flagged(L, "rabbitwander-minus-none"))

    pairs = []

    def add(factor, before, after, label, b, f):
        for k, (x, y) in enumerate(zip(b, f)):
            if x is None or y is None:
                continue
            pairs.append({"factor": factor, "before": before, "after": after, "pair": label[k],
                          **{f"d{t}": y[t] - x[t] for t in ("T1", "T2", "S")},
                          "hollow": bool(x["hollow"] or y["hollow"])})

    row = lambda i: d.loc[i] if i in d.index else None
    # 1. healing on a bush 25x: wave 1 (21 Sep) vs fast bush healing (22 Sep), same level and agent
    lab, b, f = [], [], []
    for lvl in ("02", "03", "04"):
        for ag in ("control", "modulated"):
            lab.append(f"level {lvl} {ag}")
            b.append(row(f"basicq2_wave1/lvl{lvl}_{ag}"))
            f.append(row(f"injurygrid_core/lvl{lvl}_{ag}"))
    add("Healing 25x faster on a bush (+ double food store)", "wave 1, 21 Sep", "22 Sep runs", lab, b, f)
    # 2. test bush keeps animals out (same agents)
    lab, b, f = [], [], []
    for ag in ("lvl04_control", "lvl04_modulated"):
        lab.append(ag)
        b.append(leaf_targets(f"metrics_history_rppo_basicq2_wave2/{ag}"))
        f.append(leaf_targets(f"metrics_history_rppo_basicq2_wave2_blocking_bush/{ag}"))
    add("Test bush keeps animals out (same agents)", "test bush lets animals in", "keeps them out", lab, b, f)
    # 3. training bush keeps animals out
    lab, b, f = [], [], []
    for lvl, bn, rn in (("01", "b01_mc", "b01_slowpred_5x5"), ("02", "b02_mc", "b02_predrabbit_10x10"),
                        ("03", "b03_mc", "b03_randinit_10x10"), ("04", "b04_mc", "b04_jump_10x10")):
        lab.append(f"level {lvl}")
        b.append(row(f"dp1_rppo/{bn}"))
        f.append(row(f"bushrefuge_rppo/{rn}"))
    add("Training bush keeps animals out", "July re-train", "August bush refuge", lab, b, f)
    # 4. ambush predators removed (rest premium, matched premium)
    rp = d[d.family == "Rest premium"]
    nh = d[d.family == "Rest premium, no ambush predators"]
    prem = lambda s: s.setting.str.extract(r"premium (\d+)")[0]
    rp, nh = rp.assign(p=prem(rp)), nh.assign(p=prem(nh))
    lab, b, f = [], [], []
    for p in sorted(set(rp.p) & set(nh.p), key=int):
        lab.append(f"premium {p}")
        b.append(rp[rp.p == p].iloc[0])
        f.append(nh[nh.p == p].iloc[0])
    add("Ambush predators removed from training", "with ambush predators", "without", lab, b, f)
    # 5. rest premium high vs low (each series, unpaired means)
    for name, g in (("with ambush predators", rp), ("without ambush predators", nh)):
        lo, hi = g[g.p.astype(int) <= 38], g[g.p.astype(int) >= 1207]
        if len(lo) and len(hi):
            add("Rest premium high (1207+) vs low (38 or less)", "low premium", "high premium", [name],
                [lo[["T1", "T2", "S"]].mean().to_dict() | {"hollow": False}],
                [hi[["T1", "T2", "S"]].mean().to_dict() | {"hollow": False}])
    # 6. body rules: each rule on vs off, worlds differing only in that rule, same agent
    body = d[d.family == "Body rules (level 05)"].copy()
    body["w"] = body.setting.str[:5]
    for k, name in enumerate(["Hunger slows healing", "Healing costs food", "Warmth costs food", "Scarcer food"]):
        lab, b, f = [], [], []
        for _, r in body.iterrows():
            w = r.w
            if w[1 + k] != "0":
                continue
            w1 = w[:1 + k] + "1" + w[2 + k:]
            m = body[(body.w == w1) & (body.agent == r.agent)]
            if len(m):
                lab.append(f"{w}->{w1} {r.agent}")
                b.append(r)
                f.append(m.iloc[0])
        add(f"Body rule on: {name.lower()}", "off", "on", lab, b, f)
    # 7. modulated vs ordinary, same group / scene set / setting / seed
    lab, b, f = [], [], []
    for (fam, ss, st, sd), g in d.groupby(["family", "scene_set", "setting", "seed"]):
        o, m = g[g.agent == "ordinary"], g[g.agent == "modulated"]
        if len(o) == 1 and len(m) == 1:
            lab.append(f"{fam} {st} s{sd}")
            b.append(o.iloc[0])
            f.append(m.iloc[0])
    add("Modulated agent instead of ordinary", "ordinary", "modulated", lab, b, f)
    # 8. smell worlds (seed and agent paired)
    sm = d[d.family == "Smell study (level 05)"]
    for other, name in (("single-channel smell", "Smell: single channel (rabbit smells like a weaker predator)"),
                        ("matched-strength smell", "Smell: same mixture for both animals")):
        lab, b, f = [], [], []
        for _, r in sm[sm.setting == "two-channel smell (control)"].iterrows():
            m = sm[(sm.setting == other) & (sm.agent == r.agent) & (sm.seed == r.seed)]
            if len(m):
                lab.append(f"{r.agent} s{r.seed}")
                b.append(r)
                f.append(m.iloc[0])
        add(name, "two-channel smell", other, lab, b, f)
    # 9. thirst: map 20 vs 10; smell range 3 vs whole map
    th = d[d.family == "Thirst task"].copy()
    th["map"] = th.setting.str.extract(r"(\d+)x")[0]
    th["sm"] = th.setting.str.split(", ").str[1]
    for name, key, v0, v1, other in (("Thirst: 20x20 map instead of 10x10", "map", "10", "20", "sm"),
                                      ("Thirst: smell range 3 instead of whole map", "sm", "smell carries across the map",
                                       "smell range 3", "map")):
        lab, b, f = [], [], []
        for _, r in th[th[key] == v0].iterrows():
            m = th[(th[key] == v1) & (th[other] == r[other]) & (th.agent == r.agent)]
            if len(m):
                lab.append(f"{r[other]} {r.agent}")
                b.append(r)
                f.append(m.iloc[0])
        add(name, v0, v1, lab, b, f)
    # 10. temperature scenes: fire by the bush vs no fire (same runs)
    t = d[d.scene_set == "thermal"].copy()
    t["run"] = t.index.str.split("/").str[1]
    t["var"] = t.sweep.str.replace("thermalprobe_", "", regex=False)
    for name, v0, v1 in (("Test scene: campfire beside the bush (vs none)", "neutral_clean", "fire_by_bush_clean"),
                         ("Test scene: sensor noise matched to training (vs clean)", "neutral_clean", "neutral_noise_matched")):
        lab, b, f = [], [], []
        for _, r in t[t["var"] == v0].iterrows():
            m = t[(t["var"] == v1) & (t.run == r.run)]
            if len(m):
                lab.append(r.run)
                b.append(r)
                f.append(m.iloc[0])
        add(name, v0, v1, lab, b, f)
    # 11. one curriculum level up (03 -> 04), wherever both exist with the same agent and group
    lab, b, f = [], [], []
    for (fam, ss, ag), g in d.groupby(["family", "scene_set", "agent"]):
        l3 = g[g.setting.str.startswith("level 03")]
        l4 = g[g.setting.str.startswith("level 04")]
        if len(l3) == 1 and len(l4) == 1:
            lab.append(f"{fam} {ag}")
            b.append(l3.iloc[0])
            f.append(l4.iloc[0])
    add("Curriculum level 04 instead of 03 (predator can jump)", "level 03", "level 04", lab, b, f)

    P = pd.DataFrame(pairs)
    P.to_csv(os.path.join(a.data, "factor_pairs.csv"), index=False)
    F = P.groupby("factor", sort=False).agg(
        before=("before", "first"), after=("after", "first"), pairs=("pair", "size"), hollow=("hollow", "sum"),
        dT1=("dT1", "mean"), dT1_lo=("dT1", "min"), dT1_hi=("dT1", "max"),
        dT2=("dT2", "mean"), dT2_lo=("dT2", "min"), dT2_hi=("dT2", "max"), dS=("dS", "mean")).reset_index()
    F.to_csv(os.path.join(a.data, "factors.csv"), index=False)
    pd.set_option("display.width", 220)
    print(F.round(1).to_string())


if __name__ == "__main__":
    main()
