"""Observation manipulation — run a trained agent with chosen inputs changed (see manip.py).

LIVE mode (this file): the agent plays greedy, seeded episodes in `--world` (a probe config, or
`training` for its own world). Every step the network sees the observation with the manipulation
applied; the world evolves from the true state. A SHADOW copy of the network is fed the true
observation of the same trajectory, giving (a) the natural memory for `--memory one_step` and (b)
the memory-disturbance readout: how far the acting network's recurrent state has moved from the
natural one, for the task GRU and the modulator's GRU separately.

Outputs in --out:
  episodes.csv   one row per checkpoint x condition x episode: the dwell sweep's own per-episode
                 measures (`episode_measures`, so numbers are directly comparable with every sweep
                 CSV), plus memory disturbance (mean/max over the episode) and the share of memory
                 units outside the range they take in the natural (identity) episodes.
  steps_<ckpt>.npz   with --record steps: per-step arrays (see `_scan`).
  manifest.json  run, checkpoints, world, seeds, device, memory mode, the manipulation file as
                 read, and the git SHA.

Checks, always on: the world's observation layout must equal the agent's sensor by sensor; the
identity condition (condition 0) must reproduce the shadow's actions exactly in every episode.
`--check-against-sweep DIR` additionally compares the identity condition, episode by episode,
with a dwell sweep's recordings for the same checkpoint (agent positions at every step, and the
measures) — the parity test that shows this tool measures the same episodes the sweeps do.

Survival steps, never reward.

Example:
  python scripts/analysis/obs_manipulation/run.py --mode live --run results/JAX_RecurrentPPO/<run> \\
      --checkpoints last:20 --world configs/.../avoid_none_inj00.yaml \\
      --manipulation scripts/analysis/obs_manipulation/examples/felt_injury_ladder.yaml \\
      --memory sustained --device cpu --record summary --out results/analysis/obs_manipulation/x
  python scripts/analysis/obs_manipulation/run.py --mode replay --run results/JAX_RecurrentPPO/<run> \\
      --store results/trajectories_basicq2_w2 --episodes 2000 --memory sustained --device gpu \\
      --manipulation scripts/analysis/obs_manipulation/examples/felt_injury_shift.yaml --out ...
"""
from __future__ import annotations

import argparse
import functools
import csv
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))


def _parse():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=["live", "replay"],
                    help="live: the agent acts in --world; replay: recorded episodes from --store "
                         "are fed back (see replay_mode.py)")
    ap.add_argument("--run", required=True, help="training run directory (contains models/)")
    ap.add_argument("--checkpoints", help="live only: 'all', 'last:N', or comma-separated steps")
    ap.add_argument("--world", help="live only: probe config path, or 'training'")
    ap.add_argument("--store", help="replay only: trajectory-store root holding this run's store")
    ap.add_argument("--manipulation", required=True, help="manipulation YAML (see manip.py)")
    ap.add_argument("--memory", required=True, choices=["sustained", "one_step"])
    ap.add_argument("--episodes", required=True, type=int,
                    help="episodes per condition; seeds are the world's behavior_measures.eval_seeds[:N]")
    ap.add_argument("--device", required=True, choices=["cpu", "gpu"])
    ap.add_argument("--record", choices=["summary", "steps"], help="live only")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-against-sweep", default=None,
                    help="a dwell-sweep scratch dir for this run+condition "
                         "(…/_scratch/<label>/<condition>); compares the identity condition")
    a = ap.parse_args()
    need = {"live": ("checkpoints", "world", "record"), "replay": ("store",)}[a.mode]
    miss = [k for k in need if getattr(a, k) is None]
    if miss:
        ap.error(f"--mode {a.mode} requires " + ", ".join("--" + k.replace("_", "-") for k in miss))
    wrong = [k for k in ("checkpoints", "world", "record", "store", "check_against_sweep")
             if k not in need and k != "check_against_sweep" and getattr(a, k) is not None]
    if a.mode == "replay" and a.check_against_sweep:
        wrong.append("check_against_sweep")
    if wrong:
        ap.error(f"--mode {a.mode} does not take " + ", ".join("--" + k.replace("_", "-") for k in wrong))
    return a


def _set_device(device):
    # Must run before jax is imported. CPU mirrors the dwell-sweep worker exactly
    # (scripts/eval/dwell_sweep/sweep_worker.sh), which is what makes exact parity possible.
    if device == "cpu":
        os.environ["JAX_PLATFORMS"] = "cpu"
        os.environ["XLA_FLAGS"] = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
        for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            os.environ[k] = "1"
    else:
        os.environ["JAX_PLATFORMS"] = "cuda"


def _scan(model, params, states0, h0, cond_rows, *, max_steps, M, memory, modulated):
    """Greedy rollout with manipulation. MUST be entered through nnx.jit (see replay.py)."""
    import jax
    import jax.numpy as jnp
    from src.environment.core import jax_step
    from src.environment.sensor import get_observation
    sys.path.insert(0, _HERE)
    import manip as MP

    v_step = jax.vmap(jax_step, in_axes=(0, 0, None))
    v_obs = jax.vmap(get_observation, in_axes=(0, None))
    op = jnp.asarray(M.op)[cond_rows]            # (B, K)
    val = jnp.asarray(M.value)[cond_rows]

    def body(carry, t):
        state, h_act, h_sh = carry
        obs = v_obs(state, params)
        obs_m = MP.apply(obs, t, M.index, op, val, M.t0, M.t1)
        lg_s, _, h_sh_new, _ = model(obs, h_sh)
        if memory == "sustained":
            lg_a, v_a, h_act_new, mod = model(obs_m, h_act)
        else:
            lg_a, v_a, _, mod = model(obs_m, h_sh)
            h_act_new = h_sh_new
        action = jnp.argmax(lg_a, axis=-1)
        nxt, _r, done, _info = v_step(state, action, params)
        ta, ma = MP.split_memory(h_act_new, modulated)
        ts, ms = MP.split_memory(h_sh_new, modulated)
        rel = lambda a, b: jnp.linalg.norm(a - b, axis=-1) / (jnp.linalg.norm(b, axis=-1) + 1e-6)
        out = {"action": action, "shadow_action": jnp.argmax(lg_s, axis=-1), "done": done,
               "agent_pos": nxt.agent_pos, "animal_pos": nxt.animal_pos,
               "injury": nxt.injury_level,
               "felt_true": obs[:, M.index], "felt_given": obs_m[:, M.index],
               "p_act": jax.nn.softmax(lg_a, -1), "p_shadow": jax.nn.softmax(lg_s, -1),
               "d_task": rel(ta, ts), "h_task": ta, "h_task_shadow": ts}
        # policy shift: total-variation distance between the acting and the natural move preferences
        out["policy_shift"] = 0.5 * jnp.abs(out["p_act"] - out["p_shadow"]).sum(-1)
        if modulated:
            from scripts.analysis.nmn.replay import SITE_FIELDS
            for site, (g, b) in SITE_FIELDS.items():
                if getattr(mod, g, None) is not None:       # mean over units of gain and offset
                    out[f"gain_{site}"] = getattr(mod, g).mean(-1)
                    out[f"offset_{site}"] = getattr(mod, b).mean(-1)
            out["d_mod"] = rel(ma, ms)
            out["h_mod"] = ma
            out["h_mod_shadow"] = ms
        return (nxt, h_act_new, h_sh_new), out

    return jax.lax.scan(body, (states0, h0, h0), jnp.arange(max_steps))[1]


def _snapshots(states0, out, i, T):
    """The per-episode snapshot list in the dwell sweep's recording format (initial + T steps)."""
    import numpy as np
    obs_pos = np.asarray(states0.obs_pos[i])
    S = [{"agent_pos": np.asarray(states0.agent_pos[i]), "animal_pos": np.asarray(states0.animal_pos[i]),
          "obs_pos": obs_pos, "injury_level": float(states0.injury_level[i])}]
    for t in range(T):
        S.append({"agent_pos": out["agent_pos"][t, i], "animal_pos": out["animal_pos"][t, i],
                  "obs_pos": obs_pos, "injury_level": float(out["injury"][t, i])})
    return S


def main():
    a = _parse()
    _set_device(a.device)
    sys.path.insert(0, _ROOT)
    sys.path.insert(0, _HERE)
    sys.path.insert(0, os.path.join(_ROOT, "scripts", "behavior_measures"))
    if a.mode == "replay":
        import replay_mode
        return replay_mode.run(a)
    import numpy as np
    import jax
    import jax.numpy as jnp
    from flax import nnx
    from src.environment.config_loader import (Config, load_env_config, load_env_params,
                                               load_behavior_measure_cfg)
    from src.environment.sensor import get_observation_breakdown
    from src.environment.core import jax_reset
    from scripts.analysis.nmn import replay, ckpt_io
    from avoidance_stats_heatmap import episode_measures
    import manip as MP

    models = os.path.join(os.path.abspath(a.run), "models")
    steps = ckpt_io.list_steps(models)
    if a.checkpoints == "all":
        ck = steps
    elif a.checkpoints.startswith("last:"):
        ck = steps[-int(a.checkpoints.split(":")[1]):]
    else:
        ck = [int(s) for s in a.checkpoints.split(",")]
        bad = [s for s in ck if s not in steps]
        if bad:
            raise ValueError(f"checkpoints {bad} not saved under {models}")

    world_cfg = (Config.load_yaml(os.path.join(models, "config.yaml")) if a.world == "training"
                 else load_env_config(a.world))
    params = load_env_params(world_cfg)
    bm = load_behavior_measure_cfg(world_cfg)
    if bm is None:
        raise ValueError(f"{a.world}: no behavior_measures block, so no eval_seeds to draw from")
    if len(bm.eval_seeds) < a.episodes:
        raise ValueError(f"{a.world}: only {len(bm.eval_seeds)} eval_seeds for {a.episodes} episodes")
    seeds = [int(s) for s in bm.eval_seeds[:a.episodes]]
    max_steps = int(params.max_steps)

    os.makedirs(a.out, exist_ok=True)
    rows, t_start = [], time.time()
    M = None
    for step in ck:
        agent = replay.load_agent(models, step)
        wb = get_observation_breakdown(params)
        if list(wb.items()) != list(agent.obs_breakdown.items()):
            raise ValueError(f"world observation layout {wb} != agent's {agent.obs_breakdown}")
        if M is None:
            M = MP.load(a.manipulation, agent.obs_breakdown, max_steps)
        modulated = bool(agent.model.modulation_enabled)
        C, N = M.n, len(seeds)
        keys = jnp.stack([jax.random.PRNGKey(s) for s in seeds])
        s0 = jax.vmap(jax_reset, in_axes=(None, 0))(params, keys)
        for i, s in enumerate(seeds):                     # same parity guard as eval_rollout
            if not bool(jnp.array_equal(s0.key[i], jax_reset(params, jax.random.PRNGKey(s)).key)):
                raise RuntimeError(f"batched reset PRNG parity failed at seed {s}")
        states0 = jax.tree_util.tree_map(lambda x: jnp.concatenate([x] * C, 0), s0)
        cond_rows = np.repeat(np.arange(C), N)             # batch row b -> condition b // N
        h0 = agent.model.initial_state(batch_size=C * N)
        # M, max_steps, memory and modulated are closed over (static), not traced
        fn = functools.partial(_scan, max_steps=max_steps, M=M, memory=a.memory, modulated=modulated)
        out = nnx.jit(fn)(agent.model, params, states0, h0, jnp.asarray(cond_rows))
        out = jax.tree_util.tree_map(np.asarray, out)
        states0_np = jax.tree_util.tree_map(np.asarray, states0)
        T = np.argmax(out["done"], axis=0) + 1
        valid = np.arange(max_steps)[:, None] < T[None, :]

        # identity condition must act exactly like the shadow (same inputs, same memory)
        idb = np.arange(N)
        mism = (out["action"][:, idb] != out["shadow_action"][:, idb]) & valid[:, idb]
        if mism.any():
            raise RuntimeError(f"checkpoint {step}: identity condition diverged from the shadow "
                               f"in {int(mism.any(0).sum())} episode(s) -- the manipulation path "
                               f"alters an untouched observation")

        # natural memory range per unit: every shadow state (true inputs) on every valid step of
        # every condition -- the memory this agent reaches without manipulation, on these trajectories
        def outside(key_act, key_sh):
            nat = out[key_sh][valid]                                   # (n_steps, units)
            lo, hi = nat.min(0), nat.max(0)
            x = out[key_act]
            return ((x < lo) | (x > hi)).mean(-1)                        # (T, B)
        oor_task = outside("h_task", "h_task_shadow")
        oor_mod = outside("h_mod", "h_mod_shadow") if modulated else None

        for b in range(C * N):
            c, e = divmod(b, N)
            Ti = int(T[b]); v = valid[:Ti, b]
            meas = episode_measures({"snapshots": _snapshots(states0_np, out, b, Ti)})
            r = {"checkpoint": step, "condition": c, "label": M.labels[c], "seed": seeds[e], **meas,
                 "d_task_mean": float(out["d_task"][:Ti, b].mean()),
                 "d_task_max": float(out["d_task"][:Ti, b].max()),
                 "out_of_range_task": float(oor_task[:Ti, b].mean()),
                 "policy_shift_mean": float(out["policy_shift"][:Ti, b].mean())}
            if modulated:
                r.update(d_mod_mean=float(out["d_mod"][:Ti, b].mean()),
                         d_mod_max=float(out["d_mod"][:Ti, b].max()),
                         out_of_range_mod=float(oor_mod[:Ti, b].mean()))
            rows.append(r)
        if a.record == "steps":
            keep = {k: v for k, v in out.items() if not k.startswith("h_")}
            np.savez_compressed(os.path.join(a.out, f"steps_{step}.npz"), T=T, cond_rows=cond_rows,
                                seeds=np.asarray(seeds), **keep)

        if a.check_against_sweep:
            _parity(a.check_against_sweep, step, seeds, states0_np, out, T, N, episode_measures)
        print(f"  checkpoint {step}: {C} conditions x {N} episodes  ({time.time() - t_start:.0f}s)", flush=True)

    keys_all = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 999)
    with open(os.path.join(a.out, "episodes.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys_all)
        w.writeheader(); w.writerows(rows)
    sha = subprocess.run(["git", "-C", _ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump({"run": os.path.abspath(a.run), "checkpoints": ck, "world": a.world, "seeds": seeds,
               "episodes": a.episodes, "memory": a.memory, "device": a.device, "record": a.record,
               "max_steps": max_steps, "manipulation_file": os.path.abspath(a.manipulation),
               "manipulation": M.spec, "conditions": M.labels, "git_sha": sha,
               "parity_checked_against": a.check_against_sweep},
              open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    print(f"wrote {len(rows)} rows to {a.out}/episodes.csv")


def _parity(sweep_dir, step, seeds, states0_np, out, T, N, episode_measures):
    """Identity condition vs the dwell sweep's recordings, episode by episode. Fatal on mismatch."""
    import glob
    import numpy as np
    from src.utils.eval_recording import load_episode
    recs = sorted(glob.glob(os.path.join(sweep_dir, str(step), "*", str(step), "recordings",
                                         str(step), "episode_*.rec.gz")))
    if len(recs) != N:
        raise RuntimeError(f"parity: found {len(recs)} sweep recordings for checkpoint {step} "
                           f"under {sweep_dir}, expected {N}")
    bad = []
    for i, p in enumerate(recs):
        ep = load_episode(p)
        if int(ep["seed"]) != seeds[i]:
            raise RuntimeError(f"parity: recording {i} has seed {ep['seed']}, tool used {seeds[i]}")
        S_ref = ep["snapshots"]
        S = _snapshots(states0_np, out, i, int(T[i]))
        if len(S) != len(S_ref):
            bad.append(f"seed {seeds[i]}: length {len(S) - 1} vs sweep {len(S_ref) - 1}")
            continue
        for t, (x, y) in enumerate(zip(S, S_ref)):
            if not np.array_equal(np.asarray(x["agent_pos"]), np.asarray(y["agent_pos"])):
                bad.append(f"seed {seeds[i]}: agent position differs first at step {t}")
                break
        m, m_ref = episode_measures({"snapshots": S}), episode_measures(ep)
        for k in ("bush_hiding", "survival_steps", "time_near_animal"):
            if not (np.isnan(m[k]) and np.isnan(m_ref[k])) and m[k] != m_ref[k]:
                bad.append(f"seed {seeds[i]}: {k} {m[k]} vs sweep {m_ref[k]}")
    if bad:
        raise RuntimeError(f"parity with the dwell sweep FAILED at checkpoint {step}:\n  " + "\n  ".join(bad))
    print(f"  parity with the dwell sweep: {N}/{N} episodes identical at checkpoint {step}")


if __name__ == "__main__":
    main()
