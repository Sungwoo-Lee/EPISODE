"""Observation manipulation, REPLAY mode — recorded episodes fed back through the network.

The agent does not act. For each recorded episode, the network reads the observations it actually
received (`obs_noised`, row t = the input for the action recorded in row t+1 — the store's arrival
convention), once as recorded (the SHADOW) and once manipulated. Nothing downstream of the input
changes, so every difference — in move preferences, memory, and modulator output — is caused by the
manipulation holding the whole experienced history fixed.

Parity, always on and fatal: the shadow's greedy choice must equal the recorded action on every
step (the collector is greedy too). A mismatch means this is not the network, or not the input, the
store was made from.

Outputs in --out:
  summary.csv   one row per condition x bin of the NATURAL (recorded) value of the first manipulated
                input: steps, mean move preference per action (acting and natural), policy shift,
                memory disturbance, and for a modulated agent the change in mean gain/offset per site.
  episodes.csv  one row per condition x episode: means over the episode's steps.
  manifest.json
"""
from __future__ import annotations

import csv
import glob
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
TIE_LOG_RATIO = 0.01   # a flipped greedy choice is a tie only if the recorded move is the runner-up and
                       # the two preferences differ by under 1 % of each other (|log ratio| < 0.01)
BINS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]


def _scan(model, obs, h0, cond_rows, *, M, memory, modulated):
    """obs (T, B, D) already tiled per condition. MUST be entered through nnx.jit."""
    import jax
    import jax.numpy as jnp
    sys.path.insert(0, _HERE)
    import manip as MP
    from scripts.analysis.nmn.replay import SITE_FIELDS
    op = jnp.asarray(M.op)[cond_rows]
    val = jnp.asarray(M.value)[cond_rows]

    def body(carry, xs):
        h_act, h_sh = carry
        o, t = xs
        o_m = MP.apply(o, t, M.index, op, val, M.t0, M.t1)
        lg_s, _, h_sh_new, mod_s = model(o, h_sh)
        if memory == "sustained":
            lg_a, _, h_act_new, mod_a = model(o_m, h_act)
        else:
            lg_a, _, _, mod_a = model(o_m, h_sh)
            h_act_new = h_sh_new
        ta, ma = MP.split_memory(h_act_new, modulated)
        ts, ms = MP.split_memory(h_sh_new, modulated)
        rel = lambda a, b: jnp.linalg.norm(a - b, axis=-1) / (jnp.linalg.norm(b, axis=-1) + 1e-6)
        pa, ps = jax.nn.softmax(lg_a, -1), jax.nn.softmax(lg_s, -1)
        out = {"shadow_action": jnp.argmax(lg_s, -1), "p_act": pa, "p_shadow": ps,
               "policy_shift": 0.5 * jnp.abs(pa - ps).sum(-1), "d_task": rel(ta, ts),
               "felt_true": o[:, M.index]}
        if modulated:
            out["d_mod"] = rel(ma, ms)
            for site, (g, b) in SITE_FIELDS.items():
                if getattr(mod_a, g, None) is not None:
                    out[f"dgain_{site}"] = getattr(mod_a, g).mean(-1) - getattr(mod_s, g).mean(-1)
                    out[f"doffset_{site}"] = getattr(mod_a, b).mean(-1) - getattr(mod_s, b).mean(-1)
        return (h_act_new, h_sh_new), out

    T = obs.shape[0]
    return jax.lax.scan(body, (h0, h0), (obs, jnp.arange(T)))[1]


def run(a):
    import numpy as np
    import jax
    import jax.numpy as jnp
    import pyarrow.parquet as pq
    from flax import nnx
    from scripts.analysis.nmn import replay, ckpt_io
    import manip as MP

    run_dir = os.path.abspath(a.run)
    models = os.path.join(run_dir, "models")
    tag = os.path.basename(run_dir.rstrip("/"))
    hits = sorted(glob.glob(os.path.join(a.store, tag, "*", "*", "_manifest.json")))
    if len(hits) != 1:
        raise ValueError(f"expected exactly one store for {tag} under {a.store}, found {len(hits)}: {hits}")
    store = os.path.dirname(hits[0])
    man = json.load(open(hits[0]))
    step = int(man["ckpt_step"])
    D = int(man["dims"]["D"])
    if man["obs_precision"] != "float32":
        raise ValueError(f"{store}: obs_precision {man['obs_precision']}; parity needs float32")

    # the first --episodes episodes of the population, in shard order
    need, parts = a.episodes, []
    for f in sorted(glob.glob(os.path.join(store, "steps_*.parquet"))):
        tb = pq.read_table(f, columns=["episode_seed", "t", "action", "obs_noised"])
        parts.append(tb)
        if len(set(np.asarray(tb.column("episode_seed")))) >= need:
            break
    import pyarrow as pa
    tb = pa.concat_tables(parts)
    seed = np.asarray(tb.column("episode_seed")); t = np.asarray(tb.column("t"))
    act = np.asarray(tb.column("action"))
    ch = tb.column("obs_noised").chunks
    obs_flat = np.concatenate([c.flatten().to_numpy(zero_copy_only=False) for c in ch]).reshape(-1, D)
    seeds = list(dict.fromkeys(seed.tolist()))[:need]
    if len(seeds) < need:
        raise ValueError(f"{store}: only {len(seeds)} episodes available, {need} requested")
    sel = np.isin(seed, seeds)
    seed, t, act, obs_flat = seed[sel], t[sel], act[sel], obs_flat[sel]
    col = {s: i for i, s in enumerate(seeds)}
    e = np.array([col[s] for s in seed])
    L = np.zeros(need, int)
    np.maximum.at(L, e, t)                        # an episode of length T has rows t = 0..T
    Tmax = int(L.max())
    # input for decision k (k = 0..T-1) is row t = k; the recorded choice is action in row k+1
    obs = np.zeros((Tmax, need, D), np.float32)
    rec_action = np.full((Tmax, need), -1, np.int64)
    m_in = t < L[e]
    obs[t[m_in], e[m_in]] = obs_flat[m_in]
    m_out = t >= 1
    rec_action[t[m_out] - 1, e[m_out]] = act[m_out]
    valid = np.arange(Tmax)[:, None] < L[None, :]

    agent = replay.load_agent(models, step)
    if int(sum(agent.obs_breakdown.values())) != D:
        raise ValueError(f"store D={D} but agent input width {sum(agent.obs_breakdown.values())}")
    M = MP.load(a.manipulation, agent.obs_breakdown, Tmax)
    modulated = bool(agent.model.modulation_enabled)
    C, N = M.n, need
    cond_rows = np.repeat(np.arange(C), N)
    import functools
    fn = functools.partial(_scan, M=M, memory=a.memory, modulated=modulated)
    outs = []
    # chunk over conditions to bound memory: each chunk is all N episodes of one condition
    for c in range(C):
        h0 = agent.model.initial_state(batch_size=N)
        o = nnx.jit(fn)(agent.model, jnp.asarray(obs), h0, jnp.full((N,), c))
        outs.append(jax.tree_util.tree_map(np.asarray, o))
        if c == 0:
            mism = (outs[0]["shadow_action"] != rec_action) & valid
            n_bad = int(mism.sum())
            ties = []
            if n_bad:
                # A GPU forward pass at a different batch size rounds differently, and over hundreds of
                # recurrent steps the difference grows to ~1e-3 in the logits; on a decision the agent
                # rated two moves almost equally that flips the greedy choice. Such a step is accepted
                # only if the recorded move is the network's runner-up and the two preferences are
                # within 1 % of each other; anything else is a real mismatch and fatal.
                ps = outs[0]["p_shadow"]
                for tt, i in np.argwhere(mism):
                    order = np.argsort(ps[tt, i])[::-1]
                    runner_up = int(order[1]) == int(rec_action[tt, i])
                    gap = float(abs(np.log(ps[tt, i, order[0]]) - np.log(ps[tt, i, rec_action[tt, i]])))
                    gap = gap if runner_up else float("inf")
                    ties.append((int(tt), int(seeds[i]), gap, int(rec_action[tt, i]),
                                 int(outs[0]["shadow_action"][tt, i]), [float(q) for q in ps[tt, i]]))
                real = [x for x in ties if not x[2] < TIE_LOG_RATIO]
                if real:
                    raise RuntimeError(f"replay parity FAILED on {len(real)} of {int(valid.sum())} decisions "
                                       f"(not a runner-up within |log ratio| {TIE_LOG_RATIO}); first: step {real[0][0]}, "
                                       f"seed {real[0][1]}, gap {real[0][2]!r}, recorded action {real[0][3]}, "
                                       f"network's choice {real[0][4]}, preferences {real[0][5]}")
            tie_note = (f"; {len(ties)} near-tie flip(s), largest |log preference ratio| "
                        f"{max(x[2] for x in ties):.2g}" if ties else "")
            print(f"  replay parity: {int(valid.sum()) - len(ties)} of {int(valid.sum())} recorded decisions reproduced exactly{tie_note}")
            parity = {"decisions": int(valid.sum()),
                      "near_tie_flips": [dict(step=a, seed=b, gap=c, recorded=d, chosen=e) for a, b, c, d, e, _ in ties]}

    natural = outs[0]["felt_true"][..., 0]                       # (T, N) first manipulated input
    bins = np.digitize(natural, BINS) - 1
    A = outs[0]["p_act"].shape[-1]
    extra = sorted(k for k in outs[0] if k.startswith(("dgain_", "doffset_", "d_mod")))
    summ, eps = [], []
    for c in range(C):
        o = outs[c]
        for b in range(len(BINS) - 1):
            m = valid & (bins == b)
            if not m.any():
                continue
            r = {"condition": c, "label": M.labels[c], "natural_bin_lo": BINS[b],
                 "natural_bin_hi": min(BINS[b + 1], 1.0), "steps": int(m.sum()),
                 "policy_shift": float(o["policy_shift"][m].mean()), "d_task": float(o["d_task"][m].mean())}
            for k in range(A):
                r[f"p_act_{k}"] = float(o["p_act"][..., k][m].mean())
                r[f"p_nat_{k}"] = float(o["p_shadow"][..., k][m].mean())
            for k in extra:
                r[k] = float(o[k][m].mean())
            summ.append(r)
        for i in range(N):
            v = valid[:, i]
            r = {"condition": c, "label": M.labels[c], "episode_seed": seeds[i], "length": int(L[i]),
                 "policy_shift": float(o["policy_shift"][v, i].mean()), "d_task": float(o["d_task"][v, i].mean())}
            for k in extra:
                r[k] = float(o[k][v, i].mean())
            eps.append(r)

    os.makedirs(a.out, exist_ok=True)
    for name, rows in (("summary.csv", summ), ("episodes.csv", eps)):
        with open(os.path.join(a.out, name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    sha = subprocess.run(["git", "-C", _ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump({"mode": "replay", "run": run_dir, "store": store, "checkpoint": step, "episodes": N,
               "episode_seeds_first_last": [seeds[0], seeds[-1]], "memory": a.memory, "device": a.device,
               "manipulation_file": os.path.abspath(a.manipulation), "manipulation": M.spec,
               "conditions": M.labels, "bins_natural_first_input": BINS[:-1] + [1.0],
               "parity": parity, "tie_log_ratio": TIE_LOG_RATIO, "git_sha": sha},
              open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    print(f"wrote {a.out}/summary.csv ({len(summ)} rows) and episodes.csv ({len(eps)} rows)")
