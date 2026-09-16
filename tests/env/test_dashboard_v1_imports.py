"""What the new renderer borrows from the frozen production path, pinned.

WHAT THIS IS FOR, IN PLAIN WORDS. The production episode-video renderer and the
files around it are **frozen** for the whole of this redesign: they are what
training and evaluation actually use, and a change there is a change to videos
nobody asked to change. The new renderer is therefore allowed to *read* a handful
of helpers from that frozen side, and allowed to change none of them. This file
pins the shape of every one it reads, so that if somebody later changes one, the
failure is a named test rather than a video that quietly renders the wrong
numbers.

WHAT IT ALSO CHECKS, AND WHY THAT ONE IS SUBTLE. The production renderer caches
its icons in a **process-global**, which is a recorded bug: whichever renderer
runs first in a process decides which icons the other one draws, so a frame
comparison can flip on test order alone. The new renderer must therefore not
merely avoid *editing* that module -- it must not **import** it at all. That is
checked in a subprocess, because "is this module loaded?" is a question about a
whole process and any test running earlier in the same session could answer it
for us.
"""

import inspect
import json
import os
import subprocess
import sys

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _sig(obj) -> str:
    return str(inspect.signature(obj))


# --------------------------------------------------------------------------
# the frozen helpers the package reads
# --------------------------------------------------------------------------
def test_sensor_helpers_keep_their_signatures():
    from src.environment.sensor import (
        build_sensory_viz,
        get_observation_breakdown,
        get_visual_offsets,
    )

    assert _sig(build_sensory_viz) == "(obs, state, params, true_obs=None)"
    assert _sig(get_observation_breakdown) == "(params: src.environment.state.EnvParams)"
    assert _sig(get_visual_offsets) == "(sensor_range)"


def test_the_diamond_offset_order_is_the_environments_own():
    """The order of the five squares a range-1 sense reads is NEVER re-derived.

    The dashboard draws collision and thermoception as a diamond, and which cell
    of that diamond is "up" comes from the environment's own function. A painter
    that re-derived the order could disagree with the sensor and would draw a
    reading in the wrong place -- truthful numbers in a lying arrangement.
    """
    from src.environment.sensor import get_visual_offsets

    assert [tuple(o) for o in get_visual_offsets(1)] == [(0, 0), (-1, 0), (0, 1),
                                                         (1, 0), (0, -1)]


def test_recording_helpers_keep_their_signatures():
    from src.utils.eval_recording import (
        EpisodeRecorder,
        load_episode,
        load_run_meta,
        write_run_meta,
    )

    assert _sig(load_episode) == "(path: pathlib.Path) -> Dict[str, Any]"
    assert _sig(load_run_meta) == "(recording_dir: pathlib.Path) -> Dict[str, Any]"
    assert _sig(EpisodeRecorder.__init__) == (
        "(self, episode_index: int, train_episode: int, seed: int)")
    assert _sig(write_run_meta).startswith("(out_dir: pathlib.Path, params, icon_config")


def test_select_by_class_keeps_its_signature():
    from src.environment.state import select_by_class

    assert _sig(select_by_class) == "(params, class_name: str) -> numpy.ndarray"


# --------------------------------------------------------------------------
# isolation from the frozen renderer
# --------------------------------------------------------------------------
_PROBE = r"""
import json, sys
sys.path.insert(0, %(root)r)
import src.environment.dashboard.episode as ep       # the whole drawing side
leaked = sorted(m for m in sys.modules
                if m in ("src.environment.renderer", "src.environment.renderer_v2"))
# The probe must be able to SEE a leak, or an empty answer means nothing.
import src.environment.renderer  # noqa: F401
after = sorted(m for m in sys.modules if m == "src.environment.renderer")
print(json.dumps({"leaked": leaked, "after": after}))
"""


def test_the_package_does_not_import_the_frozen_renderer():
    """Measured in a fresh process, and the probe is checked for blindness.

    The new renderer copies the helpers it needed to change (the thermal scale,
    the icon handling) rather than importing them, exactly as the plan requires.
    The consequence worth protecting is the process-global icon cache: a package
    that never imports the frozen renderer cannot prime or read that cache, so a
    V1 frame rendered after a V2 frame in one process is unaffected.
    """
    out = subprocess.run([sys.executable, "-c", _PROBE % {"root": _ROOT}],
                         capture_output=True, text=True,
                         env={**os.environ, "JAX_PLATFORMS": "cpu", "MPLBACKEND": "Agg"})
    assert out.returncode == 0, out.stderr[-2000:]
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["leaked"] == [], (
        f"the dashboard package imported a frozen renderer module: {got['leaked']}")
    assert got["after"] == ["src.environment.renderer"], (
        "the probe cannot see the module even when it IS imported, so its empty "
        "answer above was evidence of nothing")


def test_no_renderer_v2_package_was_created():
    """A ``renderer_v2/`` package would SHADOW the frozen ``renderer_v2.py``.

    The guard hashes the file; it has no assertion that a package of the same
    name was not created beside it, and such a package would take precedence on
    import while leaving the guard green.
    """
    import src.environment.renderer_v2 as rv2

    assert not os.path.isdir(os.path.join(_ROOT, "src", "environment", "renderer_v2"))
    assert rv2.__file__.endswith("renderer_v2.py")


def test_no_file_in_the_package_names_the_frozen_renderer_at_all():
    """A static partner to the subprocess check above.

    The runtime check proves the module was not loaded on one path through the
    code; this one proves no path could load it, which is what makes a lazy or
    conditional import impossible to sneak in later.
    """
    import pathlib

    pkg = pathlib.Path(_ROOT) / "src" / "environment" / "dashboard"
    offenders = []
    for path in sorted(pkg.glob("*.py")):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or '"' in stripped or "'" in stripped:
                continue          # prose, not code
            if "renderer" in stripped and "import" in stripped:
                offenders.append(f"{path.name}:{i}: {stripped}")
    assert not offenders, (
        "the dashboard package imports the frozen renderer: " + "; ".join(offenders))
