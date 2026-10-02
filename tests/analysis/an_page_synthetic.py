"""Synthetic driver outputs for the an0N figure tests of "What Both Agents Compute".

Two inputs do not exist on disk yet: `similarity_robustness.json` (written by
`run_similarity_robustness.py`, not yet run on the interim manifest) and a complete wake-up summary (the B2 sweep is still running; no May seed is summarised). These
builders write files with the SAME schema the figure scripts read, stamped with the current rules
file and a manifest path outside docs/, so every figure drawn from them is labelled TEST INPUT and
refused the page's folder. Numbers are fixture values, not results.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RULES = "docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml"
LAYERS = ("enc.out", "rnn.state", "rnn.out", "actor.out", "critic.out")


def stamp(status: str = "interim") -> dict:
    sha = hashlib.sha256(open(os.path.join(ROOT, RULES), "rb").read()).hexdigest()
    s = {"decision_rules": {"file": RULES, "sha256": sha, "commit": None},
         "evidence_status": status, "manifest": "tests/synthetic_manifest.yaml",
         "generated_utc": "2026-09-30T00:00:00Z"}
    if status == "interim":
        s.update(label=None, verdict_prefix="provisional — end of stage 1 of 5",
                 verdict_words_allowed=True,
                 verdict_statement="verdict words come only from decision_rules.evaluate_*")
    return s


def robustness_doc() -> dict:
    """In run_similarity_robustness.py's schema (layers.<layer>.pairs.<A|B>.variants.<v>)."""
    rng = np.random.default_rng(0)
    pairs = {"ordinary_s42|ordinary_s43": "OO", "ordinary_s42|ordinary_s44": "OO",
             "ordinary_s43|ordinary_s44": "OO", "modulated_s42|modulated_s43": "MM",
             "modulated_s42|modulated_s44": "MM", "modulated_s43|modulated_s44": "MM",
             "ordinary_s42|modulated_s43": "MO_diff", "ordinary_s42|modulated_s44": "MO_diff",
             "ordinary_s43|modulated_s42": "MO_diff", "ordinary_s44|modulated_s42": "MO_diff",
             "ordinary_s43|modulated_s44": "MO_diff", "ordinary_s44|modulated_s43": "MO_diff",
             "ordinary_s42|modulated_s42": "MO_same"}
    base = {"OO": 0.89, "MM": 0.86, "MO_diff": 0.85, "MO_same": 0.85}
    variants = ("all_columns", "admitted", "floored_scale")
    layers = {}
    for layer in LAYERS:
        out = {}
        for p, ps in pairs.items():
            a, b = p.split("|")
            rec = {"pair_set": ps, "a": a, "b": b, "variants": {}}
            for v in variants:
                row = {}
                for stat, shift in (("weighted", 0.0), ("unit_mean", -0.1)):
                    ab, ba = (base[ps] + shift + rng.normal(0, 0.005, 2)).tolist()
                    for d, x in (("a_to_b", ab), ("b_to_a", ba), ("mutual", min(ab, ba))):
                        row[f"{stat}_{d}"] = {"point": x, "q_lo": x - 0.003, "q_hi": x + 0.003,
                                              "nonfinite_draws": 0}
                row["fits_a_to_b"] = [{"n_columns": 125, "n_dropped": 3 if v == "admitted" else 0}]
                row["fits_b_to_a"] = [{"n_columns": 128, "n_dropped": 0}]
                rec["variants"][v] = row
            out[p] = rec
        layers[layer] = {"summary": {}, "pairs": out}
    return {**stamp(), "driver": "run_similarity_robustness",
            "status_of_these_numbers": "descriptive \u2014 not a registered statistic",
            "cell": ["stage_end:0", "active_stage0end"], "gate_G5": None,
            "row_lag_control": {p: {"lag0": 1.0} for p in pairs},
            "variants": {v: v for v in variants},
            "statistics": {"weighted": "w", "unit_mean": "u", "mutual": "m"},
            "layers": layers}


def write_robustness(folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, "similarity_robustness.json")
    json.dump(robustness_doc(), open(p, "w"))
    return p


HEADLINE = ["grad_share.total", "grad_probe.first_update.policy", "update_size.modulator",
            "rho.rnn", "swing.rnn", "freeze.gain"]


def write_wakeup(folder: str, n_l05: int = 3, n_may: int = 2) -> str:
    """b2_reading.json + curves/<run>.json + plateau.json (run_wakeup --summarise's schema), and
    points/<run>/*.json holding the update_size block the an05 control reads."""
    os.makedirs(os.path.join(folder, "curves"), exist_ok=True)
    st = {**stamp("b2_wakeup"), "label": "synthetic wake-up fixture"}
    for k in ("verdict_prefix", "verdict_words_allowed", "verdict_statement"):
        st.pop(k, None)
    runs = [(f"l05_w{i:04d}_modulated", False, 50, 200000) for i in range(n_l05)] + \
           [(f"mayrep_modulated_s{42 + i}", True, 15, 100000) for i in range(n_may)]
    wp, plat = {}, []
    for label, cont, n, step in runs:
        cks = [step * (i + 1) for i in range(n)]
        curves = {}
        for name in HEADLINE:
            anch = not (name.startswith("grad_share") or name.startswith("update_size"))
            x = ([0] if anch else []) + cks
            m = list(1 - np.exp(-np.arange(len(x)) / 5.0))
            curves[name] = {"x": [float(v) for v in x], "m": m, "measure": name.split(".")[0],
                            "anchored": anch, "headline": True}
        pdir = os.path.join(folder, "points", label)       # the control reads main_prev_norm
        os.makedirs(pdir, exist_ok=True)
        json.dump({"x": 0, "measures": {}}, open(os.path.join(pdir, "0.json"), "w"))
        for i, c in enumerate(cks):
            json.dump({"x": c, "measures": {"update_size": {
                "interval": [0 if i == 0 else cks[i - 1], c], "main_prev_norm": 70.0 + 5.0 * i}}},
                open(os.path.join(pdir, f"{c}.json"), "w"))
        t_pl = float(cks[5])
        wake = {}
        for name in HEADLINE:
            t = float(cks[3]) if name != "freeze.gain" else float("nan")
            wake[name] = {"headline_mode": "fraction_of_rise",
                          "headline": {"t": t, "index": 4 if t == t else None,
                                       "reason": None if t == t else "no sustained crossing"},
                          "beside_mode": "fraction_of_final", "beside": {"t": t},
                          "lag": ({"lag": t - t_pl, "pos_wake": 4, "pos_plateau": 6,
                                   "delta_positions": -2} if t == t else
                                  {"lag": float("nan"), "pos_wake": None, "pos_plateau": None,
                                   "delta_positions": None}),
                          "caveat": "fixture caveat"}
        wp[label] = wake
        json.dump({**st, "label": label, "t_plateau_episode": t_pl, "continual": cont,
                   "curves": curves, "per_run_caveat": "fixture caveat", "wake_points": wake},
                  open(os.path.join(folder, "curves", f"{label}.json"), "w"))
        plat.append({"label": label, "n_points": n, "t_plateau_episode": t_pl,
                     "curve": list(100 + 100 * (1 - np.exp(-np.arange(n) / 4.0)))})
    json.dump({**st, "measure": "plateau", "runs": plat}, open(os.path.join(folder, "plateau.json"), "w"))
    reading = {n: {"reading": "early", "n_def": n_l05, "k_star": n_l05, "n_late": 0,
                   "n_early": n_l05, "may": "agree"} for n in HEADLINE}
    doc = {**st, "measure": "b2_reading", "headline_curves": HEADLINE,
           "per_run_caveat": "fixture caveat: descriptive only",
           "b2_family_bound": {"family_size": len(HEADLINE) * len(runs)},
           "reading": reading, "per_run_wake_points": wp}
    p = os.path.join(folder, "b2_reading.json")
    json.dump(doc, open(p, "w"))
    return p
