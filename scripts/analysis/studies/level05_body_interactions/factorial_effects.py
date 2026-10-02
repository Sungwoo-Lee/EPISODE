#!/usr/bin/env python3
"""factorial_effects.py -- the 2^k factorial effects of the level-05 body-interactions screen (§4.2-4.3).

Plain language: each of the 16 worlds switches four body rules on or off. For every measure this
script asks how much switching a rule on (or a pair, triple, all four) changes the gap between the
modulated and the ordinary agent (`D_w` = modulated minus ordinary, per world), and the same for
each agent on its own. With one training run per cell there is no replicate, so noise is judged the
standard way for an unreplicated two-level factorial: Lenth's pseudo standard error (PSE), taken
from the bulk of small effects. Nothing is called significant; effects above the simultaneous
margin are only flagged.

Inputs (all from the analysis manifest's out_dir, produced by the sibling scripts):
  state_contrasts.json   measures 1 and 3 (true and felt injury), store survival
  combination_gain.json  measure 4
and, for measure 2, the LOCAL WandB binary of each run (manifest `wandb_ids`), read with
pilot_pick.py's reader: S = `Episode/_window_n`-weighted mean of `Episode/Steps` over rows with
`Episode/Number` in ((1 - f) N, N], f = survival_readout_fraction; reward is never read.

Effects (k factors, world code digit i = factor i, 1 = on, coded x_i = +1 / -1):
  effect(S) = sum_w y_w * prod_{i in S} x_i / 2^(k-1)   for every non-empty factor subset S
  (a main effect = mean over on-cells minus mean over off-cells; interactions the standard +- contrast)
Lenth (m = 2^k - 1 effects, d = m / 3 degrees of freedom):
  s0  = 1.5 * median |c|;  PSE = 1.5 * median { |c| : |c| < 2.5 s0 }
  ME  = t(1 - alpha/2, d) * PSE;   SME = t(gamma, d) * PSE, gamma = (1 + (1 - alpha)^(1/m)) / 2
  also reported: sqrt(2) x SME and sqrt(2) x ME (for comparing two effects)
Collapsed cells (§5): a world is collapsed for an agent when its WandB survival is below
  collapse_fraction x that agent's survival in the all-off world. When any cell collapses, effects
  are ALSO reported without the collapsed world(s): an ordinary least-squares fit of the intercept,
  main effects and two-way interactions on the remaining worlds (effect = 2 x coefficient), with no
  Lenth margin (the design is no longer orthogonal). A measure with any "not computable" or missing
  world gets no effects at all; the reason is printed.

Outputs: factorial_effects.json and factorial_effects.md in out_dir (tables only, no reading).

Usage:
  $PY scripts/analysis/studies/level05_body_interactions/factorial_effects.py MANIFEST
      [--allow-partial]   read *_PARTIAL inputs and accept runs that have not finished training
                          (tooling tests only; every output is stamped PARTIAL)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

_spec = importlib.util.spec_from_file_location("pilot_pick", Path(__file__).resolve().parent / "pilot_pick.py")
PP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PP)


# ----------------------------------------------------------------------------------- survival --
def wandb_survival(man, label, frac, allow_partial, cache_dir: Path, run_name: str):
    wid = man["wandb_ids"].get(label)
    if not wid:
        return {"status": f"no wandb_id for {label}"}
    cp = cache_dir / f"{wid}.json"
    if cp.exists():
        return json.loads(cp.read_text())
    try:
        wdir = PP.wandb_dir_for({"id": label, "wandb_id": wid})
        rows, cfg = PP.read_history(wdir, allow_truncated=allow_partial)
    except Exception as e:                                   # reported, never silently filled
        return {"status": f"unreadable: {type(e).__name__}: {e}"}
    if not cfg.get("tag") or not run_name.endswith(cfg["tag"]):   # guard a mis-mapped wandb_id
        return {"status": f"WandB tag {cfg.get('tag')!r} does not match run dir {run_name!r}"}
    N = int(cfg["episodes"])
    reached = max(r["Number"] for r in rows)
    complete = reached >= N
    if not complete and not allow_partial:
        return {"status": f"incomplete ({reached:.0f}/{N} episodes)"}
    end = N if complete else reached
    S, n = PP.weighted(rows, end - frac * end, end, "Steps")
    rec = {"status": "ok" if complete else "PARTIAL", "wandb_id": wid, "tag": cfg.get("tag"),
           "episodes": N, "reached": reached, "window": [end - frac * end, end], "rows": n, "S": S}
    if complete:
        C.write_json(cp, rec)
    return rec


# ------------------------------------------------------------------------------------ effects --
def effect_names(factors):
    k = len(factors)
    return [s for r in range(1, k + 1) for s in combinations(range(k), r)]


def design(worlds, k):
    """x[w, i] = +1 / -1 from the world code 'w' + k digits."""
    return np.array([[1 if w[1 + i] == "1" else -1 for i in range(k)] for w in worlds], float)


def all_effects(y, X, subsets):
    k = X.shape[1]
    return np.array([(y * np.prod(X[:, list(s)], axis=1)).sum() / 2 ** (k - 1) for s in subsets])


def lenth(c, alpha):
    from scipy.stats import t
    a = np.abs(c)
    m = a.size
    s0 = 1.5 * np.median(a)
    trimmed = a[a < 2.5 * s0]
    pse = 1.5 * np.median(trimmed) if trimmed.size else float("nan")
    d = m / 3.0
    gamma = (1 + (1 - alpha) ** (1.0 / m)) / 2
    me = t.ppf(1 - alpha / 2, d) * pse
    sme = t.ppf(gamma, d) * pse
    return {"PSE": pse, "s0": s0, "df": d, "ME": me, "SME": sme, "t_ME": t.ppf(1 - alpha / 2, d),
            "t_SME": t.ppf(gamma, d), "gamma": gamma, "sqrt2_ME": math.sqrt(2) * me,
            "sqrt2_SME": math.sqrt(2) * sme}


def ols_without(y, X, keep):
    """Intercept + main effects + two-way interactions on the kept worlds; effect = 2 x coef."""
    k = X.shape[1]
    subsets = [s for r in (1, 2) for s in combinations(range(k), r)]
    Z = np.column_stack([np.ones(keep.sum())] + [np.prod(X[keep][:, list(s)], axis=1) for s in subsets])
    coef, *_ = np.linalg.lstsq(Z, y[keep], rcond=None)
    return subsets, 2 * coef[1:]


def name(s, factors):
    return " x ".join(factors[i] for i in s)


# ---------------------------------------------------------------------------------------- main --
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--allow-partial", action="store_true")
    a = ap.parse_args(argv)
    man = C.load_manifest(a.manifest)
    od = C.out_dir(man)
    sfx = "_PARTIAL" if a.allow_partial else ""
    factors = list(man["factors"])
    k = len(factors)
    hi, lo = man["difference"]
    alpha = float(man["lenth_alpha"])

    sc = json.loads((od / f"state_contrasts{sfx}.json").read_text())
    cg = json.loads((od / f"combination_gain{sfx}.json").read_text())
    if sc["partial"] != a.allow_partial or cg["partial"] != a.allow_partial:
        raise ValueError("input PARTIAL stamps do not match --allow-partial")

    worlds = sorted({r["world"] for r in man["_runs"]})
    if len(worlds) != 2 ** k:
        raise ValueError(f"{len(worlds)} worlds for {k} factors; a full 2^{k} design is required")
    label = {(r["world"], r["agent"]): r["label"] for r in man["_runs"]}

    # survival (measure 2) from WandB
    cache = od / "cache" / "survival"
    cache.mkdir(parents=True, exist_ok=True)
    run_name = {r["label"]: r["run_name"] for r in man["_runs"]}
    surv = {lab: wandb_survival(man, lab, float(man["survival_readout_fraction"]), a.allow_partial, cache,
                                run_name[lab]) for lab in label.values()}

    # per-world, per-agent values of every measure; None = unavailable (with a reason)
    measures = {}

    def put(mname, w, agent, val, why=None):
        measures.setdefault(mname, {}).setdefault(w, {})[agent] = (val, why)

    for w in worlds:
        scw = sc["worlds"].get(w, {})
        for axis in ("true", "felt"):
            basis = scw.get(f"{axis}_basis", scw.get("status", "missing"))
            for m in ("M1", "M3"):
                for ag in (hi, lo):
                    v = scw.get(f"{m}_{axis}_{ag}") if scw.get("status") == "ok" else None
                    put(f"{m}_{axis}", w, ag, v, None if v is not None else basis)
        cgw = cg["worlds"].get(w, {})
        for ag in (hi, lo):
            v = cgw.get(f"gain_points_{ag}") if cgw.get("status") == "ok" else None
            put("combination_gain_points", w, ag, v, None if v is not None else cgw.get("status", "missing"))
            s = surv[label[(w, ag)]]
            put("survival_wandb", w, ag, s.get("S"), None if s.get("S") is not None else s["status"])
            rs = sc["runs"][label[(w, ag)]]["final"]
            put("survival_store", w, ag, rs["survival_store"]["mean_length"] if rs else None,
                None if rs else "missing store")

    # collapsed cells (§5), from WandB survival
    base = worlds[0]
    assert set(base[1:]) == {"0"}, "the first world must be the all-off world"
    collapsed, collapse_note = [], {}
    for ag in (hi, lo):
        b = surv[label[(base, ag)]].get("S")
        for w in worlds:
            s = surv[label[(w, ag)]].get("S")
            if b is None or s is None:
                collapse_note[f"{w}_{ag}"] = "not evaluated (survival unavailable)"
            elif s < float(man["collapse_fraction"]) * b:
                collapsed.append(w)
                collapse_note[f"{w}_{ag}"] = f"collapsed: S={s:.1f} < {man['collapse_fraction']} x {b:.1f}"
    collapsed = sorted(set(collapsed))

    X = design(worlds, k)
    subsets = effect_names(factors)
    results = {}
    for mname, per_w in measures.items():
        res = {"worlds": {}}
        series = {}
        for tag in ("D", hi, lo):
            vals, missing = [], []
            for w in worlds:
                (vh, why_h), (vl, why_l) = per_w[w][hi], per_w[w][lo]
                if tag == "D":
                    ok = vh is not None and vl is not None
                    vals.append(vh - vl if ok else None)
                    if not ok:
                        missing.append(f"{w}: {why_h or why_l}")
                else:
                    v, why = per_w[w][tag]
                    vals.append(v)
                    if v is None:
                        missing.append(f"{w}: {why}")
            series[tag] = (vals, missing)
        for i, w in enumerate(worlds):
            res["worlds"][w] = {t: series[t][0][i] for t in series}
        for tag, (vals, missing) in series.items():
            key = f"D ({hi} - {lo})" if tag == "D" else tag
            if missing:
                res[key] = {"status": "not computed", "missing": missing}
                continue
            y = np.array(vals, float)
            c = all_effects(y, X, subsets)
            L = lenth(c, alpha)
            eff = [{"effect": name(s, factors), "order": len(s), "value": float(v),
                    "exceeds_ME": bool(abs(v) > L["ME"]), "exceeds_SME": bool(abs(v) > L["SME"])}
                   for s, v in zip(subsets, c)]
            out = {"status": "ok", "grand_mean": float(y.mean()), "effects": eff, "lenth": L}
            if collapsed:
                keep = np.array([w not in collapsed for w in worlds])
                ss, ce = ols_without(y, X, keep)
                out["without_collapsed"] = {"dropped_worlds": collapsed,
                                            "effects": [{"effect": name(s, factors), "value": float(v)}
                                                        for s, v in zip(ss, ce)],
                                            "note": "OLS, main + two-way; no Lenth margin"}
            res[key] = out
        results[mname] = res

    out = {"generated": datetime.now().isoformat(timespec="seconds"), "manifest": a.manifest,
           "partial": a.allow_partial, "factors": factors, "factor_labels": man.get("factor_labels"),
           "worlds": worlds, "difference": f"{hi} - {lo}", "alpha": alpha,
           "collapsed_worlds": collapsed, "collapse_notes": collapse_note, "survival_wandb": surv,
           "measures": results}
    C.write_json(od / f"factorial_effects{sfx}.json", out)
    (od / f"factorial_effects{sfx}.md").write_text(render(out))
    print(render(out))


def render(out) -> str:
    L = [f"# Factorial effects{' (PARTIAL - tooling test, not a result)' if out['partial'] else ''}",
         f"generated {out['generated']}; D = {out['difference']}; factors "
         + ", ".join(f"{f} = {out['factor_labels'].get(f, f)}" for f in out["factors"]),
         f"collapsed worlds: {out['collapsed_worlds'] or 'none'}", ""]
    for m, res in out["measures"].items():
        L.append(f"## {m}")
        for key, r in res.items():
            if key == "worlds":
                continue
            if r["status"] != "ok":
                L.append(f"- {key}: not computed ({len(r['missing'])} world(s) unavailable: "
                         + "; ".join(r["missing"][:4]) + (" ..." if len(r["missing"]) > 4 else "") + ")")
                continue
            l_ = r["lenth"]
            L.append(f"### {key}: grand mean {r['grand_mean']:.4g}; PSE {l_['PSE']:.4g}, ME {l_['ME']:.4g}, "
                     f"SME {l_['SME']:.4g}, sqrt2xSME {l_['sqrt2_SME']:.4g}")
            L.append("| effect | value | > ME | > SME |")
            L.append("|---|---:|:-:|:-:|")
            for e in r["effects"]:
                L.append(f"| {e['effect']} | {e['value']:.4g} | {'x' if e['exceeds_ME'] else ''} | "
                         f"{'x' if e['exceeds_SME'] else ''} |")
            if "without_collapsed" in r:
                wc = r["without_collapsed"]
                L.append(f"Without collapsed {wc['dropped_worlds']} ({wc['note']}): "
                         + ", ".join(f"{e['effect']} {e['value']:.4g}" for e in wc["effects"]))
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
