"""A numpy copy of the environment's body update, for agent-free simulation of internal states.

Plain-language purpose: the study "interactions between internal states" needs to run the body's
rules (food energy, injury, body temperature) millions of times across many settings without a
trained agent. This module is one step of `src/environment/core.py::update_body`, line for line,
vectorised over arrays of bodies, plus the five planned mechanics B1-B5 exactly as specified in
docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md (Revision 3). It is only trusted after
`validate.py` has matched it against the real `update_body` (today's rules now; B1-B5 once they
land) -- a mismatch blocks every figure.

Scope: no damage (the study has no predators), so the injury smoothing buffer is not modelled;
satiation equals nutrition (level 05: nutrition_to_satiation_scaling_factor 1, max 200 both);
recovery acceleration is 0 at level 05, so the rest streak does not change the healing rate.

Units and conventions follow core.py: pre-step body temperature and nutrition feed B2/B5/A1; the
nutrition order is decay -> A1 drain -> food -> B3 charge -> one clip; reward = drive(before) -
drive(after), minus the death penalty on a real death.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Body:
    # --- today's level-05 values (configs/environment/default.yaml + basic/05) ---
    max_nutrition: float = 200.0
    setpoint: float = 100.0            # satiation setpoint; satiation == nutrition at level 05
    metabolic_cost: float = 1.0
    food_gain_net: float = 5.0          # food_nutrition_gain 6 - eating_nutrition_cost 1
    overeating_death: bool = True
    max_injury: float = 100.0
    recovery_base: float = 0.2
    bush_multiplier: float = 25.0
    t_set: float = 0.0
    t_min: float = -15.0
    t_max: float = 15.0
    k_ex: float = 0.04
    k_loss: float = 0.02
    k_met: float = 0.0
    warm_scale: float = 2.0
    cool_scale: float = 0.25
    death_penalty: float = 100.0
    # --- A1 (existing key, off at level 05) ---
    coupling: bool = False
    coupling_rate: float = 1.0
    # --- B2 healing needs warmth ---
    heal_cold_s: float = 0.0
    heal_warm_s: float = 0.0
    # --- B3 healing uses food energy ---
    heal_cost: float = 0.0
    shortfall: str = "partial"          # partial | full
    # --- B4 injury speeds heat exchange ---
    inj_gain: float = 0.0
    inj_mode: str = "cooling_only"      # cooling_only | both
    # --- B5 healing speed depends on food energy ---
    b5: bool = False
    b5_low: float = 0.0
    b5_high: float = 100.0
    b5_floor: float = 0.0
    b5_over_floor: float = 1.0
    b5_over_start: float = 150.0

    def with_(self, **kw):
        return replace(self, **kw)


def drive(N, I, T, P: Body):
    """calculate_drive with thermal on: distance to (setpoint, 0, 0) with T scaled to satiation units."""
    rng = max(P.setpoint, P.max_nutrition - P.setpoint)          # satiation_deviation_range
    t_axis = (T - P.t_set) * (rng / P.t_max)
    return np.sqrt((N - P.setpoint) ** 2 + I ** 2 + t_axis ** 2)


def step(N, I, T, rested, ate, in_bush, cell_temp, P: Body):
    """One body update. All inputs broadcastable arrays. Returns dict of new N, I, T, death flags,
    reward and the healed amount. `rested`, `ate`, `in_bush` are booleans (the agent cannot rest
    and eat in one step; the caller enforces that)."""
    N = np.asarray(N, float); I = np.asarray(I, float); T = np.asarray(T, float)
    rested = np.asarray(rested, bool); ate = np.asarray(ate, bool); in_bush = np.asarray(in_bush, bool)
    cell_temp = np.asarray(cell_temp, float)

    # ---- nutrition: decay -> A1 drain -> food (charge and clip come after injury) ----
    Npre = N - P.metabolic_cost
    if P.coupling:
        Npre = Npre - P.coupling_rate * np.abs(P.k_loss * (T - P.t_set))
    Npre = np.where(ate, Npre + P.food_gain_net, Npre)

    # ---- injury recovery (no damage in this study => applied_inc == 0) ----
    r = np.full(np.broadcast(N, I, T, rested).shape, P.recovery_base)
    if P.bush_multiplier != 1.0:
        r = r * np.where(in_bush, P.bush_multiplier, 1.0)
    if P.heal_cold_s != 0.0 or P.heal_warm_s != 0.0:                      # B2 (pre-step T)
        w = 1.0 - P.heal_cold_s * np.maximum(0.0, P.t_set - T) - P.heal_warm_s * np.maximum(0.0, T - P.t_set)
        r = r * np.maximum(0.0, w)
    if P.b5:                                                               # B5 (pre-step N)
        fh = P.b5_floor + (1 - P.b5_floor) * np.clip((N - P.b5_low) / (P.b5_high - P.b5_low), 0, 1)
        fo = 1.0
        if P.b5_over_floor < 1.0:
            fo = 1.0 - (1 - P.b5_over_floor) * np.clip((N - P.b5_over_start) / (P.max_nutrition - P.b5_over_start), 0, 1)
        r = r * fh * fo
    h_nom = np.where(rested, np.minimum(r, I), 0.0)
    if P.heal_cost > 0.0:                                                  # B3
        if P.shortfall == "partial":
            h = np.minimum(h_nom, np.maximum(Npre, 0.0) / P.heal_cost)
        else:
            h = h_nom
        N_new = np.clip(Npre - P.heal_cost * h, 0.0, P.max_nutrition)
        starve = (np.clip(Npre, 0.0, P.max_nutrition) <= 0.0) if P.shortfall == "partial" else (N_new <= 0.0)
    else:
        h = h_nom
        N_new = np.clip(Npre, 0.0, P.max_nutrition)
        starve = N_new <= 0.0
    I_new = np.clip(I - h, 0.0, P.max_injury)
    overeat = (N_new >= P.max_nutrition) if P.overeating_death else np.zeros_like(starve)
    injury_death = I_new >= P.max_injury

    # ---- body temperature ----
    k_ex = P.k_ex
    if P.inj_gain != 0.0:                                                  # B4 (pre-step I)
        boost = P.k_ex * (1.0 + P.inj_gain * I / P.max_injury)
        k_ex = boost if P.inj_mode == "both" else np.where(cell_temp < T, boost, P.k_ex)
    d = k_ex * (cell_temp - T) + P.k_met - P.k_loss * (T - P.t_set)
    if P.warm_scale == 1.0 and P.cool_scale == 1.0:
        T_new = T + d
    else:
        T_new = T + np.where(d > 0.0, P.warm_scale, P.cool_scale) * d
    thermal_death = (T_new < P.t_min) | (T_new > P.t_max)

    dead = starve | overeat | injury_death | thermal_death
    reward = drive(N, I, T, P) - drive(N_new, I_new, T_new, P) - np.where(dead, P.death_penalty, 0.0)
    return dict(N=N_new, I=I_new, T=T_new, dead=dead, starve=starve, overeat=overeat,
                injury_death=injury_death, thermal_death=thermal_death, reward=reward, healed=h)
