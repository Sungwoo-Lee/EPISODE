"""Case study inside the 22-September level-05 seed-42 pair: Analyses 1-3 and the C1-C3 scoring.

Plain-language purpose: in one ordinary-vs-modulated pair the modulated agent hides in the bush
much more when injured. This tool looks inside both networks, layer by layer, and reads every
number against two comparison pairs (same seed, replicated; seed 43, where the ordinary agent
hides more). Plan: docs/experiments/active/modulator_clues/CASE_STUDY_L05_S42.md -- Revision 1
and 1b override the earlier sections.

  a12          Analyses 1 and 2 for every agent of the selected pairs, per checkpoint.
               Live mode of scripts/analysis/obs_manipulation/run.py with orientation
               `act_true`: the acting network gets the TRUE observations (natural unhurt route),
               a shadow copy gets the manipulated felt injury (`--memory sustained`). Both passes
               are captured layer by layer (`forward_with_activations`) plus the modulator's own
               GRU state. Felt-injury inputs: the constant 0.70 (stress probe) and the natural
               trace (felt injury of the same seed's injured no-animal episode at the same
               checkpoint), both primary. The original orientation (`act_manipulated`) is a
               labelled sensitivity row of Analysis 1.
                 A1 per layer: injury-shift size = mean |man - nat| / across-state spread of the
                    layer over the unhurt live steps (all steps of the 100-step scene, zero-variance
                    units dropped); numerator and denominator reported.
                 A2 per layer: per-checkpoint ridge logistic readout of "off the bush now, arrives
                    within 5 steps", unhurt episodes of both neutral scenes only, held-out-episode
                    AUC and log-loss; felt-injury decoder and its cosine with the readout; push of
                    the injury shift on the readout in units of its log-odds SD, plus the cosine;
                    sensitivity row: readout fitted on both injury levels with felt injury as a
                    covariate.
               Fatal checks: the acting (identity) episodes reproduce the dwell sweep's recorded
               episodes exactly in all four scenes; every condition follows the identity route;
               the chain assertions of scripts/analysis/nmn/teacher_forced.py hold on the
               captured tensors (G2 tolerance 1e-5).
  a3-prepare   Analysis 3, step 1, modulated agents of case / same-seed / seed-43: per checkpoint,
               per-unit gain and offset targets pooled over the injured and unhurt live passes of
               both neutral scenes; one weight-edited copy per freeze place (gain and offset
               together) in a SEPARATE directory; read-back check; the critic freeze (null
               control) must reproduce the live trajectories bit for bit in all four scenes.
               Writes dwell-sweep specs with the same probe battery and episodes (nodes empty).
  a3-collect   Step 2: live (outcome sweep) vs frozen (new sweep): injury effect, unhurt dwell,
               log-odds effect, survival steps; disruption guard; the critic sweep must equal the
               live sweep exactly.
  score        C1-C3 counts per pair and the reading rule.

Survival steps, never reward. Felt injury is nociception, never "pain".

    python scripts/analysis/case_l05_s42/case.py a12 --pairs all --roles both \
        --checkpoints every5 --device cpu --out results/analysis/case_l05_s42
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

#: study role -> pair key in scripts/analysis/modulator_engagement/runs.py
PAIR_KEYS = {"case": "orig_lvl05_s42", "same_seed": "l05_s42", "reverse": "l05_s43",
             "closest": "l05fix_s42"}           # closest: descriptive, outside the reading rule
UNHURT = ("avoid_none_inj00", "avoid_rabbitwander_inj00")
INJURED = ("avoid_none_inj70", "avoid_rabbitwander_inj70")
SCENE_TAG = {"avoid_none_inj00": "none", "avoid_rabbitwander_inj00": "rabbitwander",
             "avoid_none_inj70": "none", "avoid_rabbitwander_inj70": "rabbitwander"}
TRACE_SCENE = "avoid_none_inj70"
LAYERS = ("enc.uni.raw", "enc.uni.mod", "enc.uni.out", "enc.raw", "enc.mod", "enc.out",
          "rnn.state", "rnn.raw", "rnn.mod", "rnn.out", "actor.raw", "actor.mod", "actor.out",
          "critic.raw", "critic.mod", "critic.out", "mod.state")
CONST = 0.70
G2_TOL = 1e-5        # algorithmic_null_decision_rules.yaml gates.G2.reconstruction_rel_tol
PLACES = {"encoder": ("encoder_unimodal", "encoder_multimodal"), "memory": ("rnn",),
          "actor": ("actor",), "critic": ("critic",),
          "all": ("encoder_unimodal", "encoder_multimodal", "rnn", "actor", "critic")}
A3_ROLES = ("case", "same_seed", "reverse")
SCENES4 = INJURED + UNHURT


def _mods():
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, "scripts", "behavior_measures"))
    from scripts.analysis.modulator_engagement import engagement as E, runs as R
    om, MP = E._om()
    from avoidance_stats_heatmap import episode_measures
    return E, R, om, MP, episode_measures


def _sha():
    return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def _append_rows(path, rows):
    if not rows:
        return
    new = not os.path.exists(path)
    cols = list(rows[0])
    for r in rows[1:]:
        cols += [k for k in r if k not in cols]
    if not new:
        with open(path) as fh:
            head = next(csv.reader(fh))
        if head != cols:
            raise ValueError(f"{path}: columns changed; write to a fresh --out")
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        if new:
            w.writeheader()
        w.writerows(rows)


def _done_steps(path):
    if not os.path.exists(path):
        return set()
    with open(path) as fh:
        return {int(r["step"]) for r in csv.DictReader(fh)}


# ------------------------------------------------------------------ scenes / parity
def _scenes(E, R, pair):
    probe, n_ep, out_dir, labels = R.spec_scene(pair)
    worlds, seeds = {}, None
    for c in SCENES4:
        p, _, w, bm = E._world(probe, c)
        s = E._seeds(bm, n_ep, p)
        if seeds is not None and s != seeds:
            raise ValueError(f"{p}: eval seeds differ from the other scenes'")
        seeds, worlds[c] = s, w
    for c in UNHURT:
        if float(worlds[c].start_injury_low) != 0.0 or float(worlds[c].start_injury_high) != 0.0:
            raise ValueError(f"{c}: not an unhurt scene")
    settle = E.felt_settle_value(worlds[TRACE_SCENE])
    if abs(settle - CONST) > 1e-6:
        raise ValueError(f"{TRACE_SCENE}: settled felt injury {settle} != {CONST}")
    if len({int(w.max_steps) for w in worlds.values()}) != 1:
        raise ValueError("scenes differ in max_steps")
    return probe, out_dir, labels, worlds, seeds


def _parity(om, E, episode_measures, out_dir, label, scene, step, seeds, r):
    """Identity (acting) episodes vs the dwell sweep: exact per-episode comparison against the
    sweep's own recordings when they are on disk (positions at every step, bush dwell,
    survival); otherwise the per-checkpoint CSV mean. Fatal on any mismatch."""
    import numpy as np
    N = len(seeds)
    scratch = os.path.join(ROOT, out_dir, "_scratch", label, scene)
    if os.path.isdir(os.path.join(scratch, str(step))):
        om._parity(scratch, step, seeds, r["states0_np"], r["out"], r["T"], N, episode_measures)
        return "exact"
    b = float(np.mean([E._bush(episode_measures, r["states0_np"], r["out"], i, r["T"], om._snapshots)
                       for i in range(N)]))
    return "csv_mean_" + E._check_sweep(b, out_dir, label, scene, step, f"{label}/{scene}")


# ------------------------------------------------------------------ capture
def _layer_arrays(out, rows, modulated):
    """{layer: (nat (T, n, W), man (T, n, W))} for batch rows `rows`, float32."""
    import numpy as np
    res = {}
    for L in LAYERS:
        if L == "mod.state":
            if not modulated:
                continue
            nat, man = out["h_mod_shadow"], out["h_mod"]
        else:
            if L not in out["acts_nat"]:
                continue
            nat, man = out["acts_nat"][L], out["acts_man"][L]
        T = nat.shape[0]
        res[L] = (np.asarray(nat[:, rows]).reshape(T, len(rows), -1).astype(np.float32),
                  np.asarray(man[:, rows]).reshape(T, len(rows), -1).astype(np.float32))
    return res


def _chain(agent, out, rows, which):
    """teacher_forced chain assertions on the `which` pass ('nat' or 'man', sustained memory)
    for batch rows `rows`. Returns the max relative deviation per assertion."""
    import numpy as np
    import jax
    from scripts.analysis.nmn import teacher_forced as TF
    sel = lambda x: np.asarray(x)[:, rows]
    acts = {k: sel(v) for k, v in out[f"acts_{which}"].items()}
    mod = jax.tree_util.tree_map(sel, out[f"mod_{which}"]) if f"mod_{which}" in out else None
    return TF.chain_deviations(agent.model, sel(out[f"obs_{which}"]), acts, mod)


def capture_checkpoint(pair, role, step, agent=None, check_sweep=True):
    """Run every pass Analyses 1-2 need for one agent and checkpoint; return the arrays."""
    import numpy as np
    from scripts.analysis.nmn import replay
    from scripts.analysis.case_l05_s42 import measures as MS
    E, R, om, MP, episode_measures = _mods()
    probe, out_dir, labels, worlds, seeds = _scenes(E, R, pair)
    N = len(seeds)
    if agent is None:
        agent = replay.load_agent(os.path.join(pair.run_dirs[role], "models"), step)
    modulated = bool(agent.model.modulation_enabled)
    br = agent.obs_breakdown
    felt_idx = MP.sensor_offsets(br)[E.FELT][0]
    Tm = int(worlds[TRACE_SCENE].max_steps)
    ident = MP.from_spec({"manipulations": [{"name": "felt_injury", "sensor": E.FELT, "element": 0,
                                             "op": "add", "values": [0.0], "steps": [0, None]}]}, br, Tm)
    M3 = MP.from_spec({"manipulations": [{"name": "felt_injury", "sensor": E.FELT, "element": 0,
                                          "op": "set", "values": [CONST, 0.0], "steps": [0, None]}]}, br, Tm)
    cap = {"seeds": seeds, "modulated": modulated, "parity": {}, "chain": {}, "capture_dlogit": 0.0,
           "injured": {}, "unhurt": {}, "unhurt_old": {}}
    idr = np.arange(N)

    def base(r, rows):
        out, T = r["out"], r["T"]
        pos = MS.positions(r["states0_np"].agent_pos[rows], out["agent_pos"][:, rows], T[rows])
        onb = MS.on_bush(pos, r["states0_np"].obs_pos[rows, 0])
        mask, lab = MS.arrival_labels(onb, T[rows])
        return {"valid": r["valid"][:, rows], "T": T[rows], "mask": mask, "lab": lab,
                "felt": np.asarray(out["felt_true"][:, rows, 0], np.float64),
                "bush": float(np.mean([E._bush(episode_measures, r["states0_np"], out, b, T, om._snapshots)
                                       for b in rows]))}

    for sc in INJURED:
        r = om.run_checkpoint(agent, worlds[sc], seeds, ident, "sustained", orientation="act_true",
                              capture=True)
        cap["parity"][sc] = (_parity(om, E, episode_measures, out_dir, labels[role], sc, step, seeds, r)
                             if check_sweep else "skipped")
        cap["capture_dlogit"] = max(cap["capture_dlogit"], float(r["out"]["capture_dlogit"].max()))
        d = base(r, idr)
        d["layers"] = {L: v[0] for L, v in _layer_arrays(r["out"], idr, modulated).items()}
        cap["injured"][sc] = d
        del r

    tr = cap["injured"][TRACE_SCENE]
    trace = tr["felt"].copy()
    for i in range(N):                       # held at its last live value after the episode ended
        L_ = int(tr["valid"][:, i].sum())
        trace[L_:, i] = trace[L_ - 1, i]
    cap["trace_max"] = float(tr["felt"][tr["valid"]].max())
    override = np.full((Tm, 3 * N), np.nan, np.float32)
    override[:, 2 * N:] = trace.astype(np.float32)

    for sc in UNHURT:
        for orient in ("act_true", "act_manipulated"):
            r = om.run_checkpoint(agent, worlds[sc], seeds, M3, "sustained", orientation=orient,
                                  capture=True, override=override, override_index=felt_idx)
            out = r["out"]
            fg = out["felt_given"][:, 2 * N:, 0]
            if not np.array_equal(fg, trace.astype(np.float32)):
                raise AssertionError(f"{sc}: the trace condition's felt injury is not the recorded trace")
            if not (out["felt_given"][:, N:2 * N, 0] == np.float32(CONST)).all():
                raise AssertionError(f"{sc}: the constant condition's felt injury is not {CONST}")
            cap["capture_dlogit"] = max(cap["capture_dlogit"], float(out["capture_dlogit"].max()))
            if orient == "act_true":
                cap["parity"][sc] = (_parity(om, E, episode_measures, out_dir, labels[role], sc, step, seeds, r)
                                     if check_sweep else "skipped")
                if sc == UNHURT[0]:          # chain assertions: true pass and sustained shadow pass
                    allr = np.arange(3 * N)
                    cap["chain"] = {"nat": _chain(agent, out, allr, "nat"),
                                    "man": _chain(agent, out, allr, "man")}
                    worst = max(max(v.values()) for v in cap["chain"].values())
                    if worst > G2_TOL:
                        raise AssertionError(f"chain assertions failed (worst {worst} > {G2_TOL}): {cap['chain']}")
            rows = {"identity": idr, "const": np.arange(N, 2 * N), "trace": np.arange(2 * N, 3 * N)}
            arrs = {k: _layer_arrays(out, v, modulated) for k, v in rows.items()}
            d = {"ident": base(r, idr), "probes": {}}
            d["layers_ident"] = {L: v[0] for L, v in arrs["identity"].items()}
            for p in ("const", "trace"):
                d["probes"][p] = {"valid": r["valid"][:, rows[p]], "layers": arrs[p],
                                  "bush": base(r, rows[p])["bush"]}
                if orient == "act_true":        # the acting pass is the identity's, bit for bit
                    for L, (nat, _man) in arrs[p].items():
                        if not np.array_equal(nat, d["layers_ident"][L]):
                            raise AssertionError(f"{sc}/{p}/{L}: true-input pass differs from the identity episodes")
            (cap["unhurt"] if orient == "act_true" else cap["unhurt_old"])[sc] = d
            del r, out
    return cap


# ------------------------------------------------------------------ Analyses 1 and 2
def analyse(cap, head):
    """A1 and A2 rows from `capture_checkpoint` output. `head`: identifying columns."""
    import numpy as np
    from scripts.analysis.case_l05_s42 import measures as MS
    a1, a2 = [], []
    layers = [L for L in LAYERS if L in cap["unhurt"][UNHURT[0]]["layers_ident"]]
    sets = {"none": (UNHURT[0],), "rabbitwander": (UNHURT[1],), "both": UNHURT}
    for L in layers:
        W = cap["unhurt"][UNHURT[0]]["layers_ident"][L].shape[-1]
        for sname, scs in sets.items():
            ref = np.concatenate([cap["unhurt"][s]["layers_ident"][L][cap["unhurt"][s]["ident"]["valid"]] for s in scs])
            keep, _mu, _sd, den = MS.spread(ref)
            for orient, src in (("act_true", cap["unhurt"]), ("act_manipulated", cap["unhurt_old"])):
                for p in ("const", "trace"):
                    man = np.concatenate([src[s]["probes"][p]["layers"][L][1][src[s]["probes"][p]["valid"]] for s in scs])
                    nat = np.concatenate([src[s]["probes"][p]["layers"][L][0][src[s]["probes"][p]["valid"]] for s in scs])
                    num, size, dead = MS.shift_size(man, nat, keep, den)
                    a1.append({**head, "layer": L, "scenes": sname, "orientation": orient, "probe": p,
                               "row": "primary" if orient == "act_true" else "sensitivity (acting = manipulated)",
                               "probe_label": "stress probe 0.70" if p == "const" else "natural trace",
                               "numerator": num, "denominator": den, "size": size,
                               "units": W, "units_kept": int(keep.sum()), "steps": int(len(man)),
                               "numerator_dropped_units": dead})

        # ---- A2 (orientation act_true, both scenes pooled)
        U = cap["unhurt"]
        ref = np.concatenate([U[s]["layers_ident"][L][U[s]["ident"]["valid"]] for s in UNHURT])
        keep, mu, _sd, den = MS.spread(ref)
        gscale = den / np.sqrt(keep.sum()) if keep.any() else 1.0   # one scalar per layer (measures.py)
        z = lambda X: (X[:, keep] - mu[keep]) / gscale
        Zu = z(ref)
        Zr, yr, gr = [], [], []
        for i, s in enumerate(UNHURT):
            m = U[s]["ident"]["mask"]
            Zr.append(z(U[s]["layers_ident"][L][m])); yr.append(U[s]["ident"]["lab"][m])
            gr.append(i * 1000 + np.broadcast_to(np.arange(m.shape[1])[None], m.shape)[m])
        Zr, yr, gr = np.concatenate(Zr), np.concatenate(yr), np.concatenate(gr)
        ro = MS.fit_readout(Zr, yr, gr)
        # felt-injury decoder: natural passes of all four scenes
        Zd, fd, gd, Zs, ys, fs, gs = [], [], [], [], [], [], []
        for i, s in enumerate(SCENES4):
            src = cap["injured"][s] if s in INJURED else {**U[s]["ident"], "layers": U[s]["layers_ident"]}
            X, v = src["layers"][L], src["valid"]
            Zd.append(z(X[v])); fd.append(src["felt"][v])
            gd.append(i * 1000 + np.broadcast_to(np.arange(v.shape[1])[None], v.shape)[v])
            m = src["mask"]
            Zs.append(z(X[m])); ys.append(src["lab"][m]); fs.append(src["felt"][m])
            gs.append(i * 1000 + np.broadcast_to(np.arange(m.shape[1])[None], m.shape)[m])
        Zd, fd, gd = np.concatenate(Zd), np.concatenate(fd), np.concatenate(gd)
        wf, r2, alpha = MS.fit_decoder(Zd, fd, gd)
        fsd = float(fd.std()) or 1.0
        Zs = np.concatenate([np.concatenate(Zs), (np.concatenate(fs) / fsd)[:, None]], 1)
        ro_s = MS.fit_readout(Zs, np.concatenate(ys), np.concatenate(gs))
        for p in ("const", "trace"):
            Dz = np.concatenate([(U[s]["probes"][p]["layers"][L][1] - U[s]["probes"][p]["layers"][L][0])
                                 [U[s]["probes"][p]["valid"]][:, keep] / gscale for s in UNHURT])
            row = {**head, "layer": L, "probe": p,
                   "probe_label": "stress probe 0.70" if p == "const" else "natural trace",
                   "units": int(ref.shape[1]), "units_kept": int(keep.sum()),
                   "readout_fitted": ro["fitted"], "readout_rows": ro["n_rows"], "readout_pos": ro["n_pos"],
                   "readout_C": ro["C"], "auc_heldout": ro["auc_heldout"],
                   "logloss_heldout": ro["logloss_heldout"], "logloss_base": ro["logloss_base"],
                   "felt_decoder_r2_heldout": r2, "felt_decoder_alpha": alpha,
                   "cos_readout_felt_decoder": MS.cosine(ro["w"], wf) if ro["fitted"] else np.nan}
            if ro["fitted"]:
                row.update(MS.push(ro["w"], ro["b"], Zu, Dz))
            else:
                row.update(push_logodds=np.nan, logit_sd=np.nan, push_sd=np.nan, cos_shift_readout=np.nan)
            row.update(sens_readout_fitted=ro_s["fitted"], sens_auc_heldout=ro_s["auc_heldout"],
                       sens_logloss_heldout=ro_s["logloss_heldout"])
            if ro_s["fitted"]:
                ps = MS.push(ro_s["w"][:-1], ro_s["b"], Zu, Dz)
                row.update(sens_push_sd=ps["push_sd"], sens_cos_shift_readout=ps["cos_shift_readout"],
                           sens_felt_coef=float(ro_s["w"][-1]))
            else:
                row.update(sens_push_sd=np.nan, sens_cos_shift_readout=np.nan, sens_felt_coef=np.nan)
            a2.append(row)
    return a1, a2


def a12_checkpoint(pair, role, step, grid_index, agent=None, check_sweep=True):
    """(a1 rows, a2 rows, check report) for one agent and checkpoint."""
    import numpy as np
    t0 = time.time()
    cap = capture_checkpoint(pair, role, step, agent=agent, check_sweep=check_sweep)
    t1 = time.time()
    head = {"pair": pair.key, "role": role, "run": getattr(pair, role), "grid_index": grid_index,
            "step": int(step)}
    a1, a2 = analyse(cap, head)
    rep = {**head, "parity": cap["parity"], "trace_max": cap["trace_max"],
           "capture_dlogit_max": cap["capture_dlogit"],
           "chain_max_rel_dev": {w: max(v.values()) for w, v in cap["chain"].items()},
           "bush_identity": {s: cap["unhurt"][s]["ident"]["bush"] for s in UNHURT}
                            | {s: cap["injured"][s]["bush"] for s in INJURED},
           "bush_shadow_route_old_orientation": {f"{s}/{p}": cap["unhurt_old"][s]["probes"][p]["bush"]
                                                 for s in UNHURT for p in ("const", "trace")},
           "seconds_capture": round(t1 - t0, 1), "seconds_analysis": round(time.time() - t1, 1)}
    return a1, a2, rep


# ------------------------------------------------------------------ Analysis 3
def _same_traj(a, b):
    import numpy as np
    return (np.array_equal(a["T"], b["T"]) and np.array_equal(a["out"]["action"], b["out"]["action"])
            and np.array_equal(a["out"]["agent_pos"], b["out"]["agent_pos"]))


def a3_prepare_checkpoint(pair, step, ck_root):
    import numpy as np
    import jax
    from flax import nnx
    from scripts.analysis.nmn import replay, freeze
    E, R, om, MP, episode_measures = _mods()
    probe, out_dir, labels, worlds, seeds = _scenes(E, R, pair)
    N = len(seeds)
    models = os.path.join(pair.run_dirs["modulated"], "models")
    agent = replay.load_agent(models, step)
    means, live = E._pooled_means(agent, worlds, seeds, om, MP)     # all four scenes pooled
    row = {"pair": pair.key, "run": pair.modulated, "step": int(step)}
    for c, r in live.items():
        row[f"live_bush_{c}"] = float(np.mean([E._bush(episode_measures, r["states0_np"], r["out"], i, r["T"],
                                                       om._snapshots) for i in range(N)]))
        row[f"parity_{c}"] = _parity(om, E, episode_measures, out_dir, labels["modulated"], c, step, seeds, r)
    for place, sites in PLACES.items():
        fa = replay.load_agent(models, step)
        edited = freeze.apply_freeze(fa.model, {s: means[s] for s in sites}, freeze_gain=True, freeze_offset=True)
        dst = os.path.join(ck_root, f"{pair.modulated}__freeze_{place}", "models")
        E._save_edited(fa.model, models, dst, step)
        back = replay.load_agent(dst, step)
        a = jax.tree_util.tree_leaves(nnx.state(fa.model))
        b = jax.tree_util.tree_leaves(nnx.state(back.model))
        if len(a) != len(b) or any(not np.array_equal(np.asarray(x), np.asarray(y)) for x, y in zip(a, b)):
            raise AssertionError(f"{dst}/{step}: saved parameters differ from the edited model")
        _, rr = E._pooled_means(back, worlds if place == "critic" else {INJURED[0]: worlds[INJURED[0]]},
                                seeds, om, MP)
        for c, r in rr.items():              # frozen signals constant at the target, every live step
            o, v = r["out"], r["valid"][:, :N]
            for s in sites:
                for p, key in (("ugain", "gamma"), ("uoffset", "beta")):
                    x = o[f"{p}_{s}"][:, :N][v]
                    if float(np.abs(x - means[s][key][None, :]).max()) != 0.0:
                        raise AssertionError(f"{dst}/{step}: frozen {key} at {s} not constant at target ({c})")
        if place == "critic":                # null control: greedy actions cannot change
            for c in SCENES4:
                if not _same_traj(rr[c], live[c]):
                    raise AssertionError(f"{pair.key} step {step}: CRITIC FREEZE CHANGED THE TRAJECTORIES "
                                         f"in {c} -- the freeze pipeline is wrong; analysis stops")
            row["critic_null_control"] = "bit-identical (4 scenes)"
        row[f"{place}_edited"] = len(edited)
        row[f"{place}_dir"] = os.path.relpath(os.path.dirname(dst), ROOT)
    np.savez_compressed(os.path.join(ck_root, f"targets_{pair.key}_{step}.npz"),
                        **{f"{s}/{k}": v for s, d in means.items() for k, v in d.items()})
    return row


def _a3_spec_name(pair):
    return "case_l05_s42_a3_" + os.path.splitext(os.path.basename(pair.spec))[0].replace("_rppo", "")


def a3_write_specs(pairs, ck_root, sweep_out_root, spec_dir):
    import yaml
    E, R, *_ = _mods()
    by_spec = {}
    for p in pairs:
        by_spec.setdefault(p.spec, []).append(p)
    os.makedirs(spec_dir, exist_ok=True)
    written = []
    for spec, ps in by_spec.items():
        src = R.load_spec(spec)
        name = _a3_spec_name(ps[0])
        runs = [{"label": f"{R.spec_scene(p)[3]['modulated']}__freeze_{place}",
                 "path": os.path.relpath(os.path.join(ck_root, f"{p.modulated}__freeze_{place}"), ROOT)}
                for p in ps for place in PLACES]
        out = {"name": name, "algo": "rppo", "output_dir": os.path.relpath(os.path.join(sweep_out_root, name), ROOT),
               "probe": src["probe"], "conditions": list(SCENES4), "episodes": int(src["episodes"]),
               "nodes": [], "x_axis": src.get("x_axis", "steps"),
               "plot_measures": ["bush_hiding", "survival_steps"], "runs": runs}
        f = os.path.join(spec_dir, f"{name}_rppo.yaml")
        with open(f, "w") as fh:
            fh.write(f"# Case study L05 S42, Analysis 3 (generated by {os.path.relpath(__file__, ROOT)}).\n"
                     f"# Same probe battery and episodes as {spec}; weight-edited checkpoints only.\n"
                     f"# `nodes` is empty on purpose: fill it after checking gpu_status + the diary.\n")
            yaml.safe_dump(out, fh, sort_keys=False)
        written.append(f)
    return written


def a3_collect(pairs, spec_dir, roles):
    """Per agent x place x checkpoint x scene rows, and per agent x place summaries with the
    guard. 'Lowered' at a checkpoint = live injury effect > frozen injury effect, on the mean of
    the two neutral scenes (also reported per scene)."""
    import numpy as np
    import yaml
    from scripts.analysis.case_l05_s42 import measures as MS
    E, R, *_ = _mods()
    rows, summ = [], []
    for p, role in zip(pairs, roles):
        _pr, _ep, out_dir, labels = R.spec_scene(p)
        sp = yaml.safe_load(open(os.path.join(spec_dir, f"{_a3_spec_name(p)}_rppo.yaml")))
        lab = labels["modulated"]
        enc_path = {r["label"]: r["path"] for r in sp["runs"]}[f"{lab}__freeze_encoder"]
        if os.path.basename(enc_path) != f"{p.modulated}__freeze_encoder":
            raise ValueError(f"{p.key}: spec run {enc_path} is not this agent's edited copy")
        steps = sorted(int(x) for x in os.listdir(os.path.join(ROOT, enc_path, "models")) if x.isdigit())
        grid = {s: g for g, s in E.select_checkpoints(os.path.join(p.run_dirs["modulated"], "models"), "every5").items()}

        def val(od, lb, sc, st, col):
            v = E._sweep_value(od, lb, sc, st, col)
            if v is None:
                raise ValueError(f"no sweep value: {od}/{lb}/{sc} step {st} {col}")
            return v

        live = {st: {sc: {c: val(out_dir, lab, sc, st, c) for c in ("bush_hiding", "survival_steps")}
                     for sc in SCENES4} for st in steps}
        for place in PLACES:
            fl = f"{lab}__freeze_{place}"
            per_ck = []
            for st in steps:
                fz = {sc: {c: val(sp["output_dir"], fl, sc, st, c) for c in ("bush_hiding", "survival_steps")}
                      for sc in SCENES4}
                if place == "critic":         # null control at the sweep level, every column
                    import pandas as pd
                    for sc in SCENES4:
                        a = pd.read_csv(os.path.join(ROOT, out_dir, lab, f"{sc}.csv"))
                        b = pd.read_csv(os.path.join(ROOT, sp["output_dir"], fl, f"{sc}.csv"))
                        a, b = a[a.step == st].reset_index(drop=True), b[b.step == st].reset_index(drop=True)
                        if not a.drop(columns=["step_M"], errors="ignore").equals(b.drop(columns=["step_M"], errors="ignore")):
                            raise AssertionError(f"{p.key} step {st} {sc}: critic-frozen sweep differs from live")
                r = {"pair": p.key, "role": role, "place": place, "grid_index": grid.get(st), "step": st}
                for tag, I, U in (("none",) + tuple(s for s in SCENES4 if SCENE_TAG[s] == "none"),
                                  ("rabbitwander",) + tuple(s for s in SCENES4 if SCENE_TAG[s] == "rabbitwander")):
                    for cond, src in (("live", live[st]), ("frozen", fz)):
                        b70, b00 = src[I]["bush_hiding"], src[U]["bush_hiding"]
                        r[f"{cond}_effect_{tag}"] = 100.0 * (b70 - b00)
                        r[f"{cond}_unhurt_{tag}"] = 100.0 * b00
                        r[f"{cond}_effect_logodds_{tag}"] = float(MS.logit(b70) - MS.logit(b00))
                        r[f"{cond}_survival_inj70_{tag}"] = src[I]["survival_steps"]
                        r[f"{cond}_survival_inj00_{tag}"] = src[U]["survival_steps"]
                for cond in ("live", "frozen"):
                    for k in ("effect", "unhurt", "effect_logodds"):
                        r[f"{cond}_{k}_mean2"] = 0.5 * (r[f"{cond}_{k}_none"] + r[f"{cond}_{k}_rabbitwander"])
                per_ck.append(r)
            rows += per_ck
            for tag in ("none", "rabbitwander", "mean2"):
                le = np.array([r[f"live_effect_{tag}"] for r in per_ck])
                fe = np.array([r[f"frozen_effect_{tag}"] for r in per_ck])
                du = np.array([abs(r[f"frozen_unhurt_{tag}"] - r[f"live_unhurt_{tag}"]) for r in per_ck])
                lo_lo = np.array([r[f"live_effect_logodds_{tag}"] - r[f"frozen_effect_logodds_{tag}"] for r in per_ck])
                n_low, n_rev, n = MS.count_expected(le - fe)
                guard = bool(du.mean() < 0.5 * le.mean())
                summ.append({"pair": p.key, "role": role, "place": place, "scenes": tag, "checkpoints": n,
                             "lowered": n_low, "raised": n_rev, "lowered_logodds": int(np.sum(lo_lo > 0)),
                             "live_effect_mean": float(le.mean()), "frozen_effect_mean": float(fe.mean()),
                             "abs_unhurt_change_mean": float(du.mean()), "guard_threshold": float(0.5 * le.mean()),
                             "guard_passed": guard,
                             "reading": "guard passed" if guard else "undetermined (disruption)"})
    return rows, summ


# ------------------------------------------------------------------ scoring
def score(out_root):
    """C1 (A1 memory-state size, natural trace), C2 (A2 memory-output push, natural trace), C3
    (A3 encoder freeze). Counts of checkpoints with the expected sign, per pair; the reading rule."""
    import numpy as np
    import pandas as pd
    from scripts.analysis.case_l05_s42 import measures as MS
    res = []

    def pair_diff(df, col, key):
        mod = df[df.role == "modulated"].set_index("grid_index")[col]
        ordi = df[df.role == "ordinary"].set_index("grid_index")[col]
        g = sorted(set(mod.index) & set(ordi.index))
        return g, (mod.loc[g] - ordi.loc[g]).to_numpy()

    a1 = pd.concat([pd.read_csv(f) for f in _glob(out_root, "a1")])
    a2 = pd.concat([pd.read_csv(f) for f in _glob(out_root, "a2")])
    sel1 = a1[(a1.layer == "rnn.state") & (a1.probe == "trace") & (a1.orientation == "act_true") & (a1.scenes == "both")]
    sel2 = a2[(a2.layer == "rnn.out") & (a2.probe == "trace")]
    for cell, df, col, what in (("C1", sel1, "size", "memory-state injury-shift size, natural trace (modulated - ordinary)"),
                                ("C2", sel2, "push_sd", "memory-output push toward the bush, natural trace (modulated - ordinary)")):
        for role, key in PAIR_KEYS.items():
            d = df[df.pair == key]
            if d.empty:
                continue
            g, diff = pair_diff(d, col, key)
            n_exp, n_rev, n = MS.count_expected(diff)
            res.append({"cell": cell, "what": what, "pair_role": role, "pair": key, "checkpoints": n,
                        "expected_sign": n_exp, "reversed": n_rev,
                        "condition": (MS.condition_met(role, n_exp) if role in MS.RULE else "descriptive"),
                        "values": json.dumps([round(float(x), 6) for x in diff])})
    s3 = os.path.join(out_root, "a3", "a3_summary.csv")
    if os.path.exists(s3):
        a3 = pd.read_csv(s3)
        for _, r in a3[(a3.place == "encoder") & (a3.scenes == "mean2")].iterrows():
            role = r["role"]
            ok = MS.condition_met(role, int(r["lowered"]))
            if role in ("case", "same_seed"):
                ok = ok and bool(r["guard_passed"])
            res.append({"cell": "C3", "what": "encoder freeze lowers the injury effect (live - frozen, mean of 2 scenes)",
                        "pair_role": role, "pair": r["pair"], "checkpoints": int(r["checkpoints"]),
                        "expected_sign": int(r["lowered"]), "reversed": int(r["raised"]),
                        "condition": ok, "guard": r["reading"], "values": ""})
    out = pd.DataFrame(res)
    verdicts = []
    for cell in ("C1", "C2", "C3"):
        d = out[(out.cell == cell) & out.pair_role.isin(list(MS.RULE))]
        if len(d) == 3:
            verdicts.append({"cell": cell, "all_three_conditions": bool(d.condition.astype(bool).all()),
                             **{f"cond_{r.pair_role}": bool(r.condition) for r in d.itertuples()}})
    os.makedirs(os.path.join(out_root, "scores"), exist_ok=True)
    out.to_csv(os.path.join(out_root, "scores", "c_cells.csv"), index=False)
    json.dump(verdicts, open(os.path.join(out_root, "scores", "reading_rule.json"), "w"), indent=1)
    return out, verdicts


def _glob(out_root, sub):
    import glob
    return sorted(glob.glob(os.path.join(out_root, sub, "*.csv")))


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("measure", choices=["a12", "a3-prepare", "a3-collect", "score"])
    ap.add_argument("--pairs", default=None,
                    help="comma-separated study roles (case,same_seed,reverse,closest) or 'all'")
    ap.add_argument("--roles", choices=["ordinary", "modulated", "both"], help="a12 only")
    ap.add_argument("--checkpoints", help="every5 | steps:a,b (a12, a3-prepare)")
    ap.add_argument("--device", choices=["cpu", "gpu"])
    ap.add_argument("--out", required=True, help="output root (results/analysis/case_l05_s42)")
    a = ap.parse_args(argv)
    sys.path.insert(0, ROOT)
    if a.measure == "score":
        out, v = score(a.out)
        print(out.drop(columns=["values"]).to_string(index=False))
        print(json.dumps(v, indent=1))
        return
    need = {"a12": ("pairs", "roles", "checkpoints", "device"), "a3-prepare": ("pairs", "checkpoints", "device"),
            "a3-collect": ("pairs",)}[a.measure]
    miss = [k for k in need if getattr(a, k) is None]
    if miss:
        ap.error(f"{a.measure} requires " + ", ".join("--" + k for k in miss))
    if a.device:      # before numpy/jax load: pins JAX and BLAS (sklearn) to one thread on cpu
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "om_run_dev", os.path.join(ROOT, "scripts", "analysis", "obs_manipulation", "run.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m._set_device(a.device)
    E, R, om, MP, _ = _mods()
    study_roles = list(PAIR_KEYS) if a.pairs == "all" else a.pairs.split(",")
    if a.measure.startswith("a3"):
        study_roles = [r for r in study_roles if r in A3_ROLES]
    bad = [r for r in study_roles if r not in PAIR_KEYS]
    if bad:
        raise ValueError(f"unknown study role(s) {bad}; valid: {list(PAIR_KEYS)}")
    pairs = [R.select(PAIR_KEYS[r])[0] for r in study_roles]
    R.validate(pairs)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    if a.measure == "a3-collect":
        d = os.path.join(a.out, "a3")
        rows, summ = a3_collect(pairs, os.path.join(d, "sweeps"), study_roles)
        for name, rr in (("a3_effects.csv", rows), ("a3_summary.csv", summ)):
            if os.path.exists(os.path.join(d, name)):
                os.remove(os.path.join(d, name))
            _append_rows(os.path.join(d, name), rr)
        print(f"wrote {len(rows)} + {len(summ)} rows to {d}")
        return

    for sr, p in zip(study_roles, pairs):
        agents = (["ordinary", "modulated"] if a.roles == "both" else [a.roles]) if a.measure == "a12" else ["modulated"]
        for role in agents:
            models = os.path.join(p.run_dirs[role], "models")
            ck = E.select_checkpoints(models, a.checkpoints)
            if a.measure == "a12":
                f1, f2 = (os.path.join(a.out, x, f"{sr}_{role}.csv") for x in ("a1", "a2"))
                fr = os.path.join(a.out, "checks", f"{sr}_{role}.jsonl")
                for x in (f1, f2, fr):
                    os.makedirs(os.path.dirname(x), exist_ok=True)
                done = _done_steps(f2)
            else:
                d = os.path.join(a.out, "a3")
                os.makedirs(os.path.join(d, "ckpts", "JAX_RecurrentPPO"), exist_ok=True)
                f3 = os.path.join(d, f"prepare_{sr}.csv")
                done = _done_steps(f3)
            todo = [(g, s) for g, s in sorted(ck.items()) if s not in done]
            print(f"[{a.measure}] {sr} {role}: {len(ck)} checkpoints, {len(todo)} to do", flush=True)
            for g, s in todo:
                t1 = time.time()
                if a.measure == "a12":
                    r1, r2, rep = a12_checkpoint(p, role, s, g)
                    _append_rows(f1, r1)
                    _append_rows(f2, r2)
                    with open(fr, "a") as fh:
                        fh.write(json.dumps(rep) + "\n")
                else:
                    row = a3_prepare_checkpoint(p, s, os.path.join(d, "ckpts", "JAX_RecurrentPPO"))
                    _append_rows(f3, [{"study_role": sr, "grid_index": g, **row,
                                       "seconds": round(time.time() - t1, 1)}])
                print(f"  {sr} {role} step {s} (grid {g}): {time.time() - t1:.0f}s", flush=True)
    if a.measure == "a3-prepare":
        print("specs:", a3_write_specs(pairs, os.path.join(a.out, "a3", "ckpts", "JAX_RecurrentPPO"),
                                       os.path.join(ROOT, "results", "eval", "avoidance", "metrics_history_rppo_case_l05_s42"),
                                       os.path.join(a.out, "a3", "sweeps")))
    json.dump({"measure": a.measure, "pairs": {r: PAIR_KEYS[r] for r in study_roles}, "checkpoints": a.checkpoints,
               "device": a.device, "layers": list(LAYERS), "const": CONST, "trace_scene": TRACE_SCENE,
               "places": PLACES, "g2_tol": G2_TOL, "git_sha": _sha(),
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(a.out, f"manifest_{a.measure}_{'_'.join(study_roles)}.json"), "w"), indent=1)
    print(f"[{a.measure}] done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
