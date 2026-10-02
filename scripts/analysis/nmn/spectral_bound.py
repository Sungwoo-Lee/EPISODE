"""Method 1 — how much can the neuromodulator move the network's output? Weights only.

Plain-language purpose
----------------------
A small side network (the "neuromodulator") watches the agent's senses and, at up to
four places inside the main network, multiplies each of 128 units by a number (the
**gain**, gamma) and adds a number to each (the **offset**, beta). The question this
module answers is a ceiling question: *given only the trained weights, and with no
rollout and no environment at all, how far apart can the network's output be for two
different things the modulator might be feeling?* If that ceiling is near zero, the
modulator cannot be doing anything, and we know it before commissioning any
expensive replay.

It is a **bound**, not a measurement. The real modulator will not reach the ceiling.
A large number here proves nothing; a small number here rules something out. That
asymmetry is the whole point of running this first.

The derivation, and every assumption in it
------------------------------------------
Write `m` for the modulator's hidden width (16 in these runs), `H` for the width of
the modulated layer (128), `K` for a head's weight matrix (shape `m x H`), `b` for
its bias, `g` for the learned per-unit baseline.

**(A1) The modulator's state lives in the open cube (-1, 1)^m.** Flax's GRU cell
computes `h_new = (1 - z) * n + z * h`, with `n = tanh(...)` in `(-1, 1)` and the
update gate `z = sigmoid(...)` in `(0, 1)`. The new state is therefore a convex
combination of a number in `(-1, 1)` and the old state. The run starts at `h = 0`
(`NeuromodulatorRNN.initial_state`), so by induction every state the modulator can
ever occupy satisfies `|h_j| < 1`. **This is exact, not an approximation.**

Every bound below is nonetheless stated on the CLOSED cube `[-1, 1]^m`, for two
reasons: it is what makes the "two states at opposite corners" swing well defined,
and in float32 the corner is actually attainable — `tanh` saturates to exactly 1.0
beyond an argument of about 9, and the update gate saturates to exactly 0 or 1. A
replay of the real runs measures `|h|` reaching exactly 1.0 in some arms
(`run_mod_distribution.py` checks this on every arm and fails if it ever exceeds 1),
so using the closed cube is not conservatism, it is correctness.

**(A2) The gain and offset are affine in that state.** From `neuromodulator.py`,
`gamma_i = (g_i + b_i) + sum_j K_ji h_j` (with `grouping_size = 1`; for `G > 1` the
head's group value is repeated across `G` units, which this module reproduces). The
first bracket is the **constant part** — the value at `h = 0` — and the sum is the
**contextual part**. Only the contextual part can differ between two moments in an
episode, so only it can carry information about context.

**(A3) The reachable swing of one unit is exact.** By (A1) and (A2), over all pairs
of reachable states the largest possible difference in unit `i`'s gain is

    swing_i(gamma) = 2 * ||K[:, i]||_1        (the column's sum of absolute values)

and likewise for the offset. `2` because the two states can sit at opposite corners
of the cube. This is the tightest weights-only statement available and it needs no
spectral norm at all.

**(A4) Vector-valued version.** `||Delta gamma||_2 <= sigma_max(K) * ||h - h'||_2 <=
2 * sqrt(m) * sigma_max(K)`, where `sigma_max` is the largest singular value. This
is the spectral-norm route; for a given head it can be tighter or looser than
`sqrt(H) * max_i swing_i`, so this module takes whichever is smaller.

**(A5) The pre-modulation activation is itself bounded, from weights alone.** The
FiLM operation is `u = gamma * a + beta` where `a` is the layer's own pre-activation.
`a` is bounded without any data because:

* at the **actor** and **critic** sites, `a = W1' x + b1` and `x` is the task GRU's
  emitted output, which by the same argument as (A1) lies in `(-1, 1)^H`;
* at the **recurrent** site, `a` *is* that GRU output, so `||a||_2 < sqrt(H)`;
* at the **encoder** site, LayerNorm sits immediately before the FiLM (these runs all
  have `use_layer_norm: true`), so its output has exactly zero mean and unit variance
  across the 128 features, giving `||z_hat||_2 = sqrt(H)` and `|z_hat_i| <=
  sqrt(H - 1)`; the learned LayerNorm scale and bias then give a weights-only bound.

**(A6) Everything downstream is bounded by operator norms.** ReLU is 1-Lipschitz, so
`||Delta u||` survives it, and each subsequent linear layer multiplies by at most its
largest singular value.

**(A7) The task GRU's single-step input sensitivity.** Only needed for the encoder
site, whose FiLM output must cross the recurrent cell before it reaches the policy.
Differentiating `h_new = (1 - z) n + z h` with respect to the cell's input, and using
`|h - n| <= 2`, `|sigmoid'| <= 1/4`, `|tanh'| <= 1`, `|1 - z| <= 1`:

    L_gru <= 0.5 * sigma(W_iz) + sigma(W_in) + 0.25 * M_n * sigma(W_ir)

with `M_n = max_j ||W_hn[:, j]||_1`, again by (A1) applied to the task GRU's own
state. **This holds the carry fixed** — it bounds the effect of perturbing one step's
input on that step's output, not the accumulated effect over an episode. The encoder
bound is therefore the loosest number this module reports, and is labelled as such.

What is reported, and what each number is a bound *on*
------------------------------------------------------
Per run, per checkpoint, per site:

* ``swing_gamma_max`` / ``swing_gamma_mean`` — widest / average reachable interval of
  a single gain unit. Dimensionless (a gain is a multiplier).
* ``swing_beta_max`` / ``swing_beta_mean`` — same for the offset, in units of the
  modulated layer's pre-activation.
* ``const_gamma_mean`` etc. — the constant (context-independent) part. Recorded
  because the optimisation-dynamics critique shows this part is a *gauge* quantity:
  it can be absorbed into the modulated layer's own weights with the network's
  function unchanged. It is here for the gauge check, not as an effect size.
* ``lipschitz_gamma`` / ``lipschitz_beta`` — bound on `||d signal / d observation||_2`
  at a fixed modulator carry. This is the rigorous form of Marquis & Farhood's
  product-of-spectral-norms estimator (theirs is a plain product because their
  nonlinearity is 1-Lipschitz; a GRU needs the gate terms above). Directly comparable
  in magnitude to their reported 3.73 (best) to 28.38 (worst).
* ``bound_dlogits`` — an upper bound on the L2 change in the policy's 6 action logits
  caused by moving the modulator between ANY two reachable states, with the
  observation and the task RNN's carry held fixed.
* ``bound_dvalue`` — the same for the critic's scalar value output.

Not a claim about behaviour. A bound on logits is not a bound on survival steps.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

__all__ = [
    "sigma_max", "column_l1", "expand_groups", "head_stats",
    "gru_input_lipschitz", "layernorm_activation_bounds",
    "site_bounds", "checkpoint_bounds",
]


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------

def sigma_max(matrix: np.ndarray) -> float:
    """Largest singular value (the matrix's operator norm on Euclidean vectors)."""
    m = np.asarray(matrix, dtype=np.float64)
    if m.ndim != 2:
        raise ValueError(f"sigma_max expects a 2-D matrix, got shape {m.shape}")
    return float(np.linalg.norm(m, ord=2))


def column_l1(kernel: np.ndarray) -> np.ndarray:
    """Per-output-unit sum of absolute input weights: ``||K[:, i]||_1`` for each i.

    With the modulator state confined to `[-1, 1]^m` (assumption A1), this is exactly
    the largest value the contextual part of that unit's signal can take.
    """
    k = np.asarray(kernel, dtype=np.float64)
    if k.ndim != 2:
        raise ValueError(f"column_l1 expects a 2-D kernel, got shape {k.shape}")
    return np.abs(k).sum(axis=0)


def expand_groups(per_group: np.ndarray, grouping_size: int, target_width: int) -> np.ndarray:
    """Repeat a per-group quantity out to per-unit, mirroring the model's own repeat.

    `NeuromodulatorRNN._get_signal` does ``jnp.repeat(raw, G, axis=-1)[..., :H]``, so
    unit `i` is driven by group `i // G`. Reproduced here so that a run with
    `grouping_size > 1` is scored on the units it actually has.
    """
    v = np.asarray(per_group, dtype=np.float64)
    if grouping_size < 1:
        raise ValueError(f"grouping_size must be >= 1, got {grouping_size}")
    out = np.repeat(v, grouping_size)[:target_width]
    if out.shape[0] != target_width:
        raise ValueError(
            f"grouping expansion produced {out.shape[0]} units but the modulated "
            f"layer is {target_width} wide — the head has {v.shape[0]} groups, which "
            f"cannot cover it at grouping_size={grouping_size}."
        )
    return out


def head_stats(kernel: np.ndarray, bias: np.ndarray, baseline: np.ndarray,
               grouping_size: int, target_width: int) -> dict[str, float]:
    """Reachable swing and constant part of one FiLM head, per assumptions A1-A4."""
    swing = 2.0 * expand_groups(column_l1(kernel), grouping_size, target_width)
    const = expand_groups(np.asarray(bias, dtype=np.float64), grouping_size,
                          target_width) + np.asarray(baseline, dtype=np.float64)
    return {
        "swing_max": float(swing.max()),
        "swing_mean": float(swing.mean()),
        "swing_min": float(swing.min()),
        "const_mean": float(const.mean()),
        "const_min": float(const.min()),
        "const_max": float(const.max()),
        "sigma_head": sigma_max(kernel),
        # L2 ceiling on the whole 128-vector's contextual deviation; the smaller of
        # the spectral route (A4) and the per-unit route (A3).
        "dev_l2_max": float(min(
            2.0 * math.sqrt(kernel.shape[0]) * sigma_max(kernel),
            math.sqrt(target_width) * swing.max(),
        )),
        "dev_linf_max": float(swing.max()),
    }


def gru_input_lipschitz(dense_i_kernel: np.ndarray,
                        dense_h_kernel: np.ndarray) -> float:
    """Bound on ``||d h_new / d input||_2`` for a Flax GRU cell, carry held fixed (A7).

    Flax packs the three gates (reset `r`, update `z`, candidate `n`) into one dense
    layer, in that order, so the kernel columns split into thirds.
    """
    wi = np.asarray(dense_i_kernel, dtype=np.float64)
    wh = np.asarray(dense_h_kernel, dtype=np.float64)
    if wi.shape[1] % 3 or wh.shape[1] % 3:
        raise ValueError(
            f"GRU dense kernels must have 3*hidden columns (r, z, n); got "
            f"dense_i {wi.shape} and dense_h {wh.shape}.")
    hsz = wi.shape[1] // 3
    w_ir, w_iz, w_in = wi[:, :hsz], wi[:, hsz:2 * hsz], wi[:, 2 * hsz:]
    w_hn = wh[:, 2 * hsz:]
    # |hh_n| <= max column-1-norm of W_hn, because the carry lies in [-1, 1]^hidden.
    m_n = float(np.abs(w_hn).sum(axis=0).max())
    return (0.5 * sigma_max(w_iz)
            + sigma_max(w_in)
            + 0.25 * m_n * sigma_max(w_ir))


def layernorm_activation_bounds(scale: np.ndarray, bias: np.ndarray) -> tuple[float, float]:
    """`(||a||_2, ||a||_inf)` ceilings for a LayerNorm output with learned affine (A5).

    LayerNorm's pre-affine output has exactly zero mean and unit variance across the
    `H` features, so its Euclidean norm is `sqrt(H)` and no single component can
    exceed `sqrt(H - 1)`.
    """
    s = np.asarray(scale, dtype=np.float64)
    c = np.asarray(bias, dtype=np.float64)
    h = s.shape[0]
    l2 = float(np.abs(s).max() * math.sqrt(h) + np.linalg.norm(c))
    linf = float(np.abs(s).max() * math.sqrt(h - 1) + np.abs(c).max())
    return l2, linf


def _linear_activation_bounds(kernel: np.ndarray, bias: np.ndarray,
                              in_linf: float, in_l2: float) -> tuple[float, float]:
    """`(||a||_2, ||a||_inf)` for `a = K' x + b` given ceilings on `x` (A5)."""
    k = np.asarray(kernel, dtype=np.float64)
    b = np.asarray(bias, dtype=np.float64)
    l2 = float(sigma_max(k) * in_l2 + np.linalg.norm(b))
    linf = float(np.abs(k).sum(axis=0).max() * in_linf + np.abs(b).max())
    return l2, linf


def _film_output_deviation(gamma: dict[str, float], beta: dict[str, float],
                           act_l2: float, act_linf: float) -> float:
    """Ceiling on `||Delta u||_2` for `u = gamma * a + beta` (A3-A5)."""
    gain_term = min(gamma["dev_linf_max"] * act_l2,
                    gamma["dev_l2_max"] * act_linf)
    return float(gain_term + beta["dev_l2_max"])


# --------------------------------------------------------------------------
# Site-level assembly
# --------------------------------------------------------------------------

_SITE_HEADS = {
    # site      -> (gamma head, beta head, gamma baseline, beta baseline)
    "encoder_unimodal":  ("head_unimodal", "head_unimodal_add",
                          "z_unimodal_baseline", "z_unimodal_add_baseline"),
    "encoder_multimodal": ("head_multimodal", "head_multimodal_add",
                           "z_hidden_baseline", "z_hidden_add_baseline"),
    "rnn":    ("head_rnn", "head_rnn_add", "z_rnn_baseline", "z_rnn_add_baseline"),
    "actor":  ("head_actor", "head_actor_add", "z_actor_baseline", "z_actor_add_baseline"),
    "critic": ("head_critic", "head_critic_add", "z_critic_baseline", "z_critic_add_baseline"),
}


def site_bounds(params: dict[str, Any], site: str, grouping_size: int,
                hidden_size: int) -> dict[str, float]:
    """All method-1 numbers for one modulation site of one checkpoint.

    Args:
        params: the ``model`` subtree from :func:`ckpt_io.load_params`.
        site: one of the keys of ``_SITE_HEADS``.
        grouping_size: the run's ``modulation.grouping_size``.
        hidden_size: the run's ``agent.hidden_size`` (width of every modulated layer).

    Returns:
        Flat dict of scalars, prefixed ``gamma_`` / ``beta_`` for the head statistics
        plus the derived Lipschitz and output-change bounds.
    """
    if site not in _SITE_HEADS:
        raise ValueError(f"unknown site {site!r}; expected one of {sorted(_SITE_HEADS)}")
    mod = params["modulator"]
    g_head, b_head, g_base, b_base = _SITE_HEADS[site]
    if g_head not in mod:
        raise ValueError(
            f"checkpoint has no head {g_head!r} — site {site!r} was not enabled in "
            f"this run. Callers must consult the run's saved config before asking.")

    gamma = head_stats(mod[g_head]["kernel"], mod[g_head]["bias"],
                       mod[g_base], grouping_size, hidden_size)
    beta = head_stats(mod[b_head]["kernel"], mod[b_head]["bias"],
                      mod[b_base], grouping_size, hidden_size)

    l_mod = gru_input_lipschitz(mod["gru"]["dense_i"]["kernel"],
                                mod["gru"]["dense_h"]["kernel"])

    out: dict[str, float] = {"site": site, "modulator_gru_lipschitz": l_mod}
    for name, st in (("gamma", gamma), ("beta", beta)):
        for k, v in st.items():
            out[f"{name}_{k}"] = v
        out[f"lipschitz_{name}"] = l_mod * st["sigma_head"]

    # --- pre-FiLM activation ceilings, and the downstream operator norms ---
    task_gru_linf, task_gru_l2 = 1.0, math.sqrt(hidden_size)
    sig_a1 = sigma_max(params["actor_fc1"]["kernel"])
    sig_a2 = sigma_max(params["actor_fc2"]["kernel"])
    sig_c1 = sigma_max(params["critic_fc1"]["kernel"])
    sig_c2 = sigma_max(params["critic_fc2"]["kernel"])

    if site == "actor":
        a_l2, a_linf = _linear_activation_bounds(
            params["actor_fc1"]["kernel"], params["actor_fc1"]["bias"],
            task_gru_linf, task_gru_l2)
        du = _film_output_deviation(gamma, beta, a_l2, a_linf)
        out.update(pre_film_act_l2=a_l2, film_output_deviation=du,
                   bound_dlogits=sig_a2 * du, bound_dvalue=float("nan"),
                   bound_tightness="tight (one linear layer downstream)")

    elif site == "critic":
        a_l2, a_linf = _linear_activation_bounds(
            params["critic_fc1"]["kernel"], params["critic_fc1"]["bias"],
            task_gru_linf, task_gru_l2)
        du = _film_output_deviation(gamma, beta, a_l2, a_linf)
        out.update(pre_film_act_l2=a_l2, film_output_deviation=du,
                   bound_dlogits=float("nan"), bound_dvalue=sig_c2 * du,
                   bound_tightness="tight (one linear layer downstream)")

    elif site == "rnn":
        # FiLM is applied to the task GRU's emitted output itself.
        du = _film_output_deviation(gamma, beta, task_gru_l2, task_gru_linf)
        out.update(pre_film_act_l2=task_gru_l2, film_output_deviation=du,
                   bound_dlogits=sig_a1 * sig_a2 * du,
                   bound_dvalue=sig_c1 * sig_c2 * du,
                   bound_tightness="moderate (two linear layers downstream)")

    elif site == "encoder_multimodal":
        if "mod_multimodal_ln" not in params:
            raise ValueError(
                "encoder bound requires the LayerNorm that sits before the FiLM "
                "(agent.use_layer_norm: true). Without it the encoder's pre-FiLM "
                "activation has no weights-only ceiling and this bound is not "
                "derivable — refusing to emit a number.")
        a_l2, a_linf = layernorm_activation_bounds(
            params["mod_multimodal_ln"]["scale"], params["mod_multimodal_ln"]["bias"])
        du = _film_output_deviation(gamma, beta, a_l2, a_linf)
        l_task = gru_input_lipschitz(params["rnn_cell"]["dense_i"]["kernel"],
                                     params["rnn_cell"]["dense_h"]["kernel"])
        out.update(pre_film_act_l2=a_l2, film_output_deviation=du,
                   task_gru_lipschitz=l_task,
                   bound_dlogits=l_task * sig_a1 * sig_a2 * du,
                   bound_dvalue=l_task * sig_c1 * sig_c2 * du,
                   bound_tightness=("loose (crosses the recurrent cell; the GRU "
                                    "factor is a single-step, carry-fixed bound)"))

    elif site == "encoder_unimodal":
        if "mod_unimodal_ln" not in params:
            raise ValueError(
                "encoder bound requires agent.use_layer_norm: true (see the "
                "encoder_multimodal branch).")
        a_l2, a_linf = layernorm_activation_bounds(
            params["mod_unimodal_ln"]["scale"], params["mod_unimodal_ln"]["bias"])
        du = _film_output_deviation(gamma, beta, a_l2, a_linf)
        # Deliberately NOT propagated to the policy output: the multimodal hub's own
        # LayerNorm sits between this site and the next one, and a LayerNorm's local
        # Lipschitz constant is 1/(input standard deviation) -- unbounded in the
        # weights alone. Reporting a fabricated number here would be dishonest.
        out.update(pre_film_act_l2=a_l2, film_output_deviation=du,
                   bound_dlogits=float("nan"), bound_dvalue=float("nan"),
                   bound_tightness=("not propagated: a LayerNorm downstream has no "
                                    "weights-only Lipschitz constant"))
    return out


def enabled_sites(agent_cfg: dict) -> list[str]:
    """Which site keys a run's saved agent config switches on."""
    mod = (agent_cfg or {}).get("modulation") or {}
    if mod.get("type") is None:
        return []
    sites = mod.get("sites") or {}
    out: list[str] = []
    if sites.get("encoder"):
        out += ["encoder_unimodal", "encoder_multimodal"]
    if sites.get("rnn"):
        if mod.get("rnn_mechanism") != "activation":
            raise ValueError(
                f"rnn site uses mechanism {mod.get('rnn_mechanism')!r}; this module "
                f"only derives bounds for the FiLM ('activation') mechanism.")
        out.append("rnn")
    if sites.get("actor"):
        out.append("actor")
    if sites.get("critic"):
        out.append("critic")
    return out


def checkpoint_bounds(params: dict[str, Any], agent_cfg: dict) -> list[dict[str, Any]]:
    """One row per enabled site for a single checkpoint."""
    mod_cfg = (agent_cfg or {}).get("modulation") or {}
    if mod_cfg.get("type") not in (None, "FiLM"):
        raise ValueError(
            f"modulation.type is {mod_cfg['type']!r}; the derivation in this module "
            f"assumes the linear FiLM operator (gain applied without a sigmoid).")
    grouping = int(mod_cfg.get("grouping_size", 1))
    hidden = int(agent_cfg["hidden_size"])
    return [site_bounds(params, s, grouping, hidden) for s in enabled_sites(agent_cfg)]
