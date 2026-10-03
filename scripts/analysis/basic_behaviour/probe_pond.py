#!/usr/bin/env python3
"""probe_pond.py - bush time before the first pond step, for probe scenes that contain a pond.

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md, Revision 2 (R2.2, R2.3) and the
re-check fixes R2-1 (5e-5 tolerance against the driver's 4-decimal CSV) and R2-3 (collect every
integrity failure in one pass before stopping).

WHY. In the thirst worlds every probe scene contains a pond (the environment always places one,
and the agents cannot run without the hydration reading). An agent that walks to the pond is no
longer showing "how much it hides"; so bush time is measured in each episode only up to the
agent's first step onto the pond, and the share of episodes that reached the pond is reported
beside it. No episode and no scene x checkpoint cell is dropped.

    P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
    # R2.3: choose the scenes' start hydration from the local calibration rollouts
    $P scripts/analysis/basic_behaviour/probe_pond.py calibrate \
        --root <out root>/  --scenes <scene root>/ --candidates 150 165 180 --out <calibration.json>
    # R2.2: one pond CSV per run x scene from the sweep's kept recordings
    $P scripts/analysis/basic_behaviour/probe_pond.py collate --sweep-specs <spec.yaml> ... [--workers N]

Layouts read (both written by scripts/eval/eval_rollout.py --record, unchanged):
    <step dir>/<run dir name>/<checkpoint>/episodes/NNNN.npz          termination_reason, length, seed
    <step dir>/<run dir name>/<checkpoint>/recordings/<ckpt>/episode_NNNNNN.rec.gz   snapshots, true_obs
collate: step dir = <output_dir>/_scratch/<label>/<cond>/<step>/ (run_sweep.py's scratch);
calibrate: step dir = <root>/h<S>/<cell>/<scene>/ (one per scene, both agents inside).

Per episode (R2.2): pond cells from replaying the scene's reset (registry.pond_cells) - never typed;
the Hydration slot found by name; integrity: for every s >= 1, agent on a pond cell at s <=>
hydration(s) > hydration(s-1); k = first s >= 1 on the pond (T + 1 if none); pre-pond bush share =
mean over s = 0..k-1 of [agent on the bush cell] (the episode_measures bush test). With no visit it
equals episode_measures' bush_hiding exactly. Death by thirst (code 6) cannot happen in a 100-step
scene that starts at 150 or more and is counted as a failure.

Data and outputs resolve under $BB_DATA_ROOT when it is set (a worktree), else this checkout.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
import warnings

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry as REG                                                  # noqa: E402

ROOT, DATA = REG.ROOT, REG.DATA_ROOT
sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
from avoidance_stats_heatmap import episode_measures                    # noqa: E402

CSV_TOL = 5e-5            # run_sweep.py writes bush_hiding with 4 decimals (R2-1)
P_VISIT_MAX, P_OD_MAX = 0.20, 0.02                                     # R2.3 pre-registered rule
POND_HEAD = ["step", "step_M", "bush_hiding_prepond", "pond_visit_share", "first_pond_step_median",
             "bush_hiding_novisit", "n_novisit", "n_overdrink", "n_thirst", "survival_steps",
             "n_episodes"]
TERM_THIRST, TERM_OVERDRINK = 6, 7


# ---------------------------------------------------------------------------------- per episode ----
def prepond(in_bush, on_pond) -> tuple[float, int]:
    """(pre-pond bush share, k). Snapshot s = 0..T; k = first s >= 1 with the agent on the pond,
    T + 1 when there is none; the share is the mean of in_bush over s = 0..k-1."""
    in_bush, on_pond = np.asarray(in_bush, bool), np.asarray(on_pond, bool)
    hit = np.flatnonzero(on_pond[1:])
    k = int(hit[0]) + 1 if hit.size else len(in_bush)
    return float(np.mean(in_bush[:k])), k


def integrity(on_pond, hyd) -> list[int]:
    """Snapshots s >= 1 where [on a pond cell] disagrees with [hydration rose] (D3 on a scene)."""
    on_pond, hyd = np.asarray(on_pond, bool), np.asarray(hyd, np.float64)
    return [int(s) for s in np.flatnonzero(on_pond[1:] != (np.diff(hyd) > 0)) + 1]


class Scene:
    """The scene's params, Hydration slot and pond cells (replayed from the scene's reset)."""
    _cache: dict = {}

    @classmethod
    def get(cls, path):
        if path not in cls._cache:
            cls._cache[path] = cls(path)
        return cls._cache[path]

    def __init__(self, path):
        from src.environment.config_loader import load_env_config, load_env_params
        from src.environment.sensor import get_observation_breakdown
        self.path = path
        self.params = load_env_params(load_env_config(path))
        if not bool(self.params.water_enabled):
            raise SystemExit(f"{path}: water is not enabled; probe_pond.py is for scenes with a pond")
        off = 0
        self.hidx = None
        for name, w in get_observation_breakdown(self.params).items():
            if name == "Hydration":
                self.hidx = off
            off += w
        if self.hidx is None:
            raise SystemExit(f"{path}: no Hydration in the observation")
        self.D = off
        self.scale = float(self.params.water_max_hydration)
        self.W = int(self.params.width)

    def pond(self, seeds) -> set:
        """Pond cells by replaying the scene's reset with these episodes' seeds. A probe scene has ONE
        candidate (asserted), so the pond cannot depend on the seed; after the first replay of a
        scene the cached cells are returned (a replay recompiles, which would dominate collation)."""
        if getattr(self, "_pond", None) is not None:
            return self._pond
        if len(self.params.water_topleft_table) != 1:
            raise SystemExit(f"{self.path}: {len(self.params.water_topleft_table)} pond candidates; "
                             f"a probe scene must have exactly one")
        R = REG.pond_cells(self.params, seeds)
        cells = [frozenset(map(tuple, R["water_pos"][i].tolist())) for i in range(len(seeds))]
        if len(set(cells)) != 1:
            raise SystemExit(f"{self.path}: pond cells differ between episodes of one scene")
        self._pond = set(cells[0])
        return self._pond


def episodes_in(step_dir):
    """[(run dir name, npz path, rec path)] for every episode under one step dir, paired by index."""
    out = []
    for ep_dir in sorted(glob.glob(os.path.join(step_dir, "*", "*", "episodes"))):
        base = os.path.dirname(ep_dir)
        run = os.path.basename(os.path.dirname(base))
        for z in sorted(glob.glob(os.path.join(ep_dir, "*.npz"))):
            i = int(os.path.basename(z)[:-4])
            rec = glob.glob(os.path.join(base, "recordings", "*", f"episode_{i:06d}.rec.gz"))
            out.append((run, z, rec[0] if len(rec) == 1 else None))
    return out


def measure_episodes(scene: Scene, eps, where: str) -> tuple[list[dict], list[str]]:
    """Per-episode values + every failure message (never stops at the first; R2-3)."""
    from src.utils.eval_recording import load_episode
    fails, rows, loaded = [], [], []
    for run, z, rec in eps:
        if rec is None:
            fails.append(f"{where}: {os.path.basename(z)} has no matching recording")
            continue
        npz = np.load(z)
        ep = load_episode(rec)
        if int(ep["seed"]) != int(npz["seed"]):
            fails.append(f"{where}: {rec} seed {ep['seed']} != episodes npz seed {int(npz['seed'])}")
            continue
        if "true_obs" not in ep or ep["true_obs"] is None:
            fails.append(f"{where}: {rec} has no true_obs")
            continue
        loaded.append((run, npz, ep, rec))
    if not loaded:
        return rows, fails + [f"{where}: no episodes"]
    pond = scene.pond([int(n["seed"]) for _, n, _, _ in loaded])
    for run, npz, ep, rec in loaded:
        S = ep["snapshots"]
        T1 = len(S)
        TO = np.asarray(ep["true_obs"], np.float64)
        if TO.shape != (T1, scene.D):
            fails.append(f"{where}: {rec} true_obs shape {TO.shape} != ({T1}, {scene.D})")
            continue
        hyd = TO[:, scene.hidx] * scene.scale
        ag = [tuple(int(x) for x in np.asarray(s["agent_pos"])) for s in S]
        bush = tuple(int(x) for x in np.asarray(S[0]["obs_pos"][0])) if len(S[0]["obs_pos"]) else None
        in_bush = np.array([bush is not None and a == bush for a in ag])
        on = np.array([a in pond for a in ag])
        bad = integrity(on, hyd)
        if bad:
            fails.append(f"{where}: {rec} pond/hydration mismatch at snapshots {bad[:10]}")
            continue
        share, k = prepond(in_bush, on)
        m = episode_measures(ep)
        if k == T1 and share != m["bush_hiding"]:
            fails.append(f"{where}: {rec} no-visit pre-pond share {share} != bush_hiding {m['bush_hiding']}")
        term = int(npz["termination_reason"])
        if term == TERM_THIRST:
            fails.append(f"{where}: {rec} died of thirst (code 6), impossible in a 100-step scene")
        rows.append({"run": run, "prepond": share, "k": k, "visit": k < T1, "bush_full": m["bush_hiding"],
                     "term": term, "survival": m["survival_steps"]})
    return rows, fails


def summarise(rows: list[dict]) -> dict:
    v = np.array([r["visit"] for r in rows])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return {"bush_hiding_prepond": float(np.mean([r["prepond"] for r in rows])),
                "pond_visit_share": float(v.mean()),
                "first_pond_step_median": float(np.median([r["k"] for r in rows if r["visit"]]))
                if v.any() else np.nan,
                "bush_hiding_novisit": float(np.mean([r["prepond"] for r in rows if not r["visit"]]))
                if (~v).any() else np.nan,
                "n_novisit": int((~v).sum()),
                "n_overdrink": int(sum(r["term"] == TERM_OVERDRINK for r in rows)),
                "n_thirst": int(sum(r["term"] == TERM_THIRST for r in rows)),
                "survival_steps": float(np.mean([r["survival"] for r in rows])),
                "n_episodes": len(rows),
                "bush_hiding_full": float(np.mean([r["bush_full"] for r in rows]))}


# ---------------------------------------------------------------------------------- calibrate ----
def choose(table: dict) -> dict:
    """R2.3 rule. table = {S: {world: {"P_visit": x, "P_od": y}}}. Returns {"S", "branch"}.

    Lowest S with P_visit <= 0.20 and P_od <= 0.02 in every world; else (fallback 1) among S with
    P_od <= 0.02 everywhere, the lowest worse-world P_visit (ties -> lower S); else (fallback 2) 150
    if offered, otherwise the lowest S."""
    Ss = sorted(table)
    od_ok = [S for S in Ss if all(w["P_od"] <= P_OD_MAX for w in table[S].values())]
    ok = [S for S in od_ok if all(w["P_visit"] <= P_VISIT_MAX for w in table[S].values())]
    if ok:
        return {"S": ok[0], "branch": "rule: lowest S with P_visit <= 0.20 and P_od <= 0.02 in every world"}
    if od_ok:
        S = min(od_ok, key=lambda s: (max(w["P_visit"] for w in table[s].values()), s))
        return {"S": S, "branch": "FALLBACK 1 (red flag): no S met P_visit <= 0.20; lowest worse-world "
                                  "P_visit among S with P_od <= 0.02"}
    return {"S": 150 if 150 in Ss else Ss[0],
            "branch": "FALLBACK 2 (red flag): no S had P_od <= 0.02 in every world; lowest-risk start"}


def _calib_scene(job):
    S, Skey, cell, scene, scene_dir, yaml_path = job
    sc = Scene.get(yaml_path)
    fails = []
    if abs(float(sc.params.water_start_hydration) - float(S)) > 1e-9:
        fails.append(f"{scene_dir}: scene start hydration {sc.params.water_start_hydration} != {S}")
    rows, f = measure_episodes(sc, episodes_in(scene_dir), f"h{Skey}/{cell}/{scene}")
    print(f"  h{Skey} {cell} {scene}: {len(rows)} episodes, {len(fails) + len(f)} failure(s)", flush=True)
    return job, rows, fails + f


def calibrate(a) -> int:
    table, per_scene, per_agent, fails = {}, {}, {}, []
    jobs = []
    for S in a.candidates:
        Skey = f"{S:g}"
        for cell_dir in sorted(glob.glob(os.path.join(a.root, f"h{Skey}", "*"))):
            cell = os.path.basename(cell_dir)
            for scene_dir in sorted(glob.glob(os.path.join(cell_dir, "avoid_*"))):
                scene = os.path.basename(scene_dir)
                jobs.append((S, Skey, cell, scene, scene_dir,
                             os.path.join(a.scenes, f"h{Skey}", cell, f"{scene}.yaml")))
    print(f"{len(jobs)} calibration scenes", flush=True)
    if a.workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers) as pool:
            res = pool.map(_calib_scene, jobs, chunksize=1)
    else:
        res = [_calib_scene(j) for j in jobs]
    grouped = {}
    for job, rows, f in res:
        fails += f
        grouped.setdefault((job[0], job[1], job[2]), []).append((job[3], rows))
    for (S, Skey, cell), scenes in sorted(grouped.items()):
            allrows = []
            for scene, rows in scenes:
                allrows += rows
                per_scene.setdefault(Skey, {}).setdefault(cell, {})[scene] = {
                    "P_visit": float(np.mean([r["visit"] for r in rows])) if rows else None, "n": len(rows)}
                for r in rows:
                    per_agent.setdefault(Skey, {}).setdefault(cell, {}).setdefault(r["run"], []).append(r["visit"])
            if allrows:
                table.setdefault(S, {})[cell] = {
                    "P_visit": float(np.mean([r["visit"] for r in allrows])),
                    "P_od": float(np.mean([r["term"] == TERM_OVERDRINK for r in allrows])),
                    "n": len(allrows)}
    for S in a.candidates:
        if S not in table or len(table[S]) < 2:
            fails.append(f"start {S:g}: rollouts found for {sorted(table.get(S, {}))}, expected two worlds")
    for S in table:
        for cell, v in table[S].items():
            if v["n"] != a.expect_per_world:
                fails.append(f"start {S:g}, {cell}: {v['n']} episodes, expected {a.expect_per_world}")
    out = {"rule": {"P_visit_max": P_VISIT_MAX, "P_od_max": P_OD_MAX, "candidates": a.candidates},
           "table": {f"{S:g}": v for S, v in table.items()},
           "per_scene_P_visit": per_scene,
           "per_agent_P_visit": {S: {c: {r: float(np.mean(v)) for r, v in d.items()} for c, d in cd.items()}
                                 for S, cd in per_agent.items()},
           "failures": fails}
    if not fails:
        out["choice"] = choose(table)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    for S, v in sorted(table.items()):
        print(f"  start {S:g}: " + "; ".join(f"{c} P_visit {w['P_visit']:.3f} P_od {w['P_od']:.3f} (n {w['n']})"
                                             for c, w in sorted(v.items())))
    if fails:
        print(f"{len(fails)} FAILURE(S) (first 20):\n  " + "\n  ".join(fails[:20]))
        return 1
    print(f"chosen start hydration {out['choice']['S']:g} -- {out['choice']['branch']}\n-> {a.out}")
    return 0


# ------------------------------------------------------------------------------------ collate ----
def _collate_cell(job):
    scene_path, step_dir, where = job
    rows, fails = measure_episodes(Scene.get(scene_path), episodes_in(step_dir), where)
    return where, int(os.path.basename(step_dir)), (summarise(rows) if rows else None), fails


def driver_csv(path) -> dict:
    return {int(r["step"]): r for r in csv.DictReader(open(path))} if os.path.exists(path) else {}


def collate(a) -> int:
    import yaml
    jobs, meta = [], []
    for sp in a.sweep_specs:
        spec = yaml.safe_load(open(sp))
        out_dir = os.path.join(DATA, spec["output_dir"])
        pdir = spec["probe"] if os.path.isabs(spec["probe"]) else os.path.join(ROOT, spec["probe"])
        conds = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(pdir, "avoid_*.yaml")))
        for run in spec["runs"]:
            for cond in conds:
                sd = os.path.join(out_dir, "_scratch", run["label"], cond)
                steps = sorted(p for p in glob.glob(os.path.join(sd, "*")) if os.path.basename(p).isdigit())
                meta.append((out_dir, run["label"], cond, len(steps)))
                jobs += [(os.path.join(pdir, f"{cond}.yaml"), p, f"{run['label']}/{cond}") for p in steps]
    print(f"{len(jobs)} scene x checkpoint cells from {len(a.sweep_specs)} spec(s)", flush=True)
    if a.workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers) as pool:
            res = []
            for i, r in enumerate(pool.imap(_collate_cell, jobs, chunksize=4)):
                res.append(r)
                if (i + 1) % 500 == 0:
                    print(f"  {i + 1}/{len(jobs)} cells", flush=True)
    else:
        res = [_collate_cell(j) for j in jobs]
    by = {}
    fails = []
    for where, step, summ, f in res:
        fails += f
        if summ is not None:
            by.setdefault(where, {})[step] = summ
    for out_dir, label, cond, n in meta:
        where = f"{label}/{cond}"
        drv = driver_csv(os.path.join(out_dir, label, f"{cond}.csv"))
        got = by.get(where, {})
        if set(drv) != set(got):
            fails.append(f"{where}: checkpoints in the driver CSV {len(drv)} vs collated {len(got)} "
                         f"(missing {sorted(set(drv) - set(got))[:5]}, extra {sorted(set(got) - set(drv))[:5]})")
        for step, s in got.items():
            if step in drv and abs(s["bush_hiding_full"] - float(drv[step]["bush_hiding"])) > CSV_TOL:
                fails.append(f"{where} @ {step}: full-episode bush_hiding {s['bush_hiding_full']:.6f} != "
                             f"driver CSV {drv[step]['bush_hiding']} (tolerance {CSV_TOL})")
    if fails:
        rep = os.path.join(DATA, a.failures_out)
        os.makedirs(os.path.dirname(rep), exist_ok=True)
        json.dump(fails, open(rep, "w"), indent=1)
        print(f"{len(fails)} FAILURE(S); nothing written. All failures -> {rep}\n  " + "\n  ".join(fails[:20]))
        return 1
    n = 0
    for out_dir, label, cond, _ in meta:
        got = by.get(f"{label}/{cond}", {})
        if not got:
            continue
        p = os.path.join(out_dir, label, "pond", f"{cond}.csv")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(POND_HEAD)
            for step in sorted(got):
                s = got[step]
                f = lambda x: "" if not np.isfinite(x) else f"{x:.6f}"
                w.writerow([step, f"{step / 1e6:.4f}", f(s["bush_hiding_prepond"]), f(s["pond_visit_share"]),
                            f(s["first_pond_step_median"]), f(s["bush_hiding_novisit"]), s["n_novisit"],
                            s["n_overdrink"], s["n_thirst"], f(s["survival_steps"]), s["n_episodes"]])
        n += 1
    print(f"wrote {n} pond CSV(s)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("--root", required=True, help="rollout root holding h<S>/<cell>/<scene>/")
    c.add_argument("--scenes", required=True, help="scene root holding h<S>/<cell>/<scene>.yaml")
    c.add_argument("--candidates", type=float, nargs="+", required=True)
    c.add_argument("--expect-per-world", type=int, required=True,
                   help="episodes per S x world (2 agents x 12 scenes x 30 = 720)")
    c.add_argument("--out", required=True)
    c.add_argument("--workers", type=int, default=1)
    k = sub.add_parser("collate")
    k.add_argument("--sweep-specs", nargs="+", required=True)
    k.add_argument("--workers", type=int, default=1)
    k.add_argument("--failures-out", default="results/analysis/basic_behaviour/thirst/probes/pond_failures.json")
    a = ap.parse_args(argv)
    return calibrate(a) if a.cmd == "calibrate" else collate(a)


if __name__ == "__main__":
    sys.exit(main())
