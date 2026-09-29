"""Unit tests for the refusals of scripts/analysis/nmn/run_wakeup.py (plan File Changes §11)."""
import os
import sys

import numpy as np
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scripts.analysis.nmn import run_wakeup as rw  # noqa: E402

MAN = os.path.join(ROOT, "docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml")


def _write(tmp_path, man):
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(man))
    return p


def test_real_manifest_loads():
    man = rw.load_manifest(MAN)
    assert len(man["runs"]) == 19


def test_point_set_key_raises(tmp_path):
    man = yaml.safe_load(open(MAN))
    man["sparse_measure_points"] = {"freeze": [1, 5, 10]}
    with pytest.raises(ValueError, match="per-measure point set"):
        rw.load_manifest(_write(tmp_path, man))
    man = yaml.safe_load(open(MAN))
    man["runs"][0]["freeze_checkpoints"] = [200019]
    with pytest.raises(ValueError, match="per-measure point set"):
        rw.load_manifest(_write(tmp_path, man))


def test_wakeup_block_must_equal_rules():
    man = rw.load_manifest(MAN)
    settings = dict(man["wakeup"])
    rw.check_wakeup_block(man, settings)
    with pytest.raises(ValueError, match="differ"):
        rw.check_wakeup_block(man, {**settings, "noise_k": 2})
    with pytest.raises(ValueError, match="keys"):
        rw.check_wakeup_block(man, {k: v for k, v in settings.items() if k != "sustain"})


def test_grid_is_the_checkpoint_list_with_step0_when_anchorable():
    run = {"label": "r", "checkpoints": [10, 20, 30]}
    assert rw.grid_x(run, True).tolist() == [0, 10, 20, 30]
    assert rw.grid_x(run, False).tolist() == [10, 20, 30]
    rw.assert_curve_grid(run, "freeze", np.array([0, 10, 20, 30]))
    with pytest.raises(AssertionError):
        rw.assert_curve_grid(run, "freeze", np.array([0, 10, 30]))
    with pytest.raises(AssertionError):
        rw.assert_curve_grid(run, "plateau", np.array([0, 10, 20, 30]))


def test_out_root_is_required(tmp_path):
    """out_root is a required manifest key (set by the designer at R.2); there is no
    --out-root CLI argument to fall back on."""
    man = yaml.safe_load(open(MAN))
    del man["out_root"]
    with pytest.raises(ValueError, match="out_root"):
        rw.load_manifest(_write(tmp_path, man))
    with pytest.raises(SystemExit):
        rw.main(["--manifest", MAN, "--measures", "plateau", "--out-root", str(tmp_path)])


def _scan_result(stages, truncated):
    rows = [{"Episode/Number": 1.0, "stage/index": float(s)} for s in stages]
    return {"rows": rows, "exit_code": None, "file": "synthetic.wandb", "truncated": truncated}


def test_truncated_read_needs_a_later_stage(monkeypatch):
    """O1: a half-written trailing record is accepted only for a continual run whose stage
    read (stage 0) is followed by logged rows of a later stage; otherwise the run stops."""
    from scripts.analysis.nmn import wandb_history as wh
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0, 0, 1], "AssertionError"))
    assert rw.read_scanned("may", "d", 0)["truncated"] == "AssertionError"
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0, 0], "AssertionError"))
    with pytest.raises(RuntimeError, match="no later stage"):
        rw.read_scanned("may", "d", 0)
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([], "AssertionError"))
    with pytest.raises(RuntimeError):
        rw.read_scanned("l05", "d", None)              # a non-continual run: never accepted
    monkeypatch.setattr(wh, "scan", lambda d, allow_truncated: _scan_result([0], None))
    assert rw.read_scanned("l05", "d", None)["truncated"] is None


def test_plateau_is_numbered_on_the_run_scale():
    """O2: the plateau curve is unanchored (array index 0 = checkpoint 1); the table's
    t_plateau_checkpoint is wakeup.position(t), i.e. index + 1, the scale every lag uses."""
    from scripts.analysis.nmn import wakeup
    B2 = {"threshold_mode_headline": "fraction_of_rise", "plateau_f": 0.9, "sustain": 2,
          "final_k": 3, "noise_k": 3, "min_noise_points": 5, "noise_window_divisor": 3,
          "noise_window_max_fraction": 0.5}                       # test fixture values
    surv = {"row_weight": "delta_episode_number", "min_window_n": 1000}
    rng = np.random.default_rng(0)
    rows = [{"Episode/Number": 4000.0 * (i + 1), "Episode/_window_n": 4000.0,
             "Episode/Steps": 100 + 100 * min(1.0, (i + 1) / 200) + rng.normal(0, 1)}
            for i in range(750)]
    cks = [100000 * (i + 1) for i in range(30)]
    r, m, info = rw.plateau_crossing("synthetic", rows, rw.grid_x({"checkpoints": cks}, False),
                                     B2, surv)
    assert r.anchored is False and r.index is not None
    assert wakeup.position(r.t, cks) == r.index + 1 == cks.index(int(r.t)) + 1
    assert info["start_counter"] == 0.0 and len(m) == 30


# ------------------------------------------------------------------ GPU measures (Stage 4) --
def test_gpu_measures_need_a_cpu_backend(monkeypatch):
    """The T8 grid check reads continual runs' saved stage on the CPU backend."""
    monkeypatch.setenv("JAX_PLATFORMS", "cuda")
    with pytest.raises(ValueError, match="cuda,cpu"):
        rw.main(["--manifest", MAN, "--measures", "rho"])


def test_update_size_is_relative_and_split():
    prev = {"modulator": {"k": np.array([3.0, 4.0])}, "actor": {"k": np.array([1.0, 0.0])}}
    cur = {"modulator": {"k": np.array([3.0, 4.0 + 5.0])}, "actor": {"k": np.array([1.0, 0.5])}}
    u = rw.update_size(prev, cur)
    assert u["mod_rel"] == pytest.approx(1.0) and u["main_rel"] == pytest.approx(0.5)
    assert u["mod_over_main"] == pytest.approx(2.0)
    with pytest.raises(ValueError):
        rw.update_size({"actor": prev["actor"]}, {"actor": cur["actor"]})


def test_update_size_curve_is_unanchored_one_point_per_checkpoint():
    run = {"label": "r", "checkpoints": [10, 20, 30]}
    assert rw.ANCHORABLE["update_size"] is False
    rw.assert_curve_grid(run, "update_size", [10, 20, 30])
    with pytest.raises(AssertionError):
        rw.assert_curve_grid(run, "update_size", [0, 10, 20, 30])


def _pts(cks, sites=("rnn",)):
    """Synthetic point files: every measure a function of the checkpoint index."""
    pts = {}
    for i, x in enumerate([0] + cks):
        v = float(i)
        M = {"grad_probe": {"first_update": {t: {"share": v, "mod_sq": v * v}
                                             for t in ("policy", "value", "entropy", "total")},
                            "full_iteration": {"share": v, "mod_grad_norm_mean": v}},
             "rho": {"rho": {s: {"gamma": {"rho": v}, "beta": {"rho": v}} for s in sites}},
             "swing": {s: {"gamma_swing_mean": v, "beta_swing_mean": v} for s in sites},
             "freeze": {"freeze_gain": {"mean_diff": -v}, "freeze_offset": {"mean_diff": -v},
                        "live_survival_mean": v}}
        if x:
            M["update_size"] = {"mod_rel": v, "main_rel": v, "mod_over_main": 1.0}
        pts[x] = {"measures": M}
    return pts


def test_run_curves_grid_and_headline_set():
    cks = [10, 20, 30, 40]
    run = {"label": "r", "checkpoints": cks}
    curves = rw.run_curves(run, _pts(cks), ["rnn"], (np.array(cks, float), [1.0, 2, 3, 4]))
    head = sorted(n for n, c in curves.items() if c["headline"])
    assert head == ["freeze.gain", "freeze.offset", "grad_probe.first_update.entropy",
                    "grad_probe.first_update.policy", "grad_probe.first_update.value",
                    "grad_share.total", "rho.rnn", "swing.rnn", "update_size.modulator"]
    assert curves["rho.rnn"]["x"] == [0, 10, 20, 30, 40] and curves["rho.rnn"]["anchored"]
    assert curves["update_size.modulator"]["x"] == cks
    assert curves["grad_share.total"]["anchored"] is False
    pts = _pts(cks)
    del pts[20]
    with pytest.raises(ValueError, match="missing"):
        rw.run_curves(run, pts, ["rnn"], (np.array(cks, float), [1.0, 2, 3, 4]))


def test_grad_share_curve_bins_rows_by_interval():
    rows = [{"Episode/Steps": 10.0, "Episode/Number": 5.0, "Episode/_window_n": 5.0,
             "timesteps": 1.0}]
    for e, ts in ((5.0, 1.0), (15.0, 2.0), (18.0, 3.0), (25.0, 4.0)):
        rows.append({"Episode/Steps": 10.0, "Episode/Number": e, "Episode/_window_n": 5.0,
                     "timesteps": ts})
    # level-05 style loss rows: no Episode/Number, joined through timesteps
    for ts, m, a in ((1.0, 1.0, 2.0), (2.0, 1.0, 4.0), (3.0, 3.0, 4.0), (4.0, 2.0, 2.0)):
        rows.append({"timesteps": ts, rw.MOD_GN: m, rw.LOSS_GN: a})
    scanned = {"rows": rows, "file": "x", "exit_code": 0, "truncated": None}
    run = {"label": "r", "checkpoints": [10, 20, 30]}
    x, m, info, logged = rw.grad_share_curve(run, scanned, None)
    assert list(x) == [10, 20, 30]
    assert m[0] == pytest.approx(0.25)                       # (1/2)^2 at episode 5
    assert m[1] == pytest.approx(((1 / 4) ** 2 + (3 / 4) ** 2) / 2)
    assert m[2] == pytest.approx(1.0)
    assert info["rows_per_interval"] == [1, 2, 1]
    assert info["start_counter"] == 0.0


def test_measure_reading_uses_positions_and_the_headline_mode():
    B2 = dict(yaml.safe_load(open(MAN))["wakeup"])
    cks = [100000.0 * i for i in range(1, 17)]
    xg = [0.0] + cks
    curve = {"x": xg, "m": [float(1 / (1 + np.exp(-(v / 1e5 - 8.0)))) for v in xg],
             "anchored": True}
    r = rw.measure_reading("t", curve, cks, cks[6], B2)     # crossing at checkpoint 8
    assert r["headline_mode"] == B2["threshold_mode_headline"] == "fraction_of_rise"
    assert r["headline"]["t"] == cks[7]
    assert r["lag"]["delta_positions"] == 1 and r["lag"]["reading"] == "coincident"
    assert rw.measure_reading("t", curve, cks, cks[5], B2)["lag"]["reading"] == "late"
    assert rw.measure_reading("t", curve, cks, cks[9], B2)["lag"]["reading"] == "early"
    assert r["beside_mode"] == "fraction_of_final"


# ------------------------------------------- registered B2 headline family (commit 322a5966) --
SITES5 = ["encoder_unimodal", "encoder_multimodal", "rnn", "actor", "critic"]
# every word a per-run wake point must not carry: the B2 reading and May words, and the per-run
# lag words that feed only the across-worlds sign test
VERDICT_WORDS = {"late", "early", "coincident", "undetermined across worlds", "agree",
                 "do not agree"}


def test_real_manifest_registers_the_17_curve_family():
    man = rw.load_manifest(MAN)
    reg = man["b2_headline_curves"]
    assert len(reg) == 17 == len(set(reg))
    assert rw.registered_sites(reg) == sorted(SITES5)


def _noisy_pts(cks, sites, rng):
    """Synthetic point files on the run's grid: a logistic rise plus small noise per curve,
    so the registered guard sees a real change and a defined wake point."""
    pts = {}
    n = len(cks)
    for i, x in enumerate([0] + cks):
        def v():
            return float(1 / (1 + np.exp(-(i - n / 2))) + rng.normal(0, 0.01))
        M = {"grad_probe": {"first_update": {t: {"share": v(), "mod_sq": 1.0}
                                             for t in ("policy", "value", "entropy", "total")},
                            "full_iteration": {"share": v(), "mod_grad_norm_mean": 1.0}},
             "rho": {"rho": {s: {"gamma": {"rho": v()}, "beta": {"rho": v()}} for s in sites}},
             "swing": {s: {"gamma_swing_mean": v(), "beta_swing_mean": v()} for s in sites},
             "freeze": {"freeze_gain": {"mean_diff": -v()}, "freeze_offset": {"mean_diff": -v()},
                        "live_survival_mean": v(), "freeze_equivalence": {"exact": True}}}
        if x:
            M["update_size"] = {"mod_rel": v(), "main_rel": 1.0, "mod_over_main": 1.0}
        pts[x] = M
    return pts


def _synthetic_summarise(tmp_path, monkeypatch, registered=None, sites_by_run=None, bound=None):
    """Runs run_wakeup.summarise end to end on synthetic curves (one level-05-style run and one
    May-style run), with the real pinned rules and the real B2 settings. No real data is read."""
    import json
    from scripts.analysis.nmn import decision_rules as dr, rules_pin, wandb_history as wh
    real = rw.load_manifest(MAN)
    pinned = dr.load(real)
    policy = dr.verdict_policy(pinned, real["evidence_status"])
    B2 = dr.b2_settings(pinned.parameters)
    rstamp = rules_pin.stamp(pinned)
    rng = np.random.default_rng(0)
    runs = [{"label": "l05_syn", "path": "syn/l05", "checkpoints": [1000 * (i + 1) for i in range(50)]},
            {"label": "may_syn", "path": "syn/may", "checkpoints": [1000 * (i + 1) for i in range(15)]}]
    man = {**real, "runs": runs,
           "b2_headline_curves": list(real["b2_headline_curves"] if registered is None else registered)}
    man["b2_family_bound"] = {**real["b2_family_bound"],
                              "family_size": len(man["b2_headline_curves"]) * len(runs),
                              **(bound or {})}
    out = tmp_path / "out"
    for r in runs:
        sites = (sites_by_run or {}).get(r["label"], SITES5)
        for x, M in _noisy_pts(r["checkpoints"], sites, rng).items():
            pf = rw.point_path(out, r["label"], x)
            pf.parent.mkdir(parents=True, exist_ok=True)
            pf.write_text(json.dumps({"rules_sha256": rstamp["sha256"], "measures": M}))
    plateau = {"runs": [{"label": r["label"], "n_points": len(r["checkpoints"]),
                         "t_plateau_episode": float(r["checkpoints"][len(r["checkpoints"]) // 4])}
                        for r in runs]}
    grids = {"l05_syn": {"continual": False, "stage_index": None},
             "may_syn": {"continual": True, "stage_index": 0}}
    monkeypatch.setattr(rw, "run_sites",
                        lambda r: list((sites_by_run or {}).get(r["label"], SITES5)))
    monkeypatch.setattr(wh, "run_tag", lambda p: "syn")
    monkeypatch.setattr(wh, "resolve_by_tag", lambda t: "syn")
    monkeypatch.setattr(rw, "read_scanned", lambda *a: {"rows": []})

    def share(run, scanned, stage_index):
        x = rw.grid_x(run, False)
        m = [float(1 / (1 + np.exp(-(i - len(x) / 2))) + rng.normal(0, 0.01)) for i in range(len(x))]
        return x, m, {"rows_per_interval": [1] * len(x), "start_counter": 0.0}, (x.copy(), np.ones(len(x)))

    monkeypatch.setattr(rw, "grad_share_curve", share)
    stamp = {"decision_rules": rstamp, "evidence_status": policy.status}
    rc = rw.summarise(man, MAN, out, stamp, rstamp, plateau, grids, B2, pinned, policy, dr)
    return rc, out


def _strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)
    elif isinstance(o, str):
        yield o


def test_summarise_headline_missing_curve_raises(tmp_path, monkeypatch):
    reg = [n for n in yaml.safe_load(open(MAN))["b2_headline_curves"] if n != "freeze.offset"]
    with pytest.raises(ValueError, match=r"differs from b2_headline_curves.*freeze\.offset"):
        _synthetic_summarise(tmp_path, monkeypatch, registered=reg)


def test_summarise_headline_extra_curve_raises(tmp_path, monkeypatch):
    reg = yaml.safe_load(open(MAN))["b2_headline_curves"] + ["freeze.live_survival"]
    with pytest.raises(ValueError, match=r"differs from b2_headline_curves.*freeze\.live_survival"):
        _synthetic_summarise(tmp_path, monkeypatch, registered=reg)


def test_duplicate_headline_name_is_refused(tmp_path):
    man = yaml.safe_load(open(MAN))
    man["b2_headline_curves"].append("freeze.gain")
    with pytest.raises(ValueError, match="distinct"):
        rw.load_manifest(_write(tmp_path, man))


def test_summarise_sixth_site_raises(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match=r"may_syn: enabled FiLM sites .* differ from the 5"):
        _synthetic_summarise(tmp_path, monkeypatch,
                             sites_by_run={"may_syn": SITES5 + ["extra_site"]})
    assert not (tmp_path / "out" / "curves").exists()      # raised before anything was written


def test_summarise_per_run_output_carries_caveat_and_no_verdict_word(tmp_path, monkeypatch):
    import json
    rc, out = _synthetic_summarise(tmp_path, monkeypatch)
    assert rc == 0
    doc = json.loads((out / "b2_reading.json").read_text())
    assert doc["headline_curves"] == yaml.safe_load(open(MAN))["b2_headline_curves"]
    per_run = [doc["per_run_wake_points"]] + [
        json.loads((out / "curves" / f"{l}.json").read_text())["wake_points"]
        for l in ("l05_syn", "may_syn")]
    defined = 0
    import re
    for block in per_run:
        points = [p for run in (block.values() if "caveat" not in next(iter(block.values()))
                                else [block]) for p in run.values()]
        assert len(points) in (17, 34)
        for p in points:
            cav = p["caveat"]
            assert cav.startswith("Descriptive only. No single run's wake point counts as evidence")
            # the rate quoted is the one registered for this curve's length
            n = cav.split("on this ")[1].split("-point")[0]
            rate = yaml.safe_load(open(MAN))["b2_family_bound"]["false_pass_rate_per_curve"][n]
            assert f"{100 * rate:.3g} %" in cav
            assert "1 level-05 worlds" in cav and "1 May seeds stay descriptive" in cav
            assert not re.search(r"\b(late|early|coincident|agree|undetermined)\b", cav, re.I)
            assert "reading" not in p["lag"]
            defined += p["lag"]["delta_positions"] is not None
            for s in _strings(p):
                if s == cav:
                    continue
                assert s.strip().lower() not in VERDICT_WORDS, s
    assert defined > 0                       # the test sees real per-run wake points
    # the across-worlds reading keeps its words; the May seeds are marked descriptive
    for b in doc["reading"].values():
        assert b["reading"] in ("late", "early", "undetermined across worlds")
        assert b["may_status"].startswith("descriptive")


def test_compile_cache_status_reports_the_launch_setting(tmp_path):
    import jax
    before = jax.config.jax_compilation_cache_dir
    try:
        jax.config.update("jax_compilation_cache_dir", None)
        assert rw.compile_cache_status()["active"] is False
        (tmp_path / "entry").write_text("x")
        jax.config.update("jax_compilation_cache_dir", str(tmp_path))
        st = rw.compile_cache_status()
        assert st["active"] is True and st["dir"] == str(tmp_path) and st["entries_at_start"] == 1
    finally:
        jax.config.update("jax_compilation_cache_dir", before)


# ------------------------------------------------------------- code review of Stage 4 -----
class _Ctx:
    """Minimal RunContext stand-in for sweep_run: step 0 only, swing only."""
    def __init__(self):
        self.run = {"label": "syn", "checkpoints": [10, 20]}
        self.episodes, self.seed_base, self.warmup_iters = 4, 90000, 1

    def agent(self, x):
        return object()

    def params(self, x, agent=None):
        return {}


PROV = {"git_sha": "a" * 40, "git_dirty": False, "evidence_status": "b2_wakeup",
        "device": "synthetic"}


def test_point_records_carry_provenance(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(rw, "measure_swing", lambda ctx, params: {"rnn": {}})
    stamp = {"sha256": "r" * 64}
    with pytest.raises(ValueError, match="provenance"):
        rw.sweep_run(_Ctx(), {"swing"}, tmp_path, stamp, points=[0])
    rw.sweep_run(_Ctx(), {"swing"}, tmp_path, stamp, points=[0], prov=PROV)
    rec = json.loads(rw.point_path(tmp_path, "syn", 0).read_text())
    assert {k: rec[k] for k in rw.PROVENANCE_KEYS} == PROV
    # resuming a point written at another code sha raises
    with pytest.raises(ValueError, match="written at code"):
        rw.sweep_run(_Ctx(), {"swing", "rho"}, tmp_path, stamp, points=[0],
                     prov={**PROV, "git_sha": "b" * 40})


def test_backfill_copies_provenance_from_done_and_changes_nothing_else(tmp_path):
    import json
    from scripts.analysis.nmn import backfill_point_provenance as bf
    d = tmp_path / "points" / "syn"
    d.mkdir(parents=True)
    old = {"label": "syn", "x": 0, "rules_sha256": "r" * 64, "settings": {"a": 1},
           "measures": {"swing": {"rnn": {"gamma_swing_mean": 1.5}}}, "seconds": {"load": 1.0},
           "generated_utc": "t"}
    (d / "0.json").write_text(json.dumps(old))
    with pytest.raises(RuntimeError, match="_done.json"):     # sweep may still be writing
        bf.plan_backfill(tmp_path, ["syn"])
    (d / "_done.json").write_text(json.dumps({**PROV, "decision_rules": {"sha256": "r" * 64},
                                              "measures": ["swing"]}))
    todo = bf.plan_backfill(tmp_path, ["syn"])
    assert len(todo) == 1
    assert bf.apply_backfill(todo, "test") == 1
    new = json.loads((d / "0.json").read_text())
    assert {k: new[k] for k in rw.PROVENANCE_KEYS} == PROV
    assert {k: new[k] for k in old} == old and new["provenance_backfilled"] == "test"
    assert bf.plan_backfill(tmp_path, ["syn"]) == []           # idempotent
    new["device"] = "other"
    (d / "0.json").write_text(json.dumps(new))
    with pytest.raises(ValueError, match="differs from"):
        bf.plan_backfill(tmp_path, ["syn"])


def test_sanity_band_first_window_opens_at_the_start_counter():
    cks = [10, 20, 30]
    pts = {c: {"measures": {"grad_probe": {"full_iteration": {"mod_grad_norm_mean": 1.0},
                                           "first_update": {"total": {"mod_sq": 1.0}}}}}
           for c in cks}
    e = np.array([2.0, 7.0, 15.0])            # episode 2 lies before a start counter of 5
    v = np.array([100.0, 1.0, 1.0])
    band = rw.sanity_band({"checkpoints": cks}, pts, (e, v), 0.05, 0.95, start=5.0)
    assert band["rows"][0]["logged_n"] == 2 and band["rows"][0]["inside"] is True
    assert rw.sanity_band({"checkpoints": cks}, pts, (e, v), 0.05, 0.95,
                          start=0.0)["rows"][0]["logged_n"] == 3


def test_git_dirty_covers_the_probe_code_path():
    import inspect
    src = inspect.getsource(rw.main)
    assert '"src/", "train.py",' in src and '"scripts/analysis/nmn"' in src


# ------------------------------------------------- b2_family_bound (commit ecf8fbe6) -------
def test_real_manifest_family_bound_matches_the_family():
    man = rw.load_manifest(MAN)
    fb = rw.check_family_bound(man)
    assert fb["family_size"] == 17 * 19 == len(man["b2_headline_curves"]) * len(man["runs"])


def test_family_size_mismatch_raises(tmp_path):
    man = yaml.safe_load(open(MAN))
    man["b2_family_bound"]["family_size"] = 322
    with pytest.raises(ValueError, match="family_size 322"):
        rw.check_family_bound(rw.load_manifest(_write(tmp_path, man)))
    man = yaml.safe_load(open(MAN))
    man["runs"] = man["runs"][:18]
    with pytest.raises(ValueError, match="= 306"):
        rw.check_family_bound(man)


def test_caveat_rate_is_picked_by_curve_length_and_unknown_length_raises():
    fb = yaml.safe_load(open(MAN))["b2_family_bound"]
    r = fb["false_pass_rate_per_curve"]
    for n in ("51", "50", "16", "15"):
        assert f"{100 * r[n]:.3g} %" in rw.family_caveat(fb, 3, 16, 3, int(n))
    with pytest.raises(ValueError, match="17-point"):
        rw.family_caveat(fb, 3, 16, 3, 17)


def test_changed_rate_in_the_manifest_changes_the_printed_caveat(tmp_path, monkeypatch):
    import json
    real = yaml.safe_load(open(MAN))["b2_family_bound"]["false_pass_rate_per_curve"]
    _, out = _synthetic_summarise(tmp_path / "a", monkeypatch)
    changed = {**real, "51": 0.0421}
    _, out2 = _synthetic_summarise(tmp_path / "b", monkeypatch,
                                   bound={"false_pass_rate_per_curve": changed})
    a = json.loads((out / "curves" / "l05_syn.json").read_text())["wake_points"]["rho.rnn"]["caveat"]
    b = json.loads((out2 / "curves" / "l05_syn.json").read_text())["wake_points"]["rho.rnn"]["caveat"]
    assert f"{100 * real['51']:.3g} %" in a and "4.21 %" not in a
    assert "4.21 %" in b and a != b
    doc = json.loads((out2 / "b2_reading.json").read_text())
    assert "4.21 % (51 points)" in doc["per_run_caveat"]
    assert "4.21 %" in doc["per_run_wake_points"]["l05_syn"]["rho.rnn"]["caveat"]
    # the May run's 16-point curve keeps its own rate
    m = doc["per_run_wake_points"]["may_syn"]["rho.rnn"]["caveat"]
    assert f"{100 * real['16']:.3g} %" in m
