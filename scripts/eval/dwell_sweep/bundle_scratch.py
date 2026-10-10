#!/usr/bin/env python
"""Migrate old behaviour-test sweep folders to one archive per checkpoint x scene cell, and check
the archives (plan docs/develop/active/refactors/SWEEP_EPISODE_BUNDLES_AND_ON_NODE_MEASURES.md, F7).

A sweep root is an output folder holding `_scratch/<run_label>/<cond>/<step>/` cell folders (class S;
class D was dropped from the plan on 2026-10-07). Commands (ROOT = output folder; `--all` = every
class-S root under results/eval/):

  inventory [ROOT ...|--all] [--deep]   read-only; per root: legacy/archived cells, (files, bytes with
                                        --deep), held / live / missing-checkpoint flags -> tmp/ CSV
  backup-tables                         copy every per-scene CSV, FIG_*.png, *.html and _provenance/
                                        under results/eval/ to results/_backup/eval_tables_<stamp>/,
                                        sha256-checked; required before any delete
  pack ROOT [--into GATE] [--dry-run]   archive every legacy cell (originals untouched). --into writes
                                        the archives into GATE/_scratch/... instead (read-only use of
                                        ROOT; the only way to pack a held root)
  verify ROOT [--into GATE]             byte-compare every (folder, archive) pair -> _bundle_log report
  gate ROOT [--into GATE] [--episodes N]   Gate G1: score every archive into an EMPTY table (no CSV
                                        seeding) and compare with ROOT's per-scene CSVs, zero tolerance
  independent-check ROOT [--sample N]   on a host other than the packing host: system unzip + diff -r
  delete ROOT                           remove the verified originals (episode_bundle.delete_verified)
  extract ZIP DEST                      unpack one archive into a folder (for folder-based tools)
  unlock ROOT                           print and remove a migration lock

Automatic exclusions (fail closed):
  E1 live: run markers without a later done_, a fresh alive_, an unfinished collation, all done_
     but no CSV newer than them ("possibly collating"), or a sweep driver/worker process on this
     host naming the root. A sweep whose node died is reported the same way until a human
     resolves it (plan-review N4).
  E2 unswitched reader: a file under scripts/ src/ tests/ that mentions sweep episodes and is in
     neither SWITCHED_READERS nor NON_READERS blocks DELETE for every root (pack/verify allowed).
  E3 lock: <root>/_scratch/_bundle.lock while pack or delete runs.
  E4 session hold: SESSION_HOLDS -- neither pack (without --into) nor delete touches a held cell.
"""
import argparse
import csv
import datetime
import json
import multiprocessing as mp
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "behavior_measures"))
sys.path.insert(0, str(_HERE.parent))
import src.utils.episode_bundle as EB  # noqa: E402

EVAL_ROOT = REPO_ROOT / "results" / "eval"
BACKUP_ROOT = REPO_ROOT / "results" / "_backup"
LOCK_STALE_S = 6 * 3600
ALIVE_FRESH_S = 600
_DIG = re.compile(r"[0-9]+")

# ---- E4: holds requested by the "Training: neuromodulation" session (2026-10-07). Lift only on that
# session's explicit word, recorded in the plan's Implementation Report (date + source).
SESSION_HOLDS = {
    "runs": [
        "20261005-160124_rppo_healrep_l05_t1none_s42",
        "20261005-160125_rppo_healrep_l05_t1none_s43",
        "20261005-160241_rppo_healrep_l05_t16quad_s42",
        "20261005-160244_rppo_healrep_l05_t16quad_s43",
        "20261006-074127_rppo_healrep_l05fix_t1none_s42",
        "20261006-074133_rppo_healrep_l05fix_t16quad_s42",
        "20260922-182534_rppo_bq2cover_lvl05_t1none_s42",
        "20260922-182538_rppo_bq2cover_lvl05_t16quad_s42",
    ],
    "roots": ["metrics_history_rppo_modeng_e4", "metrics_history_rppo_case_l05_s42"],
}

# ---- E2: readers of sweep-cell episodes verified to work on archives (plan Phase 2 / 3).
SWITCHED_READERS = {"S": [
    "scripts/eval/dwell_sweep/run_sweep.py",               # R1 (Phase 3)
    "scripts/eval/dwell_sweep/cell_measures.py",           # R1's row arithmetic (Phase 3)
    "scripts/analysis/studies/f7b_across_runs/aggregate_only.py",   # R2 (Phase 3)
    "scripts/analysis/basic_behaviour/probe_pond.py",      # R4 (Phase 2, 2026-10-07)
    "scripts/analysis/studies/basicq2_waves/_traj.py",     # R5
    "scripts/analysis/studies/thermal_probes/t04_variance_budget.py",  # R6
    "scripts/analysis/studies/injury_dependence/scene_steps.py",       # R7
    "scripts/analysis/studies/injury_dependence/run_manipulations.py",  # R8 (passes a cond dir to R9)
    "scripts/analysis/obs_manipulation/run.py",            # R9 (Phase 3 pass, 2026-10-11)
    "scripts/analysis/case_l05_s42/case.py",               # R10
    "tests/analysis/test_case_l05_s42.py",                 # R11
    "tests/analysis/test_modulator_engagement.py",         # R12
    "scripts/analysis/modinput_internals/internals.py",    # precondition() (added 2026-10-11)
    "tests/scripts/test_bundle_readers.py",                # tests of R4-R7 on both forms
]}

# ---- E2: files the reader grep matches that do NOT read sweep-cell episodes (review N7).
NON_READERS = {
    "src/utils/episode_bundle.py": "the archive library itself",
    "src/utils/eval_recording.py": "writer + load_episode definition",
    "src/utils/evaluation_core.py": "writes recordings during eval",
    "src/utils/async_render.py": "renders recordings of training-time eval",
    "src/algorithms/dreamer_srl/eval.py": "Dreamer eval writer",
    "src/algorithms/dreamer_srl/dreamer_srl_main.py": "Dreamer training entry (eval recordings it wrote)",
    "src/environment/dashboard/episode.py": "dashboard renderer of a given recording file",
    "scripts/eval/eval_rollout.py": "the test program (writer)",
    "scripts/eval/dwell_sweep/sweep_worker.sh": "worker (writes staging, calls finish_cells.py)",
    "scripts/eval/dwell_sweep/finish_cells.py": "on-node packer/scorer of fresh staging folders",
    "scripts/eval/dwell_sweep/bundle_scratch.py": "this migration tool",
    "scripts/eval/experiment_eval_checkpoint.py": "during-training eval of its own output folders",
    "scripts/behavior_measures/avoidance_stats_heatmap.py": "episode_measures; collect mode reads class-D test folders",
    "scripts/eval/continual_forgetting_matrix.py": "its own <prefix>_scratch, not a sweep root",
    "scripts/eval/parity_check_eval_rollout.py": "class-D test folders (legacy vs batched)",
    "scripts/eval/trajectory_story.py": "recordings directory given on the command line (class D)",
    "scripts/eval/render_recordings.py": "recordings directory given on the command line",
    "scripts/eval/render_recordings_v2.py": "recordings directory given on the command line",
    "scripts/eval/render_layout_audit.py": "recordings directory given on the command line",
    "scripts/eval/make_render_fixture_recordings.py": "writes render fixtures",
    "scripts/eval/dreamer_srl_probe_eval.py": "Dreamer probe eval writer",
    "scripts/eval/traj_collect/run_collection.py": "trajectory-store pipeline's own _scratch",
    "scripts/analysis/studies/level05_body_interactions/launch_collection.py": "trajectory-store pipeline's _scratch",
    "scripts/analysis/studies/continual_worlds/pilot_readout.py": "training-log 'scratch' runs, not episodes",
    "scripts/analysis/basic_behaviour/golden_gate.py": "_golden_scratch CSV gate",
    "scripts/analysis/studies/hypervigilance/golden_check.py": "_golden_scratch CSV gate",
    "scripts/dreamer/dreamer_srl_offline_wm_test.py": "Dreamer offline recordings",
    "scripts/dreamer/visualize_dream.py": "Dreamer recordings",
    "tests/scripts/test_episode_bundle.py": "synthetic cells in a temp dir",
    "tests/scripts/test_dwell_sweep_collate.py": "synthetic cells in a temp dir",
    "tests/scripts/test_bundle_scratch.py": "synthetic roots in a temp dir",
    "tests/algorithms/dreamer_srl/test_eval_recording.py": "writer tests",
    "tests/algorithms/dreamer_srl/test_eval_rollout_batched.py": "test-program tests (temp dirs)",
    "tests/algorithms/dreamer_srl/test_eval_rollout.py": "test-program tests (temp dirs)",
    "tests/algorithms/dreamer_srl/test_eval_video_smoke.py": "render tests",
    "tests/algorithms/dreamer_srl/test_render_upload.py": "render tests",
    "tests/env/test_dashboard_frames.py": "dashboard tests",
    "tests/env/test_dashboard_v1_imports.py": "dashboard tests",
    "tests/env/test_dashboard_water.py": "dashboard tests",
    "tests/env/test_render_audit_controls.py": "render tests",
    "tests/scripts/test_render_recordings_v2.py": "render tests",
    "tests/test_trajectory_collection.py": "trajectory-store tests",
    "tests/training/test_async_render_dispatch.py": "render tests",
}
READER_PATTERN = re.compile(r"rec\.gz|load_episode|_scratch")


# ------------------------------------------------------------------------------- roots/cells ----
def all_roots():
    """Every class-S root (a folder holding `_scratch/`) under results/eval/."""
    out = []
    for root, dirs, _files in os.walk(EVAL_ROOT):
        if "_scratch" in dirs:
            out.append(Path(root))
        dirs[:] = [d for d in dirs if not d.startswith("_")]
    return sorted(out)


def cells(root, newest=None):
    """[(label, cond, step, folder_or_None, zip_or_None)] for every cell under ROOT/_scratch;
    with `newest`, only the newest N steps of each (label, cond)."""
    out = []
    scr = Path(root) / "_scratch"
    for lab in sorted(os.listdir(scr)) if scr.is_dir() else []:
        if lab.startswith("_") or not (scr / lab).is_dir():
            continue
        for cond in sorted(os.listdir(scr / lab)):
            cd = scr / lab / cond
            if cond.startswith("_") or not cd.is_dir():
                continue
            steps = sorted(EB.step_names(cd), key=int)
            for s in (steps[-newest:] if newest else steps):
                d, z = cd / s, cd / f"{s}{EB.BUNDLE_SUFFIX}"
                out.append((lab, cond, int(s), d if d.is_dir() else None, z if z.is_file() else None))
    return out


def _rel(p):
    try:
        return str(Path(p).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


# ----------------------------------------------------------------------------------- E4 hold ----
def label_runs(root):
    """{label: run dir name} from the root's provenance, else its worklists. Unresolved labels
    are absent (and therefore held)."""
    root = Path(root)
    out = {}
    for p in sorted((root / "_provenance").glob("*/provenance.json")):
        try:
            for r in json.loads(p.read_text()).get("runs", []):
                out[r["label"]] = Path(r["path"]).name
        except (OSError, json.JSONDecodeError, KeyError):
            pass
    for wl in sorted((root / "_scratch" / "_worklists").glob("worklist_*.txt")):
        for line in wl.read_text().splitlines():
            parts = line.split("|")
            if len(parts) < 4:
                continue
            ck = Path(parts[0])
            run = ck.parent.parent.name          # <run>/models/<step> or <run>/checkpoints/<ep>
            for pair in parts[3].split(";"):
                out_dir = Path(pair.split(",", 1)[-1])
                if out_dir.parent.parent.parent.name == "_scratch":
                    out.setdefault(out_dir.parent.parent.name, run)
    return out


def held_labels(root):
    """(held set, reason) for a root. Every label of a held root is held; labels that cannot be
    resolved to a run are held (fail closed)."""
    root = Path(root)
    labs = sorted({c[0] for c in cells(root)})
    if any(part in SESSION_HOLDS["roots"] for part in root.parts):
        return set(labs), "held root"
    runs = label_runs(root)
    held = {lab for lab in labs if runs.get(lab) is None or runs[lab] in SESSION_HOLDS["runs"]}
    return held, "held run or unresolved label"


# ----------------------------------------------------------------------------------- E1 live ----
def live_reasons(root, now=None, ps_lines=None):
    """Reasons ROOT may be live (empty list = clear)."""
    now = time.time() if now is None else now
    root = Path(root)
    mark = root / "_scratch" / "_run_markers"
    why = []
    if mark.is_dir():
        names = set(os.listdir(mark))
        nodes = {n.split("_", 1)[1] for n in names
                 if "." not in n and n.split("_", 1)[0] in ("npar", "started")}
        dones = []
        for n in sorted(nodes):
            st = max((mark / f"{k}_{n}").stat().st_mtime for k in ("npar", "started") if f"{k}_{n}" in names)
            if f"done_{n}" not in names:
                why.append(f"node {n}: started, no done_ (live, or dead and unresolved)")
            elif (mark / f"done_{n}").stat().st_mtime < st:
                why.append(f"node {n}: started after its last done_")
            else:
                dones.append((mark / f"done_{n}").stat().st_mtime)
            a = mark / f"alive_{n}"
            if a.exists() and now - a.stat().st_mtime < ALIVE_FRESH_S:
                why.append(f"node {n}: alive_ {now - a.stat().st_mtime:.0f}s old")
        for n in sorted(names):
            if n.startswith("collate_") and n.endswith(".started"):
                cid = n[len("collate_"):-len(".started")]
                if f"collate_{cid}.done" not in names and f"collate_{cid}.failed" not in names:
                    why.append(f"collation {cid} started, not finished")
        if dones and not why:
            newest_done = max(dones)
            csvs = [p.stat().st_mtime for p in root.glob("*/*.csv")]
            if not csvs or max(csvs) < newest_done:
                why.append("all workers done but no per-scene CSV newer than them (possibly collating)")
    if ps_lines is None:
        ps_lines = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
    rel = _rel(root)
    for line in ps_lines:
        if not re.search(r"run_sweep\.py|aggregate_only\.py|sweep_worker\.sh", line):
            continue
        if str(os.getpid()) == line.split(None, 1)[0]:
            continue
        if rel in line or str(root) in line:
            why.append(f"process names the root: {line.strip()[:200]}")
            continue
        for tok in line.split():
            if tok.endswith((".yaml", ".yml")):
                p = Path(tok) if Path(tok).is_absolute() else REPO_ROOT / tok
                try:
                    import yaml
                    sp = yaml.safe_load(p.read_text()) or {}
                except Exception:
                    continue
                od = sp.get("output_dir") or f"results/eval/avoidance/{sp.get('name')}"
                if Path(od).as_posix().rstrip("/") == rel:
                    why.append(f"driver for this root: {line.strip()[:200]}")
    return why


# -------------------------------------------------------------------------------- E2 readers ----
def unswitched_readers(trees=("scripts", "src", "tests"), repo=REPO_ROOT):
    known = set(SWITCHED_READERS["S"]) | set(NON_READERS)
    hits = []
    for t in trees:
        for dirpath, dirs, files in os.walk(Path(repo) / t):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if not f.endswith((".py", ".sh")):
                    continue
                p = Path(dirpath) / f
                rel = p.relative_to(repo).as_posix()
                try:
                    if READER_PATTERN.search(p.read_text(errors="ignore")) and rel not in known:
                        hits.append(rel)
                except OSError:
                    pass
    return sorted(hits)


# ----------------------------------------------------------------------------------- E3 lock ----
def lock_is_stale(lock, now=None):
    now = time.time() if now is None else now
    lock = Path(lock)
    try:
        info = json.loads(lock.read_text())
    except (OSError, json.JSONDecodeError):
        info = {}
    if now - lock.stat().st_mtime > LOCK_STALE_S:
        return True
    if info.get("host") == socket.gethostname():
        try:
            os.kill(int(info.get("pid", -1)), 0)
        except (ProcessLookupError, ValueError):
            return True
        except PermissionError:
            return False
    return False


class Lock:
    def __init__(self, root):
        self.path = Path(root) / "_scratch" / "_bundle.lock"

    def __enter__(self):
        fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, json.dumps({"host": socket.gethostname(), "pid": os.getpid(),
                                 "start": time.time()}).encode())
        os.close(fd)
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


# ----------------------------------------------------------------------------------- reports ----
def _log_dir(root):
    d = Path(root) / "_scratch" / "_bundle_log"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _report(root, kind, rows, header, all_ok, extra=None):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = _log_dir(root) / f"{kind}_{socket.gethostname()}_{stamp}"
    with open(f"{base}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    summary = {"kind": kind, "host": socket.gethostname(), "time": stamp, "all_ok": bool(all_ok),
               "n": len(rows), **(extra or {})}
    Path(f"{base}.json").write_text(json.dumps(summary, indent=1))
    return summary


def _latest(root, kind, host=None):
    hits = sorted(_log_dir(root).glob(f"{kind}_{host or '*'}_*.json"))
    return json.loads(hits[-1].read_text()) if hits else None


# ------------------------------------------------------------------------------- operations ----
def _target(root, into, lab, cond, step):
    base = Path(into) if into else Path(root)
    return base / "_scratch" / lab / cond / f"{step}{EB.BUNDLE_SUFFIX}"


def _pack_one(args):
    folder, zp = args
    zp = Path(zp)
    for p in zp.parent.glob(zp.name + ".partial-*"):
        p.unlink()                                   # leftover from a killed pack: redo
    if zp.exists():
        try:
            EB.verify(folder, zp)
            return (str(folder), "exists-ok", "")
        except EB.BundleMismatch as e:
            return (str(folder), "exists-MISMATCH", str(e)[:300])
    zp.parent.mkdir(parents=True, exist_ok=True)
    try:
        man = EB.pack(folder, zp)
        return (str(folder), "packed", str(len(man)))
    except Exception as e:  # noqa: BLE001 -- reported per cell
        return (str(folder), "FAILED", f"{type(e).__name__}: {e}"[:300])


def _verify_one(args):
    folder, zp = args
    try:
        man = EB.verify(folder, zp)
        return (str(folder), str(zp), "ok", str(len(man)))
    except Exception as e:  # noqa: BLE001
        return (str(folder), str(zp), "MISMATCH", f"{type(e).__name__}: {e}"[:300])


def _pool_map(fn, items, workers):
    if workers <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    with mp.Pool(workers) as pool:
        return pool.map(fn, items, chunksize=4)


def cmd_pack(root, into=None, dry_run=False, workers=8, newest=None):
    held, why = held_labels(root)
    live = live_reasons(root)
    if live:
        raise SystemExit(f"{root}: E1 live, not packing:\n  " + "\n  ".join(live))
    todo, skipped = [], 0
    for lab, cond, step, d, _z in cells(root, newest):
        if d is None:
            continue
        if lab in held and not into:
            skipped += 1
            continue
        todo.append((str(d), str(_target(root, into, lab, cond, step))))
    print(f"{root}: {len(todo)} legacy cell(s) to pack" + (f" into {into}" if into else "")
          + (f"; {skipped} held cell(s) skipped ({why})" if skipped else ""))
    if dry_run or not todo:
        return []
    t = time.time()
    lock_root = Path(into) if into else Path(root)
    (lock_root / "_scratch").mkdir(parents=True, exist_ok=True)
    with Lock(lock_root):
        res = _pool_map(_pack_one, todo, workers)
    bad = [r for r in res if r[1] not in ("packed", "exists-ok")]
    print(f"  packed {sum(r[1] == 'packed' for r in res)}, already ok {sum(r[1] == 'exists-ok' for r in res)}, "
          f"problems {len(bad)} in {time.time() - t:.0f}s")
    _report(lock_root, "pack", res, ["cell", "result", "detail"], not bad, {"root": str(root)})
    return res


def cmd_verify(root, into=None, workers=8, newest=None):
    pairs = []
    for lab, cond, step, d, z in cells(root, newest):
        zp = _target(root, into, lab, cond, step) if into else z
        if d is not None and zp is not None and Path(zp).is_file():
            pairs.append((str(d), str(zp)))
    t = time.time()
    res = _pool_map(_verify_one, pairs, workers)
    bad = [r for r in res if r[2] != "ok"]
    print(f"{root}: verified {len(res)} pair(s), {len(bad)} mismatch(es) in {time.time() - t:.0f}s")
    rep_root = Path(into) if into else Path(root)
    _report(rep_root, "verify", res, ["folder", "archive", "result", "detail"], res and not bad,
            {"root": str(root)})
    return res


def cmd_gate(root, into=None, episodes=30, workers=8, newest=None):
    """Gate G1 (plan, review M2), zero tolerance: score every ARCHIVE into an empty table (no CSV
    seeding), every archive must hold exactly `episodes` recordings, the computed (run, scene, step)
    keys must equal the CSV rows' keys, every row's 13 strings identical, every CSV byte-identical.
    With `newest` N (a subset gate): only the newest N archives per (run, scene), compared with the
    newest N rows of each CSV; "byte-identical" then means header + those N lines."""
    import run_sweep as RS
    arch = Path(into) if into else Path(root)
    groups = sorted({(lab, cond) for lab, cond, *_ in cells(arch)})
    t = time.time()
    # archives only: a gate must never read the legacy folders it is meant to replace
    cell_list = []
    for gi, (lab, cond) in enumerate(groups):
        cd = arch / "_scratch" / lab / cond
        steps = sorted(EB.step_names(cd), key=int)
        for s in (steps[-newest:] if newest else steps):
            z = cd / f"{s}{EB.BUNDLE_SUFFIX}"
            cell_list.append((gi, str(z) if z.is_file() else None, int(s)))
    res = _pool_map(RS._measure_cell_n, [c for _, c, _ in cell_list if c], workers)
    it = iter(res)
    measured = [dict() for _ in groups]
    rows_out, ok = [], True
    for gi, z, s in cell_list:
        lab, cond = groups[gi]
        if z is None:
            rows_out.append([lab, cond, s, "", "NO_ARCHIVE"])
            ok = False
            continue
        r = next(it)
        if r is None or r[2] != episodes:
            rows_out.append([lab, cond, s, "" if r is None else r[2], "WRONG_EPISODE_COUNT"])
            ok = False
            continue
        measured[gi][r[0]] = r[1]
    tmpd = Path(tempfile.mkdtemp(prefix="g1_", dir=_log_dir(arch)))
    n_csv_equal = n_csv = n_rows_equal = n_rows = 0
    for (lab, cond), m in zip(groups, measured):
        ref = Path(root) / lab / f"{cond}.csv"
        out = tmpd / lab / f"{cond}.csv"
        if m:
            RS._write_csv(out, m)
        if not ref.exists():
            rows_out.append([lab, cond, "", "", "NO_REFERENCE_CSV"])
            ok = False
            continue
        n_csv += 1
        ref_rows = {int(r["step"]): [r.get(h, "") for h in RS.HEAD] for r in csv.DictReader(open(ref))}
        ref_bytes = ref.read_bytes()
        if newest:
            keep = set(sorted(ref_rows)[-newest:])
            ref_rows = {k: v for k, v in ref_rows.items() if k in keep}
            lines = ref_bytes.decode().splitlines(keepends=True)
            ref_bytes = "".join([lines[0]] + [ln for ln in lines[1:] if int(ln.split(",", 1)[0]) in keep]).encode()
        if set(ref_rows) != set(m):
            rows_out.append([lab, cond, "", "", f"KEYS_DIFFER only_csv={sorted(set(ref_rows) - set(m))[:5]} "
                                                f"only_archives={sorted(set(m) - set(ref_rows))[:5]}"])
            ok = False
        for s in sorted(set(ref_rows) & set(m)):
            n_rows += 1
            got = [str(x) for x in m[s]]
            if got == ref_rows[s]:
                n_rows_equal += 1
            else:
                rows_out.append([lab, cond, s, "", f"ROW_DIFFERS csv={ref_rows[s]} archive={got}"])
                ok = False
        if out.exists() and out.read_bytes() == ref_bytes:
            n_csv_equal += 1
        else:
            rows_out.append([lab, cond, "", "", "CSV_BYTES_DIFFER"])
            ok = False
    ref_groups = {(p.parent.name, p.stem) for p in Path(root).glob("*/*.csv") if not p.parent.name.startswith("_")}
    for lab, cond in sorted(ref_groups - set(groups)):
        rows_out.append([lab, cond, "", "", "CSV_WITHOUT_ARCHIVES"])
        ok = False
    n_cells = len(cell_list)
    ok = ok and n_cells > 0 and n_csv == len(groups)
    summ = _report(arch, "gate", rows_out, ["run_label", "cond", "step", "n", "problem"], ok,
                   {"root": str(root), "cells": n_cells, "groups": len(groups), "reference_csvs": len(ref_groups),
                    "csv_compared": n_csv,
                    "csv_byte_identical": n_csv_equal, "rows_compared": n_rows, "rows_identical": n_rows_equal,
                    "episodes_required": episodes, "newest_per_group": newest,
                    "seconds": round(time.time() - t, 1),
                    "computed_csv_dir": str(tmpd)})
    print(json.dumps(summ, indent=1))
    return summ


def cmd_independent_check(root, sample=None):
    here = socket.gethostname()
    pairs = [(d, z) for _l, _c, _s, d, z in cells(root) if d is not None and z is not None]
    if sample:
        pairs = random.Random(0).sample(pairs, min(sample, len(pairs)))
    rows, ok = [], True
    for d, z in pairs:
        if EB.read_comment(z)["pack_host"] == here:
            raise SystemExit(f"{z} was packed on this host ({here}); run independent-check elsewhere")
        with tempfile.TemporaryDirectory(prefix="indep_", dir="/tmp") as td:
            r1 = subprocess.run(["unzip", "-q", str(z), "-d", td], capture_output=True, text=True)
            r2 = subprocess.run(["diff", "-r", td, str(d)], capture_output=True, text=True)
        good = r1.returncode == 0 and r2.returncode == 0
        ok &= good
        rows.append([str(d), str(z), "identical" if good else "DIFFERENT", (r1.stderr + r2.stdout)[:300]])
    print(f"{root}: independent check of {len(rows)} cell(s) on {here}: {'all identical' if ok else 'DIFFERENCES'}")
    return _report(root, "indep", rows, ["folder", "archive", "result", "detail"], ok and rows)


def backup_marker_exists():
    return any(BACKUP_ROOT.glob("eval_tables_*/BACKUP_OK"))


def cmd_backup_tables():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_ROOT / f"eval_tables_{stamp}"
    files = []
    for root, dirs, fnames in os.walk(EVAL_ROOT):
        dirs[:] = [d for d in dirs if d != "_scratch"]
        rp = Path(root)
        in_prov = "_provenance" in rp.parts
        for f in fnames:
            if in_prov or f.endswith((".csv", ".html")) or (f.startswith("FIG_") and f.endswith(".png")):
                files.append(rp / f)
    lst = []
    for p in files:
        rel = p.relative_to(EVAL_ROOT)
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest / rel)
        a, b = EB._sha256_file(p), EB._sha256_file(dest / rel)
        if a != b:
            raise SystemExit(f"backup copy differs: {p}")
        lst.append(f"{a[1]}  {rel.as_posix()}")
    (dest / "SHA256SUMS").write_text("\n".join(lst) + "\n")
    (dest / "BACKUP_OK").write_text(f"{len(lst)} files {time.ctime()}\n")
    print(f"backed up {len(lst)} files to {dest}")
    return dest


def cmd_delete(root):
    root = Path(root)
    if not backup_marker_exists():
        raise SystemExit("no results/_backup/eval_tables_*/BACKUP_OK: run backup-tables first")
    blockers = unswitched_readers()
    if blockers:
        raise SystemExit("E2: unswitched readers block deletion:\n  " + "\n  ".join(blockers))
    live = live_reasons(root)
    if live:
        raise SystemExit(f"{root}: E1 live:\n  " + "\n  ".join(live))
    held, _ = held_labels(root)
    v = _latest(root, "verify", socket.gethostname())
    if not v or not v["all_ok"]:
        raise SystemExit(f"{root}: no all-OK verify report written on this host; run verify here first")
    g = _latest(root, "gate")
    if not g or not g["all_ok"]:
        raise SystemExit(f"{root}: no all-OK gate report; run gate first")
    wal = _log_dir(root) / "delete_wal.jsonl"
    n_files = n_cells = skipped = 0
    with Lock(root):
        for lab, cond, _step, d, z in cells(root):
            if d is None or z is None:
                continue
            if lab in held:
                skipped += 1
                continue
            n_files += EB.delete_verified(d, z, wal, repo_root=REPO_ROOT)
            n_cells += 1
    print(f"{root}: deleted {n_files} file(s) in {n_cells} cell(s); {skipped} held cell(s) kept")
    return n_cells


def cmd_inventory(roots, deep=False):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = REPO_ROOT / "tmp" / f"{stamp}_bundle_inventory.csv"
    out.parent.mkdir(exist_ok=True)
    rows = []
    for r in roots:
        cs = cells(r)
        held, _ = held_labels(r)
        runs = label_runs(r)
        missing = sorted({lab for lab in runs if not any(
            (REPO_ROOT / "results" / algo / runs[lab]).is_dir() for algo in ("JAX_RecurrentPPO", "JAX_DreamerSRL"))})
        files = nbytes = ""
        if deep:
            files = nbytes = 0
            for *_x, d, _z in cs:
                if d is not None:
                    for dp, _dn, fn in os.walk(d):
                        files += len(fn)
                        nbytes += sum(os.stat(Path(dp) / f).st_size for f in fn)
        live = live_reasons(r)
        rows.append([_rel(r), sum(c[3] is not None for c in cs), sum(c[4] is not None for c in cs), files, nbytes,
                     len({c[0] for c in cs} & held), "; ".join(live)[:200], ";".join(missing)])
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["root", "legacy_cells", "archived_cells", "files", "bytes", "held_labels", "live", "ckpt_missing"])
        w.writerows(rows)
    for row in rows:
        print(" | ".join(str(x) for x in row))
    print(f"inventory: {out}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory"); p.add_argument("roots", nargs="*"); p.add_argument("--all", action="store_true")
    p.add_argument("--deep", action="store_true")
    sub.add_parser("backup-tables")
    for name in ("pack", "verify", "gate"):
        p = sub.add_parser(name)
        p.add_argument("root")
        p.add_argument("--into", default=None)
        p.add_argument("--workers", type=int, default=8)
        p.add_argument("--newest", type=int, default=None,
                       help="only the newest N steps of each (run, scene) -- a subset gate")
        if name == "pack":
            p.add_argument("--dry-run", action="store_true")
        if name == "gate":
            p.add_argument("--episodes", type=int, default=30)
    p = sub.add_parser("independent-check"); p.add_argument("root"); p.add_argument("--sample", type=int, default=None)
    p = sub.add_parser("delete"); p.add_argument("root")
    p = sub.add_parser("extract"); p.add_argument("zip"); p.add_argument("dest")
    p = sub.add_parser("unlock"); p.add_argument("root")
    a = ap.parse_args(argv)

    def R(x):
        return Path(x) if Path(x).is_absolute() else REPO_ROOT / x

    if a.cmd == "inventory":
        cmd_inventory(all_roots() if a.all else [R(x) for x in a.roots], a.deep)
    elif a.cmd == "backup-tables":
        cmd_backup_tables()
    elif a.cmd == "pack":
        res = cmd_pack(R(a.root), a.into and R(a.into), a.dry_run, a.workers, a.newest)
        if any(r[1] not in ("packed", "exists-ok") for r in res):
            raise SystemExit(1)
    elif a.cmd == "verify":
        if any(r[2] != "ok" for r in cmd_verify(R(a.root), a.into and R(a.into), a.workers, a.newest)):
            raise SystemExit(1)
    elif a.cmd == "gate":
        if not cmd_gate(R(a.root), a.into and R(a.into), a.episodes, a.workers, a.newest)["all_ok"]:
            raise SystemExit(1)
    elif a.cmd == "independent-check":
        if not cmd_independent_check(R(a.root), a.sample)["all_ok"]:
            raise SystemExit(1)
    elif a.cmd == "delete":
        cmd_delete(R(a.root))
    elif a.cmd == "extract":
        print(EB.extract(a.zip, a.dest))
    elif a.cmd == "unlock":
        lock = R(a.root) / "_scratch" / "_bundle.lock"
        print(f"{lock}: {lock.read_text() if lock.exists() else '(no lock)'}")
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
