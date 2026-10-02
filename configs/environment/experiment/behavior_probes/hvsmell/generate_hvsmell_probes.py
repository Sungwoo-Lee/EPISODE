"""Generate the probe scenes for the single-channel smell hypervigilance study -- 3 worlds x 12 scenes.

WHAT THIS IS FOR. The study (docs/experiments/active/hypervigilance/
SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md) trained 18 agents in three versions of the level-05
world that differ ONLY in how the predator and the rabbit smell. To watch those agents in
the same 12 fixed test scenes the level-04 and thermal-probe sweeps used (no animal / hunting
predator / chasing rabbit / chasing rabbit with its predator-like odour removed / wandering
rabbit / wandering rabbit that smells like a predator, each at starting injury 0 and 70),
each scene has to be rebuilt ON TOP OF EACH WORLD: the agent must meet the world it trained
in (level-05 body, temperature system on, 58-number observation) and the animals in the scene
must smell the way that world's animals smell.

HOW EACH FILE IS BUILT. Read the core probe (behavior_probes/core/avoidance/<scene>.yaml),
then:
  1. `extends:` the study's own world file instead of `environment/default`, so every key the
     scene does not restate is the trained world's value (body mechanics, thermal physics incl.
     the random starting body temperature [-10, +5], sensors, rewards ...).
  2. Replace each animal's odour mean with THAT WORLD's value (spread stays 0, as in every core
     probe), by the rule in SMELL_RULE below. On the control world the rule reproduces the core
     probe's vectors exactly -- asserted.
  3. Append the world's own campfire entry, as ONE fire at config [5,3], beside the bush at
     [5,2] -- the thermal battery's `fire_by_bush` placement. Reason: the trained world is cold
     (ambient -31..-29); a fire-free probe at that ambient freezes the agent inside 100 steps
     (measured 86-99 steps in the thermal battery), and every training episode has 1-3 fires.
     With the fire beside the bush, 8 cells (the ring round the fire, including the bush) are
     survivable; the start cell [5,5] is not, so the agent must move one cell to stay warm.
  4. Everything else in the scene (grid, start [5,5], bush [5,2] that hides the agent AND blocks
     animals, animal spawn [5,9], animal behaviour/speed/damage/detection, no food, max_steps
     100, full nutrition, fixed start injury, `visualization.local_view_size: 10`) is the core
     probe's, untouched.

Run:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      configs/environment/experiment/behavior_probes/hvsmell/generate_hvsmell_probes.py
  ... --check-only   # load + assert the files on disk, write nothing
"""
import argparse
import copy
import os
import sys

import yaml

# hvsmell/ -> behavior_probes/ -> experiment/ -> environment/ -> configs/ -> repo root = 5.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 5)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.utils.config import dump_config_yaml                       # noqa: E402
from src.environment.config_loader import (                          # noqa: E402
    load_env_config, load_env_params, _thermal_equilibrium)

SRC_DIR = 'configs/environment/experiment/behavior_probes/core/avoidance'
OUT_ROOT = 'configs/environment/experiment/behavior_probes/hvsmell'
GEN = f'{OUT_ROOT}/generate_hvsmell_probes.py'
DOC = 'docs/experiments/active/hypervigilance/SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md'

# probe dir name -> (`extends:` target, expected predator mean, expected rabbit mean)
WORLDS = {
    'two_channel': ('environment/experiment/hypervigilance/two_channel_smell_l05_control',
                    [0.0, 0.7, 0.5, 0.0, 0.0], [0.0, 0.5, 0.7, 0.0, 0.0]),
    'single_channel': ('environment/experiment/hypervigilance/single_channel_smell_l05',
                       [0.0, 0.7, 0.0, 0.0, 0.0], [0.0, 0.5, 0.0, 0.0, 0.0]),
    'matched_strength': ('environment/experiment/hypervigilance/matched_strength_smell_l05',
                         [0.0, 0.67, 0.67, 0.0, 0.0], [0.0, 0.53, 0.53, 0.0, 0.0]),
}

WORLD_DESC = {
    'two_channel': 'CONTROL -- level 05 as is: predator smells 0.7 of odour A + 0.5 of odour B, '
                   'rabbit the reverse.',
    'single_channel': 'SINGLE-CHANNEL -- odour B switched off for both animals: predator 0.7 of '
                      'odour A, rabbit 0.5 of odour A.',
    'matched_strength': 'MATCHED-STRENGTH -- both animals smell of the same 1:1 mix: predator '
                        '0.67 + 0.67, rabbit 0.53 + 0.53.',
}


def _no_ch1(v):
    out = list(v)
    out[1] = 0.0
    return out


# Scene animal tag -> the odour mean it gets in a given world, from (pred_mean, rabbit_mean).
# `rabbit_olfzero` is the core probe's "predator odour with the predator-leaning channel 1
# removed" ([0, 0, 0.5, 0, 0] in the control); the same rule per world gives [0, 0, 0, 0, 0]
# single-channel and [0, 0, 0.67, 0, 0] matched. Not part of any pre-stated contrast.
SMELL_RULE = {
    'pred': lambda p, r: list(p),
    'rabbit': lambda p, r: list(r),
    'rabbitwander': lambda p, r: list(r),
    'rabbitwander_predsmell': lambda p, r: list(p),
    'rabbit_olfzero': lambda p, r: _no_ch1(p),
}

FIRE_CFG = (5, 3)                     # config coords, 1-indexed; beside the bush at [5,2]
AGENT, BUSH = (4, 4), (4, 1)          # array coords of config [5,5] and [5,2]


def world_entries(extends):
    """The world's resolved predator/rabbit means and its campfire entry (trainer loader)."""
    c = load_env_config(f'configs/{extends}.yaml')
    ents = {e['tag']: e for e in c.get('environment.entities')}
    fires = [o for o in c.get('environment.obstacles') if o['name'] == 'campfire']
    if len(fires) != 1:
        raise ValueError(f"{extends}: expected one campfire entry, found {len(fires)}")
    return ents['pred']['properties'], ents['rabbit']['properties'], fires[0]


def campfire(entry):
    """The world's own campfire entry, pinned to ONE fire at FIRE_CFG.

    Kept verbatim except the placement keys: `count_low/count_high` -> `count: 1`, `area` ->
    the single cell, and `edge_margin` dropped (an inset applied to `area` at load; on a
    one-cell area it would push the area off the cell).
    """
    e = copy.deepcopy(entry)
    for k in ('count_low', 'count_high', 'edge_margin'):
        e.pop(k, None)
    e['count'] = 1
    e['area'] = [list(FIRE_CFG), list(FIRE_CFG)]
    return e


def build(src_path, world):
    extends, want_p, want_r = WORLDS[world]
    pred, rabbit, fire = world_entries(extends)
    if list(pred) != want_p or list(rabbit) != want_r:
        raise ValueError(f"{world}: world smell {pred}/{rabbit} != expected {want_p}/{want_r}")
    d = yaml.safe_load(open(src_path))
    if d.get('extends') != 'environment/default':
        raise ValueError(f"{src_path}: unexpected extends {d.get('extends')!r}")
    d['extends'] = extends
    for e in d['environment']['entities']:
        if any(e['properties_std']):
            raise ValueError(f"{src_path}: core probe animal has non-zero odour spread")
        new = SMELL_RULE[e['tag']](pred, rabbit)
        if world == 'two_channel' and [float(x) for x in e['properties']] != new:
            raise ValueError(f"{src_path}: control rule {new} != core probe {e['properties']}")
        e['properties'] = new
    d['environment']['obstacles'] = list(d['environment']['obstacles']) + [campfire(fire)]
    if any(k in d for k in ('thermal', 'perceptual_noise')):
        raise ValueError(f"{src_path}: core probe unexpectedly sets thermal/noise")
    return d


def scene_description(path):
    out, on = [], False
    for line in open(path):
        line = line.rstrip('\n')
        if line.startswith('# Avoidance matrix'):
            on = True
        if on:
            if line.startswith('# Study:') or line.startswith('# Full nutrition'):
                break
            out.append('#   ' + line.lstrip('#').strip())
    return '\n'.join(out) + '\n'


HEADER = """# ============================================================================
# HVSMELL PROBE -- world `{world}`, scene `{scene}`
#
# One of 3 worlds x 12 scenes built for the single-channel smell hypervigilance study
# ({doc}). GENERATED -- do not hand-edit; regenerate with
#   /home/vncuser/miniconda3/envs/grid_world_pain/bin/python {gen}
#
# WORLD: {world_desc}
# The file `extends:` that study world, so everything the scene does not restate is the
# trained world's value: level-05 body, temperature system ON (ambient -31..-29, random
# starting body temperature -10..+5, as trained), 58-number observation. The scene's
# animals smell of this world's odour means, spread 0 (as in every core probe).
#
# SCENE (from {src}, unchanged except the odour vector{s_note}):
{scene_desc}#
# ADDED vs the core probe: one campfire (the world's own entry) at config [5,3], beside the
# hiding bush at [5,2]. Without it the cold world freezes the agent inside the 100-step
# probe. The bush is warm (survivable); the start cell [5,5] is not, so the agent has a
# thermal reason to sit near the bush -- a known lift on calm hiding (thermal-probe page).
#
# MEASURED at generation (trainer loader + real env reset):
#   observation width {obs}; survivable cells {surv}/100; bush settles {eq_bush:+.2f};
#   start cell settles {eq_agent:+.2f}; animal odour {smell}
# ============================================================================
"""


def measure(path):
    import jax
    import numpy as np
    from src.environment.wrapper import ParallelEnv

    p = load_env_params(load_env_config(path))
    state, obs = ParallelEnv(p).reset(jax.random.PRNGKey(0), 1)
    field = np.asarray(state.thermal_field[0])
    eq = _thermal_equilibrium(field, float(p.thermal_k_exchange), float(p.thermal_k_loss),
                              float(p.thermal_k_metabolic), float(p.temperature_setpoint))
    surv = (eq >= float(p.min_temperature)) & (eq <= float(p.max_temperature))
    return dict(params=p, obs=int(obs.shape[-1]), eq=eq, surv=surv, n_surv=int(surv.sum()))


def verify(m, world, d):
    import numpy as np
    fails = []
    pr = m['params']
    if m['obs'] != 58:
        fails.append(f"observation width {m['obs']} != 58")
    if m['n_surv'] != 8 or not bool(m['surv'][BUSH]) or bool(m['surv'][AGENT]):
        fails.append(f"thermal contract broken: surv={m['n_surv']} bush={bool(m['surv'][BUSH])} "
                     f"start={bool(m['surv'][AGENT])}")
    hides = np.asarray(pr.obs_hides_agent)
    blocks = np.asarray(pr.obs_blocks_animals)
    if (hides & ~blocks).any():
        fails.append("a hiding obstacle is PERMEABLE to animals")
    if not hides.any():
        fails.append("no hiding obstacle")
    if int(getattr(pr, 'local_view_size', 0)) != 10:
        fails.append("visualization.local_view_size != 10")
    ents = d['environment']['entities']
    if ents:
        got = np.asarray(pr.animal_property).reshape(-1, 5)
        want = np.asarray([e['properties'] for e in ents], dtype=float)
        if got.shape[0] < 1 or not np.allclose(got[:len(want)], want):
            fails.append(f"animal_property {got.tolist()} != {want.tolist()}")
        if np.any(np.asarray(pr.animal_property_std)):
            fails.append("animal odour spread is not zero")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()
    scenes = sorted(f[:-5] for f in os.listdir(SRC_DIR)
                    if f.startswith('avoid_') and f.endswith('.yaml'))
    if len(scenes) != 12:
        raise ValueError(f"expected 12 core probes in {SRC_DIR}, found {len(scenes)}")
    n_fail = 0
    for world in WORLDS:
        out_dir = os.path.join(OUT_ROOT, world)
        os.makedirs(out_dir, exist_ok=True)
        for scene in scenes:
            src = os.path.join(SRC_DIR, f'{scene}.yaml')
            path = os.path.join(out_dir, f'{scene}.yaml')
            d = build(src, world)
            if not args.check_only:
                with open(path, 'w') as fh:
                    dump_config_yaml(d, fh)
            m = measure(path)
            if not args.check_only:
                ents = d['environment']['entities']
                smell = ents[0]['properties'] if ents else 'none (no animal)'
                body = open(path).read()
                with open(path, 'w') as fh:
                    fh.write(HEADER.format(
                        world=world, scene=scene, doc=DOC, gen=GEN, world_desc=WORLD_DESC[world],
                        src=src, s_note=(' -- identical here' if world == 'two_channel' else
                                         '; the text below quotes the CONTROL odours, this file\'s are on\n#   the "animal odour" line at the end of this header'),
                        scene_desc=scene_description(src), obs=m['obs'], surv=m['n_surv'],
                        eq_bush=m['eq'][BUSH], eq_agent=m['eq'][AGENT], smell=smell))
                    fh.write(body)
                m = measure(path)
            fails = verify(m, world, yaml.safe_load(open(path)))
            n_fail += len(fails)
            print(f"  {world:<17} {scene:<38} obs={m['obs']} surv={m['n_surv']}/100 "
                  f"bush={m['eq'][BUSH]:+.2f} {'ok' if not fails else 'FAIL: ' + '; '.join(fails)}")
    print(f"\n{'ALL CHECKS PASSED' if not n_fail else f'{n_fail} CHECK(S) FAILED'}")
    return 1 if n_fail else 0


if __name__ == '__main__':
    sys.exit(main())
