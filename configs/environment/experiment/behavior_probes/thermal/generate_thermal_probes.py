"""Generate the THERMAL behaviour-probe battery — 4 thermal arms x 2 noise batteries x 12 scenes.

WHY THIS EXISTS. The 12 probes in `behavior_probes/core/avoidance/` produce a 52-number
observation with the body-temperature system switched OFF. Agents trained on basic levels
05 and 06 read a 58-number observation with it ON, so they cannot be measured on those
probes at all. Switching thermal on at the world's inherited ambient does not fix it: the
probe scenes contain no heat source, the body settles near -20 against a survivable floor
of -15, and the agent freezes to death inside the 100-step probe window. This script emits
probe worlds whose thermal channel is habitable, so bush-hiding can actually be measured.

WHY IT READS THE CORE PROBES INSTEAD OF RESTATING THE SCENE. The scientific value of this
battery is that its 12 scenes are the SAME 12 scenes levels 02/03/04 are measured on. Each
output is the corresponding core probe's parsed YAML with a thermal block (and, on the fire
arms, one campfire) added -- so a future edit to a core probe propagates here on the next
regeneration rather than silently forking. Everything else is carried through untouched:
the grid, the bush, the animal, the injury level, the `body:` block, and
`visualization.local_view_size: 10` (the full-arena video fix of 2026-09-23).

THE FOUR ARMS, ALL MEASURED THROUGH `load_env_config` + `ParallelEnv.reset`:
  neutral       ambient  0.0   -> body settles  +0.00, 100/100 cells survivable
  cool          ambient -7.5   -> body settles  -5.00, 100/100 cells survivable
  fire_by_bush  ambient inherited [-31,-29], campfire at config [5,3] (beside the bush)
                -> 8/100 survivable; the BUSH settles +6.07 and is survivable
  fire_away     ambient inherited [-31,-29], campfire at config [2,5] (far from the bush)
                -> 8/100 survivable; the BUSH settles -20.24 and is LETHAL

OFF-DISTRIBUTION BY NECESSITY. At equilibrium the thermoceptor (`field - body_temp`) reads
exactly one third of the ambient and the body sits at two thirds of it, so the training
world's away-from-fire reading of about -10 and survival for 100 steps are mutually
exclusive. Every habitable probe is therefore off-distribution on the thermal channel.
That is the nature of level 05, not a defect this script can engineer away -- which is
precisely why all four arms ship and the comparison is read ACROSS them.

Run from anywhere:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      configs/environment/experiment/behavior_probes/thermal/generate_thermal_probes.py
  ... --check-only   # load + assert without rewriting the YAML
"""
import argparse
import copy
import os
import sys
import textwrap

import yaml

# thermal/ -> behavior_probes/ -> experiment/ -> environment/ -> configs/ -> repo root = 5.
# The repo-root depth hazard in docs/environment/SCRIPTS_DEPENDENCY_MAP.md: a wrong count
# chdirs into a subdirectory and every relative path below silently misses.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 5)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.utils.config import dump_config_yaml                       # noqa: E402
from src.environment.config_loader import (                          # noqa: E402
    load_env_config, load_env_params, _thermal_equilibrium)

SRC_DIR = 'configs/environment/experiment/behavior_probes/core/avoidance'
OUT_ROOT = 'configs/environment/experiment/behavior_probes/thermal'
GEN = f'{OUT_ROOT}/generate_thermal_probes.py'
NOISE_SRC = 'configs/environment/experiment/basic/06-sensory_noise_10x10.yaml'
DOC = 'docs/experiments/active/behavior_measures/thermal_probe_battery_bush_hiding.md'

# Config coordinates are 1-indexed against the numpy array: config [R, C] is array
# (R-1, C-1). In every core probe the agent starts at config [5,5], the hiding bush sits
# at config [5,2] and the animal spawns at config [5,9].
AGENT_CFG, BUSH_CFG = (5, 5), (5, 2)
AGENT, BUSH = (AGENT_CFG[0] - 1, AGENT_CFG[1] - 1), (BUSH_CFG[0] - 1, BUSH_CFG[1] - 1)


def campfire(r, c):
    """Level 05's campfire entry verbatim, placed at config [r, c].

    `temperature_ratio` is the FIXED calibrated 11, not a range: a range cannot meet the
    'first step onto the fire is survivable' target in every episode (level 05's own note).
    The fire shares the obstacle visual channel with rock and bush on purpose -- feeling it
    is the only way to tell it from a rock, which is the point of the thermoceptor.
    """
    return {
        'name': 'campfire',
        'count': 1,
        'area': [[r, c], [r, c]],
        'temperature_ratio': [11, 11],
        'blocking': False,
        'blocks_sight': False,
        'damage': [0.0, 0.0],
        'nociception_intensity': 0.0,
        'properties': [0.0, 0.0, 0.0, 0.0, 0.0],
        'properties_std': [0.0, 0.0, 0.0, 0.0, 0.0],
        'visual_properties': [1.0],
        'visual_properties_std': [0.0],
    }


# name -> (default_temp override or None = inherit [-31,-29], campfire config cell or None,
#          expected survivable-cell count, expected bush survivability, one-line description)
ARMS = {
    'neutral': (
        [0.0, 0.0], None, 100, True,
        'Ambient 0.0 -- the thermal channel is switched on but carries no gradient. The body '
        'pins at +0.00 forever and the thermal term of the drive is exactly zero, so the drive '
        'reduces to the same two-axis form the level-04 probes use.'),
    'cool': (
        [-7.5, -7.5], None, 100, True,
        'Ambient -7.5 -- uniformly cool but survivable everywhere. The body settles at -5.00 '
        'and the thermal axis contributes a CONSTANT -33.3 in satiation units, a third of the '
        'full hunger scale, so rewards here are not numerically comparable with level 04.'),
    'fire_by_bush': (
        None, (5, 3), 8, True,
        "Inherited cold ambient [-31,-29] with one campfire beside the bush (config [5,3]). "
        'Only the 8 cells around the fire are survivable -- and the BUSH is one of them, so the '
        'agent can hide AND stay warm. Hiding is free.'),
    'fire_away': (
        None, (2, 5), 8, False,
        "Inherited cold ambient [-31,-29] with one campfire far from the bush (config [2,5]). "
        'The 8 survivable cells ring the fire; the BUSH IS LETHAL. Hiding costs the agent its '
        'life, which is the sharp test of parked-in-the-bush versus conditional hiding.'),
}

BATTERIES = ('clean', 'noise_matched')

HEADER = """# ============================================================================
# THERMAL BEHAVIOUR PROBE -- arm `{arm}`, battery `{battery}`, scene `{scene}`
#
# WHAT THIS IS. One cell of a 4 x 2 x 12 probe battery (4 thermal arms x 2 noise
# batteries x the 12 core avoidance scenes) built so that agents trained on basic
# levels 05 and 06 -- the ones with body temperature switched on, observation width
# 58 -- can be measured on BUSH HIDING. The existing core battery is width 52 with
# thermal off and does not fit those agents at all.
#
# THIS ARM -- {arm}:
{arm_desc}#
# VERIFIED by loading this file through `load_env_config` + `load_env_params` and
# resetting the real `ParallelEnv` (equilibrium from
# `config_loader._thermal_equilibrium`, the loader's own fixed point
# T* = (k_ex*T_field + k_loss*setpoint + k_met) / (k_ex + k_loss)):
#   observation width           {obs}
#   survivable cell count       {surv}/100   (equilibrium inside [{lo:g}, {hi:g}])
#   agent start, config [5,5]   settles {eq_agent:+.2f}  -- {agent_verdict}
#   hiding bush, config [5,2]   settles {eq_bush:+.2f}  -- {bush_verdict}
#   thermal field range         [{f_lo:+.2f}, {f_hi:+.2f}]
{fire_line}#
# OFF-DISTRIBUTION ON THE THERMAL CHANNEL, BY NECESSITY -- NOT A DEFECT.
# At equilibrium the thermoceptor reads `field - body_temp` = exactly one third of the
# ambient, and the body sits at two thirds of it. In the level-05 training world the
# ambient is [-31,-29], so the away-from-fire thermoceptor reading is about -10 and the
# body settles near -20 -- below the survivable floor of -15, which is why an agent in a
# fire-free probe at that ambient freezes after roughly 86-99 steps, inside the 100-step
# probe window. Reproducing the training-world thermoceptor reading and surviving the
# probe are therefore mutually exclusive. Every habitable probe is off-distribution on
# this channel; the response is to ship all four arms and read the result ACROSS them
# rather than to trust any single one.
#
# NOISE BATTERY -- {battery}:
{battery_desc}#
# SCENE -- carried through unchanged from the core probe
#   {src}
# whose own header describes it as:
{scene_desc}#
# GENERATED -- do not hand-edit. Regenerate with:
#   /home/vncuser/miniconda3/envs/grid_world_pain/bin/python {gen}
# The scene, the `body:` block, the injury level and `visualization.local_view_size: 10`
# (the full-arena video fix of 2026-09-23) all come from the source probe, so an edit
# there propagates here on the next regeneration instead of forking.
#
# Design doc: {doc}
# ============================================================================
"""

BATTERY_DESC = {
    'clean': (
        'no `perceptual_noise` block at all, so the disabled block in `environment/default` '
        'is inherited. This is the battery for level-05 agents (which never trained with '
        'perceptual noise) and is also the cross-level-comparable set for level 06.'),
    'noise_matched': (
        "level 06's `perceptual_noise` block verbatim -- olfaction sigma 0.15 with "
        'injury_noise_scale 4.0 and visual 0.1 with 2.0 (both injury-gated), and satiation, '
        'interoceptive_nociception and extero_nociception pinned explicitly clean at sigma '
        '0.0. Level-06 agents only.'),
}


def read_noise_block():
    """Level 06's `perceptual_noise` block, read as raw YAML (no `extends:` resolution).

    Read verbatim from the level-06 file rather than from resolved params so that what
    lands in the probe is textually the same block the agent trained under. Levels 03/04/05
    declare no `perceptual_noise`, so this block deep-merges onto `environment/default`'s in
    exactly the same way here as it does there -- asserted in `verify()`.
    """
    raw = yaml.safe_load(open(NOISE_SRC))
    if 'perceptual_noise' not in raw:
        raise ValueError(f"{NOISE_SRC} no longer declares a `perceptual_noise` block")
    return copy.deepcopy(raw['perceptual_noise'])


def scene_description(path):
    """The source probe's own scene paragraph, re-commented for the generated header.

    Spans the lines from `# Avoidance matrix` to `# Study:` inclusive -- the part of the
    core header that describes THIS scene, as opposed to the schema-regeneration preamble
    every core probe shares.
    """
    out, on = [], False
    for line in open(path):
        line = line.rstrip('\n')
        if line.startswith('# Avoidance matrix'):
            on = True
        if on:
            out.append('#   ' + line.lstrip('#').strip())
            if line.startswith('# Study:'):
                break
    if not out:
        raise ValueError(f"no scene-description block found in {path}")
    return '\n'.join(out) + '\n'


def build(src_path, arm, battery, noise_block):
    """The source probe's YAML plus a thermal block, a campfire, and maybe noise."""
    d = yaml.safe_load(open(src_path))
    temp, fire, _, _, _ = ARMS[arm]

    # `thermal.enabled` is the gate; every other thermal key is read only when it is true.
    # `default_temp` is the ONLY other key any arm touches -- sigma, the k's, the setpoint,
    # min/max_temperature, grid_range, relative and body_temp_observable all come through
    # `environment/default` so this battery tracks the live schema instead of a snapshot.
    d['thermal'] = {'enabled': True}
    if temp is not None:
        d['thermal']['default_temp'] = list(temp)

    if fire is not None:
        # `Config.merge` REPLACES lists wholesale, so the bush has to be restated alongside
        # the campfire or it vanishes. It is restated by construction here: the list is the
        # source probe's own obstacle list with the campfire appended.
        d['environment']['obstacles'] = list(d['environment']['obstacles']) + [campfire(*fire)]

    if battery == 'noise_matched':
        d['perceptual_noise'] = copy.deepcopy(noise_block)
    return d


def measure(path):
    """Load the written config the way training and eval load it, and reset the real env."""
    import jax
    import numpy as np
    from src.environment.wrapper import ParallelEnv

    p = load_env_params(load_env_config(path))
    state, obs = ParallelEnv(p).reset(jax.random.PRNGKey(0), 1)
    field = np.asarray(state.thermal_field[0])
    eq = _thermal_equilibrium(field, float(p.thermal_k_exchange), float(p.thermal_k_loss),
                              float(p.thermal_k_metabolic), float(p.temperature_setpoint))
    lo, hi = float(p.min_temperature), float(p.max_temperature)
    surv = (eq >= lo) & (eq <= hi)
    return dict(params=p, obs=int(obs.shape[-1]), field=field, eq=eq, surv=surv,
                lo=lo, hi=hi, n_surv=int(surv.sum()),
                cells=sorted((int(r) + 1, int(c) + 1) for r, c in zip(*np.where(surv))))


def _wrap(text, width=86):
    """Re-flow a prose paragraph into `# `-prefixed comment lines."""
    return '\n'.join('#   ' + ln for ln in textwrap.wrap(' '.join(text.split()), width)) + '\n'


def header_for(arm, battery, scene, src, m):
    import numpy as np
    fire_line = ''
    if ARMS[arm][1] is not None:
        fr, fc = np.unravel_index(int(np.argmax(m['field'])), m['field'].shape)
        fire_line = (f"#   fire core, config [{fr + 1},{fc + 1}]  settles {m['eq'][fr, fc]:+.2f}"
                     f"  -- lethal, as the loader's thermal-structure check requires\n"
                     f"#   the survivable cells        "
                     f"{', '.join(str(list(c)) for c in m['cells'])}\n")
    return HEADER.format(
        arm=arm, battery=battery, scene=scene, arm_desc=_wrap(ARMS[arm][4]),
        obs=m['obs'], surv=m['n_surv'], lo=m['lo'], hi=m['hi'],
        eq_agent=m['eq'][AGENT], eq_bush=m['eq'][BUSH],
        agent_verdict='survivable' if m['surv'][AGENT] else 'LETHAL, the agent must move',
        bush_verdict='survivable, hiding is free' if m['surv'][BUSH]
                     else 'LETHAL, hiding costs the agent its life',
        f_lo=float(m['field'].min()), f_hi=float(m['field'].max()),
        fire_line=fire_line, battery_desc=_wrap(BATTERY_DESC[battery]),
        src=src, scene_desc=scene_description(src), gen=GEN, doc=DOC)


def verify(path, arm, m):
    """Assert the written config matches the arm's measured contract. Returns failures."""
    _, _, want_surv, want_bush, _ = ARMS[arm]
    fails = []
    if m['obs'] != 58:
        fails.append(f"observation width {m['obs']} != 58")
    if m['n_surv'] != want_surv:
        fails.append(f"survivable cells {m['n_surv']} != {want_surv}")
    if bool(m['surv'][BUSH]) != want_bush:
        fails.append(f"bush survivable {bool(m['surv'][BUSH])} != {want_bush} "
                     f"(settles {m['eq'][BUSH]:+.2f})")

    # A HIDING BUSH MUST ALSO BLOCK ANIMALS. `blocks_animals` is read with a fallback of
    # False (config_loader.py:1888) and every probe redeclares `obstacles:`, which
    # `Config.merge` replaces wholesale -- so a source probe that omits the key yields a
    # PERMEABLE bush here. A predator can then stand on the hiding cell and bite the hidden
    # agent, which was impossible in every world these agents trained in, and which corrupts
    # the exact quantity this battery exists to measure. Caught by env-config-reviewer
    # 2026-09-23 after it had already shipped into a measured sweep; asserted from now on so
    # it cannot come back through a source-probe edit.
    import numpy as _np
    pr = m['params']
    hides = _np.asarray(pr.obs_hides_agent)
    blocks = _np.asarray(pr.obs_blocks_animals)
    leaky = _np.flatnonzero(hides & ~blocks)
    if leaky.size:
        fails.append(f"hiding obstacle(s) at slot(s) {leaky.tolist()} are PERMEABLE "
                     f"(hides_agent true, blocks_animals false) -- fix the source probe")

    # The full-arena video fix. Without it the recorded episode draws a 5x5 window and the
    # chase leaves frame, which is what made the hiding videos unreadable.
    if int(getattr(pr, 'local_view_size', 0)) != 10:
        fails.append("visualization.local_view_size != 10 -- the full-arena video fix is missing")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true',
                    help='load and assert the configs already on disk; write nothing')
    args = ap.parse_args()

    scenes = sorted(f[:-5] for f in os.listdir(SRC_DIR) if f.startswith('avoid_')
                    and f.endswith('.yaml'))
    if len(scenes) != 12:
        raise ValueError(f"expected 12 core probes in {SRC_DIR}, found {len(scenes)}")
    noise_block = read_noise_block()

    n_fail = 0
    for arm in ARMS:
        for battery in BATTERIES:
            out_dir = os.path.join(OUT_ROOT, f'{arm}_{battery}')
            os.makedirs(out_dir, exist_ok=True)
            for scene in scenes:
                src = os.path.join(SRC_DIR, f'{scene}.yaml')
                path = os.path.join(out_dir, f'{scene}.yaml')
                if not args.check_only:
                    d = build(src, arm, battery, noise_block)
                    # Written body-first, header-second: the header quotes numbers that can
                    # only be measured by loading the file, so the file has to exist first.
                    with open(path, 'w') as fh:
                        dump_config_yaml(d, fh)
                m = measure(path)
                fails = verify(path, arm, m)
                if not args.check_only:
                    body = open(path).read()
                    with open(path, 'w') as fh:
                        fh.write(header_for(arm, battery, scene, src, m))
                        fh.write(body)
                    m = measure(path)          # re-measure the FINAL file on disk
                    fails = verify(path, arm, m)
                n_fail += len(fails)
                status = 'ok' if not fails else 'FAIL: ' + '; '.join(fails)
                print(f"  {arm:<13} {battery:<13} {scene:<38} obs={m['obs']} "
                      f"surv={m['n_surv']:>3}/100 bush={m['eq'][BUSH]:+7.2f} {status}")
    print(f"\n{'ALL CHECKS PASSED' if not n_fail else f'{n_fail} CHECK(S) FAILED'}")
    return 1 if n_fail else 0


if __name__ == '__main__':
    sys.exit(main())
