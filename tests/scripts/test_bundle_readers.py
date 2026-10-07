"""Phase 2 reader ports (plan SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md, F8, readers R4-R7):
each reader gives the SAME result on a sweep condition whose checkpoints are folders and on a copy
whose checkpoints are archive-only (<step>.zip, folders removed) -- never a silent skip.

Synthetic cells in pytest's tmp_path (real EpisodeRecorder.write + np.savez_compressed), the rPPO
sweep layout <step>/<run dir>/<step>/{episodes,recordings/<step>}/. The same check on copies of
real cells is recorded in the plan's Implementation Report.
"""
import ast
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

import src.utils.episode_bundle as EB  # noqa: E402
from src.utils.eval_recording import EpisodeRecorder  # noqa: E402

STEPS = (980, 1000, 99)        # 99 < 980 < 1000 numerically; "99" > "980" > "1000" as strings


def _state(t, rng):
    return SimpleNamespace(
        agent_pos=np.array([t % 3 + 1, 1]), satiation=50.0 - t, nutrition=40.0,
        injury_level=float(rng.integers(0, 50)), rest_streak=0, res_pos=np.zeros((2, 2), int),
        res_active=np.ones(2, bool), animal_pos=np.array([[int(rng.integers(0, 7)), 4]]),
        obs_pos=np.array([[2, 1]]))


def _write_cell(cell: Path, step: int, n_ep: int, seed: int):
    rng = np.random.default_rng(seed)
    base = cell / "20260101-000000_rppo_x_s42" / str(step)
    rec = base / "recordings" / str(step)
    for e in range(n_ep):
        r = EpisodeRecorder(e, 0, seed + e)
        for t in range(6 + e):
            r.append(_state(t, rng), rng.normal(size=4), rng.normal(size=4), int(t % 4), 0.5)
        r.write(rec / f"episode_{e:06d}.rec.gz")
        (base / "episodes").mkdir(parents=True, exist_ok=True)
        np.savez_compressed(base / "episodes" / f"{e:04d}.npz", seed=np.int64(seed + e),
                            termination_reason=np.int64(0), length=np.int64(6 + e))
    (rec / "run_meta.pkl").write_bytes(b"meta")
    (base / "metadata.json").write_text(json.dumps({"step": step}))


@pytest.fixture
def forms(tmp_path):
    """Two copies of one condition dir: 'folder' (legacy) and 'zip' (archive-only)."""
    def make(rel):
        out = {}
        for form in ("folder", "zip"):
            cond = tmp_path / form / rel
            for k, s in enumerate(STEPS):
                _write_cell(cond / str(s), s, n_ep=5, seed=10 * k)
                if form == "zip":
                    EB.pack(cond / str(s), cond / f"{s}.zip")
                    shutil.rmtree(cond / str(s))
            out[form] = cond
        assert sorted(p.name for p in out["zip"].iterdir()) == sorted(f"{s}.zip" for s in STEPS)
        return SimpleNamespace(root=tmp_path, **out)
    return make


def _load(path, name, extra=()):
    for p in extra:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _eq(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return np.array_equal(a, b)
    return a == b


def test_r4_probe_pond_episodes_in(forms):
    PP = _load(_REPO / "scripts/analysis/basic_behaviour/probe_pond.py", "probe_pond_t",
               extra=(_REPO / "scripts/analysis/basic_behaviour",))
    f = forms("cond")
    for s in STEPS:
        a = PP.episodes_in(str(EB.cell_path(f.folder, s)))
        b = PP.episodes_in(str(EB.cell_path(f.zip, s)))
        assert len(a) == 5 and [x[0] for x in a] == [x[0] for x in b]
        assert [(x[2], x[3]) for x in a] == [(x[2], x[3]) for x in b]
        assert all(x[3] is not None for x in a)
        for (_, ca, za, ra), (_, cb, zb, rb) in zip(a, b):
            assert _eq(EB.load_npz(ca, za), EB.load_npz(cb, zb))
            assert _eq(EB.load_recording(ca, ra), EB.load_recording(cb, rb))
            assert int(EB.load_npz(ca, za)["seed"]) == int(EB.load_recording(ca, ra)["seed"])


def test_r5_traj_newest_checkpoint(forms, monkeypatch):
    T = _load(_REPO / "scripts/analysis/studies/basicq2_waves/_traj.py", "traj_t")
    f = forms("_scratch/lvl04_control/avoid_pred_inj00")
    got = {}
    for form in ("folder", "zip"):
        monkeypatch.setattr(T, "SCRATCH", str(f.root / form / "_scratch"))
        got[form] = (T._episodes("control", "avoid_pred_inj00"), T._one("control", "avoid_pred_inj00"))
    (ck, eps), one = got["folder"]
    assert ck == "1000" and len(eps) == 5 and one["episodes"] == 5
    assert _eq(got["folder"], got["zip"])


def test_r6_t04_newest_recordings(forms):
    src = (_REPO / "scripts/analysis/studies/thermal_probes/t04_variance_budget.py").read_text()
    fn = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "newest_recordings")
    ns = {"EB": EB, "os": __import__("os")}
    exec(compile(ast.Module([fn], []), "t04_newest_recordings", "exec"), ns)
    f = forms("lvl05_control/avoid_pred_inj00")
    a, b = ns["newest_recordings"](str(f.folder)), ns["newest_recordings"](str(f.zip))
    assert len(a) == 5 and [m for _, m in a] == [m for _, m in b]
    # selection unchanged from the folder-only code: the largest path STRING, so "99" wins
    assert all(str(c).endswith("/99") for c, _ in a) and all(str(c).endswith("/99.zip") for c, _ in b)
    for (ca, ma), (cb, mb) in zip(a, b):
        assert _eq(EB.load_recording(ca, ma), EB.load_recording(cb, mb))


def test_r7_scene_steps_one(forms, monkeypatch, tmp_path):
    inj = _REPO / "scripts/analysis/studies/injury_dependence"
    SS = _load(inj / "scene_steps.py", "scene_steps_t", extra=(inj,))
    f = forms("metrics_history_rppo_injurygrid_core/_scratch/lab/avoid_pred_inj00")
    monkeypatch.setattr(SS, "kernel_for", lambda run: np.array([0.0, 0.5, 0.3, 0.2]))
    out = {}
    for form in ("folder", "zip"):
        monkeypatch.setattr(SS, "EV", str(f.root / form))
        monkeypatch.setattr(SS, "OUT", str(tmp_path / f"out_{form}"))
        assert SS.one(("core", "lab", "unused", 2))[2] == 10
        out[form] = dict(np.load(tmp_path / f"out_{form}" / "core" / "lab.npz"))
    assert list(out["folder"]["avoid_pred_inj00__checkpoints"]) == [980, 1000]
    assert _eq(out["folder"], out["zip"])
