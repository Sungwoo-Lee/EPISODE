"""Generate the probe scenes for the thirst task -- 9 worlds x 12 scenes (Figure 7 of its page).

WHAT THIS IS FOR. The thirst task (docs/experiments/active/thirst_task/THIRST_TASK.md) trained 18
agents in nine worlds: map 10x10, 15x15 or 20x20, crossed with smell that carries across the whole
map, 5 squares or 3 squares. Every world has one pond and a hydration level. To watch those agents
in the same 12 fixed test scenes as the level-04, thermal and hvsmell probe sweeps (no animal /
hunting predator / chasing rabbit / chasing rabbit with its predator-like odour removed / wandering
rabbit / wandering rabbit that smells like a predator, each at starting injury 0 and 70), each scene
is rebuilt ON TOP OF EACH WORLD (plan docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md, D12
and Revision 2).

HOW EACH FILE IS BUILT. Read the core probe (behavior_probes/core/avoidance/<scene>.yaml), then:
  1. `extends:` the thirst world, so every key the scene does not restate is the trained world's
     value (body, temperature system, water physics, sensors, 59-number observation).
  2. Keep the world's MAP SIZE (D12 ii): height/width, the grass area and each animal's patrol area
     are set to the world's grid. The core layout keeps its absolute coordinates (start [5,5], bush
     [5,2], animal spawn [5,9]), so it sits identically against the north and west walls at every
     size. The core probe's `visualization.local_view_size: 10` is dropped (the world's own value
     is kept).
  3. Animal odour means: the world's own (spread 0). All nine thirst worlds smell like the level-05
     control, so the rule reproduces the core probe vectors exactly -- asserted.
  4. One campfire (the world's own entry) at config [5,3], beside the bush, as in the hvsmell
     scenes: the world is cold, and the bush must be warm and the start cell not.
  5. WATER (Revision 1 finding 4, Revision 2 R2-c): `placement: list` with ONE candidate whose
     top-left is config [8,8] (start + (3,3), the 10x10 level-06 geometry) at every map size; the
     world keeps its own pond size (2x2 / 3x3 / 4x4). `random_start_hydration: false` and
     `start_hydration: <--start-hydration>` (mandatory flag; chosen by the R2.3 calibration).

Run (from any folder; `extends:` targets resolve under configs/ of the checkout that loads them):
  P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
  $P .../thirst/generate_thirst_probes.py --start-hydration S --worlds g10sW ... [--out-root DIR]
  $P .../thirst/generate_thirst_probes.py --start-hydration S --worlds ... [--out-root DIR] --check-only
--check-only loads and asserts the files on disk and writes nothing. The pond is located by
replaying the scene's own reset (scripts/analysis/basic_behaviour/registry.pond_cells), and the
observation layout is compared with each trained run's saved config, found under $BB_DATA_ROOT
when that is set (a git worktree has no results/), else under this checkout.
"""
import argparse
import copy
import glob
import os
import sys

import yaml

# thirst/ -> behavior_probes/ -> experiment/ -> environment/ -> configs/ -> repo root = 5.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 5)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'scripts', 'analysis', 'basic_behaviour'))
os.chdir(_ROOT)

from src.utils.config import dump_config_yaml                       # noqa: E402
from src.environment.config_loader import (                          # noqa: E402
    load_env_config, load_env_params, _thermal_equilibrium)

SRC_DIR = 'configs/environment/experiment/behavior_probes/core/avoidance'
OUT_ROOT = 'configs/environment/experiment/behavior_probes/thirst'
GEN = f'{OUT_ROOT}/generate_thirst_probes.py'
DOC = 'docs/experiments/active/thirst_task/THIRST_TASK.md'
PLAN = 'docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md'
CALIB = 'results/analysis/basic_behaviour/thirst/probes/calibration.json'

# cell -> `extends:` target (THIRST_TASK section 9.1)
WORLDS = {
    'g10sW': 'environment/experiment/basic/06-pond_thirst_10x10',
    'g10s5': 'environment/experiment/thirst/pond_thirst_10x10_smell5',
    'g10s3': 'environment/experiment/thirst/pond_thirst_10x10_smell3',
    'g15sW': 'environment/experiment/thirst/pond_thirst_15x15',
    'g15s5': 'environment/experiment/thirst/pond_thirst_15x15_smell5',
    'g15s3': 'environment/experiment/thirst/pond_thirst_15x15_smell3',
    'g20sW': 'environment/experiment/thirst/pond_thirst_20x20',
    'g20s5': 'environment/experiment/thirst/pond_thirst_20x20_smell5',
    'g20s3': 'environment/experiment/thirst/pond_thirst_20x20_smell3',
}
REACH = {'W': 'smell across the whole map', '5': 'smell reach 5 squares', '3': 'smell reach 3 squares'}


def _no_ch1(v):
    out = list(v)
    out[1] = 0.0
    return out


# scene animal tag -> its odour mean from the world's (predator mean, rabbit mean); the hvsmell rule
SMELL_RULE = {
    'pred': lambda p, r: list(p),
    'rabbit': lambda p, r: list(r),
    'rabbitwander': lambda p, r: list(r),
    'rabbitwander_predsmell': lambda p, r: list(p),
    'rabbit_olfzero': lambda p, r: _no_ch1(p),
}

START_CFG, BUSH_CFG, FIRE_CFG, SPAWN_CFG = (5, 5), (5, 2), (5, 3), (5, 9)    # config, 1-based
POND_TOPLEFT_CFG = (8, 8)                  # start + (3, 3) at every size (Revision 1, finding 4)
A = lambda rc: (rc[0] - 1, rc[1] - 1)      # config (1-based) -> array (0-based)


def world_entries(extends):
    """The world's resolved predator/rabbit means, campfire entry, grid and water block."""
    c = load_env_config(f'configs/{extends}.yaml')
    ents = {e['tag']: e for e in c.get('environment.entities')}
    fires = [o for o in c.get('environment.obstacles') if o['name'] == 'campfire']
    if len(fires) != 1:
        raise ValueError(f"{extends}: expected one campfire entry, found {len(fires)}")
    return dict(pred=ents['pred']['properties'], rabbit=ents['rabbit']['properties'], fire=fires[0],
                H=int(c.get('environment.height')), W=int(c.get('environment.width')),
                water=c.get('water'), view=c.get('visualization.local_view_size'),
                radius=c.get('sensory.sensor_radius'))


def campfire(entry):
    """The world's own campfire entry, pinned to ONE fire at FIRE_CFG (as in the hvsmell scenes)."""
    e = copy.deepcopy(entry)
    for k in ('count_low', 'count_high', 'edge_margin'):
        e.pop(k, None)
    e['count'] = 1
    e['area'] = [list(FIRE_CFG), list(FIRE_CFG)]
    return e


def build(src_path, cell, start_hydration):
    w = world_entries(WORLDS[cell])
    d = yaml.safe_load(open(src_path))
    if d.get('extends') != 'environment/default':
        raise ValueError(f"{src_path}: unexpected extends {d.get('extends')!r}")
    d['extends'] = WORLDS[cell]
    env = d['environment']
    if (env['height'], env['width']) != (10, 10) or list(env['start_pos']) != list(START_CFG):
        raise ValueError(f"{src_path}: core probe is not the 10x10 layout this generator assumes")
    env['height'], env['width'] = w['H'], w['W']
    for la in env['location_areas']:
        if la['type'] == 'grass':
            la['area'] = [[1, 1], [w['H'], w['W']]]
    for e in env['entities']:
        if any(e['properties_std']):
            raise ValueError(f"{src_path}: core probe animal has non-zero odour spread")
        new = SMELL_RULE[e['tag']](w['pred'], w['rabbit'])
        if [float(x) for x in e['properties']] != [float(x) for x in new]:
            raise ValueError(f"{src_path}: {cell} smell rule {new} != core probe {e['properties']} "
                             f"(the thirst worlds are expected to smell like the level-05 control)")
        e['properties'] = new
        if [list(x) for x in e['spawn_area']] != [list(SPAWN_CFG), list(SPAWN_CFG)]:
            raise ValueError(f"{src_path}: unexpected spawn area {e['spawn_area']}")
        e['patrol_area'] = [[1, 1], [w['H'], w['W']]]
    env['obstacles'] = list(env['obstacles']) + [campfire(w['fire'])]
    if any(k in d for k in ('thermal', 'perceptual_noise', 'water')):
        raise ValueError(f"{src_path}: core probe unexpectedly sets thermal/noise/water")
    vis = d.pop('visualization', None)
    if vis not in (None, {'local_view_size': 10}):
        raise ValueError(f"{src_path}: unexpected visualization block {vis}")
    d['water'] = {'placement': 'list', 'candidates': [list(POND_TOPLEFT_CFG)],
                  'random_start_hydration': False, 'start_hydration': float(start_hydration)}
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
# THIRST PROBE -- world `{cell}` ({H}x{W} map, {reach}), scene `{scene}`
#
# One of 9 worlds x 12 scenes built for the thirst task ({doc}), Figure 7 of its Basic
# Behaviour page (plan {plan}). GENERATED -- do not hand-edit; regenerate with
#   /home/vncuser/miniconda3/envs/grid_world_pain/bin/python {gen} \\
#       --start-hydration {S:g} --worlds <cells>
#
# The file `extends:` the trained world, so everything the scene does not restate is the
# trained world's value. Kept from the world: map size {H}x{W}, smell reach, pond size {ph}x{pw},
# water physics, temperature system, 59-number observation, visualization.local_view_size.
#
# SCENE (from {src}; layout coordinates unchanged, grid / grass / patrol area set to the world's map):
{scene_desc}#
# ADDED vs the core probe:
#   - one campfire (the world's own entry) at config [5,3], beside the hiding bush at [5,2]
#     (the world is cold; the bush is warm and survivable, the start cell [5,5] is not);
#   - the pond: one candidate, top-left config [8,8] (start + (3,3)) at every map size;
#   - start hydration FIXED at {S:g} (random_start_hydration: false), chosen by the pre-registered
#     calibration in the plan, section R2.3 ({calib}). Bush time is read only up to the
#     agent's first pond step (plan, section R2.2).
#
# MEASURED at generation (trainer loader + real env reset):
#   observation width {obs}; survivable cells {surv}/{cells}; bush settles {eq_bush:+.2f};
#   start cell settles {eq_agent:+.2f}; pond cells (array, 0-based) {pond}; animal odour {smell}
# ============================================================================
"""


def measure(path):
    """One vmapped reset of 30 seeds (one compile per file): thermal field, pond, start, obstacles."""
    import jax
    import numpy as np
    from src.environment.core import jax_reset
    from src.environment.sensor import get_observation_breakdown

    p = load_env_params(load_env_config(path))
    st = jax.vmap(jax_reset, in_axes=(None, 0))(p, jax.vmap(jax.random.PRNGKey)(np.arange(30)))
    field = np.asarray(st.thermal_field[0])
    eq = _thermal_equilibrium(field, float(p.thermal_k_exchange), float(p.thermal_k_loss),
                              float(p.thermal_k_metabolic), float(p.temperature_setpoint))
    surv = (eq >= float(p.min_temperature)) & (eq <= float(p.max_temperature))
    R = {"water_pos": np.asarray(st.water_pos), "agent_pos": np.asarray(st.agent_pos),
         "hydration": np.asarray(st.hydration, np.float64)}
    R["corner"] = np.zeros(len(R["agent_pos"]), int)
    return dict(params=p, obs=int(sum(get_observation_breakdown(p).values())), eq=eq, surv=surv,
                n_surv=int(surv.sum()), R=R, obs_pos=np.asarray(st.obs_pos),
                obs_active=np.asarray(st.obs_active))


def run_breakdowns(cell):
    """Observation breakdown (ordered) of each trained run of this world, from its saved config."""
    import registry as REG
    from src.environment.sensor import get_observation_breakdown
    runs = sorted(glob.glob(os.path.join(REG.DATA_ROOT, 'results', 'JAX_RecurrentPPO',
                                         f'*_rppo_thirst_{cell}_t*_s42')))
    if len(runs) != 2:
        raise ValueError(f"{cell}: expected 2 trained runs under {REG.DATA_ROOT}, found {runs}")
    out = []
    for r in runs:
        cfg = yaml.safe_load(open(os.path.join(r, 'models', 'config.yaml')))
        out.append((os.path.basename(r), list(get_observation_breakdown(REG.rebuild_params(cfg)).items()),
                    int(cfg['sensory']['sensor_radius']), (int(cfg['environment']['height']),
                                                            int(cfg['environment']['width']))))
    return out


def verify(m, cell, d, path, start_hydration, trained):
    import numpy as np
    from src.environment.sensor import get_observation_breakdown
    fails = []
    pr = m['params']
    w = world_entries(WORLDS[cell])
    H, W = int(pr.height), int(pr.width)
    if m['obs'] != 59:
        fails.append(f"observation width {m['obs']} != 59")
    bd = list(get_observation_breakdown(pr).items())
    for run, tbd, radius, hw in trained:
        if bd != tbd:
            fails.append(f"observation breakdown != run {run}'s saved config")
        if int(pr.sensor_radius) != radius:
            fails.append(f"sensor_radius {int(pr.sensor_radius)} != run {run}'s {radius}")
        if (H, W) != hw:
            fails.append(f"grid {H}x{W} != run {run}'s {hw}")
    if (H, W) != (w['H'], w['W']):
        fails.append(f"grid {H}x{W} != world's {w['H']}x{w['W']}")
    if not bool(m['surv'][A(BUSH_CFG)]) or bool(m['surv'][A(START_CFG)]):
        fails.append(f"thermal contract broken: bush survivable={bool(m['surv'][A(BUSH_CFG)])} "
                     f"start survivable={bool(m['surv'][A(START_CFG)])}")
    hides = np.asarray(pr.obs_hides_agent)
    blocks = np.asarray(pr.obs_blocks_animals)
    if (hides & ~blocks).any():
        fails.append("a hiding obstacle is PERMEABLE to animals")
    if not hides.any():
        fails.append("no hiding obstacle")
    raw = yaml.safe_load(open(path))
    wt = raw.get('water') or {}
    if wt.get('start_hydration') != float(start_hydration) or wt.get('random_start_hydration') is not False:
        fails.append(f"water start written {wt.get('start_hydration')!r} / random "
                     f"{wt.get('random_start_hydration')!r}, flag says {start_hydration}")
    if wt.get('placement') != 'list' or wt.get('candidates') != [list(POND_TOPLEFT_CFG)]:
        fails.append(f"water placement {wt.get('placement')!r} candidates {wt.get('candidates')!r}")
    if float(pr.water_start_hydration) != float(start_hydration) or bool(pr.water_random_start_hydration):
        fails.append("loaded params do not carry the fixed start hydration")
    if not np.allclose(m['R']['hydration'], float(start_hydration)):
        fails.append(f"reset hydration {sorted(set(m['R']['hydration'].tolist()))} != {start_hydration}")
    R = m['R']
    pond = {tuple(x) for x in R['water_pos'][0].tolist()}
    if not all({tuple(x) for x in R['water_pos'][i].tolist()} == pond for i in range(len(R['corner']))):
        fails.append("pond cells differ between seeded resets")
    if len(pond) != int(w['water']['size'][0]) * int(w['water']['size'][1]):
        fails.append(f"pond has {len(pond)} cells, world pond size is {w['water']['size']}")
    fixed = {'start': A(START_CFG), 'bush': A(BUSH_CFG), 'fire': A(FIRE_CFG), 'spawn': A(SPAWN_CFG)}
    hit = [k for k, v in fixed.items() if v in pond]
    if hit:
        fails.append(f"pond overlaps the {hit} cell(s)")
    if not (R['agent_pos'] == np.asarray(A(START_CFG))).all():
        fails.append("agent does not start at config [5,5] in every seeded reset")
    act = m['obs_active']
    occ = [{tuple(m['obs_pos'][i][j]) for j in np.flatnonzero(act[i])} for i in range(len(act))]
    if not all(o == {A(BUSH_CFG), A(FIRE_CFG)} for o in occ):
        fails.append(f"obstacles are not exactly bush [5,2] + fire [5,3]: {occ[0]}")
    ents = d['environment']['entities']
    if ents:
        got = np.asarray(pr.animal_property).reshape(-1, 5)
        want = np.asarray([e['properties'] for e in ents], dtype=float)
        if got.shape[0] < 1 or not np.allclose(got[:len(want)], want):
            fails.append(f"animal_property {got.tolist()} != {want.tolist()}")
        if np.any(np.asarray(pr.animal_property_std)):
            fails.append("animal odour spread is not zero")
    if int(getattr(pr, 'local_view_size', -1)) != int(w['view']):
        fails.append(f"local_view_size {getattr(pr, 'local_view_size', None)} != world's {w['view']}")
    offset = tuple(int(x) for x in min(pond, key=lambda c: (max(abs(c[0] - A(START_CFG)[0]),
                                                              abs(c[1] - A(START_CFG)[1])), c)))
    offset = (offset[0] - A(START_CFG)[0], offset[1] - A(START_CFG)[1])
    return fails, sorted(pond), offset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start-hydration', type=float, required=True,
                    help='fixed start hydration of every scene (plan R2.3 chooses it); no default')
    ap.add_argument('--worlds', nargs='+', required=True, choices=sorted(WORLDS))
    ap.add_argument('--out-root', default=OUT_ROOT,
                    help=f'folder of <cell>/<scene>.yaml (default {OUT_ROOT})')
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()
    S = args.start_hydration
    if not 0.0 < S < 200.0:
        raise ValueError(f"--start-hydration {S} is outside the trained start range (0, 200)")
    scenes = sorted(f[:-5] for f in os.listdir(SRC_DIR)
                    if f.startswith('avoid_') and f.endswith('.yaml'))
    if len(scenes) != 12:
        raise ValueError(f"expected 12 core probes in {SRC_DIR}, found {len(scenes)}")
    n_fail, offsets = 0, {}
    for cell in args.worlds:
        trained = run_breakdowns(cell)
        w = world_entries(WORLDS[cell])
        out_dir = os.path.join(args.out_root, cell)
        os.makedirs(out_dir, exist_ok=True)
        for scene in scenes:
            src = os.path.join(SRC_DIR, f'{scene}.yaml')
            path = os.path.join(out_dir, f'{scene}.yaml')
            d = build(src, cell, S)
            if not args.check_only:
                with open(path, 'w') as fh:
                    dump_config_yaml(d, fh)
            m = measure(path)
            fails, pond, off = verify(m, cell, d, path, S, trained)
            if not args.check_only:
                ents = d['environment']['entities']
                smell = ents[0]['properties'] if ents else 'none (no animal)'
                body = open(path).read()
                with open(path, 'w') as fh:
                    fh.write(HEADER.format(
                        cell=cell, H=w['H'], W=w['W'], reach=REACH[cell[-1]], scene=scene, doc=DOC,
                        plan=PLAN, gen=GEN, S=S, ph=w['water']['size'][0], pw=w['water']['size'][1],
                        src=src, scene_desc=scene_description(src), calib=CALIB, obs=m['obs'],
                        surv=m['n_surv'], cells=w['H'] * w['W'], eq_bush=m['eq'][A(BUSH_CFG)],
                        eq_agent=m['eq'][A(START_CFG)], pond=pond, smell=smell))
                    fh.write(body)
                if yaml.safe_load(open(path)) != d:      # the header is comments only
                    fails.append("file content changed when the header was written")
            offsets.setdefault(off, []).append(f"{cell}/{scene}")
            n_fail += len(fails)
            print(f"  {cell:<6} {scene:<38} obs={m['obs']} surv={m['n_surv']}/{w['H'] * w['W']} "
                  f"bush={m['eq'][A(BUSH_CFG)]:+.2f} pond_offset={off} "
                  f"{'ok' if not fails else 'FAIL: ' + '; '.join(fails)}", flush=True)
    if len(offsets) != 1:
        n_fail += 1
        print(f"  FAIL: nearest-pond-cell offset from the start differs between worlds: "
              f"{ {k: len(v) for k, v in offsets.items()} }")
    else:
        print(f"  nearest-pond-cell offset from the start {next(iter(offsets))} in every scene")
    print(f"\n{'ALL CHECKS PASSED' if not n_fail else f'{n_fail} CHECK(S) FAILED'}")
    return 1 if n_fail else 0


if __name__ == '__main__':
    sys.exit(main())
