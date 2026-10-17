#!/usr/bin/env python3
"""make_random_layout_scenes.py - random-layout test scenes and sweep specs for Figure 5 of the
"Predator, Food and Hazard Settings Screen" page (half-factorial study).

Design: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md, section
"Figure 5 re-collection: a new layout every episode, sampled and greedy actions". User decisions:
tmp/20261018_005228_figure5_dashboard_decisions.md (2026-10-18).

The old Figure 5 tested every agent in world 1's frozen scenes: one fixed layout, greedy actions,
30 episodes. The new scenes keep every frozen-scene setting EXCEPT the layout, which the
environment draws anew each episode as in training (random_start_pos true; every obstacle `area`,
entity `spawn_area` and resource `spawn_area` = the whole 10x10 grid), and they are written once
per action rule (behavior_measures.eval_policy_mode stochastic = sampled, deterministic = greedy)
with behavior_measures.eval_n_episodes 100.

    scenes   write the 8 scene sets (healing on/off x food/no food x sampled/greedy), 24 scenes each
             (no animal, wandering rabbit, chasing rabbit, predator x starting injury 0-70)
    specs    write one dwell-sweep spec per scene set listing every FINISHED run; re-run it after
             more runs finish: new runs are added, already-tested ones are skipped by the sweep's
             incremental rule

Every generated scene is a fully resolved, standalone YAML (no `extends:`), round-trip checked
through src.environment.config_loader.load_env_config. Checks that stop the script:
  * each food-free frozen scene equals its food scene with `environment.resources` emptied, and
    nothing else (existing food-free sources are checked; missing ones are derived that way);
  * each healing-on frozen scene differs from its healing-off twin only in
    body.recovery_base_rate (> 0 on, 0.0 off);
  * each random-layout scene differs from its frozen source only in the layout keys and the two
    behavior_measures keys set here;
  * every scene of a set has the same observation layout and action count (one eval_rollout
    --config-list process runs all 24 per checkpoint and refuses a mismatch at run time).
"""
from __future__ import annotations

import argparse
import copy
import glob
import os
import re
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from src.environment.config_loader import load_env_config, load_env_params  # noqa: E402
from src.environment.sensor import get_observation_breakdown  # noqa: E402

BP = "configs/environment/experiment/behavior_probes"
OUT_SCENES = f"{BP}/random_layout"
OUT_SPECS = "configs/eval_sweeps/lookalike_hf_random_layout"
OUT_RESULTS = "results/eval/avoidance/metrics_history_rppo_lookalike_hf_random_layout"
FULL = [[1, 1], [10, 10]]
ANIMALS = ("none", "rabbitwander", "rabbit", "pred")   # rabbit = the chasing rabbit
INJURIES = ("00", "10", "20", "30", "50", "70")
HEAL = ("on", "off")
FOOD = ("food", "nofood")
ACTION = {"sampled": "stochastic", "greedy": "deterministic"}
EPISODES = 100
MAX_CHECKPOINTS = 20
NODES = [101, 103, 104, 105]
NPAR = 26   # 34-36 cores per node; a warm 24-scene line uses ~1.3 cores (measured 2026-10-18), 1.5 GB
LAYOUT_KEYS = {"environment.random_start_pos"}   # plus the *.area / *.spawn_area paths below


def set_name(heal, food, action):
    return f"heal{heal}_{food}_{action}"


# ----------------------------------------------------------------------------------- sources
def frozen_source(heal, food, animal, inj):
    """Repo-relative path of the existing frozen scene, or None when it does not exist."""
    grid = "injury_grid__chase_neutral_clean" if animal == "rabbit" else "injury_grid__neutral_clean"
    stem = f"avoid_{animal}_inj{inj}.yaml"
    if food == "food":
        p = f"{BP}/lookalike/{grid}/{stem}" if heal == "on" else f"{BP}/no_healing/lookalike__{grid}/{stem}"
    elif animal == "rabbit":   # food-free chasing rabbit: healing-off copy exists for injury 0-30 only
        p = f"{BP}/level_ladder/lookalike_nofood_chase__noheal/{stem}" if heal == "off" else None
    else:
        p = (f"{BP}/lookalike_nofood/injury_grid__neutral_clean/{stem}" if heal == "on"
             else f"{BP}/no_healing/lookalike_nofood__injury_grid__neutral_clean/{stem}")
    return p if p and os.path.exists(os.path.join(ROOT, p)) else None


def resolved(rel):
    return load_env_config(os.path.join(ROOT, rel)).to_dict()


def diff_paths(a, b, path=""):
    """Leaf paths where two nested dict/list trees differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            p = f"{path}.{k}" if path else str(k)
            if k not in a or k not in b:
                out.append(p)
            else:
                out += diff_paths(a[k], b[k], p)
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_paths(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [path]


def frozen_quad(animal, inj):
    """The four frozen scenes (healing x food) of one animal x injury, with where each came from."""
    q, where = {}, {}
    for heal in HEAL:
        src = frozen_source(heal, "food", animal, inj)
        if src is None:
            raise SystemExit(f"missing frozen food scene: healing {heal}, {animal}, injury {inj}")
        q[(heal, "food")], where[(heal, "food")] = resolved(src), src
    for heal in HEAL:
        food_v = q[(heal, "food")]
        expect = copy.deepcopy(food_v)
        expect["environment"]["resources"] = []
        src = frozen_source(heal, "nofood", animal, inj)
        if src is None:   # derived: the food scene with its resources emptied, nothing else
            q[(heal, "nofood")], where[(heal, "nofood")] = expect, f"{where[(heal, 'food')]} with resources emptied"
            continue
        v = resolved(src)
        d = diff_paths(expect, v)
        if d:
            raise SystemExit(f"{src}: differs from its food scene {where[(heal, 'food')]} in more than "
                             f"the food: {d}")
        q[(heal, "nofood")], where[(heal, "nofood")] = v, src
    for food in FOOD:
        on, off = q[("on", food)], q[("off", food)]
        d = diff_paths(on, off)
        if d != ["body.recovery_base_rate"]:
            raise SystemExit(f"{animal} injury {inj} {food}: healing-on and healing-off scenes differ in {d}, "
                             "expected only body.recovery_base_rate")
        if not (float(on["body"]["recovery_base_rate"]) > 0.0 and float(off["body"]["recovery_base_rate"]) == 0.0):
            raise SystemExit(f"{animal} injury {inj} {food}: recovery_base_rate on={on['body']['recovery_base_rate']} "
                             f"off={off['body']['recovery_base_rate']}")
    return q, where


def randomise(frozen, mode):
    v = copy.deepcopy(frozen)
    e = v["environment"]
    e["random_start_pos"] = True
    for o in e["obstacles"]:
        o["area"] = copy.deepcopy(FULL)
    for ent in e.get("entities") or []:
        ent["spawn_area"] = copy.deepcopy(FULL)
    for r in e["resources"]:
        r["spawn_area"] = copy.deepcopy(FULL)
    v["behavior_measures"]["eval_n_episodes"] = EPISODES
    v["behavior_measures"]["eval_policy_mode"] = mode
    allowed = LAYOUT_KEYS | {"behavior_measures.eval_n_episodes", "behavior_measures.eval_policy_mode"}
    for p in diff_paths(frozen, v):
        layout = re.fullmatch(r"environment\.(obstacles\[\d+\]\.area|(entities|resources)\[\d+\]\.spawn_area)"
                              r"(\[\d+\])*", p) is not None
        if not (layout or p in allowed):
            raise SystemExit(f"randomise changed {p}, which is not a layout key")
    return v


class _NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def cmd_scenes(_args):
    n = 0
    shapes = {}
    for animal in ANIMALS:
        for inj in INJURIES:
            q, where = frozen_quad(animal, inj)
            for heal in HEAL:
                for food in FOOD:
                    for action, mode in ACTION.items():
                        sname = set_name(heal, food, action)
                        v = randomise(q[(heal, food)], mode)
                        d = os.path.join(ROOT, OUT_SCENES, sname)
                        os.makedirs(d, exist_ok=True)
                        p = os.path.join(d, f"avoid_{animal}_inj{inj}.yaml")
                        with open(p, "w") as fh:
                            fh.write(
                                "# GENERATED by scripts/analysis/studies/half_factorial_l05/make_random_layout_scenes.py"
                                " -- do not edit; re-run the script.\n"
                                f"# Frozen source: {where[(heal, food)]}\n"
                                "# Fully resolved (no extends). Changes from the source: a new layout every episode"
                                " (random_start_pos true; every obstacle area, animal and food spawn_area = whole grid),\n"
                                f"# behavior_measures.eval_policy_mode {mode} ({action} actions), eval_n_episodes {EPISODES}.\n"
                                "# Design: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md (Figure 5 re-collection).\n")
                            yaml.dump(v, fh, Dumper=_NoAlias, sort_keys=False)
                        cfg = load_env_config(p)
                        if cfg.to_dict() != v:
                            raise SystemExit(f"{p}: round trip through load_env_config changed the scene")
                        prm = load_env_params(cfg)
                        shape = (tuple(sorted(get_observation_breakdown(prm).items())),
                                 4 + int(prm.rest_action_enabled) + int(prm.eat_action_enabled))
                        shapes.setdefault(sname, set()).add(shape)
                        n += 1
    for sname, s in shapes.items():
        if len(s) != 1:
            raise SystemExit(f"{sname}: scenes have {len(s)} different observation/action layouts")
    print(f"wrote {n} scenes in {len(shapes)} sets under {OUT_SCENES}/ "
          "(food-free = food minus resources; healing on/off differ only in recovery_base_rate; "
          "one observation layout per set)")


# ------------------------------------------------------------------------------------- runs
TRAIN = "results/JAX_RecurrentPPO"
AGENT_TAG = {"ordinary": "t1none", "modulated": "t16quad"}
FINAL = 9_990_000   # data.py's "finished" rule: newest checkpoint >= 9.99 M steps


def identities():
    """(sort key, label stem, training tag) for every training identity the page can use."""
    out = []
    for agent, t in AGENT_TAG.items():
        for seed in range(42, 50):
            out.append(((0, agent, seed), f"l05ref_{agent}_s{seed}", f"rppo_healrep_l05_{t}_s{seed}"))
            out.append(((1, agent, seed), f"lookalike_{agent}_s{seed}", f"rppo_lookalike_l05_{t}_s{seed}"))
            for w in range(2, 17):
                out.append(((w, agent, seed), f"hf_w{w}_{agent}_s{seed}", f"rppo_lookalike_hf_l05_w{w}_{t}_s{seed}"))
    return sorted(out)


def checkpoints(folder):
    md = os.path.join(ROOT, folder, "models")
    return sorted(int(c) for c in os.listdir(md) if c.isdigit()) if os.path.isdir(md) else []


def finished_runs():
    """[(label, folder)] of every finished identity, restricted to the folders that hold its
    newest MAX_CHECKPOINTS checkpoints. Folder k of an identity (oldest first, counting empty
    folders) is labelled <stem>, <stem>_resumed, <stem>_resumed2, ... as in the existing specs."""
    runs, skipped = [], []
    for _key, stem, tag in identities():
        folders = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, TRAIN, f"*_{tag}"))
                         if os.path.basename(p).split("_", 1)[1] == tag)
        if not folders:
            continue
        cks = {f: checkpoints(f) for f in folders}
        newest = max((c for f in folders for c in cks[f]), default=0)
        logs = glob.glob(os.path.join(ROOT, "logs", f"*_{tag}.log"))
        log_ok = (not logs) or any("Training complete" in open(lg, errors="ignore").read()[-20000:] for lg in logs)
        if newest < FINAL or not log_ok:
            skipped.append(f"{stem} (newest checkpoint {newest}, log complete: {log_ok})")
            continue
        top = set(sorted(c for f in folders for c in cks[f])[-MAX_CHECKPOINTS:])
        for k, f in enumerate(folders):
            if top & set(cks[f]):
                lab = stem if k == 0 else f"{stem}_resumed" + ("" if k == 1 else str(k))
                runs.append((lab, f))
    return runs, skipped


def cmd_specs(_args):
    runs, skipped = finished_runs()
    os.makedirs(os.path.join(ROOT, OUT_SPECS), exist_ok=True)
    for heal in HEAL:
        for food in FOOD:
            for action in ACTION:
                sname = set_name(heal, food, action)
                scene_dir = os.path.join(ROOT, OUT_SCENES, sname)
                if len(glob.glob(os.path.join(scene_dir, "avoid_*.yaml"))) != len(ANIMALS) * len(INJURIES):
                    raise SystemExit(f"{scene_dir}: run `scenes` first")
                spec = {
                    "name": f"lookalike_hf_random_layout_{sname}",
                    "algo": "rppo",
                    "output_dir": f"{OUT_RESULTS}/{sname}",
                    "probe": f"{OUT_SCENES}/{sname}",
                    "conditions": "all",
                    "episodes": EPISODES,
                    "max_checkpoints": MAX_CHECKPOINTS,
                    "nodes": NODES,
                    "npar": NPAR,
                    "x_axis": "steps",
                    "plot_measures": ["bush_hiding", "survival_steps"],
                    "runs": [{"label": lab, "path": f} for lab, f in runs],
                }
                p = os.path.join(ROOT, OUT_SPECS, f"lookalike_hf_random_layout_{sname}_rppo.yaml")
                with open(p, "w") as fh:
                    fh.write(
                        "# GENERATED by scripts/analysis/studies/half_factorial_l05/make_random_layout_scenes.py specs"
                        " -- do not edit; re-run it after more runs finish\n"
                        "# (newly finished runs are added; the sweep's incremental rule skips runs already tested).\n"
                        f"# Figure 5 re-collection, scene set {sname}: healing {heal}, {food.replace('nofood', 'no food')}, "
                        f"{action} actions, a new layout every episode, {EPISODES} episodes x newest {MAX_CHECKPOINTS} checkpoints.\n"
                        "# Runs: every FINISHED run (newest checkpoint >= 9.99 M and, where a log exists, 'Training complete'),\n"
                        "# only the result folders holding its newest 20 checkpoints; <label>_resumed<k> = later session folders.\n"
                        "# Design: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md (Figure 5 re-collection).\n")
                    yaml.safe_dump(spec, fh, sort_keys=False)
    print(f"wrote 8 specs under {OUT_SPECS}/ with {len(runs)} run folders "
          f"({len({lab.split('_resumed')[0] for lab, _ in runs})} finished runs)")
    for s in skipped:
        print("  not finished, left out:", s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scenes").set_defaults(fn=cmd_scenes)
    sub.add_parser("specs").set_defaults(fn=cmd_specs)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
