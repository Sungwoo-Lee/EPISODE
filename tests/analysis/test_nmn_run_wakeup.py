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
