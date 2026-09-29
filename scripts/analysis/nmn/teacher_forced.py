"""Teacher-forced replay: feed a probe's stored observations through an agent, keep its layers.

Plain-language purpose: a trajectory store records, for every step of every episode, the
exact observation the agent that generated it saw. Replaying those observations through a
network ("teacher forcing") shows what that network computes on exactly those inputs, and
lets any two networks be compared on identical inputs. The memory is rebuilt from the first
step of each episode, and depends only on the stored inputs, never on the replayed actions,
so a disagreement at one step cannot compound.

What is checked, because nothing downstream could notice if it were wrong:
* **Self-replay agreement.** An agent replayed on its OWN store must choose the stored
  action at every decision row (action at row t+1 = argmax of its logits at row t), except
  near-ties within gate G1's allowance. Logits and values are not stored, so this is the
  only link from the captured tensors to stored ground truth.
* **Alignment controls** on the probe's sampled rows, through the probe's own row index:
  step-discontinuous (argmax at row == `action_next[row]`, 100 %, on all sampled rows and on
  action-change rows) and shift-by-one (argmax at row == `action[t]`, which must be low).
* **Chain assertions** on the real checkpoint (plan finding 3): every captured tensor is
  recomputed from its upstream neighbour with the model's own submodules, in a separate
  jitted program, on `assert_n_episodes` whole episodes. A key bound to the wrong tensor
  fails at least one link.

Every entry to the model goes through `nnx.jit` (a restored NNX model called eagerly reads a
stale view of its parameters; see scripts/eval/eval_rollout.py::_rollout_scan_jit).

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §4.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

SITE_OF = {"enc.uni": ("z_unimodal", "z_unimodal_add"), "enc": ("z_multimodal", "z_multimodal_add"),
           "rnn": ("z_rnn", "z_rnn_add"), "actor": ("z_actor", "z_actor_add"),
           "critic": ("z_critic", "z_critic_add")}


# ───────────────────────────────── scans (must be entered through nnx.jit) ──
def _scan_sampled(model, obs, slots, h0, keys: tuple, n_slots: int):
    """Scan over time; write the requested layers only at sampled (t, episode) slots.

    obs (T, B, D); slots (T, B) int32, the slot index 0..n_slots-1 of a sampled row, or
    n_slots (dropped) otherwise. Returns buffers {key: (B, n_slots, W)} plus per-step argmax
    and top-two logit margin (T, B)."""
    import jax
    import jax.numpy as jnp

    B = obs.shape[1]
    probe_out = model.forward_with_activations(obs[0], h0)[4]
    bufs = {k: jnp.zeros((B, n_slots, int(np.prod(probe_out[k].shape[1:]))), jnp.float32)
            for k in keys}
    bidx = jnp.arange(B)

    def step(carry, xs):
        h, bufs = carry
        x, slot = xs
        logits, _v, h_new, _m, acts = model.forward_with_activations(x, h)
        new = {k: bufs[k].at[bidx, slot].set(acts[k].reshape(B, -1).astype(jnp.float32),
                                             mode="drop") for k in keys}
        top2 = jax.lax.top_k(logits, 2)[0]
        return (h_new, new), (jnp.argmax(logits, axis=-1).astype(jnp.int32),
                              top2[..., 0] - top2[..., 1])

    (_, bufs), (amax, margin) = jax.lax.scan(step, (h0, bufs), (obs, slots))
    return bufs, amax, margin


def _scan_full(model, obs, h0):
    """Scan capturing EVERY key and the modulator output at every step (small batches)."""
    import jax

    def step(h, x):
        _l, _v, h_new, mod, acts = model.forward_with_activations(x, h)
        return h_new, (acts, mod)
    return jax.lax.scan(step, h0, obs)[1]


def _chain(model, obs, acts, mod):
    """Recompute each captured tensor from its upstream neighbour. Arrays are (T, B, ...).
    Returns {assertion name: (recomputed, captured)}."""
    import jax
    import jax.numpy as jnp

    enc = model.obs_encoder
    x = jnp.sign(obs) * jnp.log(jnp.abs(obs) + 1.0)
    uni_ln = getattr(model, "mod_unimodal_ln", None)
    multi_ln = getattr(model, "mod_multimodal_ln", None)
    flat_ln = getattr(model, "mod_flat_ln", None)
    mtype = model.modulation_type
    enc_on = model.modulation_enabled and model.site_encoder
    out = {}

    def film(stage_key, raw, gain_field, add_field, expand):
        g, b = getattr(mod, gain_field), getattr(mod, add_field)
        if expand:
            g = g[..., None, :]
            b = None if b is None else b[..., None, :]
        if mtype == "FiLM":
            return g * raw + b
        if mtype == "PreActivation":
            return raw * jax.nn.sigmoid(g) + b
        return jax.nn.relu(raw) * jax.nn.sigmoid(g)          # Multiplicative (post-ReLU gate)

    def post(mod_t):
        return mod_t if mtype == "Multiplicative" else jax.nn.relu(mod_t)

    if enc.mode == "hierarchical":
        batch_shape = x.shape[:-1]
        xp = jnp.zeros(batch_shape + (len(enc.names), enc.max_in), dtype=x.dtype)
        start = 0
        for i, (_n, dim) in enumerate(enc.breakdown.items()):
            xp = xp.at[..., i, :dim].set(x[..., start:start + dim])
            start += dim
        u = enc.unimodal_grouped(xp)
        if uni_ln is not None:
            u = jax.vmap(uni_ln, in_axes=-2, out_axes=-2)(u)
        out["enc.uni.raw"] = (u, acts["enc.uni.raw"])
        if enc_on:
            out["enc.uni.mod"] = (film("enc.uni", acts["enc.uni.raw"], "z_unimodal",
                                       "z_unimodal_add", True), acts["enc.uni.mod"])
            out["enc.uni.out"] = (post(acts["enc.uni.mod"]), acts["enc.uni.out"])
        else:
            out["enc.uni.out"] = (jax.nn.relu(acts["enc.uni.raw"]), acts["enc.uni.out"])
        mm = enc.multimodal_hub(acts["enc.uni.out"].reshape(batch_shape + (-1,)))
        if multi_ln is not None:
            mm = multi_ln(mm)
        out["enc.raw"] = (mm, acts["enc.raw"])
        gain, add = "z_multimodal", "z_multimodal_add"
    else:
        xp = enc.monolith(x)
        if flat_ln is not None:
            xp = flat_ln(xp)
        out["enc.raw"] = (xp, acts["enc.raw"])
        gain, add = "z_unimodal", "z_unimodal_add"             # flat mode uses stage-1 fields
    if enc_on:
        out["enc.mod"] = (film("enc", acts["enc.raw"], gain, add, False), acts["enc.mod"])
        out["enc.out"] = (post(acts["enc.mod"]), acts["enc.out"])
    else:
        out["enc.out"] = (jax.nn.relu(acts["enc.raw"]), acts["enc.out"])

    # memory: (state, raw) == rnn_cell(state[t-1], enc.out[t]); state[-1] = initial_state
    if model.rnn_type == "LSTM":
        raise NotImplementedError("chain assertions: LSTM cells are not supported")
    B = obs.shape[1]
    h_init = jnp.zeros((1, B, model.hidden_size), acts["rnn.state"].dtype)
    h_prev = jnp.concatenate([h_init, acts["rnn.state"][:-1]], axis=0)
    if model.modulation_enabled and model._uses_gate_bias:
        h_new, y = model.rnn_cell(h_prev, acts["enc.out"], gate_bias=mod.z_memory)
    else:
        h_new, y = model.rnn_cell(h_prev, acts["enc.out"])
    out["rnn.state"] = (h_new, acts["rnn.state"])
    out["rnn.raw"] = (y, acts["rnn.raw"])
    if "rnn.mod" in acts:
        out["rnn.mod"] = (mod.z_rnn * acts["rnn.raw"] + mod.z_rnn_add, acts["rnn.mod"])
        out["rnn.out"] = (acts["rnn.mod"], acts["rnn.out"])
    else:
        out["rnn.out"] = (acts["rnn.raw"], acts["rnn.out"])

    for head, fc1 in (("actor", model.actor_fc1), ("critic", model.critic_fc1)):
        out[f"{head}.raw"] = (fc1(acts["rnn.out"]), acts[f"{head}.raw"])
        if f"{head}.mod" in acts:
            g, b = getattr(mod, f"z_{head}"), getattr(mod, f"z_{head}_add")
            out[f"{head}.mod"] = (g * acts[f"{head}.raw"] + b, acts[f"{head}.mod"])
            pre = acts[f"{head}.mod"]
        else:
            pre = acts[f"{head}.raw"]
        out[f"{head}.out"] = (model._activate(pre), acts[f"{head}.out"])
    lg = model.actor_fc2(acts["actor.out"])
    if model.modulation_enabled and model.temperature_enabled:
        lg = lg / mod.temperature
    out["logits"] = (lg, acts["logits"])
    out["value"] = (model.critic_fc2(acts["critic.out"]), acts["value"])
    return out


def chain_deviations(model, obs, acts, mod) -> dict:
    """{assertion: max|recomputed - captured| / max(1, max|captured|)} over (T, B, ...).
    `obs` is (T, B, D) raw observations; `acts`, `mod` from `_scan_full` on the same batch
    (initial memory at t = 0). Runs as its own nnx.jit program."""
    import jax.numpy as jnp
    from flax import nnx

    def f(m, obs, acts, mod):
        pairs = _chain(m, obs, acts, mod)
        return {k: jnp.max(jnp.abs(r - c)) / jnp.maximum(1.0, jnp.max(jnp.abs(c)))
                for k, (r, c) in pairs.items()}
    dev = nnx.jit(f)(model, obs, acts, mod)
    return {k: float(v) for k, v in dev.items()}


# ─────────────────────────────────────────────────────────────── replay ──
def _near_tie_rule(agree, margin, *, min_agree, tie_margin, tie_frac_max):
    """Gate G1 / G3 as the rules word them: agreement on at least `min_agree` of rows,
    except near-ties (top-two margin < tie_margin), which may disagree on at most
    `tie_frac_max` of rows."""
    n = int(agree.size)
    dis = ~agree
    near = margin < tie_margin
    hard, tie = int((dis & ~near).sum()), int((dis & near).sum())
    ok = n > 0 and (1.0 - hard / n) >= min_agree and tie / n <= tie_frac_max
    return {"rows": n, "agree": int(agree.sum()), "agreement": (float(agree.mean()) if n else None),
            "disagree_not_near_tie": hard, "disagree_near_tie": tie,
            "near_tie_disagree_fraction": (tie / n if n else None), "pass": bool(ok)}


def replay(agent, probe, layers: list, *, batch_size: int, is_generating: bool, g1: dict,
           g3: dict, g2_tol: float, shift_change_rows_max: float, assert_n_episodes: int,
           store_id_of_agent: int | None, capture_precision: str,
           check_precision: str | None) -> tuple[dict, dict]:
    """Replay every probe episode through `agent` (scripts.analysis.nmn.replay.LoadedAgent).

    `layers`: canonical keys to keep at the probe's sampled rows (a `.mod` key the agent does
    not have is skipped and reported). `is_generating`: the agent/checkpoint wrote store
    `store_id_of_agent` of this probe; then G1 self-agreement and the alignment controls are
    enforced on that store's episodes. All constants are passed in (rules `parameters:` and
    the manifest's `tool_checks`). Returns ({key: (n_rows, W) float32}, report). The report's
    'failures' lists every enforced check that failed; the caller aborts on any.

    Matmul precision (found in Stage 2, 2026-09-30): a store reproduces bit-for-bit only under
    the float32 matmul mode it was collected with. On an Ampere/Ada GPU JAX's default mode is
    TF32; a Turing GPU or the CPU compute full float32. The w0000 modulated store (collected
    on an RTX 3090) disagrees with a full-float32 replay on 0.2 % of rows at logit margins up
    to 0.08, and agrees 100 % under TF32; the ordinary store (RTX 2080 Ti) is the reverse. So
    the self-replay checks (G1, G3, shift) run under `check_precision`, the store's own
    collection mode, and the kept activations and chain assertions run under
    `capture_precision` (one mode for every agent, so all activations are comparable).
    Values are `jax.default_matmul_precision` names ("highest", "default")."""
    import jax
    import jax.numpy as jnp
    from flax import nnx

    model = agent.model
    D = probe.obs_all.shape[1]
    input_dim = sum(agent.obs_breakdown.values())
    if D != input_dim:
        raise ValueError(f"probe observation width {D} != model input_dim {input_dim}")
    T_max = int(agent.env_params.max_steps)
    if int(probe.ep_T.max()) > T_max:
        raise ValueError(f"probe episode length {int(probe.ep_T.max())} > max_steps {T_max}")

    h_test = model.initial_state(1)
    avail = set(nnx.jit(lambda m, x, h: m.forward_with_activations(x, h)[4])(
        model, jnp.zeros((1, D), jnp.float32), h_test))
    keys, skipped = [], []
    for k in layers:
        if k in avail:
            keys.append(k)
        elif k.endswith(".mod"):
            skipped.append(k)
        else:
            raise ValueError(f"layer {k!r} not produced by this agent (has {sorted(avail)})")
    keys = tuple(keys)

    E = probe.ep_T.size
    row_ep = probe.row_episode
    row_t = probe.row_t
    n_slots = int(np.bincount(row_ep, minlength=E).max())
    slot_of_row = np.zeros(probe.rows.size, np.int64)
    first_row = np.searchsorted(row_ep, np.arange(E), side="left")
    slot_of_row = np.arange(probe.rows.size) - first_row[row_ep]

    scan = nnx.jit(_scan_sampled, static_argnames=("keys", "n_slots"))

    def _pass(keys, precision):
        with jax.default_matmul_precision(precision):
            return _replay_pass(scan, model, probe, keys, n_slots, slot_of_row, row_ep, row_t,
                                T_max, D, batch_size)

    acts_rows, amax_all, margin_all = _pass(keys, capture_precision)
    if is_generating and check_precision != capture_precision:
        _, amax_chk, margin_chk = _pass((), check_precision)
    else:
        amax_chk, margin_chk = amax_all, margin_all
    report = _checks(probe, acts_rows, keys, skipped, n_slots, amax_all, margin_all, amax_chk,
                     margin_chk, is_generating=is_generating, store_id_of_agent=store_id_of_agent,
                     g1=g1, g3=g3, shift_change_rows_max=shift_change_rows_max)
    report["capture_precision"], report["check_precision"] = capture_precision, check_precision
    with jax.default_matmul_precision(capture_precision):
        _chain_section(model, probe, acts_rows, keys, row_ep, row_t, report,
                       assert_n_episodes=assert_n_episodes, g2_tol=g2_tol)
    return acts_rows, report


def _replay_pass(scan, model, probe, keys, n_slots, slot_of_row, row_ep, row_t, T_max, D,
                 batch_size):
    import jax.numpy as jnp
    E = probe.ep_T.size
    acts_rows = {}
    amax_all = np.empty(probe.t_all.size, np.int32)
    margin_all = np.empty(probe.t_all.size, np.float32)
    out_bufs = {k: [] for k in keys}
    for b0 in range(0, E, batch_size):
        eps = np.arange(b0, min(b0 + batch_size, E))
        B = eps.size
        obs = np.zeros((T_max, B, D), np.float32)
        slots = np.full((T_max, B), n_slots, np.int32)
        for j, e in enumerate(eps):
            off, T = int(probe.ep_offset[e]), int(probe.ep_T[e])
            obs[:T, j] = probe.obs_all[off:off + T]
        sel = (row_ep >= eps[0]) & (row_ep <= eps[-1])
        slots[row_t[sel], row_ep[sel] - eps[0]] = slot_of_row[sel]
        h0 = model.initial_state(B)
        bufs, amax, margin = scan(model, jnp.asarray(obs), jnp.asarray(slots), h0,
                                  keys=keys, n_slots=n_slots)
        amax, margin = np.asarray(amax), np.asarray(margin)
        for j, e in enumerate(eps):
            off, T = int(probe.ep_offset[e]), int(probe.ep_T[e])
            amax_all[off:off + T] = amax[:T, j]
            margin_all[off:off + T] = margin[:T, j]
        rsel = np.flatnonzero(sel)
        for k in keys:
            bk = np.asarray(bufs[k])
            out_bufs[k].append(bk[row_ep[rsel] - eps[0], slot_of_row[rsel]])
    for k in keys:
        acts_rows[k] = np.concatenate(out_bufs[k]).astype(np.float32)
    return acts_rows, amax_all, margin_all


def _checks(probe, acts_rows, keys, skipped, n_slots, amax_all, margin_all, amax_chk,
            margin_chk, *, is_generating, store_id_of_agent, g1, g3, shift_change_rows_max):
    E = probe.ep_T.size
    report = {"layers_kept": list(keys), "layers_skipped_absent_mod": skipped,
              "n_rows": int(probe.rows.size), "n_slots_max": n_slots,
              "probe_row_index_sha256": probe.row_sha256, "failures": []}

    # buffer path vs index path: the argmax of the captured logits at the sampled rows must
    # equal the per-step argmax gathered through the probe's row index
    if "logits" in keys:
        cons = np.argmax(acts_rows["logits"], axis=-1) == amax_all[probe.rows]
        report["buffer_vs_index_argmax_agreement"] = float(cons.mean())
        if not cons.all():
            report["failures"].append("sampled-row buffer and row-index argmax disagree")

    # ---- action agreement over ALL decision rows, per source store --------------------
    ep_of_all = np.repeat(np.arange(E), probe.ep_T)
    by_store = {}
    for sid in np.unique(probe.ep_store):
        m = probe.ep_store[ep_of_all] == sid
        by_store[int(sid)] = _near_tie_rule(
            amax_all[m] == probe.action_next_all[m], margin_all[m],
            min_agree=g1["action_agreement_min"], tie_margin=g1["near_tie_logit_margin"],
            tie_frac_max=g1["near_tie_fraction_max"])
    report["action_agreement_all_decision_rows_by_store (capture precision)"] = by_store
    report["is_generating_agent_of_store"] = store_id_of_agent if is_generating else None

    # ---- self-replay (G1) and alignment controls, at the store's own precision ---------
    if is_generating:
        m = probe.ep_store[ep_of_all] == store_id_of_agent
        g1_res = _near_tie_rule(
            amax_chk[m] == probe.action_next_all[m], margin_chk[m],
            min_agree=g1["action_agreement_min"], tie_margin=g1["near_tie_logit_margin"],
            tie_frac_max=g1["near_tie_fraction_max"])
        report["gate_G1_self_agreement"] = g1_res
        if not g1_res["pass"]:
            report["failures"].append("gate G1 self-replay agreement")
        own = probe.row_store == store_id_of_agent
        r = probe.rows[own]
        am, mg = amax_chk[r], margin_chk[r]
        nxt, cur = probe.action_next_all[r], probe.action_cur_all[r]
        change = (cur != nxt) & (cur >= 0)
        tie = dict(tie_margin=g1["near_tie_logit_margin"], tie_frac_max=g1["near_tie_fraction_max"])
        step_all = _near_tie_rule(am == nxt, mg, min_agree=g3["alignment_agreement_min"], **tie)
        step_chg = _near_tie_rule(am[change] == nxt[change], mg[change],
                                  min_agree=g3["alignment_agreement_min"], **tie)
        has_prev = cur >= 0
        shift_all = float((am[has_prev] == cur[has_prev]).mean())
        shift_chg = float((am[change] == cur[change]).mean()) if change.any() else None
        report["alignment_controls"] = {
            "sampled_rows": int(r.size), "action_change_rows": int(change.sum()),
            "step_discontinuous_all": step_all, "step_discontinuous_change_rows": step_chg,
            "shift_by_one_all_rows_with_t_ge_1": shift_all,
            "shift_by_one_change_rows": shift_chg,
            "shift_bound_all (gate G3)": g3["shift_control_agreement_max"],
            "shift_bound_change_rows (tool_checks)": shift_change_rows_max}
        if not (step_all["pass"] and step_chg["pass"]):
            report["failures"].append("gate G3 step-discontinuous alignment")
        if shift_all >= g3["shift_control_agreement_max"]:
            report["alignment_controls"]["shift_status"] = "inconclusive"
            report["failures"].append("shift-by-one control inconclusive (>= gate G3 maximum)")
        elif shift_chg is not None and shift_chg >= shift_change_rows_max:
            report["alignment_controls"]["shift_status"] = "failed on change rows"
            report["failures"].append("shift-by-one control on action-change rows")
        else:
            report["alignment_controls"]["shift_status"] = "below both bounds"

    return report


def _chain_section(model, probe, acts_rows, keys, row_ep, row_t, report, *, assert_n_episodes,
                   g2_tol):
    """Chain assertions on `assert_n_episodes` whole episodes, plus sampled-vs-full capture."""
    import jax.numpy as jnp
    from flax import nnx
    E = probe.ep_T.size
    D = probe.obs_all.shape[1]
    n_a = int(assert_n_episodes)
    if n_a < 1 or n_a > E:
        raise ValueError(f"assert_n_episodes {n_a} outside 1..{E}")
    # spread over the probe's stores: take the first n_a // n_stores of each store
    stores = np.unique(probe.ep_store)
    per = max(1, n_a // stores.size)
    chk = np.concatenate([np.flatnonzero(probe.ep_store == s)[:per] for s in stores])[:n_a]
    Tc = int(probe.ep_T[chk].max())
    obs = np.zeros((Tc, chk.size, D), np.float32)
    for j, e in enumerate(chk):
        off, T = int(probe.ep_offset[e]), int(probe.ep_T[e])
        obs[:T, j] = probe.obs_all[off:off + T]
    obs_j = jnp.asarray(obs)
    full_acts, full_mod = nnx.jit(_scan_full)(model, obs_j, model.initial_state(chk.size))
    valid = np.arange(Tc)[:, None] < probe.ep_T[chk][None, :]
    # Steps past an episode's end run on zero inputs; they are still network evaluations,
    # so the chain must hold there too, and every step of the (Tc, n) block is checked.
    dev = chain_deviations(model, obs_j, full_acts, full_mod)
    report["chain_assertions"] = {
        "episodes": [int(probe.ep_seed[e]) for e in chk], "episode_store": probe.ep_store[chk].tolist(),
        "episode_steps": int(valid.sum()), "steps_checked_incl_padding": int(valid.size),
        "tolerance (gate G2)": g2_tol,
        "max_rel_deviation": dev,
        "pass": bool(all(v <= g2_tol for v in dev.values()))}
    if not report["chain_assertions"]["pass"]:
        bad = {k: v for k, v in dev.items() if v > g2_tol}
        report["failures"].append(f"chain assertions {bad}")
    # the kept rows of these episodes must equal the full capture (same tensors, two programs)
    rows_in = np.flatnonzero(np.isin(row_ep, chk))
    col = {int(e): j for j, e in enumerate(chk)}
    cap_dev = {}
    for k in keys:
        full = np.asarray(full_acts[k]).reshape(Tc, chk.size, -1)
        ref = full[row_t[rows_in], [col[int(e)] for e in row_ep[rows_in]]]
        got = acts_rows[k][rows_in]
        cap_dev[k] = float(np.max(np.abs(ref - got)) / max(1.0, float(np.max(np.abs(ref)))))
    report["sampled_vs_full_capture_max_rel_deviation"] = cap_dev
    if any(v > g2_tol for v in cap_dev.values()):
        report["failures"].append("sampled-row capture differs from the full capture")


def save_activations(path, acts_rows: dict, probe_sha: str):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez(tmp, __probe_row_index_sha256__=np.array(probe_sha), **acts_rows)
    os.replace(tmp, path)
    return path.stat().st_size


def load_activations(path, probe) -> dict:
    z = np.load(path)
    if str(z["__probe_row_index_sha256__"]) != probe.row_sha256:
        raise ValueError(f"{path}: activations were captured on another probe "
                         f"({z['__probe_row_index_sha256__']} vs {probe.row_sha256})")
    return {k: z[k] for k in z.files if not k.startswith("__")}
