"""THIRST_TASK design checks 1-4 and 6 on the nine thirst worlds, through the trainer's own loader.

  1. load (load_env_config -> load_env_params), observation width, breakdown <-> noise sync, a real
     get_observation on a real reset;
  2. placement on N real resets: (0,0)-fallback signature, overlaps, every slot in its own area,
     pond never under anything, agent never on the pond, fire separation, pond-smell weight;
  3. smell direction: on the same real reset layouts, the channel-0 field from the REAL kernel
     (sensor._sense_olfaction_at) at every cell; for every non-source cell as a hypothetical agent
     position, does the strongest in-bounds neighbour reduce the Manhattan distance to the nearest
     channel-0 source (active food or a pond cell)? Binned by that distance; chance level reported;
     plus how often any channel-0 smell is in range at all (any of the five sampled cells > 0);
  4. walk lengths: Manhattan distance from the real start cell to the nearest pond cell;
  6. one sample layout per world (PNG).

Run: JAX on CPU, project interpreter, from the worktree.
"""
import os
import sys
import json
import logging

os.environ["JAX_PLATFORMS"] = "cpu"
logging.disable(logging.WARNING)
W = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst"
sys.path.insert(0, W)
os.chdir(W)
import numpy as np
import jax
import jax.numpy as jnp
from src.environment.config_loader import load_env_config, load_env_params
from src.environment.core import jax_reset, heat_source_mask
from src.environment.sensor import get_observation, get_observation_breakdown, _sense_olfaction_at

OUT = os.path.join(W, "tmp/20261001_thirst_task")
N = int(os.environ.get("N_RESETS", "2000"))
N_SMELL = int(os.environ.get("N_SMELL", "2000"))
WORLDS = [
    ("g10sW", "configs/environment/experiment/basic/06-pond_thirst_10x10.yaml"),
    ("g10s5", "configs/environment/experiment/thirst/pond_thirst_10x10_smell5.yaml"),
    ("g10s3", "configs/environment/experiment/thirst/pond_thirst_10x10_smell3.yaml"),
    ("g15sW", "configs/environment/experiment/thirst/pond_thirst_15x15.yaml"),
    ("g15s5", "configs/environment/experiment/thirst/pond_thirst_15x15_smell5.yaml"),
    ("g15s3", "configs/environment/experiment/thirst/pond_thirst_15x15_smell3.yaml"),
    ("g20sW", "configs/environment/experiment/thirst/pond_thirst_20x20.yaml"),
    ("g20s5", "configs/environment/experiment/thirst/pond_thirst_20x20_smell5.yaml"),
    ("g20s3", "configs/environment/experiment/thirst/pond_thirst_20x20_smell3.yaml"),
]
if len(sys.argv) > 1:
    WORLDS = [w for w in WORLDS if w[0] in sys.argv[1:]]
DIST_BINS = [2, 5, 10, 15]


def in_area(pos, area):
    """pos [E, S, 2]; area [S, 4] = (min_r, min_c, max_r, max_c), max exclusive."""
    return ((pos[..., 0] >= area[None, :, 0]) & (pos[..., 0] < area[None, :, 2])
            & (pos[..., 1] >= area[None, :, 1]) & (pos[..., 1] < area[None, :, 3]))


def check_load(name, rel):
    cfg = load_env_config(rel)
    p = load_env_params(cfg)
    bd = get_observation_breakdown(p)
    width = int(sum(bd.values()))
    s0 = jax_reset(p, jax.random.PRNGKey(0))
    obs = np.asarray(get_observation(s0, p))
    order = tuple(p.noise_modality_order)
    missing = [k for k in bd if k not in order]
    # The order the noise array is indexed in must follow the breakdown's emission order.
    pos = [order.index(k) for k in bd if k in order]
    return p, {
        "grid": f"{p.height}x{p.width}",
        "sensor_radius": float(p.sensor_radius),
        "decay_power": float(p.sensor_decay),
        "pond_size": [int(p.water_block_h), int(p.water_block_w)],
        "pond_table_0based": [list(map(int, t)) for t in p.water_topleft_table],
        "pond_cell_property": [round(float(v), 6) for v in p.water_cell_property],
        "pond_total_smell": [round(float(v) * p.water_block_h * p.water_block_w, 6)
                             for v in p.water_cell_property],
        "obs_breakdown": bd,
        "obs_width_breakdown": width,
        "obs_width_real": int(obs.shape[-1]),
        "noise_enabled": bool(p.perceptual_noise_enabled),
        "noise_missing_for_breakdown": missing,
        "noise_order_same_as_breakdown_INFO_ONLY_lookup_is_by_name": pos == sorted(pos),
        "max_steps": int(p.max_steps),
    }


def check_placement(p, S):
    ag = np.asarray(S.agent_pos)
    rp, ra = np.asarray(S.res_pos), np.asarray(S.res_active)
    op, oa = np.asarray(S.obs_pos), np.asarray(S.obs_active)
    an, aa = np.asarray(S.animal_pos), np.asarray(S.animal_active)
    wp = np.asarray(S.water_pos)                                   # [E, h*w, 2]
    is_fire = np.asarray(heat_source_mask(p.obs_temperature, p.obs_temp_ratio_low, p.obs_temp_ratio_high))
    in_r = in_area(rp, np.asarray(p.res_spawn_area))
    in_o = in_area(op, np.asarray(p.obs_spawn_area))
    in_a = in_area(an, np.asarray(p.animal_spawn_area))
    allpos = np.concatenate([rp, op, an], 1)
    allact = np.concatenate([ra, oa, aa], 1)
    allin = np.concatenate([in_r, in_o, in_a], 1)
    E = ag.shape[0]
    flat = allpos[..., 0] * p.width + allpos[..., 1]
    dup_act = 0
    fire_sep_viol = 0
    # Inactive slots are parked OFF the grid at (H, W) by jax_reset; every check below is on
    # ACTIVE slots. The (0,0) fallback is invisible to an area test when the area is the whole
    # map ((0,0) is a legal cell there), so compare (0,0) occupancy with its uniform expectation.
    at00 = ((allpos == 0).all(-1) & allact).sum(-1)                      # active slots at (0,0)
    allin_fire = np.concatenate([np.zeros_like(in_r), is_fire[None].repeat(E, 0),
                                 np.zeros_like(in_a)], 1)
    expected00 = ((allact & ~allin_fire).sum(-1) / (p.height * p.width)).mean()
    # Control: the other three corners are symmetric to (0,0) in every rule except the fallback.
    Hm, Wm = int(p.height) - 1, int(p.width) - 1
    corners = [((allpos == np.array(c)).all(-1) & allact).sum(-1).mean()
               for c in [(0, Wm), (Hm, 0), (Hm, Wm)]]
    parked_ok = (allact | (allpos == np.array([p.height, p.width])).all(-1)).all()
    for e in range(E):
        a = flat[e][allact[e]]
        dup_act += len(set(a)) != len(a)
        f = op[e][oa[e] & is_fire]
        if len(f) > 1:
            d = np.abs(f[:, None, :] - f[None, :, :]).sum(-1) + np.eye(len(f), dtype=int) * 99
            fire_sep_viol += int((d < int(p.thermal_min_fire_separation)).any())
    on_pond_any = (allpos[:, :, None, :] == wp[:, None, :, :]).all(-1).any(-1)   # [E, S]
    agent_on_pond = (wp == ag[:, None, :]).all(-1).any(-1)
    # also check the animals' patrol box covers the map (config-level property)
    patrol = np.asarray(p.animal_patrol)
    return {
        "resets": E,
        "fallback_signature_active_outside_own_area": float(((~allin) & allact).any(-1).mean()),
        "active_slots_at_0_0_per_reset": float(at00.mean()),
        "active_slots_at_0_0_expected_if_uniform": float(expected00),
        "active_slots_at_other_corners_mean": float(np.mean(corners)),
        "resets_with_2plus_active_at_0_0": float((at00 > 1).mean()),
        "inactive_slots_all_parked_off_grid": bool(parked_ok),
        "overlap_two_active_share_a_cell": dup_act / E,
        "any_active_on_pond": float((on_pond_any & allact).any(-1).mean()),
        "agent_starts_on_pond": float(agent_on_pond.mean()),
        "agent_starts_on_burning_fire": float(((op == ag[:, None, :]).all(-1) & oa & is_fire[None]).any(-1).mean()),
        "active_fire_pairs_closer_than_separation": fire_sep_viol / E,
        "active_counts_mean": {
            "food": float((ra & (np.asarray(p.res_type)[None] == 0)).sum(-1).mean()),
            "ambushers": float((ra & (np.asarray(p.res_type)[None] == 1)).sum(-1).mean()),
            "fires": float((oa & is_fire[None]).sum(-1).mean()),
            "animals": float(aa.sum(-1).mean()),
        },
        "slots_total": int(allpos.shape[1]),
        "spawn_areas_distinct": sorted({tuple(map(int, a)) for a in
                                        np.concatenate([np.asarray(p.res_spawn_area), np.asarray(p.obs_spawn_area),
                                                        np.asarray(p.animal_spawn_area)], 0)}),
        "patrol_areas_distinct": sorted({tuple(map(int, a)) for a in patrol}),
        "pond_topleft_freq": {str(k): float(v) for k, v in zip(*np.unique(
            [tuple(x) for x in wp[:, 0, :]], axis=0, return_counts=True))} if False else
            {f"{r},{c}": float(((wp[:, 0, 0] == r) & (wp[:, 0, 1] == c)).mean())
             for r, c in p.water_topleft_table},
    }


def smell_fields(p, S):
    """Channel-0 field at every cell of every reset, from the real kernel. [E, H, W]."""
    H, Wd = int(p.height), int(p.width)
    cells = jnp.stack(jnp.meshgrid(jnp.arange(H), jnp.arange(Wd), indexing="ij"), -1).reshape(-1, 2)
    cells = cells.astype(S.agent_pos.dtype)

    def one(state):
        return jax.vmap(lambda pt: _sense_olfaction_at(pt, state, p)[0])(cells)

    f = jax.jit(jax.vmap(one))(S)
    return np.asarray(f).reshape(-1, H, Wd)


def check_smell(p, S, fields):
    H, Wd = int(p.height), int(p.width)
    rp, ra = np.asarray(S.res_pos), np.asarray(S.res_active)
    food = ra & (np.asarray(p.res_property)[None, :, 0] > 0)
    wp = np.asarray(S.water_pos)
    E = fields.shape[0]
    rr, cc = np.meshgrid(np.arange(H), np.arange(Wd), indexing="ij")
    nb = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    stats = {d: [0.0, 0, 0.0, 0.0, 0] for d in DIST_BINS}   # success, n, chance, in-range, n_any_to_any
    any_in_range = []
    for e in range(E):
        src = np.concatenate([rp[e][food[e]], wp[e]], 0)
        dist = np.abs(rr[..., None] - src[None, None, :, 0]) + np.abs(cc[..., None] - src[None, None, :, 1])
        dmin = dist.min(-1)                                          # [H, W]
        F = fields[e]
        Fp = np.pad(F, 1, constant_values=0.0)                      # out of bounds reads zero
        Dp = np.pad(dmin, 1, constant_values=10 ** 6)
        nvals = np.stack([Fp[1 + dr:1 + dr + H, 1 + dc:1 + dc + Wd] for dr, dc in nb], -1)      # [H, W, 4]
        ndist = np.stack([Dp[1 + dr:1 + dr + H, 1 + dc:1 + dc + Wd] for dr, dc in nb], -1)
        inb = ndist < 10 ** 6
        nvals_m = np.where(inb, nvals, -np.inf)
        mx = nvals_m.max(-1, keepdims=True)
        signal = (np.concatenate([F[..., None], np.where(inb, nvals, 0.0)], -1) > 0).any(-1)   # [H, W]
        tied = (nvals_m == mx) & inb & signal[..., None]
        good = ndist < dmin[..., None]
        succ = np.where(tied.sum(-1) > 0, (tied & good).sum(-1) / np.maximum(tied.sum(-1), 1), 0.0)
        chance = (good & inb).sum(-1) / inb.sum(-1)
        nonsrc = dmin > 0
        any_in_range.append(signal[nonsrc].mean())
        for d in DIST_BINS:
            m = dmin == d
            if m.any():
                stats[d][0] += succ[m].sum()
                stats[d][1] += int(m.sum())
                stats[d][2] += chance[m].sum()
                stats[d][3] += signal[m].sum()
    out = {"any_channel0_smell_in_range_at_a_random_cell": float(np.mean(any_in_range))}
    for d, (s, n, ch, ir, _) in stats.items():
        out[f"d={d}"] = ({"n_cells": n, "points_to_nearest": s / n, "chance": ch / n,
                          "smell_in_range": ir / n} if n else {"n_cells": 0})
    return out


def walk_lengths(p, S):
    ag = np.asarray(S.agent_pos)
    wp = np.asarray(S.water_pos)
    d = np.abs(wp - ag[:, None, :]).sum(-1).min(-1)
    return {"start_to_pond_mean": float(d.mean()), "p50": float(np.percentile(d, 50)),
            "p95": float(np.percentile(d, 95)), "max": int(d.max())}


def render(name, p, S, fields, e=0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    H, Wd = int(p.height), int(p.width)
    is_fire = np.asarray(heat_source_mask(p.obs_temperature, p.obs_temp_ratio_low, p.obs_temp_ratio_high))
    hides = np.asarray(p.obs_hides_agent)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    ax = axes[0]
    ax.set_xlim(-0.5, Wd - 0.5); ax.set_ylim(H - 0.5, -0.5); ax.set_aspect("equal")
    ax.set_xticks(range(Wd)); ax.set_yticks(range(H)); ax.tick_params(labelsize=6); ax.grid(alpha=0.25)
    for r, c in np.asarray(S.water_pos)[e]:
        ax.add_patch(Rectangle((c - 0.5, r - 0.5), 1, 1, color="#4aa3df", alpha=0.6, lw=0))

    def plot(pos, mask, **kw):
        if mask.any():
            ax.scatter(pos[mask, 1], pos[mask, 0], **kw)

    op, oa = np.asarray(S.obs_pos)[e], np.asarray(S.obs_active)[e]
    plot(op, oa & hides, marker="s", s=90, c="#2e7d32", alpha=0.55, label="bush")
    plot(op, oa & is_fire, marker="^", s=110, c="#e65100", label="campfire")
    plot(op, oa & ~hides & ~is_fire, marker="x", s=40, c="#555555", label="rock")
    rp, ra = np.asarray(S.res_pos)[e], np.asarray(S.res_active)[e]
    rt = np.asarray(p.res_type)
    plot(rp, ra & (rt == 0), marker="o", s=60, c="#c2185b", label="food")
    plot(rp, ra & (rt == 1), marker="v", s=40, c="#6a1b9a", alpha=0.6, label="ambusher (hidden)")
    an, aa = np.asarray(S.animal_pos)[e], np.asarray(S.animal_active)[e]
    cls = np.asarray(p.animal_classes_int)
    plot(an, aa & (cls == 0), marker="D", s=60, c="#b71c1c", label="predator")
    plot(an, aa & (cls == 1), marker="d", s=60, c="#8d6e63", label="rabbit")
    ag = np.asarray(S.agent_pos)[e]
    ax.scatter([ag[1]], [ag[0]], marker="*", s=220, c="gold", edgecolors="k", label="agent start", zorder=5)
    ax.set_title(f"{name}: sample start layout (pond = blue block)", fontsize=9)
    ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax2 = axes[1]
    im = ax2.imshow(fields[e], cmap="viridis")
    ax2.set_title(f"channel-0 (food + pond) smell, sensor_radius {float(p.sensor_radius):g}", fontsize=9)
    fig.colorbar(im, ax=ax2, fraction=0.046, label="smell strength (sum of 1/distance)")
    ax2.set_xlabel("column (cells)"); ax2.set_ylabel("row (cells)")
    fig.tight_layout()
    path = os.path.join(OUT, f"layout_{name}.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


results = {}
for name, rel in WORLDS:
    print(f"== {name}  {rel}", flush=True)
    p, load = check_load(name, rel)
    keys = jax.random.split(jax.random.PRNGKey(7), N)
    S = jax.jit(jax.vmap(lambda k: jax_reset(p, k)))(keys)
    place = check_placement(p, S)
    Ssm = jax.tree_util.tree_map(lambda x: x[:N_SMELL], S)
    fields = smell_fields(p, Ssm)
    smell = check_smell(p, Ssm, fields)
    walk = walk_lengths(p, S)
    png = render(name, p, S, fields)
    results[name] = {"config": rel, "load": load, "placement": place, "smell": smell, "walk": walk, "png": png}
    print(json.dumps(results[name], indent=1, default=str), flush=True)

tag = "_".join(sys.argv[1:]) if len(sys.argv) > 1 else "all"
with open(os.path.join(OUT, f"validate_{tag}.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print("saved", os.path.join(OUT, f"validate_{tag}.json"))
