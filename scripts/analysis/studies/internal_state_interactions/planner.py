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
  * predators: every step NOT in a bush adds expected injury -- `hazard_rest` on a resting step
    (0.12 measured), `hazard_move` on any other step (0.70), 0.0 inside a bush (animals cannot
    enter); measured from Wave 2 level-05 training recordings. An expected value (mean-field): the
    planner sees the average cost of exposure, not single ~21-point attacks, so it under-counts
    single-hit deaths at high injury; and agents choose where they rest, so the resting rate is
    partly a selection effect
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
    hazard_rest: float = 0.12
    hazard_move: float = 0.70
    gamma: float = 0.95
    grid: tuple = (51, 26, 61)                 # food, injury, temperature grid points
    # ---- Revision 2 (balance study); the defaults reproduce Revision 1 exactly ----
    e1: bool = False                           # E1: after each bite the item moves with prob 1/bites_per_item
    bites_per_item: float = 12.0               #     (agent is then back at open ground)
    e2: str = "mean"                           # E2: "mean" = mean-field hazard; "bins" = hits drawn from hazard_bins
    hazard_eat: float | None = None            # mean mode: eating-step hazard (None -> hazard_move, Revision 1)
    hazard_bins: dict | None = None            # bins mode: {"eat"|"move"|"rest": (p_hit, [bin probs], [bin sizes])}
    hazard_scale: float = 1.0                  # diagnostic: hit probability (bins) / mean (mean) times this
    # ---- context-exploration study (Part 3); None reproduces everything above exactly ----
    find_prob: dict | None = None              # {place: p}: "go" to that place is a one-step search that
                                               #   arrives with prob p (last step in the place's cell) or
                                               #   leaves the agent on open ground (a travel step); mean
                                               #   search time 1/p steps (geometric)


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


def activity(what):
    """E2 activity class of a step: eating, resting, or moving (moves and staying in place)."""
    return "rest" if what == "rest" else "eat" if what == "eat" else "move"


def mean_hazard(world, what):
    """Mean-field hazard of one step outside cover (Revision 1 when hazard_eat is None)."""
    hz = world.hazard_rest if what == "rest" else (
        world.hazard_eat if (what == "eat" and world.hazard_eat is not None) else world.hazard_move)
    return hz * world.hazard_scale if world.hazard_scale != 1.0 else hz


def hazard_dist(world, what, bush):
    """Outcomes of one step's hazard as [(probability, injury added)], sizes 0 = no hit.
    mean mode: one certain outcome of the mean; bins mode: no hit, or a hit of each bin's measured
    mean size (the >= 100 bin kills at any injury, since injury is clipped at 100)."""
    if bush:
        return [(1.0, 0.0)]
    if world.e2 == "mean":
        return [(1.0, mean_hazard(world, what))]
    p_hit, probs, sizes = world.hazard_bins[activity(what)]
    p = min(1.0, p_hit * world.hazard_scale)
    return [(1.0 - p, 0.0)] + [(p * q, float(x)) for q, x in zip(probs, sizes) if q > 0]


def apply_hit(P, s, x):
    """Add a hit of size x (scalar or array) to a bodysim step result; same arithmetic as Revision 1."""
    I2, dead, r = s["I"], s["dead"], s["reward"]
    I3 = np.minimum(I2 + x, P.max_injury)
    newly = (~dead) & (I3 >= P.max_injury)
    r = r + (B.drive(s["N"], I2, s["T"], P) - B.drive(s["N"], I3, s["T"], P)) - np.where(newly, P.death_penalty, 0.0)
    return s["N"], I3, s["T"], r, dead | newly, newly


def one_step(world, N, I, T, what, cell, bush):
    """One environment step (bodysim) plus the expected predator hazard outside cover."""
    P = world.body
    s = B.step(N, I, T, rested=(what == "rest"), ate=(what == "eat"), in_bush=bush, cell_temp=cell, P=P)
    I2, dead, r = s["I"], s["dead"], s["reward"]
    hz = mean_hazard(world, what)
    if hz and not bush:
        I3 = np.minimum(I2 + hz, P.max_injury)
        newly = (~dead) & (I3 >= P.max_injury)
        # the hazard's injury changes the drive this step too, and an injury death costs the penalty
        r = r + (B.drive(s["N"], I2, s["T"], P) - B.drive(s["N"], I3, s["T"], P)) - np.where(newly, P.death_penalty, 0.0)
        dead = dead | newly; I2 = I3
    return s["N"], I2, s["T"], r, dead


def macro_steps(world, kind, place):
    """The environment steps of a macro action as (what, cell temperature, in bush)."""
    if kind == "go":
        n = world.trip[place]
        # the last step lands in the destination cell; arriving in a bush is already cover
        return [("move", TRAVEL_CELL, False)] * (n - 1) + [("move", CELL[place], IN_BUSH[place])]
    return [(kind, CELL[place], IN_BUSH[place])]


def macro(world, N, I, T, kind, place):
    """Apply one macro action; returns next state, summed discounted reward, death, continuation
    discount and the number of environment steps it took."""
    steps = macro_steps(world, kind, place)
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
    """Revision-1 (deterministic) solver when E1 and E2 are off; the stochastic solver otherwise."""
    if world.e1 or world.e2 != "mean" or world.find_prob:
        return solve_stochastic(world, iters, tol)
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


def summarise_map(sol, margin=0.5, T_lo=-10.0, T_hi=5.0):
    """One map, over training start states at open ground.

    need balance        share of states whose best category is each category
    tie share           share whose best and second-best categories are within `margin` return units
    single accuracy     per body variable: accuracy of "the most common best category at this value"
    pair accuracy       the same with two variables known
    combination gain    best pair accuracy - best single accuracy (the reading rule's measure)
    interaction share   1 - best single accuracy (reported; capped by the balance of categories)
    Ties are excluded from the accuracies.
    """
    mask, NN, II, TT = start_mask(sol["world"], T_lo, T_hi)
    c, tie = best_category(sol, "O", margin)
    cats, keep = c[mask], ~tie[mask]
    X = {"food energy": NN[mask], "injury": II[mask], "body temperature": TT[mask]}
    balance = {k: float((cats == k).mean()) for k in CATEGORIES}
    cc = cats[keep]

    def acc(keys):
        k = np.zeros(cc.size)
        for name in keys:
            k = k * 1e4 + X[name][keep]
        total = 0
        for v in np.unique(k):
            sel = k == v
            total += max(int((sel & (cc == c2)).sum()) for c2 in CATEGORIES)
        return total / max(cc.size, 1)
    names = list(X)
    single = {n: acc([n]) for n in names}
    pair = {f"{a} + {b}": acc([a, b]) for i, a in enumerate(names) for b in names[i + 1:]}
    return dict(balance=balance, tie_share=float((~keep).mean()), single_accuracy=single, pair_accuracy=pair,
                combination_gain=max(pair.values()) - max(single.values()),
                interaction_share=1.0 - max(single.values()), three_way_share=1.0 - max(pair.values()))


def summarise(sols, margin=0.5, T_lo=-10.0, T_hi=5.0):
    """Per-map summaries pooled with the map weights (plan-reviewer R2: accuracies and gains are
    computed within each map, so a choice that differs between maps is not counted as a body-state
    interaction)."""
    per = [(summarise_map(s, margin, T_lo, T_hi), w) for s, w in sols]
    tot = sum(w for _, w in per)
    pool = lambda f: sum(w * f(s) for s, w in per) / tot
    return dict(balance={c: pool(lambda s: s["balance"][c]) for c in CATEGORIES},
                tie_share=pool(lambda s: s["tie_share"]),
                combination_gain=pool(lambda s: s["combination_gain"]),
                interaction_share=pool(lambda s: s["interaction_share"]),
                three_way_share=pool(lambda s: s["three_way_share"]),
                per_map=[s for s, _ in per])


# =====================================================================================================
# Revision 2 (balance study): stochastic world -- E1 food relocation, E2 hits drawn from measured bins
# =====================================================================================================

def macro_branches(world, N, I, T, kind, place, steps=None):
    """Outcome branches of one macro action when the hazard is stochastic (E2 bins).

    Exact for the FIRST hit inside the macro (any bin, at any step). After a branch's first hit the
    remaining steps of the same macro take the mean-field hazard of their activity, so the expected
    damage is preserved; what is lost is the variance of a second hit within one macro (at 2.7 % per
    moving step, P(two hits in a 4-step trip) is about 0.4 %). Single-step actions are exact.
    Returns [(prob, N, I, T, discounted reward, dead)], the common continuation discount, #steps.
    With a one-outcome (mean-field) distribution this is `macro`, operation for operation.
    `steps` (optional) replaces the macro's step list (used by the find_prob search option)."""
    P = world.body
    br = [(1.0, N, I, T, np.zeros_like(N), np.zeros(N.shape, bool), False)]
    disc = np.ones_like(N)
    if steps is None:
        steps = macro_steps(world, kind, place)
    for what, cell, bush in steps:
        dist = hazard_dist(world, what, bush)
        mean = sum(p * x for p, x in dist) if len(dist) > 1 else dist[0][1]
        new = []
        for prob, n_, i_, t_, R, dead, hit in br:
            if dead.all():
                new.append((prob, n_, i_, t_, R, dead, hit)); continue
            s = B.step(n_, i_, t_, rested=(what == "rest"), ate=(what == "eat"), in_bush=bush, cell_temp=cell, P=P)
            for p, x in ([(1.0, mean)] if hit else dist):
                if p <= 0.0:
                    continue
                if x:
                    N2, I2, T2, r, d, _ = apply_hit(P, s, x)
                else:
                    N2, I2, T2, r, d = s["N"], s["I"], s["T"], s["reward"], s["dead"]
                new.append((prob * p, N2, I2, T2, R + np.where(dead, 0.0, disc * r), dead | d, hit or x > 0))
        br = new; disc = disc * world.gamma
    return [b[:6] for b in br], disc, len(steps)


def solve_stochastic(world: World, iters: int = 5000, tol: float = 1e-4):
    """Value iteration with expectations over hazard outcomes (E2) and food relocation (E1).

    Each option's expected continuation is a sparse matrix (rows: states; columns: next place x grid
    state; entries: outcome probability x survival x trilinear interpolation weight), so one Bellman
    backup is one sparse matrix-vector product. Q = R + discount * (A @ V), which for a one-outcome
    world is the Revision-1 update in the same floating-point order (validate_balance.py checks this)."""
    from scipy import sparse
    GN, GI, GT = G = grids(world)
    NN, II, TT = np.meshgrid(GN, GI, GT, indexing="ij")
    N0, I0, T0 = NN.ravel(), II.ravel(), TT.ravel()
    S = N0.size
    places = [p for p in PLACES if p != "W" or world.warm_bush]
    pi = {p: k for k, p in enumerate(places)}
    e = 1.0 / world.bites_per_item if world.e1 else 0.0
    rows8 = np.repeat(np.arange(S, dtype=np.int32)[:, None], 8, axis=1).ravel()
    blocks, Rs, Ds, names, span = [], [], [], {p: [] for p in places}, {}
    for p in places:
        start = len(Rs)
        for kind, q in options(world, p):
            fp = (world.find_prob or {}).get(q) if kind == "go" else None
            if fp is None:
                br, disc, _ = macro_branches(world, N0, I0, T0, kind, q)
                dests = [(q, 1.0 - e), ("O", e)] if (kind == "eat" and e > 0) else [(q, 1.0)]
                br = [b + (dests,) for b in br]
            else:   # search: one step, found with prob fp (step in q's cell), else a travel step to open ground
                bs, disc, _ = macro_branches(world, N0, I0, T0, kind, q, steps=[("move", CELL[q], IN_BUSH[q])])
                bf, _, _ = macro_branches(world, N0, I0, T0, kind, q, steps=[("move", TRAVEL_CELL, False)])
                br = ([(b[0] * fp,) + b[1:] + ([(q, 1.0)],) for b in bs]
                      + [(b[0] * (1.0 - fp),) + b[1:] + ([("O", 1.0)],) for b in bf])
            R = np.zeros(S); rr, cc, dd = [], [], []
            for prob, N1, I1, T1, Rb, dead, dests in br:
                R = R + prob * Rb
                if dead.all():
                    continue
                idx, wts = _interp_setup(N1, I1, T1, G)
                alive = (~dead).astype(float)
                for dq, dp in dests:
                    rr.append(rows8); cc.append((idx.T + pi[dq] * S).astype(np.int32).ravel())
                    dd.append((wts * ((prob * dp) * alive)[None, :]).T.ravel())
            A = sparse.coo_matrix((np.concatenate(dd), (np.concatenate(rr), np.concatenate(cc))),
                                  shape=(S, len(places) * S)).tocsr()
            A.sum_duplicates(); A.sort_indices()
            blocks.append(A); Rs.append(R); Ds.append(disc); names[p].append(f"{kind}_{q}")
            del rr, cc, dd
        span[p] = (start, len(Rs))
    A = sparse.vstack(blocks, format="csr"); del blocks
    Rall, Dall = np.concatenate(Rs), np.concatenate(Ds)
    nnz = int(A.nnz)
    V = np.zeros((len(places), S))

    def backup(V):
        return Rall + Dall * (A @ V.ravel())
    for it in range(iters):
        Q = backup(V)
        Vn = np.stack([Q[span[p][0] * S:span[p][1] * S].reshape(-1, S).max(0) for p in places])
        delta = np.abs(Vn - V).max(); V = Vn
        if delta < tol:
            break
    Q = backup(V)
    q_values = {p: (np.array(names[p]), Q[span[p][0] * S:span[p][1] * S].reshape(-1, S)) for p in places}
    return dict(V=V, q=q_values, places=places, iters=it + 1, delta=float(delta), world=world, nnz=nnz)


def hazard_bins_from_measurements(meas, run=None, pool=None, collapse=False):
    """World.hazard_bins from world_measurements.json["hazard_bins"].
    run      which agent's recordings (default: the primary, ordinary agent)
    pool     None = per activity (eat / move / rest); "rest_other" = rest vs eat+move pooled;
             "all" = one distribution for every step outside cover
    collapse replace each distribution by a certain hit of its mean (p 1, one bin): the
             mean-field model expressed in the bins code path (validation)."""
    hb = meas["hazard_bins"]; acts = hb["runs"][run or hb["primary_run"]]["activities"]

    def combine(keys):
        rows = sum(acts[k]["rows"] for k in keys); hits = sum(acts[k]["hits"] for k in keys)
        cnt = np.sum([np.array(acts[k]["bin_counts"], float) for k in keys], 0)
        sz = np.sum([np.array(acts[k]["bin_counts"], float) * np.array(acts[k]["bin_mean_size"]) for k in keys], 0)
        return hits / rows, (cnt / hits).tolist(), np.where(cnt > 0, sz / np.maximum(cnt, 1), 0.0).tolist()
    groups = {None: {"eat": ["eat"], "move": ["move"], "rest": ["rest"]},
              "rest_other": {"eat": ["eat", "move"], "move": ["eat", "move"], "rest": ["rest"]},
              "all": {a: ["eat", "move", "rest"] for a in ("eat", "move", "rest")}}[pool]
    out = {}
    for a, keys in groups.items():
        p, probs, sizes = combine(keys)
        if collapse:
            m = p * float(np.dot(probs, sizes))
            p, probs, sizes = 1.0, [1.0], [m]
        out[a] = (p, probs, sizes)
    return out


def mean_of_bins(bins):
    """Per-activity mean damage per step of a hazard_bins dict."""
    return {a: p * float(np.dot(probs, sizes)) for a, (p, probs, sizes) in bins.items()}


# ---- rollouts for the balance measures (study plan Revision 2a / 2b) --------------------------------
WHAT_CODES = ["idle", "rest", "eat", "move"]
DEATH_CAUSES = ["injury", "starvation", "over-eating", "cold", "heat"]


def _ratio(num_a, den_a, num_b, den_b):
    """(num_a/den_a) / (num_b/den_b); None ("not computable") on any zero denominator."""
    if den_a == 0 or den_b == 0 or num_b == 0:
        return None
    return (num_a / den_a) / (num_b / den_b)


def rollout_balance(sol, n_starts=2000, max_steps=500, T_lo=-10.0, T_hi=5.0, seed=0, early=20, dyn_world=None):
    """Follow the ideal policy step by step from training-style starts at open ground and count the
    Revision-2a balance measures. Hazard hits are SAMPLED from the world's bins (several hits per trip
    possible); in mean mode the mean-field injury is added deterministically, as in Revision 1.
    E1: after each bite the item moves with prob 1/bites_per_item and the agent is back at open ground.
    Per-step shares use the body state at the START of the step and the cell the step is spent in
    (the destination cell on a trip's last step). Returns raw counts plus derived shares / ratios.
    dyn_world (optional): the world whose body, hazard, food and search rules the rollout follows, while
    the policy is sol's (value of knowing the context); None = sol["world"], as before. find_prob
    places: a "go" is one search step, found with the place's probability, else back at open ground."""
    world = dyn_world if dyn_world is not None else sol["world"]; P = world.body
    GN, GI, GT = grids(sol["world"])
    rng = np.random.default_rng(seed)
    n = n_starts
    N = rng.uniform(0, 200, n); I = rng.uniform(0, 100, n); T = rng.uniform(T_lo, T_hi, n)
    places = sol["places"]; pidx = {p: k for k, p in enumerate(places)}
    cell_of = np.array([CELL[p] for p in places]); bush_of = np.array([IN_BUSH[p] for p in places])
    trip_of = np.array([world.trip[p] for p in places])
    fp_of = np.array([(world.find_prob or {}).get(p, -1.0) for p in places], float)   # -1: fixed trip
    search = bool(world.find_prob)
    place = np.full(n, pidx["O"]); dest = np.full(n, -1); left = np.zeros(n, int); local = np.zeros(n, int)
    alive = np.ones(n, bool); death_t = np.full(n, -1); cause = np.full(n, -1)
    e = 1.0 / world.bites_per_item if world.e1 else 0.0
    near = lambda x, g: np.clip(np.rint((x - g[0]) / (g[1] - g[0])).astype(int), 0, len(g) - 1)
    code = {"idle": 0, "rest": 1, "eat": 2}
    dist = {w: hazard_dist(world, w, False) for w in WHAT_CODES}
    C = {k: 0 for k in ("steps", "cover", "warm", "eat", "elsewhere",
                        "n_hungry", "eat_hungry", "n_fed", "eat_fed",
                        "n_cold", "warm_cold", "n_warmT", "warm_warmT",
                        "n_inj", "cover_inj", "n_heal", "cover_heal",
                        "fed_n_inj", "fed_cover_inj", "fed_n_heal", "fed_cover_heal",
                        "hun_n_inj", "hun_cover_inj", "hun_n_heal", "hun_cover_heal",
                        "need_hunger", "need_injury", "need_temperature",
                        "bites", "relocations", "food_arrivals", "hits", "hit_damage")}
    for t in range(max_steps):
        a = np.flatnonzero(alive)
        if a.size == 0:
            break
        # ---- decisions for agents not on a trip ----
        dec = a[left[a] == 0]
        for p in places:
            sel = dec[place[dec] == pidx[p]]
            if sel.size == 0:
                continue
            names, vals = sol["q"][p]
            flat = (near(N[sel], GN) * len(GI) + near(I[sel], GI)) * len(GT) + near(T[sel], GT)
            choice = names[vals[:, flat].argmax(0)]
            for c in np.unique(choice):
                k = sel[choice == c]; kind, q = c.split("_")
                if kind == "go":
                    dest[k] = pidx[q]; left[k] = 1 if fp_of[pidx[q]] >= 0 else trip_of[pidx[q]]; local[k] = -1
                else:
                    local[k] = code[kind]
        # ---- this step's activity, cell and cover ----
        trav = left[a] > 0
        last = trav & (left[a] == 1)
        if search:      # a search step is found with the destination's probability (else: a travel step)
            fpa = fp_of[np.maximum(dest[a], 0)]
            found = np.where(trav & (fpa >= 0), rng.random(a.size) < fpa, True)
            last = last & found
        what = np.where(trav, 3, local[a])
        cell = np.where(trav, np.where(last, cell_of[np.maximum(dest[a], 0)], TRAVEL_CELL), cell_of[place[a]])
        bush = np.where(trav, last & bush_of[np.maximum(dest[a], 0)], bush_of[place[a]])
        n0, i0, t0 = N[a], I[a], T[a]
        warm = cell > 0; eating = what == 2
        C["steps"] += a.size; C["cover"] += int(bush.sum()); C["warm"] += int(warm.sum())
        C["eat"] += int(eating.sum()); C["elsewhere"] += int((~bush & ~warm & ~eating).sum())
        hungry, fed_ = n0 < 60, n0 >= 100
        C["n_hungry"] += int(hungry.sum()); C["eat_hungry"] += int((eating & hungry).sum())
        C["n_fed"] += int(fed_.sum()); C["eat_fed"] += int((eating & fed_).sum())
        cold, warmT = t0 < -5, t0 > 0
        C["n_cold"] += int(cold.sum()); C["warm_cold"] += int((warm & cold).sum())
        C["n_warmT"] += int(warmT.sum()); C["warm_warmT"] += int((warm & warmT).sum())
        inj, heal = i0 >= 60, i0 <= 20
        C["n_inj"] += int(inj.sum()); C["cover_inj"] += int((bush & inj).sum())
        C["n_heal"] += int(heal.sum()); C["cover_heal"] += int((bush & heal).sum())
        for tag, m in (("fed", (n0 >= 80) & (n0 <= 160)), ("hun", hungry)):
            C[f"{tag}_n_inj"] += int((m & inj).sum()); C[f"{tag}_cover_inj"] += int((m & inj & bush).sum())
            C[f"{tag}_n_heal"] += int((m & heal).sum()); C[f"{tag}_cover_heal"] += int((m & heal & bush).sum())
        need = np.argmax(np.stack([np.abs(n0 - P.setpoint), i0, np.abs(t0 - P.t_set) * 100.0 / P.t_max]), 0)
        for k, nm in enumerate(("need_hunger", "need_injury", "need_temperature")):
            C[nm] += int((need == k).sum())
        # ---- body step, then the hazard outside cover ----
        s = B.step(n0, i0, t0, rested=(what == 1), ate=eating, in_bush=bush, cell_temp=cell, P=P)
        x = np.zeros(a.size)
        for k, w in enumerate(WHAT_CODES):
            m = (what == k) & ~bush
            if not m.any():
                continue
            outs = dist[w]
            if len(outs) == 1:
                x[m] = outs[0][1]
            else:
                pr = np.array([o[0] for o in outs]); sz = np.array([o[1] for o in outs])
                j = np.searchsorted(np.cumsum(pr) / pr.sum(), rng.random(int(m.sum())), side="right")
                x[m] = sz[np.minimum(j, len(sz) - 1)]
        if world.e2 != "mean":
            C["hits"] += int((x > 0).sum()); C["hit_damage"] += float(x.sum())
        N2, I2, T2, _, dead, newly = apply_hit(P, s, x)
        c = np.full(a.size, -1)
        for k, m in enumerate((s["injury_death"] | newly, s["starve"], s["overeat"], T2 < P.t_min, T2 > P.t_max)):
            c = np.where((c < 0) & dead & m, k, c)
        N[a], I[a], T[a] = N2, I2, T2
        died = a[dead]; alive[died] = False; death_t[died] = t; cause[died] = c[dead]
        # ---- E1 relocation, trip progress ----
        ate_alive = a[eating & ~dead]
        C["bites"] += int(eating.sum())
        if e > 0 and ate_alive.size:
            mv = ate_alive[rng.random(ate_alive.size) < e]
            C["relocations"] += int(mv.size); place[mv] = pidx["O"]
        tr = a[trav]
        left[tr] -= 1
        arr = tr[left[tr] == 0]
        if search:      # an unsuccessful search step ends on open ground
            miss = arr[~found[np.searchsorted(a, arr)]]
            dest[miss] = pidx["O"]
        C["food_arrivals"] += int((dest[arr] == pidx.get("F", -9)).sum())
        place[arr] = dest[arr]; dest[arr] = -1
    late = (death_t >= early)
    deaths = {nm: int(((cause == k) & late).sum()) for k, nm in enumerate(DEATH_CAUSES)}
    early_deaths = {nm: int(((cause == k) & (death_t >= 0) & ~late).sum()) for k, nm in enumerate(DEATH_CAUSES)}
    n_late = int(sum(deaths.values()))
    st = max(C["steps"], 1)
    steps_lived = np.where(death_t >= 0, death_t + 1, max_steps)
    out = dict(
        n_starts=n, max_steps=max_steps, counts=C,
        survival_share=float(alive.mean()), mean_survival_steps=float(steps_lived.mean()),
        time_share={k: C[k] / st for k in ("cover", "warm", "eat", "elsewhere")},
        drive_ratio=dict(eat=_ratio(C["eat_hungry"], C["n_hungry"], C["eat_fed"], C["n_fed"]),
                         warm=_ratio(C["warm_cold"], C["n_cold"], C["warm_warmT"], C["n_warmT"]),
                         hide=_ratio(C["cover_inj"], C["n_inj"], C["cover_heal"], C["n_heal"])),
        need_share={k: C[f"need_{k}"] / st for k in ("hunger", "injury", "temperature")},
        deaths_after_early=deaths, deaths_early=early_deaths, early_steps=early,
        late_death_share_of_starts=n_late / n,
        death_cause_share={k: (v / n_late if n_late else None) for k, v in deaths.items()},
        hide=dict(fed=_ratio(C["fed_cover_inj"], C["fed_n_inj"], C["fed_cover_heal"], C["fed_n_heal"]),
                  hungry=_ratio(C["hun_cover_inj"], C["hun_n_inj"], C["hun_cover_heal"], C["hun_n_heal"])),
        e1=dict(bites=C["bites"], relocations=C["relocations"], food_arrivals=C["food_arrivals"],
                relocations_per_bite=(C["relocations"] / C["bites"] if C["bites"] else None),
                bites_per_visit=(C["bites"] / C["food_arrivals"] if C["food_arrivals"] else None)))
    return out


def warming_per_decision(sol, margin=0.5, T_lo=-10.0, T_hi=5.0, cold=-5.0, warmT=0.0):
    """Criterion 2 (b'), study plan Revision 2b: among training start states at open ground, the share
    whose best choice is "warm up" at body temperature <= -5 divided by the share at >= 0.
    Primary: all start states; also reported with ties (within `margin`) excluded."""
    mask, NN, II, TT = start_mask(sol["world"], T_lo, T_hi)
    cat, tie = best_category(sol, "O", margin)
    w = (cat == "warm up")
    lo, hi = mask & (TT <= cold + 1e-9), mask & (TT >= warmT - 1e-9)
    def ratio(extra):
        a_, b_ = lo & extra, hi & extra
        if a_.sum() == 0 or b_.sum() == 0 or (w & b_).sum() == 0:
            return None, float((w & a_).sum() / max(a_.sum(), 1)), float((w & b_).sum() / max(b_.sum(), 1))
        sa, sb = (w & a_).sum() / a_.sum(), (w & b_).sum() / b_.sum()
        return float(sa / sb), float(sa), float(sb)
    r, sa, sb = ratio(np.ones_like(mask))
    rt, sat, sbt = ratio(~tie)
    return dict(ratio=r, share_cold=sa, share_warm=sb, ratio_ties_excluded=rt,
                share_cold_ties_excluded=sat, share_warm_ties_excluded=sbt)
