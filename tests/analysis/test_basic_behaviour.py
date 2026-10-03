"""Fast tests for scripts/analysis/basic_behaviour/ (no trajectory-store shard reads).

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), File Changes,
`tests/analysis/test_basic_behaviour.py`. Reads saved run configs and store manifests only.
Run locally: pytest is absent on the lab nodes.
"""
from __future__ import annotations

import copy
import glob
import json
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BB = os.path.join(ROOT, "scripts", "analysis", "basic_behaviour")
sys.path.insert(0, BB)
import registry as REG                                                  # noqa: E402
import fit as FT                                                        # noqa: E402
import screen as SC                                                     # noqa: E402

RUNS = {"a01": ("results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106", "results/trajectories"),
        "hv1ch": ("results/JAX_RecurrentPPO/20261001-002402_rppo_hv1ch_t1none_s42", "results/trajectories_hvsmell"),
        "hv1chm": ("results/JAX_RecurrentPPO/20261001-002455_rppo_hv1chm_t1none_s42", "results/trajectories_hvsmell"),
        "hv2ch": ("results/JAX_RecurrentPPO/20261001-002435_rppo_hv2ch_t1none_s43", "results/trajectories_hvsmell"),
        # thirst task (BASIC_BEHAVIOUR_WATER): a 10x10 and a 20x20 world with water
        "g10sW": ("results/JAX_RecurrentPPO/20261002_012801_rppo_thirst_g10sW_t1none_s42",
                  "results/trajectories_thirst_task"),
        "g20sW": ("results/JAX_RecurrentPPO/20261002_012738_rppo_thirst_g20sW_t1none_s42",
                  "results/trajectories_thirst_task")}
LEGACY_A01 = ["start_injury", "start_nutrition", "n_predators", "n_rabbits", "n_bushes", "n_rocks",
              "n_food", "n_ambush_predators", "spawn_dist_to_bush", "pred_detection_range",
              "pred_attack_delay", "pred_attack_range", "pred_max_stamina", "pred_smell_predatorness",
              "spawn_dist_to_predator", "pred_olf_intensity", "rab_smell_predatorness",
              "rab_olf_intensity"] + REG.CONSEQUENCES


def load(world):
    run, root = RUNS[world]
    p = os.path.join(REG.DATA_ROOT, run, "models", "config.yaml")      # $BB_DATA_ROOT in a worktree
    if not os.path.exists(p):
        pytest.skip(f"{p} not present")
    cfg = yaml.safe_load(open(p))
    man = json.load(open(glob.glob(os.path.join(REG.DATA_ROOT, root, os.path.basename(run), "*", "*",
                                                "_manifest.json"))[0]))
    return cfg, man


def describe(cfg, man):
    params = REG.rebuild_params(cfg) if (cfg.get("thermal") or {}).get("enabled") else None
    obs = REG.obs_indices(cfg, man, params)
    thermo = REG.thermal_info(cfg, params) if params is not None else None
    cols = ["agent_in_bush", "ate_food", "obs_true"]
    T = REG.targets(cfg, man, cols, obs, thermo)
    F = REG.factors(cfg, man, obs, thermo)
    REG.add_thermal_consequence(F, T["warm_cell"]["available"])
    return obs, thermo, T, F


# ------------------------------------------------------------------------------- registry ----
def test_registry_a01_legacy_names_and_order():
    cfg, man = load("a01")
    _, _, _, F = describe(cfg, man)
    assert [f["name"] for f in F] == LEGACY_A01


def test_registry_hv_campfire_is_own_factor():
    cfg, man = load("hv1ch")
    _, _, _, F = describe(cfg, man)
    names = [f["name"] for f in F]
    assert "n_campfire" in names and "n_rocks" in names
    S = REG.slots(cfg, man)
    rock = next(o for o in S["obstacles"] if o["name"] == "rock")
    fire = next(o for o in S["obstacles"] if o["name"] == "campfire")
    assert set(rock["slots"]).isdisjoint(fire["slots"])
    assert all(man["obstacle_names"][i] == "rock" for i in rock["slots"])


def test_slot_cross_check_wrong_map_fails():
    cfg, man = load("hv1ch")
    REG.slots(cfg, man)                                   # the true map passes
    bad = copy.deepcopy(man)
    bad["obstacle_names"] = ["rock"] * 3 + bad["obstacle_names"][3:]
    with pytest.raises(SystemExit):
        REG.slots(cfg, bad)


def test_audit_flags_unknown_draw():
    cfg, man = load("a01")
    _, _, _, F = describe(cfg, man)
    assert REG.unhandled(REG.audit(cfg, F, None)) == []
    c2 = copy.deepcopy(cfg)
    c2["body"]["random_start_hydration"] = True
    u = REG.unhandled(REG.audit(c2, F, None))
    assert [r["path"] for r in u] == ["body.random_start_hydration"]
    c2.setdefault("thermal", {})["use_random_spots"] = True
    u = REG.unhandled(REG.audit(c2, F, None))
    assert {r["path"] for r in u} == {"body.random_start_hydration", "thermal.use_random_spots"}
    # hv1ch: thermal.default_temp is claimed by handler 6b (Revision 2, N7 iii)
    cfg, man = load("hv1ch")
    obs, thermo, T, F = describe(cfg, man)
    assert REG.unhandled(REG.audit(cfg, F, thermo)) == []
    c3 = copy.deepcopy(cfg)
    c3["thermal"]["use_random_spots"] = True
    p3 = REG.rebuild_params(c3)
    th3 = REG.thermal_info(c3, p3)
    F3 = REG.factors(c3, man, obs, th3)
    assert "ambient_temp" not in [f["name"] for f in F3]
    u = {r["path"] for r in REG.unhandled(REG.audit(c3, F3, th3))}
    assert u == {"thermal.default_temp", "thermal.use_random_spots"}


def test_warm_target_unavailable_with_injury_gain():
    cfg, man = load("hv1ch")
    obs, thermo, T, _ = describe(cfg, man)
    assert T["warm_cell"]["available"]
    c2 = copy.deepcopy(cfg)
    c2["thermal"]["injury_heat_exchange_gain"] = 0.5
    T2 = REG.targets(c2, man, ["agent_in_bush", "ate_food", "obs_true"], obs, thermo)
    assert not T2["warm_cell"]["available"]
    assert "injury_heat_exchange_gain" in T2["warm_cell"]["reason"]


def test_obs_index_is_not_alphabetical():
    cfg, man = load("hv1ch")
    obs, _, _, _ = describe(cfg, man)
    assert obs["body_temp"] != obs["alphabetical_body_temp"]


def test_ambient_recovery_formula():
    """A field built with the environment's own blur from one baseline and two fires: the baseline is
    recovered at every square from B (Revision 2, N2)."""
    import jax.numpy as jnp
    from src.environment.core import _gaussian_smooth_normalised
    H, W, sigma, rad, ratio, base = 10, 10, 0.7, 3, 11.0, -30.37
    raw = np.full((H, W), base, np.float32)
    fires = [(2, 3), (7, 8)]
    for r, c in fires:
        raw[r, c] += ratio * abs(base)
    field = np.asarray(_gaussian_smooth_normalised(jnp.asarray(raw), sigma, rad), np.float64)
    Kr, wr = REG.blur_weights(sigma, rad, H)
    Kc, wc = REG.blur_weights(sigma, rad, W)
    for r in range(H):
        for c in range(W):
            B = sum(Kr[r, fr] * Kc[c, fc] for fr, fc in fires) / (wr[r] * wc[c])
            den = 1.0 - ratio * B
            if abs(den) > 0.05:
                assert abs(field[r, c] / den - base) < 1e-3, (r, c, field[r, c] / den)


# --------------------------------------------------------------------------------- prefit ----
class FakeCell:
    def __init__(self, arrays, factors, n, targets=("eating",)):
        self.arrs = arrays
        self.inv = {"factors": factors, "n_episodes": n,
                    "targets": {t: {"available": True} for t in targets}}
        self.n = n
        self.label = "fake"

    def a(self, k):
        return self.arrs[k]

    def factor(self, name):
        return self.arrs[f"f__{name}"]


def test_prefit_duplicate_constant_outcome():
    rng = np.random.default_rng(0)
    n = 5000
    stat = rng.normal(size=n)
    arrays = {"f__start_injury": rng.uniform(0, 100, n), "f__pred_smell_predatorness": stat,
              "f__pred_olf_intensity": stat.copy(), "f__n_food": np.full(n, 2.0),
              "f__eat_rate": rng.uniform(0, 1, n), "cnt__pred": np.ones(n)}
    F = [dict(name="start_injury", block="exogenous", role="episode", subset="all"),
         dict(name="pred_smell_predatorness", block="exogenous", role="class_trait:pred", subset="one:pred"),
         dict(name="pred_olf_intensity", block="exogenous", role="class_trait:pred", subset="one:pred"),
         dict(name="n_food", block="exogenous", role="episode", subset="all"),
         dict(name="eat_rate", block="consequence", role="consequence", subset="all")]
    pf = FT.prefit(FakeCell(arrays, F, n), "eating")
    exc = {e["name"]: e["reason"] for e in pf["excluded"]}
    assert exc == {"pred_olf_intensity": "identical to pred_smell_predatorness",
                   "n_food": "constant (= 2) in this run",
                   "eat_rate": "is (part of) the outcome being modelled"}
    assert [f["name"] for f in pf["included"]] == ["start_injury", "pred_smell_predatorness"]


def test_prefit_demotes_non_finite_episode_factor():
    n = 4000
    v = np.linspace(-31, -29, n)
    v[5] = np.nan
    arrays = {"f__ambient_temp": v}
    F = [dict(name="ambient_temp", block="exogenous", role="episode", subset="all")]
    pf = FT.prefit(FakeCell(arrays, F, n), "bush_dwell")
    assert pf["included"][0]["role"] == "episode_univariate_only"
    assert pf["demoted"] and pf["demoted"][0]["name"] == "ambient_temp"


# --------------------------------------------------------------------------------- screen ----
def runs_grid(worlds=("w0", "w1", "w2"), agents=("a0", "a1"), seeds=(42, 43, 44)):
    return [{"world": w, "agent": a, "seed": s} for a in agents for w in worlds for s in seeds]


def test_screen_stage2_on_known_values():
    runs = runs_grid()
    mean = {("w0", "a0"): 1.0, ("w1", "a0"): 2.0, ("w2", "a0"): 3.0,
            ("w0", "a1"): 1.5, ("w1", "a1"): 2.5, ("w2", "a1"): 3.5}
    off = {42: -0.1, 43: 0.0, 44: 0.1}
    v = np.array([mean[(r["world"], r["agent"])] + off[r["seed"]] for r in runs])
    res = SC.stage2(runs, v, "w0", "a0", se_episode=np.full(len(v), 0.01))
    assert res["df"] == 12
    s = np.sqrt(6 * 0.02 / 12)
    assert abs(res["s"] - s) < 1e-12
    for c in res["cells"]:
        assert abs(c["mean"] - mean[(c["world"], c["agent"])]) < 1e-12
    k = next(x for x in res["contrasts"] if x["contrast"] == "w1 - w0 | a0")
    assert abs(k["estimate"] - 1.0) < 1e-12
    assert abs(k["t"] - 1.0 / (s * np.sqrt(2 / 3))) < 1e-9 and k["df"] == 12
    # a pure world effect -> the world share is about 1
    vw = np.array([{"w0": 0.0, "w1": 5.0, "w2": 10.0}[r["world"]] + 0.01 * off[r["seed"]] for r in runs])
    vc = {x["component"]: x for x in SC.variance_components(runs, vw)["rows"]}
    assert vc["world"]["share_mom"] > 0.99
    perm = SC.permutation(runs, np.random.default_rng(3).normal(size=len(runs)))
    un = [p for p in perm if p["kind"] == "unrestricted"]
    ws = [p for p in perm if p["kind"] == "within seed"]
    assert [p["n_relabelings"] for p in un] == [1680, 1680]
    assert [p["n_distinct_groupings"] for p in un] == [280, 280]
    assert [p["n_distinct_F"] for p in un] == [280, 280]          # distinct data: no ties
    assert [p["n_relabelings"] for p in ws] == [216, 216]
    assert [p["n_distinct_groupings"] for p in ws] == [36, 36]
    assert abs(ws[0]["smallest_possible_p"] - 1 / 36) < 1e-12


def test_screen_variance_shares_near_zero_under_pure_noise():
    """Revision 2, N1: method-of-moments shares average about 0 under pure seed noise, while raw
    sum-of-squares shares average df_f / df_total."""
    rng = np.random.default_rng(1)
    runs = runs_grid()
    mom, raw = {}, {}
    for _ in range(3000):
        rows = SC.variance_components(runs, rng.normal(size=len(runs)))["rows"]
        for r in rows:
            mom.setdefault(r["component"], []).append(r["share_mom_untruncated"])
            raw.setdefault(r["component"], []).append(r["share_raw_ss"])
    for comp in ("world", "agent", "world x agent", "shared starting weights (seed within agent)"):
        assert abs(np.mean(mom[comp])) < 0.03, (comp, np.mean(mom[comp]))
    ref = {r["component"]: r["pure_noise_reference"] for r in rows}
    assert abs(np.mean(raw["shared starting weights (seed within agent)"]) - 4 / 17) < 0.02
    assert abs(ref["shared starting weights (seed within agent)"] - 4 / 17) < 1e-12


def test_screen_uses_seed_variation():
    runs = runs_grid()
    v = np.array([1.0 if r["seed"] in (42, 43) else -1.0 for r in runs])
    res = SC.stage2(runs, v, "w0", "a0", se_episode=np.full(len(v), 0.001))
    for c in res["cells"]:
        assert c["se_run"] > 50 * c["se_conditional_on_these_runs"]
    assert all(k["p"] > 0.5 for k in res["contrasts"])


def test_screen_refuses_unreplicated_cell():
    runs = runs_grid(seeds=(42,))
    with pytest.raises(SystemExit, match="fewer than 2"):
        SC.stage2(runs, np.zeros(len(runs)), "w0", "a0")
    runs = runs_grid(worlds=("w0", "w1"), agents=("a0", "a1"), seeds=(1, 2))
    D = SC.design(runs)
    assert D["df"] == 8 - 4 and D["refuse"] is None
    perm = SC.permutation(runs, np.arange(8.0))
    assert perm[0]["n_relabelings"] == 6 and [p for p in perm if p["kind"] == "within seed"][0]["n_relabelings"] == 4


def test_screen_smell_terms_carry_no_test():
    runs = runs_grid()
    res = SC.stage2(runs, np.arange(len(runs), dtype=float), "w0", "a0", smell=True)
    assert res["contrasts"] == []
    assert all(np.isnan(c["ci_lo"]) for c in res["cells"])


def test_control_smell_reading():
    out = {}
    for w in ("hv2ch", "hv1ch", "hv1chm"):
        cfg, _ = load(w)
        spec = REG.ENV.scent_spec(cfg).as_dict()
        n = 10
        x = {f"smellch__rabbit__{c}": np.linspace(0, 1, n) + c for c in range(5)}
        x["rab_smell_llr"] = np.full(n, 7.0)
        cell = FakeCell(x, [], n)
        out[w] = (spec, SC.smell_regressors(cell, spec["layout"], spec, "rabbit"))
    spec, r = out["hv2ch"]
    assert spec["layout"] == "difference" and tuple(spec["channels"]) == (1, 2)
    assert np.allclose(r["smell"], (np.linspace(0, 1, 10) + 1 - 0.6) * (0.2 / 0.09))
    assert np.allclose(r["smell_ch2_cov"], np.linspace(0, 1, 10) + 2)
    assert np.allclose(r["smell_plain"], 7.0)
    for w in ("hv1ch", "hv1chm"):
        spec, r = out[w]
        assert set(r) == {"smell"} and np.allclose(r["smell"], 7.0)


# ---------------------------------------------------------------------------------- build ----
def test_build_partial_and_broken(tmp_path):
    import build_page as BP
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pop = tmp_path / "population.json"
    pop.write_text(json.dumps({"population": "test", "cells": []}))
    out_root = tmp_path / "out"
    out_root.mkdir()
    page = tmp_path / "page"
    figs = page / "figures"
    figs.mkdir(parents=True)
    fig, ax = plt.subplots(figsize=(2, 1))
    ax.plot([0, 1], [0, 1])
    for ext in ("png", "svg", "pdf"):
        fig.savefig(figs / f"f1_behaviours_survival.{ext}")
    (figs / "f1_behaviours_survival.samples.json").write_text(json.dumps(
        [{"what": "episodes", "used": 5, "total": 10, "pct": 50.0, "note": "test"}]))
    present, pending = BP.build(str(pop), str(out_root), str(page))
    assert present == ["f1_behaviours_survival"] and pending == ["F2", "F3", "F4", "F5", "F6", "F7"]
    html_text = (page / "basic_behaviour.html").read_text()
    assert "not yet produced" in html_text and "{{" not in html_text
    assert "**Axes.**" in (page / "basic_behaviour.md").read_text()
    (figs / "f1_behaviours_survival.samples.json").unlink()
    with pytest.raises(SystemExit, match="f1_behaviours_survival"):
        BP.build(str(pop), str(out_root), str(page))
    (figs / "stray.png").write_text("x")
    with pytest.raises(SystemExit, match="not part of the F1-F7 sequence"):
        BP.build(str(pop), str(out_root), str(page))


def test_data_table_requires_reason_and_merges_identical_rows():
    """Register F71 / format-gate finding 1: a row using under 100% must say why; rows that differ
    only in the run collapse into one."""
    import build_page as BP
    run = lambda s: f"two-channel smell (control), ordinary agent, seed {s}"
    rows = [{"what": f"M2, {run(s)}", "used": 333, "total": 1000, "pct": 33.3,
             "note": "episodes with exactly one predator"} for s in (42, 43, 44)]
    out = BP.data_table("x", rows)
    assert "<details" in out and out.count("<tr><td>") == 1 and "3 runs" in out
    rows[0]["note"] = ""
    with pytest.raises(SystemExit, match="gives no reason"):
        BP.data_table("x", rows)


# ------------------------------------------------------------------- water (BASIC_BEHAVIOUR_WATER) ----
def describe_water(cfg, man):
    params = REG.rebuild_params(cfg)
    obs = REG.obs_indices(cfg, man, params)
    thermo = REG.thermal_info(cfg, params) if cfg["thermal"]["enabled"] else None
    T = REG.targets(cfg, man, ["agent_in_bush", "ate_food", "obs_true"], obs, thermo)
    F = REG.factors(cfg, man, obs, thermo)
    REG.add_thermal_consequence(F, T["warm_cell"]["available"])
    REG.add_water_factors(F, cfg, T)
    return params, obs, thermo, T, F


def test_water_audit_claims_every_draw():
    """Test 1: water draws are claimed (W1, W2); start_hydration_low/_high is looked up in the water
    block (on the pre-water code it was stamped 'not a draw' via body.random_start_hydration)."""
    cfg, man = load("g10sW")
    _, _, thermo, _, F = describe_water(cfg, man)
    rows = {r["path"]: r for r in REG.audit(cfg, F, thermo)}
    assert REG.unhandled(list(rows.values())) == []
    assert rows["water.random_start_hydration"]["claimed_by"] == "handler W1 (start_hydration)"
    assert rows["water.start_hydration_low/_high"]["claimed_by"] == "handler W1 (start_hydration)"
    assert rows["water.placement"]["claimed_by"].startswith("handler W2 (pond_corner")
    c1 = copy.deepcopy(cfg)
    c1["water"]["candidates"] = c1["water"]["candidates"][:1]
    r1 = {r["path"]: r for r in REG.audit(c1, F, thermo)}
    assert r1["water.placement"]["claimed_by"].startswith("not a draw")
    c2 = copy.deepcopy(cfg)
    c2["water"]["random_start_hydration"] = False
    r2 = {r["path"]: r for r in REG.audit(c2, F, thermo)}
    assert r2["water.start_hydration_low/_high"]["claimed_by"] == \
        "not a draw (random_start_hydration is false)"
    # a world without water: identical rows, with or without a disabled water block
    cfg, man = load("a01")
    _, _, _, Fa = describe(cfg, man)
    base = REG.audit(cfg, Fa, None)
    c3 = copy.deepcopy(cfg)
    c3["water"] = copy.deepcopy(c1["water"]) | {"enabled": False}
    assert REG.audit(c3, Fa, None) == base
    assert not any(r["path"].startswith("water") for r in base)


def test_hydration_index_by_name_not_alphabetical():
    """Test 2: the Hydration slot comes from the observation order, not the manifest's sorted keys."""
    cfg, man = load("g10sW")
    _, obs, _, _, _ = describe_water(cfg, man)
    assert obs["hydration"] == obs["order"].index("Hydration") == 2
    assert obs["alphabetical_hydration"] == 7 != obs["hydration"]
    assert obs["hydration_scale"] == float(cfg["water"]["max_hydration"])
    cfg, man = load("hv1ch")                        # no water: no hydration keys at all
    obs, _, _, _ = describe(cfg, man)
    assert "hydration" not in obs


def test_pond_replay_corner_and_cells():
    """Test 3: every replayed pond is one table row; cells inside the grid; 4x4 = 16 distinct cells."""
    for world, n_cells in (("g10sW", 4), ("g20sW", 16)):
        cfg, _ = load(world)
        params = REG.rebuild_params(cfg)
        R = REG.pond_cells(params, np.arange(1000000, 1000050))
        H, W = R["H"], R["W"]
        assert R["water_pos"].shape == (50, n_cells, 2)
        assert ((R["water_pos"] >= 0).all() and (R["water_pos"][..., 0] < H).all()
                and (R["water_pos"][..., 1] < W).all())
        for i in range(50):
            assert len({tuple(x) for x in R["water_pos"][i]}) == n_cells
            flat = R["water_pos"][i, :, 0] * W + R["water_pos"][i, :, 1]
            assert set(np.flatnonzero(R["masks"][R["corner"][i]])) == set(flat.tolist())
        assert len(set(R["corner"].tolist())) > 1           # 50 draws over 4 corners


def test_hydration_band_edge_guard():
    """Test 4: a float32 round-trip of an edge value stays in the band of the true value."""
    true100 = float(np.float32(100.0 / 200.0 - 1e-7) * 200.0)       # 99.99998
    assert REG.hyd_band(np.array([100.0, true100, 49.99996, 150.0, 0.0, 200.0])).tolist() == \
        [2, 2, 1, 3, 0, 3]


def test_term_names_cover_water_codes():
    """Test 5: codes 1-7 for populations with water; 1-5 otherwise (other pages unchanged)."""
    sys.path.insert(0, BB)
    import _fig as FG
    assert sorted(FG.term_names([{"inv": {"water": {}}}])) == [1, 2, 3, 4, 5, 6, 7]
    assert sorted(FG.term_names([{"inv": {}}])) == [1, 2, 3, 4, 5]


def test_pond_target_availability():
    """Test 6: pond available on a water world; unavailable with a reason at float16; absent without water."""
    cfg, man = load("g10sW")
    params, obs, thermo, T, F = describe_water(cfg, man)
    assert T["pond"]["available"] and T["pond"]["reason"] is None
    names = [f["name"] for f in F]
    assert names[-4:] == ["start_hydration", "spawn_dist_to_pond", "mean_hydration", "frac_time_on_pond"]
    m16 = dict(man, obs_precision="float16")
    T16 = REG.targets(cfg, m16, ["agent_in_bush", "ate_food", "obs_true"], obs, thermo)
    assert not T16["pond"]["available"] and "float16" in T16["pond"]["reason"]
    F16 = REG.factors(cfg, m16, obs, thermo)
    REG.add_water_factors(F16, cfg, T16)
    assert not any(f["name"] in ("start_hydration", "frac_time_on_pond") for f in F16)
    cfg, man = load("hv1ch")
    _, _, T, _ = describe(cfg, man)
    assert "pond" not in T


def test_make_population_cell_split(tmp_path):
    """D11: the Cell column splits on a middle dot ('1ch · ordinary') or a space ('g10sW ordinary')."""
    sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "hypervigilance"))
    import make_population as MP
    md = tmp_path / "study.md"
    md.write_text("## 9. Launch Manifest\n\n"
                  "| Run | Status | Cell | Tag (= wandb-name) | Seed | Log path |\n"
                  "|---|---|---|---|---|---|\n"
                  "| 1 | planned | g10sW ordinary | `rppo_thirst_g10sW_t1none_s42` | 42 | - |\n"
                  "| 2 | planned | g20s3 modulated | `rppo_thirst_g20s3_t16quad_s42` | 42 | - |\n"
                  "| 3 | planned | 1ch · ordinary | `rppo_hv1ch_t1none_s42` | 42 | - |\n"
                  "| 4 | planned | g10sW  ·  modulated x | `t` | 42 | - |\n")
    with pytest.raises(SystemExit):
        MP.from_study_doc(str(md), ["results/none"])
    md.write_text("\n".join(md.read_text().splitlines()[:-1]) + "\n")
    got = [(c["world"], c["agent"], c["label"]) for c in MP.from_study_doc(str(md), ["results/none"])]
    assert got == [("g10sW", "t1none", "g10sW_t1none_s42_1"), ("g20s3", "t16quad", "g20s3_t16quad_s42_2"),
                   ("hv1ch", "t1none", "hv1ch_t1none_s42_3")]


# --------------------------------------------------------- probe scenes with a pond (Revision 2) ----
def _synthetic_episode(bush_flags, pond_flags, hyd):
    bush, pond, away = (4, 1), (7, 7), (4, 4)
    snaps = []
    for b, p in zip(bush_flags, pond_flags):
        pos = bush if b else (pond if p else away)
        snaps.append({"agent_pos": np.array(pos), "obs_pos": [np.array(bush)], "animal_pos": [],
                      "injury_level": 0.0})
    return {"snapshots": snaps}, np.asarray(pond_flags, bool), np.asarray(hyd, float)


def test_prepond_truncation():
    """Test 8: no pond step -> equals episode_measures' bush_hiding; first pond step at k -> mean of
    the bush flags over 0..k-1; a hydration rise off the pond is an integrity failure."""
    import probe_pond as PP
    bush = [0, 1, 1, 1, 0, 0, 1, 1, 0, 0]
    ep, on, _ = _synthetic_episode(bush, [0] * 10, [150 - 0.625 * i for i in range(10)])
    share, k = PP.prepond(np.array(bush, bool), on)
    assert k == 10 and share == PP.episode_measures(ep)["bush_hiding"]
    pond = [0, 0, 0, 0, 0, 1, 1, 0, 0, 0]
    bush2 = [0, 1, 1, 1, 0, 0, 0, 1, 0, 0]
    hyd = [150.0]
    for p in pond[1:]:
        hyd.append(hyd[-1] + (5.0 if p else -0.625))
    share, k = PP.prepond(np.array(bush2, bool), np.array(pond, bool))
    assert k == 5 and share == pytest.approx(np.mean(bush2[:5]))
    assert PP.integrity(np.array(pond, bool), np.array(hyd)) == []
    bad = list(hyd)
    bad[3] = bad[2] + 1.0                     # hydration rose while off the pond
    assert PP.integrity(np.array(pond, bool), np.array(bad)) == [3]


def test_calibration_rule_branches():
    """Test 9: lowest qualifying S; fallback 1 (lowest worse-world P_visit with P_od ok); fallback 2."""
    import probe_pond as PP
    T = lambda pv, po: {"g10sW": {"P_visit": pv[0], "P_od": po[0]}, "g20sW": {"P_visit": pv[1], "P_od": po[1]}}
    c = PP.choose({150: T((0.25, 0.1), (0, 0)), 165: T((0.18, 0.2), (0.01, 0)), 180: T((0.1, 0.1), (0, 0))})
    assert c["S"] == 165 and c["branch"].startswith("rule")
    c = PP.choose({150: T((0.4, 0.3), (0, 0)), 165: T((0.3, 0.35), (0, 0)), 180: T((0.1, 0.1), (0.05, 0))})
    assert c["S"] == 165 and "FALLBACK 1" in c["branch"]          # worse-world 0.40 vs 0.35; 180 fails P_od
    c = PP.choose({150: T((0.4, 0.3), (0.03, 0)), 165: T((0.3, 0.3), (0.05, 0)), 180: T((0.1, 0.1), (0.1, 0))})
    assert c["S"] == 150 and "FALLBACK 2" in c["branch"]


def test_collate_tolerance_matches_4_decimal_csv():
    """R2-1: the driver CSV is rounded to 4 decimals, so a mean like 0.123456 must pass against
    '0.1235' and a real disagreement must not."""
    import probe_pond as PP
    m = 0.123456
    assert abs(m - float(f"{m:.4f}")) <= PP.CSV_TOL
    assert abs(m - 0.1236) > PP.CSV_TOL


def test_sweep_hard_stop_on_hydration_rise_off_pond():
    """d9 review N5: one injected row where hydration rose while the agent was off the pond is
    counted by the sweep's own per-step check, and the sweep's hard stop then refuses the store."""
    import sweep as SW
    # two episodes of 4 rows each (t = 0..3); the agent is on the pond at episode 0, t = 2 only
    on = np.array([0, 0, 1, 0, 0, 0, 0, 0], bool)
    hyd = np.array([100, 99.375, 104.375, 103.75, 150, 149.375, 148.75, 148.125])
    t = np.array([0, 1, 2, 3, 0, 1, 2, 3])
    idx = np.flatnonzero(t >= 1)
    prev = idx - 1
    assert SW.pond_step_exceptions(on, hyd, idx, prev) == 0
    WC = {"episodes_checked": 2, "start_cell_mismatches": 0, "steps_checked": 6, "step_exceptions": 0,
          "reset_hydration_max_abs_diff": 0.0}
    SW.require_water_checks(WC, 2, 6)                       # clean store passes
    bad = hyd.copy()
    bad[6] = bad[5] + 1.0                                   # hydration rose off the pond (episode 1, t = 2)
    n = SW.pond_step_exceptions(on, bad, idx, prev)
    assert n == 1
    with pytest.raises(SystemExit, match="water integrity checks failed"):
        SW.require_water_checks(dict(WC, step_exceptions=n), 2, 6)


def test_pond_replay_refuses_seeds_past_32_bits():
    """d9 review N3: PRNGKey truncates seeds to 32 bits; the replay refuses rather than mismatch."""
    cfg, _ = load("g10sW")
    with pytest.raises(SystemExit, match=r"outside \[0, 2\*\*31\)"):
        REG.pond_cells(REG.rebuild_params(cfg), [2 ** 31 + 5])
