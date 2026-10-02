"""The dashboard package owns its own MP4 writer.

WHY THIS FILE EXISTS. `save_jax_video` used to live in the old drawing module and
was imported across from there. It now lives at
`src/environment/dashboard/video.py`, so the dashboard package no longer depends
on the module being retired. These cases pin the three properties that
relocation could have broken, each asserted rather than assumed:

  1. the name resolves from the package at all;
  2. its signature is unchanged, so every existing caller still works;
  3. **a generator input produces a readable MP4 with the expected frame count**
     -- the property a non-streaming rewrite would silently break, because every
     production caller passes a generator so a long episode never holds all of
     its pictures in memory at once.

(3) is the one that matters. A version built on `imageio.mimsave` would pass (1)
and (2), materialise the whole sequence, and only show up as a memory blow-up on
a long episode in training. The frame count is read back by DECODING the written
file, never from what the writer reported about itself.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _frames(n, h=32, w=48):
    """`n` distinct little pictures. Distinct so a writer that drops or repeats
    one cannot pass by accident."""
    out = []
    for i in range(n):
        a = np.zeros((h, w, 3), dtype=np.uint8)
        a[:, :, 0] = (i * 20) % 256
        a[i % h, :, 1] = 255
        out.append(a)
    return out


def _decoded_frame_count(path) -> int:
    """Count frames by DECODING the file, not by trusting the writer."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=120,
        )
        text = out.stdout.strip().split(",")[0]
        if text.isdigit():
            return int(text)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    import imageio.v2 as iio
    with iio.get_reader(str(path)) as rdr:
        return int(rdr.count_frames())


def test_it_resolves_from_the_dashboard_package():
    from src.environment.dashboard import save_jax_video
    assert callable(save_jax_video)


def test_it_is_also_exported_by_name():
    import src.environment.dashboard as pkg
    assert "save_jax_video" in pkg.__all__


def test_the_signature_did_not_move():
    """Every existing caller passes these positionally or by keyword."""
    from src.environment.dashboard import save_jax_video

    params = list(inspect.signature(save_jax_video).parameters)
    assert params == ["frames", "output_path", "fps", "quiet"]


def test_a_GENERATOR_produces_a_readable_mp4_with_every_frame(tmp_path):
    """THE CASE THE RELOCATION COULD HAVE BROKEN.

    Production callers pass a generator. A writer that materialised its input
    would still pass here in wall-clock terms at this size, but would not be
    able to consume a one-shot iterator at all if it tried to walk it twice --
    and the decoded count catches a writer that consumed it lazily but dropped
    frames.
    """
    from src.environment.dashboard import save_jax_video

    out = tmp_path / "gen.mp4"
    n = 11
    save_jax_video((f for f in _frames(n)), str(out), fps=5, quiet=True)

    assert out.exists() and out.stat().st_size > 0
    assert _decoded_frame_count(out) == n


def test_a_list_gives_the_same_bytes_as_a_generator(tmp_path):
    """The two input forms are the same video, not merely both playable."""
    from src.environment.dashboard import save_jax_video

    import hashlib

    frames = _frames(9)
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    save_jax_video(list(frames), str(a), fps=5, quiet=True)
    save_jax_video((f for f in frames), str(b), fps=5, quiet=True)

    assert (hashlib.sha256(a.read_bytes()).hexdigest()
            == hashlib.sha256(b.read_bytes()).hexdigest())


def test_it_creates_the_output_directory(tmp_path):
    """Callers hand it a path under a run folder that may not exist yet."""
    from src.environment.dashboard import save_jax_video

    out = tmp_path / "deep" / "deeper" / "v.mp4"
    save_jax_video(_frames(4), str(out), fps=5, quiet=True)
    assert out.exists()


def test_quiet_restores_the_process_stdout(tmp_path, capfd):
    """`quiet` swaps the process's file descriptors; it must put them back.

    A restore bug here would silence the REST of training, not just the render,
    which is the kind of fault that is nearly impossible to trace back later.
    """
    from src.environment.dashboard import save_jax_video

    save_jax_video(_frames(3), str(tmp_path / "q.mp4"), fps=5, quiet=True)
    print("stdout is alive")
    assert "stdout is alive" in capfd.readouterr().out
