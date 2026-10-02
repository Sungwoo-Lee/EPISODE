"""Part 3a of the context-exploration study: generate the larger, less observable level-05 worlds and
check them on real environment resets.

Plain-language purpose: level 05 is a 10 x 10 campfire world whose smells carry 20 cells, so nothing is
out of smell range. This script writes throw-away variants -- grid 15 x 15 or 20 x 20, a shorter smell
range, fewer or longer-lasting food items -- as YAML files that extend level 05, loads each through the
trainer's own loader, runs 1,000 real resets per world, checks that placement did what the file says,
and saves the reset maps (agent start, food, bushes, rocks, fires, temperature field) for forager.py.
No file is written under configs/ (Part 4 configs come later, from the chosen worlds only).

Worlds (STUDY_PLAN.md Part 3, Revisions 1 and 1a):
  grid           10 (today), 15, 20; scaling factor f = (G / 10)^2 = 2.25 / 4
  smell range    20 (today), 8, 5, 3 (sensory.sensor_radius); the reset does not depend on it, so the
                 four ranges of one layout share its resets (each range's YAML is still loaded and
                 checked to differ from the range-20 world only in sensor_radius)
  food           count as today 1-4 (bites 12); density as today (f-scaled; bites 12); middle rung 2-4
                 at 15 x 15, 2-6 at 20 x 20 (bites 12); "few and rich" 1-2 items, 36 bites
  other things   fires, bushes, predators, rabbits, ambushers, rocks at today's density (primary, "od")
                 or today's count (check, "oc")
  keys widened   food / hiding_predator spawn_area; predator and rabbit spawn_area AND patrol_area;
                 rock / bush / campfire area; location_areas grass area; height / width
  counts         low' = max(1, round_half_up(f * low)) (low' = 0 when today's low is 0),
                 high' = round_half_up(f * high)
Per-reset assertions (a failure stops that world): (1) positions of every placed type span the area
the config allows, to within 1 cell of each edge, over the 1,000 resets; (2) no active item of a type
whose area excludes cell (0,0) sits at (0,0) -- for types whose area includes (0,0) the count at (0,0)
is reported next to the mean of the other three corners; (3) every drawn fire is placed inside its
inset area and at least min_fire_separation from every other fire. If (3) fails, the world's fire
count_high is lowered to the largest value that places all fires on 1,000 of 1,000 resets and the
world is labelled "fires capped at k".

  python make_worlds.py --procs 16 --resets 1000 --out results/analysis/context_exploration/worlds
"""
import argparse, copy, json, math, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LEVEL05 = "environment/experiment/basic/05-campfire_thermal_10x10"
RANGES = (20, 8, 5, 3)
FOOD = {  # name -> {grid: (low, high)} (None = density-scaled), bites
    "count": dict(n={10: (1, 4), 15: (1, 4), 20: (1, 4)}, bites=12),
    "density": dict(n={10: None, 15: None, 20: None}, bites=12),
    "mid": dict(n={15: (2, 4), 20: (2, 6)}, bites=12),
    "fewrich": dict(n={10: (1, 2), 15: (1, 2), 20: (1, 2)}, bites=36),
}


def rhu(x):
    return int(math.floor(x + 0.5))


def scale_count(low, high, f):
    return (0 if low == 0 else max(1, rhu(f * low))), rhu(f * high)


def _counts(e):
    if "count" in e:
        return e["count"], e["count"]
    return e["count_low"], e["count_high"]


def _set_counts(e, lo, hi):
    e.pop("count", None); e["count_low"] = lo; e["count_high"] = hi


def base_lists():
    sys.path.insert(0, ROOT)
    from src.environment.config_loader import load_env_config
    cfg = load_env_config(os.path.join(ROOT, "configs", LEVEL05 + ".yaml"))
    env = cfg.get("environment")
    return {k: copy.deepcopy(env[k]) for k in ("resources", "entities", "obstacles", "location_areas")}


def layouts():
    """Reset groups: (grid, food setting, other-things scaling). 10 x 10 has one scaling and no mid rung;
    its "count" and "density" food settings are the same world, so only "count" is kept ("today")."""
    out = []
    for G in (10, 15, 20):
        for food in FOOD:
            if G not in FOOD[food]["n"] or (G == 10 and food == "density"):
                continue
            for others in (("od",) if G == 10 else ("od", "oc")):
                out.append((G, food, others))
    return out


def food_slug(G, food, lo, hi):
    return f"f{lo}to{hi}b{FOOD[food]['bites']}"


def build_env(G, food, others, lists, fire_high=None):
    """The environment block of one world, and a description of every changed key."""
    f = (G / 10.0) ** 2
    L = copy.deepcopy(lists); changed = {}
    area = [[1, 1], [G, G]]
    A = lambda: [[1, 1], [G, G]]                         # fresh list per key (no YAML anchors)
    for r in L["resources"]:
        lo, hi = _counts(r)
        if r["type"] == "food":
            spec = FOOD[food]["n"][G]
            nlo, nhi = scale_count(lo, hi, f) if spec is None else spec
            _set_counts(r, nlo, nhi); r["max_consumption"] = FOOD[food]["bites"]
        else:
            nlo, nhi = scale_count(lo, hi, f) if others == "od" else (lo, hi)
            _set_counts(r, nlo, nhi)
        r["spawn_area"] = A()
        changed[f"resources.{r['name']}"] = dict(count=[r["count_low"], r["count_high"]], spawn_area=area,
                                                  max_consumption=r.get("max_consumption"))
    for e in L["entities"]:
        lo, hi = _counts(e)
        nlo, nhi = scale_count(lo, hi, f) if others == "od" else (lo, hi)
        _set_counts(e, nlo, nhi); e["spawn_area"] = A(); e["patrol_area"] = A()
        changed[f"entities.{e['tag']}"] = dict(count=[nlo, nhi], spawn_area=area, patrol_area=area)
    for o in L["obstacles"]:
        lo, hi = _counts(o)
        if hi == 0:
            continue                                       # tree: count 0, inert, left as level 05 has it
        nlo, nhi = scale_count(lo, hi, f) if others == "od" else (lo, hi)
        if o["name"] == "campfire" and fire_high is not None:
            nhi = fire_high; nlo = min(nlo, nhi)
        _set_counts(o, nlo, nhi); o["area"] = A()
        changed[f"obstacles.{o['name']}"] = dict(count=[nlo, nhi], area=area)
    for la in L["location_areas"]:
        if la["type"] == "grass":
            la["area"] = A(); changed["location_areas.grass"] = dict(area=area)
    env = dict(height=G, width=G, location_areas=L["location_areas"], resources=L["resources"],
               entities=L["entities"], obstacles=L["obstacles"])
    food_e = next(r for r in L["resources"] if r["type"] == "food")
    return env, changed, (food_e["count_low"], food_e["count_high"])


def write_yaml(path, env, rng):
    doc = {"extends": LEVEL05, "environment": env, "sensory": {"sensor_radius": rng}}
    with open(path, "w") as fh:
        fh.write("# THROW-AWAY measurement world (context-exploration study, Part 3) -- generated by\n"
                 "# scripts/analysis/studies/context_exploration/make_worlds.py; not a training config.\n")
        yaml.safe_dump(doc, fh, sort_keys=False, default_flow_style=None)


def _reset_all(P, n):
    import jax
    from src.environment import core
    keys = jax.vmap(jax.random.PRNGKey)(np.arange(n))
    st = jax.jit(jax.vmap(core.jax_reset, in_axes=(None, 0)))(P, keys)
    return {k: np.asarray(getattr(st, k)) for k in ("agent_pos", "res_pos", "res_active", "obs_pos", "obs_active",
                                                     "animal_pos", "animal_active", "thermal_field")}


def _span(pos, act, area, G):
    """area: 0-based [r0, c0, r1, c1) per slot. Returns (ok, detail) for positions of active slots."""
    if not act.any():
        return None, "never placed"
    p = pos[act]
    r0, c0 = area[:, 0].min(), area[:, 1].min(); r1, c1 = area[:, 2].max() - 1, area[:, 3].max() - 1
    lo_r, hi_r, lo_c, hi_c = p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()
    ok = lo_r <= r0 + 1 and hi_r >= r1 - 1 and lo_c <= c0 + 1 and hi_c >= c1 - 1
    return bool(ok), dict(allowed=[int(r0), int(c0), int(r1), int(c1)], seen=[int(lo_r), int(lo_c), int(hi_r), int(hi_c)])


def check_resets(P, S, G):
    """The three per-reset assertions. Returns (ok_1_2, fires_ok, report)."""
    res_type = np.asarray(P.res_type); obs_hides = np.asarray(P.obs_hides_agent)
    obs_dmg = np.asarray(P.obs_damage)[:, 1] > 0; fire = np.asarray(P.obs_temp_ratio_high) > 0
    cls = np.asarray(P.animal_classes_int)
    groups = {
        "food": ("res", res_type == 0), "ambusher": ("res", res_type == 1),
        "predator": ("animal", cls == 0), "rabbit": ("animal", cls == 1),
        "rock": ("obs", obs_dmg & ~fire), "bush": ("obs", obs_hides), "fire": ("obs", fire)}
    areas = {"res": np.asarray(P.res_spawn_area), "animal": np.asarray(P.animal_spawn_area),
             "obs": np.asarray(P.obs_spawn_area)}
    rep = {}; ok12 = True
    for name, (kind, slots) in groups.items():
        pos = S[f"{kind}_pos"][:, slots]; act = S[f"{kind}_active"][:, slots]
        area = areas[kind][slots]
        span_ok, det = _span(pos, act, area, G)
        excl00 = bool((area[:, 0] > 0).all() or (area[:, 1] > 0).all())
        at00 = int(((pos[..., 0] == 0) & (pos[..., 1] == 0) & act).sum())
        corners = [int(((pos[..., 0] == r) & (pos[..., 1] == c) & act).sum()) for r, c in ((0, G - 1), (G - 1, 0), (G - 1, G - 1))]
        z_ok = (at00 == 0) if excl00 else True
        rep[name] = dict(span_ok=span_ok, span=det, area_excludes_00=excl00, active_at_00=at00,
                         mean_other_corners=float(np.mean(corners)), zero_zero_ok=bool(z_ok),
                         placed_per_reset_mean=float(act.sum(1).mean()))
        if span_ok is False or not z_ok:
            ok12 = False
    # (3) fires
    fp = S["obs_pos"][:, fire]; fa = S["obs_active"][:, fire]; fa_area = areas["obs"][fire]
    sep = int(P.thermal_min_fire_separation)
    bad = 0
    for i in range(fp.shape[0]):
        p = fp[i][fa[i]]; ar = fa_area[fa[i]]
        inside = ((p[:, 0] >= ar[:, 0]) & (p[:, 0] < ar[:, 2]) & (p[:, 1] >= ar[:, 1]) & (p[:, 1] < ar[:, 3])).all()
        d = np.abs(p[:, None, :] - p[None, :, :]).sum(-1) + np.eye(len(p), dtype=int) * 999
        if not inside or (len(p) > 1 and d.min() < sep):
            bad += 1
    rep["fire_placement"] = dict(resets_with_misplaced_fire=bad, min_fire_separation=sep,
                                 drawn_per_reset_mean=float(fa.sum(1).mean()))
    return ok12, bad == 0, rep


def run_layout(args):
    G, food, others, out, n_resets = args
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    sys.path.insert(0, ROOT)
    from src.environment.config_loader import load_env_config, load_env_params
    t0 = time.time()
    lists = base_lists()
    fire_high = None; cap_note = None
    while True:
        env, changed, (flo, fhi) = build_env(G, food, others, lists, fire_high)
        lay = f"g{G}{food_slug(G, food, flo, fhi)}_{others}"
        wdir = os.path.join(out, lay); os.makedirs(wdir, exist_ok=True)
        paths = {}
        for r in RANGES:
            paths[r] = os.path.join(wdir, f"g{G}r{r}{food_slug(G, food, flo, fhi)}_{others}.yaml")
            write_yaml(paths[r], env, r)
        P = load_env_params(load_env_config(paths[20]))
        assert P.height == G and P.width == G and float(P.sensor_radius) == 20.0
        S = _reset_all(P, n_resets)
        ok12, fires_ok, rep = check_resets(P, S, G)
        if fires_ok:
            break
        cur = max(c["count"][1] for k, c in changed.items() if k == "obstacles.campfire")
        if cur <= 1:
            break
        fire_high = cur - 1; cap_note = f"fires capped at {fire_high}"
        print(f"[make_worlds] {lay}: fire misplaced on {rep['fire_placement']['resets_with_misplaced_fire']} resets; "
              f"retrying with fire count_high {fire_high}", flush=True)
    # every range's YAML: loads, and differs from the range-20 world only in sensor_radius
    import dataclasses
    ref = {f.name: getattr(P, f.name) for f in dataclasses.fields(P)}
    range_check = {}
    for r in RANGES[1:]:
        Pr = load_env_params(load_env_config(paths[r]))
        diff = []
        for f in dataclasses.fields(Pr):
            a, b = getattr(Pr, f.name), ref[f.name]
            try:
                same = bool(np.array_equal(np.asarray(a), np.asarray(b)))
            except Exception:
                same = a == b
            if not same:
                diff.append(f.name)
        range_check[str(r)] = dict(sensor_radius=float(Pr.sensor_radius), differing_fields=diff,
                                   ok=bool(diff == ["sensor_radius"] and float(Pr.sensor_radius) == r))
    # save the reset maps the forager needs
    obs_dmg = np.asarray(P.obs_damage)[:, 1] > 0; fire = np.asarray(P.obs_temp_ratio_high) > 0
    np.savez_compressed(os.path.join(wdir, "resets.npz"), agent_pos=S["agent_pos"],
                        food_pos=S["res_pos"][:, np.asarray(P.res_type) == 0], food_act=S["res_active"][:, np.asarray(P.res_type) == 0],
                        bush_pos=S["obs_pos"][:, np.asarray(P.obs_hides_agent)], bush_act=S["obs_active"][:, np.asarray(P.obs_hides_agent)],
                        rock_pos=S["obs_pos"][:, obs_dmg & ~fire], rock_act=S["obs_active"][:, obs_dmg & ~fire],
                        fire_pos=S["obs_pos"][:, fire], fire_act=S["obs_active"][:, fire],
                        thermal_field=S["thermal_field"])
    obs_width = sum(int(v) for v in __import__("src.environment.sensor", fromlist=["x"]).get_observation_breakdown(P).values())
    info = dict(layout=lay, grid=G, food=food, others=others, food_count=[flo, fhi], bites=FOOD[food]["bites"],
                scaling_factor=(G / 10.0) ** 2, changed_keys=changed, fires_capped=cap_note,
                yaml={str(r): os.path.relpath(paths[r], ROOT) for r in RANGES},
                assertions=dict(span_and_00_ok=ok12, fires_ok=fires_ok, ranges_ok=all(v["ok"] for v in range_check.values()),
                                detail=rep, range_check=range_check),
                world_ok=bool(ok12 and fires_ok and all(v["ok"] for v in range_check.values())),
                resets=n_resets, observation_width=obs_width, seconds=time.time() - t0)
    json.dump(info, open(os.path.join(wdir, "layout.json"), "w"), indent=1)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--resets", type=int, default=1000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="comma-separated layouts as G:food:others (smoke)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    L = layouts()
    if a.only:
        want = {tuple(x.split(":")) for x in a.only.split(",")}
        L = [l for l in L if (str(l[0]), l[1], l[2]) in want]
    os.environ["JAX_PLATFORMS"] = "cpu"
    os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")
    res = []
    with ProcessPoolExecutor(a.procs) as ex:
        for info in ex.map(run_layout, [(G, f, o, a.out, a.resets) for G, f, o in L]):
            res.append(info)
            print(f"{info['layout']:28s} ok={info['world_ok']} fires={info['fires_capped']} "
                  f"obs_width={info['observation_width']} ({info['seconds']:.0f}s)", flush=True)
    json.dump(dict(layouts=res, ranges=list(RANGES)), open(os.path.join(a.out, "layouts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
