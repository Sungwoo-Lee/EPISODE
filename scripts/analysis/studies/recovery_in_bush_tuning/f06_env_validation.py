#!/usr/bin/env python3
"""f06 - the only figure here that runs the real environment, and the check the rest depend on.

QUESTION IT ANSWERS. Every other figure on this page is algebra: a closed form for the recurrence
in `src/environment/core.py::update_body`, written out by hand in `recovery_math.py`. If that
transcription is wrong, four figures are confidently wrong together and nothing on the page would
show it. So this one drives the actual environment - a scripted always-Rest policy, once with the
agent standing on a concealing bush and once on bare ground - and plots the measured injury against
the analytic prediction. Agreement validates the algebra; DISAGREEMENT would mean the algebra is
wrong, and the page would have to say so rather than move the line.

THE WORLD IT BUILDS, and why each choice is load-bearing (the same recipe as
`tests/env/test_recovery_in_bush.py`, which is where it comes from):
  * entities stripped - a predator would move the agent off the cell under test and would deal
    damage, and `can_recover` is false on any step with net damage;
  * only the food resource kept - the ambush resource deals 15-45 damage on contact;
  * exactly one bush, pinned to a known cell, so "on the bush" is a cell and not a search;
  * injury starts near the top of the scale, because recovery is subtractive and clipped at 0: a
    healthy agent would heal nothing and the comparison would be between two zeros.

WHAT IS ALSO VALIDATED HERE, and is easy to miss: the REST BUDGET itself. The study's definition
says a resting agent can afford `nutrition / metabolic_cost` rest steps because it eats nothing
while resting. That is a claim about the environment, not about arithmetic, so the run measures the
per-step nutrition change and the data statement reports it.

KNOWN LIMITATION. Two rollouts of one setting. This validates the recurrence's SHAPE and its
location premium; it does not sweep base, accel or multiplier through the environment, and a bug
that only appears at some other value of `recovery_accel_rate` would not be caught here.
"""
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import copy
import json

import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

sys.path.insert(0, R.ROOT)
import jax                     # noqa: E402
import jax.numpy as jnp        # noqa: E402
from src.utils.config import Config                    # noqa: E402
from src.environment.config_loader import load_env_params  # noqa: E402
from src.environment.core import jax_reset, jax_step   # noqa: E402

STEM = "f06_env_validation"
REST = 4                    # jax_step: rested = rest_action_enabled AND action == 4
N_STEPS = 50
START_INJURY = 95.0         # below max_injury, so step 1 cannot trip the injury-death test
SEED = 0


def _world(base, accel, mult):
    with open(R.DEFAULT_YAML) as fh:
        d = yaml.safe_load(fh)
    env = d["environment"]
    env["entities"] = []
    env["resources"] = [r for r in env["resources"] if r.get("type") == "food"]
    bush = copy.deepcopy([o for o in env["obstacles"] if o.get("hides_agent")][0])
    bush["count_low"] = bush["count_high"] = 1
    bush.pop("count", None)
    bush["area"] = [[3, 3], [3, 3]]
    env["obstacles"] = [bush]
    d["body"]["random_start_injury"] = True
    d["body"]["start_injury_low"] = d["body"]["start_injury_high"] = START_INJURY
    d["body"]["recovery_base_rate"] = base
    d["body"]["recovery_accel_rate"] = accel
    d["body"]["recovery_in_bush_multiplier"] = mult
    return d


def _off_bush_cell(state):
    taken = {tuple(p) for p in np.array(state.obs_pos)}
    for r in range(1, 9):
        for c in range(1, 9):
            if (r, c) not in taken:
                return jnp.array([r, c], dtype=state.agent_pos.dtype)
    raise AssertionError("no obstacle-free cell found - the world builder is wrong")


def _rollout(params, start_state, in_bush_expected):
    """Rest for N_STEPS and return the per-step record. Refuses to return a contaminated rollout."""
    state = start_state
    inj = [float(state.injury_level)]
    nut = [float(state.nutrition)]
    step = jax.jit(jax_step)
    for t in range(1, N_STEPS + 1):
        state, _, _, info = step(state, REST, params)
        if not bool(info["rested"]):
            raise ValueError(f"step {t}: the agent did not rest - action {REST} is not Rest here")
        if float(info["damage"]) != 0.0:
            raise ValueError(
                f"step {t}: the agent took {float(info['damage'])} damage. Recovery is suppressed "
                f"on a damaged step, so this rollout cannot validate the recovery arithmetic")
        if bool(info["agent_in_bush"]) != in_bush_expected:
            raise ValueError(
                f"step {t}: agent_in_bush is {bool(info['agent_in_bush'])}, expected "
                f"{in_bush_expected} - the agent is not where this rollout thinks it is")
        if int(state.rest_streak) != t:
            raise ValueError(f"step {t}: rest_streak is {int(state.rest_streak)}, expected {t}")
        inj.append(float(state.injury_level))
        nut.append(float(state.nutrition))
    return np.array(inj), np.array(nut)


def main():
    house.apply()
    rec = R.recommend()
    params = load_env_params(Config(_world(rec["base"], rec["accel"], rec["mult"])))
    state = jax_reset(params, jax.random.PRNGKey(SEED))
    if not (bool(params.obs_hides_agent[0]) and bool(state.obs_active[0])):
        raise ValueError("the pinned bush is not a concealing, active obstacle")

    bush_cell = state.obs_pos[0]
    inj_bush, nut_bush = _rollout(params, state.replace(agent_pos=bush_cell), True)
    inj_open, nut_open = _rollout(params, state.replace(agent_pos=_off_bush_cell(state)), False)

    n = np.arange(0, N_STEPS + 1)
    i0 = float(state.injury_level)
    pred_open = np.clip(i0 - R.cumulative(n, rec["base"], rec["accel"], 1.0), 0.0, R.MAX_INJURY)
    pred_bush = np.clip(i0 - R.cumulative(n, rec["base"], rec["accel"], rec["mult"]),
                        0.0, R.MAX_INJURY)

    res_open = np.abs(inj_open - pred_open)
    res_bush = np.abs(inj_bush - pred_bush)
    worst = float(max(res_open.max(), res_bush.max()))

    # The per-step nutrition drop, measured rather than assumed - the rest budget depends on it.
    dn_open = np.diff(nut_open)
    dn_bush = np.diff(nut_bush)
    nut_drop = float(np.mean(np.concatenate([-dn_open, -dn_bush])))
    nut_worst = float(np.max(np.abs(np.concatenate([-dn_open, -dn_bush]) - R.METABOLIC_COST)))

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.8),
                             gridspec_kw={"width_ratios": [1.35, 1.0]})
    ax = axes[0]
    ax.plot(n, pred_open, color=K.C_REC, linestyle=K.OPEN_STYLE, linewidth=2.0,
            label="predicted by the closed form, in the open")
    ax.plot(n, pred_bush, color=K.C_REC, linestyle=K.BUSH_STYLE, linewidth=2.0,
            label="predicted by the closed form, on a bush")
    ax.plot(n[::3], inj_open[::3], linestyle="none", marker="o", markersize=6,
            markerfacecolor="none", markeredgecolor=house.INK, markeredgewidth=1.3,
            label="measured in the environment, in the open")
    ax.plot(n[::3], inj_bush[::3], linestyle="none", marker="s", markersize=5.5,
            markerfacecolor=house.INK, markeredgecolor=house.INK,
            label="measured in the environment, on a bush")
    ax.set_xlabel("rest steps taken (whole environment steps)")
    ax.set_ylabel("injury level\n(points of the 0-100 scale)")
    ax.set_xlim(0, N_STEPS)
    ax.set_ylim(-3, 100)
    ax.set_yticks([0, 25, 50, 75, 95])
    ax.set_title("(a) measured against predicted")

    ax2 = axes[1]
    floor = 1e-6
    ax2.plot(n, np.maximum(res_open, floor), color=K.C_REC, linestyle=K.OPEN_STYLE,
             marker="o", markersize=4, markerfacecolor="none", markeredgecolor=K.C_REC,
             label="in the open")
    ax2.plot(n, np.maximum(res_bush, floor), color=K.C_REC, linestyle=K.BUSH_STYLE,
             marker="s", markersize=3.5, label="on a bush")
    ax2.set_yscale("log")
    ax2.set_xlabel("rest steps taken (whole environment steps)")
    ax2.set_ylabel("|measured - predicted|\n(injury points, log scale)")
    ax2.set_xlim(0, N_STEPS)
    ax2.set_ylim(floor, 3.0)
    ax2.set_title("(b) the disagreement")
    # Short lines on purpose: at full width this note ran past the right edge of its own panel
    # (caught by house.assert_text_inside_axes, register F18 amendment).
    ax2.annotate(f"worst disagreement over both\nrollouts: {worst:.2e} injury points\n"
                 f"- about the float32 resolution\nnear injury {i0:g}, "
                 f"{np.spacing(np.float32(i0)):.1e}\n\n"
                 f"the bush residual is EXACTLY zero\nat every step; it is drawn on\n"
                 f"the {floor:.0e} floor of the log axis",
                 xy=(0.9, 1.6e0), fontsize=house.FS_LABEL, color=house.INK_2,
                 ha="left", va="top",
                 # A filled patch, not only a per-glyph halo. This panel is gridded, and a halo
                 # breaks a rule where a glyph is but leaves it running BETWEEN the glyphs - so the
                 # note still read as struck through. F33 says an annotation goes where there is no
                 # ink; a gridline is ink, so the annotation brings its own clear ground.
                 bbox=dict(boxstyle="square,pad=0.5", facecolor=house.PAPER, edgecolor="none"))

    # Both notes sit over a gridded panel, and a horizontal rule through a word loses it (F33 -
    # gridlines are ink too). Outline them in the page ground (F52).
    #
    # THIS LOOP AND ITS GUARD WERE HERE ONCE BEFORE AND WERE DELETED by a later edit of this file
    # that replaced a slice between two indices without re-reading what was inside it - which is
    # how this figure came to ship unhaloed and unguarded while the comment above its annotation
    # still named the guard. The guard now also runs from `house.save`, so losing this line again
    # cannot make the figure unsafe, only unhaloed.
    for _ax in (ax, ax2):
        for _t in _ax.texts:
            _t.set_path_effects(house.halo())
    house.assert_text_inside_axes([ax, ax2])

    house.legend_below(ax, ncol=1)
    house.legend_below(ax2, ncol=2)
    fig.subplots_adjust(bottom=0.36, left=0.09, top=0.90, right=0.99, wspace=0.30)
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Measured, not analytic: 2 rollouts of the real environment &times; {N_STEPS} rest steps "
        f"each &mdash; {2 * N_STEPS} of {2 * N_STEPS} recorded steps plotted (100%), plus the "
        f"t&nbsp;=&nbsp;0 initial state, which is not a step. One seed "
        f"(<code>PRNGKey({SEED})</code>), one world, one setting: base {rec['base']:g}, accel "
        f"{rec['accel']:g}, multiplier {rec['mult']:g}, starting injury {i0:g}. Every step was "
        f"checked before plotting for rest, zero damage, the expected bush membership and the "
        f"expected rest streak; a failure raises rather than draws. Worst disagreement between "
        f"measurement and closed form: <b>{worst:.2e} injury points</b> over all "
        f"{2 * (N_STEPS + 1)} compared values. Nutrition fell by {nut_drop:.4f} per rest step "
        f"against a <code>metabolic_cost</code> of {R.METABOLIC_COST:g} (worst per-step deviation "
        f"{nut_worst:.2e}), which is the rest-budget half of the definition, measured."))

    # The page quotes these; it reads them from here rather than having them typed into markup.
    results = dict(
        worst_residual=worst,
        worst_residual_open=float(res_open.max()),
        worst_residual_bush=float(res_bush.max()),
        float32_resolution=float(np.spacing(np.float32(i0))),
        n_compared=int(2 * (N_STEPS + 1)),
        n_steps=N_STEPS,
        seed=SEED,
        start_injury=i0,
        nutrition_drop_per_step=nut_drop,
        nutrition_drop_worst_deviation=nut_worst,
        final_injury_open=float(inj_open[-1]),
        final_injury_open_pred=float(pred_open[-1]),
        final_injury_bush=float(inj_bush[-1]),
        final_injury_bush_pred=float(pred_bush[-1]),
        steps_to_zero_bush=int(np.argmax(inj_bush <= 0.0)),
        base=rec["base"], accel=rec["accel"], mult=rec["mult"],
    )
    with open(os.path.join(K.OUT, f"{STEM}.results.json"), "w") as fh:
        json.dump(results, fh, indent=2, sort_keys=True)
    print(f"  wrote {K.OUT}/{STEM}.results.json")
    print(f"  worst |measured - predicted| = {worst:.3e} injury points")
    print(f"  nutrition drop per rest step = {nut_drop:.6f} (metabolic_cost {R.METABOLIC_COST})")
    print(f"  final injury: open {inj_open[-1]:.4f} (predicted {pred_open[-1]:.4f}), "
          f"bush {inj_bush[-1]:.4f} (predicted {pred_bush[-1]:.4f})")


if __name__ == "__main__":
    main()
