#!/usr/bin/env python3
"""verdict.py - the single-channel-smell study's pre-registered decision rule (study section 5.3).

Plan: docs/develop/active/behavior/HYPERVIGILANCE_ANALYSIS_TOOLING.md (Revision 2), section 7.

Two modes:
  --yardstick --manifest <cmp10m population.json>
        between-seed SD of P1, P2, P2d, S1 and the S2 scent slope over the five cmp10m seeds, plus
        the power table re-stated with those SDs -> results/analysis/hypervigilance/cmp10m/
        yardstick.json. FROZEN: refuses to overwrite, and refuses if any hv-study reading exists
        already (study 5.3: "Before any hv run is read ... frozen").
  --manifest <hvsmell population.json> --context-manifest <basicq2 population.json>
        the verdict -> results/analysis/hypervigilance/hvsmell/verdict.{json,md}. Refuses unless
        the yardstick is frozen, the golden stamps match, the study text still says what RULES
        says (DOC_ANCHORS), and every world x agent has readings for seeds 42, 43, 44.

Every constant in RULES is anchored to the study's own sentence, copied verbatim from the study
file, searched only inside its "### 5.2 Secondary outcomes" .. "### 5.4 Temporal evolution" slice
(the doc's feedback sections quote superseded rules and must not satisfy an anchor).
"""
from __future__ import annotations
import argparse
import datetime as _dt
import glob
import json
import os
import re
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings as RD                                 # noqa: E402
import aimed_response as AIM                          # noqa: E402  (scripts/analysis on sys.path via RD)

ROOT = RD.ROOT
STUDY_DOC = os.path.join(ROOT, "docs", "experiments", "active", "hypervigilance",
                         "SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md")
SLICE_FROM, SLICE_TO = "### 5.2 Secondary outcomes", "### 5.4 Temporal evolution"
SEEDS_STAGE1, SEEDS_STAGE2 = (42, 43, 44), (42, 43, 44, 45, 46)
U_CRIT_ONE_SIDED_5V5 = 4
U_CRIT_TWO_SIDED_5V5 = 2
C_SIGN_PP = 3.0
S4_FLOOR_PP = -3.0

#: outcome -> (predicted sign, minimum effect or None)
RULES = {"P1": (+1, 3.0), "P2": (+1, 2.0), "P2d": (-1, 1.0), "S1": (+1, 2.0), "survival": (-1, None)}
CONTRASTS = {"A": ("hv1ch", "hv2ch"), "B": ("hv1chm", "hv2ch"), "C": ("hv1ch", "hv1chm")}
AGENTS = ("t1none", "t16quad")
WORLDS = ("hv1ch", "hv1chm", "hv2ch")

VERDICT_ROWS = {
    1: "Hypothesis supported",
    2: "Confusion without (more) hypervigilance",
    3: "Confusion established; its injury dependence undetermined.",
    4: "No extra confusion",
    5: "Not separable from detection loss",
    6: "Undetermined.",
}
C_SIGN_READINGS = {
    "i": "B established, |C| < 3 pp",
    "ii": "B established, A not, C ≤ −3 pp",
    "iii": "A established, B not established, C ≥ +3 pp",
    "iv": "A established, B established, C of either sign",
}

#: (what it pins, verbatim study text). Copied from the study file, not from the plan.
DOC_ANCHORS = [
    ("P1 minimum 3 pp, +", "| P1 rabbit proximity effect | + | **3 pp** |"),
    ("P2 minimum 2 pp, +", "| P2 causal injury shift, hiding | + | **2 pp** |"),
    ("P2d minimum 1 pp, -, decides nothing alone",
     "| P2d causal injury shift, distance | − | 1 pp (read with P2: H₁b needs P2 established and "
     "P2d's Δ of the predicted sign; P2d alone decides nothing) |"),
    ("S1 minimum 2 pp per nat, +", "| + | 2 pp per nat of scent evidence |"),
    ("survival: interval, no threshold", "| Survival | − | reported with its 95 % interval; no threshold |"),
    ("two-stage rule scope", "The two-stage rule below applies to contrasts A and B only."),
    ("C descriptive", "so C is **two-sided and descriptive**"),
    ("C U <= 2 at 5 v 5",
     "a two-sided Mann–Whitney U ≤ 2 (p ≈ 0.03) at 5 v 5 is reported as \"C clearly non-zero\". "
     "C triggers no top-up of its own."),
    ("stage 1", "*Established* if all three treated seeds lie beyond all three reference seeds in the "
                "predicted direction (one-sided exact permutation p = 0.05) **and** `|Δ|` is at least "
                "the minimum effect."),
    ("stage 2 established", "*Established* if one-sided Mann–Whitney U ≤ 4 (p < 0.05) in the "
                            "predicted direction **and** `|Δ|` ≥ the minimum effect."),
    ("stage 2 refuted, predicted side",
     "**on the predicted side** — the upper bound for a + prediction, the lower bound for a − "
     "prediction (P2d, survival) — **falls short of the minimum effect** (below +min for +, above "
     "−min for −)"),
    ("stage 2 refuted, opposite U", "or if U ≤ 4 holds in the **opposite** direction. *Not "
                                    "established* otherwise. No further top-up."),
    ("C-sign i", "**B established, |C| < 3 pp**"),
    ("C-sign ii", "**B established, A not, C ≤ −3 pp**"),
    ("C-sign iii", "**A established, B not established, C ≥ +3 pp**"),
    ("C-sign iv", "**A established, B established, C of either sign**"),
    ("S4 did not fall", "the one-sided 95 % lower confidence bound (Welch) of the predator proximity "
                        "effect's Δ lies above −3 pp"),
    ("S4 deciding stage", "evaluated at the stage at which the primary outcome was decided (3 v 3 or "
                          "5 v 5). Otherwise \"S4 may have fallen\"."),
    ("verdict row 1", "| established | established | **Hypothesis supported**"),
    ("verdict row 2", "| established | **refuted** (at stage 2) | **Confusion without (more) "
                      "hypervigilance**"),
    ("verdict row 3", "| established | not established | **Confusion established; its injury "
                      "dependence undetermined.**"),
    ("verdict row 4", "| refuted, **and S4 did not fall** | any | **No extra confusion**"),
    ("verdict row 5", "| refuted or not established, **S4 may have fallen** | any | **Not separable "
                      "from detection loss**"),
    ("verdict row 6", "| not established, S4 did not fall | any | **Undetermined.**"),
    ("absolute sign of P2", "the treated world's mean P2 with its one-sided 95 % lower bound. If P2's "
                            "Δ is established but that bound is not above 0"),
    ("S1 estimator", "a weighted least-squares slope of the episode's early bush share (in pp) on the "
                     "rabbit's scent evidence (nats, §2.2), weights = the episode's early step count; "
                     "the contrast is top slope minus bottom slope, in pp per nat"),
    ("S1 window = readings.EARLY", "bush share over the first 25 chosen steps"),
    ("S1 reference arm", "the tested Δ uses the **matched-control reading**"),
    ("S2 sextiles", "within-world population sextiles"),
    ("S3 groups = aimed_response thresholds", "(log-likelihood ratio < 0 vs ≥ +0.67)"),
    ("S3 deciding row primary", "primary = the **deciding row**"),
]


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def doc_slice(path: str) -> str:
    lines = open(path).read().splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if l.startswith(SLICE_FROM))
        b = next(i for i, l in enumerate(lines) if l.startswith(SLICE_TO) and i > a)
    except StopIteration:
        raise SystemExit(f"{path}: cannot find the '{SLICE_FROM}' .. '{SLICE_TO}' slice")
    return _collapse("\n".join(lines[a:b]))


def check_anchors(path: str = STUDY_DOC) -> None:
    s = doc_slice(path)
    missing = [what for what, text in DOC_ANCHORS if _collapse(text) not in s]
    if RD.EARLY != 25:
        missing.append("readings.EARLY != 25 (the study's 'first 25 chosen steps')")
    if round(AIM.PREDATOR_LIKE_AT_NATS, 2) != 0.67 or AIM.RABBIT_LIKE_BELOW_NATS != 0.0:
        missing.append("aimed_response thresholds != the study's '< 0 vs >= +0.67'")
    if missing:
        raise SystemExit("the study text no longer says what verdict.py applies; missing anchors:\n  "
                         + "\n  ".join(missing))


# ------------------------------------------------------------------------------- statistics ----
def welch(t, r):
    """(delta, se, df) of mean(t) - mean(r) with Welch-Satterthwaite df."""
    t, r = np.asarray(t, float), np.asarray(r, float)
    vt, vr = t.var(ddof=1) / len(t), r.var(ddof=1) / len(r)
    se2 = vt + vr
    den = (vt ** 2 / (len(t) - 1) if vt > 0 else 0.0) + (vr ** 2 / (len(r) - 1) if vr > 0 else 0.0)
    df = se2 ** 2 / den if den > 0 else np.inf
    return float(t.mean() - r.mean()), float(np.sqrt(se2)), float(df)


def one_sided_bound(t, r, side: str, level=0.95) -> float:
    d, se, df = welch(t, r)
    if se == 0:
        return d
    q = stats.t.ppf(level, df)
    return d - q * se if side == "lower" else d + q * se


def two_sided_interval(t, r, level=0.95):
    d, se, df = welch(t, r)
    if se == 0:
        return (d, d)
    q = stats.t.ppf(0.5 + level / 2, df)
    return (d - q * se, d + q * se)


def u_not_beyond(t, r, sign: int) -> float:
    """Mann-Whitney U counting pairs where the treated seed is NOT beyond the reference seed in the
    predicted direction (ties 1/2). U <= 4 at 5 v 5 = one-sided p < 0.05 in the predicted direction."""
    t, r = np.asarray(t, float)[:, None], np.asarray(r, float)[None, :]
    if sign > 0:
        return float(np.sum(t < r) + 0.5 * np.sum(t == r))
    return float(np.sum(t > r) + 0.5 * np.sum(t == r))


def stage1(t, r, sign, minimum) -> dict:
    d = float(np.mean(t) - np.mean(r))
    sep = (min(t) > max(r)) if sign > 0 else (max(t) < min(r))
    ok = sep and sign * d >= minimum
    return {"stage": 1, "delta": d, "separated": bool(sep),
            "status": "established" if ok else "top-up"}


def stage2(t, r, sign, minimum) -> dict:
    d = float(np.mean(t) - np.mean(r))
    u_pred, u_opp = u_not_beyond(t, r, sign), u_not_beyond(t, r, -sign)
    bound = one_sided_bound(t, r, "upper" if sign > 0 else "lower")
    if u_pred <= U_CRIT_ONE_SIDED_5V5 and sign * d >= minimum:
        st = "established"
    elif sign * bound < minimum or u_opp <= U_CRIT_ONE_SIDED_5V5:
        st = "refuted"
    else:
        st = "not established"
    return {"stage": 2, "delta": d, "U_predicted": u_pred, "U_opposite": u_opp,
            "bound_predicted_side": bound, "status": st}


def decide(tv: dict, rv: dict, sign: int, minimum: float) -> dict:
    """Two-stage rule on {seed: value} dicts of the treated and reference world."""
    if any(v is None or not np.isfinite(v) for v in list(tv.values()) + list(rv.values())):
        return {"status": "not evaluable under §5.3", "reason": "a seed value is NaN"}
    ts, rs = sorted(tv), sorted(rv)
    if tuple(ts) == SEEDS_STAGE1 and tuple(rs) == SEEDS_STAGE1:
        return stage1([tv[s] for s in ts], [rv[s] for s in rs], sign, minimum)
    if tuple(ts) == SEEDS_STAGE2 and tuple(rs) == SEEDS_STAGE2:
        s1 = stage1([tv[s] for s in SEEDS_STAGE1], [rv[s] for s in SEEDS_STAGE1], sign, minimum)
        if s1["status"] == "established":
            return s1
        return {**stage2([tv[s] for s in ts], [rv[s] for s in rs], sign, minimum), "stage1": s1}
    return {"status": "not evaluable under §5.3", "reason": f"seed sets {ts} v {rs}"}


def describe_c(tv: dict, rv: dict) -> dict:
    ts, rs = sorted(tv), sorted(rv)
    if any(v is None or not np.isfinite(v) for v in list(tv.values()) + list(rv.values())):
        return {"status": "not evaluable under §5.3", "reason": "a seed value is NaN"}
    t, r = [tv[s] for s in ts], [rv[s] for s in rs]
    d = float(np.mean(t) - np.mean(r))
    out = {"delta": d, "interval95": list(two_sided_interval(t, r)), "status": "descriptive"}
    if tuple(ts) == SEEDS_STAGE2 and tuple(rs) == SEEDS_STAGE2:
        u = min(u_not_beyond(t, r, +1), u_not_beyond(t, r, -1))
        out["U_two_sided"] = u
        out["clearly_non_zero"] = bool(u <= U_CRIT_TWO_SIDED_5V5)
    return out


def s4_condition(p1_decision: dict, s4t: dict, s4r: dict) -> dict:
    """Study S4: one-sided 95 % Welch lower bound of the predator effect's delta > -3 pp, on the
    seed set of the stage at which P1 was decided."""
    st = p1_decision.get("stage")
    if p1_decision.get("status") == "top-up" or st is None:
        return {"status": "pending", "reason": "P1 not yet decided"}
    seeds = SEEDS_STAGE1 if st == 1 else SEEDS_STAGE2
    if not all(s in s4t and s in s4r for s in seeds):
        return {"status": "pending", "reason": f"S4 values missing for seeds {seeds}"}
    lb = one_sided_bound([s4t[s] for s in seeds], [s4r[s] for s in seeds], "lower")
    return {"stage": st, "lower_bound": lb,
            "status": "S4 did not fall" if lb > S4_FLOOR_PP else "S4 may have fallen"}


def verdict_row(p1: str, p2: str, s4: str) -> dict:
    """Study 5.3 verdict map, from the final P1 / P2 statuses and the S4 condition."""
    pending = {"row": None, "reading": "pending the top-up"}
    if p1 == "top-up":
        return pending
    if p1 == "established":
        rows = {"established": 1, "refuted": 2, "not established": 3}
        if p2 == "top-up":
            return pending
        if p2 in rows:
            return {"row": rows[p2], "reading": VERDICT_ROWS[rows[p2]]}
        return {"row": None, "reading": f"P2 {p2}"}
    if s4 == "pending":
        return pending
    if s4 == "S4 may have fallen" and p1 in ("refuted", "not established"):
        return {"row": 5, "reading": VERDICT_ROWS[5]}
    if p1 == "refuted" and s4 == "S4 did not fall":
        return {"row": 4, "reading": VERDICT_ROWS[4]}
    if p1 == "not established" and s4 == "S4 did not fall":
        return {"row": 6, "reading": VERDICT_ROWS[6]}
    return {"row": None, "reading": f"no verdict-map row for P1 {p1}, P2 {p2}, {s4}"}


def c_sign(a_status: str, b_status: str, c_delta) -> dict:
    if "top-up" in (a_status, b_status) or c_delta is None:
        return {"readings": [], "note": "pending"}
    hits = []
    if b_status == "established" and abs(c_delta) < C_SIGN_PP:
        hits.append("i")
    if b_status == "established" and a_status != "established" and c_delta <= -C_SIGN_PP:
        hits.append("ii")
    if a_status == "established" and b_status != "established" and c_delta >= C_SIGN_PP:
        hits.append("iii")
    if a_status == "established" and b_status == "established":
        hits.append("iv")
    return {"readings": [f"{h}: {C_SIGN_READINGS[h]}" for h in hits],
            "note": None if hits else "no registered cross-contrast reading"}


def absolute_p2(values: list, delta_established: bool) -> dict:
    v = np.asarray(values, float)
    lb = float(v.mean() - stats.t.ppf(0.95, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v)))
    return {"mean": float(v.mean()), "lower_bound": lb, "above_zero": bool(lb > 0),
            "weakens_boldness": bool(delta_established and not lb > 0)}


def power(effect: float, sd: float, n_draws: int = 40000, rng_seed: int = 0,
          minimum: float = 3.0, sign: int = +1) -> dict:
    """Monte-Carlo of the two-stage rule with normal seeds (the study's power table)."""
    rng = np.random.default_rng(rng_seed)
    T = rng.normal(effect, sd, (n_draws, 5))
    R = rng.normal(0.0, sd, (n_draws, 5))
    t3, r3 = T[:, :3], R[:, :3]
    d3 = t3.mean(1) - r3.mean(1)
    sep = (t3.min(1) > r3.max(1)) if sign > 0 else (t3.max(1) < r3.min(1))
    est1 = sep & (sign * d3 >= minimum)
    d5 = T.mean(1) - R.mean(1)
    tt, rr = T[:, :, None], R[:, None, :]
    u_pred = ((tt < rr).sum((1, 2)) + 0.5 * (tt == rr).sum((1, 2))) if sign > 0 else \
             ((tt > rr).sum((1, 2)) + 0.5 * (tt == rr).sum((1, 2)))
    u_opp = 25 - u_pred
    vt, vr = T.var(1, ddof=1) / 5, R.var(1, ddof=1) / 5
    se = np.sqrt(vt + vr)
    df = (vt + vr) ** 2 / (vt ** 2 / 4 + vr ** 2 / 4)
    q = stats.t.ppf(0.95, df)
    bound = d5 + q * se if sign > 0 else d5 - q * se
    est2 = (u_pred <= U_CRIT_ONE_SIDED_5V5) & (sign * d5 >= minimum)
    ref2 = ~est2 & ((sign * bound < minimum) | (u_opp <= U_CRIT_ONE_SIDED_5V5))
    top = ~est1
    return {"effect": effect, "sd": sd, "draws": n_draws,
            "established_stage1": float(est1.mean()), "top_up": float(top.mean()),
            "established_overall": float((est1 | (top & est2)).mean()),
            "refuted": float((top & ref2).mean()),
            "not_established": float((top & ~est2 & ~ref2).mean())}


# ------------------------------------------------------------------------------- readings ----
def outcome_value(r: dict, name: str, s1_ref: str | None = None):
    if name in ("P1", "P2", "P2d"):
        return r[name]["value"]
    if name == "survival":
        return r["survival"]["mean_steps"]["value"]
    if name == "S4":
        return r["S4"]["predator_proximity_effect"]["value"]
    if name == "S1":
        which = s1_ref or r["S1"]["tested"]
        return r["S1"][which]["primary"]["contrast"]["value"]
    if name == "S2":
        return r["S2"]["univariate"]["rab_smell_predatorness"]["dpp_per_nat"]["value"]
    if name.startswith("S6:"):
        return r["S6"][name[3:]]["value"]
    raise KeyError(name)


def load_readings(manifest: str, out_root: str) -> list[dict]:
    M = RD.load_population(manifest)
    out = []
    for c in M["cells"]:
        p = os.path.join(out_root, c["label"], "readings.json")
        if os.path.exists(p):
            out.append(json.load(open(p)))
    return out


def seed_sd(readings, names) -> dict:
    res = {}
    for n in names:
        v = np.array([outcome_value(r, *n) if isinstance(n, tuple) else outcome_value(r, n)
                      for r in readings], float)
        key = n if isinstance(n, str) else f"{n[0]}:{n[1]}"
        res[key] = {"values": v.tolist(), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None,
                    "mean": float(np.mean(v))}
    return res


def yardstick(manifest: str, out_root: str) -> dict:
    out_p = RD.YARDSTICK
    if os.path.exists(out_p):
        raise SystemExit(f"{out_p} exists and is frozen; it is never overwritten")
    hv_readings = glob.glob(os.path.join(RD.HV_ROOT, "hvsmell", "*", "readings.json"))
    if hv_readings:
        raise SystemExit(f"hv-study readings already exist ({len(hv_readings)}); the yardstick must be "
                         f"frozen BEFORE any hv run is read")
    R = load_readings(manifest, out_root)
    if len(R) != 5:
        raise SystemExit(f"expected readings for the five cmp10m seeds, found {len(R)}")
    sds = seed_sd(R, ["P1", "P2", "P2d", ("S1", "matched_control"), ("S1", "plain"), "S2"])
    p1, p2 = sds["P1"]["sd"], sds["P2"]["sd"]
    table = [power(3, p1, minimum=3), power(4, p1, minimum=3), power(0, p1, minimum=3),
             power(2, p2, minimum=2), power(4, p2, minimum=2), power(0, p2, minimum=2)]
    doc = {"frozen_at": _dt.datetime.now().isoformat(timespec="seconds"),
           "manifest": os.path.relpath(manifest, ROOT), "manifest_sha256": RD.sha256(manifest),
           "seeds": [r["seed"] for r in R], "labels": [r["label"] for r in R],
           "readings_sha256": {r["label"]: RD.sha256(os.path.join(out_root, r["label"], "readings.json"))
                               for r in R},
           "hv_store_state_at_freeze": {
               "results/trajectories_hvsmell exists": os.path.isdir(
                   os.path.join(ROOT, "results", "trajectories_hvsmell")),
               "hvsmell readings.json files": 0},
           "between_seed_sd": sds, "power_restated": table,
           "note": "used to re-state the power table only, never to change the thresholds (study 5.3)"}
    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    RD.dump(doc, out_p)
    os.chmod(out_p, 0o444)
    return doc


def run_verdict(manifest, out_root, context_manifest, context_root) -> dict:
    check_anchors()
    RD.require_stamps()
    if not os.path.exists(RD.YARDSTICK):
        raise SystemExit(f"{RD.YARDSTICK} missing: freeze the cmp10m yardstick first (--yardstick)")
    ys = json.load(open(RD.YARDSTICK))
    R = load_readings(manifest, out_root)
    cur = RD.source_hashes(RD.SWEEP_SOURCES + RD.ASSEMBLY_SOURCES)
    for r in R:
        if r["code"]["sources"] != cur:
            raise SystemExit(f"{r['label']}: readings.json was assembled by other code; re-assemble")
        if r["assembled"] < ys["frozen_at"]:
            raise SystemExit(f"{r['label']}: assembled {r['assembled']}, before the yardstick froze")
    RD.assert_sextiles(R)
    V = {(r["world"], r["agent"]): {} for r in R}
    for r in R:
        V[(r["world"], r["agent"])][int(r["seed"])] = r
    missing = [(w, a) for w in WORLDS for a in AGENTS
               if not all(s in V.get((w, a), {}) for s in SEEDS_STAGE1)]
    if missing:
        raise SystemExit(f"population incomplete -- no readings for seeds {SEEDS_STAGE1} in "
                         f"{missing}. The verdict runs only when every world x agent has them "
                         f"(training + collection + readings).")
    vals = lambda w, a, name, **kw: {s: outcome_value(r, name, **kw) for s, r in V[(w, a)].items()}
    out = {"written": _dt.datetime.now().isoformat(timespec="seconds"),
           "yardstick_frozen_at": ys["frozen_at"], "agents": {}, "top_up_required": []}
    for a in AGENTS:
        A = {"contrasts": {}}
        for cname, (tw, rw) in CONTRASTS.items():
            C = {}
            for name, (sign, mn) in RULES.items():
                if name == "S1" and rw == "hv2ch":
                    t = vals(tw, a, "S1")
                    tested = vals(rw, a, "S1", s1_ref="matched_control")
                    plain = vals(rw, a, "S1", s1_ref="plain")
                    if cname == "C":
                        C[name] = describe_c(t, tested)
                        continue
                    dm, dp = decide(t, tested, sign, mn), decide(t, plain, sign, mn)
                    clear = lambda d: d.get("delta") is not None and sign * d["delta"] >= mn
                    C[name] = {**dm, "reference": "matched control reading (decides)",
                               "plain_reference_descriptive": {**dp, "label":
                                   "identity-only reference, descriptive"},
                               "references_disagree": bool(clear(dm) != clear(dp))}
                    if cname == "B":
                        C[name]["note"] = ("residual strength-per-nat difference: 0.64 vs 0.45 units "
                                           "of strength per nat (study Revision 4)")
                    continue
                t, r = vals(tw, a, name), vals(rw, a, name)
                if cname == "C":
                    C[name] = describe_c(t, r)
                elif mn is None:
                    tt, rr = [t[s] for s in sorted(t)], [r[s] for s in sorted(r)]
                    C[name] = {"delta": float(np.mean(tt) - np.mean(rr)),
                               "interval95": list(two_sided_interval(tt, rr)),
                               "status": "reported, no decision"}
                else:
                    C[name] = decide(t, r, sign, mn)
                if cname != "C":
                    C[name]["per_seed"] = {"treated": t, "reference": r}
                    if C[name].get("status") == "top-up":
                        out["top_up_required"].append({"agent": a, "contrast": cname, "outcome": name,
                                                       "worlds": [tw, rw], "seeds": [45, 46]})
            if cname != "C":
                C["H1b"] = bool(C["P2"].get("status") == "established" and
                                C["P2d"].get("delta") is not None and C["P2d"]["delta"] < 0)
                C["S4_condition"] = s4_condition(C["P1"], vals(tw, a, "S4"), vals(rw, a, "S4"))
                C["verdict_map"] = verdict_row(C["P1"].get("status"), C["P2"].get("status"),
                                               C["S4_condition"]["status"])
                C["absolute_P2_treated"] = absolute_p2(
                    list(vals(tw, a, "P2").values()), C["P2"].get("status") == "established")
                C["S6"] = {v: decide(vals(tw, a, f"S6:{v}"), vals(rw, a, f"S6:{v}"),
                                     *RULES["P1" if v.startswith("P1") else "P2"])
                           for v in ("P1_without_distance0", "P2_without_distance0",
                                     "P1_predator_free", "P2_predator_free")}
            A["contrasts"][cname] = C
        A["C_sign_on_P1"] = c_sign(A["contrasts"]["A"]["P1"].get("status"),
                                   A["contrasts"]["B"]["P1"].get("status"),
                                   A["contrasts"]["C"]["P1"].get("delta"))
        A["seed_noise_post_hoc"] = {
            n: {"frozen_yardstick_sd": ys["between_seed_sd"][k]["sd"],
                "hv_control_sd_post_hoc_not_used_by_the_rule": float(np.std(
                    list(vals("hv2ch", a, n, **({"s1_ref": "matched_control"} if n == "S1" else {})
                              ).values()), ddof=1))}
            for n, k in (("P1", "P1"), ("P2", "P2"), ("P2d", "P2d"), ("S1", "S1:matched_control"))}
        out["agents"][a] = A
    out["level06_context"] = level06_context(context_manifest, context_root)
    return out


def level06_context(manifest, out_root) -> dict:
    """Study 5.5: within-wave level 06 minus level 05, P1 and P2 per agent. Descriptive only."""
    R = load_readings(manifest, out_root)
    by = {(r["wave"], r["level"], r["agent"]): r for r in R}
    res = {}
    for (wave, lvl, agent), r in by.items():
        if lvl == 6 and (wave, 5, agent) in by:
            r5 = by[(wave, 5, agent)]
            res[f"{wave}_{agent}"] = {k: (r[k]["value"] - r5[k]["value"])
                                      if r[k]["value"] is not None and r5[k]["value"] is not None
                                      else None for k in ("P1", "P2")}
    return {"descriptive_only": True, "never_pooled": True, "level06_minus_level05": res}


def to_markdown(v: dict) -> str:
    L = [f"# Verdict (written {v['written']}, yardstick frozen {v['yardstick_frozen_at']})", ""]
    for a, A in v["agents"].items():
        L.append(f"## Agent {a}")
        for cname, C in A["contrasts"].items():
            L.append(f"### Contrast {cname}")
            L.append("| outcome | status | Δ |")
            L.append("|---|---|---|")
            for k, d in C.items():
                if isinstance(d, dict) and "status" in d:
                    L.append(f"| {k} | {d['status']} | {d.get('delta')} |")
            if "verdict_map" in C:
                L.append(f"\nVerdict map: {C['verdict_map']['reading']} ({C['S4_condition']['status']})\n")
        L.append(f"C-sign on P1: {A['C_sign_on_P1']}\n")
    L.append(f"Top-up required: {v['top_up_required']}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-root", required=True, help="the readings root of --manifest (absolute)")
    ap.add_argument("--yardstick", action="store_true")
    ap.add_argument("--context-manifest", default=None)
    ap.add_argument("--context-root", default=None)
    a = ap.parse_args()
    out_root = RD.guard_out_root(a.out_root)
    if a.yardstick:
        check_anchors()
        RD.require_stamps()
        doc = yardstick(a.manifest, out_root)
        for k, s in doc["between_seed_sd"].items():
            print(f"  {k:22} SD {s['sd']:.3f}  values {np.round(s['values'], 2).tolist()}")
        for row in doc["power_restated"]:
            print(f"  power effect {row['effect']:+.0f} sd {row['sd']:.2f}: established overall "
                  f"{100 * row['established_overall']:.0f}%  refuted {100 * row['refuted']:.0f}%")
        print(f"frozen -> {RD.YARDSTICK}")
        return
    if not (a.context_manifest and a.context_root):
        raise SystemExit("--context-manifest and --context-root (the basicq2 population) are required")
    v = run_verdict(a.manifest, out_root, a.context_manifest, RD.guard_out_root(a.context_root))
    RD.dump(v, os.path.join(out_root, "verdict.json"))
    open(os.path.join(out_root, "verdict.md"), "w").write(to_markdown(v))
    print(f"written {out_root}/verdict.json, verdict.md; top-up required: {len(v['top_up_required'])}")


if __name__ == "__main__":
    main()
