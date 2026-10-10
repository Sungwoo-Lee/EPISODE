"""One behaviour-test CSV row from one checkpoint x scene cell -- the single place the row
arithmetic lives (plan SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md, F2).

Called by the on-node finisher (finish_cells.py), by run_sweep.py's `_measure_cell` (kept for
scripts/eval/experiment_eval_checkpoint.py), by the from-archives recovery path and by the gates.
The arithmetic is moved verbatim from the former `run_sweep._measure_cell`: the 11 measures of
every episode, `np.nanmean` across episodes (warnings silenced), step in millions to 4 decimals,
each mean to 4 decimals or "" if not finite.

`cell` may be a legacy cell folder or a `<step>.zip` archive (src/utils/episode_bundle.py).
Episodes are read in `EB.members` order, which equals `sorted(folder.glob(pattern))`.

Import contract: the caller puts the repo root and `scripts/behavior_measures` on sys.path
(run_sweep.py and finish_cells.py both do; finish_cells.py gets the repo root as a mandatory
argument, so a copy of this file stored in a provenance folder still finds the repo).
"""
import warnings
from pathlib import Path

import numpy as np

from avoidance_stats_heatmap import episode_measures, KEYS  # noqa: E402 (bare-name import, see SCRIPTS_DEPENDENCY_MAP.md)
import src.utils.episode_bundle as EB

HEAD = ["step", "step_M"] + KEYS
EPISODE_PATTERN = "**/episode_*.rec.gz"


def cell_row(step: int, episodes):
    """CSV row `[step, step_M, <11 measures>]` from an iterable of episode payloads (the dicts
    `load_episode` returns), or None if there are none."""
    rows = [episode_measures(ep) for ep in episodes]
    if not rows:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        agg = {k: float(np.nanmean([row[k] for row in rows])) for k in KEYS}
    return [step, f"{step / 1e6:.4f}"] + [
        ("" if not np.isfinite(agg[k]) else f"{agg[k]:.4f}") for k in KEYS
    ]


def measure_cell_n(cell, step=None):
    """(step, row, n_episodes) for one cell (folder or `.zip`), or None if it holds no recordings.
    `step` defaults to the cell's name (`10000021` or `10000021.zip`); pass it explicitly for a
    staging folder whose name is not the step."""
    cell = Path(cell)
    if step is None:
        name = cell.name[:-len(EB.BUNDLE_SUFFIX)] if cell.name.endswith(EB.BUNDLE_SUFFIX) else cell.name
        step = int(name)
    names = EB.members(cell, EPISODE_PATTERN)
    if not names:
        return None
    row = cell_row(step, (EB.load_recording(cell, n) for n in names))
    return step, row, len(names)


def measure_cell(cell, step=None):
    """(step, row) for one cell, or None -- the former `run_sweep._measure_cell` contract."""
    r = measure_cell_n(cell, step)
    return None if r is None else (r[0], r[1])
