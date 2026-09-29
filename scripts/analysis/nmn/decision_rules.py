"""The pre-registered decision rules of "What Both Agents Compute", turned into tested code.

Plain-language purpose: the rules file
(docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml) says, in words
and before any number existed, when the ordinary and the modulated agent count as computing
"the same" thing (A1 layer similarity, A2 decoding, A3 seed yardstick, A4 across worlds), when
a gate blocks every verdict, and how the wake-up timing (B2) is read across worlds. This module
implements each rule's LOGIC as one function. It never holds a number of its own: every
threshold, count and quantile is read by name from the rules file's `parameters:` block (a test
fails on any numeric literal here other than 0 and 1), and a second test checks that every
`parameters:` entry is read by some function.

Contract (tooling plan §E):
- The rules file is loaded and its whole-file sha256 checked by `rules_pin.load` (re-exported
  here as `load`); there is one loader.
- What a manifest's evidence status may say comes from the rules' `evidence_status.<status>`
  (`verdict_policy`). Every `evaluate_*` takes that policy and refuses to run when verdict
  words are not allowed (the pilot); for `interim` every word it returns carries the rules'
  prefix. A B2 manifest never yields an A1-A4 verdict and an A1-A4 manifest never a B2 reading.
- A combination of inputs the rules' prose does not assign raises ValueError naming the case;
  the evaluator never picks an outcome.
- The functions take SUMMARY statistics (band edges, point estimates, bootstrap quantiles)
  so that the fixture table in tests/analysis/test_nmn_decision_rules.py reads as the rules
  do. `summarise_pairs` turns the drivers' joint bootstrap draws into those summaries.

Each function's docstring quotes the rule text it implements.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, §E, File Changes §6.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from scripts.analysis.nmn import rules_pin
from scripts.analysis.nmn.rules_pin import PinnedRules

load = rules_pin.load
param = rules_pin.param
require_clean = rules_pin.require_clean

# ----------------------------------------------------------------------- the rules' words --
SAME = "same"
SAME_LINEAR = "same up to a linear re-weighting"
DIFFERENT = "different"
UNDETERMINED = "undetermined at 3 seeds"
UNINFORMATIVE_STAT = "uninformative — no verdict"
UNINFORMATIVE_LAYER = "uninformative (no verdict)"
YARDSTICK_INCOMPLETE = "undetermined — yardstick incomplete"
CLOSER_FLAG = "closer than two ordinary seeds"
MM_QUALIFIER = "modulated agents also differ among themselves more than ordinary agents do"

A2_MATCH = "match"
A2_MATCH_ABSENT = "match — absent in both"
A2_MATCHING, A2_DIFFERS, A2_UNDETERMINED = "matching", "differs", "undetermined"
A2_ONE_LAYER = "one-layer difference (not counted)"

A3_A = "(a) inherited from the shared start"
A3_B = "(b) the task forces one solution"
A3_BPLUS = "(b+) one solution, with a same-seed excess"
A3_C = "(c) different processing, same outcome"
A3_CPRIME = "(c') different processing, different outcome"
A3_NONE = "none of the three patterns (undetermined at 3 seeds)"
MIXED = "mixed across layers"

A4_TOGETHER = "move together"
A4_INDEPENDENT = "move independently"
A4_NO_MOVEMENT = "no measurable movement across worlds — undetermined"

B2_LATE, B2_EARLY, B2_UNDETERMINED = "late", "early", "undetermined across worlds"
B2_AGREE, B2_DISAGREE = "agree", "do not agree"

B2_STATUS = "b2_wakeup"   # rules evidence_status key whose rule admits only the B2 reading


def blocked(ids) -> str:
    return "blocked by gate " + ", ".join(ids)


# ------------------------------------------------------------------------ policy + order --
@dataclass(frozen=True)
class Policy:
    status: str
    allowed: bool
    prefix: str | None
    label: str | None


def verdict_policy(pinned: PinnedRules, status: str) -> Policy:
    """`evidence_status.<status>` of the rules: whether verdict words are allowed, the
    `verdict_prefix` and the `label` (None where the rules give none). A status that is not a
    key of the rules' evidence_status mapping raises."""
    pol = rules_pin.evidence_policy(pinned, status)
    return Policy(status=status, allowed=bool(pol["verdict_words_allowed"]),
                  prefix=pol.get("verdict_prefix"), label=pol.get("label"))


def enforce_order(pinned: PinnedRules, policy: Policy) -> None:
    """Drivers call this first: whenever the status allows verdict words (read from the rules,
    never a status list), the rules file must be committed and clean."""
    if policy.allowed:
        require_clean(pinned)


def _check_policy(policy: Policy, *, b2: bool) -> None:
    if not policy.allowed:
        raise ValueError(f"evidence status {policy.status!r}: the rules allow no verdict word; "
                         f"the decision functions must not be called")
    if b2 and policy.status != B2_STATUS:
        raise ValueError(f"the B2 reading is only produced under {B2_STATUS!r}, "
                         f"not {policy.status!r}")
    if not b2 and policy.status == B2_STATUS:
        raise ValueError(f"{B2_STATUS!r}: a B2 manifest never produces an A1-A4 verdict")


def _word(policy: Policy, w: str) -> str:
    return f"{policy.prefix}: {w}" if policy.prefix else w


def _gate_word(gates: dict, yardstick_complete: bool) -> str | None:
    """'a failed gate blocks every verdict word; the output reads "blocked by gate <id>"'.
    G5 below its minimum instead reads "undetermined — yardstick incomplete"."""
    for k, v in gates.items():
        if not isinstance(v, bool):
            raise ValueError(f"gate {k}: expected pass/fail, got {v!r}")
    failed = [k for k, v in gates.items() if not v]
    if failed:
        return blocked(failed)
    if not yardstick_complete:
        return YARDSTICK_INCOMPLETE
    return None


# ------------------------------------------------------------------ settings for drivers --
def split_settings(P) -> dict:
    """common.split: 'Group-wise train/test split by episode_seed, n_repeats repeats, test
    fraction test_frac'."""
    return {"n_repeats": int(param(P, "common.split.n_repeats")),
            "test_frac": float(param(P, "common.split.test_frac"))}


def survival_settings(P) -> dict:
    """common.survival_level: window, row weighting and the _window_n skip."""
    return {"window_episodes": float(param(P, "common.survival.window_episodes")),
            "row_weight": param(P, "common.survival.row_weight"),
            "min_window_n": float(param(P, "common.survival.min_window_n"))}


def b2_settings(P) -> dict:
    """Every B2 constant (parameters.B2), for run_wakeup to pass to wakeup.t_cross / lag and
    to check against the manifest's `wakeup:` block."""
    keys = ("threshold_mode_headline", "f", "literal_f", "plateau_f", "final_k", "noise_k",
            "sustain", "min_noise_points", "noise_window_divisor", "noise_window_max_fraction",
            "lag_coincident_max_intervals", "sign_test_alpha", "sign_test_null_p")
    return {k: param(P, f"B2.{k}") for k in keys}


def g5_stage_index(P) -> int:
    """gates.G5.stage is 1-based (May design naming); stage/index = k - 1."""
    return int(param(P, "gates.G5.stage")) - 1


def survival_stage_index(P, status: str) -> int:
    """A3.survival_stage_by_status.<status> (1-based); stage/index = k - 1. A status with no
    entry (pilot, b2_wakeup) raises."""
    return int(param(P, f"A3.survival_stage_by_status.{status}")) - 1


# ------------------------------------------------------------------------------- gates ----
def _near_tie_pass(report: dict, min_agree: float, P) -> bool:
    margin = float(param(P, "gates.G1.near_tie_logit_margin"))
    if float(report["near_tie_logit_margin"]) != margin:
        raise ValueError(f"report classified near-ties at margin {report['near_tie_logit_margin']}"
                         f", the rules' G1 margin is {margin}")
    n = int(report["rows"])
    if n <= 0:
        raise ValueError("gate report has no rows")
    hard, tie = int(report["disagree_not_near_tie"]), int(report["disagree_near_tie"])
    return (1 - hard / n) >= min_agree \
        and tie / n <= float(param(P, "gates.G1.near_tie_fraction_max"))


def gate_G1(report: dict, P) -> bool:
    """G1_self_replay: 'argmax action at row t equals the stored action at row t+1 on at least
    parameters.gates.G1.action_agreement_min of rows, except near-ties (top-two logit margin <
    parameters.gates.G1.near_tie_logit_margin), which may disagree on at most
    parameters.gates.G1.near_tie_fraction_max of rows.'

    report: {rows, disagree_not_near_tie, disagree_near_tie, near_tie_logit_margin}."""
    return _near_tie_pass(report, float(param(P, "gates.G1.action_agreement_min")), P)


def gate_G2(deviations: dict, P) -> tuple[bool, list]:
    """G2_reconstruction: every reconstruction assertion within
    '|Δ| <= parameters.gates.G2.reconstruction_rel_tol * max(1, max|reference|)'.

    deviations: {assertion: {max_abs_dev, max_abs_ref}}. Returns (pass, failing assertions)."""
    if not deviations:
        raise ValueError("G2: no reconstruction assertions reported")
    tol = float(param(P, "gates.G2.reconstruction_rel_tol"))
    bad = [k for k, d in deviations.items()
           if not float(d["max_abs_dev"]) <= tol * max(1, float(d["max_abs_ref"]))]
    return not bad, bad


def gate_G3(report: dict, P) -> bool:
    """G3_alignment: 'action[t+1] decoded from logits[t] agrees on at least
    parameters.gates.G3.alignment_agreement_min of rows, with the same near-tie allowance as G1
    ...; the shift-by-one control agrees on fewer than
    parameters.gates.G3.shift_control_agreement_max of rows.'

    report: {alignment: <G1-shaped report>, shift_control_agreement: fraction}."""
    ok = _near_tie_pass(report["alignment"], float(param(P, "gates.G3.alignment_agreement_min")), P)
    return ok and float(report["shift_control_agreement"]) < float(
        param(P, "gates.G3.shift_control_agreement_max"))


def gate_G4(stats: dict, P) -> bool:
    """G4_controls: 'Input-layer satiation R^2 >= parameters.gates.G4.input_satiation_r2_min;
    shuffled-across-episode targets give R^2 <= parameters.gates.G4.shuffled_r2_max for every
    quantity; no episode group appears in both folds.'

    stats: {input_satiation_r2, shuffled_r2: {quantity: r2}, groups_disjoint: bool}."""
    if not stats["shuffled_r2"]:
        raise ValueError("G4: no shuffled-target R^2 reported")
    return (float(stats["input_satiation_r2"]) >= float(param(P, "gates.G4.input_satiation_r2_min"))
            and all(float(v) <= float(param(P, "gates.G4.shuffled_r2_max"))
                    for v in stats["shuffled_r2"].values())
            and bool(stats["groups_disjoint"]))


def gate_G5(per_run: dict, P) -> dict:
    """G5_competence: 'A run enters only if it passes the May replication's stage-1 competence
    gate: S_k with k = parameters.gates.G5.stage >= parameters.gates.G5.stage1_survival_min_steps
    and mean Episode/FoodEaten over the same window >= parameters.gates.G5.stage1_food_bites_min.
    Minimum after exclusions: parameters.gates.G5.min_ordinary_seeds ordinary seeds and
    parameters.gates.G5.min_modulated_seeds modulated seeds. Below that, every A1–A4 verdict is
    "undetermined — yardstick incomplete".'

    per_run: {label: {arm: "ordinary"|"modulated", S, bites}} at stage/index g5_stage_index(P).
    A run whose S or bites is missing raises (the stage is not complete)."""
    s_min = float(param(P, "gates.G5.stage1_survival_min_steps"))
    b_min = float(param(P, "gates.G5.stage1_food_bites_min"))
    out, entered = {}, {"ordinary": [], "modulated": []}
    for label, r in per_run.items():
        if r["arm"] not in entered:
            raise ValueError(f"G5: run {label}: arm {r['arm']!r} is neither ordinary nor modulated")
        if r["S"] is None or r["bites"] is None:
            raise ValueError(f"G5: run {label} has no stage-{param(P, 'gates.G5.stage')} survival "
                             f"or bites (stage not complete); the gate cannot be evaluated")
        ok = float(r["S"]) >= s_min and float(r["bites"]) >= b_min
        out[label] = ok
        if ok:
            entered[r["arm"]].append(label)
    complete = (len(entered["ordinary"]) >= int(param(P, "gates.G5.min_ordinary_seeds"))
                and len(entered["modulated"]) >= int(param(P, "gates.G5.min_modulated_seeds")))
    return {"per_run": out, "entered": entered, "yardstick_complete": complete,
            "stage_index": g5_stage_index(P)}


def gate_G6(stats: dict, P) -> dict:
    """G6_sizes: 'bootstrap_n >= parameters.gates.G6.bootstrap_n_min. Every held-out fold holds
    >= parameters.gates.G6.test_fold_groups_min DISTINCT episode_seed groups, counted separately
    for every quantity and statistic on the rows it actually uses.'

    stats: {bootstrap_n, test_groups: {quantity_or_statistic: [groups per split repeat]}}.
    Returns {bootstrap_ok, per_key: {key: bool}}. A group list whose length is not
    common.split.n_repeats raises."""
    n_rep = int(param(P, "common.split.n_repeats"))
    g_min = int(param(P, "gates.G6.test_fold_groups_min"))
    per = {}
    for k, counts in stats["test_groups"].items():
        if len(counts) != n_rep:
            raise ValueError(f"G6: {k}: {len(counts)} split repeats reported, the rules fix {n_rep}")
        per[k] = all(int(c) >= g_min for c in counts)
    return {"bootstrap_ok": int(stats["bootstrap_n"]) >= int(param(P, "gates.G6.bootstrap_n_min")),
            "per_key": per}


# ------------------------------------------------------------- summaries from draws --------
def _quantiles(draws, P) -> tuple[float, float]:
    lo, hi = param(P, "common.bootstrap_interval")
    q = np.quantile(np.asarray(draws, dtype=float), [float(lo), float(hi)])
    return float(q[0]), float(q[1])


def summarise_pairs(pairs: dict, P) -> dict:
    """Turn joint bootstrap draws into the summaries the rules read.

    pairs: {pair_set: {pair_name: {"point": float, "draws": array}}} for pair sets among OO,
    MM, MO_diff, MO_same, UNTRAINED; every draws array has the same length (joint draws).

    common.seed_band: 'L = the lowest lower-quantile bootstrap value among the 3 OO pairs;
    U = the highest upper-quantile value among them.' The UNTRAINED band is the same
    construction on the UNTRAINED pairs (A1.informative_gate). 'the bootstrap distribution of
    the MO_diff mean': per draw, the mean over the pairs entered, then its quantiles."""
    def band(ps):
        qs = [_quantiles(p["draws"], P) for p in ps.values()]
        return (min(q[0] for q in qs), max(q[1] for q in qs))

    def mean_q(ps):
        return _quantiles(np.mean(np.stack([np.asarray(p["draws"], float) for p in ps.values()]),
                                  axis=0), P)

    lens = {len(p["draws"]) for s in pairs.values() for p in s.values()}
    if len(lens) != 1:
        raise ValueError(f"draws of unequal length {lens}: not joint draws")
    out = {"band": band(pairs["OO"]),
           "untrained_band": band(pairs["UNTRAINED"]) if pairs.get("UNTRAINED") else None,
           "mo_diff": [float(p["point"]) for p in pairs["MO_diff"].values()],
           "mo_diff_mean_q": mean_q(pairs["MO_diff"])}
    if pairs.get("MM"):
        out["mm_upper_max"] = max(_quantiles(p["draws"], P)[1] for p in pairs["MM"].values())
    if pairs.get("MO_same"):
        out["mo_same"] = [float(p["point"]) for p in pairs["MO_same"].values()]
        out["mo_same_mean_q"] = mean_q(pairs["MO_same"])
    return out


# ------------------------------------------------------------------------------------ A1 ---
def per_statistic(s: dict, P) -> dict:
    """A1.per_statistic_verdict (n = number of MO_diff pairs that entered):
    same: 'at most floor(n / parameters.A1.same_max_below_divisor) of the n MO_diff point
    estimates lie below L, AND the lower-quantile of the bootstrap distribution of the MO_diff
    mean is >= L. MO_diff values above U also count as same, flagged "closer than two ordinary
    seeds".'
    different: 'ALL n MO_diff point estimates lie below L, AND the upper-quantile of the
    bootstrap distribution of the MO_diff mean is < L.'
    undetermined_at_3_seeds: 'every other case.'

    s: {band: (L, U), mo_diff: [points], mo_diff_mean_q: (lo, hi)}."""
    L, U = (float(v) for v in s["band"])
    pts = [float(v) for v in s["mo_diff"]]
    n = len(pts)
    if n < 1:
        raise ValueError("no MO_diff pairs")
    lo, hi = (float(v) for v in s["mo_diff_mean_q"])
    below = sum(v < L for v in pts)
    if below <= n // int(param(P, "A1.same_max_below_divisor")) and lo >= L:
        return {"word": SAME, "flag": CLOSER_FLAG if any(v > U for v in pts) else None,
                "n": n, "below_L": below}
    if below == n and hi < L:
        return {"word": DIFFERENT, "flag": None, "n": n, "below_L": below}
    return {"word": UNDETERMINED, "flag": None, "n": n, "below_L": below}


def statistic_verdict(s: dict, P) -> dict:
    """A1.informative_gate, then per_statistic: 'If the OO band [L, U] intersects
    [L_untr, U_untr], ... that statistic on that layer reads "uninformative — no verdict".'
    s additionally holds untrained_band (L_untr, U_untr); None (no UNTRAINED pair) raises."""
    if s.get("untrained_band") is None:
        raise ValueError("no UNTRAINED pairs: the informative gate is not computable")
    L, U = (float(v) for v in s["band"])
    Lu, Uu = (float(v) for v in s["untrained_band"])
    if L <= Uu and Lu <= U:
        return {"word": UNINFORMATIVE_STAT, "flag": None, "n": len(s["mo_diff"]), "below_L": None}
    return per_statistic(s, P)


def layer_verdict(pred: str, cka: str) -> str:
    """A1.layer_verdict (predictivity decides; CKA qualifies):
    predictivity same AND CKA same -> same; predictivity same AND CKA different, undetermined
    or uninformative -> same up to a linear re-weighting (counts as same); predictivity
    different (any CKA) -> different; predictivity undetermined (any CKA) -> undetermined at 3
    seeds; predictivity uninformative (any CKA) -> uninformative (no verdict)."""
    stat_words = (SAME, DIFFERENT, UNDETERMINED, UNINFORMATIVE_STAT)
    if pred not in stat_words or cka not in stat_words:
        raise ValueError(f"A1 layer verdict: no rule row for predictivity {pred!r}, CKA {cka!r}")
    if pred == SAME:
        return SAME if cka == SAME else SAME_LINEAR
    return {DIFFERENT: DIFFERENT, UNDETERMINED: UNDETERMINED,
            UNINFORMATIVE_STAT: UNINFORMATIVE_LAYER}[pred]


def counts_as_same(word: str) -> bool:
    return word in (SAME, SAME_LINEAR)


def _check_layers(layers, verdict_layers):
    if list(layers) != list(verdict_layers):
        raise ValueError(f"inputs cover layers {list(layers)}, the rules' verdict layers are "
                         f"{list(verdict_layers)}")


def study_reading_A1(layer_words: dict, P) -> dict:
    """A1.study_verdict: same 'all 5 verdict layers read same (either form)'; different 'any
    verdict layer reads different; the layers are listed'; undetermined 'otherwise'.
    Also refutation.remedy_if_undetermined, REPORTED only: 'if A1 is undetermined in at least
    parameters.remedy.undetermined_layers_trigger of the 5 layers, the remedy is two more seeds
    per agent type (parameters.remedy.extra_seeds)' — decided by the user, never acted on here."""
    diff = [k for k, w in layer_words.items() if w == DIFFERENT]
    und = [k for k, w in layer_words.items() if w == UNDETERMINED]
    if all(counts_as_same(w) for w in layer_words.values()):
        v = SAME
    elif diff:
        v = DIFFERENT
    else:
        v = "undetermined"
    return {"verdict": v, "different_layers": diff, "undetermined_layers": und,
            "remedy_triggered": len(und) >= int(param(P, "remedy.undetermined_layers_trigger")),
            "remedy_extra_seeds": list(param(P, "remedy.extra_seeds"))}


def evaluate_A1(inputs: dict, P, *, policy: Policy, verdict_layers, gates: dict,
                yardstick_complete: bool) -> dict:
    """A1 per verdict layer and study-wide.

    inputs: {layer: {"predictivity": summary, "cka": summary}} (summaries as
    `summarise_pairs`; predictivity's may carry mm_upper_max).
    A1.mm_qualifier: 'If the whole MM band lies below L (the highest MM upper-quantile < L),
    every "different" verdict carries "modulated agents also differ among themselves more than
    ordinary agents do". It does not change the verdict word.'"""
    _check_policy(policy, b2=False)
    _check_layers(inputs, verdict_layers)
    gw = _gate_word(gates, yardstick_complete)
    layers, words = {}, {}
    for k, v in inputs.items():
        if gw:
            layers[k], words[k] = {"verdict": _word(policy, gw)}, gw
            continue
        pr, ck = statistic_verdict(v["predictivity"], P), statistic_verdict(v["cka"], P)
        w = layer_verdict(pr["word"], ck["word"])
        qual = None
        if w == DIFFERENT and v["predictivity"].get("mm_upper_max") is not None \
                and float(v["predictivity"]["mm_upper_max"]) < float(v["predictivity"]["band"][0]):
            qual = MM_QUALIFIER
        layers[k] = {"verdict": _word(policy, w), "predictivity": pr, "cka": ck, "qualifier": qual}
        words[k] = w
    study = study_reading_A1(words, P) if not gw else {
        "verdict": gw, "different_layers": [], "undetermined_layers": [],
        "remedy_triggered": False, "remedy_extra_seeds": list(param(P, "remedy.extra_seeds"))}
    study["verdict"] = _word(policy, study["verdict"])
    return {"layers": layers, "layer_words": words, "study": study}


# ------------------------------------------------------------------------------------ A2 ---
def _seed_need(n_arm: int, rule_min: int, P) -> int:
    """common.two_modulated_seeds: 'every count over the modulated arm's seeds reads over the 2
    that entered: "all 3" reads "both", and "≥ 2 of 3" reads "both".' The full seed count is
    the ordinary arm's (gates.G5.min_ordinary_seeds, 'all 3 ordinary seeds are always
    required')."""
    full = int(param(P, "gates.G5.min_ordinary_seeds"))
    if n_arm >= full:
        return rule_min
    if n_arm >= int(param(P, "gates.G5.min_modulated_seeds")):
        return n_arm
    raise ValueError(f"an arm with {n_arm} seeds is below the G5 minimum; no count applies")


def beats_clock(agent: dict, P) -> bool:
    """A2.beats_clock: 'R^2 - R^2_clock >= parameters.A2.beats_clock_margin_r2 AND the bootstrap
    lower-quantile of that excess is > 0.' agent: {excess, excess_q_lo}."""
    return (float(agent["excess"]) >= float(param(P, "A2.beats_clock_margin_r2"))
            and float(agent["excess_q_lo"]) > 0)


def a2_layer(ordinary: list, modulated: list, P) -> dict:
    """A2.per_layer_comparison for one quantity and layer.
    spread_O: 'range (max - min) of the 3 ordinary agents' R^2 point estimates, floored at the
    mean width of their bootstrap intervals'. gap: 'mean R^2 of the modulated seeds minus mean
    R^2 of the ordinary seeds'. arm_encodes: 'at least parameters.A2.arm_min_seeds of its 3
    seeds beat the clock (common.two_modulated_seeds: both)'.
    match: '|gap| <= spread_O AND both arms agree on arm_encodes (both encode, or neither: the
    latter reads "match — absent in both")'.
    different: '(all modulated R^2 values lie on the same side of all ordinary R^2 values AND
    |gap| > spread_O) OR (every seed of one arm beats the clock and none of the other arm's
    does)'. undetermined: 'every other case.'

    Each agent: {r2, r2_q: (lo, hi), excess, excess_q_lo}."""
    if len(ordinary) < 1 or len(modulated) < 1:
        raise ValueError("A2: an arm has no agent")
    ro = [float(a["r2"]) for a in ordinary]
    rm = [float(a["r2"]) for a in modulated]
    width = float(np.mean([float(a["r2_q"][1]) - float(a["r2_q"][0]) for a in ordinary]))
    spread = max(max(ro) - min(ro), width)
    gap = float(np.mean(rm) - np.mean(ro))
    bo = [beats_clock(a, P) for a in ordinary]
    bm = [beats_clock(a, P) for a in modulated]
    need_min = int(param(P, "A2.arm_min_seeds"))
    enc_o = sum(bo) >= _seed_need(len(bo), need_min, P)
    enc_m = sum(bm) >= _seed_need(len(bm), need_min, P)
    one_side = min(rm) > max(ro) or max(rm) < min(ro)
    all_vs_none = (all(bo) and not any(bm)) or (all(bm) and not any(bo))
    if abs(gap) <= spread and enc_o == enc_m:
        w = A2_MATCH if enc_o else A2_MATCH_ABSENT
    elif (one_side and abs(gap) > spread) or all_vs_none:
        w = DIFFERENT
    else:
        w = UNDETERMINED
    return {"word": w, "spread_O": spread, "gap": gap, "ordinary_encodes": enc_o,
            "modulated_encodes": enc_m, "ordinary_beats": bo, "modulated_beats": bm}


def evaluate_A2(inputs: dict, P, *, policy: Policy, quantities, verdict_layers, gates: dict,
                yardstick_complete: bool) -> dict:
    """A2 per quantity and study-wide.

    inputs: {quantity: {"g6_pass": bool, "layers": {layer: {"ordinary": [agent],
    "modulated": [agent]}}}}. A quantity failing G6 reads "blocked by gate G6".
    profile_verdict_per_quantity: matching 'all 5 verdict layers match'; differs 'at least
    parameters.A2.differs_min_layers of the 5 verdict layers are different. Fewer differing
    layers (but at least one) are reported as "one-layer difference (not counted)"';
    undetermined 'otherwise'. study_verdict: matching 'all 4 quantities matching'; differs
    'any quantity differs; the quantities and layers are listed'; undetermined 'otherwise'."""
    _check_policy(policy, b2=False)
    if list(inputs) != list(quantities):
        raise ValueError(f"inputs cover quantities {list(inputs)}, the rules' are {list(quantities)}")
    gw = _gate_word(gates, yardstick_complete)
    out, prof = {}, {}
    for q, qi in inputs.items():
        _check_layers(qi["layers"], verdict_layers)
        if gw or not qi["g6_pass"]:
            w = gw or blocked(["G6"])
            out[q] = {"profile": _word(policy, w), "layers": {}, "note": None}
            prof[q] = w
            continue
        lay = {k: a2_layer(v["ordinary"], v["modulated"], P) for k, v in qi["layers"].items()}
        n_diff = sum(r["word"] == DIFFERENT for r in lay.values())
        note = None
        if all(r["word"] in (A2_MATCH, A2_MATCH_ABSENT) for r in lay.values()):
            w = A2_MATCHING
        elif n_diff >= int(param(P, "A2.differs_min_layers")):
            w = A2_DIFFERS
        else:
            w = A2_UNDETERMINED
            if n_diff >= 1:
                note = A2_ONE_LAYER
        diff_layers = [k for k, r in lay.items() if r["word"] == DIFFERENT]
        for r in lay.values():
            r["word"] = _word(policy, r["word"])
        out[q] = {"profile": _word(policy, w), "layers": lay, "note": note,
                  "different_layers": diff_layers}
        prof[q] = w
    if gw:
        sv = gw
    elif all(w == A2_MATCHING for w in prof.values()):
        sv = A2_MATCHING
    elif any(w == A2_DIFFERS for w in prof.values()):
        sv = A2_DIFFERS
    else:
        sv = A2_UNDETERMINED
    return {"quantities": out, "profile_words": prof,
            "study": {"verdict": _word(policy, sv),
                      "differing_quantities": [q for q, w in prof.items() if w == A2_DIFFERS]}}


# ------------------------------------------------------------------------------------ A3 ---
def survival_difference(S_by_arm: dict, P) -> dict:
    """common.survival_level: 'The survival difference is modulated minus ordinary of the means
    over the seeds that entered; SE_k = sqrt(sd_k(ord)^2 / n_ord + sd_k(mod)^2 / n_mod);
    SE_used = max(SE_k, parameters.common.survival.se_floor_steps).' A3 pattern (c): 'inside
    parameters.common.survival.se_multiplier x SE_used'.

    S_by_arm: {"ordinary": [S_k per entered seed], "modulated": [...]}; any None -> not
    available (pattern (c)/(c') then reads none)."""
    o, m = S_by_arm["ordinary"], S_by_arm["modulated"]
    if any(v is None for v in list(o) + list(m)):
        return {"available": False, "same": None}
    o, m = np.asarray(o, float), np.asarray(m, float)
    if len(o) <= 1 or len(m) <= 1:
        raise ValueError("survival difference needs at least two seeds per arm (sample SD)")
    diff = float(m.mean() - o.mean())
    se = math.sqrt(o.var(ddof=1) / len(o) + m.var(ddof=1) / len(m))
    floor = float(param(P, "common.survival.se_floor_steps"))
    se_used = max(se, floor)
    return {"available": True, "mean_diff": diff, "se_raw": se, "se_used": se_used,
            "floored": se < floor,
            "same": abs(diff) <= float(param(P, "common.survival.se_multiplier")) * se_used}


def same_seed_excess(v: dict, precondition: bool) -> bool:
    """A3.same_seed_excess_E: 'E holds if every MO_same point estimate exceeds every MO_diff
    point estimate AND exceeds U, AND the bootstrap lower-quantile of the MO_same mean exceeds
    the upper-quantile of the MO_diff mean.' A3.precondition_shared_start: 'If any seed is not
    identical, E is treated as not holding.'"""
    if not precondition:
        return False
    ms, md = [float(x) for x in v["mo_same"]], [float(x) for x in v["mo_diff"]]
    U = float(v["U"])
    return (min(ms) > max(md) and min(ms) > U
            and float(v["mo_same_mean_q_lo"]) > float(v["mo_diff_mean_q_hi"]))


def a3_pattern(a1_word: str, E: bool, survival: dict) -> str:
    """A3.patterns (exactly one per layer):
    a: 'E holds AND the A1 layer verdict is NOT same'; b: 'A1 layer verdict same AND E does not
    hold'; b+: 'A1 layer verdict same AND E holds'; c: 'A1 layer verdict different AND E does
    not hold AND survival is the same'; c': '... AND the survival difference is beyond';
    none: 'every other case — A1 undetermined or uninformative without E, a blocked gate, or
    survival not available for pattern (c).'"""
    if counts_as_same(a1_word):
        return A3_BPLUS if E else A3_B
    if E:
        return A3_A
    if a1_word == DIFFERENT:
        if not survival["available"]:
            return A3_NONE
        return A3_C if survival["same"] else A3_CPRIME
    return A3_NONE


def _study_pattern(words: dict, P) -> str:
    """A3/A4 study_reading: 'the pattern held by at least parameters.study_reading.min_layers of
    the 5 verdict layers; otherwise "mixed across layers"'."""
    k = int(param(P, "study_reading.min_layers"))
    held = sorted({w for w in words.values() if sum(x == w for x in words.values()) >= k})
    if len(held) > 1:
        raise ValueError(f"study reading: several patterns reach {k} layers: {held}")
    return held[0] if held else MIXED


def evaluate_A3(inputs: dict, P, *, policy: Policy, verdict_layers, gates: dict,
                yardstick_complete: bool, precondition_shared_start: bool,
                survival: dict) -> dict:
    """A3 per verdict layer and study-wide.

    inputs: {layer: {a1_verdict, mo_same: [points], mo_diff: [points], U,
    mo_same_mean_q_lo, mo_diff_mean_q_hi}}; survival as `survival_difference` returns for the
    stage survival_stage_index(P, status). A blocked gate or an incomplete yardstick gives
    pattern "none" with the reason in `blocked`."""
    _check_policy(policy, b2=False)
    _check_layers(inputs, verdict_layers)
    gw = _gate_word(gates, yardstick_complete)
    layers, words = {}, {}
    for k, v in inputs.items():
        if gw:
            w, E = A3_NONE, None
        else:
            E = same_seed_excess(v, precondition_shared_start)
            w = a3_pattern(v["a1_verdict"], E, survival)
        layers[k] = {"pattern": _word(policy, w), "E": E, "blocked": gw}
        words[k] = w
    return {"layers": layers, "pattern_words": words,
            "study": {"reading": _word(policy, _study_pattern(words, P)), "blocked": gw},
            "precondition_shared_start": precondition_shared_start, "survival": survival}


# ------------------------------------------------------------------------------------ A4 ---
def a4_layout(P) -> dict:
    """A4.movement / within_stage_drift: the checkpoint sequence (parameters.A4.stage_sequence),
    its consecutive transitions x parameters.A4.probes (the movement profile), and
    parameters.A4.drift_pairs. The driver builds its profiles from this layout."""
    seq = list(param(P, "A4.stage_sequence"))
    probes = list(param(P, "A4.probes"))
    trans = [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
    return {"stage_sequence": seq, "probes": probes,
            "profile_entries": [(a, b, p) for (a, b) in trans for p in probes],
            "drift_pairs": [dict(d) for d in param(P, "A4.drift_pairs")]}


def arm_moves(q_lo: list, P) -> bool:
    """A4.movement_gate: 'An arm moves at a layer if, for at least
    parameters.A4.movement_min_seeds of its 3 seeds (common.two_modulated_seeds: both), the
    bootstrap lower-quantile of (mean movement - d_a) is > 0.'"""
    need = _seed_need(len(q_lo), int(param(P, "A4.movement_min_seeds")), P)
    return sum(float(q) > 0 for q in q_lo) >= need


def evaluate_A4(inputs: dict, P, *, policy: Policy, verdict_layers, gates: dict,
                yardstick_complete: bool) -> dict:
    """A4 per verdict layer and study-wide.

    inputs: {"layout": a4_layout(P) as the driver used it, "layers": {layer: {"movement":
    {"ordinary": [q_lo per seed], "modulated": [...]}, "co_movement": summary (band, mo_diff,
    mo_diff_mean_q of r), "stage_end_a1": {checkpoint: A1 layer word}}}}.
    thresholds: 'apply A1.per_statistic_verdict unchanged to r: together = same; independent =
    different'. move_together: 'movement gate passed AND co-movement "together" AND the A1
    layer verdict is not different at any of the five stage ends'. move_independently:
    'movement gate passed AND (co-movement "independent" OR the A1 layer verdict is same at one
    stage end and different at another)'. undetermined: 'every other case.' If either arm does
    not move: 'no measurable movement across worlds — undetermined'."""
    _check_policy(policy, b2=False)
    lay_expected = a4_layout(P)
    if inputs["layout"] != lay_expected:
        raise ValueError("A4 inputs were built on a layout other than parameters.A4's")
    _check_layers(inputs["layers"], verdict_layers)
    gw = _gate_word(gates, yardstick_complete)
    layers, words = {}, {}
    for k, v in inputs["layers"].items():
        if gw:
            layers[k], words[k] = {"reading": _word(policy, gw)}, gw
            continue
        if list(v["stage_end_a1"]) != lay_expected["stage_sequence"]:
            raise ValueError(f"A4 {k}: stage-end verdicts for {list(v['stage_end_a1'])}, the "
                             f"sequence is {lay_expected['stage_sequence']}")
        moves = {a: arm_moves(v["movement"][a], P) for a in ("ordinary", "modulated")}
        co = per_statistic(v["co_movement"], P)
        ends = list(v["stage_end_a1"].values())
        any_diff = any(w == DIFFERENT for w in ends)
        any_same = any(counts_as_same(w) for w in ends)
        if not all(moves.values()):
            w = A4_NO_MOVEMENT
        elif co["word"] == SAME and not any_diff:
            w = A4_TOGETHER
        elif co["word"] == DIFFERENT or (any_same and any_diff):
            w = A4_INDEPENDENT
        else:
            w = UNDETERMINED
        layers[k] = {"reading": _word(policy, w), "moves": moves, "co_movement": co}
        words[k] = w
    return {"layers": layers, "reading_words": words,
            "study": {"reading": _word(policy, gw or _study_pattern(words, P))}}


# ------------------------------------------------------------------------------------ B2 ---
def sign_test_k_star(n_def: int, P) -> int | None:
    """B2.reading_per_measure: 'k* = the smallest k with P(Binomial(n_def,
    parameters.B2.sign_test_null_p) >= k) <= parameters.B2.sign_test_alpha' (None when no
    k <= n_def satisfies it)."""
    p = float(param(P, "B2.sign_test_null_p"))
    alpha = float(param(P, "B2.sign_test_alpha"))
    for k in range(n_def + 1):
        tail = sum(math.comb(n_def, j) * p ** j * (1 - p) ** (n_def - j)
                   for j in range(k, n_def + 1))
        if tail <= alpha:
            return k
    return None


def evaluate_B2(level05: list, may: list, P, *, policy: Policy) -> dict:
    """B2.reading_per_measure, for one measure. level05 / may: per-run lag readings from
    `wakeup.lag` ("late" / "early" / "coincident", or None for an undefined lag).
    'n_def = runs with a defined lag (coincident runs included in n_def, counted as neither
    late nor early) ... "late" if at least k* runs have lag above the coincidence band; "early"
    if at least k* runs have lag below it; otherwise "undetermined across worlds" (also when no
    k <= n_def satisfies the condition). The May seeds are reported separately as "agree"
    (every May seed defined and on the side of the level-05 reading) or "do not agree".'"""
    _check_policy(policy, b2=True)
    ok = ("late", "early", "coincident", None)
    for r in list(level05) + list(may):
        if r not in ok:
            raise ValueError(f"B2: lag reading {r!r} is not one of {ok}")
    n_def = sum(r is not None for r in level05)
    n_late = sum(r == "late" for r in level05)
    n_early = sum(r == "early" for r in level05)
    k = sign_test_k_star(n_def, P)
    late = k is not None and n_late >= k
    early = k is not None and n_early >= k
    if late and early:
        raise ValueError("B2: both late and early reach k*; the rules assign no reading")
    reading = B2_LATE if late else (B2_EARLY if early else B2_UNDETERMINED)
    side = {B2_LATE: "late", B2_EARLY: "early"}.get(reading)
    agree = bool(may) and side is not None and all(r == side for r in may)
    return {"reading": _word(policy, reading), "n_def": n_def, "k_star": k, "n_late": n_late,
            "n_early": n_early, "may": _word(policy, B2_AGREE if agree else B2_DISAGREE)}
