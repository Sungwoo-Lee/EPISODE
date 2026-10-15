#!/usr/bin/env python3
"""unit_inventory.py - count every value the network computes per step, per layer, for the two agents of the
level-05 lookalike half-factorial (ordinary t1none, modulated t16quad), from a trained run's own saved config and
checkpoint. Writes the inventory the Neural Recording Pipeline page prints (no number typed by hand).

    $P scripts/analysis/studies/neural_pipeline/unit_inventory.py --out docs/experiments/active/neural_analysis/unit_inventory.json
"""
import argparse
import glob
import json
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)


def leaves(tree):
    import jax
    return [x for x in jax.tree_util.tree_leaves(tree) if hasattr(x, "shape")]


def main():
    import jax.numpy as jnp
    import numpy as np
    from scripts.analysis.nmn import replay
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="2")
    a = ap.parse_args()
    inv = {}
    for agent, tag in (("ordinary", "t1none"), ("modulated", "t16quad")):
        run = sorted(glob.glob(os.path.join(ROOT, "results/JAX_RecurrentPPO",
                                            f"*_rppo_lookalike_hf_l05_w{a.world}_{tag}_s42")))[0]
        ag = replay.load_agent(os.path.join(run, "models"))
        obs_dim = int(sum(ag.obs_breakdown.values()))
        h = ag.model.initial_state(batch_size=1)
        out = ag.model.forward_with_activations(jnp.zeros((1, obs_dim)), h)
        mod_info, acts = out[3], out[4]
        rows = [{"key": k, "shape": list(v.shape[1:]), "n": int(np.prod(v.shape[1:]))} for k, v in acts.items()]
        # recurrent carries from the initial state: (task GRU,) or (task GRU, modulator GRU)
        carry = [int(np.prod(x.shape[1:])) for x in leaves(h)]
        mod = []
        if mod_info is not None:
            for f in mod_info._fields if hasattr(mod_info, "_fields") else vars(mod_info):
                v = getattr(mod_info, f)
                if v is not None and hasattr(v, "shape"):
                    mod.append({"key": f"film.{f}", "shape": list(v.shape[1:]), "n": int(np.prod(v.shape[1:]))})
        inv[agent] = {"run": os.path.relpath(run, ROOT), "checkpoint": ag.step, "obs_dim": obs_dim,
                      "obs_groups": ag.obs_breakdown, "action_dim": ag.action_dim, "acts": rows, "film": mod,
                      "carry_sizes": carry}
    with open(a.out, "w") as f:
        json.dump(inv, f, indent=1)
    for agent, d in inv.items():
        tot = sum(r["n"] for r in d["acts"]) + sum(r["n"] for r in d["film"])
        print(agent, "values per step:", tot, "carry:", d["carry_sizes"])


if __name__ == "__main__":
    main()
