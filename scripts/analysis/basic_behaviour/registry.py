#!/usr/bin/env python3
"""registry.py - what a run's own saved config says can be measured, and what was randomised.

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), B1-B3, A2b.

Everything here is derived from the config the TRAINER saved beside the run's checkpoints and from
the trajectory store's manifest, never typed per world:

    targets(cfg, manifest, step_cols, obs)   B1  the five behaviours, available or not (with reason)
    slots(cfg, manifest)                     per-declaration slot ranges, cross-checked with the store
    factors(cfg, manifest, obs, thermo)      B2  the factor list, in the fixed role order
    audit(cfg, thermo)                       B2  every randomised-draw marker, claimed or unhandled
    obs_indices(cfg, manifest)               A2b body-temperature / own-thermoception indices
    thermal_info(cfg, params)                N2  what ambient-temperature recovery needs
    water_info(cfg, params), pond_cells()    water worlds: world features and the per-episode pond
                                             replay (docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md)

On a01 (the hiding page's agent) the factor names and their order are the legacy
`hiding_drivers.fit_glms` ones; that is what the byte-identity gate relies on.

Hard constraint (plan "Not changed"): nothing here edits a golden-stamped file; `core/env.py` and
`hiding_drivers.py` are imported as they stand.
"""
from __future__ import annotations

import copy
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))       # two levels under scripts/
A_DIR = os.path.join(ROOT, "scripts", "analysis")
# Data location (BASIC_BEHAVIOUR_WATER D13). Unset: data and outputs live under the code's own
# checkout, exactly as before. Set (a git worktree, which has no results/ and cannot symlink to it on
# the NAS): runs, stores and references resolve under $BB_DATA_ROOT, and every output of this
# pipeline goes under results/analysis/basic_behaviour/_water_dev/ there. Source hashes always use ROOT.
DATA_ROOT = ROOT
BB_ROOT = os.path.join(ROOT, "results", "analysis", "basic_behaviour")
if os.environ.get("BB_DATA_ROOT"):
    DATA_ROOT = os.path.realpath(os.environ["BB_DATA_ROOT"])
    if not os.path.isdir(os.path.join(DATA_ROOT, "results")):
        raise SystemExit(f"BB_DATA_ROOT={DATA_ROOT} has no results/ folder")
    BB_ROOT = os.path.join(DATA_ROOT, "results", "analysis", "basic_behaviour", "_water_dev")
DATA_BB_ROOT = os.path.join(DATA_ROOT, "results", "analysis", "basic_behaviour")   # references
for p in (os.path.join(A_DIR, "core"), A_DIR, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("JAX_PLATFORMS", "cpu")      # params rebuild only; never claim a GPU

import env as ENV                                                    # noqa: E402  core/env.py
from hiding_drivers import NEAR_D, INJ_EDGES, NUT_EDGES              # noqa: E402,F401

# ---------------------------------------------------------------- pre-registered constants (Q2) ----
MIN_EPISODES = 1000          # degeneracy floor, not a power criterion
COLLINEAR_R = 0.999

# entity trait -> (store episode column). Order fixes the factor order (legacy on a01).
TRAITS = [("detection_range", "animal_detect_sampled"),
          ("attack_delay", "animal_attack_delay_sampled"),
          ("attack_range", "animal_attack_range_sampled"),
          ("max_stamina", "animal_max_stamina_sampled"),
          ("stamina_recovery_rate", "animal_recovery_sampled"),
          ("hunt_stamina_threshold", "animal_hunt_thresh_sampled"),
          ("lose_interest_multiplier", "animal_lose_interest_sampled"),
          ("move_interval", "animal_move_int_sampled")]
TRAIT_COLUMNS = dict(TRAITS)

# name maps for KNOWN declarations (legacy names kept); anything else gets a generic name
ENTITY_NAMES = {"pred": dict(prefix="pred", count="n_predators", display="predator",
                             spawn="spawn_dist_to_predator"),
                "rabbit": dict(prefix="rab", count="n_rabbits", display="rabbit",
                               spawn="spawn_dist_to_rabbit")}
OBSTACLE_COUNT = {"bush": "n_bushes", "rock": "n_rocks"}
RESOURCE_COUNT = {"food": "n_food", "hiding_predator": "n_ambush_predators"}
BODY_START = [("injury", "injury_level", "start_injury"),
              ("nutrition", "nutrition", "start_nutrition"),
              ("satiation", "satiation", "start_satiation")]

TARGETS = {"bush_dwell": "hiding in a bush",
           "eating": "eating",
           "near_rabbit": "within two squares of a rabbit",
           "near_predator": "within two squares of a predator",
           "warm_cell": "on a warm square",
           "pond": "on the pond (drinking)"}           # water worlds only (BASIC_BEHAVIOUR_WATER D4)

# consequences whose formula IS (part of) a target's indicator (B3 "is the outcome")
OUTCOME_CONSEQUENCE = {"eating": ["eat_rate"], "near_predator": ["frac_time_predator_near"],
                       "near_rabbit": ["frac_time_rabbit_near"],
                       "warm_cell": ["frac_time_warm_cell"], "pond": ["frac_time_on_pond"]}

# hydration bands of the F6 cross-tables (D8): <50, 50-100, 100-150, 150+
HYD_EDGES = [50.0, 100.0, 150.0]
REPLAY_CHUNK = 2048                         # episodes per vmapped jax_reset (the pilot reader's chunk)


def hyd_band(h):
    """Hydration band index 0-3 (HYD_EDGES). Rounded to 1e-3 first, so a float32 round-trip of a
    value on an edge (100.0 read back as 99.99998) cannot cross the edge (D8)."""
    return np.digitize(np.round(h, 3), HYD_EDGES)

CONSEQUENCES = ["frac_time_injured", "frac_time_inj_severe", "mean_injury", "peak_injury",
                "frac_time_low_nutrition", "mean_nutrition", "total_damage_taken", "eat_rate",
                "rest_rate", "episode_length", "frac_time_predator_near", "frac_time_rabbit_near"]

# config blocks that describe the world (the audit walks these; agent / logging blocks hold no draws)
WORLD_BLOCKS = ("environment", "body", "thermal", "sensory", "perceptual_noise", "water")
NOT_A_DRAW = {
    "damage": "drawn per hit, not per episode",
    "spawn_area": "placement region", "patrol_area": "placement region", "area": "placement region",
    "healing_hunger": "healing-curve breakpoints (fixed parameters, not a per-episode draw)",
}


def decl_label(d: dict) -> str:
    return str(d.get("tag", d.get("name", d.get("type", d.get("class", "?")))))


# ------------------------------------------------------------------------------------- slots ----
def slots(cfg: dict, manifest: dict | None = None) -> dict:
    """Per-declaration slot ranges, plus the class-level lists `core/env.slot_layout` gives.

    Cross-checked against the store manifest's per-slot classes / tags / obstacle names / resource
    types; any disagreement is a hard stop (plan B2 "Slot cross-check").
    """
    env = cfg["environment"]
    lay = ENV.slot_layout(cfg)
    ents, s = [], 0
    for e in env["entities"]:
        n = ENV._alloc(e, "entity")
        ents.append(dict(tag=e.get("tag", e["class"]), cls=e["class"], slots=list(range(s, s + n)),
                         predator=e["class"] == "predator", decl=e)); s += n
    obs, s = [], 0
    for o in env.get("obstacles", []):
        n = ENV._alloc(o, "obstacle")
        obs.append(dict(name=o.get("name", f"obstacle{len(obs)}"), slots=list(range(s, s + n)),
                        hides=bool(o.get("hides_agent")), decl=o)); s += n
    res, s = [], 0
    for r in env.get("resources", []):
        n = ENV._alloc(r, "resource")
        res.append(dict(name=r.get("name", r.get("type", f"resource{len(res)}")), type=r.get("type"),
                        slots=list(range(s, s + n)), decl=r)); s += n
    out = dict(entities=ents, obstacles=obs, resources=res, pred=lay["pred"], neutral=lay["neutral"],
               bush=[i for o in obs if o["hides"] for i in o["slots"]],
               n_animal=lay["n_animal"], n_obs=sum(len(o["slots"]) for o in obs),
               n_res=sum(len(r["slots"]) for r in res))
    if manifest is not None:
        cross_check_slots(out, manifest)
    return out


def cross_check_slots(S: dict, man: dict) -> None:
    bad = []
    cls = [e["cls"] for e in S["entities"] for _ in e["slots"]]
    tags = [e["tag"] for e in S["entities"] for _ in e["slots"]]
    if list(man.get("animal_classes", [])) != cls:
        bad.append(f"animal classes: config {cls} vs store {man.get('animal_classes')}")
    if list(man.get("animal_tags", [])) != tags:
        bad.append(f"animal tags: config {tags} vs store {man.get('animal_tags')}")
    names = [o["name"] for o in S["obstacles"] for _ in o["slots"]]
    if list(man.get("obstacle_names", [])) != names:
        bad.append(f"obstacle names: config {names} vs store {man.get('obstacle_names')}")
    hides = [o["hides"] for o in S["obstacles"] for _ in o["slots"]]
    if "obs_hides_agent" in man and [bool(x) for x in man["obs_hides_agent"]] != hides:
        bad.append("obstacle hides_agent flags disagree with the store")
    rtype = [0 if r["type"] == "food" else 1 for r in S["resources"] for _ in r["slots"]]
    if list(man.get("res_type", [])) != rtype:
        bad.append(f"resource types: config {rtype} vs store {man.get('res_type')}")
    if bad:
        raise SystemExit("slot cross-check failed (config vs store manifest):\n  " + "\n  ".join(bad))


# ------------------------------------------------------------------------------ params / obs ----
def rebuild_params(cfg: dict):
    """EnvParams from the saved config, exactly as the trajectory collector builds them."""
    from src.environment.config_loader import load_env_params
    from src.environment.saved_config_compat import apply_saved_config_compat
    from src.utils.config import Config
    c = copy.deepcopy(cfg)
    apply_saved_config_compat(c, source="basic_behaviour")
    return load_env_params(Config(c))


def obs_indices(cfg: dict, manifest: dict, params=None) -> dict | None:
    """{body_temp, thermo_own_cell, relative, D} or None when the world has no thermal block.

    The manifest's `observation_breakdown` is written with sort_keys=True, so its key ORDER is
    alphabetical; the order comes from `sensor.get_observation_breakdown(params)` on params rebuilt
    from the saved config, then names, widths and the total D are cross-checked against the manifest.
    The thermoception block's first cell is the agent's own square (sensor.py: centre, up, right,
    down, left); this is verified against the environment's own field by golden_gate.py (S0.4).
    """
    th = cfg.get("thermal") or {}
    water = water_enabled(cfg)
    if not th.get("enabled") and not water:
        return None
    from src.environment.sensor import get_observation_breakdown
    params = params if params is not None else rebuild_params(cfg)
    bd = get_observation_breakdown(params)
    mb = manifest.get("observation_breakdown") or {}
    if dict(bd) != dict(mb):
        raise SystemExit(f"observation breakdown rebuilt from the config {dict(bd)} differs from the "
                         f"store manifest's {mb}")
    D = int(manifest["dims"]["D"])
    if sum(bd.values()) != D:
        raise SystemExit(f"observation widths sum to {sum(bd.values())}, store D = {D}")
    off, idx = 0, {}
    for name, w in bd.items():
        idx[name] = (off, w)
        off += w
    out = {"D": D, "relative": bool(th.get("relative")), "order": list(bd.keys())}
    out["body_temp"] = idx["Body Temperature"][0] if "Body Temperature" in idx else None
    out["thermo_own_cell"] = idx["Thermoception"][0] if "Thermoception" in idx else None
    out["alphabetical_body_temp"] = None
    if "Body Temperature" in mb:
        o = 0
        for name in sorted(mb):
            if name == "Body Temperature":
                out["alphabetical_body_temp"] = o
            o += mb[name]
    if water:                                       # D1; keys absent on worlds without water
        out["hydration"] = idx["Hydration"][0] if "Hydration" in idx else None
        out["hydration_scale"] = float(cfg["water"]["max_hydration"])      # mandatory key
        out["alphabetical_hydration"] = None
        o = 0
        for name in sorted(mb):
            if name == "Hydration":
                out["alphabetical_hydration"] = o
            o += mb[name]
    return out


def water_enabled(cfg: dict) -> bool:
    """True when the saved config has a water block with enabled: true (a real YAML boolean)."""
    w = cfg.get("water")
    if not isinstance(w, dict):
        return False
    if not isinstance(w["enabled"], bool):
        raise SystemExit(f"water.enabled is {w['enabled']!r}, not a boolean")
    return w["enabled"]


def water_info(cfg: dict, params) -> dict:
    """World features of a water world (D6), from the saved config and the rebuilt params.

    Constants within a run: they label worlds on the page, they are not regressors. The corner table
    is the loader's 0-based top-left table (`params.water_topleft_table`), never re-typed here."""
    w = cfg["water"]
    table = [[int(r), int(c)] for r, c in params.water_topleft_table]
    return {"map_size": [int(params.height), int(params.width)],
            "pond_size": [int(x) for x in w["size"]],
            "pond_cells": int(params.water_block_h) * int(params.water_block_w),
            "placement": w["placement"], "pond_corners": table,
            "sensor_radius": int(cfg["sensory"]["sensor_radius"]),
            "max_hydration": float(w["max_hydration"]),
            "random_start_hydration": bool(w["random_start_hydration"])}


def pond_cells(params, seeds) -> dict:
    """Replay each episode's reset (D2): the pond, the start cell and the pond's table row.

    `jax.vmap(jax_reset)` over PRNGKey(episode_seed) in chunks of REPLAY_CHUNK, params rebuilt from
    the saved config exactly as the collector builds them (the THIRST_PILOT section 4.2 method).
    Returns water_pos [n, h*w, 2], agent_pos [n, 2], hydration [n] (the reset's start value), corner
    [n] (row of the 0-based top-left table) and the per-corner flat pond masks [K, H*W]. Every episode
    must match exactly one table row and lie on the grid, else a hard stop."""
    import jax
    from src.environment.core import jax_reset
    seeds = np.asarray(seeds, dtype=np.int64)
    f = jax.jit(lambda s: (lambda st: (st.water_pos, st.agent_pos, st.hydration))(
        jax.vmap(jax_reset, in_axes=(None, 0))(params, jax.vmap(jax.random.PRNGKey)(s))))
    wp, ap, hy = [], [], []
    for i in range(0, len(seeds), REPLAY_CHUNK):
        s = seeds[i:i + REPLAY_CHUNK]
        pad = REPLAY_CHUNK - len(s)                 # one compiled shape for every chunk
        a, b, c = f(np.concatenate([s, np.full(pad, s[-1], np.int64)]) if pad else s)
        n = len(s)
        wp.append(np.asarray(a)[:n]); ap.append(np.asarray(b)[:n]); hy.append(np.asarray(c)[:n])
    wp, ap, hy = np.concatenate(wp), np.concatenate(ap), np.concatenate(hy)
    H, W = int(params.height), int(params.width)
    table = np.asarray(params.water_topleft_table, dtype=np.int64)            # [K, 2], 0-based
    match = (wp[:, 0, None, :] == table[None, :, :]).all(-1)                 # [n, K]
    if not (match.sum(1) == 1).all():
        bad = np.flatnonzero(match.sum(1) != 1)[:10]
        raise SystemExit(f"pond replay: {int((match.sum(1) != 1).sum())} episodes whose pond top-left "
                         f"is not exactly one table row (seeds {seeds[bad].tolist()})")
    corner = match.argmax(1)
    offs = np.asarray([(r, c) for r in range(int(params.water_block_h))
                       for c in range(int(params.water_block_w))], dtype=np.int64)
    want = table[corner][:, None, :] + offs[None]
    if not np.array_equal(wp, want):
        raise SystemExit("pond replay: pond cells are not the table top-left plus the block offsets")
    if (wp < 0).any() or (wp[..., 0] >= H).any() or (wp[..., 1] >= W).any():
        raise SystemExit("pond replay: a pond cell lies outside the grid")
    masks = np.zeros((len(table), H * W), bool)
    for k in range(len(table)):
        cells = table[k] + offs
        masks[k, cells[:, 0] * W + cells[:, 1]] = True
    return {"water_pos": wp, "agent_pos": ap, "hydration": hy.astype(np.float64), "corner": corner,
            "masks": masks, "H": H, "W": W}


def thermal_info(cfg: dict, params) -> dict:
    """What the warm-square target and the ambient-temperature recovery need, or why not (N2, N7)."""
    from src.environment.core import heat_source_mask
    th = cfg["thermal"]
    p = params
    info = {"sigma": float(p.thermal_sigma), "kernel_radius": int(p.thermal_kernel_radius),
            "H": int(p.height), "W": int(p.width),
            "default_low": float(p.thermal_default_temp_low),
            "default_high": float(p.thermal_default_temp_high),
            "k_exchange": float(th["k_exchange"]), "k_loss": float(th["k_loss"]),
            "k_metabolic": float(th["k_metabolic"]), "setpoint": float(th["temperature_setpoint"]),
            "max_temperature": float(th["max_temperature"]),
            "injury_gain": float(th.get("injury_heat_exchange_gain", 0.0))}
    oh = np.asarray(heat_source_mask(np.asarray(p.obs_temperature), np.asarray(p.obs_temp_ratio_low),
                                     np.asarray(p.obs_temp_ratio_high)), bool)
    rh = np.asarray(heat_source_mask(np.asarray(p.res_temperature), np.asarray(p.res_temp_ratio_low),
                                     np.asarray(p.res_temp_ratio_high)), bool) \
        if np.asarray(p.res_temperature).size else np.zeros(0, bool)
    info["heat_obstacle_slots"] = [int(i) for i in np.flatnonzero(oh)]
    why = []
    if th.get("use_random_spots"):
        why.append("thermal.use_random_spots is on (hot-spot positions are not recorded)")
    if rh.any():
        why.append("a resource is a heat source (resource positions at t=0 are not used here)")
    if oh.any():
        lo = np.asarray(p.obs_temp_ratio_low)[oh]; hi = np.asarray(p.obs_temp_ratio_high)[oh]
        ab = np.asarray(p.obs_temperature)[oh]
        if (ab != 0).any():
            why.append("a heat source declares an absolute 'temperature' (not a ratio)")
        elif not np.all(lo == hi) or not np.all(lo == lo[0]):
            why.append(f"heat-source temperature_ratio is drawn per episode ({lo.tolist()}..{hi.tolist()})")
        else:
            info["ratio"] = float(lo[0])
    else:
        info["ratio"] = 0.0
    if info["default_low"] < 0 < info["default_high"]:
        why.append("thermal.default_temp straddles 0, so |baseline| has no fixed sign")
    info["sign"] = -1.0 if info["default_high"] <= 0 else 1.0
    if info["default_low"] == info["default_high"]:
        why.append("thermal.default_temp is fixed (not a draw)")
    info["ambient_unavailable"] = "; ".join(why) or None
    return info


def blur_weights(sigma: float, radius: int, n: int):
    """Row (or column) blur matrix of the environment's weight-normalised Gaussian.

    `core._gaussian_smooth_normalised` is separable in both its numerator and its weight sum, so a
    single stamp at (fr, fc) contributes k[fr - r] * k[fc - c] / (w_row[r] * w_col[c]) at (r, c).
    Returns (Kmat[n, n] with Kmat[r, r'] = k[r' - r] for |r' - r| <= radius, wsum[n]).
    """
    offs = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (offs / sigma) ** 2)
    K = np.zeros((n, n))
    for r in range(n):
        for j, dr in enumerate(offs):
            if 0 <= r + dr < n:
                K[r, r + dr] = k[j]
    return K, K.sum(1)


# ----------------------------------------------------------------------------------- targets ----
def targets(cfg: dict, manifest: dict, step_cols, obs: dict | None, thermo: dict | None) -> dict:
    """{target: {available, label, reason}} per B1."""
    env = cfg["environment"]
    S = slots(cfg)
    cols = set(step_cols)
    out = {}

    def put(t, ok, why=None):
        out[t] = {"label": TARGETS[t], "available": bool(ok), "reason": None if ok else why}

    hides = [o for o in S["obstacles"] if o["hides"] and len(o["slots"]) > 0]
    put("bush_dwell", "agent_in_bush" in cols and hides,
        "no step column agent_in_bush" if "agent_in_bush" not in cols else
        "no obstacle declaration with hides_agent: true and a non-zero allocation")
    food = [r for r in S["resources"] if r["type"] == "food"]
    put("eating", "ate_food" in cols and env.get("eat_action_enabled") and food,
        "no step column ate_food" if "ate_food" not in cols else
        "environment.eat_action_enabled is false" if not env.get("eat_action_enabled") else
        "no resource declaration of type food")
    put("near_rabbit", len(S["neutral"]) > 0, "no neutral-class animal slot")
    put("near_predator", len(S["pred"]) > 0, "no predator-class animal slot")
    th = cfg.get("thermal") or {}
    why = None
    if not th.get("enabled"):
        why = "thermal.enabled is false"
    elif obs is None or obs.get("thermo_own_cell") is None:
        why = "no thermoception in the observation"
    elif obs["relative"] and obs.get("body_temp") is None:
        why = "thermoception is relative but body temperature is not observed"
    elif manifest.get("obs_precision") != "float32":
        why = f"store obs_precision is {manifest.get('obs_precision')!r}, not float32"
    elif "obs_true" not in cols:
        why = "no step column obs_true"
    elif float(th.get("injury_heat_exchange_gain", 0.0)) != 0.0:
        why = ("thermal.injury_heat_exchange_gain is non-zero, so the settling temperature depends "
               "on injury and the static warm band does not apply (plan Revision 2, N7)")
    put("warm_cell", why is None, why)
    if water_enabled(cfg):                  # D4: the pond target exists only in worlds with water
        why = None
        if obs is None or obs.get("hydration") is None:
            why = "no Hydration in the observation"
        elif manifest.get("obs_precision") != "float32":
            why = f"store obs_precision is {manifest.get('obs_precision')!r}, not float32"
        elif "obs_true" not in cols:
            why = "no step column obs_true"
        put("pond", why is None, why)
    return out


# ----------------------------------------------------------------------------------- factors ----
def _varies(v) -> bool:
    return isinstance(v, (list, tuple)) and len(v) == 2 and \
        all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) and v[0] != v[1]


def _ent_names(e: dict) -> dict:
    tag = e["tag"]
    if tag in ENTITY_NAMES:
        return ENTITY_NAMES[tag]
    return dict(prefix=tag, count=f"n_{tag}", display=tag, spawn=f"spawn_dist_to_{tag}")


def _count_varies(d: dict) -> bool:
    return "count_high" in d and int(d.get("count_low", d["count_high"])) < int(d["count_high"])


def factors(cfg: dict, manifest: dict, obs: dict | None, thermo: dict | None) -> list[dict]:
    """Factor specs in the fixed role order (plan B2). Each: name, block, role, subset, source,
    plus what the sweep needs to compute it (`kind` and its arguments)."""
    env, body = cfg["environment"], cfg.get("body") or {}
    th = cfg.get("thermal") or {}
    S = slots(cfg)
    F = []

    def add(name, block, role, subset, source, kind, **kw):
        if any(f["name"] == name for f in F):
            raise SystemExit(f"two factors would be named {name!r}; extend the name map")
        F.append(dict(name=name, block=block, role=role, subset=subset, source=source, kind=kind, **kw))

    # 1 starting body state
    for x, col, nm in BODY_START:
        if body.get(f"random_start_{x}") is True:
            add(nm, "exogenous", "episode", "all", f"body.random_start_{x}", "start", column=col)
    # 2 entity counts
    for e in S["entities"]:
        if _count_varies(e["decl"]):
            add(_ent_names(e)["count"], "exogenous", "episode", "all",
                f"environment.entities[{e['tag']}].count_low/high", "count_entity", tag=e["tag"])
    # 3 obstacle counts, by declaration name (campfires are not rocks)
    for o in S["obstacles"]:
        if _count_varies(o["decl"]):
            add(OBSTACLE_COUNT.get(o["name"], f"n_{o['name']}"), "exogenous", "episode", "all",
                f"environment.obstacles[{o['name']}].count_low/high", "count_obstacle", decl=o["name"])
    # 4 resource counts, by name
    for r in S["resources"]:
        if _count_varies(r["decl"]):
            add(RESOURCE_COUNT.get(r["name"], f"n_{r['name']}"), "exogenous", "episode", "all",
                f"environment.resources[{r['name']}].count_low/high", "count_resource", decl=r["name"])
    # 5 spawn distance to the nearest hiding obstacle
    if env.get("random_start_pos") is True and any(o["hides"] and o["slots"] for o in S["obstacles"]):
        add("spawn_dist_to_bush", "exogenous", "episode", "all", "environment.random_start_pos",
            "spawn_dist_bush")
    # 6 starting body temperature (from obs_true at t = 0)
    if th.get("enabled") and th.get("random_start_body_temp") and th.get("body_temp_observable") \
            and obs is not None and obs.get("body_temp") is not None:
        add("start_body_temp", "exogenous", "episode", "all", "thermal.random_start_body_temp",
            "start_body_temp")
    # 6b baseline world temperature (N2)
    if th.get("enabled") and _varies(list(th.get("default_temp", [0, 0]))) and thermo is not None \
            and thermo.get("ambient_unavailable") is None and obs is not None \
            and obs.get("thermo_own_cell") is not None and (obs.get("body_temp") is not None
                                                            or not obs["relative"]):
        add("ambient_temp", "exogenous", "episode", "all", "thermal.default_temp", "ambient_temp")
    # 7 / 8 class traits: predator-class declarations first, then neutral-class
    spec = None
    try:
        spec = ENV.scent_spec(cfg)
    except SystemExit:
        spec = None
    for want_pred in (True, False):
        for e in [x for x in S["entities"] if x["predator"] == want_pred]:
            nm = _ent_names(e)
            sub = f"one:{e['tag']}"
            for key, col in TRAITS:
                if _varies(e["decl"].get(key)):
                    add(f"{nm['prefix']}_{key}", "exogenous", f"class_trait:{e['tag']}", sub,
                        f"environment.entities[{e['tag']}].{key}", "trait", tag=e["tag"], column=col)
            smells = spec is not None and _smell_varies(e["decl"], spec)
            if smells:
                add(f"{nm['prefix']}_smell_predatorness", "exogenous", f"class_trait:{e['tag']}", sub,
                    f"environment.entities[{e['tag']}].properties_std", "smell", tag=e["tag"])
            if want_pred and env.get("random_start_pos") is True:
                add(nm["spawn"], "exogenous", f"class_trait:{e['tag']}", sub,
                    "environment.random_start_pos", "spawn_dist_entity", tag=e["tag"])
            if smells:
                add(f"{nm['prefix']}_olf_intensity", "exogenous", f"class_trait:{e['tag']}", sub,
                    f"environment.entities[{e['tag']}].properties_std", "intensity", tag=e["tag"])
    # 9 consequences (legacy formulas)
    for c in CONSEQUENCES:
        add(c, "consequence", "consequence", "all", "episode outcome", "consequence")
    # 10 thermal consequences
    if obs is not None and obs.get("body_temp") is not None:
        add("mean_body_temp", "consequence", "consequence", "all", "obs_true Body Temperature",
            "consequence")
    return F


def _smell_varies(decl: dict, spec) -> bool:
    sd = decl.get("properties_std") or []
    return any(float(sd[c]) > 0 for c in spec.channels if c < len(sd))


def add_thermal_consequence(F: list, warm_available: bool) -> None:
    if warm_available and not any(f["name"] == "frac_time_warm_cell" for f in F):
        F.append(dict(name="frac_time_warm_cell", block="consequence", role="consequence",
                      subset="all", source="obs_true thermoception + body temperature",
                      kind="consequence"))


def add_water_factors(F: list, cfg: dict, T: dict) -> None:
    """D5: water factors and consequences, appended after every existing factor (so the order of a
    world without water is untouched). Only when the pond target is available: the pond replay and
    the hydration read that these need run only then."""
    if "pond" not in T or not T["pond"]["available"]:
        return
    w, env = cfg["water"], cfg["environment"]
    names = {f["name"] for f in F}

    def add(name, block, role, source, kind):
        if name in names:
            raise SystemExit(f"two factors would be named {name!r}")
        F.append(dict(name=name, block=block, role=role, subset="all", source=source, kind=kind))

    if w["random_start_hydration"] is True:
        add("start_hydration", "exogenous", "episode", "water.random_start_hydration", "start_hydration")
    if env.get("random_start_pos") is True:
        add("spawn_dist_to_pond", "exogenous", "episode", "environment.random_start_pos + water pond",
            "spawn_dist_pond")
    add("mean_hydration", "consequence", "consequence", "obs_true Hydration", "consequence")
    add("frac_time_on_pond", "consequence", "consequence", "agent cell on the replayed pond",
        "consequence")


def m5_helpers(F: list, S: dict) -> dict | None:
    """The fixed M5 recipe's helpers for the first predator class, or None with a reason."""
    c1 = next((e for e in S["entities"] if e["predator"]), None)
    if c1 is None:
        return {"skip": "no predator-class declaration"}
    nm = _ent_names(c1)["prefix"]
    need = [f"{nm}_detection_range", f"{nm}_attack_delay", f"{nm}_max_stamina"]
    names = {f["name"] for f in F}
    miss = [n for n in need if n not in names]
    if miss:
        return {"skip": f"first predator class lacks varying traits {miss}"}
    return {"tag": c1["tag"], "prefix": nm}


# ------------------------------------------------------------------------------------- audit ----
def _walk(node, path):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
        yield ("dict", path, node)
    elif isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node):
            for i, x in enumerate(node):
                lab = decl_label(x)
                yield from _walk(x, f"{path}[{lab}]")


def audit(cfg: dict, F: list[dict], thermo: dict | None, spec_ok: bool = True) -> list[dict]:
    """Every randomised-draw marker in the saved config; claimed ones return {..., claimed_by},
    unclaimed ones are the *unhandled* rows (plan B2). Nothing here stops the run."""
    names = {f["name"]: f for f in F}
    sources = {}
    for f in F:
        sources.setdefault(f["source"], []).append(f["name"])
    rows = []
    try:
        spec = ENV.scent_spec(cfg)
    except SystemExit as e:
        spec, spec_err = None, str(e)
    else:
        spec_err = None

    def row(marker, path, claimed_by=None, why=None):
        rows.append({"marker": marker, "path": path, "claimed_by": claimed_by,
                     "why_no_handler": None if claimed_by else why})

    for block in WORLD_BLOCKS:
        if not isinstance(cfg.get(block), dict):
            continue
        if block == "water" and not water_enabled(cfg):
            continue                        # D7: walked only in worlds with water
        for kind, path, d in _walk(cfg[block], block):
            for k, v in d.items():
                p = f"{path}.{k}"
                leaf = k
                if path == "water" and k == "placement":                         # D7 marker W2
                    if v == "random" or (v == "list" and len(d["candidates"]) > 1):
                        got = [n for n in ("spawn_dist_to_pond",) if n in names]
                        row("pond placement drawn per episode", p,
                            "handler W2 (pond_corner" + (", " + ", ".join(got) if got else "") + ")"
                            if "frac_time_on_pond" in names else None,
                            "the pond is not replayed (pond target unavailable)")
                    else:
                        row("pond placement", p, f"not a draw (placement {v!r}"
                            + (", one candidate)" if v == "list" else ")"))
                if leaf.startswith("random_") and v is True:
                    if path == "water" and leaf == "random_start_hydration":
                        row("random_* true", p, "handler W1 (start_hydration)" if "start_hydration"
                            in names else None, "Hydration is not read from the observation")
                    elif leaf == "random_start_pos":
                        row("random_* true", p, "handler 5 / 7 (spawn distances)")
                    elif leaf == "random_start_body_temp":
                        row("random_* true", p, "handler 6 (start_body_temp)" if "start_body_temp" in names
                            else None, "body temperature is not observable, so its start is not recorded")
                    elif leaf.startswith("random_start_"):
                        x = leaf[len("random_start_"):]
                        nm = next((n for xx, _, n in BODY_START if xx == x), None)
                        row("random_* true", p, f"handler 1 ({nm})" if nm in names else None,
                            f"no store step column for body variable '{x}'")
                    else:
                        row("random_* true", p, None, "no handler for this random_* switch")
                if leaf == "use_random_spots" and v is True:
                    row("thermal hot spots on", p, None, "hot-spot positions are not recorded in the store")
                if leaf.endswith("_low") and f"{leaf[:-4]}_high" in d and d[leaf] != d[f"{leaf[:-4]}_high"]:
                    base = leaf[:-4]
                    pp = f"{path}.{base}_low/_high"
                    if base == "count":
                        cl = sources.get(f"{path}.count_low/high", [])
                        row("count_low < count_high", pp, f"count handler ({', '.join(cl)})" if cl
                            else None, "count varies but no factor was produced")
                    elif base.startswith("start_body_temp"):
                        row("_low/_high pair", pp, "handler 6 (start_body_temp)" if "start_body_temp"
                            in names else "not a draw (body temperature start not randomised)")
                    elif base.startswith("start_"):
                        x = base[len("start_"):]
                        # the switch lives in the same block as the pair (D7; W-b): body.* for the
                        # body variables, water.random_start_hydration for start_hydration_low/_high
                        rnd = d.get(f"random_start_{x}") is True
                        nm = next((n for xx, _, n in BODY_START if xx == x), None)
                        if not rnd:
                            row("_low/_high pair", pp, f"not a draw (random_start_{x} is false)")
                        elif path == "water" and x == "hydration":
                            row("_low/_high pair", pp, "handler W1 (start_hydration)" if
                                "start_hydration" in names else None,
                                "Hydration is not read from the observation")
                        else:
                            row("_low/_high pair", pp, f"handler 1 ({nm})" if nm in names else None,
                                f"no store step column for body variable '{x}'")
                    elif base in NOT_A_DRAW:
                        row("_low/_high pair", pp, f"not a draw ({NOT_A_DRAW[base]})")
                    else:
                        row("_low/_high pair", pp, None, "no handler for this range")
                if _varies(v) and _in_decl_or_thermal(path):
                    if k in NOT_A_DRAW:
                        row("[a, b] range", p, f"not a draw ({NOT_A_DRAW[k]})")
                    elif block == "thermal" and k == "default_temp":
                        row("[a, b] range", p, "handler 6b (ambient_temp)" if "ambient_temp" in names
                            else None, (thermo or {}).get("ambient_unavailable")
                            or "ambient temperature recovery unavailable")
                    elif k in TRAIT_COLUMNS and path.startswith("environment.entities"):
                        got = [n for n in sources.get(p, [])]
                        row("[a, b] range", p, f"handler 7/8 ({', '.join(got)})" if got else None,
                            "trait range with no factor")
                    else:
                        row("[a, b] range", p, None, f"no handler for a per-episode range on '{k}'")
                if k in ("properties_std", "visual_properties_std") and isinstance(v, list) \
                        and any(float(x) > 0 for x in v) and path.startswith("environment."):
                    on = [i for i, x in enumerate(v) if float(x) > 0]
                    if k == "properties_std" and path.startswith("environment.entities") \
                            and spec is not None and set(on) <= set(spec.channels):
                        got = sources.get(p, [])
                        row("properties_std > 0", p, f"smell handler ({', '.join(got)})" if got else
                            "smell handler (constant smell factor dropped by pre-fit)")
                    elif k == "properties_std" and path.startswith("environment.entities"):
                        row("properties_std > 0", p, None,
                            spec_err or f"odour noise on non-emitting channels {on}")
                    elif k == "properties_std":
                        row("properties_std > 0", p, None,
                            "resource / obstacle property draws are re-drawn on regeneration "
                            "(store schema section 6)")
                    else:
                        row("visual_properties_std > 0", p, None, "visual-property draws have no handler")
    return rows


def _in_decl_or_thermal(path: str) -> bool:
    return path.startswith(("environment.entities[", "environment.obstacles[",
                            "environment.resources[", "thermal"))


def unhandled(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not r["claimed_by"]]
