#!/usr/bin/env python
"""Delete the episode archives of ONE Figure 5 re-collection scene set, only after every cell is
proven complete and extracted (plan-review findings C2 and M3 in
docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md, "Figure 5 re-collection").

    prune_archives.py <sweep spec .yaml>            # dry run (default): check + list, delete nothing
    prune_archives.py <sweep spec .yaml> --delete   # check, then delete the listed archives

1. Expected cells, built WITHOUT the sweep's worklists or rows tables: every spec label x every
   scene of the spec's probe folder x that label's newest ``max_checkpoints`` steps, listed from
   the run folder's own ``models/`` (the rule the sweep applies to a fresh output folder).
2. Per run (labels sharing a name without ``_resumed<k>``), the run's checkpoints are merged across
   ALL its session folders (folders under the same parent whose name after the
   ``YYYYMMDD-HHMMSS_`` prefix is the same, found on disk, not from the spec). Steps closer than
   half the checkpoint interval (e.g. 8200036 and 8200088 of a resumed run) are one slot. The
   newest ``max_checkpoints`` slots must each hold at least one expected cell; the window and the
   number of two-step slots are printed (M3).
3. Per expected cell, all of: the per-scene CSV row; a rows-table row (any launch under
   ``_scratch/_rows/``) with ``n_episodes`` = the spec's ``episodes``, ``bundle`` =
   ``<label>/<scene>/<step>.zip`` and the same 13 values as the CSV row; the archive on disk
   (or, if a previous ``--delete`` logged it, its logged sha256); the per-episode table
   (extract_episodes.py) holding exactly ``episodes`` rows for the cell, episode i with the scene's
   ``eval_seeds[i]``, and the archive's sha256; the scene file in some ``_provenance/*/scenes/``.
4. ANY failure aborts the whole batch: nothing is deleted.
5. Deletion is limited to the listed ``*.zip`` files, each asserted to be
   ``<repo>/results/eval/avoidance/metrics_history_rppo_lookalike_hf_random_layout/<set>/_scratch/
   <label>/<scene>/<digits>.zip`` with ``<set>`` = ``heal{on,off}_{food,nofood}_{sampled,greedy}``.
   Nothing else is touched: not ``_rows``, ``_logs``, ``_run_markers``, ``_worklists``,
   ``_provenance``, the CSVs, the per-episode table, or any other results folder. Each file's
   path, size and sha256 is appended (and fsynced) to ``<output_dir>/_prune/<time>_deleted.tsv``
   BEFORE it is removed. The dry run writes its list to ``<output_dir>/_prune/<time>_dryrun.tsv``.

Archives on disk that are not expected cells are listed and kept. Exit status: 0 ok, 1 aborted.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_episodes as XE  # noqa: E402

XE._setup_path()

ALLOWED_PARENT_REL = Path("results/eval/avoidance/metrics_history_rppo_lookalike_hf_random_layout")
SET_RE = re.compile(r"heal(on|off)_(food|nofood)_(sampled|greedy)")
STEP_ZIP_RE = re.compile(r"\d+\.zip")
SESSION_RE = re.compile(r"^\d{8}-\d{6}_(.+)$")
PROTECTED = {"_rows", "_logs", "_run_markers", "_worklists", "_provenance", "_episodes", "_prune", "_format"}


class Abort(Exception):
    pass


# ------------------------------------------------------------------------------- path guard ----
def check_output_dir(repo, out):
    parent = (repo / ALLOWED_PARENT_REL).resolve()
    out = out.resolve()
    if out.parent != parent or not SET_RE.fullmatch(out.name):
        raise Abort(f"output_dir {out} is not {parent}/heal{{on,off}}_{{food,nofood}}_{{sampled,greedy}}")
    return out


def assert_deletable(path, scratch, labels, conds):
    """Raise Abort unless `path` is exactly <scratch>/<label>/<cond>/<digits>.zip, a regular file."""
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise Abort(f"refusing {p}: not a regular file")
    rp = p.resolve()
    sc = scratch.resolve()
    if not str(rp).startswith(str(sc) + os.sep):
        raise Abort(f"refusing {rp}: outside {sc}")
    parts = rp.relative_to(sc).parts
    if len(parts) != 3 or not STEP_ZIP_RE.fullmatch(parts[2]) or not rp.name.endswith(".zip"):
        raise Abort(f"refusing {rp}: not <label>/<scene>/<step>.zip under {sc}")
    if parts[0] in PROTECTED or parts[0].startswith("_") or parts[0] not in labels or parts[1] not in conds:
        raise Abort(f"refusing {rp}: label/scene not in the spec")
    return rp


# ----------------------------------------------------------------------------- expectations ----
def list_steps(run_dir):
    d = Path(run_dir) / "models"
    if not d.is_dir():
        return []
    return sorted(int(p.name) for p in d.iterdir() if p.name.isdigit())


def session_folders(run_dir):
    """All session folders of the run `run_dir` belongs to (same name after the time prefix)."""
    run_dir = Path(run_dir)
    m = SESSION_RE.match(run_dir.name)
    if not m:
        return [run_dir]
    return sorted(p for p in run_dir.parent.iterdir()
                  if p.is_dir() and (SESSION_RE.match(p.name) or [None, None])[1] == m.group(1))


def slots(steps):
    """Group sorted steps into checkpoint slots: steps closer than half the median interval are
    one slot. Returns a list of lists, oldest first."""
    steps = sorted(set(steps))
    if len(steps) < 2:
        return [[s] for s in steps]
    diffs = sorted(b - a for a, b in zip(steps, steps[1:]))
    tol = diffs[len(diffs) // 2] / 2
    out = [[steps[0]]]
    for s in steps[1:]:
        if s - out[-1][-1] < tol:
            out[-1].append(s)
        else:
            out.append([s])
    return out


def expected_cells(spec, repo, conds, max_ck):
    """({(label, cond, step)}, run report lines, problems)."""
    cells, report, problems = set(), [], []
    by_run = defaultdict(list)
    for r in spec["runs"]:
        run_dir = repo / r["path"]
        steps = list_steps(run_dir)
        if not steps:
            problems.append(f"{r['label']}: no checkpoints in {run_dir}/models")
            continue
        for s in steps[-max_ck:]:
            for c in conds:
                cells.add((r["label"], c, s))
        by_run[XE.run_of(r["label"])].append((r["label"], run_dir, set(steps[-max_ck:])))
    for run, members in sorted(by_run.items()):
        covered = set().union(*(m[2] for m in members))
        folders = set()
        for _, d, _ in members:
            folders.update(session_folders(d))
        merged = sorted({s for f in folders for s in list_steps(f)})
        sl = slots(merged)
        if len(sl) < max_ck:
            problems.append(f"{run}: only {len(sl)} checkpoint slots across {len(folders)} session folder(s)")
            continue
        window = sl[-max_ck:]
        miss = [w for w in window if not covered.intersection(w)]
        if miss:
            problems.append(f"{run}: newest-{max_ck} slot(s) {miss[:3]} not tested by any spec label "
                            f"({[m[0] for m in members]})")
        dup = [w for w in window if len(w) > 1]
        report.append(f"{run}: window {window[0][0] / 1e6:.2f}-{window[-1][-1] / 1e6:.2f} M, "
                      f"{len(window)} slots, {len(dup)} two-step slot(s){' ' + str(dup) if dup else ''}, "
                      f"labels {[m[0] for m in members]}")
    return cells, report, problems


# ---------------------------------------------------------------------------------- evidence ----
def read_rows_tables(scratch):
    """{(label, cond, step): [row dicts]} over every launch's rows tables (node pieces if a node's
    concatenated table is missing)."""
    out = defaultdict(list)
    base = scratch / "_rows"
    if not base.is_dir():
        return out
    for launch in sorted(p for p in base.iterdir() if p.is_dir()):
        files = sorted(launch.glob("rows_*.csv"))
        have = {f.stem[len("rows_"):] for f in files}
        for nd in sorted(p for p in launch.iterdir() if p.is_dir() and p.name not in have):
            files.extend(sorted(nd.glob("*.csv")))
        for f in files:
            with open(f, newline="") as fh:
                for r in csv.DictReader(fh):
                    out[(r["run_label"], r["cond"], int(r["step"]))].append(r)
    return out


def read_prune_logs(out):
    """{repo-relative path: sha256} of archives a previous --delete removed."""
    done = {}
    for f in sorted((out / "_prune").glob("*_deleted.tsv")):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                done[r["path"]] = r["sha256"]
    return done


def table_index(table_path):
    """{(label, cond, step): (seeds in episode order, set of sha256, n rows)} from the table."""
    t = XE.load_table(table_path)
    if t is None:
        return {}
    d = t.select(["run_label", "cond", "step", "episode_index", "seed", "archive_sha256"]).to_pydict()
    acc = defaultdict(list)
    for lab, c, s, i, sd, sh in zip(d["run_label"], d["cond"], d["step"], d["episode_index"],
                                    d["seed"], d["archive_sha256"]):
        acc[(lab, c, int(s))].append((int(i), int(sd), sh))
    return {k: (tuple(sd for _, sd, _ in sorted(v)), {sh for _, _, sh in v}, len(v),
                [i for i, _, _ in sorted(v)]) for k, v in acc.items()}


def check(spec_path, repo, workers):
    spec, out, probe, conds, episodes = XE.load_spec(spec_path, repo)
    out = check_output_dir(repo, out)
    max_ck = int(XE.mandatory(spec, "max_checkpoints"))
    scratch = out / "_scratch"
    labels = {r["label"] for r in spec["runs"]}
    seeds = XE.expected_seeds(probe, conds, episodes)
    cells, report, problems = expected_cells(spec, repo, conds, max_ck)
    rows = read_rows_tables(scratch)
    pruned = read_prune_logs(out)
    tab = table_index(out / XE.TABLE_REL)
    prov = {p.stem for p in out.glob("_provenance/*/scenes/*.yaml") if not p.name.endswith(".resolved.yaml")}
    for c in conds:
        if c not in prov:
            problems.append(f"scene {c}: no _provenance/*/scenes/{c}.yaml")
    csv_cache = {}
    to_hash, listed, n_pruned = [], [], 0
    for (label, cond, step) in sorted(cells):
        tag = f"{label}/{cond}/{step}"
        if (label, cond) not in csv_cache:
            csv_cache[(label, cond)] = XE.read_csv_rows(out / label / f"{cond}.csv")
        crow = csv_cache[(label, cond)].get(step)
        if crow is None:
            problems.append(f"{tag}: no CSV row"); continue
        bundle = f"{label}/{cond}/{step}.zip"
        good = [r for r in rows.get((label, cond, step), [])
                if str(r.get("n_episodes")) == str(episodes) and r.get("bundle") == bundle
                and XE.rows_equal([r.get(h, "") for h in _head()], crow)]
        if not good:
            problems.append(f"{tag}: no rows-table row with n_episodes={episodes}, bundle={bundle} "
                            f"and the CSV row's values ({len(rows.get((label, cond, step), []))} row(s) seen)"); continue
        ti = tab.get((label, cond, step))
        if ti is None:
            problems.append(f"{tag}: not in the per-episode table"); continue
        tseeds, tsha, tn, tidx = ti
        if tn != episodes or tidx != list(range(episodes)) or tseeds != seeds[cond] or len(tsha) != 1:
            problems.append(f"{tag}: per-episode table has {tn} rows / wrong episode indices / "
                            f"seeds differ from the scene's eval_seeds / {len(tsha)} archive sha256s"); continue
        z = scratch / bundle
        rel = z.relative_to(repo).as_posix()
        if not z.exists():
            if rel in pruned and pruned[rel] in tsha:
                n_pruned += 1
                continue  # deleted by an earlier --delete, logged with the extracted sha
            problems.append(f"{tag}: archive {rel} missing and not in any _prune log"); continue
        to_hash.append((label, cond, step, z, next(iter(tsha))))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        hashed = list(ex.map(lambda j: XE.sha256_file(j[3]), to_hash))
    for (label, cond, step, z, want), (nb, sha) in zip(to_hash, hashed):
        if sha != want:
            problems.append(f"{label}/{cond}/{step}: archive sha256 {sha[:12]} != extracted {want[:12]}")
            continue
        st = z.stat()
        listed.append((assert_deletable(z, scratch, labels, conds), nb, sha, st.st_mtime_ns))
    # archives on disk that are not expected cells: kept, listed
    expected_paths = {(scratch / f"{l}/{c}/{s}.zip").resolve() for (l, c, s) in cells}
    extras = sorted(p for p in scratch.glob("*/*/*.zip")
                    if not p.parts[-3].startswith("_") and p.resolve() not in expected_paths)
    return dict(out=out, scratch=scratch, labels=labels, conds=conds, cells=cells, report=report,
                problems=problems, listed=listed, extras=extras, n_pruned=n_pruned)


def _head():
    from cell_measures import HEAD
    return HEAD


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--delete", action="store_true", help="really delete (default is a dry run)")
    ap.add_argument("--workers", type=int, default=8, help="threads hashing archives")
    ap.add_argument("--data-root", default=str(XE.REPO_ROOT),
                    help="root the spec's paths and the allowed results folder are relative to "
                         "(default: this repository; tests point it at a synthetic copy)")
    a = ap.parse_args(argv)
    repo = Path(a.data_root).resolve()
    XE._setup_path()
    try:
        r = check(a.spec, repo, a.workers)
    except Abort as e:
        print(f"[prune] ABORT: {e}")
        return 1
    for line in r["report"]:
        print(f"  {line}")
    ts = time.strftime("%Y%m%d_%H%M%S")
    print(f"[prune] {r['out'].name}: {len(r['cells'])} expected cells; {len(r['listed'])} archives "
          f"verified, {r['n_pruned']} already pruned, {len(r['extras'])} unlisted archive(s) kept")
    for p in r["extras"][:20]:
        print(f"  KEPT (not an expected cell): {p}")
    if r["problems"]:
        print(f"[prune] ABORT: {len(r['problems'])} problem(s); nothing deleted. First 30:")
        for p in r["problems"][:30]:
            print(f"  {p}")
        return 1
    pdir = r["out"] / "_prune"
    pdir.mkdir(exist_ok=True)
    total = sum(nb for _, nb, _, _ in r["listed"])
    if not a.delete:
        f = pdir / f"{ts}_dryrun.tsv"
        with open(f, "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["path", "bytes", "sha256"])
            for p, nb, sha, _ in r["listed"]:
                w.writerow([p.relative_to(repo).as_posix(), nb, sha])
        print(f"[prune] DRY RUN: would delete {len(r['listed'])} archives, {total / 1e9:.2f} GB; list {f}")
        return 0
    f = pdir / f"{ts}_deleted.tsv"
    n = 0
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["path", "bytes", "sha256", "time"])
        fh.flush()
        for p, nb, sha, mt in r["listed"]:
            p = assert_deletable(p, r["scratch"], r["labels"], r["conds"])
            st = p.stat()
            if st.st_size != nb or st.st_mtime_ns != mt:
                print(f"[prune] STOP: {p} changed since it was checked; {n} deleted so far, log {f}")
                return 1
            w.writerow([p.relative_to(repo).as_posix(), nb, sha, time.strftime("%Y-%m-%d %H:%M:%S")])
            fh.flush()
            os.fsync(fh.fileno())
            p.unlink()
            n += 1
    print(f"[prune] deleted {n} archives, {total / 1e9:.2f} GB; log {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
