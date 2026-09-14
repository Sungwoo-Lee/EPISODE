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
HEAD, a frame baseline present but not checkable yet, refused re-record/accept, or any
unexpected exception). A guard that compared nothing must never look green.

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
    record-frames           Phase 0b (CP0.1b); not implemented yet, refuses to run.

Stdlib only. Git is called read-only (`--no-optional-locks`, no index writes).
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

PASS, ACCEPTED, ATTRIBUTED, UNATTRIBUTABLE = (
    "PASS", "ACCEPTED", "ATTRIBUTED", "UNATTRIBUTABLE",
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
    raise GuardError(
        "record-frames belongs to Phase 0b (CP0.1b) and is not implemented yet; it runs "
        "after make_render_fixture_recordings.py lands."
    )


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
    if "frames" in data or "fixtures" in data:
        raise GuardError(
            "baseline carries a frame/fixture baseline, but frame checking is not "
            "implemented in this version of the guard (Phase 0b). Refusing to report "
            "files only while frames go uncompared."
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
    print("== frames: NOT compared (no frame baseline yet; record-frames is Phase 0b)")
    if counts[UNATTRIBUTABLE]:
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
    c.set_defaults(func=cmd_check)

    a = sub.add_parser("accept", help="USER ONLY: accept exact current content of a "
                                      "frozen file. Agents must never run this.")
    a.add_argument("path")
    a.add_argument("sha256")
    a.add_argument("--note", default=None)
    a.set_defaults(func=cmd_accept)

    f = sub.add_parser("record-frames", help="Phase 0b; not implemented yet")
    f.set_defaults(func=cmd_record_frames)
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
