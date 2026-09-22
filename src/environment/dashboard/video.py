"""Write a sequence of RGB frames out as an MP4 file.

PLAIN-LANGUAGE SUMMARY. The dashboard draws one picture per step of an episode.
This module is what turns that sequence of pictures into a single video file a
person can open. It does nothing else: no drawing, no layout, no reading of
recordings.

WHY THE STREAMING FORM IS REQUIRED. Callers hand this a GENERATOR of frames, not
a list -- `render_recordings_v2.py` builds each frame on demand so a long episode
never holds every picture in memory at once. `imageio.get_writer` plus
`append_data` consumes frames one at a time and satisfies that. The
`imageio.mimsave` variant found elsewhere in the codebase materialises the whole
sequence first and is NOT the source this was taken from.

WHY `quiet` REDIRECTS FILE DESCRIPTORS RATHER THAN SETTING A LOG LEVEL. The
encoder writes progress chatter from native code, below Python's logging, so the
only thing that actually silences it is swapping the process's stdout and stderr
descriptors for `/dev/null` around the write and restoring them afterwards. That
matters because this runs inside training: a checkpoint render that printed a
progress bar per frame would bury the training log.

PROVENANCE. This is a verbatim copy of `save_jax_video` as it stood at
`renderer.py:1094-1132`, taken at commit `5364ad60` on 2026-09-22. It was copied
rather than re-exported so that the dashboard package owns its own file writer
and stops depending on the older drawing module, which is being retired.
See `docs/develop/active/refactors/RENDERER_V1_RETIREMENT_AND_RENAME.md` Step 1.
"""

from __future__ import annotations


def save_jax_video(frames, output_path, fps=5, quiet=False):
    """
    Save a list of RGB frames as an MP4 video.

    Args:
        frames: List of numpy arrays (H, W, 3)
        output_path: Path to save the video
        fps: Frames per second
        quiet: Suppress output messages
    """
    import os
    import imageio

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if quiet:
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        old_stdout_fd = os.dup(sys.stdout.fileno())
        old_stderr_fd = os.dup(sys.stderr.fileno())
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            os.dup2(devnull, sys.stderr.fileno())
            os.close(devnull)
            with imageio.get_writer(output_path, fps=fps) as writer:
                for frame in frames:
                    writer.append_data(frame)
        finally:
            os.dup2(old_stdout_fd, sys.stdout.fileno())
            os.dup2(old_stderr_fd, sys.stderr.fileno())
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)
    else:
        with imageio.get_writer(output_path, fps=fps) as writer:
            for frame in frames:
                writer.append_data(frame)
        print(f"Saved video to {output_path}")
