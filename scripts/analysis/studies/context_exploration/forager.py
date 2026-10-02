"""Part 3b of the context-exploration study: how long does it take to find food, cover and warmth?

Plain-language purpose: the planner cannot search; it needs to be told how many steps finding a food
item, a bush or a warm spot takes in each world. A simple memoryless forager measures that on the real
reset maps saved by make_worlds.py (1,000 resets per world, from the reset's own agent start):
  food / cover  if any of the five sampled smell cells (the agent's cell and its four neighbours,
                in-bounds only) lies within the smell range (Euclidean, as the environment's
                sensor) of an item, walk straight (Manhattan) to the nearest such item; otherwise take
                one uniform random step of four (a step into the wall stays put). Rocks and fires are
                crossed, as in level 05 (non-blocking); steps onto rocks are counted as exposure.
  warmth        by feel (no smell): the five-cell thermal stencil (edge cells clamp, as the sensor);
                a cell >= threshold above ambient (5 C primary; 2 and 10 C sensitivity; ambient = the
                episode's coldest cell, the field's fill value) means "felt"; then climb to the warmest
                stencil neighbour until standing on a cell above 0 C; a random step if nothing is felt
                or the climb is stuck below 0 C.
  warmth, with memory (primary since Revision 2 / 2a): the walking distance (breadth-first grid steps
                of four moves, never entering a rock or fire cell, bushes crossable) from a random open
                cell to the nearest cell warmer than 0 C. Open cell = interior cell (rows / columns 1 ..
                G-2, as measure_world.py's ring trip) that is not a bush, rock or fire; 20 samples per
                reset (seed 0), as measure_world.py. The Manhattan distance through everything (the
                balance study's ring-trip definition) is reported beside it. The blind search above is
                kept as the pessimistic bracket.
  cap           2,000 steps; the capped share is reported; > 1 % capped food searches = "search
                unmeasured" (not a candidate).
Reported per world: median, mean (with 95 % interval), 90th percentile, capped share, exposure steps.

Validation (STUDY_PLAN.md Part 3, can fail):
  (i)   empty grid 10 / 15 / 20, one fixed target (centre, and cell (1,1)), smell range 3 / 5 / 8: the
        forager's mean search time (20,000 walks from uniform starts; cap raised to 100,000 so the
        comparison is not truncated) matches the exact hitting time of its own walk, solved as a
        Markov chain, within 10 %
  (ii)  in every layout, mean and median food search do not increase as the smell range grows (a
        violation = the longer range's 95 % interval lies entirely above the shorter range's)
  (iii) sanity only: today's world at range 20 vs the measured 4-step median food trip

  python forager.py --procs 16 --worlds results/analysis/context_exploration/worlds \
      --out results/analysis/context_exploration/part3_search_times_rev2.json
  (Revision-1 output part3_search_times.json is kept; food / cover / blind warmth are seeded and identical)
"""
import argparse, glob, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAP = 2000
RANGES = (20, 8, 5, 3)
WARM_THRESHOLDS = (2.0, 5.0, 10.0)
STENCIL = np.array([[0, 0], [-1, 0], [0, 1], [1, 0], [0, -1]])       # sensor.get_visual_offsets(1)
MOVES = np.array([[-1, 0], [0, 1], [1, 0], [0, -1]])


def _detect(pos, items, act, r, G):
    """pos [n,2]; items [n,K,2]; act [n,K]. Returns (detected [n], index of nearest sensed item [n])."""
    cells = pos[:, None, :] + STENCIL[None]                                     # [n,5,2]
    inb = ((cells >= 0) & (cells < G)).all(-1)                                   # [n,5]
    d = np.sqrt(((cells[:, :, None, :] - items[:, None, :, :]) ** 2).sum(-1))   # [n,5,K]
    sensed = ((d <= r) & inb[:, :, None] & act[:, None, :]).any(1)             # [n,K]
    man = np.abs(items - pos[:, None, :]).sum(-1).astype(float)
    man = np.where(sensed, man, np.inf)
    return sensed.any(1), man.argmin(1)


def _walk_exposure(p, q, rocks):
    """Steps onto rock cells along the straight Manhattan walk p -> q (larger axis first)."""
    p = p.copy(); n = 0
    while (p != q).any():
        dr, dc = q[0] - p[0], q[1] - p[1]
        if abs(dr) >= abs(dc):
            p[0] += np.sign(dr)
        else:
            p[1] += np.sign(dc)
        n += int(((rocks == p).all(-1)).any())
    return n


def smell_search(start, items, act, r, G, rocks, rock_act, seed, cap=CAP):
    """Vectorised forager search for one target type. Returns steps [n] (CAP+ if capped), capped [n],
    exposure steps [n]."""
    n = start.shape[0]
    rng = np.random.default_rng(seed)
    pos = start.astype(int).copy()
    t = np.zeros(n, int); done = np.zeros(n, bool); steps = np.full(n, cap, int); expo = np.zeros(n, int)
    rock_grid = np.zeros((n, G, G), bool)
    for i in range(n):
        rp = rocks[i][rock_act[i]]
        rock_grid[i, rp[:, 0], rp[:, 1]] = True
    ar = np.arange(n)
    for step in range(cap + 1):
        live = ~done
        if not live.any():
            break
        L = np.flatnonzero(live)
        det, j = _detect(pos[L], items[L], act[L], r, G)
        for k in np.flatnonzero(det):
            i = L[k]; q = items[i, j[k]]
            steps[i] = t[i] + int(np.abs(q - pos[i]).sum())
            expo[i] += _walk_exposure(pos[i], q, rocks[i][rock_act[i]])
            done[i] = True
        mv = L[~det]
        if step == cap or mv.size == 0:
            continue
        d = MOVES[rng.integers(0, 4, mv.size)]
        pos[mv] = np.clip(pos[mv] + d, 0, G - 1)
        t[mv] += 1
        expo[mv] += rock_grid[mv, pos[mv, 0], pos[mv, 1]]
    capped = ~done | (steps > cap)
    return np.minimum(steps, cap), capped, expo


def warmth_search(start, field, thr, rocks, rock_act, seed):
    n, G, _ = field.shape
    rng = np.random.default_rng(seed)
    amb = field.reshape(n, -1).min(1)
    pos = start.astype(int).copy()
    t = np.zeros(n, int); done = np.zeros(n, bool); expo = np.zeros(n, int)
    rock_grid = np.zeros((n, G, G), bool)
    for i in range(n):
        rp = rocks[i][rock_act[i]]
        rock_grid[i, rp[:, 0], rp[:, 1]] = True
    ar = np.arange(n)
    for step in range(CAP + 1):
        here = field[ar, pos[:, 0], pos[:, 1]]
        done |= here > 0.0
        live = np.flatnonzero(~done)
        if live.size == 0 or step == CAP:
            break
        p = pos[live]
        cells = np.clip(p[:, None, :] + STENCIL[None], 0, G - 1)                 # clamp, as the sensor
        vals = field[live[:, None], cells[..., 0], cells[..., 1]]                 # [m,5]
        felt = (vals >= amb[live, None] + thr).any(1)
        nb = p[:, None, :] + STENCIL[None, 1:]                                    # four neighbours
        inb = ((nb >= 0) & (nb < G)).all(-1)
        nbc = np.clip(nb, 0, G - 1)
        nv = np.where(inb, field[live[:, None], nbc[..., 0], nbc[..., 1]], -np.inf)
        best = nv.argmax(1)
        climb = felt & (nv[np.arange(live.size), best] > vals[:, 0])
        newp = np.where(climb[:, None], nbc[np.arange(live.size), best],
                        np.clip(p + MOVES[rng.integers(0, 4, live.size)], 0, G - 1))
        pos[live] = newp; t[live] += 1
        expo[live] += rock_grid[live, newp[:, 0], newp[:, 1]]
    return t, ~done, expo


def warmth_memory(Z, G, n_per_reset=20, seed=0):
    """Revision 2 / 2a warmth trip with memory: BFS walking distance around rocks and fires from random
    open cells to the nearest cell > 0 C. Returns (walk [m], unreachable [m], manhattan-through [m])."""
    from collections import deque
    rng = np.random.default_rng(seed)
    F = Z["thermal_field"]; walk, unr, man = [], [], []
    for i in range(F.shape[0]):
        block = np.zeros((G, G), bool)
        for key in ("rock", "fire"):
            p = Z[f"{key}_pos"][i][Z[f"{key}_act"][i]]
            block[p[:, 0], p[:, 1]] = True
        bush = np.zeros((G, G), bool)
        b = Z["bush_pos"][i][Z["bush_act"][i]]; bush[b[:, 0], b[:, 1]] = True
        warm = (F[i] > 0.0) & ~block
        # multi-source BFS from every warm cell (four moves, blocked cells never entered)
        dist = np.full((G, G), -1, int); q = deque()
        for r, c in np.argwhere(warm):
            dist[r, c] = 0; q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in MOVES:
                rr, cc = r + dr, c + dc
                if 0 <= rr < G and 0 <= cc < G and dist[rr, cc] < 0 and not block[rr, cc]:
                    dist[rr, cc] = dist[r, c] + 1; q.append((rr, cc))
        wc = np.argwhere(F[i] > 0.0)
        for _ in range(n_per_reset):
            p = (int(rng.integers(1, G - 1)), int(rng.integers(1, G - 1)))
            if block[p] or bush[p]:
                continue
            man.append(int(np.abs(wc - np.array(p)).sum(1).min()) if len(wc) else np.nan)
            walk.append(int(dist[p])); unr.append(bool(dist[p] < 0))
    return np.array(walk), np.array(unr), np.array(man, float)


def stats(x, capped, expo):
    x = np.asarray(x, float); n = x.size
    rng = np.random.default_rng(0)
    bs = rng.integers(0, n, (200, n))
    med_b = np.median(x[bs], 1)
    return dict(n=int(n), median=float(np.median(x)), mean=float(x.mean()),
                mean_ci95=[float(x.mean() - 1.96 * x.std(ddof=1) / np.sqrt(n)), float(x.mean() + 1.96 * x.std(ddof=1) / np.sqrt(n))],
                median_ci95=[float(np.percentile(med_b, 2.5)), float(np.percentile(med_b, 97.5))],
                p90=float(np.percentile(x, 90)), capped_share=float(np.mean(capped)),
                exposure_steps_mean=float(np.mean(expo)))


def measure_layout(wdir):
    t0 = time.time()
    Z = np.load(os.path.join(wdir, "resets.npz")); info = json.load(open(os.path.join(wdir, "layout.json")))
    G = info["grid"]; start = Z["agent_pos"]
    out = dict(layout=info["layout"], grid=G, food={}, cover={}, warmth={})
    for r in RANGES:
        s, c, e = smell_search(start, Z["food_pos"], Z["food_act"], r, G, Z["rock_pos"], Z["rock_act"], seed=11)
        out["food"][str(r)] = stats(s, c, e)
        s, c, e = smell_search(start, Z["bush_pos"], Z["bush_act"], r, G, Z["rock_pos"], Z["rock_act"], seed=12)
        out["cover"][str(r)] = stats(s, c, e)
    for thr in WARM_THRESHOLDS:
        s, c, e = warmth_search(start, Z["thermal_field"], thr, Z["rock_pos"], Z["rock_act"], seed=13)
        out["warmth"][str(thr)] = stats(s, c, e)
    w, u, m = warmth_memory(Z, G)
    ok = ~u
    out["warmth_memory"] = dict(**stats(w[ok], np.zeros(ok.sum(), bool), np.zeros(ok.sum())),
                                samples=int(w.size), unreachable_share=float(u.mean()),
                                manhattan_through_mean=float(np.nanmean(m)), manhattan_through_median=float(np.nanmedian(m)),
                                definition="walking distance (4 moves, around rocks and fires) from a random open "
                                           "interior cell (not bush / rock / fire; 20 per reset, seed 0) to the "
                                           "nearest cell > 0 C; unreachable samples excluded and counted")
    # (ii) monotone in smell range (longer range must not be slower)
    viol = []
    for kind in ("food", "cover"):
        order = sorted(RANGES)                                  # 3, 5, 8, 20
        for a_, b_ in zip(order[:-1], order[1:]):
            A, B = out[kind][str(a_)], out[kind][str(b_)]
            if B["mean_ci95"][0] > A["mean_ci95"][1]:
                viol.append(f"{kind} mean r{b_} > r{a_}")
            if B["median_ci95"][0] > A["median_ci95"][1]:
                viol.append(f"{kind} median r{b_} > r{a_}")
    out["monotone_violations"] = viol
    out["seconds"] = time.time() - t0
    return out


# ---- (i) exact hitting time of the forager's own walk on an empty grid -----------------------------
def hitting_time_exact(G, target, r):
    from scipy.sparse import lil_matrix
    from scipy.sparse.linalg import spsolve
    tgt = np.array(target)
    idx = lambda p: p[0] * G + p[1]
    N = G * G; A = lil_matrix((N, N)); b = np.zeros(N)
    for i in range(G):
        for j in range(G):
            p = np.array([i, j]); k = idx(p)
            cells = p + STENCIL; inb = ((cells >= 0) & (cells < G)).all(-1)
            if (np.sqrt(((cells[inb] - tgt) ** 2).sum(-1)) <= r).any():
                A[k, k] = 1.0; b[k] = float(np.abs(p - tgt).sum()); continue
            A[k, k] = 1.0; b[k] = 1.0
            for m in MOVES:
                q = np.clip(p + m, 0, G - 1)
                A[k, idx(q)] -= 0.25
    h = spsolve(A.tocsr(), b)
    return float(h.mean())


def validate_chain():
    rows = []
    for G in (10, 15, 20):
        for target in ((G // 2, G // 2), (1, 1)):
            for r in (3, 5, 8):
                exact = hitting_time_exact(G, target, r)
                n = 20000
                rng = np.random.default_rng(G * 100 + r)
                start = np.stack([rng.integers(0, G, n), rng.integers(0, G, n)], 1)
                items = np.broadcast_to(np.array(target)[None, None, :], (n, 1, 2)).copy()
                act = np.ones((n, 1), bool)
                rocks = np.zeros((n, 0, 2), int); ra = np.zeros((n, 0), bool)
                s, c, _ = smell_search(start, items, act, r, G, rocks, ra, seed=G + r, cap=50 * CAP)
                sim = float(s.mean()); rel = abs(sim - exact) / exact if exact else abs(sim)
                rows.append(dict(grid=G, target=list(target), range=r, exact=exact, simulated=sim, rel_error=rel,
                                 capped=float(c.mean()), pass_=bool(rel <= 0.10)))
    return dict(checks=rows, pass_=all(x["pass_"] for x in rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--worlds", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    val = validate_chain()
    print(f"[forager] (i) hitting-time check pass={val['pass_']}: max rel error "
          f"{max(x['rel_error'] for x in val['checks']):.3f}", flush=True)
    dirs = sorted(d for d in glob.glob(os.path.join(a.worlds, "*")) if os.path.exists(os.path.join(d, "resets.npz")))
    res = {}
    with ProcessPoolExecutor(a.procs) as ex:
        for o in ex.map(measure_layout, dirs):
            res[o["layout"]] = o
            f = o["food"]
            print(f"{o['layout']:28s} food mean " + " ".join(f"r{r}:{f[str(r)]['mean']:.1f}" for r in RANGES)
                  + f"  cover r3 {o['cover']['3']['mean']:.1f}  warmth(5C) {o['warmth']['5.0']['mean']:.1f}"
                  + f"  warmth memory {o['warmth_memory']['mean']:.2f} (unreach {o['warmth_memory']['unreachable_share']:.3f})"
                  + (f"  VIOL {o['monotone_violations']}" if o["monotone_violations"] else "") + f" ({o['seconds']:.0f}s)",
                  flush=True)
    meas = json.load(open(os.path.join(ROOT, "results/analysis/internal_state_interactions/world_measurements.json")))
    today = res.get("g10f1to4b12_od")
    sanity = None
    if today:
        sanity = dict(forager_median_food_search_r20=today["food"]["20"]["median"],
                      forager_mean_food_search_r20=today["food"]["20"]["mean"],
                      measured_median_food_trip=meas["trip_steps"]["food"]["median"],
                      measured_mean_food_trip=meas["trip_steps"]["food"]["mean"],
                      note="sanity only (plan iii): the balance study's trip is from a random open cell to the "
                           "nearest food; the forager starts at the reset's agent start")
    out = dict(design="STUDY_PLAN.md Part 3 (Revisions 1, 1a, 2, 2a): search times on real resets", cap=CAP,
               ranges=list(RANGES), warmth_thresholds=list(WARM_THRESHOLDS),
               validation=dict(i_hitting_time=val,
                               ii_monotone=dict(violations={k: v["monotone_violations"] for k, v in res.items() if v["monotone_violations"]},
                                                pass_=not any(v["monotone_violations"] for v in res.values())),
                               iii_sanity=sanity),
               layouts=res, seconds=time.time() - t0)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["validation"]["ii_monotone"]), json.dumps(sanity))


if __name__ == "__main__":
    main()
