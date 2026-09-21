"""directional sensors — parity, kernel geometry, masking, diamond behaviour.

Plan: docs/develop/active/sensors/DIRECTIONAL_SENSORS_PLAN.md

Consolidated into one module rather than the six the plan named; the sections
below map 1:1 onto that plan's test table.

Bit-exactness tests pin the CPU backend. Float results are lowering-dependent —
CPU and GPU legitimately differ, and GPU autotuning makes repeat GPU runs differ
from each other — so a bit-exact assertion is only meaningful on a fixed backend.
"""
import os
os.environ.setdefault('JAX_PLATFORMS', 'cpu')

import sys
import numpy as np
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _ROOT)

import jax
import jax.numpy as jnp
from src.utils.config import Config
from src.environment.config_loader import load_env_params, _read_visual_mask
from src.environment.sensor import (
    get_observation, get_observation_breakdown, get_visual_offsets,
    sense_visual, sense_olfaction_cells, _psf_weights, _visual_mask_gate,
)
from src.environment.wrapper import ParallelEnv

DEFAULT = os.path.join(_ROOT, 'configs/environment/default.yaml')


def params(**overrides):
    c = Config.load_yaml(DEFAULT)
    for k, v in overrides.items():
        c.set(k, v)
    return load_env_params(c)


def one_state(p, seed=7):
    env = ParallelEnv(p)
    st, obs = env.reset(jax.random.PRNGKey(seed), 1)
    return jax.tree.map(lambda x: x[0], st), np.asarray(obs[0])


def eight_channel_params(**overrides):
    """`default.yaml` as it read before the visual vector was narrowed to one channel.

    Three tests below are about arithmetic that only EXISTS at more than one
    channel -- a cap that must apply per channel says nothing in a world with a
    single channel to apply it to. The eight-channel world is not archived
    anywhere loadable, so it is rebuilt here from the live default rather than
    pinned to a file that would rot: widen the vector, then drop the per-entity
    `visual_properties` and the terrain table that were written for width 1, so
    the loader falls back to the one-hot channel map it auto-generates at width
    8 -- food 3, hiding predator 4, obstacle 6, terrain 0/1/2. That map IS the
    historical world, so these tests read the same channels they always did.

    Deleting the keys rather than rewriting them is the point: an override that
    widened the vector and left a length-1 `visual_properties` in place would be
    rejected by the loader, which is the check working, not a nuisance.
    """
    import copy
    d = copy.deepcopy(Config.load_yaml(DEFAULT).to_dict())
    d['sensory']['visual_vector_size'] = 8
    d['sensory'].pop('visual_background_properties', None)
    for group in ('resources', 'entities', 'obstacles'):
        for entry in d['environment'].get(group) or []:
            entry.pop('visual_properties', None)
            entry.pop('visual_properties_std', None)
    c = Config(d)
    for k, v in overrides.items():
        c.set(k, v)
    return load_env_params(c)


def visual_at(p, V, *, obstacles_on_agent=0, food_on_agent=0, obstacle_at=None,
              agent=(5, 5), seed=7):
    """Read the visual sensor in a scene we placed by hand -> `[num_cells, V]`.

    Every entity the reset drew is switched OFF first and only the named ones
    switched back on. That is not tidiness: under blur every active entity in
    the world writes some quantity into every sampled cell, so a scene left as
    reset would fold a dozen strangers' tails into the number under test.
    """
    st, _ = one_state(p, seed)
    a = jnp.array(agent, dtype=st.agent_pos.dtype)
    obs_pos, obs_act = jnp.full_like(st.obs_pos, 99), jnp.zeros_like(st.obs_active)
    for i in range(obstacles_on_agent):
        obs_pos, obs_act = obs_pos.at[i].set(a), obs_act.at[i].set(True)
    if obstacle_at is not None:
        i = obstacles_on_agent
        obs_pos = obs_pos.at[i].set(jnp.array(obstacle_at, dtype=obs_pos.dtype))
        obs_act = obs_act.at[i].set(True)
    res_pos, res_act = jnp.full_like(st.res_pos, 99), jnp.zeros_like(st.res_active)
    for i in range(food_on_agent):           # slot 0.. are the `food` resource
        res_pos, res_act = res_pos.at[i].set(a), res_act.at[i].set(True)
    st2 = st.replace(agent_pos=a, obs_pos=obs_pos, obs_active=obs_act,
                     res_pos=res_pos, res_active=res_act,
                     animal_active=jnp.zeros_like(st.animal_active))
    return np.asarray(sense_visual(a, st2, p)).reshape(-1, V)


# ---------------------------------------------------------------- parity ---

#: What `configs/environment/default.yaml` ships since 2026-09-19 (commit 47b1b8c3):
#: the sensor ladder's `Q2_presence_binary` arm. Spelled out in one place so a
#: drift in the default fails ONE named test with a readable diff, instead of
#: scattering unexplained failures across the module the way it did when it moved.
Q2_PRESENCE_BINARY = {
    'olfactory_grid_range': 1,
    'visual_sensor_range': 2,
    'visual_vector_size': 1,
    'visual_value_mode': 'clamp',
    'visual_blur_enabled': True,
}


def test_the_shipped_defaults_are_the_presence_binary_arm():
    """The directional sensors ship ON, and this is the arm they ship as.

    This test used to assert the opposite, and was right to. The feature was
    allowed in on the promise that every knob shipped at the value which
    reproduced the older sensor byte for byte, so turning it on was a deliberate
    act and no existing run changed meaning underneath anyone. The sensor-ladder
    study ended that argument -- smell at radius 1 was the most valuable single
    change it measured -- and on 2026-09-19 the default moved onto the ladder's
    `Q2_presence_binary` arm. That is intended and permanent, so the premise is
    replaced rather than patched.

    The five keys are pinned TOGETHER because the arm is one decision, not five.
    Sight samples a 13-cell diamond but reports a single channel capped at
    presence, so it says WHERE something is and never WHAT; identity moves to
    the nose, whose five readings carry a gradient and separate a predator from
    a rabbit by the ratio of two odour channels. Widen the vector without
    narrowing anything else and vision answers both questions, olfaction goes
    unused, and the agent is in a condition the ladder measured as worse.

    Nothing the old defaults covered is lost. Each retired setting is exercised
    below through an explicit local override: range 0 in the bitwise parity
    test, `sum` in the value-mode test, blur off in the clamp and leak tests,
    the eight-channel vector in `eight_channel_params`.
    """
    p = params()
    got = {'olfactory_grid_range': int(p.olfactory_grid_range),
           'visual_sensor_range': int(p.visual_sensor_range),
           'visual_vector_size': int(p.visual_vector_size),
           'visual_value_mode': str(p.visual_value_mode),
           'visual_blur_enabled': bool(p.visual_blur_enabled)}
    assert got == Q2_PRESENCE_BINARY, (
        "configs/environment/default.yaml has drifted off the Q2_presence_binary "
        "arm. If that is deliberate, change this dict and say why in the "
        "CONFIG_CRITICAL_SETTINGS change log -- these keys are load-bearing for "
        "every run that does not override them.")
    for m in (p.res_visual_mask, p.animal_visual_mask, p.obs_visual_mask):
        assert int(np.asarray(m).sum()) == 0, "no entity is masked by default"


def test_on_source_half_cell_floor_is_bit_identical_at_shipped_gamma():
    """Option B: 1/(0.5**gamma) replaces the literal 2.0. At gamma=1 they must be
    the same bits, in the traced form the sensor actually evaluates."""
    @jax.jit
    def traced(g):
        return 1.0 / jnp.power(jnp.float32(0.5), g)
    got = np.asarray(traced(jnp.float32(1.0)))
    assert got.tobytes() == np.float32(2.0).tobytes()


def test_observation_is_bit_identical_to_stored_pre_change_fixture():
    """CP1. Compares against an artefact captured BEFORE the change, not a fresh
    re-derivation from source."""
    fix = os.path.join(_ROOT, 'tests/env/fixtures/directional_sensors/obs_baseline.npz')
    if not os.path.exists(fix):
        pytest.skip('baseline fixture not captured')
    import scripts.verification.capture_sensor_baseline as cap
    # THIS GATE PINS A PAST REFACTOR, NOT THE CURRENT WORLD. The fixture is a
    # pre-DIRECTIONAL_SENSORS artefact, so it must keep being compared against the
    # world it was captured in. On 2026-09-14 the bush gained `blocks_animals: true`
    # (A1 of BUSH_REFUGE_AND_LOCATION_DEPENDENT_RECOVERY), a deliberate change to the
    # LIVE world that moved animal trajectories and reddened this test. Freezing the
    # WORLD keeps the refactor evidence; re-baselining the fixture would destroy it.
    # The npz KEY stays 'configs__environment__default.yaml' — it names the config the
    # fixture was captured from, which has not changed. Contrast
    # tests/env/fixtures/thermal_parity/, which reads the LIVE configs on purpose.
    ref = np.load(fix)['configs__environment__default.yaml']
    got = cap.rollout(cap.PARITY_WORLD)
    assert got.shape == ref.shape
    assert got.tobytes() == ref.tobytes(), (
        f"max abs diff {np.abs(got - ref).max():.3e}")


# ------------------------------------------------------------- breakdown ---

@pytest.mark.parametrize('olf,vis', [(0, 0), (1, 0), (0, 2), (1, 2), (2, 1)])
def test_breakdown_sums_to_actual_observation_width(olf, vis):
    """CP2 — a mismatch here silently mis-assigns perceptual noise."""
    p = params(**{'sensory.olfactory_grid_range': olf, 'sensory.visual_sensor_range': vis})
    _, obs = one_state(p)
    bd = get_observation_breakdown(p)
    assert sum(bd.values()) == obs.shape[0]
    assert bd['Olfaction'] == (2 * olf ** 2 + 2 * olf + 1) * int(p.res_property.shape[-1])
    assert bd['Visual'] == (2 * vis ** 2 + 2 * vis + 1) * int(p.visual_vector_size)


# ---------------------------------------------------------- psf geometry ---

def _W(p, st):
    cells = st.agent_pos + get_visual_offsets(p.visual_sensor_range)
    pos = jnp.concatenate([st.res_pos, st.animal_pos, st.obs_pos], 0)
    return np.asarray(_psf_weights(cells, pos, st.agent_pos, p)), np.asarray(cells), np.asarray(pos)


def test_psf_is_finite_everywhere_including_on_the_agent_cell():
    """CP3. sigma_floor exists precisely so an entity at d=0 does not divide by zero."""
    p = params(**{'sensory.visual_sensor_range': 2, 'sensory.visual_blur_enabled': True})
    st, _ = one_state(p)
    W, _, _ = _W(p, st)
    assert np.isfinite(W).all() and not np.isnan(W).any()
    # force an entity onto the agent's own cell
    st2 = st.replace(res_pos=st.res_pos.at[0].set(st.agent_pos))
    W2, _, _ = _W(p, st2)
    assert np.isfinite(W2).all(), "sigma_floor must keep the on-agent case finite"


def test_anisotropy_one_is_isotropic():
    """CP3 — rho=1 must give equal weight to cells equidistant from the entity."""
    p = params(**{'sensory.visual_sensor_range': 2, 'sensory.visual_blur_enabled': True,
                  'sensory.visual_blur_anisotropy': 1.0})
    st, _ = one_state(p)
    W, cells, pos = _W(p, st)
    d = np.linalg.norm(cells - pos[0], axis=1)
    same = np.abs(d - d[0]) < 1e-6
    assert np.allclose(W[same, 0], W[same, 0][0], rtol=1e-5)


def test_total_weight_falls_off_with_distance():
    """CP4 — if this fails the normalisation is wrong and distance carries no signal."""
    p = params(**{'sensory.visual_sensor_range': 2, 'sensory.visual_blur_enabled': True})
    st, _ = one_state(p)
    agent = st.agent_pos
    cells = agent + get_visual_offsets(2)
    totals = []
    for dist in (1, 2, 3, 4, 5):
        e = jnp.array([[agent[0] - dist, agent[1]]], dtype=st.res_pos.dtype)
        totals.append(float(np.asarray(_psf_weights(cells, e, agent, p)).sum()))
    assert all(a > b for a, b in zip(totals, totals[1:])), f"not monotonic: {totals}"


# ---------------------------------------------------------------- masking ---

def test_far_mask_leaks_nothing_anywhere_including_the_centre_cell():
    """Regression for the Critical review finding: gating on the CELL's distance
    instead of the ENTITY's left a masked entity depositing its blur tail in the
    agent's own cell."""
    agent = jnp.array([5, 5])
    ents = jnp.array([[5, 5], [4, 5], [3, 5], [8, 8]])       # co-located, 1, 2, 6 away
    gate = np.asarray(_visual_mask_gate(agent, ents, jnp.array([1, 1, 1, 1])))[0]
    assert gate[0] == 1.0, "'far' stays visible when the agent stands on it"
    assert (gate[1:] == 0.0).all(), "'far' must contribute exactly zero at any d>=1"


def test_all_mask_hides_everywhere_and_none_hides_nothing():
    agent = jnp.array([5, 5])
    ents = jnp.array([[5, 5], [4, 5], [8, 8]])
    assert (np.asarray(_visual_mask_gate(agent, ents, jnp.array([2, 2, 2])))[0] == 0.0).all()
    assert (np.asarray(_visual_mask_gate(agent, ents, jnp.array([0, 0, 0])))[0] == 1.0).all()


def test_unknown_visual_mask_string_raises_at_load():
    with pytest.raises(ValueError, match='visual_mask'):
        _read_visual_mask({'visual_mask': 'invisible'}, 'TestEntity')
    assert _read_visual_mask({}, 'TestEntity') == 0            # absent -> none


# ------------------------------------------------------- olfactory diamond ---

def test_diamond_reading_is_highest_toward_the_source():
    p = params(**{'sensory.olfactory_grid_range': 1})
    st, _ = one_state(p)
    agent = jnp.array([5, 5])
    V = int(p.res_property.shape[-1])
    for (dr, dc), name in [((-2, 0), 'north'), ((2, 0), 'south'),
                           ((0, 2), 'east'), ((0, -2), 'west')]:
        st2 = st.replace(
            agent_pos=agent,
            res_pos=jnp.full_like(st.res_pos, 99).at[0].set(jnp.array([5 + dr, 5 + dc])),
            res_active=jnp.zeros_like(st.res_active).at[0].set(True),
            animal_active=jnp.zeros_like(st.animal_active),
            obs_active=jnp.zeros_like(st.obs_active))
        out = np.asarray(sense_olfaction_cells(st2, p)).reshape(-1, V)
        offs = np.asarray(get_visual_offsets(1))
        toward = int(np.argmin(np.abs(offs - np.array([np.sign(dr), np.sign(dc)])).sum(1)))
        away = int(np.argmin(np.abs(offs + np.array([np.sign(dr), np.sign(dc)])).sum(1)))
        assert out[toward, 0] > out[away, 0], f"{name}: gradient points the wrong way"


def test_out_of_bounds_diamond_cells_read_exactly_zero():
    """Without this the suite stays green while olfaction reads through walls."""
    p = params(**{'sensory.olfactory_grid_range': 1})
    st, _ = one_state(p)
    V = int(p.res_property.shape[-1])
    st2 = st.replace(agent_pos=jnp.array([0, 0]))              # top-left corner
    out = np.asarray(sense_olfaction_cells(st2, p)).reshape(-1, V)
    offs = np.asarray(get_visual_offsets(1))
    oob = [i for i, (dr, dc) in enumerate(offs) if dr < 0 or dc < 0]
    assert oob, "corner placement should put some cells out of bounds"
    assert (out[oob] == 0.0).all(), "out-of-bounds cells must be exactly zero"


def test_range_zero_matches_the_single_point_sensor_bitwise():
    """Range 0 must stay an exact re-implementation of the sensor it replaced.

    The diamond sampler was allowed to ship on the promise that its range-0 case
    IS the old single-sample sensor -- not close to it, the same bits -- so a run
    recorded before the change stays comparable with one recorded after. Moving
    the default to radius 1 on 2026-09-19 changed which case is ORDINARY; it did
    not retire the promise, and the override below is now the only thing holding
    it under test. Bitwise rather than approximate on purpose: a float that
    drifts in its last place means the lowering changed, and this module pins
    the CPU backend precisely so it is allowed to say so.
    """
    p = params(**{'sensory.olfactory_grid_range': 0})
    st, _ = one_state(p)
    from src.environment.sensor import _sense_olfaction_at
    a = np.asarray(sense_olfaction_cells(st, p))
    b = np.asarray(_sense_olfaction_at(st.agent_pos, st, p))
    assert a.tobytes() == b.tobytes()


# ------------------------------------------------ DIRECTIONAL_SENSORS value mode + occlusion ---

def test_value_mode_ships_clamp_still_accepts_sum_and_rejects_unknown():
    """Three facts about one key: what ships, what still loads, what is refused.

    `clamp` became the shipped value on 2026-09-19 as half of the presence-binary
    arm -- a one-wide vector is only a presence bit if something caps it. `sum`,
    the older behaviour in which two rocks in a cell read 2.0, was not removed,
    only demoted, so it is asserted here through the same explicit override every
    test in this module now uses to reach it.

    The rejection half was never about defaults and is the reason this test
    predates the change: the mode selects a trace-time branch, so an unrecognised
    string cannot fail at run time -- it would fall silently through to `sum` and
    train an agent nobody meant to train. It has to raise at LOAD.
    """
    assert params().visual_value_mode == 'clamp'
    assert params(**{'sensory.visual_value_mode': 'sum'}).visual_value_mode == 'sum'
    with pytest.raises(ValueError, match='visual_value_mode'):
        params(**{'sensory.visual_value_mode': 'average'})


#: Channels of the eight-wide one-hot map the loader auto-generates: obstacle 6,
#: food 3. Terrain owns 0/1/2, so both of these carry entity mass and nothing else.
CH_OBSTACLE, CH_FOOD = 6, 3

#: What ONE entity standing on the agent's own cell contributes under the shipped
#: blur, derived rather than measured: `_psf_weights` normalises by the kernel's
#: analytic mass `2*pi*sigma_par*sigma_perp`, and at distance 0 both sigmas are
#: held at the `visual_blur_sigma_floor` of 0.5, so the peak is `1/(2*pi*0.25)`.
#: It is 0.637 -- comfortably under the cap, which is the whole point below.
LONE_ENTITY_UNDER_BLUR = 2.0 / np.pi


def test_clamp_caps_the_per_channel_entity_sum_which_blur_keeps_one_entity_from_reaching():
    """What `clamp` caps, and why the shipped world almost never reaches the cap.

    READ THIS BEFORE DESCRIBING `clamp` ANYWHERE. The obvious reading -- "a cell
    with something in it reads 1.0" -- is wrong under the settings that ship, and
    that exact misunderstanding reached three config comments and a change-log
    entry before a reviewer caught it. The code (`sensor.py`, the matmul then
    `jnp.minimum`) sums EVERY entity's weighted contribution over ALL entities
    and only then caps the total. The cap is on a sum, not a switch on a cell.

    With blur OFF the two readings coincide, because an entity's weight is 1 on
    its own cell and 0 everywhere else: one obstacle gives exactly 1.0, two give
    2.0 summed and 1.0 capped. That is the arithmetic this test was written for
    in an eight-channel world, and the first half keeps it -- including the part
    the name claims, that the cap is PER CHANNEL: a food sharing the same cell is
    one entity in a different channel and the obstacle cap does not touch it.

    With blur ON -- which is what ships -- a lone entity on the agent's own cell
    contributes 0.637, so `clamp` changes nothing at all and the channel reports
    a blurred DENSITY rather than a presence bit. The cap only binds when two or
    more entities share a cell, where the summed 1.273 is cut back to 1.0. The
    second half asserts both, at the real default, so the difference cannot be
    described away again.
    """
    # ---- blur OFF: the exact-match arithmetic, in the eight-channel world it
    # ---- was written for. Two obstacles and one food on the agent's own cell.
    off = {'sensory.visual_sensor_range': 1, 'sensory.visual_blur_enabled': False}
    summed = visual_at(eight_channel_params(**off, **{'sensory.visual_value_mode': 'sum'}),
                       8, obstacles_on_agent=2, food_on_agent=1)
    capped = visual_at(eight_channel_params(**off, **{'sensory.visual_value_mode': 'clamp'}),
                       8, obstacles_on_agent=2, food_on_agent=1)
    assert summed[0, CH_OBSTACLE] == pytest.approx(2.0), "two obstacles must COUNT as two"
    assert capped[0, CH_OBSTACLE] == pytest.approx(1.0), "the cap must cut 2.0 back to 1.0"
    assert summed[0, CH_FOOD] == pytest.approx(1.0)
    assert capped[0, CH_FOOD] == pytest.approx(1.0), (
        "the cap is per channel: a single food in the same cell is already below "
        "1.0 and must come through untouched by the obstacle channel's cap")
    # Exact matching writes nowhere else. Contrast the blurred reading below.
    assert (summed[1:, CH_OBSTACLE] == 0.0).all()

    # ---- blur ON, at the shipped defaults: one channel, radius 2, clamp.
    ship = params()
    loose = params(**{'sensory.visual_value_mode': 'sum'})
    lone_capped = visual_at(ship, 1, obstacles_on_agent=1)
    lone_summed = visual_at(loose, 1, obstacles_on_agent=1)
    assert lone_summed[0, 0] == pytest.approx(LONE_ENTITY_UNDER_BLUR, rel=1e-5)
    assert lone_capped[0, 0] == pytest.approx(lone_summed[0, 0], rel=1e-6), (
        "at the shipped settings a lone entity is 0.637, far under the cap, so "
        "`clamp` is a NO-OP on it -- the channel is a density, not a presence bit")
    assert lone_capped[0, 0] < 1.0

    pair_capped = visual_at(ship, 1, obstacles_on_agent=2)
    pair_summed = visual_at(loose, 1, obstacles_on_agent=2)
    assert pair_summed[0, 0] == pytest.approx(2 * LONE_ENTITY_UNDER_BLUR, rel=1e-5)
    assert pair_summed[0, 0] > 1.0, "two co-located entities is where the cap starts to bind"
    assert pair_capped[0, 0] == pytest.approx(1.0)

    # The density half: blur puts real mass in every neighbouring sampled cell,
    # which is what makes distance vague while bearing stays sharp.
    assert (lone_capped[1:, 0] > 0.0).all(), (
        "blur must spread the entity into the rest of the diamond; if this is "
        "zero the kernel is not being applied and the reading is exact matching")


def test_blur_leaks_an_entity_from_outside_the_visual_range_into_the_diamond():
    """`visual_sensor_range` is where the agent SAMPLES, not how far it can see.

    `_psf_weights` applies no radius gate whatsoever. It writes every entity in
    the world into every sampled cell with a gaussian weight, and the only thing
    keeping a distant one out of the reading is that the weight has decayed --
    never a test on the entity's distance. So an obstacle three cells from an
    agent whose range is 1 lands a seventh of a co-located entity's contribution
    in the diamond, and one six cells away still lands a fiftieth.

    Worth pinning because the range reads like a wall and is not one, and because
    the leak is directional -- the mass arrives in the cell FACING the entity, so
    it is informative rather than noise. Whether it should be gated is a design
    question nobody has answered; this test does not take a side, it records what
    the shipped kernel does so a future gate shows up as a deliberate change here
    rather than as a quiet shift in what every agent has been seeing.
    """
    p = params(**{'sensory.visual_sensor_range': 1})
    offs = [tuple(int(x) for x in o) for o in np.asarray(get_visual_offsets(1))]
    south = offs.index((1, 0))

    seen = []
    for dist in (2, 3, 4, 6):                       # all well outside range 1
        cells = visual_at(p, 1, obstacle_at=(5 + dist, 5))[:, 0]
        assert cells.max() > 0.0, (
            f"an entity {dist} cells away registered nothing at range 1; if a "
            f"radius gate was added to _psf_weights, that is a deliberate change "
            f"to what every agent sees and belongs in the critical-settings log")
        assert int(np.argmax(cells)) == south, (
            f"the leak from {dist} cells south arrived in cell {offs[int(np.argmax(cells))]}, "
            f"not the southern one -- the kernel has lost its bearing")
        seen.append(float(cells.max()))
    assert all(a > b for a, b in zip(seen, seen[1:])), f"not monotonic: {seen}"
    assert seen[1] == pytest.approx(LONE_ENTITY_UNDER_BLUR / 7, rel=0.1)

    # Exact matching is the contrast: nothing outside the diamond can register.
    exact = visual_at(params(**{'sensory.visual_sensor_range': 1,
                                'sensory.visual_blur_enabled': False}),
                      1, obstacle_at=(5 + 3, 5))
    assert (exact[:, 0] == 0.0).all(), "without blur an entity off the diamond is invisible"


def test_blur_knobs_are_conditional_on_the_enabling_flag():
    """Read only when blur is on, so a historical run snapshot that predates them
    still loads. But loud the moment blur is actually enabled without them.

    Blur ships ON since 2026-09-19, so both halves now name the flag explicitly.
    The tolerant half HAS to -- it is the off-path, and inheriting it from the
    default is what silently turned this test into a duplicate of the strict half
    on the day the default moved. The strict half says so too, rather than
    leaning on a default that could move again.

    The tolerance is narrow by design. These three knobs are optional only while
    the code reading them is switched off; the moment blur is on they are
    mandatory with no fallback, because a missing radial scale is not a harmless
    omission -- it is a kernel shape nobody chose.
    """
    import copy
    from src.environment.config_loader import load_env_config
    from src.utils.config import Config
    KNOBS = ('visual_blur_radial_scale', 'visual_blur_anisotropy', 'visual_blur_sigma_floor')
    base = load_env_config(DEFAULT).to_dict()

    d = copy.deepcopy(base)
    for k in KNOBS:
        d['sensory'].pop(k, None)
    d['sensory']['visual_blur_enabled'] = False     # the off-path, stated not inherited
    load_env_params(Config(d))                      # blur off, knobs absent -> fine

    d = copy.deepcopy(base)
    for k in KNOBS:
        d['sensory'].pop(k, None)
    d['sensory']['visual_blur_enabled'] = True
    with pytest.raises(ValueError, match='visual_blur'):
        load_env_params(Config(d))                  # blur on, knobs absent -> raises


@pytest.mark.parametrize('knob,bad', [('visual_blur_anisotropy', 0.0),
                                      ('visual_blur_sigma_floor', 0.0),
                                      ('visual_blur_radial_scale', -1.0)])
def test_blur_knobs_still_validated_when_blur_is_on(knob, bad):
    """The NaN trap must stay closed now that the checks are conditional."""
    with pytest.raises(ValueError, match=knob):
        params(**{'sensory.visual_blur_enabled': True, f'sensory.{knob}': bad})


def test_occlusion_defaults_off_and_validates_its_subkeys():
    p = params()
    assert p.visual_occlusion_enabled is False
    for bad, key in [({'sensory.visual_occlusion_enabled': True,
                       'sensory.visual_occlusion_cone_deg': 120.0,
                       'sensory.visual_occlusion_strength': 1.0}, 'cone_deg'),
                     ({'sensory.visual_occlusion_enabled': True,
                       'sensory.visual_occlusion_cone_deg': 10.0,
                       'sensory.visual_occlusion_strength': 3.0}, 'strength')]:
        with pytest.raises(ValueError, match=key):
            params(**bad)


def test_occlusion_hides_only_what_is_behind_a_blocker():
    """A blocker at 2 cells hides a target at 4 cells on the same bearing, and
    leaves a target on a different bearing alone."""
    from src.environment.sensor import _occlusion_gate
    p = params(**{'sensory.visual_sensor_range': 2,
                  'sensory.visual_occlusion_enabled': True,
                  'sensory.visual_occlusion_cone_deg': 15.0,
                  'sensory.visual_occlusion_strength': 1.0})
    agent = jnp.array([5, 5])
    pos = jnp.array([[3, 5],     # 0: blocker, 2 north
                     [1, 5],     # 1: target,  4 north  -> hidden by 0
                     [5, 9]])    # 2: target,  4 east   -> unaffected
    active = jnp.array([True, True, True])
    blocks = jnp.array([True, False, False])
    g = np.asarray(_occlusion_gate(agent, pos, active, blocks, p))[0]
    assert g[0] == pytest.approx(1.0), "the blocker itself stays visible"
    assert g[1] == pytest.approx(0.0), "target behind the blocker must be hidden"
    assert g[2] == pytest.approx(1.0), "target on another bearing is unaffected"


def test_occlusion_strength_attenuates_rather_than_hides():
    from src.environment.sensor import _occlusion_gate
    p = params(**{'sensory.visual_sensor_range': 2,
                  'sensory.visual_occlusion_enabled': True,
                  'sensory.visual_occlusion_cone_deg': 15.0,
                  'sensory.visual_occlusion_strength': 0.4})
    agent = jnp.array([5, 5])
    pos = jnp.array([[3, 5], [1, 5]])
    g = np.asarray(_occlusion_gate(agent, pos, jnp.array([True, True]),
                                   jnp.array([True, False]), p))[0]
    assert g[1] == pytest.approx(0.6), "strength 0.4 should leave 60% through"


def test_nothing_blocks_sight_by_default():
    p = params()
    for arr in (p.res_blocks_sight, p.animal_blocks_sight, p.obs_blocks_sight):
        assert not bool(np.asarray(arr).any())
