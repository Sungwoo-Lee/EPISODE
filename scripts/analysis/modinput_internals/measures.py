"""Pure measures of the modulator-input internals screen (numpy only, no JAX): unit-testable.

Plain-language purpose: the screen hides felt injury from the modulator, from the main network, or
from both, and asks how much of the injured agent's extra bush dwell goes away. This file holds the
arithmetic for that (Q3: paired differences, the pooled "direct-input share", its "undefined" and
additivity rules, the survival guard) and the counting rules of predictions P1-P3.
Plan: docs/experiments/active/modulator_clues/MODULATOR_INPUT_INTERNALS.md, Revision 1 and 1a
(they override the earlier sections).

Data layout for Q3: for one agent and one scene pair (injured 70 / unhurt 0), `dwell[cond]` and
`surv[cond]` are arrays (K, N, 2): K checkpoints, N episode seeds (the same seeds in every
condition, scene and checkpoint), last axis 0 = injured, 1 = unhurt. Bush dwell is a fraction;
results are reported in percentage points (pp).

Conventions:
* Injury effect of a condition = mean injured dwell - mean unhurt dwell, averaged over checkpoints
  ("pooled"). Unhurt runs are identical across conditions (asserted by the driver), so differences
  between conditions are differences of injured dwell, paired by seed.
* Bootstrap = resampling episode SEEDS with replacement, jointly across conditions, scenes and
  checkpoints (one index draw per replicate is applied everywhere); 95% percentile interval.
* Share = (E_live - E_mod) / (E_live - E_both), pooled. "undefined" when the interval of E_live
  or of the divisor (E_live - E_both) includes 0 (Revision 1a).
* Interaction = (live - mod - main + both) of the pooled injury effects. "additive" only if its
  interval includes 0 AND its half-width is under half the |divisor|; otherwise "additivity not
  established" and no share is read.
* Survival guard: a hidden condition whose pooled injured survival is more than 10% below live's
  is flagged and left out of the share (Revision 1a).
"""
from __future__ import annotations

import numpy as np

CONDITIONS = ("live", "mod_hidden", "main_hidden", "both_hidden")
N_BOOT = 10000
CI = 0.95
BOOT_SEED = 20261008
SURVIVAL_DROP = 0.10
SHARE_THRESHOLD = 0.25        # P3
RULE_K = 7                    # "at least 7 of 9 checkpoints" (P1, P2)


def _check(dwell):
    shapes = {c: np.asarray(dwell[c]).shape for c in CONDITIONS}
    if len(set(shapes.values())) != 1:
        raise ValueError(f"conditions differ in shape: {shapes}")
    s = next(iter(shapes.values()))
    if len(s) != 3 or s[2] != 2:
        raise ValueError(f"expected (checkpoints, seeds, 2[injured, unhurt]), got {s}")
    return s


def boot_indices(n, n_boot=N_BOOT, seed=BOOT_SEED):
    """(n_boot, n) seed indices; row 0 is NOT the identity (the point estimate is computed apart)."""
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def _effects(dwell, idx=None):
    """Pooled injury effect per condition, in pp. idx (n_boot, N) -> arrays (n_boot,)."""
    out = {}
    for c in CONDITIONS:
        d = np.asarray(dwell[c], np.float64)
        if idx is None:
            out[c] = 100.0 * float((d[..., 0] - d[..., 1]).mean())
        else:
            e = d[..., 0] - d[..., 1]                       # (K, N)
            out[c] = 100.0 * e[:, idx].mean(axis=(0, 2))   # (n_boot,)
    return out


def interval(samples, ci=CI):
    a = (1.0 - ci) / 2.0
    lo, hi = np.quantile(np.asarray(samples, np.float64), [a, 1.0 - a])
    return float(lo), float(hi)


def _includes0(iv):
    return iv[0] <= 0.0 <= iv[1]


def paired_dwell_difference(dwell, a="live", b="mod_hidden", ck=None, idx=None):
    """Injured dwell, condition a minus b, in pp, with a bootstrap interval over seeds.
    `ck`: a checkpoint index (per-checkpoint value) or None (pooled over checkpoints)."""
    _check(dwell)
    da = np.asarray(dwell[a], np.float64)[..., 0]
    db = np.asarray(dwell[b], np.float64)[..., 0]
    d = da - db                                                # (K, N)
    if ck is not None:
        d = d[ck:ck + 1]
    if idx is None:
        idx = boot_indices(d.shape[1])
    point = 100.0 * float(d.mean())
    bs = 100.0 * d[:, idx].mean(axis=(0, 2))
    lo, hi = interval(bs)
    return {"diff_pp": point, "ci_lo": lo, "ci_hi": hi}


def survival_guard(surv, drop=SURVIVAL_DROP):
    """{cond: {"injured_survival": pooled mean, "drop_frac": (live - cond)/live, "flagged"}}."""
    _check(surv)
    live = float(np.asarray(surv["live"], np.float64)[..., 0].mean())
    out = {}
    for c in CONDITIONS:
        m = float(np.asarray(surv[c], np.float64)[..., 0].mean())
        f = (live - m) / live if live > 0 else float("nan")
        out[c] = {"injured_survival": m, "drop_frac": f, "flagged": bool(c != "live" and f > drop)}
    return out


def pooled_share(dwell, surv, n_boot=N_BOOT, seed=BOOT_SEED):
    """The direct-input share and its reading for one agent and scene (see module docstring).

    Returns a dict with the pooled effects per condition (pp), the numerator (E_live - E_mod),
    divisor (E_live - E_both), interaction, their intervals, the survival guard, and
    `reading` in {"share", "undefined", "additivity not established", "excluded: survival guard"};
    `share` is a number only when reading == "share" (otherwise it is still reported as
    `share_point` for the record, never as the result)."""
    K, N, _ = _check(dwell)
    idx = boot_indices(N, n_boot, seed)
    pt = _effects(dwell)
    bs = _effects(dwell, idx)
    num_pt, div_pt = pt["live"] - pt["mod_hidden"], pt["live"] - pt["both_hidden"]
    int_pt = pt["live"] - pt["mod_hidden"] - pt["main_hidden"] + pt["both_hidden"]
    num_bs = bs["live"] - bs["mod_hidden"]
    div_bs = bs["live"] - bs["both_hidden"]
    int_bs = bs["live"] - bs["mod_hidden"] - bs["main_hidden"] + bs["both_hidden"]
    iv_live, iv_div, iv_num, iv_int = interval(bs["live"]), interval(div_bs), interval(num_bs), interval(int_bs)
    half = (iv_int[1] - iv_int[0]) / 2.0
    guard = survival_guard(surv)
    flagged = [c for c in CONDITIONS if guard[c]["flagged"]]
    additive = bool(_includes0(iv_int) and half < 0.5 * abs(div_pt))
    undefined = bool(_includes0(iv_live) or _includes0(iv_div))
    with np.errstate(divide="ignore", invalid="ignore"):
        share_pt = num_pt / div_pt if div_pt != 0 else float("nan")
        share_bs = np.where(div_bs != 0, num_bs / div_bs, np.nan)
    if flagged:
        reading = "excluded: survival guard"
    elif undefined:
        reading = "undefined"
    elif not additive:
        reading = "additivity not established"
    else:
        reading = "share"
    res = {"checkpoints": K, "episodes": N,
           **{f"effect_{c}_pp": pt[c] for c in CONDITIONS},
           "effect_live_ci_lo": iv_live[0], "effect_live_ci_hi": iv_live[1],
           "numerator_pp": num_pt, "numerator_ci_lo": iv_num[0], "numerator_ci_hi": iv_num[1],
           "divisor_pp": div_pt, "divisor_ci_lo": iv_div[0], "divisor_ci_hi": iv_div[1],
           "interaction_pp": int_pt, "interaction_ci_lo": iv_int[0], "interaction_ci_hi": iv_int[1],
           "interaction_halfwidth_pp": half, "additive": additive, "undefined": undefined,
           "survival_flagged": ",".join(flagged),
           **{f"inj_survival_{c}": guard[c]["injured_survival"] for c in CONDITIONS},
           **{f"inj_survival_drop_{c}": guard[c]["drop_frac"] for c in CONDITIONS},
           "share_point": float(share_pt),
           "share_boot_ci_lo": float(np.nanquantile(share_bs, (1 - CI) / 2)),
           "share_boot_ci_hi": float(np.nanquantile(share_bs, 1 - (1 - CI) / 2)),
           "reading": reading,
           "share": float(share_pt) if reading == "share" else None}
    return res


# ------------------------------------------------------------------ P1 / P2 counting
def count_greater(a, b):
    """Per-checkpoint count of a > b (aligned arrays; NaN counts as not greater)."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    if a.shape != b.shape:
        raise ValueError(f"misaligned checkpoints: {a.shape} vs {b.shape}")
    return int(np.sum(a > b)), int(len(a))


def p1(variant_rows, reference_rows):
    """P1 per variant: E1 larger than the reference's at >= 7 of 9 checkpoints, on BOTH
    co-primary rows (`trace` teacher-forced trace, `const` 0.70). Inputs:
    {variant: {"trace": [9], "const": [9]}}, {"trace": [9], "const": [9]}."""
    out = {}
    for v, r in variant_rows.items():
        ct, n = count_greater(r["trace"], reference_rows["trace"])
        cc, _ = count_greater(r["const"], reference_rows["const"])
        out[v] = {"trace_count": ct, "const_count": cc, "n": n,
                  "holds": bool(ct >= RULE_K and cc >= RULE_K)}
    return out


def p2(variant_shift, reference_shift, ordinary_shift):
    """P2: in at least one variant the raw memory-state shift at 0.70 exceeds the ordinary
    partner's at >= 7 of 9 checkpoints, while the reference does not (Revision 1/1a; a pass is a
    hint, not a result: three chances, strongly alike checkpoints)."""
    per = {v: count_greater(s, ordinary_shift) for v, s in variant_shift.items()}
    ref, n = count_greater(reference_shift, ordinary_shift)
    any_v = any(c >= RULE_K for c, _ in per.values())
    return {"variants": {v: {"count": c, "n": nn, "exceeds": bool(c >= RULE_K)} for v, (c, nn) in per.items()},
            "reference": {"count": ref, "n": n, "exceeds": bool(ref >= RULE_K)},
            "holds": bool(any_v and ref < RULE_K)}


def p3(shares):
    """P3: for every one of N, I and IT, the pooled rabbit-scene share is defined, additive, not
    excluded and >= 0.25. `shares`: {variant: pooled_share(...) result for the rabbit scene}.
    The reference comparison is descriptive only and is not part of this count."""
    per = {}
    for v, r in shares.items():
        ok = r["reading"] == "share" and r["share"] is not None and r["share"] >= SHARE_THRESHOLD
        per[v] = {"reading": r["reading"], "share": r["share"], "share_point": r["share_point"],
                  "holds": bool(ok)}
    return {"variants": per, "holds": bool(per) and all(x["holds"] for x in per.values())}
