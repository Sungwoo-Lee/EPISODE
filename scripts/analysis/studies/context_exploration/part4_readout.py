#!/usr/bin/env python3
"""part4_readout.py - Part 4 read-out of the context-exploration study (trained ordinary agent).

Implements, as pre-registered, docs/experiments/active/context_exploration/STUDY_PLAN.md
"Part 4 design" (4.4-4.6) + "Part 4 Revision 1" (R1.1-R1.6), for any manifest in the format of
docs/experiments/active/context_exploration/part4_manifest.yaml.

Data source: the LOCAL WandB binary `wandb/run-*-<id>/run-<id>.wandb` (never the web API) plus the
run's stdout log (completion, calibration record, observation width, neuromodulation banner).
Reward is never read; survival is `Episode/Steps` (survival steps per episode).

Window: rows with `Episode/Number` in (N - 0.1 N, N], N = the budget read from the WandB run config
(never the saved config.yaml). Row weight = `Episode/_window_n` (R1.6 L2, as the level-05 pilots).
- survival S, death shares, Term_*: weight w;
- time shares: weight w * Episode/Steps;
- conditional shares (eat | hungry, bush | injured, ...): weight = the row's state counter
  `Bal_N_*`; ratios are recomputed from the pooled shares (a ratio is "not computable" only if a
  POOLED denominator is zero); the w-weighted mean of per-row ratios is reported beside it;
- late-death cause shares: weight w * Bal_LateDeathShare.

Rules applied (all from the plan; nothing tuned here):
  replication gate (R1.6 L4), still-learning flag (4.4: S[1.8-2.0M] / S[1.6-1.8M] - 1 > 5 %),
  criteria 1-5 (4.4), criterion 3-fwd (R1.1), withheld criteria (R1.2), step ratio (R1.3),
  borderline band = max(reference seed gap, floor) (R1.5), seed-43 rule for simulation-disagreeing
  criterion-4 verdicts (R1.5), agreement table + trust rule (4.5 + R1.2), forwarding (4.6 + R1.1).

Usage:
  python scripts/analysis/studies/context_exploration/part4_readout.py MANIFEST.yaml \
      [--md-out FILE] [--json-out FILE]
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import re
import sys

import numpy as np
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
P = "Episode/Bal_"
TIME_KEYS = ("TimeBush", "TimeWarm", "TimeEat", "TimeElsewhere", "TimeNearFire")
CAUSES = ("Starvation", "Overeating", "Injury", "Thermal")
# conditional share -> its state counter
COND = {
    "EatShare_Hungry": "N_Hungry", "EatShare_Fed": "N_Fed",
    "BushShare_InjHi_True": "N_InjHi_True", "BushShare_InjLo_True": "N_InjLo_True",
    "BushShare_InjHi_True_Fed": "N_InjHi_True_Fed", "BushShare_InjLo_True_Fed": "N_InjLo_True_Fed",
    "BushShare_InjHi_Felt": "N_InjHi_Felt", "BushShare_InjLo_Felt": "N_InjLo_Felt",
    "BushShare_InjHi_Felt_Fed": "N_InjHi_Felt_Fed", "BushShare_InjLo_Felt_Fed": "N_InjLo_Felt_Fed",
    "WarmShare_Cold": "N_Cold", "WarmShare_Warm": "N_Warm",
}
RATIOS = {  # name -> (hi share, lo share)
    "EatRatio": ("EatShare_Hungry", "EatShare_Fed"),
    "HideRatio_True": ("BushShare_InjHi_True", "BushShare_InjLo_True"),
    "HideRatio_True_Fed": ("BushShare_InjHi_True_Fed", "BushShare_InjLo_True_Fed"),
    "HideRatio_Felt": ("BushShare_InjHi_Felt", "BushShare_InjLo_Felt"),
    "HideRatio_Felt_Fed": ("BushShare_InjHi_Felt_Fed", "BushShare_InjLo_Felt_Fed"),
    "WarmRatio": ("WarmShare_Cold", "WarmShare_Warm"),
}
# floors of the borderline band (R1.5)
FLOOR_SHARE, FLOOR_RATIO, FLOOR_SURV_REL = 0.05, 0.5, 0.05


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


# ------------------------------------------------------------------------------------ reading --
def read_run(run: dict) -> dict:
    from wandb.proto import wandb_internal_pb2 as pb
    from wandb.sdk.internal import datastore

    hits = sorted(glob.glob(os.path.join(ROOT, "wandb", f"run-*-{run['wandb_id']}")))
    if len(hits) != 1:
        raise ValueError(f"{run['id']}: expected one wandb/run-*-{run['wandb_id']}, found {hits}")
    wdir = hits[0]
    f = glob.glob(os.path.join(wdir, "run-*.wandb"))
    if len(f) != 1:
        raise ValueError(f"{wdir}: expected one run-*.wandb")
    ds = datastore.DataStore()
    ds.open_for_scan(f[0])
    rows, cfg = [], {}
    while True:
        data = ds.scan_data()
        if data is None:
            break
        rec = pb.Record()
        rec.ParseFromString(data)
        t = rec.WhichOneof("record_type")
        if t in ("run", "config"):
            for it in (rec.run.config.update if t == "run" else rec.config.update):
                cfg[it.key or "/".join(it.nested_key)] = json.loads(it.value_json)
            continue
        if t != "history":
            continue
        item = {(it.key or "/".join(it.nested_key)): it.value_json for it in rec.history.item}
        if "Episode/Number" not in item:
            continue
        r = {}
        for k, v in item.items():
            if k.startswith("Episode/") or k == "timesteps":
                try:
                    r[k] = float(json.loads(v))
                except (TypeError, ValueError):
                    pass
        rows.append(r)
    rows.sort(key=lambda r: r["Episode/Number"])
    args = json.load(open(os.path.join(wdir, "files", "wandb-metadata.json"))).get("args", [])
    launch_cfg = args[args.index("--config") + 1] if "--config" in args else None
    # --- identity / budget checks (WandB config, not the stale saved config.yaml) ---
    if cfg.get("tag") != run["tag"]:
        raise ValueError(f"{run['id']}: tag {cfg.get('tag')!r} != manifest {run['tag']!r}")
    if launch_cfg != run["config"]:
        raise ValueError(f"{run['id']}: --config {launch_cfg!r} != manifest {run['config']!r}")
    if int(cfg.get("seed", -1)) != int(run["seed"]):
        raise ValueError(f"{run['id']}: WandB seed {cfg.get('seed')} != manifest {run['seed']}")
    # --- log checks ---
    log = open(_abs(run["log"]), errors="replace").read()
    m = re.search(r"\[balance\] balance_calibration: (\{.*\})", log)
    calib = ast.literal_eval(m.group(1)) if m else None
    obs = re.search(r"Observation Dim: (\d+)", log)
    return {"wdir": os.path.relpath(wdir, ROOT), "rows": rows, "episodes_cfg": int(cfg["episodes"]),
            "seed_cfg": int(cfg["seed"]), "complete_log": "Training complete" in log[-20000:],
            "calibration": calib, "obs_dim": int(obs.group(1)) if obs else None,
            "nmn_disabled": "Neuromodulation: DISABLED" in log,
            "first_row_bal_keys": sum(1 for k in rows[0] if k.startswith(P))}


# ------------------------------------------------------------------------------------ pooling --
def pool(rows: list[dict]) -> dict:
    if not rows:
        return {"n_rows": 0}
    g = lambda r, k: r.get(k)
    w = np.array([r["Episode/_window_n"] for r in rows])
    st = np.array([r["Episode/Steps"] for r in rows])
    out = {"n_rows": len(rows), "S": float((w * st).sum() / w.sum())}
    for k in ("Bal_EarlyDeathShare", "Bal_LateDeathShare"):
        out[k[4:]] = float(sum(r["Episode/" + k] * r["Episode/_window_n"] for r in rows) / w.sum())
    out["FoodEaten"] = float(sum(r["Episode/FoodEaten"] * r["Episode/_window_n"] for r in rows) / w.sum())
    for c in ("Starvation", "Overeating", "Injury", "Thermal", "MaxSteps"):
        out["Term_" + c] = float(sum(r["Episode/Term_" + c] * r["Episode/_window_n"] for r in rows) / w.sum())
    for k in TIME_KEYS:
        num = sum(r[P + k] * r["Episode/_window_n"] * r["Episode/Steps"] for r in rows if P + k in r)
        den = sum(r["Episode/_window_n"] * r["Episode/Steps"] for r in rows if P + k in r)
        out[k] = float(num / den) if den > 0 else None
    lw = [(r["Episode/_window_n"] * r[P + "LateDeathShare"], r) for r in rows]
    den = sum(x for x, _ in lw)
    for c in CAUSES:
        out["LateDeath_" + c] = (float(sum(x * r.get(P + "LateDeath_" + c, 0.0) for x, r in lw) / den)
                                 if den > 0 else None)
    for sh, nk in COND.items():
        num = sum(r[P + nk] * r[P + sh] for r in rows if P + sh in r)
        den = sum(r[P + nk] for r in rows)
        out[sh] = float(num / den) if den > 0 else None
    for rk, (hi, lo) in RATIOS.items():
        h, l_ = out[hi], out[lo]
        out[rk] = (h / l_) if (h is not None and l_ not in (None, 0.0)) else None
        vals = [(r["Episode/_window_n"], r[P + rk]) for r in rows if P + rk in r]
        out[rk + "_rowmean"] = (float(sum(a * b for a, b in vals) / sum(a for a, _ in vals))
                                if vals else None)
    causes = {c: out["LateDeath_" + c] for c in CAUSES if out["LateDeath_" + c] is not None}
    if causes:
        top = max(causes, key=causes.get)
        out["D"], out["D_cause"] = causes[top], top
    else:
        out["D"], out["D_cause"] = None, None
    return out


def window(rows, lo, hi):
    return [r for r in rows if lo < r["Episode/Number"] <= hi]


def ts_at(rows, n):
    sel = [r for r in rows if r["Episode/Number"] <= n and "timesteps" in r]
    return sel[-1]["timesteps"] if sel else None


# ----------------------------------------------------------------------------------- criteria --
def criteria(p: dict, S_ref: float | None, D_ref: float | None) -> dict:
    ts = [p[k] for k in ("TimeBush", "TimeWarm", "TimeEat", "TimeElsewhere")]
    c = {}
    c[1] = (None not in ts and max(ts) <= 0.70 and min(ts[:3]) >= 0.10)
    c[2] = (p["EatRatio"] is not None and p["EatRatio"] >= 2 and
            p["HideRatio_True"] is not None and p["HideRatio_True"] >= 2)
    late = p["LateDeathShare"]
    c[3] = late < 0.05 or (p["D"] is not None and p["D"] <= 0.60)
    c["3fwd"] = (late < 0.05 or (p["D"] is not None and D_ref is not None
                                 and p["D"] <= max(0.60, D_ref + 0.05)))
    c[4] = (S_ref is not None and p["S"] >= 0.8 * S_ref)
    c[5] = p["HideRatio_True_Fed"] is not None and p["HideRatio_True_Fed"] >= 2
    return c


def borderline(p, S_ref, D_ref, gaps) -> list[str]:
    """Quantities within max(reference seed gap, floor) of their threshold (R1.5)."""
    out = []

    def chk(name, val, thr, gap, floor):
        if val is None:
            return
        band = max(gap, floor)
        if abs(val - thr) <= band:
            out.append(f"{name} {val:.3f} vs {thr:.3f} (band {band:.3f})")
    tmax = max(("TimeBush", "TimeWarm", "TimeEat", "TimeElsewhere"), key=lambda k: p[k] or -1)
    chk(f"crit1 {tmax} (max share)", p[tmax], 0.70, gaps[tmax], FLOOR_SHARE)
    for k in ("TimeBush", "TimeWarm", "TimeEat"):
        chk(f"crit1 {k}", p[k], 0.10, gaps[k], FLOOR_SHARE)
    chk("crit2 EatRatio", p["EatRatio"], 2.0, gaps["EatRatio"], FLOOR_RATIO)
    chk("crit2 HideRatio_True", p["HideRatio_True"], 2.0, gaps["HideRatio_True"], FLOOR_RATIO)
    chk("crit3 LateDeathShare", p["LateDeathShare"], 0.05, gaps["LateDeathShare"], FLOOR_SHARE)
    if p["LateDeathShare"] >= 0.05 and D_ref is not None:
        chk("crit3-fwd dominant cause", p["D"], max(0.60, D_ref + 0.05), gaps["D"], FLOOR_SHARE)
    thr = 0.8 * S_ref
    chk("crit4 survival steps", p["S"], thr, gaps["S"], FLOOR_SURV_REL * thr)
    chk("crit5 HideRatio_True_Fed", p["HideRatio_True_Fed"], 2.0, gaps["HideRatio_True_Fed"], FLOOR_RATIO)
    return out


# ------------------------------------------------------------------------------------- main --
def analyse(man: dict) -> dict:
    N = int(man["episodes"])
    f = float(man["readout_fraction"])
    runs = {}
    for run in man["runs"]:
        d = read_run(run)
        if d["episodes_cfg"] != N:
            raise ValueError(f"{run['id']}: WandB budget {d['episodes_cfg']} != {N}")
        reached = d["rows"][-1]["Episode/Number"]
        cal = d["calibration"] or {}
        cal_ok = all(cal.get(k) == v for k, v in man["calibration"].items())
        rows = d["rows"]
        d.update(run)
        d.update({"reached": reached, "complete": reached >= N and d["complete_log"], "calibration_ok": cal_ok,
                  "win": pool(window(rows, N - f * N, N)),
                  "prev": pool(window(rows, N - 2 * f * N, N - f * N)),
                  "ts_18": ts_at(rows, N - f * N), "ts_20": ts_at(rows, N),
                  "blocks": [pool(window(rows, N * b / 10, N * (b + 1) / 10)) for b in range(10)]})
        d["rise"] = d["win"]["S"] / d["prev"]["S"] - 1
        d["still_learning"] = d["rise"] > 0.05
        del d["rows"]
        d["_rows"] = rows
        runs[run["id"]] = d

    ref_ids = [r["id"] for r in man["runs"] if man["worlds"][r["world"]]["arm"] == "reference"]
    gate = {}
    for rid, g in man["replication_gate"].items():
        S = runs[rid]["win"]["S"]
        gate[rid] = {"S": S, "target": g["target"], "tol": g["tol"], "pass": abs(S - g["target"]) <= g["tol"]}
    S_ref = float(np.mean([runs[i]["win"]["S"] for i in ref_ids]))
    D_ref = float(np.mean([runs[i]["win"]["D"] for i in ref_ids]))
    ts_ref = float(np.mean([runs[i]["ts_20"] for i in ref_ids]))
    pooled_ref = pool(sum((window(runs[i]["_rows"], N - f * N, N) for i in ref_ids), []))
    gap_keys = ["S", "D", "LateDeathShare", "EatRatio", "HideRatio_True", "HideRatio_True_Fed",
                "TimeBush", "TimeWarm", "TimeEat", "TimeElsewhere"]
    a, b = (runs[i]["win"] for i in ref_ids[:2])
    gaps = {k: abs(a[k] - b[k]) if (a[k] is not None and b[k] is not None) else 0.0 for k in gap_keys}

    for d in runs.values():
        d["crit"] = criteria(d["win"], S_ref, D_ref)
        d["surv_ratio"] = d["win"]["S"] / S_ref
        d["step_ratio"] = d["ts_20"] / ts_ref
    ref_pooled_crit = criteria(pooled_ref, S_ref, D_ref)
    withheld = [c for c in (1, 2, 5) if not ref_pooled_crit[c] or any(not runs[i]["crit"][c] for i in ref_ids)]
    kept = [c for c in (1, 2, 4, 5) if c not in withheld]

    worlds = {}
    for d in runs.values():
        wk = d["world"]
        W = man["worlds"][wk]
        sim = {int(k): v for k, v in W["sim_c"].items()}
        agree = all(int(d["crit"][c]) == sim[c] for c in kept)
        c4_disagree = int(d["crit"][4]) != sim[4]
        bl = [] if W["arm"] == "reference" else borderline(d["win"], S_ref, D_ref, gaps)
        balanced = all(d["crit"][c] for c in kept) and d["crit"]["3fwd"]
        if W["arm"] == "reference":
            fwd = "reference (not forwarded)"
        elif not d["complete"] or not d["calibration_ok"]:
            fwd = "invalid run"
        elif d["still_learning"]:
            fwd = "withheld: still learning"
        elif not balanced:
            fwd = "not forwarded"
        elif c4_disagree:
            fwd = "pending seed 43 (criterion 4 disagrees with the simulation)"
        elif bl:
            fwd = "pending seed 43 (borderline)"
        else:
            fwd = "forward"
        d.update({"arm": W["arm"], "sim": sim, "agree": agree, "c4_disagree": c4_disagree,
                  "borderline": bl, "balanced_fwd": balanced, "forward": fwd})
        worlds[d["id"]] = wk

    nonref = [d for d in runs.values() if d["arm"] != "reference"]
    n_agree = sum(d["agree"] for d in nonref)
    too_pess = [d["id"] for d in nonref if d["arm"] == "edge" and d["crit"][4]]
    too_opt = [d["id"] for d in nonref if d["arm"] == "balanced" and not d["crit"][4]]
    trust = n_agree >= 5 and not too_pess and not too_opt
    fwd = [d for d in nonref if d["forward"] == "forward"]
    fwd.sort(key=lambda d: (d["arm"] != "edge", -man["worlds"][d["world"]]["search"]))
    for d in runs.values():
        d.pop("_rows")
    return {"runs": runs, "gate": gate, "gate_pass": all(g["pass"] for g in gate.values()),
            "S_ref": S_ref, "D_ref": D_ref, "ts_ref": ts_ref, "gaps": gaps, "pooled_ref": pooled_ref,
            "ref_pooled_crit": {str(k): v for k, v in ref_pooled_crit.items()},
            "withheld": withheld, "kept": kept, "n_agree": n_agree, "n_nonref": len(nonref),
            "too_pessimistic": too_pess, "too_optimistic": too_opt, "trust": trust,
            "trust_label": "survival-only" if not [c for c in kept if c != 4] else "",
            "forward_order": [d["id"] for d in fwd][:3]}


def fmt(x, n=2):
    return "n/c" if x is None else f"{x:.{n}f}"


def yn(b):
    return "pass" if b else "FAIL"


def render(man, R) -> str:
    runs = R["runs"]
    L = []
    L.append("**Run validity.**\n")
    L.append("| Run | World | Seed (WandB) | Budget (WandB) | Last episode logged | 'Training complete' | Calibration = level 05 | Obs width | Modulator off | Bal keys on first row | Env steps at 1.8 M | Env steps at 2.0 M | Step ratio vs reference |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in runs.values():
        L.append(f"| {d['id']} | `{d['world']}` | {d['seed_cfg']} | {d['episodes_cfg']:,} | {d['reached']:,.0f} | "
                 f"{'yes' if d['complete_log'] else 'NO'} | {'yes' if d['calibration_ok'] else 'NO'} | {d['obs_dim']} | "
                 f"{'yes' if d['nmn_disabled'] else 'NO'} | {d['first_row_bal_keys']} | {d['ts_18']:,.0f} | {d['ts_20']:,.0f} | {d['step_ratio']:.2f} |")
    L.append("")
    L.append("**Replication gate** (reference runs vs the level-05 pilots at 2 M):\n")
    L.append("| Run | Survival steps, last 10 % | Pilot target | Allowed range | Result |")
    L.append("|---|---|---|---|---|")
    for rid, g in R["gate"].items():
        L.append(f"| {rid} | {g['S']:.1f} | {g['target']} | {g['target']-g['tol']:.1f}-{g['target']+g['tol']:.1f} | {yn(g['pass'])} |")
    L.append("")
    L.append(f"Reference survival S_ref = mean(C1a, C1b) = **{R['S_ref']:.1f}** steps; criterion-4 line 0.8 x S_ref = "
             f"{0.8*R['S_ref']:.1f}. Reference dominant late-death share D_ref = {R['D_ref']:.3f}; criterion-3-fwd line = "
             f"max(0.60, D_ref + 0.05) = {max(0.60, R['D_ref']+0.05):.3f}.\n")
    L.append("**Survival and still-learning flag** (survival steps per episode, `_window_n`-weighted):\n")
    L.append("| Run | World | Arm | S 1.6-1.8 M | S 1.8-2.0 M | Rise | Still learning (> 5 %) | Survival vs reference | Sim survival vs today |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for d in runs.values():
        W = man["worlds"][d["world"]]
        L.append(f"| {d['id']} | `{d['world']}` | {d['arm']} | {d['prev']['S']:.1f} | {d['win']['S']:.1f} | {100*d['rise']:+.1f} % | "
                 f"{'**YES**' if d['still_learning'] else 'no'} | {d['surv_ratio']:.2f} | {W['sim_surv']:.2f} |")
    L.append("")
    L.append("**Criterion values, last 10 %** (shares as fractions; ratios pooled, per-row mean in brackets):\n")
    L.append("| Run | Bush | Warm cell | Eating | Elsewhere | Near fire (report) | Eat ratio | Hide ratio, true injury | Hide ratio, felt (report) | Hide ratio among fed, true | Warm ratio (report) | Early-death share | Late-death share | Late deaths: starvation / overeating / injury / thermal | All deaths: starvation / injury / thermal / reached cap |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in runs.values():
        w = d["win"]
        L.append(f"| {d['id']} | {fmt(w['TimeBush'],3)} | {fmt(w['TimeWarm'],3)} | {fmt(w['TimeEat'],3)} | {fmt(w['TimeElsewhere'],3)} | "
                 f"{fmt(w['TimeNearFire'],3)} | {fmt(w['EatRatio'])} ({fmt(w['EatRatio_rowmean'])}) | "
                 f"{fmt(w['HideRatio_True'])} ({fmt(w['HideRatio_True_rowmean'])}) | {fmt(w['HideRatio_Felt'])} | "
                 f"{fmt(w['HideRatio_True_Fed'])} ({fmt(w['HideRatio_True_Fed_rowmean'])}) | {fmt(w['WarmRatio'])} | "
                 f"{fmt(w['EarlyDeathShare'],3)} | {fmt(w['LateDeathShare'],3)} | "
                 f"{fmt(w['LateDeath_Starvation'],2)} / {fmt(w['LateDeath_Overeating'],2)} / {fmt(w['LateDeath_Injury'],2)} / {fmt(w['LateDeath_Thermal'],2)} | "
                 f"{fmt(w['Term_Starvation'],2)} / {fmt(w['Term_Injury'],2)} / {fmt(w['Term_Thermal'],2)} / {fmt(w['Term_MaxSteps'],2)} |")
    L.append("")
    p = R["pooled_ref"]
    L.append(f"Reference pooled over both seeds: bush {fmt(p['TimeBush'],3)}, warm {fmt(p['TimeWarm'],3)}, eat {fmt(p['TimeEat'],3)}, "
             f"elsewhere {fmt(p['TimeElsewhere'],3)}; eat ratio {fmt(p['EatRatio'])}; hide ratio {fmt(p['HideRatio_True'])}; "
             f"hide among fed {fmt(p['HideRatio_True_Fed'])}; criteria 1/2/5 pooled: "
             f"{yn(R['ref_pooled_crit']['1'])}/{yn(R['ref_pooled_crit']['2'])}/{yn(R['ref_pooled_crit']['5'])}.\n")
    L.append("Reference seed gaps (C1a vs C1b; the borderline band is the larger of this and the floor): "
             + ", ".join(f"{k} {v:.3f}" for k, v in R["gaps"].items()) + ".\n")
    L.append("**Verdicts per criterion** (trained agent):\n")
    L.append("| Run | World | 1 time split | 2 eat & hide | 3 deaths (absolute 60 %) | 3-fwd (reference-relative) | Dominant late cause | 4 survival | 5 hide among fed | Borderline quantities | Forwarding |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for d in runs.values():
        c = d["crit"]
        L.append(f"| {d['id']} | `{d['world']}` | {yn(c[1])} | {yn(c[2])} | {yn(c[3])} | {yn(c['3fwd'])} | "
                 f"{d['win']['D_cause']} {fmt(d['win']['D'],2)} | {yn(c[4])} | {yn(c[5])} | "
                 f"{'; '.join(d['borderline']) or '-'} | {d['forward']} |")
    L.append("")
    L.append(f"Withheld criteria (reference fails them in training, R1.2): **{', '.join(map(str, R['withheld'])) or 'none'}**; "
             f"agreement scored on: {', '.join(map(str, R['kept']))}.\n")
    L.append("**Agreement with the simulation** (sim / trained, pass = 1):\n")
    L.append("| Run | World | Arm | Crit 1 | Crit 2 | Crit 4 | Crit 5 | Trained crit 3 (abs / fwd) | Survival vs today, sim / trained | Late deaths injury / starvation, sim / trained | Step ratio | Agree (scored criteria) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in runs.values():
        W = man["worlds"][d["world"]]
        cells = []
        for c in (1, 2, 4, 5):
            s = f"{d['sim'][c]} / {int(d['crit'][c])}"
            cells.append(s + (" (withheld)" if c in R["withheld"] else ""))
        L.append(f"| {d['id']} | `{d['world']}` | {d['arm']} | " + " | ".join(cells) +
                 f" | {int(d['crit'][3])} / {int(d['crit']['3fwd'])} | {W['sim_surv']:.2f} / {d['surv_ratio']:.2f} | "
                 f"{W['sim_inj']:.2f} / {fmt(d['win']['LateDeath_Injury'])} ; {W['sim_starve']:.2f} / {fmt(d['win']['LateDeath_Starvation'])} | "
                 f"{d['step_ratio']:.2f} | {'yes' if d['agree'] else 'no'} |")
    L.append("")
    L.append(f"Non-reference agreements: **{R['n_agree']} / {R['n_nonref']}**. Edge worlds passing criterion 4 (sim too pessimistic): "
             f"{', '.join(R['too_pessimistic']) or 'none'}. Balanced worlds failing criterion 4 (sim too optimistic): "
             f"{', '.join(R['too_optimistic']) or 'none'}. Trust verdict: **{'trustworthy' if R['trust'] else 'not trustworthy'}"
             f"{' (' + R['trust_label'] + ')' if R['trust_label'] else ''}**.\n")
    L.append(f"Forward order (max 3): {', '.join(R['forward_order']) or 'none'}.\n")
    L.append("**Temporal evolution** (200,000-episode blocks, 0-0.2 M ... 1.8-2.0 M):\n")
    for key, lab, n in (("S", "Survival steps", 0), ("FoodEaten", "Food bites eaten per episode (report-only)", 2), ("TimeWarm", "Warm-cell time share", 3), ("TimeBush", "Bush time share", 3),
                        ("TimeEat", "Eating time share", 3), ("EatRatio", "Eat ratio", 2), ("HideRatio_True", "Hide ratio (true injury)", 2),
                        ("HideRatio_True_Fed", "Hide ratio among fed", 2), ("LateDeathShare", "Late-death share", 3),
                        ("LateDeath_Injury", "Injury share of late deaths", 2), ("LateDeath_Starvation", "Starvation share of late deaths", 2)):
        L.append(f"*{lab}*\n")
        L.append("| Run | " + " | ".join(f"{0.2*(i+1):.1f} M" for i in range(10)) + " |")
        L.append("|---|" + "---|" * 10)
        for d in runs.values():
            L.append(f"| {d['id']} | " + " | ".join(fmt(b.get(key), n) for b in d["blocks"]) + " |")
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest")
    ap.add_argument("--md-out")
    ap.add_argument("--json-out")
    a = ap.parse_args()
    man = yaml.safe_load(open(_abs(a.manifest)))
    R = analyse(man)
    md = render(man, R)
    print(md)
    if a.md_out:
        open(a.md_out, "w").write(md)
    if a.json_out:
        json.dump(R, open(a.json_out, "w"), indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
