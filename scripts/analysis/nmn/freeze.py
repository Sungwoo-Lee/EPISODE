"""Method 3 — hold the modulator's output at its per-unit time-mean, by editing weights.

Plain-language purpose
----------------------
The decisive question about the neuromodulator is whether its *moment-to-moment
variation* does any work, or whether it has settled into a fixed re-tuning the rest
of the network has already absorbed. The test, due to Perez et al. (2018 sec 4.3), is
to replay a trained agent with the modulation replaced by its own average and see
whether behaviour changes. Perez ran it separately on the gain and the offset and
found the effect wildly asymmetric — replacing the gain with its mean cost 65.4
accuracy points, the offset 1.0 — so freezing them together would have hidden the
result. This module therefore freezes them independently.

Why this is a weight edit and not a code change
-----------------------------------------------
The modulator's gain for unit `i` is, exactly (`neuromodulator.py::_get_signal`),

    gamma_i(h) = baseline_i + repeat(bias)_i + sum_j kernel_ji h_j

Three of those four terms are parameters and only the last depends on the modulator's
state `h`. So setting

    kernel := 0        bias := 0        baseline := target

makes the head emit exactly `target` at every timestep, for every input, forever —
and it does so **without touching a line of `src/`**. The task network's forward pass
is byte-identical; the modulator's GRU still runs and still updates its state, so any
head left un-edited keeps varying with context exactly as before. That is what makes
"freeze the gain but not the offset" a well-defined intervention rather than an
approximation.

The `baseline` parameter carries the target rather than the bias because the baseline
is per-unit (`target_hidden_size` wide) while the bias is per-*group*. With
`grouping_size > 1` a per-unit target cannot be expressed through the bias at all, so
routing it through the baseline is what makes the edit correct in general rather than
only for the `grouping_size = 1` runs we happen to have.

This equivalence is the load-bearing assumption of the whole method, so it is checked
three ways: a hand-computed unit test (`tests/analysis/test_nmn_freeze.py`), an
exhaustive check on a real trained modulator over random inputs
(`verify_freeze_equivalence` below, run before every sweep), and an assertion during
the sweep itself that the replayed frozen gain is constant to the last bit.

Interpreting a null
-------------------
An optimisation review of these runs established that the *time-averaged* gain and
offset are gauge quantities: they can be absorbed into the modulated layer's own
affine parameters with the network's function unchanged. Freezing at the mean is
therefore mathematically the same as deleting the modulator and folding its constant
part into the layer. So a null result here says **"the modulator's variation is
unused"** — a positive finding about what the modulation is. It does NOT say "the
modulator changed nothing during training", which is a different claim.
"""
from __future__ import annotations

import numpy as np

#: site -> (gain head, offset head, gain baseline, offset baseline), matching
#: `NeuromodulatorRNN`'s attribute names. Same table as `spectral_bound._SITE_HEADS`,
#: repeated rather than imported so that neither module can silently re-map the other.
SITE_PARAMS = {
    "encoder_unimodal":   ("head_unimodal", "head_unimodal_add",
                           "z_unimodal_baseline", "z_unimodal_add_baseline"),
    "encoder_multimodal": ("head_multimodal", "head_multimodal_add",
                           "z_hidden_baseline", "z_hidden_add_baseline"),
    "rnn":                ("head_rnn", "head_rnn_add",
                           "z_rnn_baseline", "z_rnn_add_baseline"),
    "actor":              ("head_actor", "head_actor_add",
                           "z_actor_baseline", "z_actor_add_baseline"),
    "critic":             ("head_critic", "head_critic_add",
                           "z_critic_baseline", "z_critic_add_baseline"),
}

CONDITIONS = ("live", "freeze_gain", "freeze_offset", "freeze_both")


def head_signal(kernel: np.ndarray, bias: np.ndarray, baseline: np.ndarray,
                h: np.ndarray, grouping_size: int, width: int) -> np.ndarray:
    """Reproduce `NeuromodulatorRNN._get_signal` for one head, in numpy.

    Exists so the freeze can be checked against an independent implementation of the
    thing it claims to hold constant, rather than against itself.

    Args:
        kernel: (mod_hidden, n_groups)      bias: (n_groups,)
        baseline: (width,)                  h: (..., mod_hidden)
    """
    raw = np.asarray(h) @ np.asarray(kernel) + np.asarray(bias)
    sig = np.repeat(raw, grouping_size, axis=-1)[..., :width]
    return sig + np.asarray(baseline)


def frozen_head_params(target: np.ndarray, kernel_shape: tuple[int, int],
                       bias_shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The (kernel, bias, baseline) that make a head emit `target` for every input.

    Returns zeros for the kernel and the bias, and `target` for the baseline — see
    the module docstring for why the target goes to the baseline and not the bias.

    **Dtype note.** The model's parameters are float32, so the returned baseline is
    the target rounded to float32 and the head then emits *that* value exactly, at
    every step, forever. The guarantee this method needs is "constant", which holds
    to the last bit; it is not "equal to a float64 mean", which no float32 parameter
    could deliver. Callers computing the target from float32 rollout data (which is
    all of them) see no rounding at all.
    """
    target = np.asarray(target)
    if target.ndim != 1:
        raise ValueError(f"the frozen target must be per-unit (1-D), got shape "
                         f"{target.shape}. A scalar mean is not what this method "
                         f"freezes at.")
    return (np.zeros(kernel_shape, dtype=np.float32),
            np.zeros(bias_shape, dtype=np.float32),
            target.astype(np.float32))


def per_unit_time_means(rollout_out: dict) -> dict[str, dict[str, np.ndarray]]:
    """Per-unit mean gain and offset over every timestep the agent was alive.

    The mask matters: episodes have different lengths, and pooling the padding after
    an agent died would freeze the modulator at an average that includes readings
    from a dead agent.
    """
    valid = rollout_out["valid"]
    out = {}
    for site in rollout_out["gamma"]:
        out[site] = {
            "gamma": rollout_out["gamma"][site][valid].mean(axis=0),
            "beta": rollout_out["beta"][site][valid].mean(axis=0),
        }
    return out


def apply_freeze(model, means: dict[str, dict[str, np.ndarray]],
                 *, freeze_gain: bool, freeze_offset: bool) -> list[str]:
    """Edit a live model's modulator in place so the named signals are constant.

    Returns the list of parameter paths edited, so the caller can record exactly
    what was touched rather than trusting that it was.
    """
    import jax.numpy as jnp

    if not (freeze_gain or freeze_offset):
        return []
    mod = model.modulator
    edited: list[str] = []
    for site, means_site in means.items():
        g_head, b_head, g_base, b_base = SITE_PARAMS[site]
        jobs = []
        if freeze_gain:
            jobs.append((g_head, g_base, means_site["gamma"]))
        if freeze_offset:
            jobs.append((b_head, b_base, means_site["beta"]))
        for head_name, base_name, target in jobs:
            head = getattr(mod, head_name)
            baseline = getattr(mod, base_name)
            k, b, base = frozen_head_params(
                target, tuple(head.kernel.value.shape), tuple(head.bias.value.shape))
            head.kernel.value = jnp.asarray(k)
            head.bias.value = jnp.asarray(b)
            baseline.value = jnp.asarray(base)
            edited += [f"{head_name}.kernel", f"{head_name}.bias", base_name]
    if not edited:
        raise ValueError("freeze requested but no site was edited — `means` was empty, "
                         "which means the rollout found no enabled sites.")
    return edited


def verify_freeze_equivalence(load_agent_fn, means, sites, *, n_probe: int = 512,
                              seed: int = 0) -> dict:
    """Prove the weight edit is exactly a constant, on a REAL trained modulator.

    The whole method rests on "zero the kernel, put the mean in the baseline" being
    an identity rather than an approximation, so it is checked against an independent
    numpy implementation of the head (`head_signal`) over random inputs, and against
    the unedited model for the signals that must NOT move.

    Three claims are checked, all required to hold to the last bit:

    1. the frozen gain equals the per-unit target for every one of `n_probe` random
       modulator states, at every unit;
    2. the offset — deliberately left live — is bit-identical to the unedited
       model's offset for the same inputs, so freezing one signal does not perturb
       the other;
    3. the modulator's own GRU state update is bit-identical, so the frozen model
       still tracks context in exactly the same way.

    Returns a dict of the measured maximum deviations (all expected to be 0.0).
    """
    import jax
    import jax.numpy as jnp

    ref = load_agent_fn()
    frozen = load_agent_fn()
    apply_freeze(frozen.model, means, freeze_gain=True, freeze_offset=False)

    mod_ref, mod_frz = ref.model.modulator, frozen.model.modulator
    key = jax.random.PRNGKey(seed)
    k1, k2 = jax.random.split(key)
    obs_dim = mod_ref.gru.dense_i.kernel.value.shape[0]
    m = mod_ref.mod_hidden_size
    # Probe states span the whole reachable cube, including the corners, so the check
    # is not confined to the region a rollout happens to visit.
    obs = jax.random.normal(k1, (n_probe, obs_dim)) * 3.0
    h = jax.random.uniform(k2, (n_probe, m), minval=-1.0, maxval=1.0)

    out_ref, h_ref = mod_ref(obs, h)
    out_frz, h_frz = mod_frz(obs, h)

    from scripts.analysis.nmn.replay import SITE_FIELDS
    report: dict = {"n_probe": int(n_probe)}
    worst = 0.0
    for site in sites:
        g_field, b_field = SITE_FIELDS[site]
        gamma_frz = np.asarray(getattr(out_frz, g_field))
        beta_frz = np.asarray(getattr(out_frz, b_field))
        beta_ref = np.asarray(getattr(out_ref, b_field))
        target = np.asarray(means[site]["gamma"])

        d_const = float(np.abs(gamma_frz - target[None, :]).max())
        d_beta = float(np.abs(beta_frz - beta_ref).max())
        # Independent numpy reconstruction of what the EDITED head should emit.
        head = getattr(mod_frz, SITE_PARAMS[site][0])
        base = getattr(mod_frz, SITE_PARAMS[site][2])
        recon = head_signal(np.asarray(head.kernel.value), np.asarray(head.bias.value),
                            np.asarray(base.value), np.asarray(h_frz),
                            mod_frz.grouping_size, mod_frz.target_hidden_size)
        d_recon = float(np.abs(gamma_frz - recon).max())
        report[site] = {"max_dev_from_target": d_const,
                        "max_dev_offset_vs_unedited": d_beta,
                        "max_dev_vs_numpy_reconstruction": d_recon}
        worst = max(worst, d_const, d_beta, d_recon)

    d_state = float(np.abs(np.asarray(h_frz) - np.asarray(h_ref)).max())
    report["max_dev_modulator_state"] = d_state
    worst = max(worst, d_state)
    report["worst_deviation"] = worst
    report["exact"] = bool(worst == 0.0)
    if not report["exact"]:
        raise AssertionError(
            "The freeze-by-weight-edit is NOT exactly a constant on this arm "
            f"(worst deviation {worst}). Every number method 3 would produce rests on "
            f"this identity, so the sweep must not proceed.\n{report}")
    return report


def paired_differences(live_lengths: np.ndarray, frozen_lengths: np.ndarray) -> dict:
    """Summarise the per-episode paired change in survival steps.

    Paired, because both conditions replayed the SAME episodes from the same seeds:
    the difference is taken within an episode, so the between-episode variance — which
    is enormous here, survival ranges from 1 step to the 500-step cap — cancels
    instead of drowning the effect. That is what makes the result readable with one
    training seed per configuration.

    Survival steps, never cumulative reward.
    """
    live = np.asarray(live_lengths, dtype=np.int64)
    frozen = np.asarray(frozen_lengths, dtype=np.int64)
    if live.shape != frozen.shape:
        raise ValueError(f"unpaired inputs: {live.shape} live vs {frozen.shape} frozen "
                         f"episodes. The comparison is only meaningful episode by "
                         f"episode.")
    d = frozen - live
    n = d.size
    n_changed = int((d != 0).sum())
    n_worse = int((d < 0).sum())
    n_better = int((d > 0).sum())
    out = {
        "n_episodes": int(n),
        "mean_live": float(live.mean()), "mean_frozen": float(frozen.mean()),
        "mean_diff": float(d.mean()), "median_diff": float(np.median(d)),
        "sd_diff": float(d.std(ddof=1)) if n > 1 else float("nan"),
        "min_diff": int(d.min()), "max_diff": int(d.max()),
        "q05_diff": float(np.quantile(d, 0.05)), "q95_diff": float(np.quantile(d, 0.95)),
        "frac_episodes_changed": n_changed / n,
        "frac_episodes_worse": n_worse / n, "frac_episodes_better": n_better / n,
        "n_changed": n_changed, "n_worse": n_worse, "n_better": n_better,
    }
    # Sign test over the episodes that changed at all: distribution-free, makes no
    # assumption about the shape of the difference distribution, and is the right
    # test when the quantity is a paired count with many exact ties.
    if n_changed:
        from scipy import stats
        out["sign_test_p"] = float(
            stats.binomtest(n_better, n_changed, 0.5).pvalue)
    else:
        out["sign_test_p"] = float("nan")
    return out
