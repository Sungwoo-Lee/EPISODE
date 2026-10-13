#!/usr/bin/env python
"""Run registry: one CSV row per training session, built from WandB's local run records.

Every training launch (train.py, dreamer_srl) leaves ``wandb/run-<YYYYmmdd_HHMMSS>-<id>/`` with
the full launch command in ``files/wandb-metadata.json``. This script reads all of them, matches
each to its results folder, and writes ``docs/experiments/run_registry/runs.csv``. A run that was
stopped and resumed under the same WandB id has one row per session.

Usage (from the repo root, conda python):
    scripts/lab/run_registry.py build [--live]     # rebuild runs.csv (--live: ask nodes which runs are alive)
    scripts/lab/run_registry.py find <text>...     # rows whose name / tag / id / group contain all <text>
    scripts/lab/run_registry.py resume <name|id>   # flags to resume a run from its newest checkpoint

Column meanings and status rules: docs/experiments/run_registry/README.md
"""
import argparse
import csv
import glob
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "experiments", "run_registry", "runs.csv")
RUNNING_WINDOW_S = 30 * 60      # a session whose console log (files/output.log) changed this recently counts as running
MATCH_BEFORE_S = 15 * 60        # results folder is named up to this long BEFORE wandb.init (slow NAS mkdir) ...
MATCH_AFTER_S = 60              # ... and never more than this after it
WORKERS = 32                    # parallel NAS reads; the build is I/O-latency bound
FINISHED_FRACTION = 0.999       # last checkpoint >= this x target episodes counts as finished

COLUMNS = ["wandb_id", "run_name", "session", "status", "session_start", "node", "gpu",
           "first_ckpt", "last_ckpt", "n_ckpt", "target_episodes", "results_dir",
           "resumed_from_dir", "resumed_from_ckpt", "algorithm", "trainer", "tag", "wandb_group",
           "wandb_job_type", "wandb_project", "seed", "env_config", "agent_config", "git_commit",
           "wandb_dir"]


def arg_value(args, *names):
    for n in names:
        if n in args:
            i = args.index(n)
            if i + 1 < len(args):
                return args[i + 1]
    return ""


def parse_ts(s, fmt):
    try:
        return datetime.strptime(s, fmt)
    except ValueError:
        return None


def ckpt_numbers(results_dir):
    """Numeric checkpoint folder names (episodes) under models/ or checkpoints/."""
    nums = []
    for sub in ("models", "checkpoints"):
        p = os.path.join(results_dir, sub)
        if os.path.isdir(p):
            nums += [int(n) for n in os.listdir(p) if n.isdigit()]
    return sorted(nums)


def index_results():
    """{name_suffix: [(start_datetime, relpath)]} and a flat list, over every results folder."""
    by_suffix, flat = {}, []
    pats = ["results/JAX_*/*", "results/_aborted/*", "results/_superseded/*"]
    for pat in pats:
        for p in glob.glob(os.path.join(REPO, pat)):
            name = os.path.basename(p)
            m = re.match(r"^(\d{8}-\d{6})_(.+)$", name)
            if not m or not os.path.isdir(p):
                continue
            ts = parse_ts(m.group(1), "%Y%m%d-%H%M%S")
            rel = os.path.relpath(p, REPO)
            by_suffix.setdefault(m.group(2), []).append((ts, rel))
            flat.append((ts, rel))
    return by_suffix, flat


def match_results(rows, by_suffix, flat):
    """Give each session the results folder named closest before its WandB start; one folder per session.

    The trainer names the folder from the clock before wandb.init, so a folder is a candidate only if its
    timestamp lies in [start - MATCH_BEFORE_S, start + MATCH_AFTER_S]. When two sessions (e.g. an aborted
    duplicate launch) compete for one folder, the closer one gets it and the other has none.
    """
    pairs = []
    for i, r in enumerate(rows):
        names = [n for n in (r["tag"], r["run_name"]) if n]
        cands = [c for n in set(names) for c in by_suffix.get(n, [])] if names else flat
        start = r["_start"]
        for ts, rel in cands:
            d = (start - ts).total_seconds()
            if -MATCH_AFTER_S <= d <= MATCH_BEFORE_S:
                pairs.append((abs(d), i, rel))
    taken_rows, taken_dirs = set(), set()
    for _, i, rel in sorted(pairs):
        if i not in taken_rows and rel not in taken_dirs:
            rows[i]["results_dir"] = rel
            taken_rows.add(i)
            taken_dirs.add(rel)


def resumed_from(load_path, start):
    """(folder relpath, checkpoint number restored) for a --load-checkpoint path."""
    if not load_path:
        return "", ""
    p = load_path if os.path.isabs(load_path) else os.path.join(REPO, load_path)
    p = os.path.normpath(p)
    if os.path.basename(p) in ("models", "checkpoints"):
        p = os.path.dirname(p)
    elif os.path.basename(p).isdigit():
        p = os.path.dirname(os.path.dirname(p))
    folder = os.path.relpath(p, REPO) if p.startswith(REPO) else load_path
    before = []
    for sub in ("models", "checkpoints"):
        d = os.path.join(p, sub)
        if os.path.isdir(d):
            for n in os.listdir(d):
                if n.isdigit() and os.path.getmtime(os.path.join(d, n)) <= start.timestamp():
                    before.append(int(n))
    return folder, (max(before) if before else "")


def session_row(run_dir):
    meta = json.load(open(os.path.join(run_dir, "files", "wandb-metadata.json")))
    args = meta.get("args", [])
    base = os.path.basename(run_dir)
    m = re.match(r"^run-(\d{8}_\d{6})-([a-z0-9]+)$", base)
    start = parse_ts(m.group(1), "%Y%m%d_%H%M%S")
    program = meta.get("program", "")
    trainer = "dreamer_srl" if "dreamer_srl" in program else os.path.basename(program).replace(".py", "")
    tag = arg_value(args, "--tag")
    name = arg_value(args, "--wandb-name") or tag
    ac = arg_value(args, "--agent_config", "--agent-config")
    algorithm = ("DreamerSRL" if trainer == "dreamer_srl" else
                 "RecurrentPPO" if "recurrent_ppo" in ac else
                 "DreamerV3" if "dreamer" in ac else "")
    target = arg_value(args, "--episodes", "--total-steps")
    rdir, rck = resumed_from(arg_value(args, "--load-checkpoint"), start)
    host = meta.get("host", "")
    node = host.split("-")[-1] if re.match(r"^docker-\d+$", host) else ""
    device = arg_value(args, "--device")
    console = os.path.join(run_dir, "files", "output.log")
    recent = os.path.exists(console) and time.time() - os.path.getmtime(console) < RUNNING_WINDOW_S
    return {
        "wandb_id": m.group(2), "run_name": name, "session": 0, "status": "",
        "session_start": start.strftime("%Y-%m-%d %H:%M:%S"), "node": node,
        "gpu": device.split(":")[-1] if device.startswith("cuda:") else "",
        "first_ckpt": "", "last_ckpt": "", "n_ckpt": 0, "target_episodes": target, "results_dir": "",
        "resumed_from_dir": rdir, "resumed_from_ckpt": rck, "algorithm": algorithm,
        "trainer": trainer, "tag": tag, "wandb_group": arg_value(args, "--wandb-group"),
        "wandb_job_type": arg_value(args, "--wandb-job-type"),
        "wandb_project": arg_value(args, "--wandb-project"), "seed": arg_value(args, "--seed"),
        "env_config": arg_value(args, "--config", "--env-config"),
        "agent_config": arg_value(args, "--agent_config", "--agent-config"),
        "git_commit": (meta.get("git") or {}).get("commit", "")[:8],
        "wandb_dir": os.path.relpath(run_dir, REPO), "_recent": recent, "_start": start,
    }


def assign_status(rows):
    by_id = {}
    for r in rows:
        by_id.setdefault(r["wandb_id"], []).append(r)
    for sessions in by_id.values():
        sessions.sort(key=lambda r: r["session_start"])
        for i, r in enumerate(sessions, 1):
            r["session"] = i
            res, last, tgt = r["results_dir"], r["last_ckpt"], r["target_episodes"]
            if res.startswith("results/_aborted/"):
                r["status"] = "aborted"
            elif res.startswith("results/_superseded/"):
                r["status"] = "superseded"
            elif tgt.isdigit() and last != "" and last >= FINISHED_FRACTION * int(tgt):
                r["status"] = "finished"
            elif i < len(sessions):
                r["status"] = "resumed_later"
            elif r["_recent"]:
                r["status"] = "running"
            elif not res:
                r["status"] = "no_results"
            else:
                r["status"] = "stopped"


def live_check(rows):
    """Ask each node whether the newest session of each unfinished run still has a process."""
    from_node = {}
    for r in rows:
        if r["status"] in ("running", "stopped") and r["node"] and (r["tag"] or r["run_name"]):
            from_node.setdefault(r["node"], []).append(r)

    def check(node):
        cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-p", "1800",
               f"vncuser@192.168.0.{node}", "pgrep -af 'train[.]py|dreamer_srl_main' || true"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return node, None
        return node, (r.stdout if r.returncode == 0 else None)

    with ThreadPoolExecutor(8) as ex:
        for node, out in ex.map(check, list(from_node)):
            if out is None:
                continue  # node unreachable: keep the file-based status
            tokens = [set(line.split()) for line in out.splitlines()]
            for r in from_node[node]:
                key = r["tag"] or r["run_name"]
                r["status"] = "running" if any(key in t for t in tokens) else "stopped"


def build(live):
    by_suffix, flat = index_results()
    dirs = [d for d in sorted(glob.glob(os.path.join(REPO, "wandb", "run-*")))
            if os.path.exists(os.path.join(d, "files", "wandb-metadata.json"))]
    with ThreadPoolExecutor(WORKERS) as ex:
        rows = list(ex.map(session_row, dirs))
    match_results(rows, by_suffix, flat)

    def fill_ckpts(r):
        res = r["results_dir"]
        if res.startswith("results/JAX_"):
            r["algorithm"] = res.split("/")[1][len("JAX_"):]
        nums = ckpt_numbers(os.path.join(REPO, res)) if res else []
        if nums:
            r.update(first_ckpt=nums[0], last_ckpt=nums[-1], n_ckpt=len(nums))

    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(fill_ckpts, rows))
    assign_status(rows)
    if live:
        live_check(rows)
    rows.sort(key=lambda r: (r["session_start"], r["wandb_id"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, OUT)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"wrote {os.path.relpath(OUT, REPO)}: {len(rows)} sessions, "
          f"{len({r['wandb_id'] for r in rows})} WandB runs; " +
          ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


def load():
    with open(OUT, newline="") as f:
        return list(csv.DictReader(f))


def find(terms):
    terms = [t.lower() for t in terms]
    hits = [r for r in load()
            if all(t in " ".join((r["run_name"], r["tag"], r["wandb_id"], r["wandb_group"])).lower()
                   for t in terms)]
    for r in hits:
        print(f"{r['wandb_id']}  s{r['session']}  {r['status']:<13} {r['session_start']}  "
              f"{(r['node'] + ':' + r['gpu']) if r['node'] else '?':<7} ckpt {r['last_ckpt'] or '-':>9}"
              f"/{r['target_episodes'] or '?':<9} {r['run_name']}  {r['results_dir']}")
    print(f"{len(hits)} session(s)")


def resume(key):
    rows = [r for r in load() if key in (r["wandb_id"], r["run_name"], r["tag"])]
    if not rows:
        sys.exit(f"no run with name, tag or WandB id '{key}' (run `build` first if it is new)")
    ids = {r["wandb_id"] for r in rows}
    if len(ids) > 1:
        sys.exit(f"'{key}' matches several WandB runs {sorted(ids)}; pass the WandB id")
    rows.sort(key=lambda r: int(r["session"]))
    have = [r for r in rows if r["last_ckpt"]]
    if not have:
        sys.exit("no checkpoint saved in any session of this run: nothing to resume from")
    best = max(have, key=lambda r: int(r["last_ckpt"]))
    latest = rows[-1]
    print(f"run {latest['run_name']}  WandB id {latest['wandb_id']}  status {latest['status']}")
    print(f"newest checkpoint: {best['last_ckpt']} in {best['results_dir']} (session {best['session']})")
    if latest["status"] == "running":
        print("WARNING: the latest session looks RUNNING; check it is really stopped "
              "(`build --live`) before resuming, or you get two processes on one WandB run.")
    if latest["status"] == "finished":
        print("NOTE: this run already reached its target episodes.")
    meta = json.load(open(os.path.join(REPO, latest["wandb_dir"], "files", "wandb-metadata.json")))
    args = list(meta.get("args", []))
    for flag in ("--load-checkpoint", "--wandb-resume-id", "--load-episode"):
        while flag in args:
            i = args.index(flag)
            del args[i:i + 2]
    if latest["trainer"] == "dreamer_srl":
        extra = ["--load-checkpoint", f"{best['results_dir']}/checkpoints"]
        print("NOTE: dreamer_srl has no WandB-resume flag; the resumed session gets a NEW WandB run.")
    else:
        extra = ["--load-checkpoint", f"{best['results_dir']}/models",
                 "--wandb-resume-id", latest["wandb_id"]]
    prog = "train.py" if latest["trainer"] == "train" else "-m src.algorithms.dreamer_srl.dreamer_srl_main"
    quoted = " ".join(a if re.match(r"^[\w./:=,+-]+$", a) else f'"{a}"' for a in args + extra)
    print("\nresume flags:  " + " ".join(extra))
    print(f"full command (set --device for the new card):\n  python {prog} {quoted}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="rebuild runs.csv from wandb/ and results/")
    b.add_argument("--live", action="store_true", help="ask nodes over ssh which unfinished runs are alive")
    f = sub.add_parser("find", help="print sessions matching all terms")
    f.add_argument("terms", nargs="+")
    r = sub.add_parser("resume", help="print the flags to resume a run")
    r.add_argument("key")
    a = p.parse_args()
    os.chdir(REPO)
    if a.cmd == "build":
        build(a.live)
    elif a.cmd == "find":
        find(a.terms)
    else:
        resume(a.key)


if __name__ == "__main__":
    main()
