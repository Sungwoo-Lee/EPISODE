"""Generate the pre-change rollout fixture for the five state-dependent body mechanics.

**What this fixture is for.** The body-mechanics plan
(`docs/develop/active/thermal/STATE_DEPENDENT_BODY_MECHANICS.md`) adds five mechanics
(B1 random start temperature, B2 warmth-dependent healing, B3 healing costs food, B4
injury speeds heat exchange, B5 nutrition-dependent healing), fifteen config keys, all
shipped at an "off" value. The claim to defend is that at the off values the environment
behaves exactly as the pre-change code did. This script records that pre-change
behaviour; `tests/env/test_body_mechanics_parity.py` holds HEAD to it with
`np.array_equal` and no tolerance, plus jaxpr-string equality.

**Worlds:** the maintained curriculum levels 05 (campfire, thermal on) and 04 (thermal
off), resolved through `load_env_config` -> `load_env_params` exactly as the trainer does.

**Episodes:** seeds 0..15, 300 steps each. A seed's stream auto-resets on `done`
(episode e resets with `fold_in(PRNGKey(seed), e)`), as training does. Deviation from the
plan's "up to 300 steps each": with random actions most level-04/05 episodes end within
~20 steps (random start injury up to 100), so a single episode per seed never ate and the
coverage gate below refused to write.

**Actions:** deterministic. Rest (4) when `(t // 20) % 3 == 2`; otherwise
`randint(fold_in(PRNGKey(1234), seed*1000 + t), 0, 6)`.

**Records per step:** every `EnvState` leaf (reset state included), `reward`, `done`,
every `info` entry, and `get_observation(state, params)`. Per world: the
`jax_step` / `jax_reset` / `update_body` jaxpr SHA-1s and the resolved config dict as
canonical YAML (so the test can name unrelated config drift instead of reporting an
unexplained mismatch).

**Refuses to write** unless each world has a rest step with healing, a rest step in a
bush with healing, a real death, and an eat event; level 05's body temperature must also
span at least 5 degrees. Counts are printed.

**The episode loop, action rule, seeds and step budget are duplicated in
`tests/env/test_body_mechanics_parity.py`** (it imports them from here). Change them here
only together with a regenerated fixture.

**It must be generated from code that predates the change**, or it proves nothing.
`--src-root` is REQUIRED (no default). Point it at a worktree of the pre-change tip:

    git worktree add --detach /tmp/gwp_bodymech_baseline <pre-change SHA>
    JAX_PLATFORMS=cpu /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \\
        scripts/fixtures/generate_body_mechanics_parity_fixture.py \\
        --src-root /tmp/gwp_bodymech_baseline
    git worktree remove /tmp/gwp_bodymech_baseline

`--src-root` supplies BOTH `src/` and `configs/` (the loader's `_CONFIGS_ROOT` follows
the imported module), so the captured worlds are entirely that commit's. Its SHA is
stamped as `_provenance_sha`. Output always goes to THIS checkout's `tests/env/fixtures/`.
"""
import os

# Backend pinning MUST precede any jax import (fixtures are compared on CPU).
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import argparse
import hashlib
import subprocess
import sys

import numpy as np
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

OUT_REL = os.path.join("tests", "env", "fixtures", "body_mechanics_parity",
                       "pre_change_rollouts.npz")

WORLDS = {
    "lvl05": os.path.join("configs", "environment", "experiment", "basic",
                          "05-campfire_thermal_10x10.yaml"),
    "lvl04": os.path.join("configs", "environment", "experiment", "basic",
                          "04-jump_attack_10x10.yaml"),
}
SEEDS = tuple(range(16))
MAX_T = 300
ACTION_KEY = 1234
REST = 4


def action_at(jax, seed, t):
    """The deterministic action rule shared with the test."""
    if (t // 20) % 3 == 2:
        return REST
    k = jax.random.fold_in(jax.random.PRNGKey(ACTION_KEY), seed * 1000 + t)
    return int(jax.random.randint(k, (), 0, 6))


def _leaf_name(path):
    import jax
    return jax.tree_util.keystr(path).lstrip(".")


def jaxpr_shas(jax, jnp, core, params, state):
    """SHA-1 of the jaxpr strings of jax_step, jax_reset and update_body with params TRACED.

    Params are passed as an argument (not closed over), so every pytree leaf of
    EnvParams is a jaxpr input: a new traced field would renumber the string. That is
    why every new body-mechanics field is static (plan §A1, reviewer M1).
    """
    act = jnp.asarray(REST, dtype=jnp.int32)
    step_jp = jax.make_jaxpr(lambda s, a, p: core.jax_step(s, a, p))(state, act, params)
    reset_jp = jax.make_jaxpr(lambda p, k: core.jax_reset(p, k))(
        params, jax.random.PRNGKey(0))
    info = {"ate_food": jnp.array(False), "damage": jnp.array(0.0, dtype=jnp.float32),
            "rested": jnp.array(True)}
    ub_jp = jax.make_jaxpr(lambda s, i, p, pos: core.update_body(s, i, p, pos))(
        state, info, params, state.agent_pos)

    def sha(x):
        return hashlib.sha1(str(x).encode("utf-8")).hexdigest()
    return {"jax_step": sha(step_jp), "jax_reset": sha(reset_jp), "update_body": sha(ub_jp)}


def rollout_world(jax, jnp, core, get_observation, params):
    """Roll the 16 seeds, MAX_T steps each, auto-resetting on `done`.

    Episode `e` of seed `s` resets with `fold_in(PRNGKey(s), e)` (episode 0 uses
    `PRNGKey(s)` itself). Returns {f"s{seed}.{field}": array}: `state.*` / `obs` are the
    POST-step state and observation (one row per step); `reset.*` / `reset_obs` are the
    reset states (one row per episode); `ep_start` is the step index each episode began at.
    """
    step = jax.jit(core.jax_step)
    reset = jax.jit(core.jax_reset)
    out = {}
    for seed in SEEDS:
        state = reset(params, jax.random.PRNGKey(seed))
        resets, reset_obs, ep_start = [state], [np.asarray(get_observation(state, params))], [0]
        states, obs, rewards, dones, infos = [], [], [], [], []
        for t in range(MAX_T):
            a = jnp.asarray(action_at(jax, seed, t), dtype=jnp.int32)
            state, r, d, info = step(state, a, params)
            states.append(state)
            obs.append(np.asarray(get_observation(state, params)))
            rewards.append(np.asarray(r))
            dones.append(np.asarray(d))
            infos.append({k: np.asarray(v) for k, v in info.items()})
            if bool(d) and t + 1 < MAX_T:
                state = reset(params, jax.random.fold_in(jax.random.PRNGKey(seed),
                                                         len(resets)))
                resets.append(state)
                reset_obs.append(np.asarray(get_observation(state, params)))
                ep_start.append(t + 1)
        for tag, seq in (("state", states), ("reset", resets)):
            flat = [jax.tree_util.tree_flatten_with_path(x)[0] for x in seq]
            for i, (path, _) in enumerate(flat[0]):
                out[f"s{seed}.{tag}.{_leaf_name(path)}"] = np.stack(
                    [np.asarray(f[i][1]) for f in flat])
        out[f"s{seed}.obs"] = np.stack(obs)
        out[f"s{seed}.reset_obs"] = np.stack(reset_obs)
        out[f"s{seed}.ep_start"] = np.asarray(ep_start, dtype=np.int32)
        out[f"s{seed}.reward"] = np.stack(rewards)
        out[f"s{seed}.done"] = np.stack(dones)
        for k in infos[0]:
            out[f"s{seed}.info.{k}"] = np.stack([inf[k] for inf in infos])
    return out


def coverage(arrays, params, world):
    """Counts the fixture must be non-zero on (shared with the test)."""
    c = {"heal_rest": 0, "heal_rest_bush": 0, "real_death": 0, "eat": 0}
    tmin, tmax = np.inf, -np.inf
    for seed in SEEDS:
        post = arrays[f"s{seed}.state.injury_level"].astype(np.float64)
        pre = np.concatenate([[0.0], post[:-1]])
        starts = arrays[f"s{seed}.ep_start"]
        pre[starts] = arrays[f"s{seed}.reset.injury_level"].astype(np.float64)
        rested = arrays[f"s{seed}.info.rested"].astype(bool)
        bush = arrays[f"s{seed}.info.agent_in_bush"].astype(bool)
        healed = post < pre
        c["heal_rest"] += int((rested & healed).sum())
        c["heal_rest_bush"] += int((rested & healed & bush).sum())
        reason = arrays[f"s{seed}.info.termination_reason"]
        c["real_death"] += int(np.isin(reason, [2, 3, 4, 5]).sum())
        c["episodes"] = c.get("episodes", 0) + len(starts)
        c["eat"] += int(arrays[f"s{seed}.info.ate_food"].astype(bool).sum())
        bt = arrays[f"s{seed}.state.body_temp"]
        tmin, tmax = min(tmin, float(bt.min())), max(tmax, float(bt.max()))
    c["body_temp_span"] = tmax - tmin
    return c


def check_coverage(c, world):
    for k in ("heal_rest", "heal_rest_bush", "real_death", "eat"):
        assert c[k] >= 1, f"{world}: coverage '{k}' is {c[k]} — fixture would be vacuous"
    if world == "lvl05":
        assert c["body_temp_span"] >= 5.0, (
            f"{world}: body temperature spans only {c['body_temp_span']:.2f} degrees")


def capture(src_root):
    sys.path.insert(0, src_root)
    import jax
    import jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    import src.environment.core as core
    from src.environment.sensor import get_observation
    assert os.path.abspath(core.__file__).startswith(src_root + os.sep), (
        f"src imported from {core.__file__}, not from --src-root {src_root}")

    arrays, counts = {}, {}
    for world, rel in WORLDS.items():
        cfg = load_env_config(os.path.join(src_root, rel))
        params = load_env_params(cfg)
        arrays[f"{world}._config_yaml"] = np.array(
            yaml.safe_dump(cfg.to_dict(), sort_keys=True, default_flow_style=False))
        w = rollout_world(jax, jnp, core, get_observation, params)
        c = coverage(w, params, world)
        check_coverage(c, world)
        counts[world] = c
        state0 = core.jax_reset(params, jax.random.PRNGKey(0))
        for fn, h in jaxpr_shas(jax, jnp, core, params, state0).items():
            arrays[f"{world}._jaxpr_sha.{fn}"] = np.array(h)
        for k, v in w.items():
            arrays[f"{world}.{k}"] = v
    return arrays, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-root", required=True,
                    help="Repo root to import src/ and read configs/ from: a worktree of "
                         "the pre-change tip. Required on purpose; the working tree is NOT "
                         "a valid reference.")
    args = ap.parse_args()
    src_root = os.path.abspath(args.src_root)
    sha = subprocess.check_output(["git", "-C", src_root, "rev-parse", "HEAD"],
                                  text=True).strip()
    dirty = subprocess.check_output(["git", "-C", src_root, "status", "--porcelain",
                                     "--", "src", "configs"], text=True).strip()
    if dirty:
        raise SystemExit(f"--src-root has uncommitted src/configs changes:\n{dirty}")

    arrays, counts = capture(src_root)
    out = os.path.join(_ROOT, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, _provenance_sha=np.array(sha), **arrays)
    print(f"wrote {out}")
    print(f"  source tree : {src_root}")
    print(f"  HEAD        : {sha}")
    for world, c in counts.items():
        print(f"  {world}: " + ", ".join(
            f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in c.items()))
        for fn in ("jax_step", "jax_reset", "update_body"):
            print(f"    jaxpr sha1 {fn:11s}: {arrays[f'{world}._jaxpr_sha.{fn}']}")


if __name__ == "__main__":
    main()
