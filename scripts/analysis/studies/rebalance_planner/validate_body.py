"""Check that the old study's body simulator (bodysim.py) still matches the real environment's
update_body when a bite is worth 16 food energy (the "+" food economy of the rebalance worlds).

Plain-language purpose: the rebalance planner reuses bodysim.py with a new food gain. This runs the old
study's own check (validate.check: thousands of random body states and actions, simulator vs
src/environment/core.update_body, float32 tolerance 1e-3, death flags must agree) on the lookalike
world's config with body.food_nutrition_gain set IN MEMORY (6 = today, 16 = new); no config file is
written. Then the same check on every lookalike_hf_* world config AS LOADED (no override); the
simulator's food gain is taken from the loaded config, and validate.check refuses to run if any
constant (food gain - eating cost included) differs, so a pass proves the gain took effect.

  python validate_body.py --out docs/experiments/active/rebalance_planner/figures/validation_body.json
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OLD = os.path.join(ROOT, "scripts/analysis/studies/internal_state_interactions")
WORLD = "configs/environment/experiment/basic/lookalike_animals_close_pounce_small_food_10x10.yaml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default=WORLD)
    ap.add_argument("--n", type=int, default=6000)
    a = ap.parse_args()
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    sys.path.insert(0, ROOT); sys.path.insert(0, OLD)
    import jax, jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment import core
    import bodysim as B
    import validate as V
    cfg = load_env_config(os.path.join(ROOT, a.world))
    P0 = load_env_params(cfg)
    eat_cost = float(P0.eating_nutrition_cost)
    res = []
    for gain in (6.0, 16.0):
        P = P0.replace(food_nutrition_gain=jnp.asarray(gain, dtype=jnp.asarray(P0.food_nutrition_gain).dtype))
        r = V.check(P, B.Body().with_(food_gain_net=gain - eat_cost), core, B, jax, jnp, a.n)
        r["food_nutrition_gain"] = gain
        res.append(r)
        print(gain, r["pass"], r["max_abs_diff"], r["death_flag_mismatches"], flush=True)
    import glob
    for f in sorted(glob.glob(os.path.join(ROOT, "configs/environment/experiment/basic/lookalike_hf_*.yaml"))):
        P = load_env_params(load_env_config(f))
        gain = float(P.food_nutrition_gain)
        r = V.check(P, B.Body().with_(food_gain_net=gain - float(P.eating_nutrition_cost)), core, B, jax, jnp, a.n)
        r.update(food_nutrition_gain=gain, world=os.path.relpath(f, ROOT))
        res.append(r)
        print(os.path.basename(f), gain, r["pass"], r["death_flag_mismatches"], flush=True)
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = dict(world=a.world, n=a.n, src="working tree", head=commit, eating_nutrition_cost=eat_cost, sets=res,
               pass_=all(r["pass"] for r in res))
    json.dump(out, open(a.out, "w"), indent=1)
    sys.exit(0 if out["pass_"] else 1)


if __name__ == "__main__":
    main()
