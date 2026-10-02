"""Render saved eval recordings to MP4 with the NEW dashboard renderer (V2).

PLAIN-LANGUAGE SUMMARY. This turns a folder of recorded episodes into videos you
can watch, using the redesigned dashboard in ``src/environment/dashboard/``
rather than the renderer training currently uses. It is a **separate entry
point on purpose**: the old pipeline
(``scripts/eval/render_recordings.py``) keeps working, untouched, and keeps
writing to ``videos/``. This one writes only to ``videos_v2/`` and is never
called by training, by evaluation, or by anything under ``src/``. Which renderer
you get is decided by which script you run, and by nothing else.

Usage::

    python scripts/eval/render_recordings_v2.py <recordings_dir> [--concat]
                                                [--workers N] [--fps 5]

``<recordings_dir>`` is the same directory ``render_recordings.py`` reads --
``run_meta.pkl`` plus ``episode_*.rec.gz`` -- e.g.
``results/<run>/recordings/<checkpoint_pct>/``.

Writes one MP4 per episode to::

    results/<run>/videos_v2/<checkpoint_pct>/episode_<NNNNNN>.mp4

and, with ``--concat``, one consolidated file::

    results/<run>/videos_v2/eval_<checkpoint_pct>.mp4

WHY THE OUTPUT FOLDER IS THE POINT (plan section D5.4). ``videos/`` belongs to
the frozen V1 pipeline. This script never reads, writes or deletes anything
there; ``--skip-existing`` looks only inside ``videos_v2/``; and there is
deliberately **no** ``--cleanup-per-episode`` flag, so it has no code path that
deletes a file at all.

THREE PROPERTIES THIS SCRIPT CHECKS RATHER THAN ASSUMES.

1. **Every MP4 is probed after it is written**, and its decoded frame count must
   equal the number of recorded steps. A writer that silently drops or
   duplicates a frame is the failure this exists to catch, so the count is read
   back out of the finished file (with ``ffprobe`` where available) instead of
   being taken on trust from the writer.
2. **A concatenated video may not change shape half way through.** Every episode
   reports its ``layout_signature()`` -- panel keys, boxes, square size, window
   rule -- and ``--concat`` refuses to write unless all of them agree.
3. **A recording that cannot be rendered fails loudly and alone.** Recordings
   saved before the body-temperature system carry an ``EnvParams`` with no
   ``thermal_enabled`` field, and the frozen observation breakdown reads that
   field unconditionally, so they raise ``AttributeError``. Such an episode is
   reported in full, the rest of the batch still renders, and the process exits
   non-zero so a failure cannot pass for success.

FD-limit note: as in V1, each rendered episode opens a few hundred matplotlib
font file descriptors, so the soft ``RLIMIT_NOFILE`` is raised at startup before
the pool is created. That helper is **copied** from V1 rather than imported,
because V1 is a frozen file and this script must not depend on its internals.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# CPU-only, belt-and-braces GPU isolation, set BEFORE anything imports JAX.
# Copied from `src/utils/async_render.py::_render_env` (a frozen file) rather
# than imported: rendering must never touch a training GPU, and 20 render
# workers each grabbing a device would be the way it happened.
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

_WORKER_STATE = {}

# Target soft RLIMIT_NOFILE. Copied from render_recordings.py, not imported.
_TARGET_SOFT_NOFILE = 8192


def _raise_fd_limit(target: int = _TARGET_SOFT_NOFILE) -> None:
    """Raise the soft RLIMIT_NOFILE toward the hard limit, best-effort.

    Copied from `scripts/eval/render_recordings.py` (frozen; see module
    docstring). Background launch contexts commonly default the soft fd limit to
    ~1024 while matplotlib opens ~250 fds per render, so a handful of parallel
    workers can exhaust it. Never raises.
    """
    import resource
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft >= target:
            return
        new_soft = target if hard == resource.RLIM_INFINITY else min(target, hard)
        if new_soft > soft:
            resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))
    except (ValueError, OSError):
        pass  # never crash a render because the fd limit could not be raised


# --------------------------------------------------------------------- probing


def probe_frame_count(path) -> int:
    """Count the frames in a written MP4 by DECODING it.

    The point of this function is that it does not ask the writer how many
    frames it wrote. It opens the finished file and counts what comes out, so a
    dropped or duplicated frame is visible. `ffprobe` is preferred because it is
    a different program from the one that wrote the file; the imageio fallback
    still decodes the container rather than trusting a return value.
    """
    path = str(path)
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path],
            capture_output=True, text=True, check=True,
        ).stdout.strip().strip(",")
        if out.isdigit():
            return int(out)
    except (OSError, subprocess.CalledProcessError):
        pass
    import imageio.v2 as imageio
    rdr = imageio.get_reader(path)
    try:
        return int(rdr.count_frames())
    finally:
        rdr.close()


def _assert_single_layout(sig_by_episode: dict) -> str:
    """Refuse to concatenate episodes whose dashboards are not the same shape.

    `sig_by_episode` maps an episode label to its `layout_signature()`. A
    concatenated video that switches panel set, panel boxes, arena square size or
    window rule part way through is not one video of one run; it is two videos in
    a trench coat, and every frame after the switch is measured against the wrong
    geometry. Returns the single shared signature, or raises `SystemExit`.
    """
    sigs = sorted(set(sig_by_episode.values()))
    if len(sigs) > 1:
        groups = {}
        for ep, sig in sorted(sig_by_episode.items()):
            groups.setdefault(sig, []).append(str(ep))
        detail = "\n".join(f"    {sig[:16]}…  episodes {', '.join(eps)}"
                           for sig, eps in sorted(groups.items()))
        raise SystemExit(
            "--concat refuses to write: these episodes do not share one dashboard "
            f"layout, so a single video would change shape mid-play.\n{detail}\n"
            "  A layout signature covers the panel set, every panel's box, the arena "
            "square size and the window rule. Render the groups separately."
        )
    if not sigs:
        raise SystemExit("--concat: no episode rendered, so there is nothing to concatenate.")
    return sigs[0]


# ---------------------------------------------------------------------- worker


def _worker_init(run_meta_path: str, local_view_size=None, title=None):
    """Runs once per worker: matplotlib backend + the run's metadata.

    Deliberately does NOT call the frozen renderer's `_load_icons`. That cache is
    process-global and ignores its argument after the first call, so priming it
    from a V2 worker is how "V1 is unaffected" would quietly stop being true
    (plan finding #48). The V2 renderer reads its own artwork and needs no icon
    cache at all.

    `local_view_size` overrides the recording's own
    `visualization.local_view_size` -- how many world squares the grid view draws
    across. It is a RENDERING choice and nothing else: the recording is not
    re-stepped, no environment is built, and the saved params are copied rather
    than mutated, so two renders of one recording at different window sizes are
    the same episode seen at two zoom levels.
    """
    import matplotlib
    matplotlib.use("Agg")
    from src.utils.eval_recording import load_run_meta

    _raise_fd_limit()  # also done in the parent; cheap and safe to repeat
    meta = load_run_meta(Path(run_meta_path).parent)
    params = meta["params"]
    if local_view_size is not None:
        # Set the ONE field on this worker's freshly-unpickled copy rather than
        # rebuilding the object. `dataclasses.replace` (and flax's `.replace`,
        # which calls it) reads back every field the CURRENT EnvParams class
        # declares, and an archived recording predates some of them — measured on
        # the render-audit fixtures, which have no `thermal_warming_rate_scale` —
        # so rebuilding raises on a field nobody asked to change. Nothing is
        # written back to the recording.
        object.__setattr__(params, "local_view_size", int(local_view_size))
    _WORKER_STATE["params"] = params
    _WORKER_STATE["icon_config"] = meta["icon_config"]
    _WORKER_STATE["action_map"] = meta.get("action_map")
    # The recording's own sensor-channel names. Absent on any recording written
    # before they existed, which is the signal the renderer falls back on.
    _WORKER_STATE["channel_display"] = meta.get("channel_display")
    _WORKER_STATE["title"] = title or Path(run_meta_path).parent.name


def _render_episode(episode_path_str: str, out_video_path_str: str, fps: int) -> dict:
    """Worker body: one episode in, one probed MP4 out.

    Returns a result dict either way. A recording this renderer cannot draw
    reports itself as `ok: False` with its traceback rather than killing the
    pool, so one archived world cannot abort a batch of thirty good ones.
    """
    import time
    import traceback

    from src.utils.eval_recording import load_episode

    ep_path = Path(episode_path_str)
    out = Path(out_video_path_str)
    t0 = time.perf_counter()
    result = {"episode": ep_path.name, "out": str(out), "ok": False}

    try:
        from src.environment.dashboard import EpisodeRenderer, save_jax_video

        payload = load_episode(ep_path)
        renderer = EpisodeRenderer(
            _WORKER_STATE["params"], _WORKER_STATE["icon_config"], payload,
            title=_WORKER_STATE["title"], action_map=_WORKER_STATE["action_map"],
            channel_display=_WORKER_STATE["channel_display"],
        )
        try:
            steps = renderer.n_steps
            result["episode_index"] = int(payload.get("episode_index", 0))
            result["steps"] = steps
            result["signature"] = renderer.layout_signature()
            out.parent.mkdir(parents=True, exist_ok=True)
            save_jax_video((renderer.frame(t) for t in range(steps)), str(out),
                           fps=fps, quiet=True)
        finally:
            renderer.close()

        written = probe_frame_count(out)
        result["frames"] = written
        if written != steps:
            result["error"] = (
                f"frame count mismatch: the recording has {steps} steps but the "
                f"written MP4 decodes to {written} frames"
            )
            return result
        result["ok"] = True
    except Exception as exc:  # reported per episode; the batch carries on
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    finally:
        result["render_seconds"] = time.perf_counter() - t0
    return result


# ------------------------------------------------------------------- benchmark


def _benchmark(recordings_dir: str, episodes, min_frames: int) -> dict:
    """Time V2 and V1 on the same recordings, in this process (plan section D5.3).

    Writes no video. V1 is timed by calling `render_jax_state` read-only with the
    same per-step inputs `render_recordings.py` builds for it.
    """
    import resource
    import statistics as st
    import time

    import matplotlib
    matplotlib.use("Agg")
    import numpy as np

    from src.environment.dashboard import EpisodeRenderer
    from src.environment.renderer import render_jax_state, thermal_color_limits
    from src.environment.sensor import build_sensory_viz
    from src.utils.eval_recording import load_episode, load_run_meta

    rec_dir = Path(recordings_dir)
    meta = load_run_meta(rec_dir)
    params, icon_config = meta["params"], meta["icon_config"]
    out = {"v2_frames_ms": [], "v1_frames_ms": [], "episodes": 0,
           "v2_setup_ms": None, "v1_first_frame_ms": None}

    for ep_path in episodes:
        payload = load_episode(Path(ep_path))
        n = len(payload["snapshots"])

        t0 = time.perf_counter()
        renderer = EpisodeRenderer(params, icon_config, payload,
                                   title=rec_dir.name, action_map=meta.get("action_map"),
                                   channel_display=meta.get("channel_display"))
        setup_ms = (time.perf_counter() - t0) * 1e3
        out["v2_setup_ms"] = setup_ms if out["v2_setup_ms"] is None else out["v2_setup_ms"]
        for t in range(n):
            a = time.perf_counter()
            renderer.frame(t)
            out["v2_frames_ms"].append((time.perf_counter() - a) * 1e3)
        renderer.close()

        clim = thermal_color_limits(payload["snapshots"][0].get("thermal_field"), params)
        for t in range(n):
            snap = payload["snapshots"][t]

            class _S:
                pass

            s = _S()
            for k, v in snap.items():
                setattr(s, k, v)
            true_obs = (payload["true_obs"][t]
                        if payload.get("true_obs") is not None else None)
            viz = build_sensory_viz(payload["obs"][t], s, params, true_obs)
            act = int(payload["actions"][t]) if payload["actions"][t] >= 0 else None
            a = time.perf_counter()
            render_jax_state(s, params, episode=payload.get("episode_index", 0), step=t,
                             train_episode=None, action=act, sensory_data=viz, info=None,
                             icon_config=icon_config, thermal_clim=clim)
            ms = (time.perf_counter() - a) * 1e3
            if out["v1_first_frame_ms"] is None:
                out["v1_first_frame_ms"] = ms
            out["v1_frames_ms"].append(ms)

        out["episodes"] += 1
        if len(out["v2_frames_ms"]) >= min_frames:
            break

    def stats(xs):
        warm = xs[5:] or xs
        return (st.median(warm), float(np.percentile(warm, 95)), xs[:5], len(warm))

    out["v2"], out["v1"] = stats(out["v2_frames_ms"]), stats(out["v1_frames_ms"])
    out["rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    try:
        out["open_fds"] = len(os.listdir(f"/proc/{os.getpid()}/fd"))
    except OSError:
        out["open_fds"] = -1
    return out


# ------------------------------------------------------------------------ main


def main():
    ap = argparse.ArgumentParser(
        description="Render eval recordings to MP4 with the V2 dashboard renderer. "
                    "Writes only under videos_v2/; the V1 pipeline is untouched.")
    ap.add_argument("recordings_dir", help="Directory containing run_meta.pkl + episode_*.rec.gz")
    ap.add_argument("--workers", type=int, default=None,
                    help="Parallel episode renders. Default: one per episode, capped at "
                         "CPU count - 1. One episode is one task; a worker holds a whole "
                         "figure, so idle workers are not created.")
    ap.add_argument("--fps", type=int, default=5)
    ap.add_argument("--concat", action="store_true",
                    help="Also write a consolidated MP4 of every episode in order. "
                         "Refuses if the episodes' layout signatures differ.")
    ap.add_argument("--skip-existing", action="store_true",
                    help="Skip episodes whose MP4 already exists UNDER videos_v2/. "
                         "Never looks at videos/.")
    ap.add_argument("--max-episodes", type=int, default=None,
                    help="Render only the first N episodes (after --stride).")
    ap.add_argument("--stride", type=int, default=1,
                    help="Render only every Nth episode (1 = every episode).")
    ap.add_argument("--output-dir", default=None,
                    help="Override the per-episode output folder. Default: "
                         "<run_root>/videos_v2/<recordings_dir name>/.")
    ap.add_argument("--local-view-size", type=int, default=None,
                    help="Override how many world squares the grid view draws across "
                         "(the recording's visualization.local_view_size). The arena "
                         "panel is a fixed size, so this is a ZOOM: a smaller number is "
                         "a closer view with larger squares. The output filename carries "
                         "it, so three window sizes of one episode cannot overwrite each "
                         "other.")
    ap.add_argument("--title", default=None,
                    help="Frame title. Default: the recordings directory's name.")
    ap.add_argument("--benchmark", action="store_true",
                    help="Time V2 against V1 on these recordings and exit. Writes no video.")
    ap.add_argument("--benchmark-frames", type=int, default=200,
                    help="Minimum frames to time per renderer under --benchmark.")
    args = ap.parse_args()

    _raise_fd_limit()  # before the pool, so forked workers inherit it

    rec_dir = Path(args.recordings_dir)
    run_meta_path = rec_dir / "run_meta.pkl"
    if not run_meta_path.exists():
        raise SystemExit(f"run_meta.pkl not found in {rec_dir}")

    episode_files = sorted(rec_dir.glob("episode_*.rec.gz"))
    if not episode_files:
        raise SystemExit(f"No episode_*.rec.gz files in {rec_dir}")
    if args.stride > 1:
        episode_files = episode_files[::args.stride]
    if args.max_episodes is not None:
        episode_files = episode_files[:args.max_episodes]
    if not episode_files:
        raise SystemExit(f"--stride/--max-episodes selected 0 episodes from {rec_dir}")

    if args.benchmark:
        b = _benchmark(str(rec_dir), episode_files, args.benchmark_frames)
        v2_med, v2_p95, v2_first, v2_n = b["v2"]
        v1_med, v1_p95, v1_first, v1_n = b["v1"]
        print(f"Benchmark on {rec_dir} ({b['episodes']} episode(s))")
        print(f"  V2 setup            {b['v2_setup_ms']:.0f} ms")
        print(f"  V1 first frame      {b['v1_first_frame_ms']:.0f} ms")
        print(f"  V2 per frame        median {v2_med:.1f} ms   p95 {v2_p95:.1f} ms   (n={v2_n})")
        print(f"  V1 per frame        median {v1_med:.1f} ms   p95 {v1_p95:.1f} ms   (n={v1_n})")
        print(f"  ratio V2/V1         {v2_med / v1_med:.3f}")
        print(f"  first 5 excluded    V2 {[f'{x:.0f}' for x in v2_first]}  "
              f"V1 {[f'{x:.0f}' for x in v1_first]}")
        print(f"  max RSS             {b['rss_mb']:.0f} MB")
        print(f"  open fds            {b['open_fds']}")
        return 0

    # videos_v2/<checkpoint_pct>/ -- a sibling of videos/, never videos/ itself.
    run_root = rec_dir.parent.parent
    video_dir = (Path(args.output_dir) if args.output_dir
                 else run_root / "videos_v2" / rec_dir.name)
    video_dir.mkdir(parents=True, exist_ok=True)

    # The window size goes in the FILENAME. Rendering one episode at three window
    # sizes is the way the window rule is demonstrated, and without this the
    # second render would silently overwrite the first.
    view_tag = "" if args.local_view_size is None else f"_view{args.local_view_size}"
    planned = [(ep, video_dir / (ep.stem.replace(".rec", "") + view_tag + ".mp4"))
               for ep in episode_files]
    tasks = [(str(ep), str(mp4)) for ep, mp4 in planned
             if not (args.skip_existing and mp4.exists())]

    workers = args.workers
    if workers is None:
        workers = max(1, min(len(tasks) or 1, (os.cpu_count() or 2) - 1))

    failures, results = [], {}
    if tasks:
        print(f"Rendering {len(tasks)} episode(s) with {workers} worker(s) "
              f"(fps={args.fps}) → {video_dir}")
        with ProcessPoolExecutor(
                max_workers=workers, initializer=_worker_init,
                initargs=(str(run_meta_path), args.local_view_size, args.title)) as pool:
            futures = [pool.submit(_render_episode, ep, out, args.fps) for ep, out in tasks]
            for fut in as_completed(futures):
                r = fut.result()
                if r["ok"]:
                    results[r["episode"]] = r
                    print(f"  ep {r['episode_index']:>4}: {r['steps']} steps, "
                          f"{r['frames']} frames verified, "
                          f"{r['render_seconds']:.1f}s → {r['out']}")
                else:
                    failures.append(r)
                    print(f"  FAILED {r['episode']}: {r['error']}", file=sys.stderr)
    else:
        print("All selected episodes already rendered under videos_v2/.")

    if failures:
        print(f"\n{len(failures)} recording(s) could not be rendered:", file=sys.stderr)
        for r in failures:
            print(f"\n=== {r['episode']} ===\n{r.get('traceback', r['error'])}", file=sys.stderr)
        print("The remaining episodes were rendered. Nothing under videos/ was touched.",
              file=sys.stderr)

    if args.concat:
        renderable = [(ep, mp4) for ep, mp4 in planned if mp4.exists()]
        if not renderable:
            raise SystemExit("--concat: no per-episode MP4 exists to concatenate.")
        # Signatures come from this run's workers; an episode skipped because its
        # MP4 already existed contributes no signature and is not asserted on.
        sigs = {r["episode_index"]: r["signature"] for r in results.values()}
        if sigs:
            _assert_single_layout(sigs)

        from src.environment.dashboard import save_jax_video
        import imageio.v2 as imageio

        expected = 0
        for _, mp4 in renderable:
            expected += probe_frame_count(mp4)

        def frame_generator():
            for _, mp4 in renderable:
                rdr = imageio.get_reader(str(mp4))
                try:
                    for frame in rdr:
                        yield frame
                finally:
                    rdr.close()

        consolidated = video_dir.parent / f"eval_{rec_dir.name}.mp4"
        save_jax_video(frame_generator(), str(consolidated), fps=args.fps, quiet=True)
        got = probe_frame_count(consolidated)
        print(f"Consolidated {len(renderable)} episode(s) → {consolidated}")
        print(f"  {got} frames verified (expected {expected})")
        if got != expected:
            print(f"  FRAME COUNT MISMATCH: expected {expected}, decoded {got}",
                  file=sys.stderr)
            return 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
