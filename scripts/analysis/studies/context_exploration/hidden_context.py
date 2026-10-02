"""Part 1 of the context-exploration study: do today's level-05 agents adapt to the one hidden danger?

Plain-language purpose: the number of ambushers (hidden predators that have no smell) changes from
episode to episode, 2 to 12. If an agent infers "this episode is dangerous", then at the same body
state and the same point in the episode it should hide more when there are many ambushers than when
there are few. This script measures that gap on the Wave-2 level-05 recordings of both agents (the
ordinary agent and the full modulator agent), and the same for the hunting-predator count, which
the agent can smell (reported as "sensed threat", never as hidden).

Design (docs/experiments/active/context_exploration/STUDY_PLAN.md, Part 1, Revision 1):
  hidden axis    ambushers per episode = res_allocated & (res_type == 1); low 2-5 vs high 9-12
  sensed axis    hunting predators 0 / 1 / 2 (animal_active of the predator slots); also matched on
                 the recorded animal smell (sum over the five sampled cells of the animal channels
                 1 and 2 of obs_true), in quintiles fixed on block 0 of both agents
  matching       true injury (0-20 ... 80-100) x food energy (0-50 ... 150-200) x time in episode
                 (steps 1-50, 51-150, 151-300, > 300); a cell counts if both contexts have >= 200
                 steps; gap = mean over counted cells weighted by the pooled step count.
                 Sensitivity: time replaced by steps since the last hit (0-10, 11-50, > 50, none yet)
  measures       share of steps in cover (primary), eating, in the open away from cover (not in a
                 bush and Manhattan distance >= 2 from every bush); steps before the first bite per
                 episode, matched on starting food energy (bins of 40)
  interval       95 % bootstrap over episodes, 1,000 resamples, as Poisson(1) episode weights
                 seeded by the episode seed -- the two agents share seed_base, so each episode gets
                 the same weight in both and the agent difference is paired per episode
  reading        adapts: gap >= 5 points and interval excludes 0; does not adapt: upper bound < 5;
                 undecided otherwise (cover share, per agent; reported for the other measures)

  python hidden_context.py --procs 16 --out results/analysis/context_exploration/part1_hidden_context.json
"""
import argparse, glob, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "internal_state_interactions"))
from measure_world import RUNS                      # noqa: E402  (ordinary agent first)

STORE = os.path.join(ROOT, "results/trajectories_basicq2_w2")
R = 1000                                            # bootstrap resamples
MIN_STEPS = 200
MEASURES = ("steps", "cover", "eat", "open")
OLF0, V = 9, 5                                      # olfaction block start in the 58-wide observation
ANIMAL_CH = (1, 2)
SINCE_LABELS = ["0-10", "11-50", ">50", "no hit yet"]
TIME_LABELS = ["1-50", "51-150", "151-300", ">300"]


def store_dir(run):
    d = glob.glob(os.path.join(STORE, run, "*", "*"))
    assert len(d) == 1, d
    return d[0]


def manifest(run):
    return json.load(open(os.path.join(store_dir(run), "_manifest.json")))


def animal_smell(obs_true):
    cols = [OLF0 + V * c + ch for c in range(5) for ch in ANIMAL_CH]
    return obs_true[:, cols].sum(1)


def read_block(steps_path, cols):
    import pyarrow.parquet as pq
    return pq.read_table(steps_path, columns=cols)


def smell_edges(n_blocks=1):
    import pyarrow.parquet as pq
    xs = []
    for run in RUNS:
        for f in sorted(glob.glob(os.path.join(store_dir(run), "steps_*.parquet")))[:n_blocks]:
            ot = pq.read_table(f, columns=["obs_true"]).column("obs_true").combine_chunks()
            xs.append(animal_smell(np.asarray(ot.flatten()).reshape(len(ot), -1)))
    x = np.concatenate(xs)
    q = np.quantile(x, [0.2, 0.4, 0.6, 0.8])
    return np.unique(q).tolist(), dict(n_steps=int(x.size), share_zero=float((x == 0).mean()))


def _poisson_weights(seeds):
    W = np.empty((len(seeds), R + 1), np.float32); W[:, 0] = 1.0
    for i, s in enumerate(seeds):
        W[i, 1:] = np.random.default_rng([int(s), 7]).poisson(1.0, R)
    return W


def _group_sums(ep, col, vals, ncol, W):
    """sum over steps of vals[:, m] into (episode, col) then weighted by W -> (ncol*len(MEASURES), R+1)."""
    from scipy import sparse
    n_ep = W.shape[0]; out = []
    for m in range(vals.shape[1]):
        E = sparse.coo_matrix((vals[:, m].astype(np.float32), (ep, col)), shape=(n_ep, ncol)).tocsr()
        out.append(np.asarray((E.T @ W)))
    return np.concatenate(out, 0)              # measure-major: m * ncol + col


def work(args):
    run_i, steps_path, edges = args
    import pyarrow.parquet as pq
    t0 = time.time()
    ep_path = steps_path.replace("steps_", "episodes_")
    et = pq.read_table(ep_path, columns=["episode_seed", "animal_active", "res_allocated", "obs_active", "length"])
    seeds = et.column("episode_seed").to_numpy()
    n_ep = len(seeds)
    aa = np.asarray(et.column("animal_active").combine_chunks().flatten()).reshape(n_ep, -1)
    ra = np.asarray(et.column("res_allocated").combine_chunks().flatten()).reshape(n_ep, -1)
    oa = np.asarray(et.column("obs_active").combine_chunks().flatten()).reshape(n_ep, -1)
    man = manifest(RUNS[run_i])
    pred_slots = np.array([c == "predator" and b == "hunt" for c, b in zip(man["animal_classes"], man["animal_behaviours"])])
    res_type = np.array(man["res_type"]); bush_slots = np.array(man["obs_hides_agent"])
    n_pred = aa[:, pred_slots].sum(1)
    n_amb = (ra & (res_type == 1)[None, :]).sum(1)
    band = np.where((n_amb >= 2) & (n_amb <= 5), 0, np.where((n_amb >= 9) & (n_amb <= 12), 1, -1))

    st = pq.read_table(steps_path, columns=["episode_seed", "t", "nutrition", "injury_level", "agent_in_bush",
                                            "ate_food", "damage", "obs_true", "obs_row", "obs_col",
                                            "agent_row", "agent_col"])
    es = st.column("episode_seed").to_numpy(); t = st.column("t").to_numpy().astype(np.int64)
    n = len(es)
    assert np.all(np.diff(es) >= 0), "steps not grouped by episode"
    ep = np.searchsorted(seeds, es); assert np.array_equal(seeds[ep], es)
    start = np.r_[True, es[1:] != es[:-1]]
    assert np.all(t[start] == 0) and np.all(np.diff(t)[~start[1:]] == 1), "t not consecutive within episodes"
    nut = st.column("nutrition").to_numpy(); inj = st.column("injury_level").to_numpy()
    bush = st.column("agent_in_bush").to_numpy(zero_copy_only=False).astype(bool)
    ate = st.column("ate_food").to_numpy(zero_copy_only=False).astype(bool)
    dmg = st.column("damage").to_numpy()
    ot = st.column("obs_true").combine_chunks()
    smell = animal_smell(np.asarray(ot.flatten()).reshape(n, -1)); del ot
    # bush cells per episode from the episode's first row (obstacles do not move)
    first = np.flatnonzero(start)
    orow = np.asarray(st.column("obs_row").combine_chunks().flatten()).reshape(n, -1)[first]
    ocol = np.asarray(st.column("obs_col").combine_chunks().flatten()).reshape(n, -1)[first]
    ar = st.column("agent_row").to_numpy().astype(np.int64); ac = st.column("agent_col").to_numpy().astype(np.int64)
    bmask = (oa & bush_slots[None, :])[ep[first]]                                 # [episodes-in-order, 25]
    ep_order = np.cumsum(start) - 1                                             # step -> episode-in-order
    dmin = np.full(n, 99)
    for j in np.flatnonzero(bush_slots):
        d = np.abs(ar - orow[ep_order, j]) + np.abs(ac - ocol[ep_order, j])
        dmin = np.where(bmask[ep_order, j], np.minimum(dmin, d), dmin)
    open_away = (~bush) & (dmin >= 2)

    # bins
    ib = np.clip((inj // 20).astype(int), 0, 4)
    fb = np.clip((nut // 50).astype(int), 0, 3)
    step = t + 1
    tb = np.digitize(step, [51, 151, 301])
    hit = dmg > 0
    idx = np.arange(n)
    last_hit_row = np.maximum.accumulate(np.where(hit, idx, -1))
    ep_start_row = np.maximum.accumulate(np.where(start, idx, 0))
    has_hit = last_hit_row >= ep_start_row
    since = t - t[np.maximum(last_hit_row, 0)]
    sb = np.where(has_hit, np.digitize(since, [11, 51]), 3)
    kb = np.digitize(smell, edges)                                              # 0..len(edges)
    nk = len(edges) + 1
    cell = (ib * 4 + fb) * 4 + tb                                               # 80
    cell_s = (ib * 4 + fb) * 4 + sb
    vals = np.stack([np.ones(n), bush, ate, open_away], 1).astype(np.float32)
    W = _poisson_weights(seeds)
    bs = band[ep]; ps = n_pred[ep]
    out = {}
    ma = bs >= 0
    out["amb"] = _group_sums(ep[ma], bs[ma] * 80 + cell[ma], vals[ma], 160, W)
    out["amb_since"] = _group_sums(ep[ma], bs[ma] * 80 + cell_s[ma], vals[ma], 160, W)
    out["pred"] = _group_sums(ep, ps * 80 + cell, vals, 240, W)
    out["pred_smell"] = _group_sums(ep, (ps * 80 + cell) * nk + kb, vals, 240 * nk, W)
    out["amb_raw"] = _group_sums(ep[ma], bs[ma], vals[ma], 2, W)
    out["pred_raw"] = _group_sums(ep, ps, vals, 3, W)
    # first bite, per episode, matched on starting food energy (bins of 40)
    fbite = np.full(n_ep, -1)
    bite_rows = np.flatnonzero(ate)
    fr = np.full(n_ep, n + 1); np.minimum.at(fr, ep[bite_rows], bite_rows)
    fbite[fr <= n] = t[fr[fr <= n]]
    s0 = np.zeros(n_ep); s0[ep[first]] = nut[first]
    sbin = np.clip((s0 // 40).astype(int), 0, 4)
    e_ok = band >= 0
    col = band[e_ok] * 5 + sbin[e_ok]
    fvals = np.stack([np.ones(e_ok.sum()), (fbite[e_ok] >= 0), np.maximum(fbite[e_ok], 0)], 1)
    from scipy import sparse
    fb_out = []
    for m in range(3):
        E = sparse.coo_matrix((fvals[:, m], (np.flatnonzero(e_ok), col)), shape=(n_ep, 10)).tocsr()
        fb_out.append(np.asarray(E.T @ W))
    out["first_bite"] = np.concatenate(fb_out, 0)
    info = dict(episodes=n_ep, steps=n, amb_band_counts=np.bincount(band + 1, minlength=3).tolist(),
                pred_counts=np.bincount(n_pred, minlength=3).tolist(), seeds_first=int(seeds[0]),
                seconds=time.time() - t0)
    return run_i, os.path.basename(steps_path), out, info


# ---------------------------------------------------------------------------------------------------------
def gap_from(S, ncell, ctx_a, ctx_b, nm, sel=None):
    """S: (len(MEASURES) * nctx * ncell, R+1). Returns per-measure gap arrays (R+1,) of rate(b) - rate(a),
    over cells with >= MIN_STEPS steps in both contexts (full sample), weighted by pooled full-sample steps."""
    nctx = S.shape[0] // (len(MEASURES) * ncell)
    X = S.reshape(len(MEASURES), nctx, ncell, -1)
    st_a, st_b = X[0, ctx_a], X[0, ctx_b]
    ok = (st_a[:, 0] >= MIN_STEPS) & (st_b[:, 0] >= MIN_STEPS)
    w = (st_a[ok, 0] + st_b[ok, 0])
    res = {}
    for mi, m in enumerate(MEASURES[1:], 1):
        with np.errstate(invalid="ignore", divide="ignore"):
            ra = X[mi, ctx_a][ok] / st_a[ok]; rb = X[mi, ctx_b][ok] / st_b[ok]
        g = rb - ra
        good = np.isfinite(g)
        gw = np.where(good, g, 0.0) * w[:, None]
        res[m] = (gw.sum(0) / (good * w[:, None]).sum(0)) * 100.0            # percentage points
    return res, dict(cells_counted=int(ok.sum()), cells_total=int(ncell),
                     steps_in_counted_cells=int(w.sum()),
                     steps_total=int(st_a[:, 0].sum() + st_b[:, 0].sum()))


def summarise(g):
    lo, hi = np.percentile(g[1:], [2.5, 97.5])
    return dict(gap_points=float(g[0]), ci95=[float(lo), float(hi)])


def reading(s):
    if s["gap_points"] >= 5 and s["ci95"][0] > 0:
        return "adapts"
    if s["ci95"][1] < 5:
        return "does not adapt"
    return "undecided"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--blocks", type=int, default=200)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    mans = [manifest(r) for r in RUNS]
    seed_bases = [m["seed_base"] for m in mans]
    paired = len(set(seed_bases)) == 1
    edges, edge_info = smell_edges()
    print(f"[part1] seed_base {seed_bases} paired={paired}; smell quintile edges {edges}", flush=True)
    files = {i: sorted(glob.glob(os.path.join(store_dir(r), "steps_*.parquet")))[:a.blocks] for i, r in enumerate(RUNS)}
    avail = {i: len(glob.glob(os.path.join(store_dir(r), "steps_*.parquet"))) for i, r in enumerate(RUNS)}
    jobs = [(i, f, edges) for i in files for f in files[i]]
    acc = {i: {} for i in files}; info = {i: [] for i in files}; firsts = {i: {} for i in files}
    with Pool(a.procs) as pool:
        for k, (i, name, out, inf) in enumerate(pool.imap_unordered(work, jobs)):
            for g, v in out.items():
                acc[i][g] = acc[i].get(g, 0) + v
            info[i].append(inf); firsts[i][name] = inf["seeds_first"]
            if k % 20 == 0:
                print(f"  {k + 1}/{len(jobs)} blocks ({time.time() - t0:.0f}s)", flush=True)
    if paired:
        assert firsts[0] == firsts[1], "episode seeds differ between the two stores"
    nk = len(edges) + 1
    res = dict(design="STUDY_PLAN.md Part 1 (Revision 1)", runs=RUNS, seed_base=seed_bases, paired=paired,
               blocks_used={RUNS[i]: len(files[i]) for i in files}, blocks_available={RUNS[i]: avail[i] for i in files},
               bootstrap=f"{R} Poisson(1) episode-weight resamples seeded by episode seed (paired across agents)",
               min_steps_per_cell=MIN_STEPS, smell_quintile_edges=edges, smell_edge_source=edge_info,
               open_away_definition="not in a bush and Manhattan distance >= 2 from every active bush",
               per_agent={})
    gaps = {}
    for i, run in enumerate(RUNS):
        A = acc[i]; tag = "ordinary" if i == 0 else "modulator"
        n_ep = sum(x["episodes"] for x in info[i])
        amb_counts = np.sum([x["amb_band_counts"] for x in info[i]], 0)
        pc = np.sum([x["pred_counts"] for x in info[i]], 0)
        prim, cov = gap_from(A["amb"], 80, 0, 1, "amb")
        sens, cov_s = gap_from(A["amb_since"], 80, 0, 1, "amb")
        gaps[i] = prim
        # raw (unmatched)
        raw = A["amb_raw"].reshape(len(MEASURES), 2, -1)
        raw_rates = {m: [float(raw[mi, c, 0] / raw[0, c, 0] * 100) for c in (0, 1)] for mi, m in enumerate(MEASURES) if mi}
        # predator axis
        pred = {}
        for (ca, cb) in ((0, 1), (0, 2), (1, 2)):
            g1, c1 = gap_from(A["pred"], 80, ca, cb, "p")
            g2, c2 = gap_from(A["pred_smell"], 80 * nk, ca, cb, "ps")
            pred[f"{cb}_minus_{ca}"] = dict(matched_body_time={m: summarise(v) for m, v in g1.items()}, coverage=c1,
                                            matched_body_time_smell={m: summarise(v) for m, v in g2.items()},
                                            coverage_smell=c2)
        praw = A["pred_raw"].reshape(len(MEASURES), 3, -1)
        # first bite
        F = A["first_bite"].reshape(3, 2, 5, -1)                                # (n, n_bite, sum_t) x band x bin
        ok = (F[1, 0, :, 0] >= MIN_STEPS) & (F[1, 1, :, 0] >= MIN_STEPS)
        with np.errstate(invalid="ignore", divide="ignore"):
            mt = F[2] / F[1]
        wf = F[1, 0, ok, 0] + F[1, 1, ok, 0]
        fg = ((mt[1, ok] - mt[0, ok]) * wf[:, None]).sum(0) / wf.sum()
        first_bite = dict(gap_steps_high_minus_low=summarise(fg), bins_counted=int(ok.sum()),
                          start_energy_bins=["0-40", "40-80", "80-120", "120-160", "160-200"],
                          mean_steps_per_bin={"low": mt[0, :, 0].tolist(), "high": mt[1, :, 0].tolist()},
                          episodes_per_bin={"low": F[0, 0, :, 0].tolist(), "high": F[0, 1, :, 0].tolist()},
                          no_bite_share={"low": float(1 - F[1, 0, :, 0].sum() / F[0, 0, :, 0].sum()),
                                         "high": float(1 - F[1, 1, :, 0].sum() / F[0, 1, :, 0].sum())},
                          note="mean over episodes with at least one bite; min 200 such episodes per band and bin")
        summ = {m: summarise(v) for m, v in prim.items()}
        res["per_agent"][tag] = dict(
            run=run, episodes=int(n_ep), ambusher_band_episodes=dict(excluded_6to8=int(amb_counts[0]), low_2to5=int(amb_counts[1]),
                                                                    high_9to12=int(amb_counts[2])),
            predator_count_episodes=pc.tolist(),
            hidden_axis=dict(matched_body_time={m: dict(**s, reading=reading(s)) for m, s in summ.items()},
                             coverage=cov, primary_reading_cover=reading(summ["cover"]),
                             sensitivity_since_last_hit={m: dict(**summarise(v), reading=reading(summarise(v))) for m, v in sens.items()},
                             coverage_since_last_hit=cov_s, since_hit_bins=SINCE_LABELS,
                             raw_unmatched_share_points=dict(low=[raw_rates[m][0] for m in raw_rates], high=[raw_rates[m][1] for m in raw_rates],
                                                             measures=list(raw_rates)),
                             first_bite=first_bite),
            sensed_threat_axis=dict(gaps=pred, raw_share_points={m: [float(praw[mi, c, 0] / praw[0, c, 0] * 100) for c in range(3)]
                                                                for mi, m in enumerate(MEASURES) if mi}),
            block_seconds=float(np.mean([x["seconds"] for x in info[i]])))
    if paired:
        res["agent_difference_modulator_minus_ordinary"] = {m: summarise(gaps[1][m] - gaps[0][m]) for m in gaps[0]}
    res["seconds"] = time.time() - t0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    for tag, v in res["per_agent"].items():
        h = v["hidden_axis"]["matched_body_time"]
        print(tag, {m: (round(x["gap_points"], 2), [round(c, 2) for c in x["ci95"]], x["reading"]) for m, x in h.items()})
    print(f"[part1] wrote {a.out} ({res['seconds']:.0f}s)")


if __name__ == "__main__":
    main()
