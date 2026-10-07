"""Statistics of the modulator engagement check, exactly as the plan fixes them (Revision 1a).

Plain-language purpose: the check asks whether the modulated agents whose modulator responds most
to felt injury (E1) are the ones whose injury-driven hiding beats their ordinary partner's most.
With 9 pairs spread over 3 training levels, a level that happens to have both high E1 and large
gaps would fake a relation, so every decision statistic is computed WITHIN level: each pair's E1
and outcome are demeaned within its level, Spearman's rank correlation is taken on the demeaned
values, and its p-value comes from shuffling E1 among the three pairs of each level -- all
3! x 3! x 3! = 216 arrangements, p = share of arrangements whose correlation is at least the
observed one (one-sided, observed arrangement included, so the smallest p is 1/216).

Decision rule (plan, Predictions + Revision 1a), all on demeaned values, each with its own null:
  P-main   rho(E1 gain, rabbit-scene injury gap)    supports: rho >= 0.6 and p <= 0.05;
           counts against: rho <= 0; unclear otherwise
  P-own    rho(E1 gain, the MODULATED agent's own rabbit-scene injury effect) >= 0.6, required
  control  rho(E1 gain, the ORDINARY partner's rabbit-scene injury effect) >= 0.6 withdraws "supports"
Verdict "supports" needs all three; "unclear" is never reported as partial support.
Reported beside it, never able to rescue P-main: E1 against the no-animal injury gap, the predator
gap and the shared no-animal unhurt baseline gap; E1 offset, the felt-injury-trace E1, E1-natural,
E2 and E3 against the primary outcome; the pooled (not demeaned) rho; within-level rho; P-rank;
the level-05 (and 05+06) own-scene sensitivity rows; P-cause (E4) and P-out (out-of-sample pairs).

Engagement is averaged over each pair's own tested checkpoint set (the grid points where both
agents' primary outcome was measured); a pair missing engagement at any of those points is an
error, not a smaller average.

    python scripts/analysis/modulator_engagement/analyze.py --data results/analysis/modulator_engagement
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
THRESH_RHO, THRESH_P = 0.6, 0.05
P_RANK_TOP = ("l04_s44", "l05_s42")
P_RANK_BOTTOM = ("l04_s43", "l05_s43")


# ------------------------------------------------------------------ statistics (pure)
def spearman(x, y):
    """Spearman's rho with average ranks for ties; nan if either side is constant."""
    from scipy.stats import rankdata
    rx, ry = rankdata(x), rankdata(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def demean_within(v, levels):
    v = np.asarray(v, float)
    out = v.copy()
    for lv in set(levels):
        m = np.asarray([l == lv for l in levels])
        out[m] = v[m] - v[m].mean()
    return out


def within_level_arrangements(levels):
    """Every permutation of indices that only moves items within their own level (product of
    per-level permutations); the identity is included."""
    levels = list(levels)
    groups = {}
    for i, l in enumerate(levels):
        groups.setdefault(l, []).append(i)
    keys = sorted(groups)
    out = []
    for combo in itertools.product(*[itertools.permutations(groups[k]) for k in keys]):
        perm = list(range(len(levels)))
        for k, pi in zip(keys, combo):
            for src, dst in zip(groups[k], pi):
                perm[src] = dst
        out.append(perm)
    return np.asarray(out)


def within_level_test(x, y, levels):
    """Spearman rho of level-demeaned x and y, with the exact within-level permutation null on x.
    Returns {rho, p, n_arrangements, null}. p = share of arrangements with rho >= observed."""
    xd, yd = demean_within(x, levels), demean_within(y, levels)
    rho = spearman(xd, yd)
    arr = within_level_arrangements(levels)
    null = np.asarray([spearman(xd[p], yd) for p in arr])
    p = float(np.mean(null >= rho - 1e-12))
    return {"rho": rho, "p": p, "n_arrangements": int(len(arr)), "null": null}


def p_main_call(rho, p):
    if rho >= THRESH_RHO and p <= THRESH_P:
        return "supports"
    if rho <= 0:
        return "counts against"
    return "unclear"


def verdict(main, own, control):
    call = p_main_call(main["rho"], main["p"])
    if call != "supports":
        return call, []
    why = []
    if not own["rho"] >= THRESH_RHO:
        why.append(f"P-own rho {own['rho']:.2f} < {THRESH_RHO}")
    if control["rho"] >= THRESH_RHO:
        why.append(f"negative control rho {control['rho']:.2f} >= {THRESH_RHO}")
    return ("unclear" if why else "supports"), why


# ------------------------------------------------------------------ data
def _read_csv_dir(d):
    import pandas as pd
    if not os.path.isdir(d):
        return None
    fs = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".csv")
          and not f.startswith("e4_")]
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else None


def per_pair_engagement(df, outcomes, cols, what):
    """{pair: {col: mean over the pair's own grid points}} -- fatal if any point is missing."""
    res = {}
    if df is None:
        return res
    for key, rec in outcomes.items():
        if "__own" in key:
            continue
        sub = df[df["pair"] == key]
        if sub.empty:
            continue
        want = set(rec["grid_points"])
        have = set(int(g) for g in sub["grid_index"])
        miss = sorted(want - have)
        if miss:
            raise ValueError(f"{what}: pair {key} lacks grid points {miss} of its tested set")
        s = sub[sub["grid_index"].isin(want)]
        res[key] = {c: float(s[c].mean()) for c in cols if c in s}
        res[key]["n_checkpoints"] = int(len(s))
    return res


def build_table(data_dir):
    import pandas as pd
    O = json.load(open(os.path.join(data_dir, "outcomes.json")))
    outc, prov = O["pairs"], O["provenance"]
    e1 = _read_csv_dir(os.path.join(data_dir, "e1"))
    e2 = _read_csv_dir(os.path.join(data_dir, "e2"))
    e3 = _read_csv_dir(os.path.join(data_dir, "e3"))
    E = {"e1": per_pair_engagement(e1, outc, ["e1g_mean4", "e1b_mean4", "e1g_trace_mean4", "e1b_trace_mean4",
                                              "e1nat_g_mean4", "e1nat_b_mean4", "gainsd_mean4",
                                              *[f"e1g_{s}" for s in ("encoder_unimodal", "encoder_multimodal", "rnn", "actor")]], "E1"),
         "e2": per_pair_engagement(e2, outc, ["e2g_rho_mean4", "e2b_rho_mean4"], "E2"),
         "e3": per_pair_engagement(e3, outc, ["e3_freeze_gain_mean_diff", "e3_freeze_offset_mean_diff"], "E3")}
    from scripts.analysis.modulator_engagement import runs as R
    rows = []
    for p in R.PAIRS:
        o = outc[p.key]
        r = {"pair": p.key, "group": p.group, "level": p.level, "seed": p.seed, "outcome_source": o["source"]}
        for k in ("gap_injw", "gap_inj", "gap_pred", "gap_base", "mod_injw", "ord_injw", "mod_inj", "ord_inj"):
            r[k] = o[k]
        r["outcome_checkpoints"] = len(o["grid_points"])
        own = outc.get(p.key + "__own")
        r["gap_injw_own"] = own["gap_injw"] if own else None
        for m in E.values():
            r.update(m.get(p.key, {}))
        rows.append(r)
    return pd.DataFrame(rows), prov


def analyse(T):
    """All statistics from the pair table. Returns (stats dict, null table)."""
    M = T[T.group == "main"].reset_index(drop=True)
    lv = list(M.level)
    st, nulls = {}, {}

    def test(name, xcol, ycol, frame=M):
        if xcol not in frame or frame[xcol].isna().any() or frame[ycol].isna().any():
            st[name] = None
            return None
        r = within_level_test(frame[xcol].to_numpy(float), frame[ycol].to_numpy(float), list(frame.level))
        nulls[name] = r.pop("null")
        st[name] = {**r, "x": xcol, "y": ycol,
                    "pooled_rho_not_demeaned": spearman(frame[xcol], frame[ycol])}
        return st[name]

    main = test("P-main", "e1g_mean4", "gap_injw")
    own = test("P-own", "e1g_mean4", "mod_injw")
    ctl = test("negative_control", "e1g_mean4", "ord_injw")
    if main and own and ctl:
        call, why = verdict(main, own, ctl)
        st["verdict"] = {"call": call, "p_main_call": p_main_call(main["rho"], main["p"]),
                         "supports_withdrawn_because": why}
    for name, x, y in (("E1g_vs_gap_inj", "e1g_mean4", "gap_inj"), ("E1g_vs_gap_pred", "e1g_mean4", "gap_pred"),
                       ("E1g_vs_gap_base", "e1g_mean4", "gap_base"), ("E1b_vs_gap_injw", "e1b_mean4", "gap_injw"),
                       ("E1g_trace_vs_gap_injw", "e1g_trace_mean4", "gap_injw"),
                       ("E1nat_g_vs_gap_injw", "e1nat_g_mean4", "gap_injw"),
                       ("E2g_rho_vs_gap_injw", "e2g_rho_mean4", "gap_injw"),
                       ("E3_freeze_gain_vs_gap_injw", "e3_freeze_gain_mean_diff", "gap_injw")):
        test(name, x, y)
    # level-05 own-scene sensitivity (pre-specified), and 05+06
    for name, lvls in (("sensitivity_own_l05", ("l05",)), ("sensitivity_own_l05_l06", ("l05", "l06"))):
        F = M.copy()
        sel = F.level.isin(lvls)
        F.loc[sel, "gap_injw"] = F.loc[sel, "gap_injw_own"]
        test(name, "e1g_mean4", "gap_injw", F)
    # within-level rho (3 pairs each, descriptive)
    if "e1g_mean4" in M and not M["e1g_mean4"].isna().any():
        st["within_level_rho"] = {l: spearman(g["e1g_mean4"], g["gap_injw"]) for l, g in M.groupby("level")}
        order = M.sort_values("e1g_mean4", ascending=False).pair.tolist()
        st["P-rank"] = {"order_high_to_low": order,
                        "top3_has_predicted": [k in order[:3] for k in P_RANK_TOP],
                        "bottom3_has_predicted": [k in order[-3:] for k in P_RANK_BOTTOM]}
    # out-of-sample (descriptive): raw rho, l05fix alone and all five; and sign vs the main rho
    for name, groups in (("P-out_l05fix", ("oos_fix",)), ("P-out_all5", ("oos_fix", "oos_orig"))):
        F = T[T.group.isin(groups)]
        if "e1g_mean4" in F and not F["e1g_mean4"].isna().any() and len(F) >= 3:
            rho = spearman(F["e1g_mean4"], F["gap_injw"])
            st[name] = {"rho_raw": rho, "n": int(len(F)),
                        "same_sign_as_main": (None if not main else bool(np.sign(rho) == np.sign(main["rho"])))}
    return st, nulls


def p_cause(data_dir, T):
    """E4, descriptive: share of the modulated agent's rabbit-scene injury effect removed by
    freezing, per pair (mean over its E4 checkpoints), against E1."""
    import pandas as pd
    f = os.path.join(data_dir, "e4", "e4_effects.csv")
    if not os.path.exists(f):
        return None
    cols = ["injw_live", "injw_freeze_gain", "injw_freeze_offset"]
    R = pd.read_csv(f)
    # a checkpoint counts only if live AND both frozen effects exist (e.g. level 04 seed 44 at 10.0 M
    # has frozen scores but was never tested live), so all three means use the same checkpoints
    R = R.dropna(subset=cols)
    D = R.groupby("pair")[cols].mean()
    D["e4_checkpoints"] = R.groupby("pair").size()
    D["removed_share_gain"] = 1 - D["injw_freeze_gain"] / D["injw_live"]
    D["removed_share_offset"] = 1 - D["injw_freeze_offset"] / D["injw_live"]
    D = D.join(T.set_index("pair")[["e1g_mean4", "group", "level"]])
    M = D[D.group == "main"]
    med = M["e1g_mean4"].median()
    return {"per_pair": D.reset_index().to_dict("records"),
            "rho_e1_vs_removed_share_gain": spearman(M["e1g_mean4"], M["removed_share_gain"]),
            "high_e1_mean_removed_gain": float(M[M.e1g_mean4 > med]["removed_share_gain"].mean()),
            "low_e1_mean_removed_gain": float(M[M.e1g_mean4 <= med]["removed_share_gain"].mean())}


def main(argv=None):
    sys.path.insert(0, ROOT)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="results/analysis/modulator_engagement")
    a = ap.parse_args(argv)
    T, prov = build_table(a.data)
    st, nulls = analyse(T)
    st["P-cause"] = p_cause(a.data, T)
    T.to_csv(os.path.join(a.data, "pair_table.csv"), index=False)
    import pandas as pd
    pd.DataFrame(nulls).to_csv(os.path.join(a.data, "permutation_null.csv"), index_label="arrangement")
    sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump({"stats": st, "outcome_provenance": prov, "git_sha": sha,
               "plan": "docs/experiments/active/modulator_clues/MODULATOR_ENGAGEMENT_CHECK.md (Revision 1a)",
               "thresholds": {"rho": THRESH_RHO, "p": THRESH_P},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(a.data, "stats.json"), "w"), indent=1, default=float)
    v = st.get("verdict")
    print(f"wrote pair_table.csv, permutation_null.csv, stats.json to {a.data}; verdict: {v}")


if __name__ == "__main__":
    main()
