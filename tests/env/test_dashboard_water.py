"""The episode dashboard draws a pond and a hydration row (THIRST_WATER_PLAN D8).

WHAT THIS FILE PINS, IN PLAIN WORDS. The thirst plan adds one fixed pond per
episode and a hydration body state. The dashboard learned to draw both BEFORE the
environment can produce them, so everything here is keyed on what a recording
carries -- a snapshot's `water_pos` (every pond cell, shape [N, 2]) and
`hydration` -- and checked against `params.water_enabled` once that exists.

  * A recording with neither key draws exactly as before (no pond, no row).
  * The pond is GROUND COVER: drawn under every token, so an animal or the agent
    standing in the water stays fully visible. Asserted by counting the agent's
    own-colour pixels with and without a pond under it -- a pond painted on top
    would lower that count.
  * Hydration gets an observed row when the agent senses it and a hidden twin
    when it does not, like every other body state.
  * No silent defaults: a hydration value without `water_max_hydration` raises,
    and a one-cell `water_pos` (which cannot say how big the pond is) raises.
"""
import copy
import os
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts" / "eval"))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import matplotlib  # noqa: E402
matplotlib.use("Agg")

import render_layout_audit as audit  # noqa: E402
import src.environment.dashboard.panels as P  # noqa: E402
from src.environment.dashboard import palette as PAL  # noqa: E402
from src.environment.dashboard.layout import pack  # noqa: E402

FIXTURES = _ROOT / audit.DEFAULT_FIXTURE_ROOT
_MISSING = (f"render-audit fixtures not on disk ({FIXTURES}); regenerate with "
            f"scripts/eval/make_render_fixture_recordings.py")


def _have(cell="M4"):
    d = FIXTURES / cell / cell
    return d.is_dir() and any(d.glob("episode_*.rec.gz"))


needs_fixtures = pytest.mark.skipif(not _have(), reason=_MISSING)


# ---------------------------------------------------------------------------
# presence: keyed on the recording, checked against params
# ---------------------------------------------------------------------------
class _Params:
    """Just enough of EnvParams for `from_params`; attributes set per test."""


def _base_params():
    from src.environment.config_loader import load_env_config, load_env_params
    cfg = load_env_config(str(_ROOT / "configs/environment/default.yaml"))
    return load_env_params(cfg)


def test_params_now_carry_the_water_flag():
    """The environment shipped the flag (THIRST_WATER_PLAN C2): a water-off world says so."""
    params = _base_params()
    assert params.water_enabled is False
    assert P.LayoutContext.from_params(params).water is False
    with pytest.raises(ValueError, match="agree"):
        P.LayoutContext.from_params(params, water=True)


def test_a_params_pickle_from_before_water_renders_as_water_off():
    """Recordings pickle EnvParams into run_meta.pkl. One written before the water fields
    existed must still build a layout -- as a world without water. (Before
    EnvParams.__setstate__ filled the missing fields, `get_observation_breakdown` raised
    AttributeError on every such recording.) Simulated by unpickling a state dict with the
    water fields removed, which is exactly what an old pickle carries."""
    import pickle
    from src.environment.sensor import get_observation_breakdown
    from src.environment.state import EnvParams
    params = _base_params()
    old_state = {k: v for k, v in params.__dict__.items() if not k.startswith("water_")}
    old = EnvParams.__new__(EnvParams)
    old.__setstate__(old_state)
    assert old.water_enabled is False and old.water_max_hydration == 0.0
    assert get_observation_breakdown(old) == get_observation_breakdown(params)
    assert P.LayoutContext.from_params(old).water is False
    round_trip = pickle.loads(pickle.dumps(params))
    assert round_trip.water_enabled is False


def test_a_recording_that_disagrees_with_its_world_raises():
    params = copy.copy(_base_params())
    object.__setattr__(params, "water_enabled", False)
    with pytest.raises(ValueError, match="agree"):
        P.LayoutContext.from_params(params, water=True)
    object.__setattr__(params, "water_enabled", True)
    assert P.LayoutContext.from_params(params, water=True).water is True
    assert P.LayoutContext.from_params(params).water is True   # derived from params


# ---------------------------------------------------------------------------
# the hydration row and its hidden twin
# ---------------------------------------------------------------------------
LEVEL_05 = _ROOT / "configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml"


def _ctx(water, observed):
    """The real level-05 campfire world -- the world level 06 extends -- with
    water on or off, and hydration in the observation or not.

    Built through the trainer's own loader rather than written by hand: an
    earlier hand-made breakdown declared interoceptive nociception enabled while
    leaving it out of the observation, and the completeness check correctly
    refused a world that contradicts itself.
    """
    import dataclasses
    from src.environment.config_loader import load_env_config, load_env_params
    params = load_env_params(load_env_config(str(LEVEL_05)))
    if water:
        # The params must agree with the recording (from_params checks it now that
        # EnvParams carries the flag): level 05 with the water gate switched on.
        params = params.replace(water_enabled=True, water_max_hydration=200.0)
    ctx = P.LayoutContext.from_params(params, water=water)
    if observed:
        ctx = dataclasses.replace(ctx, breakdown={**ctx.breakdown, "Hydration": 1})
    else:
        # With water on, the real breakdown always carries Hydration (the plan has no
        # "hydration hidden" flag yet); drop it by hand to exercise the hidden twin.
        ctx = dataclasses.replace(
            ctx, breakdown={k: v for k, v in ctx.breakdown.items() if k != "Hydration"})
    return ctx


def _present(ctx):
    return {s.key for s in P.present_panels(ctx)}


@pytest.mark.parametrize("water,observed,row,absent", [
    (True, True, "hydration", "hydration_hidden"),
    (True, False, "hydration_hidden", "hydration"),
])
def test_exactly_one_hydration_row_face_in_a_water_world(water, observed, row, absent):
    keys = _present(_ctx(water, observed))
    assert row in keys and absent not in keys


def test_a_world_without_water_has_no_hydration_row_at_all():
    keys = _present(_ctx(False, False))
    assert "hydration" not in keys and "hydration_hidden" not in keys


@pytest.mark.parametrize("observed", [True, False])
def test_the_vitals_card_still_packs_with_the_extra_row(observed):
    """Six rows in the fixed-size left column: the campfire world's five plus
    hydration. The packer must place it, not refuse the frame."""
    lay = pack(_ctx(True, observed))
    key = "hydration" if observed else "hydration_hidden"
    assert key in lay.panels
    vitals = lay.cards["vitals"]
    row = lay.panels[key]
    assert vitals.y <= row.y and row.y + row.h <= vitals.y + vitals.h


# ---------------------------------------------------------------------------
# the sensor adapter
# ---------------------------------------------------------------------------
def test_build_sensory_viz_turns_a_hydration_dim_into_a_tile(monkeypatch):
    import src.environment.sensor as S
    params = _base_params()
    real = S.get_observation_breakdown(params)

    def with_h(p):
        out = {}
        for k, v in real.items():
            out[k] = v
            if k == "Satiation":
                out["Hydration"] = 1
        return out

    monkeypatch.setattr(S, "get_observation_breakdown", with_h)
    width = sum(with_h(params).values())
    obs = np.zeros(width, dtype=np.float32)
    idx = list(with_h(params)).index("Hydration")
    obs[sum(list(with_h(params).values())[:idx])] = 0.37

    class _State:
        pass

    tiles = {e["name"]: e for e in S.build_sensory_viz(obs, _State(), params)}
    assert tiles["Hydration"]["type"] == "intensity"
    assert tiles["Hydration"]["intensity"] == pytest.approx(0.37)


# ---------------------------------------------------------------------------
# on a rendered frame
# ---------------------------------------------------------------------------
def _renderer(water_pos=None, hydration=None, max_h=200.0):
    from src.environment.dashboard import EpisodeRenderer
    from src.utils.eval_recording import load_episode, load_run_meta

    rec = FIXTURES / "M4" / "M4"
    meta = load_run_meta(rec)
    params = copy.copy(meta["params"])
    if max_h is not None:
        object.__setattr__(params, "water_max_hydration", max_h)
    if water_pos is not None or hydration is not None:
        # Since THIRST_WATER_PLAN C2 every EnvParams carries `water_enabled` (M4's pickle
        # unpickles as False), and the renderer checks it agrees with the recording.
        object.__setattr__(params, "water_enabled", True)
    payload = load_episode(sorted(rec.glob("episode_*.rec.gz"))[1])
    for s in payload["snapshots"]:
        if water_pos is not None:
            s["water_pos"] = np.asarray(water_pos, dtype=np.int32)
        if hydration is not None:
            s["hydration"] = float(hydration)
    return EpisodeRenderer(params, meta["icon_config"], payload, title="water test"), payload


def _iris_px(frame):
    """Pixels exactly the agent's own colour: the agent token's opaque interior."""
    iris = np.array([int(PAL.IRIS[i:i + 2], 16) for i in (1, 3, 5)])
    return int(np.all(frame == iris, axis=-1).sum())


def _water_px(frame):
    water = np.array([int(PAL.WATER[i:i + 2], 16) for i in (1, 3, 5)])
    return int(np.all(np.abs(frame.astype(int) - water) <= 2, axis=-1).sum())


@needs_fixtures
@pytest.mark.integration
def test_the_pond_is_drawn_UNDER_the_agent_standing_in_it():
    """Both frames carry water, so both have the same layout; the only
    difference is an EMPTY pond list versus a pond under the agent.

    An earlier version compared a no-water frame against a water frame. The
    water frame also has a hydration row, which makes the vitals card taller and
    the World map smaller -- so the map's agent dot and viewport box MOVED, and
    that reflow was counted as the pond covering the agent (561 pixels lost, all
    in the map, none in the grid view). Same layout both sides removes that.
    """
    r0, payload = _renderer(water_pos=np.zeros((0, 2), dtype=np.int32), hydration=100.0)
    try:
        plain = r0.frame(0)
    finally:
        r0.close()
    a = tuple(int(x) for x in np.asarray(payload["snapshots"][0]["agent_pos"]))
    pond = [(a[0], a[1]), (a[0], a[1] + 1), (a[0] + 1, a[1]), (a[0] + 1, a[1] + 1)]
    r1, _ = _renderer(water_pos=pond, hydration=100.0)
    try:
        wet = r1.frame(0)
    finally:
        r1.close()
    assert _water_px(plain) == 0, "water colour on a frame with no pond"
    assert _water_px(wet) > 0, "the pond was not drawn"
    assert _iris_px(wet) == _iris_px(plain), (
        f"the agent lost pixels to the pond ({_iris_px(plain)} -> {_iris_px(wet)}): "
        f"the pond is being drawn over a token instead of under it")


@needs_fixtures
@pytest.mark.integration
def test_hydration_without_its_maximum_raises():
    with pytest.raises(ValueError, match="water_max_hydration"):
        _renderer(water_pos=[(1, 1), (1, 2), (2, 1), (2, 2)], hydration=90.0, max_h=None)


@needs_fixtures
@pytest.mark.integration
def test_a_one_cell_water_pos_is_refused_not_guessed():
    r, _ = _renderer(water_pos=[[1, 1]], hydration=90.0)
    try:
        # shape (1, 2) is a legal list of cells; a bare (2,) is not
        for s in r.snapshots:
            s["water_pos"] = np.array([1, 1], dtype=np.int32)
        with pytest.raises(ValueError, match=r"\[N, 2\]"):
            r.frame(0)
    finally:
        r.close()


# ---------------------------------------------------------------------------
# the pixel audit and ground cover (THIRST_WATER_PLAN D8.8)
# ---------------------------------------------------------------------------
def test_the_ground_cover_tag_is_one_string_in_painter_and_audit():
    """The audit may not import the dashboard, so it holds its own copy. Two
    copies of one name can disagree silently; this makes them disagree loudly."""
    from src.environment.dashboard import cells as C
    assert audit.GROUND_COVER_GID == C.GROUND_COVER_GID


def _audit_pond_frame(mutate_over=False):
    """Audit M4 episode 1 step 0 with a pond under the agent. `mutate_over` forces
    the ground cover ABOVE every token -- the defect the guard exists to refuse."""
    import src.environment.dashboard.painters as PN
    from src.environment.dashboard import cells as C
    rec = FIXTURES / "M4" / "M4"
    fi = audit.load_inputs(rec, 0, episode=1)
    r0, payload = _renderer()
    r0.close()
    a = tuple(int(x) for x in np.asarray(payload["snapshots"][0]["agent_pos"]))
    pond = [(a[0], a[1]), (a[0], a[1] + 1), (a[0] + 1, a[1]), (a[0] + 1, a[1] + 1)]
    orig = PN.rrect

    def over(ax, x, y, w, h, rad, fc, *args, **kw):
        if fc == PAL.WATER:
            kw["z"] = C.TOKEN_Z + 1
        return orig(ax, x, y, w, h, rad, fc, *args, **kw)

    if mutate_over:
        PN.rrect = over
    try:
        r, _ = _renderer(water_pos=pond, hydration=100.0)
    finally:
        PN.rrect = orig
    try:
        frame = r.frame(0)
        saved = audit.render_capture
        audit.render_capture = lambda _r, _fi, _f=frame, _g=r.fig: (_f, _g)
        try:
            findings, probe, _ = audit.audit_frame(fi, "dashboard", arena_axes="arena",
                                                  cell_axes="arena")
        finally:
            audit.render_capture = saved
        probe.close()
    finally:
        r.close()
    return findings


@needs_fixtures
@pytest.mark.integration
def test_a_pond_under_the_agent_adds_no_cell_findings():
    """D8.8's gate: the pond is ground cover, not a creature, so a correct frame
    with the agent standing in it reports no co-occupancy finding at all."""
    cell = [f for f in _audit_pond_frame() if f.rule.startswith("cell_")]
    assert cell == [], [(f.rule, f.a, f.b) for f in cell]


@needs_fixtures
@pytest.mark.integration
def test_ground_cover_painted_OVER_the_agent_is_refused():
    """The tag that keeps ground cover out of the creature count must not let it
    cover a creature. Forced above the tokens, the guard fires."""
    hits = [f for f in _audit_pond_frame(mutate_over=True)
            if f.rule == "cell_overdraw" and "ground cover" in f.detail]
    assert hits, "ground cover drawn over an occupant was not reported"


@pytest.mark.skipif(not _have("W1"), reason=_MISSING)
@pytest.mark.integration
def test_a_REAL_level_06_frame_passes_the_audit():
    """THE D8.8 GATE ON A GENUINE WATER WORLD, not a level-05 world with water bolted on.

    The pond test above audits M4, whose own recording does not OBSERVE Hydration, so the
    audit's "every observed modality has a panel title" rule had nothing to check there.
    On a real level-06 recording it does: the Hydration row is drawn, and the audit must
    be able to read its title back. It could not until `TITLE_TABLE` learned the name --
    the row was plainly on screen and the audit reported it absent.
    """
    from src.environment.dashboard import EpisodeRenderer
    from src.utils.eval_recording import load_episode, load_run_meta

    rec = FIXTURES / "W1" / "W1"
    meta = load_run_meta(rec)
    assert meta["params"].water_enabled, "W1 must be the level-06 pond world"
    fi = audit.load_inputs(rec, 0, episode=0)
    payload = load_episode(sorted(rec.glob("episode_*.rec.gz"))[0])
    r = EpisodeRenderer(meta["params"], meta["icon_config"], payload, title="W1 audit",
                        action_map=meta.get("action_map"),
                        channel_display=meta.get("channel_display"))
    try:
        frame = r.frame(0)
        saved = audit.render_capture
        audit.render_capture = lambda _r, _fi, _f=frame, _g=r.fig: (_f, _g)
        try:
            findings, probe, _ = audit.audit_frame(fi, "dashboard", arena_axes="arena",
                                                  cell_axes="arena")
        finally:
            audit.render_capture = saved
        probe.close()
    finally:
        r.close()
    bad = [(f.rule, f.a) for f in findings
           if f.rule == "panel_absent" or f.rule.startswith("cell_")]
    assert bad == [], bad
