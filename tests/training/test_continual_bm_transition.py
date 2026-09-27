"""Regression test: continual-learning stage transition with behavior_measures enabled.

Bug context
-----------
train.py lines ~1221-1236 wiped BMState accumulators at stage transitions by
referencing the OLD flat array names (``m1_candidates``, ``m2_onsets``, etc.)
that were removed when the BMState dataclass was introduced in commit 89ade04.
Any curriculum run with ``behavior_measures: enabled: true`` crashed at its first
stage boundary with::

    NameError: name 'm1_candidates' is not defined

Fix: replace the stale block with a loop over ``_bm_reset_env(i)`` for each
env, using the same helper already used at episode end.

This test exercises the crash path end-to-end by running ``train.py`` as a
subprocess across a 2-stage schedule so a stage transition fires within the
first ~12 episodes (~seconds on CPU with 2 envs and a 5x5 grid).

Red → green contract
--------------------
BEFORE the fix: test fails (subprocess exits with a non-zero returncode and
the combined output contains ``NameError``).
AFTER the fix:  returncode == 0, ``[STAGE]`` marker in stdout, no Traceback.

Run with::

    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \\
        -m pytest tests/training/test_continual_bm_transition.py -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap

import pytest
import yaml

_PYTHON = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_TRAIN_PY = os.path.join(_REPO_ROOT, "train.py")
_AGENT_CONFIG = os.path.join(
    _REPO_ROOT, "configs", "models", "recurrent_ppo", "recurrent_ppo.yaml"
)

# ---------------------------------------------------------------------------
# Stage configs — both extend environment/default so behavior_measures is
# inherited as enabled.  They differ only in the trivial grid/entity scene so
# the two stages share identical obs/action dimensions (mandatory for a valid
# continual run).  Using the same 5x5 no-entity scene for both stages keeps
# obs/action dims identical while still triggering a genuine stage transition.
# ---------------------------------------------------------------------------

_STAGE_A_YAML = textwrap.dedent("""\
    # Continual-BM regression test — stage A (5x5 no entities, food only)
    extends: environment/default

    environment:
      height: 5
      width: 5
      start_pos: [3, 3]
      max_steps: 20
      location_areas:
        - type: "grass"
          area: [[1, 1], [5, 5]]
        - type: "sand"
          area: [[0, 0], [0, 0]]
      resources:
        - name: "food"
          type: "food"
          count: 2
          spawn_area: [[1, 1], [5, 5]]
          properties: [1.0, 0.0, 0.0, 0.0, 0.0]
          properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
          visual_properties: [0, 0, 0, 1, 0, 0, 0, 0]
          visual_properties_std: [0, 0, 0, 0, 0, 0, 0, 0]
          max_consumption: 12
          regeneration_delay: 0
          damage: [0.0, 0.0]
          nociception_intensity: 0.0
        - name: "hiding_predator"
          type: "hiding_predator"
          count: 1
          spawn_area: [[1, 1], [5, 5]]
          properties: [0.0, 0.0, 0.0, 0.0, 0.0]
          properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
          visual_properties: [0, 0, 0, 0, 1, 0, 0, 0]
          visual_properties_std: [0, 0, 0, 0, 0, 0, 0, 0]
          max_consumption: -1
          regeneration_delay: 20
          damage: [15.0, 45.0]
          nociception_intensity: 0.9
      entities: []
      obstacles: []
""")

_STAGE_B_YAML = textwrap.dedent("""\
    # Continual-BM regression test — stage B (same 5x5 scene, different name)
    extends: environment/default

    environment:
      height: 5
      width: 5
      start_pos: [3, 3]
      max_steps: 20
      location_areas:
        - type: "grass"
          area: [[1, 1], [5, 5]]
        - type: "sand"
          area: [[0, 0], [0, 0]]
      resources:
        - name: "food"
          type: "food"
          count: 2
          spawn_area: [[1, 1], [5, 5]]
          properties: [1.0, 0.0, 0.0, 0.0, 0.0]
          properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
          visual_properties: [0, 0, 0, 1, 0, 0, 0, 0]
          visual_properties_std: [0, 0, 0, 0, 0, 0, 0, 0]
          max_consumption: 12
          regeneration_delay: 0
          damage: [0.0, 0.0]
          nociception_intensity: 0.0
        - name: "hiding_predator"
          type: "hiding_predator"
          count: 1
          spawn_area: [[1, 1], [5, 5]]
          properties: [0.0, 0.0, 0.0, 0.0, 0.0]
          properties_std: [0.0, 0.0, 0.0, 0.0, 0.0]
          visual_properties: [0, 0, 0, 0, 1, 0, 0, 0]
          visual_properties_std: [0, 0, 0, 0, 0, 0, 0, 0]
          max_consumption: -1
          regeneration_delay: 20
          damage: [15.0, 45.0]
          nociception_intensity: 0.9
      entities: []
      obstacles: []
""")

# Schedule: 2-stage boundary at episode 6, end at 12.
_SCHEDULE_YAML = textwrap.dedent("""\
    continual:
      episode_boundaries: [6, 12]
      checkpoint_frequencies: [100, 100]
""")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Regression test
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_continual_bm_stage_transition_no_crash():
    """Run a 2-stage continual schedule with behavior_measures enabled.

    Before the fix this crashed with NameError at the first stage transition.
    After the fix it must complete with returncode 0 and a [STAGE] marker in
    the output, confirming the transition ran without error.
    """
    with tempfile.TemporaryDirectory(prefix="bm_transition_test_") as tmpdir:
        # Write stage configs
        stages_dir = os.path.join(tmpdir, "stages")
        os.makedirs(stages_dir)
        _write(os.path.join(stages_dir, "00_a.yaml"), _STAGE_A_YAML)
        _write(os.path.join(stages_dir, "01_b.yaml"), _STAGE_B_YAML)

        # Write schedule
        schedule_path = os.path.join(tmpdir, "schedule.yaml")
        _write(schedule_path, _SCHEDULE_YAML)

        # Write results to tmp as well so we don't pollute the repo
        results_dir = os.path.join(tmpdir, "results")
        os.makedirs(results_dir)

        cmd = [
            _PYTHON, _TRAIN_PY,
            "--configs-dir", stages_dir,
            "--continual-schedule", schedule_path,
            "--agent_config", _AGENT_CONFIG,
            "--num-envs", "2",
            "--num-steps", "10",   # short rollout so stage boundary fires between iterations
            "--device", "cpu",
            "--no-wandb",
            "--results-dir", results_dir,
            # Do NOT pass --quiet so that [STAGE] markers are printed to stdout
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=_REPO_ROOT,
        )

        combined = result.stdout + result.stderr

        # 1. No NameError / Traceback
        assert "NameError" not in combined, (
            f"NameError seen in output — the stale flat-array names are still "
            f"present in the stage-transition block.\n\nSTDOUT:\n{result.stdout}\n"
            f"\nSTDERR:\n{result.stderr}"
        )
        assert "Traceback" not in combined, (
            f"Unexpected traceback in output.\n\nSTDOUT:\n{result.stdout}\n"
            f"\nSTDERR:\n{result.stderr}"
        )

        # 2. Stage transition marker present
        assert "[STAGE]" in combined, (
            f"No [STAGE] marker found — stage transition may not have fired "
            f"(check episode_boundaries in schedule).\n\nSTDOUT:\n{result.stdout}\n"
            f"\nSTDERR:\n{result.stderr}"
        )

        # 3. Clean exit
        assert result.returncode == 0, (
            f"train.py exited with non-zero code {result.returncode}.\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# T10 (balance metrics, docs/develop/active/behavior/BALANCE_METRICS_TRAINING_LOGGING.md):
# the balance switch is on (configs/train/recurrent_ppo.yaml) across a stage swap.
#
# The plan asked for a thermal-on -> thermal-off stage pair. That pair cannot exist:
# train.py rejects any continual schedule whose stages differ in `thermal_enabled` or
# `interoceptive_nociception_enabled` (the obs-dim check and `_modality_fingerprint`),
# so the balance flags can never change across a swap. What CAN go wrong at a swap --
# the per-env counters not being wiped, the calibration not being re-recorded, a crash
# in the emit path -- is exercised here on two level-05 (thermal + felt injury) stages.
# WANDB_MODE=disabled keeps `wandb_enabled` true so the Episode/* emit path (and with it
# the Bal_* aggregation) actually runs, without network or files.
# ---------------------------------------------------------------------------
_BAL_STAGE_YAML = textwrap.dedent("""\
    # Balance-metrics continual test stage: level 05, short episodes, small windows.
    extends: environment/experiment/basic/05-campfire_thermal_10x10
    environment:
      max_steps: 30
    logging:
      episode:
        smoothing_episodes: 4
        interval_episodes: 2
    training:
      video_during_training: false
""")


@pytest.mark.slow
def test_continual_balance_metrics_stage_swap():
    with tempfile.TemporaryDirectory(prefix="bal_transition_test_") as tmpdir:
        stages_dir = os.path.join(tmpdir, "stages")
        os.makedirs(stages_dir)
        _write(os.path.join(stages_dir, "00_a.yaml"), _BAL_STAGE_YAML)
        _write(os.path.join(stages_dir, "01_b.yaml"), _BAL_STAGE_YAML)
        schedule_path = os.path.join(tmpdir, "schedule.yaml")
        _write(schedule_path, _SCHEDULE_YAML)
        results_dir = os.path.join(tmpdir, "results")
        os.makedirs(results_dir)
        cmd = [
            _PYTHON, _TRAIN_PY,
            "--configs-dir", stages_dir,
            "--continual-schedule", schedule_path,
            "--agent_config", _AGENT_CONFIG,
            "--num-envs", "2",
            "--num-steps", "10",
            "--device", "cpu",
            "--results-dir", results_dir,
        ]
        env = dict(os.environ, WANDB_MODE="disabled", WANDB_DIR=tmpdir)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                                cwd=_REPO_ROOT, env=env)
        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, combined[-4000:]
        assert result.returncode == 0, combined[-4000:]
        assert "[STAGE]" in combined, combined[-4000:]
        assert "[balance] balance_calibration: " in combined, combined[-4000:]
        stage1 = [l for l in combined.splitlines()
                  if l.startswith("[balance] balance_calibration_stage_1: ")]
        assert len(stage1) == 1, combined[-4000:]
        assert "'thermal_on': True" in stage1[0] and "'max_injury': 100.0" in stage1[0]
        assert "'early_death_max_steps': 20" in stage1[0]
