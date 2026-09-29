"""untrained.build must equal the network train.py actually constructs (bitwise).

Plain-language context: no step-0 checkpoint is saved, so `scripts/analysis/nmn/untrained.py`
re-derives train.py's key chain to rebuild a run's starting weights. A re-derivation can be
silently wrong (the obvious key, `model_key`, is never used by train.py), so it is checked
against the trainer itself: train.main() is run with the run's own launch arguments up to the
network's construction, the constructed parameters are recorded, and the run stops there.

Slow (imports and starts train.py) and needs the gitignored runs + local WandB metadata; run
with `-m integration`. Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md,
File Changes §11, Checkpoints 3.3 / 4.4.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

RUNS = {
    "may_t1none_s43": "results/JAX_RecurrentPPO/20260929-153652_rppo_cw_mayrep_t1none_s43",
    "may_t16quad_s44": "results/JAX_RecurrentPPO/20260929-153723_rppo_cw_mayrep_t16quad_s44",
    "l05_t1none_w0000": "results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42",
    "l05_t16quad_w0000": "results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42",
}
_DROP = {"--device": 1, "--wandb-name": 1, "--wandb-group": 1, "--wandb-job-type": 1,
         "--results-dir": 1}


class _Built(Exception):
    pass


def train_constructed_params(run_dir, tmp_path, monkeypatch) -> dict:
    from scripts.analysis.nmn import untrained
    args = untrained.launch_args(run_dir)
    kept, i = [], 0
    while i < len(args):
        if args[i] in _DROP:
            i += 1 + _DROP[args[i]]
            continue
        kept.append(args[i]); i += 1
    argv = ["train.py", *kept, "--device", "cpu", "--no-wandb", "--quiet",
            "--results-dir", str(tmp_path / "results")]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.chdir(_REPO)
    import train
    captured = {}
    Orig = train.ActorCriticRNN

    class Recording(Orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            captured.update(untrained.param_arrays(self))
            raise _Built

    monkeypatch.setattr(train, "ActorCriticRNN", Recording)
    with pytest.raises(_Built):
        train.main()
    return captured


@pytest.mark.integration
@pytest.mark.parametrize("name", list(RUNS))
def test_matches_train_py_construction(name, tmp_path, monkeypatch):
    from scripts.analysis.nmn import untrained
    run = _REPO / RUNS[name]
    if not (run / "models" / "config.yaml").exists():
        pytest.skip(f"{run} not present (gitignored)")
    want = train_constructed_params(run, tmp_path, monkeypatch)
    model, _ = untrained.build(run)
    got = untrained.param_arrays(model)
    assert set(got) == set(want)
    bad = [k for k in want if not np.array_equal(want[k], got[k])]
    assert not bad, (name, bad[:5])
    print(f"{name}: {len(want)} parameter arrays equal bitwise to train.py's construction")


@pytest.mark.integration
def test_own_seed_rebuild_is_closest_to_first_checkpoint():
    """Checkpoint 4.4 second half (R4-6) on one run; all 22 are in the Implementation Report."""
    from scripts.analysis.nmn import untrained
    run = _REPO / RUNS["l05_t16quad_w0000"]
    if not (run / "models" / "config.yaml").exists():
        pytest.skip(f"{run} not present (gitignored)")
    res = untrained.closeness_to_first_checkpoint(run, [43, 44])
    assert res["own_closest"], res
    with pytest.raises(ValueError):
        untrained.closeness_to_first_checkpoint(run, [42, 43])   # own seed among the others
