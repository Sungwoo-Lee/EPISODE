#!/usr/bin/env python3
"""make_population.py - write the population manifest that readings.py reads.

Plan: docs/develop/active/behavior/HYPERVIGILANCE_ANALYSIS_TOOLING.md (Revision 2, R3 / N1 / N3 / N4).

One JSON per population, one entry per cell:
    {label, run, stores, store_root, checkpoint, world, agent, seed, level, wave, status, tag}
`status` is one of completed / running / failed / planned; readings.py reads `completed` only.
This script NEVER decides between two candidates for one seed and never promotes a status: it
writes what the source says and readings.py refuses ambiguity.

Three sources, one flag each:
  --from-study-doc <md>       the study's Launch Manifest table (the ground truth for status).
                              Its Status column is kept true by the session that runs training and
                              collection (plan Revision 2, N1); a `running` row whose run already has
                              a final checkpoint AND a store is refused as a stale status.
  --from-ladder-manifest <j>  an existing {label: {run, stores}} file (all completed), optionally
                              plus `--add-level L --wave-root wN=<root>` cells found on disk
  --runs <dir> ...            an explicit list (all completed)

--checkpoint-nearest N picks, per run, the store checkpoint closest to N (ties refused) and records
the actual number (plan Revision 2, N3); without it a run with several store checkpoints is refused.

Output: results/analysis/hypervigilance/<population>/population.json (source + its sha256 recorded).
"""
from __future__ import annotations
import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis"))
from hiding_drivers import find_stores      # noqa: E402

HV_ROOT = os.path.join(ROOT, "results", "analysis", "hypervigilance")
STATUSES = ("completed", "running", "failed", "planned")
CELL_WORLD = {"1ch": "hv1ch", "1chm": "hv1chm", "2ch": "hv2ch"}
CELL_AGENT = {"ordinary": "t1none", "modulated": "t16quad"}
AGENT_RE = re.compile(r"_(?P<agent>t1none|t16quad)(_ALL)?_s(?P<seed>\d+)(_r\d+)?$")
SEED_RE = re.compile(r"_s(?P<seed>\d+)(_r\d+)?$")


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- markdown table (N4) ----
def split_row(line: str) -> list[str]:
    """Split one markdown table row on `|`, ignoring any `|` inside a backtick span."""
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        raise SystemExit(f"not a table row: {line!r}")
    cells, cur, tick = [], [], False
    for ch in s[1:-1]:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if tick:
        raise SystemExit(f"unbalanced backtick in table row: {line!r}")
    cells.append("".join(cur).strip())
    return cells


def parse_launch_manifest(md: str) -> list[dict]:
    """Rows of the '## 3. Launch Manifest' table as dicts keyed by the header."""
    lines = open(md).read().splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## ") and "Launch Manifest" in l)
    except StopIteration:
        raise SystemExit(f"{md}: no '## ... Launch Manifest' section")
    hdr_i = next(i for i in range(start, len(lines)) if lines[i].startswith("| Run | Status |"))
    header = split_row(lines[hdr_i])
    rows = []
    for i in range(hdr_i + 2, len(lines)):
        if not lines[i].startswith("|"):
            break
        cells = split_row(lines[i])
        if len(cells) != len(header):
            raise SystemExit(f"{md}:{i + 1}: row has {len(cells)} cells, the header has "
                             f"{len(header)} -- refusing rather than mis-aligning columns")
        rows.append(dict(zip(header, cells)))
    return rows


def parse_status(cell: str) -> str:
    m = re.match(r"\s*([A-Za-z]+)", cell)
    st = m.group(1).lower() if m else ""
    if st not in STATUSES:
        raise SystemExit(f"unknown status {cell!r}; expected one of {STATUSES}")
    return st


def run_dir_of(log_cell: str):
    m = re.search(r"run dir `([^`]+)`", log_cell)
    return m.group(1).rstrip("/") if m else None


# ------------------------------------------------------------------------- stores (N3) ----
def store_checkpoints(run: str, roots) -> list[str]:
    tag = os.path.basename(run.rstrip("/"))
    out = set()
    for r in roots:
        for d in glob.glob(os.path.join(ROOT, r, tag, "*", "*", "")):
            out.add(os.path.basename(os.path.dirname(os.path.dirname(d))))
    return sorted(out)


def resolve_stores(run: str, roots, nearest=None):
    """(checkpoint, stores) for one run, or (None, []) when nothing is collected yet."""
    cks = store_checkpoints(run, roots)
    if not cks:
        return None, []
    if nearest is None:
        if len(cks) > 1:
            raise SystemExit(f"{run}: several store checkpoints {cks}; pass --checkpoint-nearest")
        ck = cks[0]
    else:
        dist = sorted((abs(int(c) - nearest), c) for c in cks if c.isdigit())
        if len(dist) > 1 and dist[0][0] == dist[1][0]:
            raise SystemExit(f"{run}: checkpoints {dist[0][1]} and {dist[1][1]} are equally near "
                             f"{nearest}; refusing to choose")
        ck = dist[0][1]
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        stores = find_stores(run, ck, roots)
    finally:
        os.chdir(cwd)
    return ck, [s if s.endswith("/") else s + "/" for s in stores]


def final_checkpoint(run: str):
    """The run's largest saved checkpoint if it has reached the configured episode budget."""
    import yaml
    cfgp = os.path.join(ROOT, run, "models", "config.yaml")
    if not os.path.exists(cfgp):
        return None
    budget = int(yaml.safe_load(open(cfgp))["episodes"])
    steps = [int(d) for d in os.listdir(os.path.join(ROOT, run, "models")) if d.isdigit()]
    return max(steps) if steps and max(steps) >= budget else None


def cell(label, run, roots, world, agent, seed, status, nearest=None, level=None, wave=None, tag=None):
    ck, stores = resolve_stores(run, roots, nearest) if run else (None, [])
    return {"label": label, "run": run, "stores": stores, "store_root": list(roots),
            "checkpoint": ck, "world": world, "agent": agent, "seed": int(seed), "level": level,
            "wave": wave, "status": status, "tag": tag}


# --------------------------------------------------------------------------------- sources ----
def from_study_doc(md, roots, nearest=None) -> list[dict]:
    out = []
    for r in parse_launch_manifest(md):
        st = parse_status(r["Status"])
        run = run_dir_of(r["Log path"])
        wpart, apart = [x.strip() for x in r["Cell"].split("·")]
        world, agent = CELL_WORLD[wpart], CELL_AGENT[apart]
        tag = r["Tag (= wandb-name)"].strip("`")
        relaunch = re.search(r"(_r\d+)$", run) if run else None
        label = f"{world}_{agent}_s{int(r['Seed'])}" + (relaunch.group(1) if relaunch else "")
        if run is None:
            label += f"_{r['Run']}"
        if run is None:
            if st != "planned":
                raise SystemExit(f"row {r['Run']}: status {st} but no run dir in the Log path cell")
            out.append(cell(label, None, roots, world, agent, r["Seed"], st, tag=tag))
            continue
        c = cell(label, run, roots, world, agent, r["Seed"], st, nearest, tag=tag)
        if st == "running" and c["stores"] and final_checkpoint(run) is not None:
            raise SystemExit(f"stale status: {run} is marked running but has a final checkpoint "
                             f"({final_checkpoint(run)}) and a store ({c['stores']}) -- update the "
                             f"study's Launch Manifest (plan Revision 2, N1); never auto-promoted")
        if st == "completed" and not c["stores"]:
            raise SystemExit(f"{run} is marked completed but has no store under {roots}")
        out.append(c)
    return out


def from_ladder_manifest(path, world, add_levels, wave_roots, nearest=None) -> list[dict]:
    man = json.load(open(path))
    out = []
    for label, e in man.items():
        m = re.match(r"^(?P<wave>w\d+)_lvl(?P<lvl>\d+)_", label)
        am = AGENT_RE.search(os.path.basename(e["run"].rstrip("/")))
        c = cell(label, e["run"].rstrip("/"), roots_of(e["stores"]), world, am["agent"], am["seed"],
                 "completed", nearest, level=int(m["lvl"]) if m else None,
                 wave=m["wave"] if m else None)
        if sorted(c["stores"]) != sorted(s if s.endswith("/") else s + "/" for s in e["stores"]):
            raise SystemExit(f"{label}: stores on disk {c['stores']} differ from {path}'s {e['stores']}")
        out.append(c)
    for lvl in add_levels:
        for wave, root in wave_roots:
            for d in sorted(glob.glob(os.path.join(ROOT, root, f"*_lvl{lvl:02d}_*"))):
                base = os.path.basename(d)
                am = AGENT_RE.search(base)
                if not am:
                    continue
                arm = "control" if am["agent"] == "t1none" else "modulated"
                run = f"results/JAX_RecurrentPPO/{base}"
                out.append(cell(f"{wave}_lvl{lvl:02d}_{arm}", run, [root], world, am["agent"],
                                am["seed"], "completed", nearest, level=lvl, wave=wave))
    return out


def roots_of(stores) -> list[str]:
    """store dir <root>/<tag>/<ckpt>/<hash>/ -> <root>"""
    return sorted({os.path.normpath(s).rsplit(os.sep, 3)[0] for s in stores})


def from_runs(runs, world, roots, nearest=None, agent_flag=None) -> list[dict]:
    out = []
    for run in runs:
        run = run.rstrip("/")
        base = os.path.basename(run)
        am = AGENT_RE.search(base)
        sm = SEED_RE.search(base)
        if am and agent_flag and am["agent"] != agent_flag:
            raise SystemExit(f"{base}: tag says agent {am['agent']}, --agent says {agent_flag}")
        agent = am["agent"] if am else agent_flag
        if agent is None:
            raise SystemExit(f"{base}: the tag carries no agent; pass --agent")
        if not sm:
            import yaml
            seed = int(yaml.safe_load(open(os.path.join(ROOT, run, "models", "config.yaml")))["seed"])
        else:
            seed = int(sm["seed"])
        out.append(cell(base.split("_", 1)[1], run, roots, world, agent, seed, "completed", nearest))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True, help="output folder name, e.g. hvsmell, basicq2")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-study-doc")
    src.add_argument("--from-ladder-manifest")
    src.add_argument("--runs", nargs="+")
    ap.add_argument("--world", default=None, help="world name for --from-ladder-manifest / --runs")
    ap.add_argument("--store-root", nargs="+", default=None)
    ap.add_argument("--agent", default=None, help="agent name for --runs when the tag carries none")
    ap.add_argument("--add-level", type=int, nargs="*", default=[])
    ap.add_argument("--wave-root", nargs="*", default=[], help="wN=<store root>")
    ap.add_argument("--checkpoint-nearest", type=int, default=None)
    ap.add_argument("--out", default=None, help="default results/analysis/hypervigilance/<population>/"
                                                 "population.json")
    a = ap.parse_args()
    if a.from_study_doc:
        if not a.store_root:
            raise SystemExit("--from-study-doc needs --store-root")
        cells = from_study_doc(a.from_study_doc, a.store_root, a.checkpoint_nearest)
        source = a.from_study_doc
    elif a.from_ladder_manifest:
        if not a.world:
            raise SystemExit("--from-ladder-manifest needs --world")
        wr = [tuple(x.split("=", 1)) for x in a.wave_root]
        cells = from_ladder_manifest(a.from_ladder_manifest, a.world, a.add_level, wr,
                                     a.checkpoint_nearest)
        source = a.from_ladder_manifest
    else:
        if not (a.world and a.store_root):
            raise SystemExit("--runs needs --world and --store-root")
        cells = from_runs(a.runs, a.world, a.store_root, a.checkpoint_nearest, a.agent)
        source = None
    out = a.out or os.path.join(HV_ROOT, a.population, "population.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    doc = {"population": a.population, "written": _dt.datetime.now().isoformat(timespec="seconds"),
           "source": os.path.relpath(source, ROOT) if source else {"runs": a.runs},
           "source_sha256": sha256(source) if source else None,
           "checkpoint_nearest": a.checkpoint_nearest, "cells": cells}
    json.dump(doc, open(out, "w"), indent=1)
    by = {}
    for c in cells:
        by[c["status"]] = by.get(c["status"], 0) + 1
    print(f"{out}: {len(cells)} cells {by}")


if __name__ == "__main__":
    main()
