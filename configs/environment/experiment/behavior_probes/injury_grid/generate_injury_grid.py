"""Generate the INJURY-GRID probe battery — three scenes at ten starting injuries, core + thermal.

WHY THIS EXISTS. The core avoidance probes start the agent at injury 0 or 70 only. The
injury-dependence analysis (docs/experiments/active/modulator_clues/INJURY_DEPENDENCE_PLAN.md,
workstream A) needs the whole dose-response: how hiding changes as the starting injury rises
0, 10, ... 90. This script writes those scenes without restating any of them.

WHAT IT READS AND WRITES.
  source   behavior_probes/core/avoidance/avoid_{none,pred,rabbitwander}_inj00.yaml
  core/                  <scene>_injNN.yaml   30 files, observation 52 (levels 02-04)
  <arm>_<battery>/       <scene>_injNN.yaml   8 x 30 files, observation 58 (levels 05/06),
                         the four thermal arms x {clean, noise_matched} of the thermal battery

Each core file is the source probe with ONLY `body.start_injury_low` and `body.start_injury_high`
set to the level (the start is drawn uniformly between the two, so both must be set). Each thermal
file is that core file passed through the thermal generator's own `build()`, so a thermal arm here
is byte-for-byte the recipe the existing thermal battery uses.

THE CHASING RABBIT IS NOT INCLUDED in those folders. Once it catches up it stays on the agent's cell
(Known Bugs, glued rabbit, open), so its within-reach measure is time out of cover read backwards.

--chasing-rabbit (added 2026-10-06) writes the chasing-rabbit scene at the same ten injuries into two
SEPARATE folders, chase_core/ (observation 52) and chase_neutral_clean/ (58, thermal arm neutral,
clean battery), for the cross-run page's most-effective-conditions figures, which read bush dwell
only (not the within-reach measure the bug distorts). Separate folders, because the existing sweeps
point at core/ and <arm>_<battery>/ with `conditions: all`: a file added there would silently join
their next run.

Run from anywhere:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      configs/environment/experiment/behavior_probes/injury_grid/generate_injury_grid.py
  ... --check-only   # load + assert the files on disk, write nothing
  ... --chasing-rabbit [--check-only]   # only the chase_core/ and chase_neutral_clean/ folders
"""
import argparse
import importlib.util
import os
import sys

import yaml

# injury_grid/ -> behavior_probes/ -> experiment/ -> environment/ -> configs/ -> repo root = 5.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 5)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.utils.config import dump_config_yaml                       # noqa: E402

SRC_DIR = 'configs/environment/experiment/behavior_probes/core/avoidance'
OUT_ROOT = 'configs/environment/experiment/behavior_probes/injury_grid'
GEN = f'{OUT_ROOT}/generate_injury_grid.py'
PLAN = 'docs/experiments/active/modulator_clues/INJURY_DEPENDENCE_PLAN.md'
SCENES = ('avoid_none', 'avoid_pred', 'avoid_rabbitwander')
LEVELS = tuple(range(0, 100, 10))

_spec = importlib.util.spec_from_file_location(
    'thermal_gen', os.path.join(_ROOT, 'configs/environment/experiment/behavior_probes/thermal/'
                                       'generate_thermal_probes.py'))
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

HEADER = """# ============================================================================
# INJURY-GRID PROBE — {scene}, start injury {level}, {variant}
# GENERATED — do not hand-edit. Regenerate with:
#   /home/vncuser/miniconda3/envs/grid_world_pain/bin/python {gen}
# Source scene: {src}
# The only change from the source is body.start_injury_low = body.start_injury_high = {level}{thermal}.
# Observation width {obs}.
# Plan: {plan}
#
# The source probe's own scene description:
{scene_desc}# ============================================================================
"""


def core_dict(src, level):
    d = yaml.safe_load(open(src))
    body = d['body']
    for k in ('random_start_injury', 'start_injury_low', 'start_injury_high'):
        if k not in body:
            raise ValueError(f"{src}: body.{k} missing -- the source no longer sets the start injury")
    body['start_injury_low'] = level
    body['start_injury_high'] = level
    return d


def write(path, d, header):
    with open(path, 'w') as fh:
        dump_config_yaml(d, fh)
    body = open(path).read()
    with open(path, 'w') as fh:
        fh.write(header)
        fh.write(body)


def check(path, level, want_obs):
    """Load the file the way training/eval load it and assert the grid's contract."""
    import numpy as np
    m = T.measure(path)
    p = m['params']
    fails = []
    if m['obs'] != want_obs:
        fails.append(f"observation width {m['obs']} != {want_obs}")
    lo, hi = float(p.start_injury_low), float(p.start_injury_high)
    if (lo, hi) != (float(level), float(level)):
        fails.append(f"start injury loaded as [{lo}, {hi}], expected [{level}, {level}]")
    leaky = np.flatnonzero(np.asarray(p.obs_hides_agent) & ~np.asarray(p.obs_blocks_animals))
    if leaky.size:
        fails.append(f"hiding obstacle(s) {leaky.tolist()} are PERMEABLE")
    if int(getattr(p, 'local_view_size', 0)) != 10:
        fails.append("visualization.local_view_size != 10")
    return m, fails


def chasing_rabbit(check_only, noise_block):
    """avoid_rabbit at ten injuries: chase_core/ (thermal off) and chase_neutral_clean/ (neutral, clean)."""
    scene, n_fail, n_files = 'avoid_rabbit', 0, 0
    src = os.path.join(SRC_DIR, f'{scene}_inj00.yaml')
    core_dir, th_dir = os.path.join(OUT_ROOT, 'chase_core'), os.path.join(OUT_ROOT, 'chase_neutral_clean')
    os.makedirs(core_dir, exist_ok=True)
    os.makedirs(th_dir, exist_ok=True)
    for level in LEVELS:
        name = f'{scene}_inj{level:02d}'
        path = os.path.join(core_dir, f'{name}.yaml')
        if not check_only:
            write(path, core_dict(src, level), HEADER.format(
                scene=scene, level=level, variant='core (thermal off), chasing rabbit', gen=GEN, src=src,
                thermal='', obs=52, plan=PLAN, scene_desc=T.scene_description(src)))
        _, fails = check(path, level, 52)
        tpath = os.path.join(th_dir, f'{name}.yaml')
        if not check_only:
            d = T.build(path, 'neutral', 'clean', noise_block)
            write(tpath, d, '')
            m0 = T.measure(tpath)
            write(tpath, d, HEADER.format(
                scene=scene, level=level, variant='thermal neutral, clean, chasing rabbit', gen=GEN, src=src,
                obs=m0['obs'], plan=PLAN, scene_desc=T.scene_description(src),
                thermal=", then the thermal battery's build() for arm 'neutral', battery 'clean'"))
        m, tfails = check(tpath, level, 58)
        tfails += T.verify(tpath, 'neutral', m)
        n_fail += len(fails) + len(tfails); n_files += 2
        print(f"  {name:<22} core {'ok' if not fails else 'FAIL: ' + '; '.join(fails)}   "
              f"neutral_clean {'ok' if not tfails else 'FAIL: ' + '; '.join(tfails)}")
    print(f"\n{n_files} files; {'ALL CHECKS PASSED' if not n_fail else f'{n_fail} CHECK(S) FAILED'}")
    return 1 if n_fail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--chasing-rabbit', action='store_true',
                    help='write/check only chase_core/ and chase_neutral_clean/ (see the module docstring)')
    args = ap.parse_args()
    noise_block = T.read_noise_block()
    if args.chasing_rabbit:
        return chasing_rabbit(args.check_only, noise_block)
    n_fail = n_files = 0

    core_dir = os.path.join(OUT_ROOT, 'core')
    os.makedirs(core_dir, exist_ok=True)
    for scene in SCENES:
        src = os.path.join(SRC_DIR, f'{scene}_inj00.yaml')
        for level in LEVELS:
            name = f'{scene}_inj{level:02d}'
            path = os.path.join(core_dir, f'{name}.yaml')
            if not args.check_only:
                write(path, core_dict(src, level), HEADER.format(
                    scene=scene, level=level, variant='core (thermal off)', gen=GEN, src=src,
                    thermal='', obs=52, plan=PLAN, scene_desc=T.scene_description(src)))
            _, fails = check(path, level, 52)
            n_fail += len(fails); n_files += 1
            print(f"  core                        {name:<26} {'ok' if not fails else 'FAIL: ' + '; '.join(fails)}")

            for arm in T.ARMS:
                for battery in T.BATTERIES:
                    out_dir = os.path.join(OUT_ROOT, f'{arm}_{battery}')
                    os.makedirs(out_dir, exist_ok=True)
                    tpath = os.path.join(out_dir, f'{name}.yaml')
                    if not args.check_only:
                        d = T.build(path, arm, battery, noise_block)
                        write(tpath, d, '')
                        m0 = T.measure(tpath)
                        write(tpath, d, HEADER.format(
                            scene=scene, level=level, variant=f'thermal {arm}, {battery}', gen=GEN,
                            src=src, obs=m0['obs'], plan=PLAN, scene_desc=T.scene_description(src),
                            thermal=f', then the thermal battery\'s build() for arm {arm!r}, '
                                    f'battery {battery!r}'))
                    m, fails = check(tpath, level, 58)
                    fails += T.verify(tpath, arm, m)
                    n_fail += len(fails); n_files += 1
                    if fails:
                        print(f"  {arm + '_' + battery:<27} {name:<26} FAIL: {'; '.join(fails)}")
    print(f"\n{n_files} files; {'ALL CHECKS PASSED' if not n_fail else f'{n_fail} CHECK(S) FAILED'}")
    return 1 if n_fail else 0


if __name__ == '__main__':
    sys.exit(main())
