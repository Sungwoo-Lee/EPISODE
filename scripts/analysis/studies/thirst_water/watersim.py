"""An agent-free sandbox for the planned water/thirst rules: how hard is the level-06 world?

Plain-language purpose: water does not exist in the environment yet (docs/develop/active/thirst/
THIRST_WATER_PLAN.md is approved for an artifact only). To see how the planned settings -- how fast
thirst drains, how much one step on the pond gives back, how big the grid is, where the pond may sit --
change the difficulty, this module runs many episodes of a reduced level-06 world with a SCRIPTED
agent (a fixed rule, not a trained policy) and reports survival steps and causes of death.

What is real and what is not:
  * food and body temperature: `bodysim.step` from the internal-state study, a line-for-line numpy
    copy of `core.py::update_body` validated against the real environment (4,000 steps, max
    difference 2e-5, commit 2004b234). Level-05 values: nutrition 0-200 setpoint 100, decay 1/step,
    +5 net per bite on top (bite = the eat action on a food cell), overeating death at 200;
    temperature k_exchange 0.04, k_loss 0.02, warming 2.0 / cooling 0.25, death outside [-15, 15].
  * water: the PLAN's rule, not code (none exists): W' = clip(W - drain + gain*on_pond, 0, max),
    death at W' <= 0 (thirst) or W' >= max (over-drinking); drinking is automatic on any pond cell.
  * map: cell temperature = the MEASURED median by Manhattan distance to the nearest fire (300 real
    level-05 resets: 77.3, 8.8, -16.5, -29.4, -30.0 at distance 0,1,2,3,>=4); overlapping fires are
    not summed (min_fire_separation 4 keeps overlap small). Fires 1-3 inside the edge-margin-2 area,
    Manhattan >= 4 apart; food 1-4 items, 12 bites each, then the item moves to a random free cell;
    one 2x2 pond placed by the plan's three modes; nothing on the pond. Moves are the four compass
    steps (nothing on the level-05 map blocks the agent), so a trip is a Manhattan distance.
  * NOT modelled: predators and injury (so the numbers are an upper bound on survival), and smell.
    By default the scripted agent knows every position (it measures the rules' budget). With
    `search=True` it must FIND the pond each episode: it knows the placement mode (the candidate
    list, or "anywhere inside the margin", or the fixed centre) but not which cell was drawn, and it
    discovers the pond when any pond cell is within Manhattan `see` (the vision sensor's range 2).
    Under list mode it checks the nearest unchecked candidate; under random mode it walks to the
    nearest cell it has not yet seen. Food and fires stay known -- only water is searched for.

The scripted agent ("a sensible homeostat"): it camps on the fire ring (the cold clock is the
fastest), and when the most urgent need's spare time -- steps until that need kills, minus the walk
to its nearest source -- drops below `margin`, it commits to that need until it is refilled
(water to `w_hi`, food to `n_hi`, temperature to `t_hi`), switching early only if another need
becomes critical. It walks the shortest compass path, sidestepping fire cells.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "internal_state_interactions"))
import bodysim as B  # noqa: E402

CELL_TEMP = np.array([77.26, 8.76, -16.52, -29.42, -30.04])     # by Manhattan distance to a fire, >=4 clipped
CAUSES = ["survived 500", "thirst", "over-drinking", "starvation", "over-eating", "cold", "heat"]
ACTS = ["walking to water", "drinking", "walking to food", "eating", "walking to a fire", "at the fire ring"]


@dataclass(frozen=True)
class Water:
    max: float = 200.0
    setpoint: float = 100.0
    drain: float = 0.625
    gain: float = 5.625
    start_low: float = 0.0            # user decision 2026-09-29: full range
    start_high: float = 200.0
    size: int = 2
    placement: str = "list"           # list | random | center
    edge_margin: int = 1

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass(frozen=True)
class World:
    grid: int = 10
    water: Water = field(default_factory=Water)
    body: B.Body = field(default_factory=B.Body)
    fires: tuple = (1, 3)
    food: tuple = (1, 4)
    bites: int = 12
    fire_margin: int = 2
    fire_sep: int = 4
    start_T: tuple = (-10.0, 5.0)     # level 05 random_start_body_temp
    start_N: tuple = (0.0, 200.0)     # level 03+ random_start_nutrition
    steps: int = 500
    # scripted agent
    margin: float = 25.0
    w_hi: float = 160.0
    n_hi: float = 160.0
    t_hi: float = 4.5
    search: bool = False
    see: int = 2

    def with_(self, **kw):
        return replace(self, **kw)


def pond_topleft_options(G, w: Water):
    s, m = w.size, w.edge_margin
    if w.placement == "list":        # the plan's default: the four quadrant blocks just inside the margin
        a, b = m, G - m - s
        return [(a, a), (a, b), (b, a), (b, b)]
    if w.placement == "random":
        return [(r, c) for r in range(m, G - m - s + 1) for c in range(m, G - m - s + 1)]
    if w.placement == "center":
        return [((G - s) // 2, (G - s) // 2)]
    raise ValueError(w.placement)


def _cold_steps_table(P: B.Body, ambient=-30.04):
    """Steps until cold death from each start temperature at the cold ambient (the fire-free clock)."""
    Ts = np.linspace(-15.0, 15.0, 301)
    T = Ts.copy(); alive = np.ones_like(T, bool); n = np.zeros_like(T)
    for k in range(1, 2000):
        d = P.k_ex * (ambient - T) - P.k_loss * (T - P.t_set)
        T = T + np.where(d > 0, P.warm_scale, P.cool_scale) * d
        died = alive & (T < P.t_min); n[died] = k; alive &= ~died
        if not alive.any():
            break
    return Ts, n


def _place(rng, W: World, E):
    G = W.grid; s = W.water.size
    opts = pond_topleft_options(G, W.water)
    k = rng.integers(0, len(opts), E)
    pond_tl = np.array(opts)[k]                                        # (E,2)
    pond = np.zeros((E, G, G), bool)
    for e in range(E):
        r, c = pond_tl[e]; pond[e, r:r + s, c:c + s] = True
    # fires, rejection-sampled per episode (small numbers)
    fire = np.zeros((E, G, G), bool); fires = []
    lo, hi = W.fire_margin, G - W.fire_margin
    for e in range(E):
        nf = rng.integers(W.fires[0], W.fires[1] + 1); pts = []
        for _ in range(10000):
            if len(pts) == nf:
                break
            p = (int(rng.integers(lo, hi)), int(rng.integers(lo, hi)))
            if pond[e, p[0], p[1]] or any(abs(p[0] - q[0]) + abs(p[1] - q[1]) < W.fire_sep for q in pts):
                continue
            pts.append(p)
        for p in pts:
            fire[e, p[0], p[1]] = True
        fires.append(pts)
    return pond_tl, pond, fire, fires


def _dist_maps(mask):
    """Manhattan distance from every cell to the nearest True cell, and that cell's coordinates."""
    E, G, _ = mask.shape
    rr, cc = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
    D = np.full((E, G, G), 10 ** 6); TR = np.zeros((E, G, G), int); TC = np.zeros((E, G, G), int)
    for e in range(E):
        pts = np.argwhere(mask[e])
        if len(pts) == 0:
            continue
        d = np.abs(rr[None] - pts[:, 0, None, None]) + np.abs(cc[None] - pts[:, 1, None, None])
        i = d.argmin(0); D[e] = d.min(0); TR[e] = pts[i, 0]; TC[e] = pts[i, 1]
    return D, TR, TC


def run(W: World, E=2000, seed=0, record_track=False):
    rng = np.random.default_rng(seed)
    G, P, Wt = W.grid, W.body, W.water
    pond_tl, pond, fire, fires = _place(rng, W, E)
    fireD, _, _ = _dist_maps(fire)
    cell_temp = CELL_TEMP[np.minimum(fireD, 4)]
    ring = (fireD == 1) & ~pond
    ringD, ringR, ringC = _dist_maps(ring)
    pondD, pondR, pondC = _dist_maps(pond)
    Ts_tab, cold_tab = _cold_steps_table(P)

    free = ~pond & ~fire
    def rand_free(e):
        cells = np.argwhere(free[e]); return cells[rng.integers(len(cells))]
    pos = np.array([rand_free(e) for e in range(E)])
    nfood = rng.integers(W.food[0], W.food[1] + 1, E)
    food = np.array([[rand_free(e) for _ in range(W.food[1])] for e in range(E)])      # (E,4,2)
    food_on = np.arange(W.food[1])[None] < nfood[:, None]
    bites = np.full((E, W.food[1]), W.bites)

    rr, cc = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
    sz = Wt.size
    opts = np.array(pond_topleft_options(G, Wt))                      # (K,2)
    known = np.full(E, (not W.search) or Wt.placement == "center")
    seen = np.zeros((E, G, G), bool)
    cand_alive = np.ones((E, len(opts)), bool)
    first_found = np.full(E, -1)
    N = rng.uniform(*W.start_N, E); T = rng.uniform(*W.start_T, E)
    Wv = rng.uniform(Wt.start_low, Wt.start_high, E); I = np.zeros(E)
    W0 = Wv.copy()
    alive = np.ones(E, bool); life = np.full(E, W.steps); cause = np.zeros(E, int)
    goal = np.full(E, -1)            # -1 camp, 0 water, 1 food, 2 warm
    act = np.zeros((E, len(ACTS)))
    visits = np.zeros(E); drinks = np.zeros(E); drink_steps = np.zeros(E); arr_sum = np.zeros(E)
    on_pond_prev = pond[np.arange(E), pos[:, 0], pos[:, 1]]
    ar = np.arange(E)
    track = [] if record_track else None

    for t in range(W.steps):
        r, c = pos[:, 0], pos[:, 1]
        if W.search:
            md = np.abs(rr[None] - r[:, None, None]) + np.abs(cc[None] - c[:, None, None])   # (E,G,G)
            seen |= md <= W.see
            newly = ~known & (seen & pond).any((1, 2))
            first_found = np.where(newly, t, first_found); known |= newly
            # candidate blocks fully checked (any of their cells seen) and not the pond are ruled out
            for k, (a, b) in enumerate(opts):
                cand_alive[:, k] &= ~seen[:, a:a + sz, b:b + sz].any((1, 2)) | pond[:, a, b]
            if Wt.placement == "list":
                dr_ = np.maximum(0, np.maximum(opts[None, :, 0] - r[:, None], r[:, None] - (opts[None, :, 0] + sz - 1)))
                dc_ = np.maximum(0, np.maximum(opts[None, :, 1] - c[:, None], c[:, None] - (opts[None, :, 1] + sz - 1)))
                cd = np.where(cand_alive, dr_ + dc_, 10 ** 6); ki = cd.argmin(1)
                sr = np.clip(r, opts[ki, 0], opts[ki, 0] + sz - 1); sc = np.clip(c, opts[ki, 1], opts[ki, 1] + sz - 1)
                sdist = cd[ar, ki]
            else:
                um = np.where(seen, 10 ** 6, md).reshape(E, -1); j = um.argmin(1)
                sr, sc = j // G, j % G; sdist = um[ar, j]
        # --- distances to each need's nearest source ---
        fd = np.abs(food[:, :, 0] - r[:, None]) + np.abs(food[:, :, 1] - c[:, None])
        fd = np.where(food_on, fd, 10 ** 6); fi = fd.argmin(1); food_dist = fd[ar, fi]
        d_w, d_f, d_h = pondD[ar, r, c], food_dist, ringD[ar, r, c]
        if W.search:
            d_w = np.where(known, d_w, sdist)
        left_w = Wv / Wt.drain if Wt.drain > 0 else np.full(E, 1e9)
        left_f = N / P.metabolic_cost
        left_h = np.interp(T, Ts_tab, cold_tab)
        slack = np.stack([left_w - d_w, left_f - d_f, left_h - d_h], 1)
        # --- goal logic ---
        done_w = (goal == 0) & (Wv >= W.w_hi); done_f = (goal == 1) & (N >= W.n_hi); done_h = (goal == 2) & (T >= W.t_hi)
        goal = np.where(done_w | done_f | done_h, -1, goal)
        urgent = slack.argmin(1); m = slack.min(1)
        pick = (goal == -1) & (m < W.margin)
        crit = (goal >= 0) & (m < 5) & (urgent != goal)
        goal = np.where(pick | crit, urgent, goal)
        # --- target cell ---
        pr_, pc_ = pondR[ar, r, c], pondC[ar, r, c]
        if W.search:
            pr_ = np.where(known, pr_, sr); pc_ = np.where(known, pc_, sc)
        tr = np.where(goal == 0, pr_, np.where(goal == 1, food[ar, fi, 0], ringR[ar, r, c]))
        tc = np.where(goal == 0, pc_, np.where(goal == 1, food[ar, fi, 1], ringC[ar, r, c]))
        at = (tr == r) & (tc == c)
        if W.search:
            at = at & ~((goal == 0) & ~known)          # a search target is a waypoint, not a place to stop
        eat = (goal == 1) & at & alive
        # --- move one compass step toward the target, sidestepping fire ---
        dr, dc = np.sign(tr - r), np.sign(tc - c)
        prefer_r = np.abs(tr - r) >= np.abs(tc - c)
        m1 = np.stack([np.where(prefer_r, dr, 0), np.where(prefer_r, 0, dc)], 1)
        m2 = np.stack([np.where(prefer_r, 0, dr), np.where(prefer_r, dc, 0)], 1)
        cand1 = np.clip(pos + m1, 0, G - 1); cand2 = np.clip(pos + m2, 0, G - 1)
        f1 = fire[ar, cand1[:, 0], cand1[:, 1]]; f2 = fire[ar, cand2[:, 0], cand2[:, 1]]
        side = np.stack([m1[:, 1], m1[:, 0]], 1)                       # perpendicular step
        cand3 = np.clip(pos + side, 0, G - 1); f3 = fire[ar, cand3[:, 0], cand3[:, 1]]
        nxt = np.where(~f1[:, None], cand1, np.where((~f2 & (np.abs(m2).sum(1) > 0))[:, None], cand2,
                       np.where(~f3[:, None], cand3, pos)))
        stay = at | eat
        new = np.where(stay[:, None], pos, nxt)
        new = np.where(alive[:, None], new, pos)
        # --- body step (post-move cell, as in the environment) ---
        nr, nc = new[:, 0], new[:, 1]
        on_pond = pond[ar, nr, nc]
        out = B.step(N, I, T, rested=np.zeros(E, bool), ate=eat, in_bush=np.zeros(E, bool),
                     cell_temp=cell_temp[ar, nr, nc], P=P)
        W_new = np.clip(Wv - Wt.drain + Wt.gain * on_pond, 0.0, Wt.max)
        thirst = W_new <= 0.0; overdrink = W_new >= Wt.max
        cold = out["thermal_death"] & (out["T"] < P.t_min); heat = out["thermal_death"] & (out["T"] > P.t_max)
        # label priority: water codes win over cold (plan call 7), as the plan specifies
        cz = np.select([thirst, overdrink, out["starve"], out["overeat"], cold, heat], [1, 2, 3, 4, 5, 6], 0)
        dies = alive & (cz > 0)
        cause = np.where(dies, cz, cause); life = np.where(dies, t + 1, life)
        # activity bookkeeping (alive episodes only)
        a = np.where(goal == 0, np.where(on_pond, 1, 0), np.where(goal == 1, np.where(eat, 3, 2),
                     np.where(goal == 2, 4, 5)))
        a = np.where((goal == 0) & on_pond, 1, a)
        np.add.at(act, (ar[alive], a[alive]), 1)
        entry = alive & on_pond & ~on_pond_prev
        visits += entry
        dentry = entry & (goal == 0)                     # a deliberate drink, not a walk-through
        drinks += dentry; arr_sum += np.where(dentry, Wv, 0.0)
        drink_steps += alive & on_pond & (goal == 0)
        on_pond_prev = on_pond
        if record_track:
            track.append(dict(W=Wv.copy(), N=N.copy(), T=T.copy(), goal=goal.copy(), on_pond=on_pond.copy(),
                              alive=alive.copy()))
        # commit
        pos = new; N, T = out["N"], out["T"]; Wv = W_new
        alive = alive & ~dies
        # food bites and relocation
        bites[ar, fi] = np.where(eat, bites[ar, fi] - 1, bites[ar, fi])
        gone = eat & (bites[ar, fi] <= 0)
        for e in np.flatnonzero(gone):
            food[e, fi[e]] = rand_free(e); bites[e, fi[e]] = W.bites
        if not alive.any():
            break
    share = act / np.maximum(act.sum(1, keepdims=True), 1)
    res = dict(life=life, cause=cause, share=share, visits=visits, drinks=drinks, drink_steps=drink_steps,
               arr_sum=arr_sum, W0=W0, pond_tl=pond_tl,
               first_found=first_found, known_at_end=known, E=E)
    if record_track:
        res["track"] = track
    return res


def cause_shares(res):
    return {name: float(np.mean(res["cause"] == i)) for i, name in enumerate(CAUSES)}
