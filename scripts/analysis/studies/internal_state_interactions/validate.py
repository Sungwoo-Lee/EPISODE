"""Validate bodysim.py against the REAL environment's update_body and calculate_drive.

The simulator is trusted only if, on thousands of random body states and actions, its next food
energy, injury, body temperature, death flag and drive equal what the environment computes (float32
tolerance). Run it against a chosen source tree:

  python validate.py --src-root <dir containing src/ and configs/> --world <config path in that tree>
                     --mechanics none|all --n 4000 --out <json>

`--src-root` lets the check run against a frozen copy of a commit (so a half-edited working tree can
never be what it compares against). `--mechanics all` switches B1-B5 on with non-trivial values in
BOTH the environment params and the simulator (only possible once the implementation has landed);
`none` checks today's rules. Exits non-zero on any mismatch.
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-root", required=True)
    ap.add_argument("--world", required=True)
    ap.add_argument("--mechanics", required=True, choices=["none", "all"])
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    sys.path.insert(0, os.path.abspath(a.src_root)); sys.path.insert(0, HERE)
    import jax, jax.numpy as jnp
    from src.environment.config_loader import load_env_config, load_env_params
    from src.environment import core
    import bodysim as B

    cfg = load_env_config(os.path.join(a.src_root, a.world))
    P_env = load_env_params(cfg)
    Psim = B.Body()
    if a.mechanics == "all":
        over = dict(thermal_healing_cold_sensitivity=0.08, thermal_healing_warm_sensitivity=0.04,
                    thermal_injury_heat_exchange_gain=1.0, thermal_injury_heat_exchange_mode="cooling_only",
                    healing_nutrition_cost=0.7, healing_nutrition_shortfall="partial",
                    healing_nutrition_dependence=True, healing_hunger_low=20.0, healing_hunger_high=100.0,
                    healing_hunger_floor=0.2, healing_overfull_floor=0.5, healing_overfull_start=150.0,
                    thermal_metabolic_coupling=True, thermal_metabolic_coupling_rate=1.0)
        missing = [k for k in over if not hasattr(P_env, k)]
        if missing:
            raise SystemExit(f"env params lack {missing}: the B1-B5 implementation has not landed in "
                             f"{a.src_root}; field names may differ -- check the implemented names")
        P_env = P_env.replace(**over)
        Psim = Psim.with_(heal_cold_s=0.08, heal_warm_s=0.04, inj_gain=1.0, inj_mode="cooling_only",
                          heal_cost=0.7, shortfall="partial", b5=True, b5_low=20.0, b5_high=100.0,
                          b5_floor=0.2, b5_over_floor=0.5, b5_over_start=150.0,
                          coupling=True, coupling_rate=1.0)

    # the constants the simulator hard-codes must be the world's own
    checks = dict(max_nutrition=float(P_env.max_nutrition), setpoint=float(P_env.setpoint),
                  metabolic_cost=float(P_env.metabolic_cost),
                  food_gain_net=float(P_env.food_nutrition_gain - P_env.eating_nutrition_cost),
                  max_injury=float(P_env.max_injury), recovery_base=float(P_env.recovery_base_rate),
                  bush_multiplier=float(P_env.recovery_in_bush_multiplier),
                  t_set=float(P_env.temperature_setpoint), t_min=float(P_env.min_temperature),
                  t_max=float(P_env.max_temperature), k_ex=float(P_env.thermal_k_exchange),
                  k_loss=float(P_env.thermal_k_loss), k_met=float(P_env.thermal_k_metabolic),
                  warm_scale=float(P_env.thermal_warming_rate_scale),
                  cool_scale=float(P_env.thermal_cooling_rate_scale), death_penalty=float(P_env.death_penalty))
    bad_const = {k: (v, getattr(Psim, k)) for k, v in checks.items() if abs(v - getattr(Psim, k)) > 1e-9}
    if bad_const:
        raise SystemExit(f"simulator constants differ from the world's: {bad_const}")
    if float(P_env.recovery_accel_rate) != 0.0 or float(P_env.nutrition_to_satiation_scaling_factor) != 1.0 \
            or float(P_env.max_satiation) != float(P_env.max_nutrition):
        raise SystemExit("world breaks a simulator assumption (accel 0, satiation == nutrition)")

    s0 = jax.jit(core.jax_reset)(P_env, jax.random.PRNGKey(0))
    hides = np.asarray(P_env.obs_hides_agent) & np.asarray(s0.obs_active)
    bush = np.asarray(s0.obs_pos)[np.flatnonzero(hides)[0]]
    occupied = {tuple(p) for p in np.asarray(s0.obs_pos)}
    open_cell = next((r, c) for r in range(1, 9) for c in range(1, 9) if (r, c) not in occupied)
    shape = s0.thermal_field.shape

    rng = np.random.default_rng(0); n = a.n
    N = rng.uniform(0, 200, n); I = rng.uniform(0, 100, n); T = rng.uniform(-15, 15, n)
    cell = np.where(rng.random(n) < 0.4, -30.0, np.where(rng.random(n) < 0.5, 8.5, rng.uniform(-35, 80, n)))
    act = rng.integers(0, 3, n)                      # 0 move/idle, 1 rest, 2 eat
    rested = act == 1; ate = act == 2; in_bush = rng.random(n) < 0.5
    # edge cases: near-starvation, near-overeating, near-freezing, full injury
    N[:200] = rng.uniform(0, 6, 200); N[200:300] = rng.uniform(194, 200, 100)
    T[300:400] = rng.uniform(-15, -13, 100); I[400:450] = 100.0

    def one(Ni, Ii, Ti, ci, ri, ai, bi):
        st = s0.replace(nutrition=jnp.float32(Ni), satiation=jnp.float32(Ni), injury_level=jnp.float32(Ii),
                        body_temp=jnp.float32(Ti), thermal_field=jnp.full(shape, ci, jnp.float32),
                        injury_buffer=jnp.zeros_like(s0.injury_buffer), rest_streak=jnp.int32(0))
        pos = jnp.where(bi, jnp.asarray(bush), jnp.asarray(open_cell))
        info = {"damage": jnp.float32(0.0), "ate_food": ai, "rested": ri}
        out = core.update_body(st, info, P_env, pos)
        sat, nut, inj, _buf, _hist, _streak, bt, _td, done = out[:9]
        drv = core.calculate_drive(sat, inj, P_env, bt)
        return nut, inj, bt, done, drv
    f = jax.jit(jax.vmap(one))
    nut, inj, bt, done, drv = [np.asarray(x) for x in f(
        jnp.asarray(N, jnp.float32), jnp.asarray(I, jnp.float32), jnp.asarray(T, jnp.float32),
        jnp.asarray(cell, jnp.float32), jnp.asarray(rested), jnp.asarray(ate), jnp.asarray(in_bush))]

    N32, I32, T32, c32 = (np.asarray(x, np.float32).astype(float) for x in (N, I, T, cell))
    s = B.step(N32, I32, T32, rested, ate, in_bush, c32, Psim)
    tol = 1e-3
    res = {"n": n, "mechanics": a.mechanics, "src_root": a.src_root, "world": a.world,
           "max_abs_diff": {"nutrition": float(np.abs(s["N"] - nut).max()), "injury": float(np.abs(s["I"] - inj).max()),
                            "body_temp": float(np.abs(s["T"] - bt).max()),
                            "drive": float(np.abs(B.drive(s["N"], s["I"], s["T"], Psim) - drv).max())},
           "death_flag_mismatches": int((s["dead"] != done).sum())}
    res["pass"] = all(v < tol for v in res["max_abs_diff"].values()) and res["death_flag_mismatches"] == 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
