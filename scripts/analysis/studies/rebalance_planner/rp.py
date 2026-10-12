"""Rebalance-planner core: the old study's ideal planner with per-source hazards (predator, trap, rock).

Plain-language purpose: reuse the internal-state-interactions planner (value iteration over food energy x
injury x body temperature x place) unchanged, but feed it each candidate world's own hit odds, split by
source, so that the planner's best choice -- hide in a bush, go out to eat, or something else -- can be
read per world, and its policy can be followed step by step to count survival, causes of death and time
use. Imports the old modules by path; nothing in the old study is edited.

What is changed relative to the old study (all in this file):
  * hazard_dist is replaced (monkeypatched on the imported planner module) by one that reads
    world.hazard_bins = {what: [(prob, size, source)]} for what in move / idle / eat / rest; sources are
    mutually exclusive within one step (two sources hitting the same step, probability <= ~0.006 in the
    invisible-hazard worlds, is folded into one hit)
  * a rollout that samples each hit's SOURCE, so injury deaths are split into predator / trap / rock,
    and that splits time into in a bush / travelling / eating / warming / other in the open
Everything else -- body (bodysim), discount 0.95, the two maps (no warm bush 0.59, warm bush 0.41),
trips of 2 steps to bush / ring / open, E1 food relocation after a bite with prob 1/bites, the training
start states (food 0-200, injury 0-100, temperature -10..+5 at open ground) -- is the old study's.
"""
from __future__ import annotations

import importlib.util, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OLD = os.path.join(ROOT, "scripts/analysis/studies/internal_state_interactions")
FIG = os.path.join(ROOT, "docs/experiments/active/rebalance_planner/figures")
MAPPINGS = os.path.join(FIG, "mappings.json")


def _load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(OLD, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


B = _load("bodysim")          # planner.py does `import bodysim as B`; registering it first keeps one copy
PL = _load("planner")
assert PL.B is B
_OLD_HAZARD_DIST = PL.hazard_dist
SOURCES = ["predator", "trap", "rock"]
DECISION = {"rest in cover": "hide", "eat": "forage", "warm up": "other", "stay in the open": "other"}
DECISIONS = ["hide", "forage", "other"]
TIME_KEYS = ["bush", "travel", "eat", "warm", "open"]
DEATHS = ["predator", "trap", "rock", "starvation", "over-eating", "cold", "heat"]


def hazard_dist(world, what, bush):
    """[(prob, injury added)] for one step; 0 = no hit. Only for worlds built by make_world (tagged)."""
    hb = world.hazard_bins
    if not (isinstance(hb, dict) and hb.get("_rebalance")):
        return _OLD_HAZARD_DIST(world, what, bush)
    if bush:
        return [(1.0, 0.0)]
    outs = hb[what]
    p = sum(o[0] for o in outs)
    assert p <= 1.0, (what, p)
    return [(1.0 - p, 0.0)] + [(o[0], o[1]) for o in outs if o[0] > 0]


PL.hazard_dist = hazard_dist


def hazard_table(wmap, pred_scale=1.0):
    """mappings.json world entry -> {what: [(prob, size, source index)]}, tagged for hazard_dist.
    pred_scale (exploratory lever sweep): multiplies the predator hit odds only."""
    out = {"_rebalance": True}
    for what, src in wmap["hazard"].items():
        out[what] = [(v["p"] * q * (pred_scale if k == "predator" else 1.0), x, SOURCES.index(k))
                     for k, v in src.items() for q, x in v["bins"] if v["p"] * q > 0]
    return out


def make_world(wmap, warm, trip_food=None, grid=(51, 26, 61), pred_scale=1.0, bush_multiplier=None, gamma=0.95):
    """bush_multiplier (exploratory, planner only): bush healing multiplier; None = today's 25."""
    f = wmap["food"]
    body = B.Body().with_(food_gain_net=float(f["net"]))
    if bush_multiplier is not None:
        body = body.with_(bush_multiplier=float(bush_multiplier))
    trip = {"O": 2, "B": 2, "W": 2, "R": 2, "F": int(trip_food or f["trip"])}
    return PL.World(body=body, trip=trip, warm_bush=warm, e1=True, bites_per_item=float(f["bites"]),
                    e2="bins", hazard_bins=hazard_table(wmap, pred_scale), gamma=gamma, grid=grid)


# ---------------------------------------------------------------------------------------------------
def decision_shares(sol, place="O", margin=0.0, T_lo=-10.0, T_hi=5.0):
    """Shares of training start states (at `place`) whose best category is hide / forage / other.
    margin > 0: states whose best two categories are within `margin` return units are dropped."""
    mask, NN, II, TT = PL.start_mask(sol["world"], T_lo, T_hi)
    cat, tie = PL.best_category(sol, place, margin if margin > 0 else 1e-12)
    keep = mask & (~tie if margin > 0 else np.ones_like(mask))
    d = np.array([DECISION[c] for c in cat[keep]])
    return {k: float((d == k).mean()) for k in DECISIONS} | dict(n=int(keep.sum()), n_start=int(mask.sum()))


def hide_forage_gap(sol, place="O", T_lo=-10.0, T_hi=5.0):
    """Exploratory: per start state, best 'hide' value minus best 'forage' value (return units)."""
    mask, *_ = PL.start_mask(sol["world"], T_lo, T_hi)
    names, vals = sol["q"][place]
    cats = np.array([DECISION[PL.CATEGORY[n]] for n in names])
    hide = np.where((cats == "hide")[:, None], vals, -np.inf).max(0)
    eat = np.where((cats == "forage")[:, None], vals, -np.inf).max(0)
    return (hide - eat)[mask]


def category_codes(sol, place="O"):
    cat, tie = PL.best_category(sol, place, 0.5)
    return np.array([DECISIONS.index(DECISION[c]) for c in cat], np.uint8), tie


# ---------------------------------------------------------------------------------------------------
def rollout(sol, n_starts=4000, max_steps=500, T_lo=-10.0, T_hi=5.0, seed=0):
    """Follow the ideal policy step by step (same decision rule and step order as planner.rollout_balance),
    sampling each hit's source. Returns survival, death causes, time shares and hit counts."""
    world = sol["world"]; P = world.body; GN, GI, GT = PL.grids(world)
    rng = np.random.default_rng(seed); n = n_starts
    N = rng.uniform(0, 200, n); I = rng.uniform(0, 100, n); T = rng.uniform(T_lo, T_hi, n)
    places = sol["places"]; pidx = {p: k for k, p in enumerate(places)}
    cell_of = np.array([PL.CELL[p] for p in places]); bush_of = np.array([PL.IN_BUSH[p] for p in places])
    trip_of = np.array([world.trip[p] for p in places])
    place = np.full(n, pidx["O"]); dest = np.full(n, -1); left = np.zeros(n, int); local = np.zeros(n, int)
    alive = np.ones(n, bool); death_t = np.full(n, -1); cause = np.full(n, -1)
    e = 1.0 / world.bites_per_item
    near = lambda x, g: np.clip(np.rint((x - g[0]) / (g[1] - g[0])).astype(int), 0, len(g) - 1)
    code = {"idle": 0, "rest": 1, "eat": 2}
    WHAT = ["idle", "rest", "eat", "move"]
    tab = {}
    for k, w in enumerate(WHAT):
        outs = world.hazard_bins[w]
        pr = np.array([1.0 - sum(o[0] for o in outs)] + [o[0] for o in outs])
        tab[k] = (np.cumsum(pr), np.array([0.0] + [o[1] for o in outs]), np.array([-1] + [o[2] for o in outs]))
    time = dict.fromkeys(TIME_KEYS, 0); warm_cell = 0; steps = 0
    hits = np.zeros(len(SOURCES), int); dmg = np.zeros(len(SOURCES))
    for t in range(max_steps):
        a = np.flatnonzero(alive)
        if a.size == 0:
            break
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
                    dest[k] = pidx[q]; left[k] = trip_of[pidx[q]]; local[k] = -1
                else:
                    local[k] = code[kind]
        trav = left[a] > 0; last = trav & (left[a] == 1)
        what = np.where(trav, 3, local[a])
        dsafe = np.maximum(dest[a], 0)
        cell = np.where(trav, np.where(last, cell_of[dsafe], PL.TRAVEL_CELL), cell_of[place[a]])
        bush = np.where(trav, last & bush_of[dsafe], bush_of[place[a]])
        eating = what == 2
        steps += a.size; warm_cell += int((cell > 0).sum())
        time["bush"] += int(bush.sum())
        time["travel"] += int((trav & ~bush).sum())
        time["eat"] += int((eating & ~bush).sum())
        time["warm"] += int((~trav & ~bush & ~eating & (cell > 0)).sum())
        time["open"] += int((~trav & ~bush & ~eating & (cell <= 0)).sum())
        s = B.step(N[a], I[a], T[a], rested=(what == 1), ate=eating, in_bush=bush, cell_temp=cell, P=P)
        x = np.zeros(a.size); src = np.full(a.size, -1)
        u = rng.random(a.size)
        for k in range(4):
            m = (what == k) & ~bush
            if m.any():
                cum, sz, so = tab[k]
                j = np.minimum(np.searchsorted(cum, u[m], side="right"), len(sz) - 1)
                x[m] = sz[j]; src[m] = so[j]
        for k in range(len(SOURCES)):
            hits[k] += int((src == k).sum()); dmg[k] += float(x[src == k].sum())
        N2, I2, T2, _, dead, newly = PL.apply_hit(P, s, x)
        c = np.full(a.size, -1)
        inj = s["injury_death"] | newly
        c = np.where(dead & inj & (src >= 0), src, c)                       # 0 predator, 1 trap, 2 rock
        for k, m in ((3, s["starve"]), (4, s["overeat"]), (5, T2 < P.t_min), (6, T2 > P.t_max)):
            c = np.where((c < 0) & dead & m, k, c)
        assert not (dead & (c < 0)).any(), "unattributed death"
        N[a], I[a], T[a] = N2, I2, T2
        died = a[dead]; alive[died] = False; death_t[died] = t; cause[died] = c[dead]
        ate_alive = a[eating & ~dead]
        if ate_alive.size:
            place[ate_alive[rng.random(ate_alive.size) < e]] = pidx["O"]
        tr = a[trav]; left[tr] -= 1
        arr = tr[left[tr] == 0]; place[arr] = dest[arr]; dest[arr] = -1
    deaths = {nm: int((cause == k).sum()) for k, nm in enumerate(DEATHS)}
    early = {nm: int(((cause == k) & (death_t < 20)).sum()) for k, nm in enumerate(DEATHS)}
    lived = np.where(death_t >= 0, death_t + 1, max_steps)
    return dict(n_starts=n, max_steps=max_steps, survival=float(alive.mean()), mean_steps=float(lived.mean()),
                deaths=deaths, deaths_before_step_20=early, death_share_of_starts={k: v / n for k, v in deaths.items()},
                time_share={k: v / max(steps, 1) for k, v in time.items()}, warm_cell_share=warm_cell / max(steps, 1),
                hits_per_100_steps={s_: 100.0 * hits[k] / max(steps, 1) for k, s_ in enumerate(SOURCES)},
                damage_per_100_steps={s_: 100.0 * dmg[k] / max(steps, 1) for k, s_ in enumerate(SOURCES)},
                agent_steps=int(steps))


def load_mappings():
    return json.load(open(MAPPINGS))
