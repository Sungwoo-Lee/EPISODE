#!/usr/bin/env python
"""V1 video-path guard for the renderer layout redesign.

WHAT THIS IS. While the new episode-video renderer ("dashboard") is being built, the
current (V1) video pipeline is frozen by a user constraint: ten files are not edited by
the plan. This script turns that promise into a check. It records a content-hash
baseline of the ten files, then, at every phase boundary, assigns each file exactly one
state and exits non-zero if any file is UNATTRIBUTABLE.

Plan: docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md, section D5.4, checkpoints
CP0.1a / CP0.1b / CP-G.

STATES (mechanical; evaluated in this order per frozen file)
    PASS            working-tree sha256 == baseline worktree_sha256
    ACCEPTED        working-tree sha256 is in user_accepted for that path (user-authored)
    ATTRIBUTED      working-tree content == HEAD blob of the path (no uncommitted delta),
                    at least one commit in <plan_start>..HEAD (full history, merges
                    included) touches the path, and EVERY such commit (a) carries a
                    Claude-Session trailer, (b) has no trailer naming a plan session, and
                    (c) touches no plan-owned path
    UNATTRIBUTABLE  anything else, including a missing file or a symlink

Because history is read with --full-history, a trailer-less merge commit that touches a
frozen path also classifies the file UNATTRIBUTABLE (fail-closed, by design).

SESSION MATCHING. A trailer names a plan session when its session id equals a recorded
one. The id is the `session_...` part, so `https://claude.ai/code/session_X` and the bare
`session_X` are the same session. Anything else must match exactly (`session_Xy` is not
`session_X`).

PLAN-OWNED PATHS used by `check` are the union of the baseline's list and this script's
PLAN_OWNED_PATHS, so an out-of-date baseline cannot narrow the mixed-commit rule.

Exit codes: 0 = no UNATTRIBUTABLE file; 1 = at least one UNATTRIBUTABLE file;
2 = the guard could not do its job (missing/corrupt baseline, zero files compared,
frozen set mismatch, --repo-root not the git toplevel, plan start not an ancestor of
HEAD, a frame baseline present but not checkable yet, a pinned fixture missing from disk,
refused re-record/accept, or any unexpected exception). A guard that compared nothing
must never look green.

SUBCOMMANDS
    record-files            write baseline.json + frozen_files_at_baseline.diff.
                            With --force (re-record) it refuses if any file is
                            UNATTRIBUTABLE against the previous baseline.
    add-session <trailer>   add a Claude-Session trailer value to plan_sessions
    check                   report every frozen file's state (run at each phase end)
    accept <path> <sha256>  USER ONLY. Agents (developer, senior-developer, any Claude
                            session) must NEVER run this: it is how the user, in writing,
                            clears a file they have looked at. The sha256 must equal the
                            file's current content. It never changes worktree_sha256 or
                            any frame baseline.
    record-frames           Phase 0b (CP0.1b). Records, per fixture cell, the sha256 of
                            each recording's DECOMPRESSED payload and of run_meta.pkl,
                            plus the sha256 of the first 8 RAW frames V1 renders from it.
                            Frame hashes are computed in two separate processes, which
                            must agree, else the guard refuses (the plan's fallback is a
                            pixel-diff tolerance, to be recorded by hand).
    frame-worker            Internal. One process's frame hashes, as JSON on stdout.

FRAMES AT `check` TIME (plan section D5.4 item 4).
    fixture hash differs         -> FIXTURE CHANGED: the fixture was regenerated, so the
                                    frames are not comparable. Reported, frames skipped.
                                    Not a failure — fixtures live under gitignored
                                    results/ and may legitimately be regenerated or
                                    cleaned; re-record frames after confirming the
                                    generator commit.
    fixture missing              -> FIXTURE MISSING: a STRUCTURAL failure (exit 2), not a
                                    pass. The frame baseline pins something that is no
                                    longer on disk, so the frame half of the guard is
                                    comparing nothing — the "gate reports green at exactly
                                    the moment it stops working" shape recorded in
                                    KNOWN_BUGS.md (the extero-nociception byte-parity gate,
                                    which skipped for three months on a missing fixture).
                                    `--allow-missing-fixtures` tolerates it (exit 0) for
                                    the one legitimate case: the fixtures have not been
                                    generated yet, or gitignored results/ was cleaned and
                                    the caller knowingly wants the file-only verdict. The
                                    flag never masks a fixture that is PRESENT and
                                    disagrees.
    fixtures equal, frames equal -> FRAMES PASS.
    fixtures equal, frames differ-> UNATTRIBUTABLE when every frozen file is PASS
                                    (something outside the frozen set changed V1 output:
                                    an asset, a config, a library). When the frozen files
                                    that moved are ATTRIBUTED, the frames follow them and
                                    are reported ATTRIBUTED.

Stdlib only on the `check`/`record-files` path. Frame hashing runs V1 in a SUBPROCESS, so
matplotlib and numpy are imported only there, never into the guard itself. Git is called
read-only (`--no-optional-locks`, no index writes).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BASELINE_REL = (
    "docs/develop/active/refactors/renderer_layout_redesign/v1_guard/baseline.json"
)
DIFF_FILENAME = "frozen_files_at_baseline.diff"

# The ten frozen files (plan section D5.4 / File Changes "Frozen").
FROZEN_FILES = (
    "src/environment/renderer.py",
    "scripts/eval/render_recordings.py",
    "src/utils/async_render.py",
    "src/utils/evaluation_core.py",
    "src/algorithms/dreamer_srl/eval.py",
    "src/utils/eval_recording.py",
    "src/environment/sensor.py",
    "scripts/eval/benchmark_render.py",
    "src/environment/renderer_v2.py",
    "configs/visualization/default.yaml",
)

# Paths this plan owns (plan D5.4 UNATTRIBUTABLE row + File Changes). An entry containing
# a glob character is matched with fnmatch; otherwise it is a prefix ("dir/" is a
# directory, "tests/env/test_dashboard_" a filename prefix). A commit touching a frozen
# file AND any of these is UNATTRIBUTABLE whatever its trailer.
PLAN_OWNED_PATHS = (
    "src/environment/dashboard/",
    "scripts/eval/v1_path_guard.py",
    "scripts/eval/make_render_fixture_recordings.py",
    "scripts/eval/render_layout_audit.py",
    "scripts/eval/render_recordings_v2.py",
    "scripts/eval/episode_viewer.py",
    "scripts/eval/episode_viewer.html",
    "tests/env/test_v1_path_guard.py",
    "tests/env/test_render_audit_controls.py",
    "tests/env/test_dashboard_",
    "tests/scripts/test_render_recordings_v2.py",
    "tests/scripts/test_episode_viewer.py",
    "configs/environment/experiment/basic/*-campfire_thermal_*.yaml",
    "assets/fonts/dashboard_sans_tab/",
    "assets/dashboard_icons/",
    "assets/campfire.png",
    "docs/develop/active/refactors/renderer_layout_redesign/",
    "docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md",
)

# ---- frame baseline (CP0.1b) ------------------------------------------------------
# The fixture cells whose V1 output is pinned. All three are written by
# scripts/eval/make_render_fixture_recordings.py and live under gitignored `results/`, so
# they can be cleaned away. `check` treats that as a STRUCTURAL failure (exit 2): a frame
# baseline that pins a fixture nobody can find is a gate that compares nothing while
# printing a verdict. Regenerate the fixtures, or pass --allow-missing-fixtures to ask
# deliberately for the file-only verdict.
#
# M7 is deliberately ABSENT, although CP0.1b names it. M7 is the real pre-thermal
# trained-policy recording at
#   results/eval/noPredator_chasingRabbit/models/9520028/recordings/9520028
# and V1 cannot render it at current code: its pickled `EnvParams` predates the thermal
# system, while the FROZEN `src/environment/sensor.py::get_observation_breakdown` reads
# `params.thermal_enabled` unconditionally, so `render_recordings._render_episode` dies
# with `AttributeError: 'EnvParams' object has no attribute 'thermal_enabled'` (measured
# 2026-09-16 through `_worker_init` + `_render_episode`, the production path). There is no
# V1 frame to baseline. The plan's own answer is `_recording_flag` (section D4.1), which is
# Phase 1 code, and the frozen file may not be edited to make this cell pinnable.
DEFAULT_FRAME_CELLS = {
    "M1": "results/render_audit/recordings/M1/M1",
    "M2": "results/render_audit/recordings/M2/M2",
    "M4": "results/render_audit/recordings/M4/M4",
}
FRAME_STEPS = 8

PASS, ACCEPTED, ATTRIBUTED, UNATTRIBUTABLE = (
    "PASS", "ACCEPTED", "ATTRIBUTED", "UNATTRIBUTABLE",
)
FIXTURE_CHANGED, FIXTURE_MISSING, FRAMES_PASS = (
    "FIXTURE CHANGED", "FIXTURE MISSING", "FRAMES PASS",
)

EXIT_OK, EXIT_UNATTRIBUTABLE, EXIT_GUARD_ERROR = 0, 1, 2

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OID_RE = re.compile(r"^[0-9a-f]{40}$")


class GuardError(Exception):
    """The guard cannot produce a trustworthy verdict (exit 2)."""


# --------------------------------------------------------------------------- helpers


def _git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True, text=True,
    )
    if check and proc.returncode != 0:
        raise GuardError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _repo(args) -> Path:
    repo = Path(args.repo_root).resolve()
    top = _git(repo, "rev-parse", "--show-toplevel").strip()
    if Path(top).resolve() != repo:
        raise GuardError(f"--repo-root {repo} is not the git toplevel ({top})")
    return repo


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _head_blob(repo: Path, rel: str) -> str | None:
    proc = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), "rev-parse", "--verify",
         "--quiet", f"HEAD:{rel}"],
        capture_output=True, text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def _worktree_blob(repo: Path, rel: str) -> str:
    # hash-object without -w computes the blob id and writes nothing.
    return _git(repo, "hash-object", "--", rel).strip()


def _is_plan_owned(path: str, owned) -> bool:
    for p in owned:
        if any(ch in p for ch in "*?["):
            if fnmatch.fnmatchcase(path, p):
                return True
        elif path == p or path.startswith(p):
            return True
    return False


def session_id(value: str) -> str:
    """Canonical session id: the `session_...` part of a trailer value, else the value."""
    v = value.strip()
    i = v.rfind("session_")
    return v[i:] if i >= 0 else v


def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _resolve_baseline(repo: Path, baseline: str | None) -> Path:
    p = Path(baseline) if baseline else repo / DEFAULT_BASELINE_REL
    return p if p.is_absolute() else repo / p


def _require(cond: bool, path: Path, msg: str) -> None:
    if not cond:
        raise GuardError(f"baseline {path} is malformed: {msg}")


def _load_baseline(path: Path) -> dict:
    if not path.is_file():
        raise GuardError(f"baseline not found: {path} (run record-files first)")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise GuardError(f"baseline is not valid JSON: {path}: {exc}") from exc
    _require(isinstance(data, dict), path, "top level is not an object")
    for key in ("plan_start_commit", "frozen_files", "plan_sessions",
                "plan_owned_paths", "user_accepted"):
        _require(key in data, path, f"missing required key {key!r}")
    _require(isinstance(data["plan_start_commit"], str)
             and bool(_OID_RE.match(data["plan_start_commit"])),
             path, "plan_start_commit is not a 40-hex commit id")
    files = data["frozen_files"]
    _require(isinstance(files, dict), path, "frozen_files is not an object")
    if not files:
        raise GuardError(f"baseline {path} lists zero frozen files; nothing to compare")
    for rel, entry in files.items():
        _require(isinstance(entry, dict), path, f"entry for {rel!r} is not an object")
        sha = entry.get("worktree_sha256")
        _require(isinstance(sha, str) and bool(_SHA256_RE.match(sha)),
                 path, f"entry for {rel!r} has no valid worktree_sha256")
        hb = entry.get("head_blob")
        _require(hb is None or (isinstance(hb, str) and bool(_OID_RE.match(hb))),
                 path, f"entry for {rel!r} has an invalid head_blob")
    for key in ("plan_sessions", "plan_owned_paths"):
        _require(isinstance(data[key], list)
                 and all(isinstance(v, str) and v.strip() for v in data[key]),
                 path, f"{key} is not a list of non-empty strings")
    for s in data["plan_sessions"]:
        _require(session_id(s).startswith("session_"), path,
                 f"plan_sessions entry {s!r} is not a Claude session id")
    _require(isinstance(data["user_accepted"], list), path, "user_accepted is not a list")
    for a in data["user_accepted"]:
        _require(isinstance(a, dict) and isinstance(a.get("path"), str)
                 and isinstance(a.get("sha256"), str)
                 and bool(_SHA256_RE.match(a["sha256"])),
                 path, f"user_accepted entry {a!r} lacks a path or valid sha256")
    for key in ("fixtures", "frames"):
        if key in data:
            _require(isinstance(data[key], dict), path, f"{key} is not an object")
    for name, entry in data.get("fixtures", {}).items():
        _require(isinstance(entry, dict) and isinstance(entry.get("recordings_dir"), str)
                 and isinstance(entry.get("run_meta_sha256"), str)
                 and bool(_SHA256_RE.match(entry["run_meta_sha256"]))
                 and isinstance(entry.get("episodes"), dict) and entry["episodes"],
                 path, f"fixtures entry {name!r} is malformed")
    for name, entry in data.get("frames", {}).items():
        _require(isinstance(entry, dict) and isinstance(entry.get("episode"), str)
                 and isinstance(entry.get("sha256"), list) and bool(entry["sha256"])
                 and all(isinstance(s, str) and bool(_SHA256_RE.match(s))
                         for s in entry["sha256"]),
                 path, f"frames entry {name!r} is malformed")
    _require(set(data.get("frames", {})) <= set(data.get("fixtures", {})), path,
             "a frames entry has no matching fixtures entry, so it could never be checked")
    return data


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _write_baseline(path: Path, data: dict) -> None:
    _atomic_write_text(path, json.dumps(data, indent=2, sort_keys=False) + "\n")


# --------------------------------------------------------------------------- classify


def _commits_on_path(repo: Path, plan_start: str, rel: str) -> list[dict]:
    fmt = "%H%x1f%(trailers:key=Claude-Session,valueonly,separator=%x1d)%x1e"
    # --full-history: default history simplification can hide a side-branch commit
    # whose change also arrived on the main line (probe case B1).
    out = _git(repo, "log", "--full-history", f"--format={fmt}",
               f"{plan_start}..HEAD", "--", rel)
    commits = []
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, _, trailers = record.partition("\x1f")
        values = [v.strip() for v in trailers.split("\x1d") if v.strip()]
        touched = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r",
                       "-m", "--root", sha.strip()).split()
        commits.append({"sha": sha.strip(), "sessions": values,
                        "files": sorted(set(touched))})
    return commits


def classify_file(repo: Path, rel: str, entry: dict, data: dict,
                  owned) -> tuple[str, list[str]]:
    """Return (state, reasons) for one frozen file."""
    path = repo / rel
    if path.is_symlink():
        return UNATTRIBUTABLE, ["path is a symlink (type change)"]
    if not path.is_file():
        return UNATTRIBUTABLE, ["file is missing from the working tree"]
    wt_sha = sha256_file(path)
    if wt_sha == entry["worktree_sha256"]:
        return PASS, []
    accepted = {a["sha256"] for a in data["user_accepted"] if a["path"] == rel}
    if wt_sha in accepted:
        return ACCEPTED, [f"content {wt_sha[:12]} accepted by the user"]

    reasons = [f"content {wt_sha[:12]} != baseline {entry['worktree_sha256'][:12]}"]
    head = _head_blob(repo, rel)
    if head is None or _worktree_blob(repo, rel) != head:
        reasons.append("uncommitted delta on top of HEAD")
        return UNATTRIBUTABLE, reasons

    commits = _commits_on_path(repo, data["plan_start_commit"], rel)
    if not commits:
        reasons.append("content moved with no commit since plan start to attribute it to")
        return UNATTRIBUTABLE, reasons
    plan_ids = {session_id(s) for s in data["plan_sessions"]}
    bad = False
    for c in commits:
        short = c["sha"][:9]
        commit_bad = False
        if not c["sessions"]:
            reasons.append(f"{short}: no Claude-Session trailer")
            commit_bad = True
        elif plan_ids.intersection(session_id(s) for s in c["sessions"]):
            reasons.append(f"{short}: trailer is a plan session")
            commit_bad = True
        mixed = [f for f in c["files"] if _is_plan_owned(f, owned)]
        if mixed:
            reasons.append(f"{short}: also touches plan-owned path(s) {mixed}")
            commit_bad = True
        if not commit_bad:
            reasons.append(f"{short}: foreign session {c['sessions']}")
        bad = bad or commit_bad
    return (UNATTRIBUTABLE if bad else ATTRIBUTED), reasons


def _require_ancestor(repo: Path, plan_start: str) -> None:
    anc = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), "merge-base",
         "--is-ancestor", plan_start, "HEAD"], capture_output=True,
    )
    if anc.returncode != 0:
        raise GuardError(f"plan_start_commit {plan_start} is not an ancestor of HEAD")


def _owned_union(data: dict) -> list[str]:
    return sorted(set(data["plan_owned_paths"]) | set(PLAN_OWNED_PATHS))


# ------------------------------------------------------------------ fixtures and frames


def _gzip_payload_sha256(path: Path) -> str:
    """sha256 of a `.rec.gz`'s DECOMPRESSED bytes.

    gzip headers embed the write time, so hashing the file itself would report every
    regeneration as a change even when the recording is byte-identical (review finding 30).
    """
    import gzip
    h = hashlib.sha256()
    with gzip.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fixture_hashes(rec_dir: Path) -> dict:
    """`{'run_meta_sha256':…, 'episodes': {name: sha256}}` for one recordings directory."""
    if not rec_dir.is_dir():
        raise FileNotFoundError(f"recordings directory not found: {rec_dir}")
    meta = rec_dir / "run_meta.pkl"
    if not meta.is_file():
        raise FileNotFoundError(f"run_meta.pkl not found in {rec_dir}")
    episodes = sorted(rec_dir.glob("episode_*.rec.gz"))
    if not episodes:
        raise FileNotFoundError(f"no episode_*.rec.gz in {rec_dir}")
    return {"run_meta_sha256": sha256_file(meta),
            "episodes": {p.name: _gzip_payload_sha256(p) for p in episodes}}


def _frame_worker_hashes(repo: Path, rec_dir: Path, episode: str, steps: int) -> list:
    """Hash the first `steps` RAW frames V1 renders. Runs inside the frame-worker process.

    It drives the FROZEN offline renderer exactly as production does — `_worker_init` to
    fill `_WORKER_STATE` and warm the icon cache, then `_render_episode` — and captures the
    frames by monkeypatching `src.environment.renderer.save_jax_video`, the name
    `_render_episode` imports at call time. No MP4 is written and no frozen file is edited.

    The episode is first TRUNCATED to `steps` snapshots in a temp copy. Each frame depends
    only on that step's snapshot / obs / true_obs / action plus params, icon_config and the
    episode-wide `thermal_clim`, which is taken from snapshot 0 and therefore survives
    truncation; so the truncated frames are byte-identical to the full episode's first
    `steps` frames. Without truncation a 121-step fixture would render 121 frames per cell
    per process at every phase boundary.
    """
    import gzip as _gz
    import pickle
    import tempfile
    import numpy as np

    sys.path.insert(0, str(repo / "scripts" / "eval"))
    import render_recordings as rr
    import src.environment.renderer as renderer

    with _gz.open(rec_dir / episode, "rb") as fh:
        payload = pickle.load(fh)
    n = min(int(steps), len(payload["snapshots"]))
    cut = dict(payload)
    cut["snapshots"] = payload["snapshots"][:n]
    for key in ("obs", "actions", "rewards"):
        cut[key] = payload[key][:n]
    cut["true_obs"] = None if payload["true_obs"] is None else payload["true_obs"][:n]

    captured = {}

    def _capture(frames, output_path, fps=5, quiet=False):
        captured["frames"] = list(frames)

    original = renderer.save_jax_video
    with tempfile.TemporaryDirectory() as td:
        trunc = Path(td) / episode
        with _gz.open(trunc, "wb") as fh:
            pickle.dump(cut, fh, protocol=pickle.HIGHEST_PROTOCOL)
        rr._worker_init(str(rec_dir / "run_meta.pkl"))
        renderer.save_jax_video = _capture
        try:
            rr._render_episode(str(trunc), str(Path(td) / "unused.mp4"), 5)
        finally:
            renderer.save_jax_video = original
    return [hashlib.sha256(np.ascontiguousarray(f).tobytes()).hexdigest()
            for f in captured["frames"][:n]]


def _cell_frame_hashes(repo: Path, rec_dir: Path, episode: str, steps: int,
                       processes: int = 1) -> list:
    """Frame hashes from `processes` separate subprocesses, which must agree.

    Kept as one small seam so the guard's own tests can substitute it without rendering.
    """
    results = []
    for _ in range(max(1, int(processes))):
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--repo-root", str(repo),
             "frame-worker", str(rec_dir), episode, str(steps)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise GuardError(
                f"frame worker failed for {rec_dir}/{episode} "
                f"(exit {proc.returncode}):\n{proc.stderr.strip()}"
            )
        results.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    for other in results[1:]:
        if other != results[0]:
            raise GuardError(
                f"two processes disagree on the raw frames of {rec_dir}/{episode}. Agg "
                f"output is not byte-stable across processes on this machine, so a hash "
                f"baseline cannot be trusted; the plan's fallback is a pixel-diff "
                f"tolerance, to be measured and recorded by hand (CP0.1b)."
            )
    return results[0]


def _parse_cells(items) -> dict:
    if not items:
        return {}
    out = {}
    for item in items:
        if "=" not in item:
            raise GuardError(f"--cells entry {item!r} must be NAME=repo/relative/dir")
        name, rel = item.split("=", 1)
        out[name] = rel
    return out


def check_frames(repo: Path, data: dict, states: dict,
                 allow_missing: bool = False) -> bool:
    """Print every cell's fixture/frame verdict. True if any is UNATTRIBUTABLE.

    Raises GuardError (exit 2) if a pinned fixture is missing from disk, unless
    `allow_missing` — see the FIXTURE MISSING note in the module docstring.
    """
    fixtures, frames = data.get("fixtures"), data.get("frames")
    if not fixtures or not frames:
        print("== frames: NOT compared (no frame baseline yet; run record-frames — CP0.1b)")
        return False
    files_all_pass = all(s == PASS for s in states.values())
    moved = sorted(k for k, v in states.items() if v != PASS)
    bad = False
    missing = []
    print("== fixture + frame states")
    for name in sorted(frames):
        entry = frames[name]
        fx = fixtures.get(name, {})
        rel = fx.get("recordings_dir", "")
        rec_dir = repo / rel
        try:
            current = fixture_hashes(rec_dir)
        except FileNotFoundError as exc:
            tolerated = " (tolerated by --allow-missing-fixtures)" if allow_missing else ""
            print(f"  {FIXTURE_MISSING:<15} {name}  {exc}; frames NOT compared{tolerated}")
            missing.append(f"{name}: {exc}")
            continue
        if (current["run_meta_sha256"] != fx.get("run_meta_sha256")
                or current["episodes"] != fx.get("episodes")):
            print(f"  {FIXTURE_CHANGED:<15} {name}  the fixture was regenerated; frames "
                  f"NOT compared (re-record only after confirming the generator commit)")
            continue
        got = _cell_frame_hashes(repo, rec_dir, entry["episode"],
                                 entry.get("steps", FRAME_STEPS))
        if got == entry["sha256"]:
            print(f"  {FRAMES_PASS:<15} {name}  {len(got)} raw frames identical")
            continue
        differing = [i for i, (a, b) in enumerate(zip(got, entry["sha256"])) if a != b]
        if len(got) != len(entry["sha256"]):
            differing.append(f"count {len(got)} != {len(entry['sha256'])}")
        if files_all_pass:
            print(f"  {UNATTRIBUTABLE:<15} {name}  frames differ at {differing} while every "
                  f"frozen file is PASS — something OUTSIDE the frozen set changed V1 "
                  f"output (an asset, a config, or a library)")
            bad = True
        else:
            print(f"  {ATTRIBUTED:<15} {name}  frames differ at {differing}; follows the "
                  f"moved frozen file(s) {moved}")
    if missing and not allow_missing:
        raise GuardError(
            "the frame baseline pins fixture(s) that are not on disk, so the frame gate "
            "compared nothing:\n  " + "\n  ".join(missing) +
            "\nRegenerate them with scripts/eval/make_render_fixture_recordings.py, or "
            "pass --allow-missing-fixtures to ask for the frozen-file verdict alone "
            "(only legitimate when the fixtures have not been generated yet)."
        )
    return bad


# --------------------------------------------------------------------------- commands


def cmd_record_files(args) -> int:
    repo = _repo(args)
    frozen = list(args.frozen) if args.frozen else list(FROZEN_FILES)
    owned = list(args.plan_owned) if args.plan_owned else list(PLAN_OWNED_PATHS)
    baseline_path = _resolve_baseline(repo, args.baseline)

    previous = None
    if baseline_path.exists():
        if not args.force:
            raise GuardError(
                f"baseline already exists: {baseline_path}. Re-recording is allowed only "
                f"after an ATTRIBUTED verdict, citing the foreign commits; pass --force. "
                f"An UNATTRIBUTABLE file is never re-baselined."
            )
        previous = _load_baseline(baseline_path)
        _require_ancestor(repo, previous["plan_start_commit"])
        owned = sorted(set(owned) | set(previous["plan_owned_paths"]))
        prev_owned = _owned_union(previous)
        blocked = []
        for rel, entry in previous["frozen_files"].items():
            state, reasons = classify_file(repo, rel, entry, previous, prev_owned)
            if state == UNATTRIBUTABLE:
                blocked.append(f"{rel}: {'; '.join(reasons)}")
        if blocked:
            raise GuardError(
                "refusing to re-record: file(s) are UNATTRIBUTABLE against the previous "
                "baseline (only the user clears these):\n  " + "\n  ".join(blocked)
            )

    bad = [rel for rel in frozen
           if (repo / rel).is_symlink() or not (repo / rel).is_file()]
    if bad:
        raise GuardError(f"frozen file(s) missing or symlinked, cannot record: {bad}")

    plan_start = _git(repo, "rev-parse", "HEAD").strip()
    files = {
        rel: {"worktree_sha256": sha256_file(repo / rel),
              "head_blob": _head_blob(repo, rel)}
        for rel in frozen
    }
    data = {
        "description": (
            "V1 video-path guard baseline for RENDERER_LAYOUT_REDESIGN.md (section D5.4). "
            "Written by scripts/eval/v1_path_guard.py; do not hand-edit. user_accepted "
            "entries are added by the user only, via the accept subcommand."
        ),
        "recorded_at": _now(),
        "plan_start_commit": plan_start,
        "frozen_files": files,
        "plan_sessions": list(previous["plan_sessions"]) if previous else [],
        "plan_owned_paths": owned,
        "user_accepted": list(previous["user_accepted"]) if previous else [],
    }
    if previous:
        data["rerecorded_from_plan_start_commit"] = previous["plan_start_commit"]
        data["rerecord_note"] = args.note or ""

    diff = _git(repo, "diff", plan_start, "--", *frozen)
    header = (
        f"# SNAPSHOT of other sessions' uncommitted work-in-progress at guard baseline "
        f"({_dt.date.today().isoformat()}). Record only; DO NOT apply.\n"
    )
    _write_baseline(baseline_path, data)
    diff_path = baseline_path.parent / DIFF_FILENAME
    _atomic_write_text(diff_path, header + diff)

    print(f"baseline written: {baseline_path}")
    print(f"diff written:     {diff_path} ({len(diff.splitlines())} diff lines)")
    print(f"plan_start_commit {plan_start}")
    for rel, e in files.items():
        dirty = "clean" if e["head_blob"] == _worktree_blob(repo, rel) else "DIRTY vs HEAD"
        print(f"  {e['worktree_sha256'][:12]}  {rel}  ({dirty})")
    return EXIT_OK


def cmd_add_session(args) -> int:
    repo = _repo(args)
    baseline_path = _resolve_baseline(repo, args.baseline)
    data = _load_baseline(baseline_path)
    value = args.session.strip()
    if not session_id(value).startswith("session_"):
        raise GuardError(
            f"not a Claude session id: {value!r} (expected "
            f"'https://claude.ai/code/session_...' or 'session_...')"
        )
    if session_id(value) in {session_id(s) for s in data["plan_sessions"]}:
        print(f"already recorded: {value}")
        return EXIT_OK
    data["plan_sessions"].append(value)
    _write_baseline(baseline_path, data)
    print(f"plan_sessions += {value}")
    return EXIT_OK


def cmd_accept(args) -> int:
    repo = _repo(args)
    baseline_path = _resolve_baseline(repo, args.baseline)
    data = _load_baseline(baseline_path)
    rel = args.path
    if rel not in data["frozen_files"]:
        raise GuardError(f"{rel!r} is not a frozen file in the baseline")
    sha = args.sha256.strip().lower()
    if not _SHA256_RE.match(sha):
        raise GuardError(f"not a sha256 hex digest: {args.sha256!r}")
    path = repo / rel
    if path.is_symlink() or not path.is_file():
        raise GuardError(f"{rel} is missing or a symlink; nothing to accept")
    current = sha256_file(path)
    if current != sha:
        raise GuardError(
            f"{rel} currently hashes to {current}, not {sha}; accept only the exact "
            f"content you looked at"
        )
    data["user_accepted"].append(
        {"path": rel, "sha256": sha, "date": _now(), "note": args.note or ""}
    )
    _write_baseline(baseline_path, data)
    print(f"user_accepted += {rel} {sha[:12]}")
    return EXIT_OK


def cmd_record_frames(args) -> int:
    repo = _repo(args)
    baseline_path = _resolve_baseline(repo, args.baseline)
    data = _load_baseline(baseline_path)
    cells = _parse_cells(args.cells) or dict(DEFAULT_FRAME_CELLS)
    if "frames" in data or "fixtures" in data:
        if not args.force:
            raise GuardError(
                f"{baseline_path} already carries a frame baseline. Re-recording frames is "
                f"exactly how a real V1 output change would be hidden, so it takes --force "
                f"and a --note citing why."
            )
        if not (args.note or "").strip():
            raise GuardError(
                f"{baseline_path} already carries a frame baseline and --force was given "
                f"without --note. Both are required, exactly as the refusal above says: "
                f"the reason for a re-record is recorded in the baseline (frames_note) or "
                f"it is not a re-record anyone can audit."
            )
    fixtures, frames = {}, {}
    for name, rel in cells.items():
        rec_dir = repo / rel
        try:
            fx = fixture_hashes(rec_dir)
        except FileNotFoundError as exc:
            raise GuardError(f"cell {name}: {exc}") from exc
        episode = sorted(fx["episodes"])[0]
        hashes = _cell_frame_hashes(repo, rec_dir, episode, args.steps, processes=2)
        fixtures[name] = {"recordings_dir": rel, **fx}
        frames[name] = {"episode": episode, "steps": len(hashes), "sha256": hashes}
        print(f"  {name}: {len(fx['episodes'])} episode(s); {len(hashes)} raw frames from "
              f"{episode}; two processes agree (first {hashes[0][:12]})")
    data["fixtures"] = fixtures
    data["frames"] = frames
    data["frames_recorded_at"] = _now()
    if args.note:
        data["frames_note"] = args.note
    _write_baseline(baseline_path, data)
    print(f"frame baseline written: {baseline_path}")
    return EXIT_OK


def cmd_frame_worker(args) -> int:
    """Internal: one process's raw-frame hashes, as JSON on stdout."""
    hashes = _frame_worker_hashes(Path(args.repo_root).resolve(), Path(args.rec_dir),
                                  args.episode, args.steps)
    print(json.dumps(hashes))
    return EXIT_OK


def cmd_check(args) -> int:
    repo = _repo(args)
    baseline_path = _resolve_baseline(repo, args.baseline)
    data = _load_baseline(baseline_path)
    expected = sorted(args.frozen) if args.frozen else sorted(FROZEN_FILES)
    recorded = sorted(data["frozen_files"])
    if recorded != expected:
        raise GuardError(
            f"baseline frozen set does not match the guard's frozen set.\n"
            f"  only in baseline: {sorted(set(recorded) - set(expected))}\n"
            f"  only in guard:    {sorted(set(expected) - set(recorded))}"
        )
    plan_start = data["plan_start_commit"]
    _require_ancestor(repo, plan_start)
    owned = _owned_union(data)
    drift = sorted(set(PLAN_OWNED_PATHS) - set(data["plan_owned_paths"]))

    frozen = recorded
    print(f"== git diff --stat {plan_start[:12]} -- <frozen files>")
    print(_git(repo, "diff", "--stat", plan_start, "--", *frozen).rstrip() or "(none)")
    print(f"== git log --full-history {plan_start[:12]}..HEAD -- <frozen files> "
          f"(Claude-Session trailers)")
    log = _git(repo, "log", "--full-history",
               "--format=%h %(trailers:key=Claude-Session,valueonly,separator=%x2C) %s",
               f"{plan_start}..HEAD", "--", *frozen)
    print(log.rstrip() or "(none)")
    if drift:
        print(f"== note: plan-owned paths not in baseline (applied anyway): {drift}")

    print("== frozen file states")
    states = {}
    for rel in frozen:
        state, reasons = classify_file(repo, rel, data["frozen_files"][rel], data, owned)
        states[rel] = state
        print(f"  {state:<15} {rel}")
        for r in reasons:
            print(f"                  - {r}")
    compared = len(states)
    if compared == 0:
        raise GuardError("zero frozen files were compared")
    counts = {s: sum(1 for v in states.values() if v == s)
              for s in (PASS, ACCEPTED, ATTRIBUTED, UNATTRIBUTABLE)}
    print(f"== compared {compared} file(s): " +
          ", ".join(f"{k}={v}" for k, v in counts.items()))
    frames_bad = check_frames(repo, data, states,
                              allow_missing=args.allow_missing_fixtures)
    if counts[UNATTRIBUTABLE] or frames_bad:
        print("RESULT: FAIL (UNATTRIBUTABLE; only the user clears this)")
        return EXIT_UNATTRIBUTABLE
    print("RESULT: OK")
    return EXIT_OK


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--repo-root", default=str(REPO_ROOT))
    p.add_argument("--baseline", default=None,
                   help=f"baseline JSON (default: <repo>/{DEFAULT_BASELINE_REL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record-files", help="write the file-hash baseline")
    r.add_argument("--frozen", nargs="+", default=None,
                   help="override the frozen set (tests only)")
    r.add_argument("--plan-owned", nargs="+", default=None,
                   help="override plan-owned paths (tests only)")
    r.add_argument("--force", action="store_true",
                   help="overwrite an existing baseline; refused if any file is "
                        "UNATTRIBUTABLE against it")
    r.add_argument("--note", default=None)
    r.set_defaults(func=cmd_record_files)

    s = sub.add_parser("add-session", help="record a plan session trailer value")
    s.add_argument("session")
    s.set_defaults(func=cmd_add_session)

    c = sub.add_parser("check", help="assign each frozen file a state")
    c.add_argument("--frozen", nargs="+", default=None,
                   help="override the expected frozen set (tests only)")
    c.add_argument("--allow-missing-fixtures", action="store_true",
                   help="exit 0 on a pinned fixture that is not on disk, reporting the "
                        "frozen-file verdict alone, instead of failing with exit 2. Only "
                        "legitimate when the fixtures have not been generated yet; it "
                        "never tolerates a fixture that is present and disagrees.")
    c.set_defaults(func=cmd_check)

    a = sub.add_parser("accept", help="USER ONLY: accept exact current content of a "
                                      "frozen file. Agents must never run this.")
    a.add_argument("path")
    a.add_argument("sha256")
    a.add_argument("--note", default=None)
    a.set_defaults(func=cmd_accept)

    f = sub.add_parser("record-frames",
                       help="Phase 0b: record the fixture + raw-frame baseline (CP0.1b)")
    f.add_argument("--cells", nargs="+", default=None,
                   help="NAME=repo/relative/recordings/dir entries "
                        f"(default: {sorted(DEFAULT_FRAME_CELLS)})")
    f.add_argument("--steps", type=int, default=FRAME_STEPS,
                   help="how many leading frames to hash per cell")
    f.add_argument("--force", action="store_true",
                   help="overwrite an existing frame baseline (needs --note)")
    f.add_argument("--note", default=None)
    f.set_defaults(func=cmd_record_frames)

    w = sub.add_parser("frame-worker",
                       help="internal: print one process's raw-frame hashes as JSON")
    w.add_argument("rec_dir")
    w.add_argument("episode")
    w.add_argument("steps", type=int)
    w.set_defaults(func=cmd_frame_worker)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except GuardError as exc:
        print(f"GUARD ERROR: {exc}", file=sys.stderr)
        return EXIT_GUARD_ERROR
    except Exception:  # never let a crash look like a verdict (exit 1)
        traceback.print_exc()
        print("GUARD ERROR: unexpected exception (see traceback)", file=sys.stderr)
        return EXIT_GUARD_ERROR


if __name__ == "__main__":
    sys.exit(main())
