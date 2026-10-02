#!/usr/bin/env python3
"""sweep.py - one pass over each cell's trajectory store -> per-episode arrays and cross-tables.

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), B1-B3, B6,
File Changes "sweep.py".

    P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
    nice -n 19 $P scripts/analysis/basic_behaviour/sweep.py \
        --population results/analysis/basic_behaviour/hvsmell/population.json \
        --out-root /abs/path/results/analysis/basic_behaviour/hvsmell [--cells L ...] [--workers 3]

Writes, per completed cell of the population manifest:
    <cell>/episodes.npz     every factor (f__<name>), every target's successes (y__<target>), the
                            trials (n_steps), per-declaration counts (cnt__<decl>), the rabbit smell
                            on the evidence scale (rab_smell_llr), survival (length) and the raw
                            per-episode sums the legacy script keeps (same keys, same arithmetic)
    <cell>/xtab.npz         cross-tables conditioned on row t-1 (plan A6 / B6)
    <cell>/inventory.json   targets available / unavailable, factors, audit rows, slot map, scent spec
    <cell>/_provenance.json run, stores, checkpoint, source sha256s, git HEAD, seconds

Worlds with water (docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md) add: the pond replayed
from each episode's seed, the D3 integrity checks on every store (hard stop on any exception),
y__pond / hyd0 / hyd_sum1 / d_pond0 / pond_corner, the hydration x nutrition cross-tables
(hyd_nut__*, and hyd_nut_onset__pond binned at bout onset), inventory "water" and "water_checks".
$BB_DATA_ROOT (D13): data read from there, outputs only under its basic_behaviour/_water_dev/.

The per-episode arithmetic copies `hiding_drivers.aggregate()` primitive for primitive
(np.add.reduceat over episode starts per shard, np.bincount with minlength, float64 casts of the
same columns, the same mean_over) - the a01 byte-identity gate is what proves it.

GUARDS: --out-root absolute and under results/analysis/basic_behaviour/; the hv blinding guard
(readings.require_yardstick_for); outputs on disk are refused unless --reuse-cache, and then only if
run, stores and source hashes equal the recorded ones (the stale-cache trap).
Runs LOCALLY only (statsmodels / env drift on the lab nodes, Known Bugs).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry as REG                                                  # noqa: E402

ROOT, A_DIR = REG.ROOT, REG.A_DIR
sys.path.insert(0, os.path.join(A_DIR, "studies", "hypervigilance"))
import readings as RD                                                   # noqa: E402
from hiding_drivers import shard_files, NEAR_D, INJ_EDGES, NUT_EDGES    # noqa: E402
from env import listcol                                                 # noqa: E402

BB_ROOT = REG.BB_ROOT                     # under $BB_DATA_ROOT/.../_water_dev when that is set (D13)
DATA = REG.DATA_ROOT                      # where runs and stores are read from
SWEEP_SOURCES = ["scripts/analysis/basic_behaviour/registry.py",
                 "scripts/analysis/basic_behaviour/sweep.py",
                 "scripts/analysis/core/env.py", "scripts/analysis/hiding_drivers.py"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def source_hashes(rel):
    return {p: sha256(os.path.join(ROOT, p)) for p in rel}


def git_head():
    try:
        return subprocess.run(["git", "--no-optional-locks", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:                                              # noqa: BLE001
        return f"unavailable ({e!r})"


def guard_out_root(path):
    if not os.path.isabs(path):
        raise SystemExit(f"--out-root must be an absolute path, got {path!r}")
    out, par = os.path.realpath(path), os.path.realpath(BB_ROOT)
    if not out.startswith(par + os.sep):
        raise SystemExit(f"--out-root {out} is not under {par}")
    return out


def store_manifest(stores):
    mans = [json.load(open(os.path.join(DATA, s, "_manifest.json"))) for s in stores]
    keys = ["animal_classes", "animal_tags", "obstacle_names", "res_type", "observation_breakdown",
            "dims", "obs_precision", "env_fp"]
    for m in mans[1:]:
        for k in keys:
            if m.get(k) != mans[0].get(k):
                raise SystemExit(f"stores of one run disagree on {k}: {stores}")
    return mans[0], sum(int(m["n_episodes"]) for m in mans)


def step_columns(stores):
    import pyarrow.parquet as pq
    f = shard_files([os.path.join(DATA, s) for s in stores], "steps")[0]
    return [x.name for x in pq.read_schema(f)]


# ------------------------------------------------------------------------------------ describe ----
def describe(c: dict) -> dict:
    """Everything the sweep needs to know about one cell, from config + store manifest only."""
    import yaml
    cfg = yaml.safe_load(open(os.path.join(DATA, c["run"], "models", "config.yaml")))
    man, n_ep = store_manifest(c["stores"])
    S = REG.slots(cfg, man)
    th = cfg.get("thermal") or {}
    water_on = REG.water_enabled(cfg)
    params = REG.rebuild_params(cfg) if (th.get("enabled") or water_on) else None
    obs = REG.obs_indices(cfg, man, params)
    thermo = REG.thermal_info(cfg, params) if th.get("enabled") else None
    cols = step_columns(c["stores"])
    T = REG.targets(cfg, man, cols, obs, thermo)
    F = REG.factors(cfg, man, obs, thermo)
    REG.add_thermal_consequence(F, T["warm_cell"]["available"])
    REG.add_water_factors(F, cfg, T)
    rows = REG.audit(cfg, F, thermo)
    try:
        spec = REG.ENV.scent_spec(cfg)
    except SystemExit as e:
        raise SystemExit(f"{c['label']}: {e}")
    water = REG.water_info(cfg, params) if water_on else None
    return dict(cfg=cfg, man=man, n_ep_manifest=n_ep, S=S, obs=obs, thermo=thermo, cols=cols, T=T,
                F=F, audit=rows, spec=spec, m5=REG.m5_helpers(F, S), water=water,
                params=params if water_on else None)


# ----------------------------------------------------------------------------------- aggregate ----
def aggregate(stores, d: dict, verbose=True) -> tuple[dict, dict]:
    """One sweep of the step table -> (per-episode arrays, run cross-tables).

    Mirrors hiding_drivers.aggregate() operation for operation for every array it shares with it.
    """
    import pyarrow.parquet as pq
    S, F, T, spec, obs, thermo = d["S"], d["F"], d["T"], d["spec"], d["obs"], d["thermo"]
    stores = [os.path.join(DATA, s) for s in stores]
    kinds = {f["kind"] for f in F}
    trait_cols = sorted({f["column"] for f in F if f["kind"] == "trait"}
                        | ({"animal_detect_sampled"} if d["m5"] and "skip" not in d["m5"] else set()))
    epf = shard_files(stores, "episodes")
    ep = pq.read_table(epf, columns=["episode_seed", "length", "termination_reason", "animal_active",
                                     "obs_active", "res_allocated", "animal_property_sampled"]
                       + trait_cols)
    o = np.argsort(ep.column("episode_seed").to_numpy())
    seed = ep.column("episode_seed").to_numpy()[o]
    seed0, nep = int(seed[0]), len(seed)
    if seed.max() - seed0 + 1 != nep:
        raise SystemExit("episode seeds are not contiguous; this reader assumes they are")
    na, nobs, nres = S["n_animal"], S["n_obs"], S["n_res"]
    Lc = lambda c, w, dt=np.float64: listcol(ep.column(c), w)[o].astype(dt)
    act, oa, ra = Lc("animal_active", na, bool), Lc("obs_active", nobs, bool), Lc("res_allocated", nres, bool)
    prop = listcol(ep.column("animal_property_sampled"), na * len(spec.pred_mean))[o] \
        .astype(np.float64).reshape(nep, na, -1)
    mean_over = lambda X, M: np.where(M.sum(1) > 0, (X * M).sum(1) / np.maximum(M.sum(1), 1), np.nan)
    P, R = S["pred"], S["neutral"]
    E = {"seed": seed, "term": ep.column("termination_reason").to_numpy(zero_copy_only=False)[o],
         "length": ep.column("length").to_numpy()[o].astype(np.int64)}
    ent = {e["tag"]: e for e in S["entities"]}
    for e in S["entities"]:
        E[f"cnt__{e['tag']}"] = act[:, e["slots"]].sum(1).astype(float)
    for ob in S["obstacles"]:
        E[f"cnt__obs__{ob['name']}"] = oa[:, ob["slots"]].sum(1).astype(float)
    for r in S["resources"]:
        E[f"cnt__res__{r['name']}"] = ra[:, r["slots"]].sum(1).astype(float)
    traits = {}
    for f in F:
        if f["kind"] == "trait":
            sl = ent[f["tag"]]["slots"]
            traits[f["name"]] = mean_over(Lc(f["column"], na)[:, sl], act[:, sl])
        elif f["kind"] in ("smell", "intensity"):
            sl = ent[f["tag"]]["slots"]
            fn = spec.statistic if f["kind"] == "smell" else spec.intensity
            traits[f["name"]] = mean_over(fn(prop[:, sl]), act[:, sl])
    # smell on the evidence scale + per-channel means, for every declaration (screening, F6)
    for e in S["entities"]:
        sl = e["slots"]
        E[f"smell__{e['tag']}"] = mean_over(spec.statistic(prop[:, sl]), act[:, sl])
        for ch in spec.channels:
            E[f"smellch__{e['tag']}__{ch}"] = mean_over(prop[:, sl, ch], act[:, sl])
    c2 = next((e for e in S["entities"] if not e["predator"]), None)
    E["rab_smell_llr"] = spec.llr(E[f"smell__{c2['tag']}"]) if c2 else np.full(nep, np.nan)
    m5 = d["m5"]
    if m5 and "skip" not in m5:
        sl = ent[m5["tag"]]["slots"]
        pa1 = act[:, sl]
        det = Lc("animal_detect_sampled", na)[:, sl]
        E["detect_max"] = np.where(pa1.sum(1) > 0,
                                   np.nanmax(np.where(pa1, det, np.nan), axis=1), np.nan)
        E["detect_min"] = np.where(pa1.sum(1) > 0,
                                   np.nanmin(np.where(pa1, det, np.nan), axis=1), np.nan)

    z = lambda: np.zeros(nep)
    G = {k: z() for k in ["n_rows", "n_steps", "bush_steps", "inj0", "nut0", "sat0", "arow0", "acol0",
                          "inj_sum", "inj_max", "nut_sum", "dmg_sum", "n_ate", "n_rest", "d_bush0",
                          "d_pred0", "n_pred_near", "n_rab_near",
                          "y_eat", "y_near_pred", "y_near_rab", "n_both_near"]}
    IB, NB = np.zeros((nep, 4)), np.zeros((nep, 4))
    thermal_on = obs is not None and (T["warm_cell"]["available"] or "start_body_temp" in
                                      {f["name"] for f in F} or "ambient_temp" in {f["name"] for f in F})
    if thermal_on:
        for k in ("bt0", "tsq0", "bt_sum1", "y_warm", "ambient_den"):
            G[k] = z()
        G["ambient"] = np.full(nep, np.nan)          # stays NaN when recovery is unavailable
        Kr, wr = REG.blur_weights(thermo["sigma"], thermo["kernel_radius"], thermo["H"])
        Kc, wc = REG.blur_weights(thermo["sigma"], thermo["kernel_radius"], thermo["W"])
        heat = thermo["heat_obstacle_slots"]
        from src.environment.config_loader import _thermal_equilibrium
    avail = [t for t, v in T.items() if v["available"]]
    XT = {"inj_nut_trials": np.zeros(16), "near_trials": np.zeros(4)}
    for t_ in avail:
        XT[f"inj_nut__{t_}"] = np.zeros(16)
        XT[f"near__{t_}"] = np.zeros(4)
    # water (BASIC_BEHAVIOUR_WATER D2-D5, D8): the pond is replayed from each episode's seed
    water_on = "pond" in T and T["pond"]["available"]
    if water_on:
        PR = REG.pond_cells(d["params"], seed)
        cmask, Wd = PR["masks"], PR["W"]
        for k in ("y_pond", "hyd0", "hyd_sum1", "d_pond0"):
            G[k] = z()
        G["pond_corner"] = PR["corner"].astype(np.int64)
        hscale = obs["hydration_scale"]
        XT["hyd_nut_trials"] = np.zeros(16)
        for t_ in avail:
            XT[f"hyd_nut__{t_}"] = np.zeros(16)
        XT["hyd_nut_onset_trials"] = np.zeros(16)
        XT["hyd_nut_onset__pond"] = np.zeros(16)
        WC = {"episodes_checked": 0, "start_cell_mismatches": 0, "steps_checked": 0,
              "step_exceptions": 0, "reset_hydration_max_abs_diff": 0.0}
    cols = ["episode_seed", "t", "agent_in_bush", "injury_level", "nutrition", "damage", "ate_food",
            "rested", "agent_row", "agent_col", "obs_row", "obs_col", "animal_row", "animal_col"]
    if "start_satiation" in {f["name"] for f in F}:
        cols.append("satiation")
    if thermal_on or water_on:
        cols.append("obs_true")
    hide_slots = S["bush"]
    files = shard_files(stores, "steps")
    t0 = time.time()
    for fi, f in enumerate(files):
        tb = pq.read_table(f, columns=cols)
        sd = tb.column("episode_seed").to_numpy(); t = tb.column("t").to_numpy()
        gi = sd - seed0
        st = np.flatnonzero(t == 0); gidx = gi[st]
        if not np.array_equal(gidx, np.arange(gidx[0], gidx[0] + len(gidx))):
            raise SystemExit(f"{f}: episodes are not shard-aligned/contiguous")
        num = lambda c: tb.column(c).to_numpy(zero_copy_only=False).astype(np.float64)
        bu, inj, nut = num("agent_in_bush"), num("injury_level"), num("nutrition")
        ar, ac = num("agent_row"), num("agent_col")
        ate = num("ate_food")
        red = lambda a: np.add.reduceat(a, st)
        G["n_rows"][gidx] += np.diff(np.append(st, len(t)))
        G["inj_sum"][gidx] += red(inj); G["nut_sum"][gidx] += red(nut)
        G["dmg_sum"][gidx] += red(num("damage"))
        G["n_ate"][gidx] += red(ate); G["n_rest"][gidx] += red(num("rested"))
        G["inj_max"][gidx] = np.maximum.reduceat(inj, st)
        G["inj0"][gidx], G["nut0"][gidx] = inj[st], nut[st]
        if "satiation" in cols:
            G["sat0"][gidx] = num("satiation")[st]
        G["arow0"][gidx], G["acol0"][gidx] = ar[st], ac[st]

        AR, AC = listcol(tb.column("animal_row"), na), listcol(tb.column("animal_col"), na)
        near = (np.maximum(np.abs(AR - ar[:, None]), np.abs(AC - ac[:, None])) <= NEAR_D) \
            & act[gi]
        pn = near[:, P].any(1); rn = near[:, R].any(1) & ~pn
        rn_any = near[:, R].any(1)

        m = t >= 1
        li = gi[m] - gidx[0]; nb_ = len(gidx)
        bc = lambda w=None: np.bincount(li, weights=w, minlength=nb_)
        G["n_steps"][gidx] += bc(); G["bush_steps"][gidx] += bc(bu[m])
        G["n_pred_near"][gidx] += bc(pn[m].astype(float))
        G["n_rab_near"][gidx] += bc(rn[m].astype(float))
        G["y_eat"][gidx] += bc(ate[m])
        G["y_near_pred"][gidx] += bc(pn[m].astype(float))
        G["y_near_rab"][gidx] += bc(rn_any[m].astype(float))
        G["n_both_near"][gidx] += bc((rn_any & pn)[m].astype(float))
        ib = np.digitize(inj[m], INJ_EDGES); nbn = np.digitize(nut[m], NUT_EDGES)
        for M, Bn in ((IB, ib), (NB, nbn)):
            M[gidx] += np.bincount(li * 4 + Bn, minlength=nb_ * 4).reshape(-1, 4)
        OR, OC = listcol(tb.column("obs_row"), nobs), listcol(tb.column("obs_col"), nobs)
        a0r, a0c = ar[st][:, None], ac[st][:, None]
        ob = oa[gidx][:, hide_slots]
        db = np.where(ob, np.maximum(np.abs(OR[st][:, hide_slots] - a0r),
                                     np.abs(OC[st][:, hide_slots] - a0c)), np.inf)
        G["d_bush0"][gidx] = db.min(1) if len(hide_slots) else np.inf
        pact = act[gidx][:, P]
        dp = np.where(pact, np.maximum(np.abs(AR[st][:, P] - a0r),
                                       np.abs(AC[st][:, P] - a0c)), np.inf)
        G["d_pred0"][gidx] = dp.min(1) if len(P) else np.inf

        succ = {"bush_dwell": bu, "eating": ate, "near_rabbit": rn_any.astype(float),
                "near_predator": pn.astype(float)}
        if thermal_on:
            OT = listcol(tb.column("obs_true"), obs["D"])
            bt = OT[:, obs["body_temp"]].astype(np.float64) if obs["body_temp"] is not None else None
            th = OT[:, obs["thermo_own_cell"]].astype(np.float64)
            tsq = th + bt if obs["relative"] else th
            if bt is not None:
                G["bt0"][gidx] = bt[st]
                G["bt_sum1"][gidx] += bc(bt[m])
            G["tsq0"][gidx] = tsq[st]
            if T["warm_cell"]["available"]:
                Ts = _thermal_equilibrium(tsq, thermo["k_exchange"], thermo["k_loss"],
                                          thermo["k_metabolic"], thermo["setpoint"])
                warm = ((Ts >= thermo["setpoint"]) & (Ts <= thermo["max_temperature"])).astype(float)
                G["y_warm"][gidx] += bc(warm[m])
                succ["warm_cell"] = warm
            if thermo.get("ambient_unavailable") is None:
                r0, c0 = ar[st].astype(int), ac[st].astype(int)
                B = np.zeros(len(st))
                if heat:
                    fr, fc = OR[st][:, heat].astype(int), OC[st][:, heat].astype(int)
                    ok = oa[gidx][:, heat] & (fr >= 0) & (fr < thermo["H"]) & (fc >= 0) & (fc < thermo["W"])
                    frc, fcc = np.clip(fr, 0, thermo["H"] - 1), np.clip(fc, 0, thermo["W"] - 1)
                    B = np.where(ok, Kr[r0[:, None], frc] * Kc[c0[:, None], fcc], 0.0).sum(1) \
                        / (wr[r0] * wc[c0])
                den = 1.0 + thermo["sign"] * thermo["ratio"] * B
                G["ambient_den"][gidx] = den
                G["ambient"][gidx] = np.where(np.abs(den) > 1e-6, tsq[st] / np.where(den == 0, 1, den),
                                              np.nan)
        # cross-tables on row t-1 (plan A6 / B6)
        idx = np.flatnonzero(m); prev = idx - 1
        if (prev < 0).any() or not (np.array_equal(sd[prev], sd[idx]) and np.array_equal(t[prev] + 1, t[idx])):
            raise SystemExit(f"{f}: a t >= 1 row's previous row is not the same episode at t - 1")
        if water_on:
            OTw = OT if thermal_on else listcol(tb.column("obs_true"), obs["D"])
            hyd = OTw[:, obs["hydration"]].astype(np.float64) * hscale
            on = cmask[G["pond_corner"][gi], ar.astype(np.int64) * Wd + ac.astype(np.int64)]
            # D3 integrity checks, every episode, every step (the pilot's R1 checks)
            WC["episodes_checked"] += len(st)
            WC["start_cell_mismatches"] += int(((ar[st] != PR["agent_pos"][gidx, 0])
                                                | (ac[st] != PR["agent_pos"][gidx, 1])).sum())
            WC["reset_hydration_max_abs_diff"] = max(WC["reset_hydration_max_abs_diff"], float(
                np.abs(hyd[st] - PR["hydration"][gidx]).max()))
            WC["steps_checked"] += len(idx)
            WC["step_exceptions"] += int((on[idx] != (hyd[idx] > hyd[prev])).sum())
            G["y_pond"][gidx] += bc(on[m].astype(float))
            G["hyd0"][gidx] = hyd[st]
            G["hyd_sum1"][gidx] += bc(hyd[m])
            pr0 = PR["water_pos"][gidx]                                     # [episodes, h*w, 2]
            G["d_pond0"][gidx] = np.maximum(np.abs(pr0[..., 0] - ar[st][:, None]),
                                            np.abs(pr0[..., 1] - ac[st][:, None])).min(1)
            succ["pond"] = on.astype(float)
            hcell = REG.hyd_band(hyd[prev]) * 4 + np.digitize(nut[prev], NUT_EDGES)
            XT["hyd_nut_trials"] += np.bincount(hcell, minlength=16)
            for t_ in avail:
                XT[f"hyd_nut__{t_}"] += np.bincount(hcell, weights=succ[t_][idx], minlength=16)
            off = ~on[prev]                     # bout onset (D8, Revision 1): off the pond at t-1
            XT["hyd_nut_onset_trials"] += np.bincount(hcell[off], minlength=16)
            XT["hyd_nut_onset__pond"] += np.bincount(hcell[off], weights=on[idx][off].astype(float),
                                                     minlength=16)
        cell = np.digitize(inj[prev], INJ_EDGES) * 4 + np.digitize(nut[prev], NUT_EDGES)
        nr = rn_any[prev].astype(int) * 2 + pn[prev].astype(int)
        XT["inj_nut_trials"] += np.bincount(cell, minlength=16)
        XT["near_trials"] += np.bincount(nr, minlength=4)
        for t_ in avail:
            w = succ[t_][idx]
            XT[f"inj_nut__{t_}"] += np.bincount(cell, weights=w, minlength=16)
            XT[f"near__{t_}"] += np.bincount(nr, weights=w, minlength=4)
        if verbose and fi % 25 == 0:
            print(f"  shard {fi}/{len(files)} ({time.time()-t0:.0f}s)", flush=True)

    assert np.allclose(IB.sum(1), G["n_steps"]) and np.allclose(NB.sum(1), G["n_steps"])
    assert (G["bush_steps"] <= G["n_steps"]).all()
    assert np.allclose(G["n_rows"], G["n_steps"] + 1), "expected exactly one reset row/episode"
    for k in ("y_eat", "y_near_pred", "y_near_rab"):
        assert (G[k] <= G["n_steps"]).all(), f"{k}: successes exceed trials"
    if thermal_on and T["warm_cell"]["available"]:
        assert (G["y_warm"] <= G["n_steps"]).all()
    assert XT["inj_nut_trials"].sum() == G["n_steps"].sum()
    if water_on:
        assert (G["y_pond"] <= G["n_steps"]).all()
        assert XT["hyd_nut_trials"].sum() == G["n_steps"].sum()
        WC["episodes_expected"] = int(nep)
        d["water_checks"] = WC
        bad = (WC["episodes_checked"] != nep or WC["start_cell_mismatches"] or WC["step_exceptions"]
               or WC["steps_checked"] != int(G["n_steps"].sum())
               or WC["reset_hydration_max_abs_diff"] > 1e-4)
        if bad:
            raise SystemExit(f"water integrity checks failed (D3): {WC}")
    return dict(**E, **G, IB=IB, NB=NB, traits=traits), XT


def factor_arrays(A: dict, d: dict) -> dict:
    """f__<name> per factor, from the aggregate, with the legacy formulas for the legacy names."""
    S, F = d["S"], d["F"]
    L = A["n_steps"]
    ns = np.maximum(L, 1)
    ent = {e["tag"]: e for e in S["entities"]}
    out = {}
    for f in F:
        n, k = f["name"], f["kind"]
        if k == "start":
            v = {"injury_level": A["inj0"], "nutrition": A["nut0"], "satiation": A["sat0"]}[f["column"]]
        elif k == "count_entity":
            v = A[f"cnt__{f['tag']}"]
        elif k == "count_obstacle":
            v = A[f"cnt__obs__{f['decl']}"]
        elif k == "count_resource":
            v = A[f"cnt__res__{f['decl']}"]
        elif k == "spawn_dist_bush":
            v = A["d_bush0"]
        elif k == "spawn_dist_entity":
            v = np.where(np.isfinite(A["d_pred0"]), A["d_pred0"], np.nan)
            if len(ent[f["tag"]]["slots"]) != len(S["pred"]):
                raise SystemExit("spawn distance per predator declaration needs one predator "
                                 "declaration (only one is supported)")
        elif k == "start_body_temp":
            v = A["bt0"]
        elif k == "ambient_temp":
            v = A["ambient"]
        elif k == "start_hydration":
            v = A["hyd0"]
        elif k == "spawn_dist_pond":
            v = A["d_pond0"]
        elif k in ("trait", "smell", "intensity"):
            v = A["traits"][n]
        elif k == "consequence":
            v = {"frac_time_injured": lambda: A["IB"][:, 1:].sum(1) / ns,
                 "frac_time_inj_severe": lambda: A["IB"][:, 3] / ns,
                 "mean_injury": lambda: (A["inj_sum"] - A["inj0"]) / ns,
                 "peak_injury": lambda: A["inj_max"],
                 "frac_time_low_nutrition": lambda: (A["NB"][:, 0] + A["NB"][:, 1]) / ns,
                 "mean_nutrition": lambda: (A["nut_sum"] - A["nut0"]) / ns,
                 "total_damage_taken": lambda: A["dmg_sum"], "eat_rate": lambda: A["n_ate"] / ns,
                 "rest_rate": lambda: A["n_rest"] / ns, "episode_length": lambda: L.astype(float),
                 "frac_time_predator_near": lambda: A["n_pred_near"] / ns,
                 "frac_time_rabbit_near": lambda: A["n_rab_near"] / ns,
                 "mean_body_temp": lambda: A["bt_sum1"] / ns,
                 "frac_time_warm_cell": lambda: A["y_warm"] / ns,
                 "mean_hydration": lambda: A["hyd_sum1"] / ns,
                 "frac_time_on_pond": lambda: A["y_pond"] / ns}[n]()
        else:
            raise SystemExit(f"unknown factor kind {k}")
        out[f"f__{n}"] = np.asarray(v, dtype=np.float64)
    return out


TARGET_KEY = {"bush_dwell": "bush_steps", "eating": "y_eat", "near_rabbit": "y_near_rab",
              "near_predator": "y_near_pred", "warm_cell": "y_warm", "pond": "y_pond"}


# -------------------------------------------------------------------------------------- cells ----
def cell_dir(out_root, c):
    return os.path.join(out_root, c["label"])


def sweep_cell(c: dict, out_root: str, reuse: bool, verbose=True) -> dict:
    dd = cell_dir(out_root, c)
    prov_p = os.path.join(dd, "_provenance.json")
    outs = [os.path.join(dd, x) for x in ("episodes.npz", "xtab.npz", "inventory.json")]
    cur = source_hashes(SWEEP_SOURCES)
    if any(os.path.exists(p) for p in outs + [prov_p]):
        if not reuse:
            raise SystemExit(f"{c['label']}: outputs exist in {dd}; pass --reuse-cache to keep them "
                             f"(they are then checked against run, stores and source hashes)")
        if not os.path.exists(prov_p) or not all(os.path.exists(p) for p in outs):
            raise SystemExit(f"{c['label']}: partial outputs in {dd} -- stale cache, remove them")
        pv = json.load(open(prov_p))
        if pv["run"] != c["run"] or pv["stores"] != c["stores"] or pv["sources"] != cur:
            raise SystemExit(f"{c['label']}: cached outputs in {dd} were built from another run, "
                             f"store or sweep code -- stale cache")
        print(f"{c['label']}: cache reused ({dd})")
        return pv
    t0 = time.time()
    d = describe(c)
    print(f"{c['label']}: {c['run']}\n  stores {c['stores']}\n  targets "
          + ", ".join(f"{t}={'yes' if v['available'] else 'no'}" for t, v in d["T"].items())
          + f"\n  factors {len(d['F'])}; unhandled markers {len(REG.unhandled(d['audit']))}", flush=True)
    A, XT = aggregate(c["stores"], d, verbose=verbose)
    if A["seed"].size != d["n_ep_manifest"]:
        raise SystemExit(f"{c['label']}: {A['seed'].size} episodes read, manifests say {d['n_ep_manifest']}")
    FA = factor_arrays(A, d)
    Y = {f"y__{t}": A[TARGET_KEY[t]] for t, v in d["T"].items() if v["available"]}
    keep = {k: v for k, v in A.items() if k != "traits"}
    os.makedirs(dd, exist_ok=True)
    np.savez_compressed(os.path.join(dd, "episodes.npz"), **keep, **FA, **Y)
    np.savez_compressed(os.path.join(dd, "xtab.npz"), **XT)
    inv = {"label": c["label"], "run": c["run"], "world": c["world"], "agent": c["agent"],
           "seed": c["seed"], "n_episodes": int(A["seed"].size),
           "targets": d["T"],
           "factors": [{k: f[k] for k in ("name", "block", "role", "subset", "source", "kind")}
                       for f in d["F"]],
           "audit": d["audit"], "unhandled": REG.unhandled(d["audit"]),
           "slots": {"entities": [{k: e[k] for k in ("tag", "cls", "slots")} for e in d["S"]["entities"]],
                     "obstacles": [{k: o[k] for k in ("name", "hides", "slots")} for o in d["S"]["obstacles"]],
                     "resources": [{k: r[k] for k in ("name", "type", "slots")} for r in d["S"]["resources"]]},
           "scent": d["spec"].as_dict(), "obs_indices": d["obs"],
           "thermal": d["thermo"], "m5": d["m5"],
           "ambient_finite_share": (float(np.isfinite(A["ambient"]).mean()) if "ambient" in A else None),
           "constants": {"MIN_EPISODES": REG.MIN_EPISODES, "COLLINEAR_R": REG.COLLINEAR_R,
                         "NEAR_D": NEAR_D, "INJ_EDGES": INJ_EDGES, "NUT_EDGES": NUT_EDGES}}
    if d["water"] is not None:              # worlds with water only, so other inventories are unchanged
        inv["water"] = d["water"]
        inv["water_checks"] = d.get("water_checks")
        inv["constants"]["HYD_EDGES"] = REG.HYD_EDGES
        if "pond_corner" in A:
            inv["water"]["pond_corner_counts"] = np.bincount(
                A["pond_corner"], minlength=len(d["water"]["pond_corners"])).tolist()
    json.dump(inv, open(os.path.join(dd, "inventory.json"), "w"), indent=1, default=float)
    pv = {"label": c["label"], "run": c["run"], "stores": c["stores"], "checkpoint": c.get("checkpoint"),
          "sources": cur, "git_head": git_head(), "seconds": round(time.time() - t0, 1),
          "obs_true_read": "obs_true" in d["cols"] and d["obs"] is not None}
    json.dump(pv, open(prov_p, "w"), indent=1)
    print(f"{c['label']}: done in {pv['seconds']} s -> {dd}", flush=True)
    return pv


def _one(args):
    c, out_root, reuse = args
    try:
        return sweep_cell(c, out_root, reuse, verbose=False)
    except SystemExit as e:
        return {"label": c["label"], "error": str(e)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--cells", nargs="*", default=None)
    ap.add_argument("--reuse-cache", action="store_true")
    ap.add_argument("--workers", type=int, default=1, help="cells swept in parallel (default 1)")
    a = ap.parse_args(argv)
    out_root = guard_out_root(a.out_root)
    pop = RD.load_population(a.population)
    cells = pop["cells"]
    if a.cells:
        miss = set(a.cells) - {c["label"] for c in cells}
        if miss:
            raise SystemExit(f"--cells not among the completed cells: {sorted(miss)}")
        cells = [c for c in cells if c["label"] in a.cells]
    RD.require_yardstick_for(cells)
    print(f"population {pop['population']}: {len(cells)} completed cells to sweep "
          f"({pop['n_not_completed']} not completed, skipped)")
    if a.workers <= 1:
        for c in cells:
            sweep_cell(c, out_root, a.reuse_cache)
        return
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(_one, [(c, out_root, a.reuse_cache) for c in cells]))
    errs = [r for r in res if "error" in r]
    for r in res:
        print(f"  {r['label']}: " + (f"FAILED {r['error']}" if "error" in r else f"{r['seconds']} s"))
    if errs:
        raise SystemExit(f"{len(errs)} cell(s) failed")


if __name__ == "__main__":
    main()
