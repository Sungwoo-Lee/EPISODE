"""Modulator engagement measures E1-E4 for the explicit pair list (runs.py).

Plain-language purpose: for each modulated agent, at each checkpoint the behaviour outcomes use,
measure how much its modulator's output -- the per-unit gain (gamma) and offset (beta) it applies
at the encoder, memory (task GRU) and actor -- changes when ONLY the felt-injury input changes,
and a few companion measures. The critic site is recorded but never enters a summary: it cannot
change what the agent does.

  e1   Teacher-forced injury responsiveness, in the pair's own unhurt no-animal test scene, through
       the observation-manipulation tool's LIVE mode (scripts/analysis/obs_manipulation/run.py).
       The acting network sees felt injury (`Interoceptive Nociception`) set to 0.70 from step 0
       (the settled value of a constant injury 70: start_injury / max_injury, the felt-injury
       kernel sums to 1, checked per world); the shadow network sees the true observations of the
       SAME trajectory. E1 = mean over steps, episodes and units of |gamma_act - gamma_shadow|
       (and the same for beta), per site and averaged over the four non-critic FiLM heads.
         sensitivity row  ("trace"): felt injury follows the recorded felt-injury trace of the
                          natural injury-70 no-animal episode, step by step, instead of 0.70.
         E1-natural       (secondary, confounded): the natural injured (70) and unhurt (0) episodes
                          of the same seeds, step-aligned, |gamma_70 - gamma_0| on steps both live.
       Every checkpoint is checked against the dwell sweep that produced the outcomes: the identity
       episodes' bush dwell must equal the sweep CSV's value for that checkpoint (both scenes).
  e2   Context share: `mod_distribution.variance_split` of the gain (and offset) per site on
       greedy rollouts in the run's own training world (rho = across-time / total variance).
  e3   Freeze cost in the training world: `freeze.py`'s verified weight edit, gain and offset
       separately, paired survival-step differences (`freeze.paired_differences`).
  e4-prepare   Causal measure, step 1: in the rabbit-wander test scenes at injury 70 and 0, one
       pooled per-unit time-mean of gain and offset per checkpoint (both scenes' live passes
       together), then weight-edited copies of the checkpoint (gain frozen; offset frozen) written
       to a SEPARATE directory -- never over the originals -- and a dwell-sweep spec that scores
       them with the same probe battery and episodes as the outcomes. The sweep itself is launched
       separately (training-runner), after the budget is approved.
  e4-collect   Step 2: the modulated agent's rabbit-scene injury effect live (the original sweep
       CSVs) vs frozen (the new sweep CSVs), on the same checkpoints and seeds.

Checkpoints: `grid` = the 41 checkpoints nearest 2.0, 2.2, ..., 10.0 M steps (within 0.05 M, the
rule of checkpoint_stats.on_grid); `every5` = every fifth grid point (9); `steps:a,b` = explicit.
Outputs go to --out/<measure>/<pair>.csv, one row per checkpoint, appended as each checkpoint
finishes (a rerun skips checkpoints already written), plus --out/<measure>/manifest_<pair>.json.

Survival steps, never reward.

    python scripts/analysis/modulator_engagement/engagement.py e1 --pairs main --checkpoints grid \
        --device cpu --out results/analysis/modulator_engagement
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OM_DIR = os.path.join(ROOT, "scripts", "analysis", "obs_manipulation")

SITES = ("encoder_unimodal", "encoder_multimodal", "rnn", "actor")     # critic excluded
FELT = "Interoceptive Nociception"
LO_M, HI_M, SPACING_M = 2.0, 10.0, 0.2
E1_CONST = 0.70
E4_SCENES = ("avoid_rabbitwander_inj70", "avoid_rabbitwander_inj00")


def _om():
    """The observation-manipulation tool's run.py and manip.py, as modules."""
    sys.path.insert(0, OM_DIR)
    import manip as MP
    spec = importlib.util.spec_from_file_location("om_run", os.path.join(OM_DIR, "run.py"))
    om = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(om)
    return om, MP


# ------------------------------------------------------------------ checkpoints
def grid_index_map(steps):
    """{grid index g: checkpoint step} for g = 0..40 (2.0 + 0.2 g M steps); a grid point counts
    only if a checkpoint lies within spacing/4 of it (checkpoint_stats.on_grid's rule)."""
    import numpy as np
    s = np.asarray(sorted(steps), float)
    out = {}
    for g, x in enumerate(np.arange(LO_M, HI_M + SPACING_M / 2, SPACING_M) * 1e6):
        j = int(np.argmin(np.abs(s - x)))
        if abs(s[j] - x) <= SPACING_M * 1e6 / 4 and int(s[j]) not in out.values():
            out[g] = int(s[j])
    return out


def select_checkpoints(models_dir, how):
    from scripts.analysis.nmn import ckpt_io
    steps = ckpt_io.list_steps(models_dir)
    gm = grid_index_map(steps)
    if how == "grid":
        return gm
    if how == "every5":
        return {g: s for g, s in gm.items() if g % 5 == 0}
    if how.startswith("steps:"):
        want = [int(x) for x in how[6:].split(",")]
        inv = {s: g for g, s in gm.items()}
        bad = [w for w in want if w not in steps]
        if bad:
            raise ValueError(f"checkpoints {bad} not saved under {models_dir}")
        return {inv.get(w, -1 - i): w for i, w in enumerate(want)}
    raise ValueError(f"--checkpoints must be grid | every5 | steps:a,b ; got {how!r}")


# ------------------------------------------------------------------ io helpers
def _done(csv_path):
    if not os.path.exists(csv_path):
        return set()
    with open(csv_path) as fh:
        return {int(r["step"]) for r in csv.DictReader(fh)}


def _append(csv_path, row):
    new = not os.path.exists(csv_path)
    if not new:
        with open(csv_path) as fh:
            head = next(csv.reader(fh))
        if head != list(row):
            raise ValueError(f"{csv_path}: columns changed ({len(head)} vs {len(row)}); "
                             f"write to a fresh --out")
    with open(csv_path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def _sha():
    return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def _world(probe, cond):
    from src.environment.config_loader import load_env_config, load_env_params, load_behavior_measure_cfg
    path = os.path.join(ROOT, probe, f"{cond}.yaml")
    cfg = load_env_config(path)
    return path, cfg, load_env_params(cfg), load_behavior_measure_cfg(cfg)


def _seeds(bm, n, path):
    if bm is None or len(bm.eval_seeds) < n:
        raise ValueError(f"{path}: fewer than {n} behavior_measures.eval_seeds")
    return [int(s) for s in bm.eval_seeds[:n]]


def _sweep_value(out_dir, label, cond, step, col="bush_hiding"):
    import pandas as pd
    f = os.path.join(ROOT, out_dir, label, f"{cond}.csv")
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    hit = d[d["step"] == step]
    return None if hit.empty else float(hit[col].iloc[0])


def _check_sweep(measured, out_dir, label, cond, step, what):
    """Identity episodes must reproduce the dwell sweep's own per-checkpoint value (CSVs round to
    4 decimals). A missing sweep value is recorded, not silently passed."""
    ref = _sweep_value(out_dir, label, cond, step)
    if ref is None:
        return "no_sweep_value"
    if abs(measured - ref) > 6e-5:
        raise RuntimeError(f"{what}: identity bush dwell {measured:.6f} != sweep {ref:.4f} "
                           f"({out_dir}/{label}/{cond}.csv, step {step}) -- not the episodes the outcomes used")
    return "match"


def _bush(om_episode_measures, states0_np, out, b, T, snapshots):
    return float(om_episode_measures({"snapshots": snapshots(states0_np, out, b, int(T[b]))})["bush_hiding"])


# ------------------------------------------------------------------ E1
def felt_settle_value(params):
    """The value felt injury settles at for a constant starting injury, from the world's own
    parameters: start_injury / max_injury, valid only if the start injury is fixed, the
    felt-injury convolution kernel sums to 1, and perceptual noise is off."""
    import numpy as np
    lo, hi = float(params.start_injury_low), float(params.start_injury_high)
    if lo != hi:
        raise ValueError(f"start injury is a range [{lo}, {hi}], not a constant")
    if bool(params.interoceptive_convolution_enabled):
        ks = float(np.asarray(params.interoceptive_kernel).sum())
        if abs(ks - 1.0) > 1e-5:
            raise ValueError(f"felt-injury kernel sums to {ks}, not 1: the settled value is not "
                             f"start/max")
    noise = getattr(params, "perceptual_noise_enabled", None)
    if noise is not None and bool(noise):
        raise ValueError("perceptual noise is on in this world; felt injury does not settle to a constant")
    return lo / float(params.max_injury)


def _trace_specs(felt, valid, seeds):
    """Group episodes by identical recorded felt-injury trace; one manipulation spec per group.
    A trace is held at its last live value after the natural episode ended. Consecutive equal
    values are merged into one step window."""
    import numpy as np
    T, N = felt.shape
    groups = {}
    for i in range(N):
        L = int(valid[:, i].sum())
        tr = felt[:, i].copy()
        tr[L:] = tr[L - 1]
        groups.setdefault(tr.tobytes(), (tr, []))[1].append(i)
    out = []
    for tr, idx in groups.values():
        ents, t0 = [], 0
        for t in range(1, T + 1):
            if t == T or tr[t] != tr[t0]:
                ents.append({"name": f"felt_t{t0}", "sensor": FELT, "element": 0, "op": "set",
                             "values": [float(tr[t0])], "steps": [t0, t if t < T else None]})
                t0 = t
        out.append(({"manipulations": ents}, [seeds[i] for i in idx], idx, tr))
    return out


def _site_means(out, rows, valid, prefix):
    """Mean over valid (t, b in rows) of out[f'{prefix}_{site}'] per site, + the 4-site mean."""
    import numpy as np
    r = {}
    for s in SITES:
        k = f"{prefix}_{s}"
        if k not in out:
            raise ValueError(f"site {s} has no modulator output in this run ({k} missing)")
        r[s] = float(out[k][:, rows][valid[:, rows]].mean())
    r["mean4"] = float(np.mean([r[s] for s in SITES]))
    return r


def e1_checkpoint(pair, step, device_note="", agent=None, check_sweep=True):
    """All E1 numbers for one modulated checkpoint. Returns a flat row.

    `agent` (tests only) replaces the restored checkpoint, e.g. with a weight-edited model; such a
    model's episodes are not the sweep's, so the tests pass `check_sweep=False`."""
    import numpy as np
    from scripts.analysis.modulator_engagement import runs as R
    from scripts.analysis.nmn import replay
    om, MP = _om()
    sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
    from avoidance_stats_heatmap import episode_measures

    probe, n_ep, out_dir, labels = R.spec_scene(pair)
    p00, _, w00, bm00 = _world(probe, "avoid_none_inj00")
    p70, _, w70, bm70 = _world(probe, "avoid_none_inj70")
    seeds = _seeds(bm00, n_ep, p00)
    if _seeds(bm70, n_ep, p70) != seeds:
        raise ValueError("injured and unhurt scenes use different eval seeds")
    settle = felt_settle_value(w70)
    if abs(settle - E1_CONST) > 1e-6:
        raise ValueError(f"{p70}: settled felt injury {settle} != the plan's {E1_CONST}")
    if float(w00.start_injury_low) != 0.0 or float(w00.start_injury_high) != 0.0:
        raise ValueError(f"{p00}: not an unhurt scene")

    if agent is None:
        agent = replay.load_agent(os.path.join(pair.run_dirs["modulated"], "models"), step)
    br = agent.obs_breakdown
    const = MP.from_spec({"manipulations": [{"name": "felt_injury", "sensor": FELT, "element": 0, "op": "set",
                                             "values": [E1_CONST], "steps": [0, None]}]}, br, int(w00.max_steps))
    ident = MP.from_spec({"manipulations": [{"name": "felt_injury", "sensor": FELT, "element": 0, "op": "add",
                                             "values": [0.0], "steps": [0, None]}]}, br, int(w70.max_steps))
    N = len(seeds)
    r00 = om.run_checkpoint(agent, w00, seeds, const, "sustained", per_unit=True)
    r70 = om.run_checkpoint(agent, w70, seeds, ident, "sustained", per_unit=True)
    o00, o70, v00, v70 = r00["out"], r70["out"], r00["valid"], r70["valid"]
    nat, man = np.arange(N), np.arange(N, 2 * N)

    row = {"pair": pair.key, "group": pair.group, "level": pair.level, "seed": pair.seed,
           "run": pair.modulated, "step": int(step)}
    # parity with the sweep that produced the outcomes (identity = natural episodes)
    b00 = [_bush(episode_measures, r00["states0_np"], o00, b, r00["T"], om._snapshots) for b in nat]
    b70 = [_bush(episode_measures, r70["states0_np"], o70, b, r70["T"], om._snapshots) for b in nat]
    bman = [_bush(episode_measures, r00["states0_np"], o00, b, r00["T"], om._snapshots) for b in man]
    row["bush_nat00"], row["bush_nat70"], row["bush_const"] = map(float, (np.mean(b00), np.mean(b70), np.mean(bman)))
    for c, k in (("avoid_none_inj00", "bush_nat00"), ("avoid_none_inj70", "bush_nat70")):
        row[f"sweep_check_{c[-2:]}"] = (_check_sweep(row[k], out_dir, labels["modulated"], c, step, pair.key)
                                        if check_sweep else "skipped")

    # primary: constant 0.70, acting vs shadow on the acting trajectory
    for k, v in _site_means(o00, man, v00, "absdgain").items():
        row[f"e1g_{k}"] = v
    for k, v in _site_means(o00, man, v00, "absdoffset").items():
        row[f"e1b_{k}"] = v
    for k, v in _site_means(o00, man, v00, "gainsd").items():
        row[f"gainsd_{k}"] = v
    for kk in ("absdgain", "absdoffset"):      # identity condition: must be exactly zero
        z = max(float(np.abs(o00[f"{kk}_{s}"][:, nat]).max()) for s in SITES)
        if z != 0.0:
            raise AssertionError(f"{pair.key} step {step}: identity condition has |{kk}| = {z} != 0")

    # sensitivity: the recorded natural felt-injury trace
    felt = o70["felt_true"][:, nat, 0]
    row["felt_nat70_max"] = float(felt[v70[:, nat]].max())
    row["felt_nat70_steps_ge_0p65"] = float((felt[v70[:, nat]] >= 0.65).mean())
    groups = _trace_specs(felt, v70[:, nat], seeds)
    row["trace_groups"] = len(groups)
    acc = {f"{p}_{s}": [] for p in ("absdgain", "absdoffset") for s in SITES}
    wts = []
    for spec, gseeds, _idx, _tr in groups:
        Mt = MP.from_spec(spec, br, int(w00.max_steps), source="felt-injury trace")
        rt = om.run_checkpoint(agent, w00, gseeds, Mt, "sustained")
        n = len(gseeds)
        m_rows = np.arange(n, 2 * n)
        vv = rt["valid"][:, m_rows]
        wts.append(int(vv.sum()))
        for k in acc:
            acc[k].append(float(rt["out"][k][:, m_rows][vv].mean()))
    w = np.asarray(wts, float) / sum(wts)
    for p, tag in (("absdgain", "e1g_trace"), ("absdoffset", "e1b_trace")):
        vals = {s: float(np.dot(w, acc[f"{p}_{s}"])) for s in SITES}
        for s in SITES:
            row[f"{tag}_{s}"] = vals[s]
        row[f"{tag}_mean4"] = float(np.mean(list(vals.values())))

    # E1-natural: natural injured vs unhurt, step-aligned, steps live in both
    both = v00[:, nat] & v70[:, nat]
    for p, tag in (("ugain", "e1nat_g"), ("uoffset", "e1nat_b")):
        vals = {}
        for s in SITES:
            d = np.abs(o70[f"{p}_{s}"][:, nat] - o00[f"{p}_{s}"][:, nat]).mean(-1)
            vals[s] = float(d[both].mean())
            row[f"{tag}_{s}"] = vals[s]
        row[f"{tag}_mean4"] = float(np.mean(list(vals.values())))
    row["e1nat_steps"] = int(both.sum())
    row["device"] = device_note
    return row


# ------------------------------------------------------------------ E2 / E3
def e2_checkpoint(pair, step, seeds):
    import numpy as np
    from scripts.analysis.nmn import replay, mod_distribution as md
    agent = replay.load_agent(os.path.join(pair.run_dirs["modulated"], "models"), step)
    out = replay.rollout(agent, seeds)
    v = out["valid"]
    row = {"pair": pair.key, "group": pair.group, "level": pair.level, "seed": pair.seed,
           "run": pair.modulated, "step": int(step), "n_episodes": len(seeds),
           "mean_survival_steps": float(out["lengths"].mean())}
    for name, arr in (("g", out["gamma"]), ("b", out["beta"])):
        rhos = []
        for s in SITES:
            r = md.variance_split(arr[s], v)
            row[f"e2{name}_rho_{s}"] = r["rho"]
            row[f"e2{name}_var_total_{s}"] = r["var_total"]
            rhos.append(r["rho"])
        row[f"e2{name}_rho_mean4"] = float(np.mean(rhos))
    return row


def e3_checkpoint(pair, step, seeds, verify):
    """Live vs gain-frozen vs offset-frozen in the training world, paired survival steps."""
    import numpy as np
    from scripts.analysis.nmn import replay, freeze
    models = os.path.join(pair.run_dirs["modulated"], "models")
    agent = replay.load_agent(models, step)
    live = replay.rollout(agent, seeds)
    means = freeze.per_unit_time_means(live)
    row = {"pair": pair.key, "group": pair.group, "level": pair.level, "seed": pair.seed,
           "run": pair.modulated, "step": int(step), "n_episodes": len(seeds),
           "live_mean_survival": float(live["lengths"].mean())}
    # the weight-edit equivalence is proven once per run, on its first checkpoint; the column is
    # present on every row (empty when not run) so the per-checkpoint CSV keeps one schema
    row["equivalence_worst_deviation"] = ""
    if verify:
        rep = freeze.verify_freeze_equivalence(lambda: replay.load_agent(models, step), means, sorted(means))
        row["equivalence_worst_deviation"] = rep["worst_deviation"]
    for cond, fg, fo in (("freeze_gain", True, False), ("freeze_offset", False, True)):
        fa = replay.load_agent(models, step)
        freeze.apply_freeze(fa.model, means, freeze_gain=fg, freeze_offset=fo)
        out = replay.rollout(fa, seeds)
        _assert_frozen(out, means, fg, fo, f"{pair.key}/{step}/{cond}")
        pd_ = freeze.paired_differences(live["lengths"], out["lengths"])
        for k in ("mean_frozen", "mean_diff", "median_diff", "frac_episodes_changed", "sign_test_p"):
            row[f"e3_{cond}_{k}"] = pd_[k]
    return row


def _assert_frozen(out, means, fg, fo, what):
    """Frozen signals must be bit-constant at the requested target in the replay itself (as in
    run_freeze.py): catches an edit that did not take."""
    import numpy as np
    v = out["valid"]
    for site in out["gamma"]:
        for name, arr, on in (("gamma", out["gamma"][site], fg), ("beta", out["beta"][site], fo)):
            if not on:
                continue
            if float(np.ptp(arr[v], axis=0).max()) != 0.0:
                raise AssertionError(f"{what}: frozen {name} at {site} still varies")
            if float(np.abs(arr[v] - means[site][name][None, :]).max()) != 0.0:
                raise AssertionError(f"{what}: frozen {name} at {site} is not at the target")


# ------------------------------------------------------------------ E4
def _pooled_means(agent, worlds, seeds, om, MP):
    """Per-unit time-means of gain and offset pooled over the live (identity) passes in every
    world in `worlds` (every live step of every episode, all scenes together)."""
    import numpy as np
    acc, res = {}, {}
    for name, w in worlds.items():
        ident = MP.from_spec({"manipulations": [{"name": "felt_injury", "sensor": FELT, "element": 0,
                                                 "op": "add", "values": [0.0], "steps": [0, None]}]},
                             agent.obs_breakdown, int(w.max_steps))
        r = om.run_checkpoint(agent, w, seeds, ident, "sustained", per_unit=True)
        N = len(seeds)
        v = r["valid"][:, :N]
        res[name] = r
        for site in [k[len("ugain_"):] for k in r["out"] if k.startswith("ugain_")]:
            for p, key in (("ugain", "gamma"), ("uoffset", "beta")):
                acc.setdefault(site, {}).setdefault(key, []).append(r["out"][f"{p}_{site}"][:, :N][v])
    means = {s: {k: np.concatenate(v, 0).mean(0).astype(np.float32) for k, v in d.items()} for s, d in acc.items()}
    return means, res


def _save_edited(agent_model, src_models, dst_models, step):
    """Write the edited model as checkpoint `step` under dst_models (a fresh directory tree that
    mirrors the run's models/ metadata files). Refuses to write inside the source run."""
    import orbax.checkpoint as ocp
    from flax import nnx
    src_run = os.path.realpath(os.path.dirname(src_models))
    if os.path.realpath(dst_models).startswith(src_run + os.sep):
        raise ValueError(f"refusing to write edited checkpoints inside the source run {src_run}")
    os.makedirs(dst_models, exist_ok=True)
    for f in ("config.yaml", "provenance.json", "schedule.yaml"):
        s = os.path.join(src_models, f)
        if os.path.exists(s) and not os.path.exists(os.path.join(dst_models, f)):
            shutil.copy2(s, os.path.join(dst_models, f))
    if os.path.exists(os.path.join(dst_models, str(step))):
        raise FileExistsError(f"{dst_models}/{step} already exists")
    mngr = ocp.CheckpointManager(os.path.abspath(dst_models))
    mngr.save(step, args=ocp.args.PyTreeSave({"model": nnx.state(agent_model)}))
    mngr.wait_until_finished()


def e4_prepare_checkpoint(pair, step, ck_root):
    import numpy as np
    import jax
    from flax import nnx
    from scripts.analysis.modulator_engagement import runs as R
    from scripts.analysis.nmn import replay, freeze
    om, MP = _om()
    sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
    from avoidance_stats_heatmap import episode_measures

    probe, n_ep, out_dir, labels = R.spec_scene(pair)
    worlds, seeds = {}, None
    for c in E4_SCENES:
        p, _, w, bm = _world(probe, c)
        s = _seeds(bm, n_ep, p)
        if seeds is not None and s != seeds:
            raise ValueError("the two rabbit scenes use different eval seeds")
        seeds, worlds[c] = s, w
    models = os.path.join(pair.run_dirs["modulated"], "models")
    agent = replay.load_agent(models, step)
    means, live = _pooled_means(agent, worlds, seeds, om, MP)
    means = {s: v for s, v in means.items()}
    row = {"pair": pair.key, "group": pair.group, "level": pair.level, "seed": pair.seed,
           "run": pair.modulated, "step": int(step)}
    N = len(seeds)
    for c, r in live.items():
        b = float(np.mean([_bush(episode_measures, r["states0_np"], r["out"], i, r["T"], om._snapshots)
                           for i in range(N)]))
        row[f"live_bush_{c}"] = b
        row[f"sweep_check_{c}"] = _check_sweep(b, out_dir, labels["modulated"], c, step, pair.key)
    for head, fg, fo in (("freeze_gain", True, False), ("freeze_offset", False, True)):
        fa = replay.load_agent(models, step)
        freeze.apply_freeze(fa.model, means, freeze_gain=fg, freeze_offset=fo)
        dst = os.path.join(ck_root, f"{pair.modulated}__{head}", "models")
        _save_edited(fa.model, models, dst, step)
        # read back through the same loader the analysis tools use: bit-identical parameters, and
        # the frozen signal constant at the target in a live pass in the injured rabbit scene
        back = replay.load_agent(dst, step)
        a = jax.tree_util.tree_leaves(nnx.state(fa.model))
        b = jax.tree_util.tree_leaves(nnx.state(back.model))
        if len(a) != len(b) or any(not np.array_equal(np.asarray(x), np.asarray(y)) for x, y in zip(a, b)):
            raise AssertionError(f"{dst}/{step}: saved parameters differ from the edited model")
        w = worlds[E4_SCENES[0]]
        _, rr = _pooled_means(back, {E4_SCENES[0]: w}, seeds, om, MP)
        o, v = rr[E4_SCENES[0]]["out"], rr[E4_SCENES[0]]["valid"][:, :N]
        for site in means:
            for p, key, on in (("ugain", "gamma", fg), ("uoffset", "beta", fo)):
                if on:
                    x = o[f"{p}_{site}"][:, :N][v]
                    if float(np.abs(x - means[site][key][None, :]).max()) != 0.0:
                        raise AssertionError(f"{dst}/{step}: frozen {key} at {site} not constant at target")
        row[f"{head}_dir"] = os.path.relpath(os.path.dirname(dst), ROOT)
    np.savez_compressed(os.path.join(ck_root, f"targets_{pair.key}_{step}.npz"),
                        **{f"{s}/{k}": v for s, d in means.items() for k, v in d.items()})
    return row


def e4_write_specs(pairs, ck_root, sweep_out_root, spec_dir):
    """One dwell-sweep spec per source spec: same probe battery and episodes as the outcome
    sweep, only the two rabbit-wander scenes, the edited runs as `runs`. `nodes` must be filled
    in by whoever launches it (left empty so nothing launches by accident)."""
    from scripts.analysis.modulator_engagement import runs as R
    import yaml
    by_spec = {}
    for p in pairs:
        by_spec.setdefault(p.spec, []).append(p)
    written = []
    os.makedirs(spec_dir, exist_ok=True)
    for spec, ps in by_spec.items():
        src = R.load_spec(spec)
        name = "modeng_e4_" + os.path.splitext(os.path.basename(spec))[0].replace("_rppo", "")
        runs = []
        for p in ps:
            lab = R.spec_scene(p)[3]["modulated"]
            for head in ("freeze_gain", "freeze_offset"):
                runs.append({"label": f"{lab}__{head}",
                             "path": os.path.relpath(os.path.join(ck_root, f"{p.modulated}__{head}"), ROOT)})
        out = {"name": name, "algo": "rppo",
               "output_dir": os.path.relpath(os.path.join(sweep_out_root, name), ROOT),
               "probe": src["probe"], "conditions": list(E4_SCENES), "episodes": int(src["episodes"]),
               "nodes": [], "x_axis": src.get("x_axis", "steps"), "plot_measures": ["bush_hiding", "survival_steps"],
               "runs": runs}
        f = os.path.join(spec_dir, f"{name}_rppo.yaml")
        with open(f, "w") as fh:
            fh.write(f"# Modulator engagement check, E4 (generated by {os.path.relpath(__file__, ROOT)}).\n"
                     f"# Same probe battery and episodes as {spec}; weight-edited checkpoints only.\n"
                     f"# `nodes` is empty on purpose: fill it after checking gpu_status + the diary.\n")
            yaml.safe_dump(out, fh, sort_keys=False)
        written.append(f)
    return written


def e4_collect(pairs, spec_dir):
    """Per pair and checkpoint: the modulated agent's rabbit-scene injury effect (70 - 0, bush
    dwell pp), live (outcome sweep) vs gain-frozen vs offset-frozen (E4 sweep)."""
    import yaml
    from scripts.analysis.modulator_engagement import runs as R
    rows = []
    for p in pairs:
        _probe, _ep, out_dir, labels = R.spec_scene(p)
        name = "modeng_e4_" + os.path.splitext(os.path.basename(p.spec))[0].replace("_rppo", "")
        e4 = yaml.safe_load(open(os.path.join(spec_dir, f"{name}_rppo.yaml")))
        lab = labels["modulated"]
        ck =os.path.join(ROOT, os.path.dirname(e4["runs"][0]["path"]), f"{p.modulated}__freeze_gain", "models")
        steps = sorted(int(x) for x in os.listdir(ck) if x.isdigit())
        for st in steps:
            r = {"pair": p.key, "group": p.group, "level": p.level, "seed": p.seed, "step": st}
            for cond, (od, lb) in (("live", (out_dir, lab)),
                                   ("freeze_gain", (e4["output_dir"], f"{lab}__freeze_gain")),
                                   ("freeze_offset", (e4["output_dir"], f"{lab}__freeze_offset"))):
                a = _sweep_value(od, lb, E4_SCENES[0], st)
                b = _sweep_value(od, lb, E4_SCENES[1], st)
                r[f"injw_{cond}"] = None if (a is None or b is None) else 100.0 * (a - b)
            rows.append(r)
    return rows


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("measure", choices=["e1", "e2", "e3", "e4-prepare", "e4-collect"])
    ap.add_argument("--pairs", required=True, help="main | oos | all | comma-separated pair keys")
    ap.add_argument("--checkpoints", help="grid | every5 | steps:a,b (not for e4-collect)")
    ap.add_argument("--device", choices=["cpu", "gpu"], help="not for e4-collect")
    ap.add_argument("--out", required=True, help="output root (results/analysis/modulator_engagement)")
    ap.add_argument("--episodes", type=int, help="e2/e3: episodes in the training world")
    ap.add_argument("--seed-base", type=int, help="e2/e3: first episode seed (contiguous block)")
    a = ap.parse_args(argv)
    need = {"e1": ("checkpoints", "device"), "e2": ("checkpoints", "device", "episodes", "seed_base"),
            "e3": ("checkpoints", "device", "episodes", "seed_base"),
            "e4-prepare": ("checkpoints", "device"), "e4-collect": ()}[a.measure]
    miss = [k for k in need if getattr(a, k) is None]
    if miss:
        ap.error(f"{a.measure} requires " + ", ".join("--" + k.replace("_", "-") for k in miss))

    om, _ = _om()
    if a.device:
        om._set_device(a.device)
    sys.path.insert(0, ROOT)
    from scripts.analysis.modulator_engagement import runs as R
    pairs = R.select(a.pairs)
    R.validate(pairs)
    mdir = os.path.join(a.out, a.measure.split("-")[0])
    os.makedirs(mdir, exist_ok=True)

    if a.measure == "e4-collect":
        rows = e4_collect(pairs, os.path.join(mdir, "sweeps"))
        with open(os.path.join(mdir, "e4_effects.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {mdir}/e4_effects.csv")
        return

    seeds = None
    if a.measure in ("e2", "e3"):
        from scripts.analysis.nmn import replay
        seeds = replay.episode_seeds(a.episodes, a.seed_base)
    t0 = time.time()
    for p in pairs:
        models = os.path.join(p.run_dirs["modulated"], "models")
        ck = select_checkpoints(models, a.checkpoints)
        f = os.path.join(mdir, f"{p.key}.csv")
        done = _done(f)
        todo = [(g, s) for g, s in sorted(ck.items()) if s not in done]
        print(f"[{a.measure}] {p.key}: {len(ck)} checkpoints, {len(todo)} to do", flush=True)
        for i, (g, s) in enumerate(todo):
            t1 = time.time()
            if a.measure == "e1":
                row = e1_checkpoint(p, s, a.device)
            elif a.measure == "e2":
                row = e2_checkpoint(p, s, seeds)
            elif a.measure == "e3":
                row = e3_checkpoint(p, s, seeds, verify=(i == 0 and not done))
            else:
                row = e4_prepare_checkpoint(p, s, os.path.join(mdir, "ckpts", "JAX_RecurrentPPO"))
            row = {"grid_index": g, **row, "seconds": round(time.time() - t1, 1)}
            _append(f, row)
            print(f"  {p.key} step {s} (grid {g}): {time.time() - t1:.0f}s", flush=True)
        json.dump({"measure": a.measure, "pair": p.key, "modulated_run": p.modulated, "ordinary_run": p.ordinary,
                   "spec": p.spec, "checkpoints": a.checkpoints, "grid": {str(g): s for g, s in ck.items()},
                   "device": a.device, "episodes": a.episodes, "seed_base": a.seed_base,
                   "e1_constant": E1_CONST if a.measure == "e1" else None,
                   "e1_constant_how": ("start_injury / max_injury of the injured no-animal scene; checked per "
                                       "checkpoint: fixed start injury, felt-injury kernel sums to 1, no "
                                       "perceptual noise (felt_settle_value)") if a.measure == "e1" else None,
                   "sites": list(SITES), "git_sha": _sha(),
                   "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                  open(os.path.join(mdir, f"manifest_{p.key}.json"), "w"), indent=1)
    if a.measure == "e4-prepare":
        print("specs:", e4_write_specs(pairs, os.path.join(mdir, "ckpts", "JAX_RecurrentPPO"),
                                       os.path.join(ROOT, "results", "eval", "avoidance", "metrics_history_rppo_modeng_e4"),
                                       os.path.join(mdir, "sweeps")))
    print(f"[{a.measure}] done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
