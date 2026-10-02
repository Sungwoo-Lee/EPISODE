#!/usr/bin/env python3
"""screen.py - which settings move each behaviour: exploratory screening across runs (plan B5, A7).

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2).

    P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
    nice -n 19 $P scripts/analysis/basic_behaviour/screen.py --population <population.json> \
        --out-root /abs/results/analysis/basic_behaviour/<pop> --target bush_dwell \
        --control-world hv2ch --reference-agent t1none

EXPLORATORY, NOT A VERDICT. Each training run is one replicate, so every uncertainty here comes from
how much the seeds of a setting disagree, never from the ~1 M episodes inside a run.

Stage 1, per run: the behaviour level (share of chosen steps and its logit) and a quasi-binomial
model on episodes with exactly one rabbit: start injury and start nutrition (per 10 points), the
rabbit's smell in nats, smell x start injury, plus the M1 exogenous covariates included in every
run. The smell regressor follows the smell study's registered reading: the scent statistic on its
evidence scale in single-channel / matched-strength worlds; channel 1 in nats with channel 2 as a
covariate in the two-channel control world (the plain x1 - x2 reading is fitted beside it,
descriptive). Outputs: logit coefficients with episode-level SEs, and average marginal effects in
percentage points (the interaction's by finite difference of fitted probabilities).

Stage 2, across runs, per quantity: cell-means OLS on the world x agent cells built from the manifest
(df computed, never typed; refuses when any cell has < 2 runs), contrasts with run-level SEs and exact
t, standardised effects (the primary ranking), method-of-moments variance components truncated at 0
with their pure-noise reference marks (secondary), per-cell SDs + the largest per-run SE per cell,
Welch contrasts when cell SDs differ more than 3-fold, exact permutation of world labels within agent
(unrestricted and within-seed), and the "conditional on these runs" SE. Smell terms carry no test,
no interval and no variance share (Revision 2, N5) - the smell study's registered reading decides.

Outputs: <out-root>/screen/<target>/{per_run,cells,contrasts,variance,permutation}.csv, prefit.json.
Requires the golden stamp and every cell of the population completed and swept.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry as REG                                                  # noqa: E402
import fit as FT                                                        # noqa: E402

from hiding_drivers import quasi_binomial_fit                           # noqa: E402

QUANTITIES = ["level", "start_injury", "start_nutrition", "smell", "smell_x_injury"]
SMELL_Q = {"smell", "smell_x_injury"}
WELCH_SD_RATIO = 3.0
PERM_LIMIT = 2_000_000


# ------------------------------------------------------------------------------- stage 1 ----
def level(Y, L):
    """Share, its logit, and the logit's quasi-binomial SE (Pearson dispersion, intercept-only)."""
    p = Y.sum() / L.sum()
    k = L > 0
    mu = L[k] * p
    phi = float(((Y[k] - mu) ** 2 / (L[k] * p * (1 - p))).sum() / (k.sum() - 1))
    se = math.sqrt(phi / (L.sum() * p * (1 - p)))
    return p, math.log(p / (1 - p)), se


def smell_regressors(cell: FT.Cell, world_layout: str, spec: dict, c2tag: str) -> dict:
    """{'smell': nats, optional 'smell_ch2_cov': raw, 'smell_plain': nats} per the study's reading."""
    from env import ScentSpec
    S = ScentSpec(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in spec.items()
                     if k in ScentSpec.__dataclass_fields__})
    if world_layout == "difference":
        c1, c2 = S.channels
        mid, k1 = S.channel_scale(c1)
        x1 = cell.a(f"smellch__{c2tag}__{c1}")
        return {"smell": (x1 - mid) * k1, "smell_ch2_cov": cell.a(f"smellch__{c2tag}__{c2}"),
                "smell_plain": cell.a("rab_smell_llr")}
    return {"smell": cell.a("rab_smell_llr")}


def stage1_run(cell: FT.Cell, target: str, covariates: list[str], c2tag: str | None) -> list[dict]:
    import pandas as pd
    Y, L = FT.target_arrays(cell, target)
    inv = cell.inv
    p, lg, se = level(Y, L)
    rows = [{"quantity": "level", "coef": lg, "se_episode": se, "ame_pp": 100 * p, "n": int((L > 0).sum()),
             "share_pct": 100 * p}]
    keep = (cell.a(f"cnt__{c2tag}") == 1) if c2tag else np.ones(cell.n, bool)
    inj = cell.factor("start_injury") / 10.0
    nut = cell.factor("start_nutrition") / 10.0

    def model(smell_key):
        X = {"start_injury": inj, "start_nutrition": nut}
        sm = None
        if c2tag:
            sr = smell_regressors(cell, inv["scent"]["layout"], inv["scent"], c2tag)
            sm = sr[smell_key]
            X["smell"] = sm
            X["smell_x_injury"] = sm * inj
            if smell_key == "smell" and "smell_ch2_cov" in sr:
                X["smell_ch2_cov"] = sr["smell_ch2_cov"]
        for c in covariates:
            X[c] = cell.factor(c)
        Xd = pd.DataFrame(X)
        f = quasi_binomial_fit(Xd, keep, "screen", Y, L)
        k = keep & np.isfinite(Xd.to_numpy()).all(1)
        beta = f.set_index("term")["coef"]
        Xk = Xd[k]
        eta = beta["const"] + Xk.to_numpy() @ beta[Xd.columns].to_numpy()
        pr = 1 / (1 + np.exp(-eta))
        out = {}
        for t in ["start_injury", "start_nutrition"] + (["smell", "smell_x_injury"] if c2tag else []):
            r = f[f.term == t].iloc[0]
            out[t] = {"coef": float(r.coef), "se_episode": float(r.se), "n": int(r.n),
                      "ame_pp": float(np.mean(r.coef * pr * (1 - pr)) * 100)}
        if c2tag:
            # interaction in pp: change of the smell effect per +10 points of start injury, by finite
            # difference of fitted probabilities (a logit product coefficient is not a marginal effect)
            bs, bi = beta["smell"], beta["smell_x_injury"]
            i0 = Xk["start_injury"].to_numpy()

            def smell_effect(ishift):
                e = eta + beta["start_injury"] * ishift + bi * Xk["smell"].to_numpy() * ishift
                q = 1 / (1 + np.exp(-e))
                return (bs + bi * (i0 + ishift)) * q * (1 - q)
            out["smell_x_injury"]["ame_pp"] = float(np.mean(smell_effect(1.0) - smell_effect(0.0)) * 100)
        return out
    main = model("smell")
    for q in ["start_injury", "start_nutrition", "smell", "smell_x_injury"]:
        if q in main:
            rows.append({"quantity": q, **main[q]})
    if c2tag and inv["scent"]["layout"] == "difference":
        plain = model("smell_plain")
        for q in ("smell", "smell_x_injury"):
            rows.append({"quantity": f"{q}__plain_control_reading", **plain[q]})
    return rows


# ------------------------------------------------------------------------------- stage 2 ----
def design(runs: list[dict]) -> dict:
    """Cells from the runs' world x agent labels; df and counts computed (plan Revision 2, N3)."""
    cells = sorted({(r["world"], r["agent"]) for r in runs})
    n = {c: sum(1 for r in runs if (r["world"], r["agent"]) == c) for c in cells}
    short = [c for c, k in n.items() if k < 2]
    return {"cells": cells, "n": n, "N": len(runs), "df": len(runs) - len(cells),
            "refuse": (f"cells with fewer than 2 completed runs: {short} -- the seed-to-seed SD is "
                       f"undefined, so the run-level screening cannot be computed") if short else None}


def tcdf2(t, df):
    from scipy import stats
    return float(2 * stats.t.sf(abs(t), df))


def stage2(runs: list[dict], values: np.ndarray, control_world: str | None, ref_agent: str | None,
           smell: bool = False, se_episode: np.ndarray | None = None) -> dict:
    """Cell means, pooled seed-to-seed SD, contrasts, Welch sensitivity. `runs` carry world/agent."""
    from scipy import stats
    D = design(runs)
    if D["refuse"]:
        raise SystemExit(D["refuse"])
    v = np.asarray(values, float)
    key = [(r["world"], r["agent"]) for r in runs]
    mean = {c: float(np.mean([x for x, k in zip(v, key) if k == c])) for c in D["cells"]}
    sdc = {c: float(np.std([x for x, k in zip(v, key) if k == c], ddof=1)) for c in D["cells"]}
    resid = np.array([x - mean[k] for x, k in zip(v, key)])
    df = D["df"]
    s = float(math.sqrt((resid ** 2).sum() / df))
    tq = float(stats.t.ppf(0.975, df))
    cells = []
    for c in D["cells"]:
        nc = D["n"][c]
        se = s / math.sqrt(nc)
        idx = [i for i, k in enumerate(key) if k == c]
        row = {"world": c[0], "agent": c[1], "n_runs": nc, "mean": mean[c], "se_run": se,
               "ci_lo": mean[c] - tq * se, "ci_hi": mean[c] + tq * se, "seed_sd_pooled": s,
               "cell_sd": sdc[c], "df": df,
               "min_run": float(v[idx].min()), "max_run": float(v[idx].max())}
        if se_episode is not None:
            e = np.asarray(se_episode, float)[idx]
            row["se_conditional_on_these_runs"] = float(math.sqrt((e ** 2).sum()) / nc)
            row["largest_run_se_episode"] = float(e.max())
        if smell:
            row["ci_lo"] = row["ci_hi"] = float("nan")          # no interval for smell terms (N5)
        cells.append(row)
    worlds = sorted({c[0] for c in D["cells"]})
    agents = sorted({c[1] for c in D["cells"]})
    cons = []
    if not smell:
        def add(name, w):
            est = sum(wi * mean[c] for c, wi in w.items())
            se = s * math.sqrt(sum(wi ** 2 / D["n"][c] for c, wi in w.items()))
            t = est / se if se > 0 else float("nan")
            row = {"contrast": name, "estimate": est, "se_run": se, "t": t, "df": df,
                   "p": tcdf2(t, df), "ci_lo": est - tq * se, "ci_hi": est + tq * se,
                   "standardised": est / s if s > 0 else float("nan"),
                   "std_ci_lo": (est - tq * se) / s if s > 0 else float("nan"),
                   "std_ci_hi": (est + tq * se) / s if s > 0 else float("nan")}
            sds = [sdc[c] for c in w]
            if max(sds) > WELCH_SD_RATIO * max(min(sds), 1e-300):
                a = [(wi ** 2) * sdc[c] ** 2 / D["n"][c] for c, wi in w.items()]
                sw = math.sqrt(sum(a))
                dfw = sum(a) ** 2 / sum(ai ** 2 / (D["n"][c] - 1) for ai, c in zip(a, w))
                row.update({"welch_se": sw, "welch_df": dfw, "welch_p": tcdf2(est / sw, dfw)})
            cons.append(row)
        if control_world and control_world in worlds:
            for a in agents:
                for w in worlds:
                    if w != control_world and (w, a) in mean and (control_world, a) in mean:
                        add(f"{w} - {control_world} | {a}", {(w, a): 1.0, (control_world, a): -1.0})
            for w in worlds:
                if w == control_world:
                    continue
                ok = all((w, a) in mean and (control_world, a) in mean for a in agents)
                if ok and len(agents) > 1:
                    wt = {}
                    for a in agents:
                        wt[(w, a)] = 1.0 / len(agents)
                        wt[(control_world, a)] = -1.0 / len(agents)
                    add(f"{w} - {control_world} | average over agents (sum-to-zero coding)", wt)
        if ref_agent and ref_agent in agents:
            for w in worlds:
                for a in agents:
                    if a != ref_agent and (w, a) in mean and (w, ref_agent) in mean:
                        add(f"{a} - {ref_agent} | {w}", {(w, a): 1.0, (w, ref_agent): -1.0})
            for a in agents:
                if a == ref_agent or len(worlds) < 2:
                    continue
                if all((w, a) in mean and (w, ref_agent) in mean for w in worlds):
                    wt = {}
                    for w in worlds:
                        wt[(w, a)] = 1.0 / len(worlds)
                        wt[(w, ref_agent)] = -1.0 / len(worlds)
                    add(f"{a} - {ref_agent} | average over worlds (sum-to-zero coding)", wt)
    return {"cells": cells, "contrasts": cons, "s": s, "df": df}


def variance_components(runs: list[dict], values) -> dict:
    """Method-of-moments shares for world, agent, world x agent, seed within agent, remainder (N1).

    Needs the balanced crossed design (every agent has the same seeds in every world, one run each).
    Share_f = (SS_f - df_f * MS_rem) / (SS_tot + MS_rem), truncated at 0 and flagged; the remainder is
    reported as 1 - sum of the truncated factor shares (its untruncated value N * MS_rem / (SS_tot +
    MS_rem) is kept beside it, and makes the untruncated shares sum to 1). Reference mark:
    df_f / df_tot, the share a factor's raw sum of squares takes under pure seed noise.
    """
    v = np.asarray(values, float)
    W = sorted({r["world"] for r in runs}); A = sorted({r["agent"] for r in runs})
    seeds = {a: sorted({r["seed"] for r in runs if r["agent"] == a}) for a in A}
    S = len(next(iter(seeds.values())))
    grid = {}
    for r, x in zip(runs, v):
        grid.setdefault((r["world"], r["agent"], r["seed"]), []).append(x)
    balanced = (all(len(seeds[a]) == S for a in A) and len(runs) == len(W) * len(A) * S
                and all(len(grid.get((w, a, s), [])) == 1 for w in W for a in A for s in seeds[a]))
    if not balanced or S < 2 or len(W) < 2:
        return {"unavailable": "variance components need a balanced design with every seed in every "
                               "world (one run each), at least 2 seeds and 2 worlds"}
    y = np.array([[[grid[(w, a, s)][0] for s in seeds[a]] for a in A] for w in W])   # [W, A, S]
    g = y.mean()
    yw, ya, ywa, yas = y.mean((1, 2)), y.mean((0, 2)), y.mean(2), y.mean(0)
    nW, nA = len(W), len(A)
    SS = {"world": nA * S * ((yw - g) ** 2).sum(),
          "agent": nW * S * ((ya - g) ** 2).sum(),
          "world x agent": S * ((ywa - yw[:, None] - ya[None, :] + g) ** 2).sum(),
          "shared starting weights (seed within agent)": nW * ((yas - ya[:, None]) ** 2).sum()}
    DF = {"world": nW - 1, "agent": nA - 1, "world x agent": (nW - 1) * (nA - 1),
          "shared starting weights (seed within agent)": nA * (S - 1)}
    SST = ((y - g) ** 2).sum(); N = y.size
    SSr = SST - sum(SS.values()); dfr = (N - 1) - sum(DF.values())
    MSr = SSr / dfr
    rows = []
    for f in [k for k in SS if DF[k] > 0]:         # a component with no degrees of freedom is absent
        raw = (SS[f] - DF[f] * MSr) / (SST + MSr)
        rows.append({"component": f, "df": DF[f], "ss": SS[f], "share_mom": max(raw, 0.0),
                     "share_mom_untruncated": raw, "truncated": raw < 0,
                     "share_raw_ss": SS[f] / SST if SST > 0 else float("nan"),
                     "pure_noise_reference": DF[f] / (N - 1)})
    # remainder: what the (truncated) factor shares leave, so the reported shares sum to 1
    rem_raw = N * MSr / (SST + MSr)
    rows.append({"component": "remainder", "df": dfr, "ss": SSr,
                 "share_mom": max(0.0, 1.0 - sum(r["share_mom"] for r in rows)),
                 "share_mom_untruncated": rem_raw, "truncated": False, "share_raw_ss": SSr / SST if SST > 0 else float("nan"),
                 "pure_noise_reference": dfr / (N - 1)})
    return {"rows": rows}


def _F(v, labels):
    groups = {}
    for x, l in zip(v, labels):
        groups.setdefault(l, []).append(x)
    g = np.mean(v)
    k, n = len(groups), len(v)
    ssb = sum(len(x) * (np.mean(x) - g) ** 2 for x in groups.values())
    ssw = sum(((np.asarray(x) - np.mean(x)) ** 2).sum() for x in groups.values())
    return (ssb / (k - 1)) / (ssw / (n - k)) if ssw > 0 else float("inf")


def _n_groupings(label_lists) -> int:
    """Distinct ways of splitting the runs into world groups, ignoring which name each group gets:
    the between-world F cannot change when worlds are merely renamed, so this is the number of
    distinct F values at most, and 1 / it is the smallest attainable p (Revision 2, N6)."""
    seen = set()
    for lab in label_lists:
        g = {}
        for i, l in enumerate(lab):
            g.setdefault(l, []).append(i)
        seen.add(frozenset(frozenset(v) for v in g.values()))
    return len(seen)


def _multiset_perms(labels):
    """All distinct orderings of a label multiset."""
    labels = sorted(labels)
    if len(labels) == 0:
        yield ()
        return
    for u in sorted(set(labels)):
        rest = list(labels)
        rest.remove(u)
        for p in _multiset_perms(rest):
            yield (u,) + p


def permutation(runs: list[dict], values) -> list[dict]:
    """Per agent: exact p for 'the worlds differ' (between-world F), all relabelings of world labels
    across that agent's runs, and the within-seed version (worlds permuted within each seed)."""
    v = np.asarray(values, float)
    out = []
    for a in sorted({r["agent"] for r in runs}):
        idx = [i for i, r in enumerate(runs) if r["agent"] == a]
        lab = [runs[i]["world"] for i in idx]
        x = v[idx]
        if len(set(lab)) < 2:
            continue
        nperm = math.factorial(len(lab)) // math.prod(math.factorial(lab.count(u)) for u in set(lab))
        if nperm > PERM_LIMIT:
            out.append({"agent": a, "kind": "unrestricted", "unavailable": f"{nperm} relabelings"})
            continue
        f0 = _F(x, lab)
        perms = list(_multiset_perms(lab))
        Fs = np.array([_F(x, p) for p in perms])
        ng = _n_groupings(perms)
        out.append({"agent": a, "kind": "unrestricted", "n_relabelings": len(Fs),
                    "n_distinct_groupings": ng, "n_distinct_F": int(len(np.unique(np.round(Fs, 10)))),
                    "F": f0, "p": float((Fs >= f0 - 1e-12).mean()), "smallest_possible_p": 1.0 / ng})
        by_seed = {}
        for i in idx:
            by_seed.setdefault(runs[i]["seed"], []).append(i)
        if all(sorted(runs[i]["world"] for i in g) == sorted(set(lab)) for g in by_seed.values()):
            groups = list(by_seed.values())
            perms = [list(itertools.permutations([runs[i]["world"] for i in g])) for g in groups]
            Fw, labs = [], []
            for combo in itertools.product(*perms):
                new = {}
                for g, pw in zip(groups, combo):
                    for i, w in zip(g, pw):
                        new[i] = w
                labs.append(tuple(new[i] for i in idx))
                Fw.append(_F(x, labs[-1]))
            Fw = np.array(Fw)
            ng = _n_groupings(labs)
            out.append({"agent": a, "kind": "within seed", "n_relabelings": len(Fw),
                        "n_distinct_groupings": ng, "n_distinct_F": int(len(np.unique(np.round(Fw, 10)))),
                        "F": f0, "p": float((Fw >= f0 - 1e-12).mean()), "smallest_possible_p": 1.0 / ng})
    return out


# ---------------------------------------------------------------------------------- main ----
def main(argv=None):
    import pandas as pd
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--target", required=True, choices=sorted(REG.TARGETS))
    ap.add_argument("--control-world", required=True, help="world the treated worlds are compared with")
    ap.add_argument("--reference-agent", required=True, help="agent the other agents are compared with")
    a = ap.parse_args(argv)
    FT.require_stamp()
    sys.path.insert(0, os.path.join(REG.A_DIR, "studies", "hypervigilance"))
    import readings as RD
    M = json.load(open(a.population))
    notdone = [c["label"] for c in M["cells"] if c["status"] != "completed"]
    if notdone:
        raise SystemExit(f"screen.py needs every cell of the population completed; not yet: {notdone}")
    pop = RD.load_population(a.population)
    runs = pop["cells"]
    unswept = [c["label"] for c in runs if not os.path.exists(os.path.join(a.out_root, c["label"], "episodes.npz"))]
    if unswept:
        raise SystemExit(f"cells not swept yet: {unswept}")
    D = design(runs)
    od = os.path.join(a.out_root, "screen", a.target)
    os.makedirs(od, exist_ok=True)
    if D["refuse"]:
        json.dump({"refused": D["refuse"]}, open(os.path.join(od, "prefit.json"), "w"), indent=1)
        raise SystemExit(D["refuse"])
    cells = {c["label"]: FT.Cell(a.out_root, c["label"]) for c in runs}
    pfs = {l: FT.prefit(c, a.target) for l, c in cells.items()}
    c2tags = {next((e["tag"] for e in c.inv["slots"]["entities"] if e["cls"] != "predator"), None)
              for c in cells.values()}
    if len(c2tags) != 1:
        raise SystemExit(f"runs disagree on the first neutral-class declaration: {c2tags}")
    c2tag = c2tags.pop()
    c2count = REG.ENTITY_NAMES.get(c2tag, {}).get("count", f"n_{c2tag}")
    eps = [set(f["name"] for f in pf["included"] if f["role"] == "episode") for pf in pfs.values()]
    covs = [f["name"] for f in next(iter(pfs.values()))["included"]
            if f["role"] == "episode" and all(f["name"] in e for e in eps)
            and f["name"] not in ("start_injury", "start_nutrition", c2count)]
    rows = []
    for c in runs:
        for r in stage1_run(cells[c["label"]], a.target, covs, c2tag):
            rows.append({"label": c["label"], "world": c["world"], "agent": c["agent"], "seed": c["seed"], **r})
    PR = pd.DataFrame(rows)
    PR.to_csv(os.path.join(od, "per_run.csv"), index=False)
    allc, allk, allv, allp = [], [], [], []
    for q in QUANTITIES:
        sub = PR[PR.quantity == q]
        if len(sub) != len(runs):
            continue
        rr = [{"world": r.world, "agent": r.agent, "seed": r.seed} for r in sub.itertuples()]
        res = stage2(rr, sub.coef.to_numpy(), a.control_world, a.reference_agent, smell=q in SMELL_Q,
                     se_episode=sub.se_episode.to_numpy())
        allc += [{"quantity": q, **x} for x in res["cells"]]
        allk += [{"quantity": q, **x} for x in res["contrasts"]]
        if q not in SMELL_Q:
            vc = variance_components(rr, sub.coef.to_numpy())
            allv += [{"quantity": q, **x} for x in vc.get("rows", [])] or \
                [{"quantity": q, "unavailable": vc["unavailable"]}]
            allp += [{"quantity": q, **x} for x in permutation(rr, sub.coef.to_numpy())]
    pd.DataFrame(allc).to_csv(os.path.join(od, "cells.csv"), index=False)
    pd.DataFrame(allk).to_csv(os.path.join(od, "contrasts.csv"), index=False)
    pd.DataFrame(allv).to_csv(os.path.join(od, "variance.csv"), index=False)
    pd.DataFrame(allp).to_csv(os.path.join(od, "permutation.csv"), index=False)
    med = {q: float(PR[PR.quantity == q].se_episode.median()) for q in QUANTITIES
           if (PR.quantity == q).any()}
    sv = {q: next((x["seed_sd_pooled"] for x in allc if x["quantity"] == q), None) for q in med}
    json.dump({"target": a.target, "control_world": a.control_world, "reference_agent": a.reference_agent,
               "design": {"cells": [list(c) for c in D["cells"]], "n_runs": D["N"], "df": D["df"]},
               "covariates": covs, "subset": f"exactly one {c2tag}" if c2tag else "all episodes",
               "excluded_per_run": {l: pf["excluded"] for l, pf in pfs.items()},
               "demoted_per_run": {l: pf["demoted"] for l, pf in pfs.items()},
               "median_episode_se_vs_seed_sd": {q: {"median_se_episode": med[q], "seed_sd": sv[q],
                                                    "se_below_half_sd": (sv[q] is not None and med[q] < 0.5 * sv[q])}
                                                for q in med}},
              open(os.path.join(od, "prefit.json"), "w"), indent=1)
    print(f"screen {a.target}: {len(runs)} runs, {len(D['cells'])} cells, df {D['df']} -> {od}")


if __name__ == "__main__":
    main()
