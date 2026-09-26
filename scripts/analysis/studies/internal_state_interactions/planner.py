"""An ideal planner over a reduced level-05 world: what is the best thing to do in every body state?

Plain-language purpose: for a given set of body rules (bodysim.Body) and a reduced map, compute by
value iteration (dynamic programming: the best long-run return from every state, updated until it
stops changing) the best next choice for every combination of food energy, injury, body temperature
and place, then summarise per world (see `summarise`).

The reduced world -- every number measured, see measure_world.py / world_measurements.json:
  O  open ground, cell -30     B  bush in the cold, cell -30     W  bush on a fire ring, cell +8.8
  R  open fire ring, cell +8.8 F  a food item, cell -30
  * going to a place takes `trip[place]` steps (median measured trip 2) on cold ground; the last
    step is taken in the destination cell, as in the environment (post-move cell)
  * predators: every step NOT in a bush adds `hazard` expected injury (0.64 measured from Wave 2
    level-05 training recordings; 0.0 inside a bush, which animals cannot enter) -- an expected
    value, so the planner sees the average cost of exposure, not single attacks
  * a bush on a fire ring exists in 41 % of episodes; each world is solved with and without one and
    summaries pool the two maps with weights 0.59 / 0.41
  * food items allow 12 bites before moving; the planner's food never runs out (stated limitation:
    it makes eating look cheaper than it is)
Discount 0.95: the level-05 training runs' own `agent.gamma` (read from their saved configs).
Reward = the environment's: decrease in drive, -100 on death (bodysim.step).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import bodysim as B

PLACES = ["O", "B", "W", "R", "F"]
CELL = {"O": -30.0, "B": -30.0, "W": 8.8, "R": 8.8, "F": -30.0}
IN_BUSH = {"O": False, "B": True, "W": True, "R": False, "F": False}
TRAVEL_CELL = -30.0
WARM_BUSH_SHARE = 0.41
# choice categories used by the reading rule (merged) and for display
CATEGORY = {"go_B": "rest in cover", "rest_B": "rest in cover", "idle_B": "rest in cover",
            "go_W": "rest in cover", "rest_W": "rest in cover", "idle_W": "rest in cover",
            "go_R": "warm up", "rest_R": "warm up", "idle_R": "warm up",
            "go_F": "eat", "eat_F": "eat", "idle_F": "stay in the open", "rest_F": "stay in the open",
            "go_O": "stay in the open", "rest_O": "stay in the open", "idle_O": "stay in the open"}
CATEGORIES = ["rest in cover", "warm up", "eat", "stay in the open"]


@dataclass
class World:
    body: B.Body = field(default_factory=B.Body)
    trip: dict = field(default_factory=lambda: {"O": 2, "B": 2, "W": 2, "R": 2, "F": 2})
    warm_bush: bool = True
    hazard: float = 0.64
    gamma: float = 0.95
    grid: tuple = (51, 26, 61)                 # food, injury, temperature grid points


def grids(world):
    n, i, t = world.grid
    return np.linspace(0, 200, n), np.linspace(0, 100, i), np.linspace(-15, 15, t)


def _interp_setup(N, I, T, G):
    GN, GI, GT = G
    def axis(x, g):
        x = np.clip(x, g[0], g[-1]); h = g[1] - g[0]
        j = np.minimum(((x - g[0]) / h).astype(int), len(g) - 2)
        return j, (x - g[j]) / h
    (jn, wn), (ji, wi), (jt, wt) = axis(N, GN), axis(I, GI), axis(T, GT)
    idx, wts = [], []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                idx.append(((jn + a) * len(GI) + (ji + b)) * len(GT) + (jt + c))
                wts.append((wn if a else 1 - wn) * (wi if b else 1 - wi) * (wt if c else 1 - wt))
    return np.stack(idx), np.stack(wts)


def one_step(world, N, I, T, what, cell, bush):
    """One environment step (bodysim) plus the expected predator hazard outside cover."""
    P = world.body
    s = B.step(N, I, T, rested=(what == "rest"), ate=(what == "eat"), in_bush=bush, cell_temp=cell, P=P)
    I2, dead, r = s["I"], s["dead"], s["reward"]
    if world.hazard and not bush:
        I3 = np.minimum(I2 + world.hazard, P.max_injury)
        newly = (~dead) & (I3 >= P.max_injury)
        # the hazard's injury changes the drive this step too, and an injury death costs the penalty
        r = r + (B.drive(s["N"], I2, s["T"], P) - B.drive(s["N"], I3, s["T"], P)) - np.where(newly, P.death_penalty, 0.0)
        dead = dead | newly; I2 = I3
    return s["N"], I2, s["T"], r, dead


def macro(world, N, I, T, kind, place):
    """Apply one macro action; returns next state, summed discounted reward, death, continuation
    discount and the number of environment steps it took."""
    if kind == "go":
        n = world.trip[place]
        steps = [("move", TRAVEL_CELL, False)] * (n - 1) + [("move", CELL[place], False)]
    else:
        steps = [(kind, CELL[place], IN_BUSH[place])]
    R = np.zeros_like(N); disc = np.ones_like(N); dead = np.zeros(N.shape, bool)
    for what, cell, bush in steps:
        N2, I2, T2, r, d = one_step(world, N, I, T, what, cell, bush)
        R = R + np.where(dead, 0.0, disc * r); dead = dead | d
        N, I, T = N2, I2, T2; disc = disc * world.gamma
    return N, I, T, R, dead, disc, len(steps)


def options(world, p):
    places = [q for q in PLACES if q != "W" or world.warm_bush]
    opts = [("idle", p), ("rest", p)] + ([("eat", p)] if p == "F" else [])
    return opts + [("go", q) for q in places if q != p]


def solve(world: World, iters: int = 5000, tol: float = 1e-4):
    GN, GI, GT = G = grids(world)
    NN, II, TT = np.meshgrid(GN, GI, GT, indexing="ij")
    N0, I0, T0 = NN.ravel(), II.ravel(), TT.ravel()
    places = [p for p in PLACES if p != "W" or world.warm_bush]
    pi = {p: k for k, p in enumerate(places)}
    trans = {}
    for p in places:
        for kind, q in options(world, p):
            N1, I1, T1, R, dead, disc, _ = macro(world, N0, I0, T0, kind, q)
            idx, wts = _interp_setup(N1, I1, T1, G)
            trans[(p, kind, q)] = (pi[q], idx, wts, R, dead, disc)
    V = np.zeros((len(places), N0.size))
    for it in range(iters):
        Vn = np.full_like(V, -np.inf)
        for (p, kind, q), (qi, idx, wts, R, dead, disc) in trans.items():
            Vn[pi[p]] = np.maximum(Vn[pi[p]], R + np.where(dead, 0.0, disc * (V[qi][idx] * wts).sum(0)))
        delta = np.abs(Vn - V).max(); V = Vn
        if delta < tol:
            break
    q_values = {}
    for p in places:
        names, vals = [], []
        for (pp, kind, q), (qi, idx, wts, R, dead, disc) in trans.items():
            if pp == p:
                names.append(f"{kind}_{q}"); vals.append(R + np.where(dead, 0.0, disc * (V[qi][idx] * wts).sum(0)))
        q_values[p] = (np.array(names), np.stack(vals))
    return dict(V=V, q=q_values, places=places, iters=it + 1, delta=float(delta), world=world)


def best_category(sol, place, margin):
    """Best choice category per state, and whether the best other category is within `margin`."""
    names, vals = sol["q"][place]
    cats = np.array([CATEGORY[n] for n in names])
    best_by_cat = np.stack([np.where((cats == c)[:, None], vals, -np.inf).max(0) for c in CATEGORIES])
    order = np.argsort(-best_by_cat, axis=0)
    top = order[0]; second = order[1]
    gap = best_by_cat[top, np.arange(top.size)] - best_by_cat[second, np.arange(top.size)]
    return np.array(CATEGORIES)[top], gap < margin


def rollout_survival(sol, n_starts=2000, max_steps=500, T_lo=-10.0, T_hi=5.0, seed=0):
    """Follow the ideal policy (nearest grid point) from random training-style start states at open
    ground; returns the share surviving `max_steps` environment steps and mean survival steps."""
    world = sol["world"]; GN, GI, GT = grids(world)
    rng = np.random.default_rng(seed)
    N = rng.uniform(0, 200, n_starts); I = rng.uniform(0, 100, n_starts); T = rng.uniform(T_lo, T_hi, n_starts)
    place = np.array(["O"] * n_starts, dtype=object); steps = np.zeros(n_starts); alive = np.ones(n_starts, bool)
    near = lambda x, g: np.clip(np.rint((x - g[0]) / (g[1] - g[0])).astype(int), 0, len(g) - 1)
    for _ in range(max_steps):
        if not alive.any() or (steps[alive] >= max_steps).all():
            break
        for p in sol["places"]:
            sel = np.flatnonzero(alive & (place == p) & (steps < max_steps))
            if sel.size == 0:
                continue
            names, vals = sol["q"][p]
            flat = (near(N[sel], GN) * len(GI) + near(I[sel], GI)) * len(GT) + near(T[sel], GT)
            choice = names[vals[:, flat].argmax(0)]
            for c in np.unique(choice):
                k = sel[choice == c]; kind, q = c.split("_")
                N2, I2, T2, _, dead, _, n = macro(world, N[k], I[k], T[k], kind, q)
                N[k], I[k], T[k] = N2, I2, T2
                steps[k] += n; alive[k] &= ~dead; place[k] = q
    steps = np.minimum(steps, max_steps)
    return float(alive.mean()), float(steps.mean())


def start_mask(world, T_lo=-10.0, T_hi=5.0):
    GN, GI, GT = grids(world)
    NN, II, TT = np.meshgrid(GN, GI, GT, indexing="ij")
    return ((TT >= T_lo - 1e-9) & (TT <= T_hi + 1e-9)).ravel(), NN.ravel(), II.ravel(), TT.ravel()


def summarise(sols, margin=0.5, T_lo=-10.0, T_hi=5.0):
    """Pool the two maps (no warm bush / warm bush, weights 0.59 / 0.41) over training start states.

    need balance        weighted share of states whose best category is each category
    tie share           share whose best and second-best categories are within `margin` return units
    single accuracy     per body variable: accuracy of "the most common best category at this value"
    pair accuracy       the same with two variables known
    combination gain    best pair accuracy - best single accuracy (the reading rule's measure)
    interaction share   1 - best single accuracy (reported; capped by the balance of categories)
    Ties are excluded from the accuracies.
    """
    cats, keep, w, X = [], [], [], {"food energy": [], "injury": [], "body temperature": []}
    for sol, weight in sols:
        mask, NN, II, TT = start_mask(sol["world"], T_lo, T_hi)
        c, tie = best_category(sol, "O", margin)
        cats.append(c[mask]); keep.append(~tie[mask]); w.append(np.full(mask.sum(), weight / mask.sum()))
        X["food energy"].append(NN[mask]); X["injury"].append(II[mask]); X["body temperature"].append(TT[mask])
    cats, keep, w = np.concatenate(cats), np.concatenate(keep), np.concatenate(w)
    X = {k: np.concatenate(v) for k, v in X.items()}
    w = w / w.sum()
    balance = {c: float(w[cats == c].sum()) for c in CATEGORIES}
    tie_share = float(w[~keep].sum())
    cw, cc = w[keep] / w[keep].sum(), cats[keep]

    def acc(keys):
        k = np.zeros(cc.size)
        for j, name in enumerate(keys):
            k = k * 1e4 + X[name][keep]
        total = 0.0
        for v in np.unique(k):
            sel = k == v
            total += max(cw[sel & (cc == c)].sum() for c in CATEGORIES)
        return total
    names = list(X)
    single = {n: acc([n]) for n in names}
    pair = {f"{a} + {b}": acc([a, b]) for i, a in enumerate(names) for b in names[i + 1:]}
    return dict(balance=balance, tie_share=tie_share, single_accuracy=single, pair_accuracy=pair,
                combination_gain=max(pair.values()) - max(single.values()),
                interaction_share=1.0 - max(single.values()),
                three_way_share=1.0 - max(pair.values()))
