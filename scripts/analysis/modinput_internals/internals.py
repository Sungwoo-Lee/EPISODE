"""Modulator-input study, inside the networks: Q1-Q3 and the P1-P3 scoring.

Plain-language purpose: four modulated agents differ only in what their modulator reads (N: felt
injury; I: fullness + felt injury; IT: fullness, body temperature + felt injury; X: outside world
only). This tool asks, per agent and checkpoint: does the modulator respond to felt injury (Q1),
how far does felt injury move the main network's memory compared with an ordinary agent (Q2), and
how much of the injured agent's extra bush dwell goes away when felt injury is hidden from the
modulator, the main network, or both (Q3, the "direct-input share").
Plan: docs/experiments/active/modulator_clues/MODULATOR_INPUT_INTERNALS.md -- Revision 1 and 1a
override the earlier sections.

Agents (scripts/analysis/modulator_engagement/runs.py): N, I, IT, X = pairs nmninp_<V>_s42
(modulated); reference = pair l05_s42 modulated; ordinary = pair l05_s42 ordinary (Q2 partner).

  precondition  Felt injury is exactly 0 at every step of the RECORDED unhurt episodes (the dwell
                sweep's recordings, observation as the agent got it and the true one) at the 9
                checkpoints. Reads a sweep's recordings only once its collated CSVs exist.
  q1            The modulator engagement check's E1 (engagement.e1_checkpoint): the `trace` row
                (teacher-forced recorded felt-injury trace, e1g_trace_*) and the constant 0.70 row
                (e1g_*), co-primary, with the gain's across-unit SD (gainsd_*) beside them.
  q2            The case study's Analysis 1 capture (case.capture_checkpoint, orientation
                act_true): the RAW shift (mean Euclidean length of manipulated - true pass) of
                enc.out, rnn.state, rnn.out and the modulator's own state, under the natural trace
                and under 0.70, scenes none / rabbitwander / both. The across-state spread of the
                layer is reported in its own column and never divides a between-agent number.
  q3            Four conditions on the same 100 episode seeds in the no-animal and wandering-rabbit
                scenes at injury 70 and 0: live; felt injury hidden from the modulator only; from
                the main network only; from both. The hide happens inside the forward pass
                (ActorCriticRNN.forward_hidden) at fixed integer columns. Fatal checks:
                  - the agent's modulator reads felt injury (X and ordinary agents are refused);
                  - captured modulator and main-network inputs: felt column exactly 0 where hidden,
                    exactly the compressed true value where not, every other column exactly the
                    compressed true observation, in every condition and step;
                  - live: forward_hidden without a hide gives __call__'s logits bit for bit;
                  - unhurt scenes: felt injury exactly 0 at every step of all 100 episodes, and
                    every condition's episodes identical to live's;
                  - the reference's live dwell on the first 30 seeds equals its sweep CSV.
  parity        Live (identity) dwell on the first 30 seeds of the 100 = the stage-1 sweep CSV per
                checkpoint and scene; q1's natural-episode dwell = q3's live dwell. Reads the
                input runs' sweep only when every label/scene CSV exists and holds every
                checkpoint; otherwise reports "pending" and reads nothing.
  summarize     Q3 per agent and scene: per-checkpoint and pooled paired dwell difference
                (live - modulator-hidden, pp, bootstrap CI), pooled share with the "undefined",
                additivity and survival-guard readings (measures.pooled_share).
  score         P1-P3 counts (measures.p1/p2/p3) and the nesting table, from the outputs above.

Checkpoints: the 9 nearest 2, 3, ..., 10 M steps (engagement.select_checkpoints `every5`), each
required within 100 steps of its grid point. Survival steps, never reward. Felt injury is
nociception, never "pain".

    python scripts/analysis/modinput_internals/internals.py q3 --agents N,I,IT,reference \
        --device cpu --out results/analysis/modinput_internals
"""
from __future__ import annotations

import argparse
import csv
import functools
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

AGENTS = {"N": ("nmninp_N_s42", "modulated"), "I": ("nmninp_I_s42", "modulated"),
          "IT": ("nmninp_IT_s42", "modulated"), "X": ("nmninp_X_s42", "modulated"),
          "reference": ("l05_s42", "modulated"), "ordinary": ("l05_s42", "ordinary")}
VARIANTS = ("N", "I", "IT")
Q1_AGENTS = ("N", "I", "IT", "reference")
Q2_AGENTS = ("N", "I", "IT", "reference", "ordinary")
Q3_AGENTS = ("N", "I", "IT", "reference")
CONDITIONS = ("live", "mod_hidden", "main_hidden", "both_hidden")
HIDES = {"live": (False, False), "mod_hidden": (True, False), "main_hidden": (False, True),
         "both_hidden": (True, True)}
SCENES = {"none": ("avoid_none_inj70", "avoid_none_inj00"),
          "rabbitwander": ("avoid_rabbitwander_inj70", "avoid_rabbitwander_inj00")}
Q3_EPISODES = 100
SWEEP_EPISODES = 30
GRID_TOL = 100
Q2_LAYERS = ("enc.out", "rnn.state", "rnn.out", "mod.state")


def _mods():
    sys.path.insert(0, ROOT)
    from scripts.analysis.case_l05_s42 import case as C
    E, R, om, MP, episode_measures = C._mods()
    return C, E, R, om, MP, episode_measures


def _sha():
    return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def agent_pair(name):
    from scripts.analysis.modulator_engagement import runs as R
    if name not in AGENTS:
        raise ValueError(f"unknown agent {name!r}; valid: {list(AGENTS)}")
    key, role = AGENTS[name]
    return R.select(key)[0], role


def checkpoints(name):
    """{grid index: step} for the 9 grid points 2..10 M, each within GRID_TOL steps."""
    from scripts.analysis.modulator_engagement import engagement as E
    pair, role = agent_pair(name)
    ck = E.select_checkpoints(os.path.join(pair.run_dirs[role], "models"), "every5")
    if len(ck) != 9:
        raise ValueError(f"{name}: {len(ck)} grid checkpoints, expected 9")
    for g, s in ck.items():
        want = (E.LO_M + E.SPACING_M * g) * 1e6
        if abs(s - want) > GRID_TOL:
            raise ValueError(f"{name}: checkpoint {s} is {abs(s - want):.0f} steps from grid point {want:.0f}")
    return dict(sorted(ck.items()))


def _append_rows(path, rows):
    from scripts.analysis.case_l05_s42 import case as C
    C._append_rows(path, rows)


def _done(path, col="step"):
    if not os.path.exists(path):
        return set()
    with open(path) as fh:
        return {int(r[col]) for r in csv.DictReader(fh)}


# ------------------------------------------------------------------ Q1
def q1_checkpoint(name, step, device=""):
    _C, E, *_ = _mods()
    pair, role = agent_pair(name)
    if role != "modulated":
        raise ValueError(f"q1: {name} has no modulator")
    # the input runs' sweep is checked later by `parity` (never read a partial sweep folder)
    row = E.e1_checkpoint(pair, step, device, check_sweep=(pair.group != "nmninp"))
    return {"agent": name, **row}


# ------------------------------------------------------------------ Q2
def q2_rows(cap, head):
    """Raw-shift rows from case.capture_checkpoint output (orientation act_true only)."""
    import numpy as np
    from scripts.analysis.case_l05_s42 import measures as MS
    from scripts.analysis.case_l05_s42.case import UNHURT
    U = cap["unhurt"]
    sets = {"none": (UNHURT[0],), "rabbitwander": (UNHURT[1],), "both": UNHURT}
    rows = []
    for L in Q2_LAYERS:
        if L not in U[UNHURT[0]]["layers_ident"]:
            continue
        for sname, scs in sets.items():
            ref = np.concatenate([U[s]["layers_ident"][L][U[s]["ident"]["valid"]] for s in scs])
            keep, _mu, _sd, spread = MS.spread(ref)
            for p in ("const", "trace"):
                man = np.concatenate([U[s]["probes"][p]["layers"][L][1][U[s]["probes"][p]["valid"]] for s in scs])
                nat = np.concatenate([U[s]["probes"][p]["layers"][L][0][U[s]["probes"][p]["valid"]] for s in scs])
                raw_all = float(np.linalg.norm(man.astype(np.float64) - nat, axis=1).mean())
                num_kept, _size, dead = MS.shift_size(man, nat, keep, spread)
                rows.append({**head, "layer": L, "scenes": sname, "probe": p,
                             "probe_label": "dose 0.70" if p == "const" else "natural trace",
                             "raw_shift": raw_all, "raw_shift_kept_units": num_kept,
                             "raw_shift_silent_units": dead,
                             "spread_reported_separately": spread,
                             "units": int(ref.shape[1]), "units_kept": int(keep.sum()), "steps": int(len(man))})
    return rows


def q2_checkpoint(name, step, grid_index):
    C, *_ = _mods()
    pair, role = agent_pair(name)
    cap = C.capture_checkpoint(pair, role, step, check_sweep=(pair.group != "nmninp"))
    head = {"agent": name, "pair": pair.key, "role": role, "run": getattr(pair, role),
            "grid_index": grid_index, "step": int(step)}
    rep = {**head, "parity": cap["parity"], "trace_max": cap["trace_max"],
           "capture_dlogit_max": cap["capture_dlogit"],
           "chain_max_rel_dev": {w: max(v.values()) for w, v in cap["chain"].items()},
           "bush_identity": {s: cap["unhurt"][s]["ident"]["bush"] for s in cap["unhurt"]}
                            | {s: cap["injured"][s]["bush"] for s in cap["injured"]}}
    return q2_rows(cap, head), rep


# ------------------------------------------------------------------ Q3
def hide_columns(model, breakdown, felt_name="Interoceptive Nociception"):
    """(felt column in the flat observation, felt column in the modulator's input). Fixed
    integers from the agent's own breakdown (config order, outside jit) and its stored
    `mod_input_idx`. Refuses a network whose modulator does not read felt injury."""
    from scripts.analysis.obs_manipulation import manip as MP
    offs = MP.sensor_offsets(breakdown)
    if felt_name not in offs:
        raise ValueError(f"no {felt_name!r} in this agent's observation")
    felt_col = int(offs[felt_name][0])
    if not bool(model.modulation_enabled):
        raise ValueError("q3 refused: the agent has no modulator, so there is nothing to hide from it")
    idx = tuple(int(i) for i in model.mod_input_idx)
    if felt_col not in idx:
        raise ValueError(f"q3 refused: the modulator does not read felt injury (observation column "
                         f"{felt_col} not among its inputs {idx}); a share is not defined for it")
    return felt_col, idx.index(felt_col)


def _q3_scan(model, params, states0, h0, *, max_steps, mod_col, main_col, felt_col, felt_mod_col, mod_idx):
    """Greedy rollout with felt injury hidden as requested. Enter through nnx.jit.
    `mod_col`/`main_col`: Python ints or None (static). Live (both None) acts with the plain
    `model(...)` call and evaluates forward_hidden alongside for the capture."""
    import jax
    import jax.numpy as jnp
    from src.environment.core import jax_step
    from src.environment.sensor import get_observation
    v_step = jax.vmap(jax_step, in_axes=(0, 0, None))
    v_obs = jax.vmap(get_observation, in_axes=(0, None))
    live = mod_col is None and main_col is None
    mi = jnp.asarray(mod_idx)

    def body(carry, t):
        state, h = carry
        obs = v_obs(state, params)
        lg_h, _v, h_hid, _m, acts = model.forward_hidden(obs, h, mod_col, main_col)
        if live:
            lg, _v2, h_new, _m2 = model(obs, h)
            dlogit = jnp.abs(lg_h - lg).max(-1)
        else:
            lg, h_new, dlogit = lg_h, h_hid, jnp.zeros(obs.shape[0])
        action = jnp.argmax(lg, axis=-1)
        nxt, _r, done, _info = v_step(state, action, params)
        # expected inputs, computed here independently of the network code
        xs = jnp.sign(obs) * jnp.log(jnp.abs(obs) + 1.0)
        exp_mod = xs[:, mi]
        mod_in, main_in = acts["mod.in"], acts["main.in"]
        n_mod, n_main = exp_mod.shape[-1], xs.shape[-1]
        om_ = jnp.arange(n_mod) != felt_mod_col
        on_ = jnp.arange(n_main) != felt_col
        out = {"action": action, "done": done, "agent_pos": nxt.agent_pos, "animal_pos": nxt.animal_pos,
               "injury": nxt.injury_level, "felt_true": obs[:, felt_col], "felt_true_c": xs[:, felt_col],
               "mod_felt": mod_in[:, felt_mod_col], "main_felt": main_in[:, felt_col],
               "mod_dev_other": jnp.where(om_[None], jnp.abs(mod_in - exp_mod), 0.0).max(-1),
               "main_dev_other": jnp.where(on_[None], jnp.abs(main_in - xs), 0.0).max(-1),
               "dlogit": dlogit}
        return (nxt, h_new), out

    return jax.lax.scan(body, (states0, h0), jnp.arange(max_steps))[1]


_JIT = {}


def _jitted(**static):
    from flax import nnx
    key = tuple(sorted(static.items()))
    if key not in _JIT:
        _JIT[key] = nnx.jit(functools.partial(_q3_scan, **static))
    return _JIT[key]


def q3_rollout(agent, params, seeds, cond, felt_col, felt_mod_col):
    """One scene, one condition, all seeds. Returns the numpy outputs plus T, valid, states0."""
    import numpy as np
    import jax
    import jax.numpy as jnp
    from src.environment.core import jax_reset
    hm, hx = HIDES[cond]
    keys = jnp.stack([jax.random.PRNGKey(s) for s in seeds])
    s0 = jax.vmap(jax_reset, in_axes=(None, 0))(params, keys)
    for i, s in enumerate(seeds):                     # same parity guard as eval_rollout
        if not bool(jnp.array_equal(s0.key[i], jax_reset(params, jax.random.PRNGKey(s)).key)):
            raise RuntimeError(f"batched reset PRNG parity failed at seed {s}")
    h0 = agent.model.initial_state(batch_size=len(seeds))
    fn = _jitted(max_steps=int(params.max_steps), mod_col=felt_mod_col if hm else None,
                 main_col=felt_col if hx else None, felt_col=felt_col, felt_mod_col=felt_mod_col,
                 mod_idx=tuple(int(i) for i in agent.model.mod_input_idx))
    out = jax.tree_util.tree_map(np.asarray, fn(agent.model, params, s0, h0))
    T = np.argmax(out["done"], axis=0) + 1
    valid = np.arange(int(params.max_steps))[:, None] < T[None, :]
    return {"out": out, "T": T, "valid": valid, "states0_np": jax.tree_util.tree_map(np.asarray, s0)}


def check_inputs(r, cond, what):
    """Fatal: the captured inputs are hidden exactly where intended (Revision 1a)."""
    import numpy as np
    o, v = r["out"], r["valid"]
    hm, hx = HIDES[cond]
    for nm, hidden in (("mod", hm), ("main", hx)):
        f = o[f"{nm}_felt"][v]
        if hidden:
            if not np.all(f == 0.0):
                raise AssertionError(f"{what}/{cond}: {nm} felt-injury input not 0 (max |x| {np.abs(f).max()})")
        elif not np.array_equal(f, o["felt_true_c"][v]):
            raise AssertionError(f"{what}/{cond}: {nm} felt-injury input differs from the true value")
        dev = float(o[f"{nm}_dev_other"][v].max())
        if dev != 0.0:
            raise AssertionError(f"{what}/{cond}: a non-felt {nm} input column differs from the true value ({dev})")
    if cond == "live":
        d = float(o["dlogit"][v].max())
        if d != 0.0:
            raise AssertionError(f"{what}: forward_hidden without a hide differs from __call__ (|dlogit| {d})")


def assert_unhurt_zero(felt_true, valid, what):
    """Fatal unless felt injury is exactly 0 at every live step (Revision 1a: all 100 unhurt
    episodes, at run time)."""
    import numpy as np
    ft = np.asarray(felt_true)[np.asarray(valid, bool)]
    if not np.all(ft == 0.0):
        raise AssertionError(f"{what}: UNHURT-ZERO PRECONDITION FAILED: felt injury non-zero at "
                             f"{int((ft != 0).sum())} steps (max {np.abs(ft).max()})")


def _same(a, b):
    import numpy as np
    return (np.array_equal(a["T"], b["T"]) and np.array_equal(a["out"]["action"], b["out"]["action"])
            and np.array_equal(a["out"]["agent_pos"], b["out"]["agent_pos"]))


def q3_checkpoint(name, step, grid_index, episodes=Q3_EPISODES, agent=None):
    """Episode rows for every scene x condition x seed, plus a check report."""
    import numpy as np
    from scripts.analysis.nmn import replay
    from src.environment.sensor import get_observation_breakdown
    C, E, R, om, MP, episode_measures = _mods()
    pair, role = agent_pair(name)
    if agent is None:
        agent = replay.load_agent(os.path.join(pair.run_dirs[role], "models"), step)
    felt_col, felt_mod_col = hide_columns(agent.model, agent.obs_breakdown)   # refuses X / ordinary
    probe, n_sweep, out_dir, labels = R.spec_scene(pair)
    if n_sweep != SWEEP_EPISODES:
        raise ValueError(f"{pair.spec}: sweep has {n_sweep} episodes, plan says {SWEEP_EPISODES}")
    rows, rep = [], {"agent": name, "step": int(step), "grid_index": grid_index, "felt_col": felt_col,
                     "felt_mod_col": felt_mod_col, "checks": [], "live_bush_first30": {}, "sweep": {}}
    seeds = None
    for sname, (inj, unh) in SCENES.items():
        for sc in (inj, unh):
            p, _, w, bm = E._world(probe, sc)
            s = E._seeds(bm, episodes, p)
            if seeds is not None and s != seeds:
                raise ValueError(f"{p}: eval seeds differ between scenes")
            seeds = s
            wb = get_observation_breakdown(w)
            if list(wb.items()) != list(agent.obs_breakdown.items()):
                raise ValueError(f"{sc}: world observation layout differs from the agent's")
            res = {}
            for cond in CONDITIONS:
                r = q3_rollout(agent, w, seeds, cond, felt_col, felt_mod_col)
                check_inputs(r, cond, f"{name}/{step}/{sc}")
                res[cond] = r
            if sc == unh:
                assert_unhurt_zero(res["live"]["out"]["felt_true"], res["live"]["valid"], f"{name}/{step}/{sc}")
                for cond in CONDITIONS[1:]:
                    if not _same(res[cond], res["live"]):
                        raise AssertionError(f"{name}/{step}/{sc}: condition {cond} differs from live in the "
                                             f"unhurt scene -- the hide is not inert at felt injury 0")
                rep["checks"].append(f"{sc}: felt injury 0 at all {int(res['live']['valid'].sum())} live steps "
                                     f"of {len(seeds)} episodes; all conditions identical to live")
            for cond, r in res.items():
                for b in range(len(seeds)):
                    m = episode_measures({"snapshots": om._snapshots(r["states0_np"], r["out"], b, int(r["T"][b]))})
                    rows.append({"agent": name, "run": getattr(pair, role), "grid_index": grid_index,
                                 "step": int(step), "scene": sname, "scene_file": sc,
                                 "injury": "injured" if sc == inj else "unhurt", "condition": cond,
                                 "seed": seeds[b], "seed_index": b, "bush_hiding": float(m["bush_hiding"]),
                                 "survival_steps": float(m["survival_steps"])})
            b30 = float(np.mean([r_["bush_hiding"] for r_ in rows[-len(seeds) * 4:]
                                 if r_["condition"] == "live" and r_["seed_index"] < SWEEP_EPISODES]))
            rep["live_bush_first30"][sc] = b30
            if len(seeds) < SWEEP_EPISODES:
                rep["sweep"][sc] = f"skipped: {len(seeds)} episodes < the sweep's {SWEEP_EPISODES} (smoke run)"
            elif pair.group != "nmninp":      # reference: its sweep is complete; check now
                rep["sweep"][sc] = E._check_sweep(b30, out_dir, labels[role], sc, step, f"{name}/{sc}")
            else:
                rep["sweep"][sc] = "deferred to `parity`"
    rep["checks"].append("inputs hidden exactly where intended, all conditions and steps; "
                         "live forward_hidden == __call__ bit for bit")
    return rows, rep


# ------------------------------------------------------------------ parity
def _sweep_complete(out_dir, label, scenes, steps):
    """True only if every scene CSV exists for the label and holds every requested checkpoint."""
    import pandas as pd
    for sc in scenes:
        f = os.path.join(ROOT, out_dir, label, f"{sc}.csv")
        if not os.path.exists(f):
            return False
        if not set(steps) <= set(pd.read_csv(f)["step"].astype(int)):
            return False
    return True


def parity(out_root, agents=Q3_AGENTS):
    import pandas as pd
    _C, E, R, *_ = _mods()
    rep = {}
    scenes = [s for pr in SCENES.values() for s in pr]
    for name in agents:
        pair, role = agent_pair(name)
        _p, _n, out_dir, labels = R.spec_scene(pair)
        f = os.path.join(out_root, "q3", f"{name}_checks.jsonl")
        if not os.path.exists(f):
            rep[name] = "no q3 output"
            continue
        checks = [json.loads(l) for l in open(f)]
        if any(str(v).startswith("skipped") for c in checks for v in c["sweep"].values()):
            raise ValueError(f"{f}: holds smoke-run checkpoints (< {SWEEP_EPISODES} episodes); not a parity input")
        steps = [c["step"] for c in checks]
        if not _sweep_complete(out_dir, labels[role], scenes, steps):
            rep[name] = "pending: sweep CSVs not collated yet (nothing read)"
            continue
        res = []
        for c in checks:
            for sc in scenes:
                res.append(E._check_sweep(c["live_bush_first30"][sc], out_dir, labels[role], sc, c["step"],
                                          f"{name}/{sc}"))
        # q1's natural no-animal episodes are the same episodes as q3's live first 30
        q1f = os.path.join(out_root, "q1", f"{name}.csv")
        if os.path.exists(q1f):
            q1 = pd.read_csv(q1f).set_index("step")
            for c in checks:
                if c["step"] in q1.index:
                    for col, sc in (("bush_nat00", "avoid_none_inj00"), ("bush_nat70", "avoid_none_inj70")):
                        if abs(float(q1.loc[c["step"], col]) - c["live_bush_first30"][sc]) > 1e-9:
                            raise RuntimeError(f"{name} step {c['step']}: q1 {col} != q3 live dwell ({sc})")
        rep[name] = f"match ({len(res)} checkpoint x scene values)" if all(x == "match" for x in res) else res
    os.makedirs(out_root, exist_ok=True)
    json.dump(rep, open(os.path.join(out_root, "parity.json"), "w"), indent=1)
    return rep


# ------------------------------------------------------------------ precondition (recordings)
def precondition(agents=Q3_AGENTS):
    """Felt injury exactly 0 at every recorded step of the unhurt sweep episodes."""
    import numpy as np
    import src.utils.episode_bundle as EB
    _C, E, R, om, MP, _ = _mods()
    rep = {}
    for name in agents:
        pair, role = agent_pair(name)
        _p, _n, out_dir, labels = R.spec_scene(pair)
        lab = labels[role]
        ck = list(checkpoints(name).values())
        unh = [u for _i, u in SCENES.values()]
        if not _sweep_complete(out_dir, lab, [s for pr in SCENES.values() for s in pr], ck):
            rep[name] = "pending: sweep not collated (recordings not read)"
            continue
        br = None
        n_steps, n_eps, worst = 0, 0, 0.0
        for sc in unh:
            for st in ck:
                # <step>.zip archive or legacy <step>/ folder (plan SWEEP_EPISODE_BUNDLES..., F8)
                cell = EB.cell_path(os.path.join(ROOT, out_dir, "_scratch", lab, sc), st)
                recs = [] if cell is None else EB.members(cell, f"*/{st}/recordings/{st}/episode_*.rec.gz")
                if len(recs) != SWEEP_EPISODES:
                    raise RuntimeError(f"{name}/{sc}/{st}: {len(recs)} recordings, expected {SWEEP_EPISODES}")
                if br is None:
                    from scripts.analysis.nmn import replay
                    br = replay.load_agent(os.path.join(pair.run_dirs[role], "models"), st).obs_breakdown
                    col = MP.sensor_offsets(br)[E.FELT][0]
                for f in recs:
                    ep = EB.load_recording(cell, f)
                    for k in ("obs", "true_obs"):
                        x = np.asarray(ep[k])[:, col]
                        worst = max(worst, float(np.abs(x).max()))
                    n_steps += len(ep["obs"])
                    n_eps += 1
        if worst != 0.0:
            raise AssertionError(f"{name}: UNHURT-ZERO PRECONDITION FAILED, max |felt injury| {worst}")
        rep[name] = f"pass: felt injury exactly 0 in {n_eps} recorded unhurt episodes, {n_steps} steps"
    return rep


# ------------------------------------------------------------------ summarize / score
def _q3_arrays(df, scene):
    """dwell, surv: {cond: (K, N, 2)} for one agent and scene."""
    import numpy as np
    d = df[df["scene"] == scene]
    steps = sorted(d["step"].unique())
    N = int(d["seed_index"].max()) + 1
    dw, sv = {}, {}
    for c in CONDITIONS:
        a = np.full((len(steps), N, 2), np.nan)
        b = np.full((len(steps), N, 2), np.nan)
        for k, st in enumerate(steps):
            for j, inj in enumerate(("injured", "unhurt")):
                x = d[(d["step"] == st) & (d["condition"] == c) & (d["injury"] == inj)].sort_values("seed_index")
                if len(x) != N:
                    raise ValueError(f"{scene}/{st}/{c}/{inj}: {len(x)} episodes, expected {N}")
                a[k, :, j], b[k, :, j] = x["bush_hiding"].to_numpy(), x["survival_steps"].to_numpy()
        dw[c], sv[c] = a, b
    return dw, sv, steps


def summarize(out_root, agents=Q3_AGENTS):
    import pandas as pd
    from scripts.analysis.modinput_internals import measures as M
    summ, per = {}, []
    for name in agents:
        f = os.path.join(out_root, "q3", f"{name}_episodes.csv")
        if not os.path.exists(f):
            continue
        df = pd.read_csv(f)
        summ[name] = {}
        for scene in SCENES:
            dw, sv, steps = _q3_arrays(df, scene)
            summ[name][scene] = {"steps": [int(s) for s in steps], **M.pooled_share(dw, sv),
                                 "dwell_diff_live_minus_mod_pooled": M.paired_dwell_difference(dw)}
            for k, st in enumerate(steps):
                row = {"agent": name, "scene": scene, "step": int(st)}
                for c in CONDITIONS:
                    row[f"effect_{c}_pp"] = 100.0 * float((dw[c][k, :, 0] - dw[c][k, :, 1]).mean())
                    row[f"inj_survival_{c}"] = float(sv[c][k, :, 0].mean())
                for b in CONDITIONS[1:]:
                    pdd = M.paired_dwell_difference(dw, "live", b, ck=k)
                    row.update({f"live_minus_{b}_pp": pdd["diff_pp"], f"live_minus_{b}_ci_lo": pdd["ci_lo"],
                                f"live_minus_{b}_ci_hi": pdd["ci_hi"]})
                per.append(row)
    os.makedirs(os.path.join(out_root, "q3"), exist_ok=True)
    json.dump(summ, open(os.path.join(out_root, "q3", "summary.json"), "w"), indent=1)
    if per:
        pd.DataFrame(per).to_csv(os.path.join(out_root, "q3", "per_checkpoint.csv"), index=False)
    return summ


def score(out_root):
    import numpy as np
    import pandas as pd
    from scripts.analysis.modinput_internals import measures as M
    res = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git_sha": _sha()}
    pf = os.path.join(out_root, "parity.json")
    res["parity"] = json.load(open(pf)) if os.path.exists(pf) else "not run"
    # Q1 / P1
    q1 = {a: pd.read_csv(os.path.join(out_root, "q1", f"{a}.csv")).sort_values("step")
          for a in Q1_AGENTS if os.path.exists(os.path.join(out_root, "q1", f"{a}.csv"))}
    if set(Q1_AGENTS) <= set(q1):
        rows = lambda d: {"trace": d["e1g_trace_mean4"].to_numpy(), "const": d["e1g_mean4"].to_numpy()}
        res["P1"] = M.p1({v: rows(q1[v]) for v in VARIANTS}, rows(q1["reference"]))
        res["Q1_table"] = {a: {"e1g_trace_mean4": q1[a]["e1g_trace_mean4"].round(6).tolist(),
                               "e1g_const_mean4": q1[a]["e1g_mean4"].round(6).tolist(),
                               "gainsd_mean4": q1[a]["gainsd_mean4"].round(6).tolist()} for a in q1}
    # Q2 / P2: raw rnn.state shift, dose 0.70, both scenes pooled
    q2 = {a: pd.read_csv(os.path.join(out_root, "q2", f"{a}.csv"))
          for a in Q2_AGENTS if os.path.exists(os.path.join(out_root, "q2", f"{a}.csv"))}
    if set(Q2_AGENTS) <= set(q2):
        sel = lambda d, p="const": d[(d["layer"] == "rnn.state") & (d["scenes"] == "both")
                                     & (d["probe"] == p)].sort_values("step")["raw_shift"].to_numpy()
        res["P2"] = M.p2({v: sel(q2[v]) for v in VARIANTS}, sel(q2["reference"]), sel(q2["ordinary"]))
        res["Q2_table"] = {a: {p: sel(q2[a], p).round(6).tolist() for p in ("const", "trace")} for a in q2}
    # Q3 / P3
    sf = os.path.join(out_root, "q3", "summary.json")
    if os.path.exists(sf):
        s = json.load(open(sf))
        if set(VARIANTS) <= set(s):
            res["P3"] = M.p3({v: s[v]["rabbitwander"] for v in VARIANTS})
        res["Q3_reference_descriptive"] = s.get("reference", {}).get("rabbitwander", {}).get("share_point")
        res["nesting_Q3_share_point_rabbit"] = {v: s[v]["rabbitwander"]["share_point"] for v in VARIANTS if v in s}
    if "Q1_table" in res:
        res["nesting_Q1_trace_mean"] = {v: float(np.mean(res["Q1_table"][v]["e1g_trace_mean4"]))
                                        for v in VARIANTS if v in res["Q1_table"]}
    json.dump(res, open(os.path.join(out_root, "score.json"), "w"), indent=1, default=str)
    return res


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("measure", choices=["precondition", "q1", "q2", "q3", "parity", "summarize", "score"])
    ap.add_argument("--agents", help="comma-separated agent names (default: the measure's list)")
    ap.add_argument("--checkpoints", default="grid9",
                    help="grid9 (the 9 grid points) or steps:a,b (smoke tests)")
    ap.add_argument("--device", choices=["cpu", "gpu"])
    ap.add_argument("--episodes", type=int, default=Q3_EPISODES, help="q3 episodes per arm (plan: 100)")
    ap.add_argument("--out", required=True, help="output root (results/analysis/modinput_internals)")
    a = ap.parse_args(argv)
    if a.measure in ("q1", "q2", "q3"):
        if a.device is None:
            ap.error(f"{a.measure} requires --device")
        sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "obs_manipulation"))
        import run as om_run
        om_run._set_device(a.device)
    sys.path.insert(0, ROOT)
    default = {"q1": Q1_AGENTS, "q2": Q2_AGENTS, "q3": Q3_AGENTS, "precondition": Q3_AGENTS,
               "parity": Q3_AGENTS, "summarize": Q3_AGENTS, "score": ()}[a.measure]
    agents = tuple(a.agents.split(",")) if a.agents else default
    for n in agents:
        agent_pair(n)
    os.makedirs(a.out, exist_ok=True)
    if a.measure == "precondition":
        r = precondition(agents)
        json.dump(r, open(os.path.join(a.out, "precondition.json"), "w"), indent=1)
        print(json.dumps(r, indent=1))
        return
    if a.measure == "parity":
        print(json.dumps(parity(a.out, agents), indent=1))
        return
    if a.measure == "summarize":
        s = summarize(a.out, agents)
        print(json.dumps({n: {sc: {k: v[k] for k in ("reading", "share_point", "numerator_pp", "divisor_pp",
                                                     "interaction_pp", "survival_flagged")}
                              for sc, v in d.items()} for n, d in s.items()}, indent=1))
        return
    if a.measure == "score":
        print(json.dumps(score(a.out), indent=1, default=str))
        return

    mdir = os.path.join(a.out, a.measure)
    os.makedirs(mdir, exist_ok=True)
    t0 = time.time()
    for name in agents:
        ck = checkpoints(name)
        if a.checkpoints.startswith("steps:"):
            want = [int(x) for x in a.checkpoints[6:].split(",")]
            ck = {g: s for g, s in ck.items() if s in want}
            if len(ck) != len(want):
                raise ValueError(f"{name}: {want} are not all grid checkpoints {checkpoints(name)}")
        elif a.checkpoints != "grid9":
            raise ValueError("--checkpoints must be grid9 or steps:a,b")
        main_csv = os.path.join(mdir, f"{name}{'_episodes' if a.measure == 'q3' else ''}.csv")
        done = _done(main_csv)
        for g, s in ck.items():
            if s in done:
                continue
            t1 = time.time()
            if a.measure == "q1":
                row = q1_checkpoint(name, s, a.device)
                _append_rows(main_csv, [{"grid_index": g, **row, "seconds": round(time.time() - t1, 1)}])
            elif a.measure == "q2":
                rows, rep = q2_checkpoint(name, s, g)
                _append_rows(main_csv, rows)
                with open(os.path.join(mdir, f"{name}_checks.jsonl"), "a") as fh:
                    fh.write(json.dumps({**rep, "seconds": round(time.time() - t1, 1)}) + "\n")
            else:
                rows, rep = q3_checkpoint(name, s, g, episodes=a.episodes)
                _append_rows(main_csv, rows)
                with open(os.path.join(mdir, f"{name}_checks.jsonl"), "a") as fh:
                    fh.write(json.dumps({**rep, "seconds": round(time.time() - t1, 1)}) + "\n")
            print(f"[{a.measure}] {name} step {s} (grid {g}): {time.time() - t1:.0f}s", flush=True)
        pair, role = agent_pair(name)
        json.dump({"measure": a.measure, "agent": name, "run": getattr(pair, role),
                   "grid": {str(g): s for g, s in ck.items()},
                   "device": a.device, "episodes": a.episodes if a.measure == "q3" else None,
                   "git_sha": _sha(), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                  open(os.path.join(mdir, f"manifest_{name}.json"), "w"), indent=1)
    print(f"[{a.measure}] done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
