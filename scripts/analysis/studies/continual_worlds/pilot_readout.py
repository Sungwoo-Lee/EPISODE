#!/usr/bin/env python3
"""pilot_readout.py - read-out of the continual-worlds pilots (finished OR still-training runs).

Design: docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md (Revision 1)
  3.3 plateau + stage-length rule, 3.6 pilots (survivable rule, "too easy" flag, Pilot 3 pass
  criterion), 5.1 dip / recovery / return, 4 run manifest.
  Revision 2a (5.1, 2, 7.9, 7.11): common-reference companion. Ordinary and modulated runs are paired by
  tag with the agent token and any relaunch suffix removed (sequence / world + seed, e.g.
  rppo_cw_p3_s42); for each switch of a pair, R_common = min(R_ord, R_mod), dip against R_common in
  survival steps (and as a fraction), recovery to 0.9 x R_common in episodes and env steps, and the
  votes: H-dip counts only if own AND common favour the same agent, H-rec only if all four
  (own / common x episodes / env steps) do; otherwise "not counted". Pilot pairs are descriptive;
  a vote role is given only to sequence pairs launched as wandb-job-type `prod`.

Run-agnostic: the run list is parsed from the design doc's section-4 manifest table (every row with a
WandB id), and each run is classified from its OWN launch arguments (wandb-metadata.json):
  * `--continual-schedule`            -> "sequence"  (Pilot 2 now; the P1-P3 branches later)
  * single world + `--load-checkpoint` -> "world"     (Pilot 1: Home -> X)
  * single world, no checkpoint        -> "scratch"   (Pilot 3: Nursery legs; later Home legs)
The Home reference of a loaded run is found from its `--load-checkpoint` path: results dir -> tag ->
the local wandb folder launched with that `--tag`. Nothing run-specific is hard-coded.

Data: ONLY the local WandB binary `wandb/run-*-<id>/run-<id>.wandb` (never the web API) and the run's
stdout log ("Training complete"). Survival = `Episode/Steps` (survival steps per episode; the doc
writes `Episode/Steps_mean`, the trainer logs the mean under `Episode/Steps`). Reward is never read.

Row weighting (3.3): rows are logged every 4,000 episodes, each the mean of a rolling window of up to
5,000 episodes (`Episode/_window_n`); a row is weighted by the episodes it covers, delta
`Episode/Number`; rows with `_window_n` < 1,000 are skipped (5.1). The start counter of a run is
first_row.Number - first_row._window_n (the restored counter for a loaded run, 0 from scratch).
Environment steps = sum(delta episodes x survival) from the switch (3.3 / 5.1).

Windows: "trailing 200k at e" = rows in (e - 200k, e] of the same stage; it counts only when a FULL
200k has elapsed since the stage start. "20k running mean" (recovery) likewise requires a full 20k.

Partial runs: every number that depends on the run's end (plateau T, R_X, survivable verdict, L_X,
Pilot 3 pass) is computed on the data so far and marked provisional.

Usage:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      scripts/analysis/studies/continual_worlds/pilot_readout.py \
      --design-doc docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md \
      --json-out results/analysis/continual_worlds/pilot_readout.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))

# =============================================================================================
# PRE-REGISTERED CONSTANTS - every value cites CONTINUAL_WORLDS.md (Revision 1; common reference Rev 2a). check_doc()
# asserts that each one still appears verbatim in the doc text, so a doc revision fails loudly.
# =============================================================================================
PLATEAU_WINDOW = 200_000        # 3.3  trailing mean over (e - 200,000, e]
PLATEAU_FRAC = 0.95             # 3.3  T = first e with trailing >= 0.95 x best window
NOT_PLATEAUED_TAIL = 500_000    # 3.3  T in the last 500,000 episodes of a pilot -> "not plateaued"
L_MIN, L_MAX = 1_000_000, 3_000_000   # 3.3  L_X = min(3M, max(1M, 1.5 x max(T_ord, T_mod)))
L_MULT, L_ROUND = 1.5, 100_000        # 3.3  ... rounded up to a multiple of 100,000
DIP_WINDOW = 20_000             # 3.6 / 5.1  dip = 1 - S(first 20,000 episodes) / reference
RECOVERY_FRAC = 0.9             # 5.1  recovery: 20k running mean first reaches 0.9 x R_X
LEVEL_WINDOW = 200_000          # 5.1  R_X = last 200,000 episodes of X's first visit; 3.6 last 200k
MIN_WINDOW_N = 1_000            # 5.1  rows under 1,000 episodes are skipped
SURVIVABLE_FRAC = 0.5           # 3.6  mean survival >= 50 % of that agent's Home level
SURVIVABLE_BITES = 1.0          # 3.6  mean Episode/FoodEaten >= 1.0 bite per episode
TOO_EASY_FRAC, TOO_EASY_DIP = 0.95, 0.05   # 3.6  both agents >= 95 % of Home and dip < 5 %
# 3.6 Pilot 3 pass criterion (last 200,000 episodes of the leg): key -> (op, threshold)
P3_CRITERIA = {
    "survival": (">=", 200.0),                      # mean Episode/Steps(_mean)
    "FoodEaten": (">=", 15.0),                      # mean Episode/FoodEaten
    "Bal_EatRatio": (">=", 2.0),                    # Episode/Bal_EatRatio
    "Bal_HideRatio_True": (">=", 2.0),              # Episode/Bal_HideRatio_True
    "Bal_TimeWarm": (">=", 0.10),                   # Episode/Bal_TimeWarm
    "Bal_LateDeath_Thermal": ("<=", 0.25),          # Episode/Bal_LateDeath_Thermal
}
P3_COLLAPSE_FRAC = 0.8          # 3.6  trailing 200k never below 0.8 x the first competent window
# Home level: the doc's "final Home survival (factorial section 7)" = mean Episode/Steps over the
# LAST 10 % OF TRAINING (LEVEL05_BODY_INTERACTIONS.md 7.2: "Survival = WandB, last 10 % of
# training"); the 124.9 / 126.7 survivable lines in 3.6 are 50 % of those. Recomputed here and
# asserted equal to the doc's numbers (3.4) to 0.05 steps.
HOME_LEVEL_FRACTION = 0.10
HOME_ASSERT_TOL = 0.05

DOC_PATTERNS = [  # (regex that must match the design doc, what it pins)
    (r"\(\*e\* − 200,000, \*e\*\]", "PLATEAU_WINDOW"),
    (r"≥ 0\.95 × best", "PLATEAU_FRAC"),
    (r"last 500,000 episodes of a\s+pilot", "NOT_PLATEAUED_TAIL"),
    (r"L_X = min\(3,000,000, max\(1,000,000, 1\.5 × max\(T_X,ordinary, T_X,modulated\)\)\)", "L rule"),
    (r"rounded up to a\s+multiple of 100,000", "L_ROUND"),
    (r"first 20,000 episodes vs\. Home level", "DIP_WINDOW (pilot 1)"),
    (r"first reaches\s+\*\*0\.9 × `R_X`\*\*", "RECOVERY_FRAC"),
    (r"last 200,000\s+episodes of X's first visit", "LEVEL_WINDOW"),
    (r"rows under 1,000 episodes are skipped", "MIN_WINDOW_N"),
    (r"≥ \*\*50 % of that agent's Home level\*\* \(ordinary ≥ 124\.9, modulated ≥ 126\.7 steps\)", "SURVIVABLE_FRAC"),
    (r"`Episode/FoodEaten` ≥ \*\*1\.0\*\* bite per episode", "SURVIVABLE_BITES"),
    (r"both agents ≥ 95 % of Home \*\*and\*\* a Home → X dip < 5 %", "TOO_EASY"),
    (r"\| Survives \| mean `Episode/Steps_mean` \| ≥ 200 steps", "P3 survival"),
    (r"≥ 15 bites per episode \*\*and\*\* ratio ≥ 2", "P3 FoodEaten / EatRatio"),
    (r"`Episode/Bal_HideRatio_True`.*\| ≥ 2 \|", "P3 HideRatio_True"),
    (r"≥ 0\.10 \*\*and\*\* ≤ 0\.25", "P3 TimeWarm / LateDeath_Thermal"),
    (r"never below 0\.8 × that window's value", "P3_COLLAPSE_FRAC"),
    # Revision 2a common-reference companion (5.1, 2, 7.11)
    (r"`R_X,common` = min\(`R_X,ord`, `R_X,mod`\)", "COMMON_REF = min(R_ord, R_mod)"),
    (r"in\s+\*\*absolute survival steps\*\* \(also shown as a fraction of `R_X,common`\)", "common dip in steps + fraction"),
    (r"reaches \*\*0\.9 × `R_X,common`\*\*, in episodes \*\*and\*\* environment steps", "common recovery, both units"),
    (r"favourable sign under \*\*both\*\* the own-reference and the\s+common-reference reading", "H-dip vote: 2 readings"),
    (r"favourable under \*\*all four\*\* readings\s+\(own / common reference × episodes / environment steps\)", "H-rec vote: 4 readings"),
    (r"\| 7\.11 \*\(Rev 2a\)\* \|", "failure mode 7.11"),
    (r"\| 7\.3 \| A world is never recovered \(censored\) for both agents", "failure mode 7.3"),
]
DEATH_CAUSES = ("Injury", "Starvation", "Thermal", "Overeating", "MaxSteps")   # Episode/Term_* (descriptive)
AGENT_KIND = {"t1none": "ordinary", "t16quad": "modulated"}   # 3.4 / 4 tag scheme


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def check_doc(text: str) -> None:
    missing = [what for pat, what in DOC_PATTERNS if not re.search(pat, text)]
    if missing:
        raise ValueError(f"design doc no longer states the pre-registered constants: {missing} "
                         "- update the constant block and DOC_PATTERNS together")


def parse_manifest(text: str) -> list[dict]:
    """Rows of the section-4 launch-manifest table that carry a WandB id.

    Run ids are "<n>" or a relaunch "<n>-r<k>". When relaunches of <n> exist, only the latest one
    (highest k) is kept: the original / earlier attempts were abandoned (e.g. a hung node)."""
    sec = text.split("## 4. Launch Manifest", 1)[1].split("### 4.1", 1)[0]
    runs = []
    for line in sec.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        m = re.fullmatch(r"(\d+)(?:-r(\d+))?", c[0]) if c else None
        if len(c) != 12 or not m:
            continue
        wid = c[10].strip("`")
        if not re.fullmatch(r"[a-z0-9]{8}", wid):
            continue
        logs = re.findall(r"`([^`]+)`", c[11]) or [c[11]]
        runs.append({"run": c[0], "base": int(m.group(1)), "attempt": int(m.group(2) or 1),
                     "status": c[1], "cell": c[2], "tag": c[3].strip("`"),
                     "job_type": c[5], "seed": int(c[6]), "node": c[7], "gpu": c[8], "wandb_id": wid, "log": logs[0]})
    if not runs:
        raise ValueError("no manifest rows with a WandB id found in section 4")
    latest = {}
    for r in runs:
        if r["base"] not in latest or r["attempt"] > latest[r["base"]]["attempt"]:
            latest[r["base"]] = r
    superseded = [r["run"] for r in runs if latest[r["base"]] is not r]
    if superseded:
        print(f"[manifest] superseded by a relaunch, not read: {', '.join(superseded)}", file=sys.stderr)
    return [r for r in runs if latest[r["base"]] is r]


def parse_home_numbers(text: str) -> dict:
    """3.4: results dir of each pre-trained agent + 'Their final Home survival (...)' numbers."""
    m = re.search(r"final Home survival \(factorial §7\): ([\d.]+) \(ordinary\) and ([\d.]+) \(modulated\)", text)
    if not m:
        raise ValueError("3.4 'Their final Home survival' sentence not found")
    dirs = dict(re.findall(r"\| (Ordinary|Modulated)[^|]*\| `(results/JAX_RecurrentPPO/[^`]+)`", text))
    if set(dirs) != {"Ordinary", "Modulated"}:
        raise ValueError(f"3.4 pre-trained run table not parsed: {dirs}")
    return {os.path.basename(dirs["Ordinary"]): float(m.group(1)),
            os.path.basename(dirs["Modulated"]): float(m.group(2))}


# ------------------------------------------------------------------------------------ reading --
def scan(wdir: str) -> tuple[list[dict], dict]:
    from wandb.proto import wandb_internal_pb2 as pb
    from wandb.sdk.internal import datastore

    f = glob.glob(os.path.join(wdir, "run-*.wandb"))
    if len(f) != 1:
        raise ValueError(f"{wdir}: expected one run-*.wandb")
    ds = datastore.DataStore()
    ds.open_for_scan(f[0])
    rows, cfg, it_rows = [], {}, []
    while True:
        data = ds.scan_data()
        if data is None:
            break
        rec = pb.Record()
        rec.ParseFromString(data)
        t = rec.WhichOneof("record_type")
        if t in ("run", "config"):
            for it in (rec.run.config.update if t == "run" else rec.config.update):
                cfg[it.key or "/".join(it.nested_key)] = json.loads(it.value_json)
            continue
        if t != "history":
            continue
        item = {(it.key or "/".join(it.nested_key)): it.value_json for it in rec.history.item}
        if "iteration" in item and "stage/index" in item:
            try:
                it_rows.append((int(json.loads(item["stage/index"])), float(json.loads(item["iteration"]))))
            except (TypeError, ValueError):
                pass
        if "Episode/Steps" not in item:
            continue
        r = {}
        for k, v in item.items():
            if k.startswith("Episode/") or k in ("timesteps", "stage/index", "_runtime"):
                try:
                    r[k] = float(json.loads(v))
                except (TypeError, ValueError):
                    pass
        rows.append(r)
    rows.sort(key=lambda r: r["Episode/Number"])
    return rows, {"cfg": cfg, "iterations": it_rows}


def wandb_dir(wid: str) -> str:
    hits = sorted(glob.glob(os.path.join(ROOT, "wandb", f"run-*-{wid}")))
    if len(hits) != 1:
        raise ValueError(f"wandb/run-*-{wid}: expected exactly one local folder, found {len(hits)}")
    return hits[0]


def launch_args(wdir: str) -> list[str]:
    return json.load(open(os.path.join(wdir, "files", "wandb-metadata.json"))).get("args", [])


def arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def find_wandb_by_tag(tag: str, date: str | None = None) -> str:
    """Local wandb folder launched with --tag <tag> (latest such folder). Folders from the results
    dir's launch date are searched first, then all folders."""
    hits = []
    pats = ([f"run-{date}_*"] if date else []) + ["run-*"]
    for pat in pats:
        for mf in glob.glob(os.path.join(ROOT, "wandb", pat, "files", "wandb-metadata.json")):
            try:
                if arg(json.load(open(mf)).get("args", []), "--tag") == tag:
                    hits.append(os.path.dirname(os.path.dirname(mf)))
            except (ValueError, OSError):
                continue
        if hits:
            break
    if not hits:
        raise ValueError(f"no local wandb folder launched with --tag {tag}")
    return sorted(hits)[-1]


# ---------------------------------------------------------------------------------- series ---
class Series:
    """Episode rows of one stage, weighted by delta Episode/Number (3.3)."""

    def __init__(self, rows: list[dict], start: float):
        self.start = start
        keep, prev = [], start
        for r in rows:
            e = r["Episode/Number"]
            w = e - prev
            prev = e
            if r.get("Episode/_window_n", 0) < MIN_WINDOW_N or w <= 0:
                continue
            keep.append((e, w, r))
        self.e = np.array([k[0] for k in keep])
        self.w = np.array([k[1] for k in keep])
        self.rows = [k[2] for k in keep]
        self.s = np.array([r["Episode/Steps"] for r in self.rows])
        self.cum_steps = np.cumsum(self.w * self.s)

    @property
    def last(self):
        return float(self.e[-1]) if len(self.e) else self.start

    def mean(self, key, lo, hi, weight=None):
        m = (self.e > lo) & (self.e <= hi)
        vals = np.array([r.get(key, np.nan) for r, k in zip(self.rows, m) if k])
        w = self.w[m] if weight is None else self.w[m] * weight[m]
        ok = ~np.isnan(vals)
        if not ok.any() or w[ok].sum() <= 0:
            return None
        return float((vals[ok] * w[ok]).sum() / w[ok].sum())

    def S(self, lo, hi):
        return self.mean("Episode/Steps", lo, hi)

    def steps_to(self, e):
        """Environment steps from the stage start to episode e (3.3)."""
        m = self.e <= e
        return float(self.cum_steps[m][-1]) if m.any() else 0.0

    def trailing(self, window):
        """(e, trailing mean) for every row with a full window since the stage start."""
        return [(float(e), self.S(e - window, e)) for e in self.e if e - self.start >= window]


def plateau(ser: Series):
    tr = ser.trailing(PLATEAU_WINDOW)
    if not tr:
        return None
    best_e, best = max(tr, key=lambda x: x[1])
    T_e = next(e for e, v in tr if v >= PLATEAU_FRAC * best)
    return {"best": best, "best_at_ep": best_e - ser.start, "T_ep": T_e - ser.start,
            "T_env_steps": ser.steps_to(T_e), "current_trailing": tr[-1][1]}


def recovery(ser: Series, R: float | None, censor: float | None):
    """First full 20k running-mean window reaching 0.9 x R, from the stage start (5.1)."""
    if R is None:
        return None
    for e, v in ser.trailing(DIP_WINDOW):
        if v >= RECOVERY_FRAC * R:
            return {"ep": e - ser.start, "env_steps": ser.steps_to(e), "censored": False}
    return {"ep": None, "env_steps": None, "censored": True, "censor_at": censor,
            "note": "not recovered" + (f" by {censor:,.0f}" if censor else " yet")}


def first_window(ser: Series):
    """Mean survival over the first 20,000 episodes after the switch (5.1), or None if not yet reached."""
    if ser.last - ser.start < DIP_WINDOW:
        return None
    return ser.S(ser.start, ser.start + DIP_WINDOW)


def dip(ser: Series, ref: float | None):
    s0 = first_window(ser)
    if ref is None or s0 is None:
        return None
    return 1 - s0 / ref


def last_level(ser: Series, key="Episode/Steps"):
    if ser.last - ser.start < LEVEL_WINDOW:
        return None
    return ser.mean(key, ser.last - LEVEL_WINDOW, ser.last)


def throughput(rows: list[dict], start: float):
    rt = [(r["Episode/Number"], r["_runtime"]) for r in rows if "_runtime" in r]
    if len(rt) < 2 or rt[-1][1] <= 0:
        return None
    return (rt[-1][0] - start) / (rt[-1][1] / 3600)     # episodes per hour since launch


# ------------------------------------------------------------------------------------ runs ---
_HOME_CACHE: dict = {}
_SERIES: dict = {}   # (run, stage or None) -> (Series of that switch, censor length or None); not written to JSON


def home_level(load_ckpt: str, doc_home: dict) -> dict:
    rdir = os.path.basename(os.path.dirname(load_ckpt.rstrip("/"))) if load_ckpt.rstrip("/").endswith("models") \
        else os.path.basename(load_ckpt.rstrip("/"))
    if rdir in _HOME_CACHE:
        return _HOME_CACHE[rdir]
    tag = re.sub(r"^\d{8}-\d{6}_", "", rdir)
    wdir = find_wandb_by_tag(tag, rdir[:8] if re.match(r"^\d{8}-", rdir) else None)
    rows, meta = scan(wdir)
    N = float(meta["cfg"]["episodes"])
    start = rows[0]["Episode/Number"] - rows[0]["Episode/_window_n"]
    ser = Series(rows, start)
    lvl = ser.S(N - HOME_LEVEL_FRACTION * N, N)
    out = {"results_dir": rdir, "wandb_dir": os.path.relpath(wdir, ROOT), "tag": tag,
           "budget": N, "level_last10pct": lvl, "level_last200k": ser.S(ser.last - LEVEL_WINDOW, ser.last),
           "doc_value": doc_home.get(rdir)}
    if out["doc_value"] is not None:
        if abs(lvl - out["doc_value"]) > HOME_ASSERT_TOL:
            raise AssertionError(f"Home level of {rdir}: recomputed {lvl:.2f} != doc {out['doc_value']}")
        out["doc_match"] = True
    _HOME_CACHE[rdir] = out
    return out


def read_run(m: dict, doc_home: dict) -> dict:
    wdir = wandb_dir(m["wandb_id"])
    args = launch_args(wdir)
    if arg(args, "--tag") != m["tag"]:
        raise ValueError(f"run {m['run']}: launch --tag {arg(args, '--tag')} != manifest {m['tag']}")
    rows, meta = scan(wdir)
    own = os.path.join(wdir, "files", "output.log")      # per-run stdout copy; never shared
    lp = own if os.path.exists(own) else _abs(m["log"])
    log = open(lp, errors="replace").read() if os.path.exists(lp) else ""
    d = {**m, "wandb_dir": os.path.relpath(wdir, ROOT), "finished": "Training complete" in log[-20000:],
         "log_found": bool(log), "agent": next((v for k, v in AGENT_KIND.items() if k in m["tag"]), "?"),
         "n_rows": len(rows)}
    if not rows:
        d["kind"] = "no episode rows yet"
        return d
    start = rows[0]["Episode/Number"] - rows[0]["Episode/_window_n"]
    d.update({"start_counter": start, "last_counter": rows[-1]["Episode/Number"],
              "episodes_done": rows[-1]["Episode/Number"] - start,
              "ep_per_hour": throughput(rows, start)})
    ckpt = arg(args, "--load-checkpoint")
    d["home"] = home_level(ckpt, doc_home) if ckpt else None
    if arg(args, "--continual-schedule"):
        d["kind"] = "sequence"
        analyse_sequence(d, rows, args, meta)
    elif ckpt:
        d["kind"] = "world"
        analyse_world(d, rows, float(meta["cfg"]["episodes"]))
    else:
        d["kind"] = "scratch"
        analyse_scratch(d, rows, float(meta["cfg"]["episodes"]))
    return d


def _eta(d, budget):
    rate = d.get("ep_per_hour")
    return (budget - d["last_counter"]) / rate if rate else None


def analyse_world(d, rows, budget):
    ser = Series(rows, d["start_counter"])
    home = d["home"]["level_last10pct"]
    length = budget - d["start_counter"]
    d["budget_counter"] = budget
    d["pilot_length"] = length
    d["eta_h"] = None if d["finished"] else _eta(d, budget)
    d["S_trailing200k"] = last_level(ser)
    d["bites_trailing200k"] = last_level(ser, "Episode/FoodEaten")
    p = plateau(ser)
    d["plateau"] = p
    if p:
        p["provisional"] = not d["finished"]
        # 3.3 fallback: T in the last 500k of the pilot -> not plateaued. On a partial run the same
        # test against the data so far is reported as 'still climbing' (provisional).
        horizon = length if d["finished"] else d["episodes_done"]
        p["in_last_500k"] = p["T_ep"] > horizon - NOT_PLATEAUED_TAIL
        p["status"] = ("not plateaued" if (d["finished"] and p["in_last_500k"]) else
                       "plateaued" if d["finished"] else "provisional")
    d["deaths_trailing200k"] = {c: last_level(ser, "Episode/Term_" + c) for c in DEATH_CAUSES}
    d["dip_vs_home"] = dip(ser, home)
    R = d["S_trailing200k"]
    d["R_X"] = R
    d["S_first20k"] = first_window(ser)
    d["dip_vs_R"] = dip(ser, R)
    d["recovery_to_0.9R"] = recovery(ser, R, None if not d["finished"] else length)
    _SERIES[(d["run"], None)] = (ser, None if not d["finished"] else length)
    if R is not None:
        surv = R >= SURVIVABLE_FRAC * home
        bites = d["bites_trailing200k"] is not None and d["bites_trailing200k"] >= SURVIVABLE_BITES
        d["survivable"] = {"survival_line": SURVIVABLE_FRAC * home, "survival_pass": surv,
                           "bites_pass": bites, "pass": surv and bites, "provisional": not d["finished"]}
        d["frac_of_home"] = R / home
    else:
        d["survivable"] = None


def analyse_scratch(d, rows, budget):
    ser = Series(rows, d["start_counter"])
    d["budget_counter"] = budget
    d["eta_h"] = None if d["finished"] else _eta(d, budget)
    d["S_trailing200k"] = last_level(ser)
    d["bites_trailing200k"] = last_level(ser, "Episode/FoodEaten")
    d["plateau"] = plateau(ser)

    def crit(lo, hi):
        vals = {"survival": ser.S(lo, hi), "FoodEaten": ser.mean("Episode/FoodEaten", lo, hi)}
        for k in ("Bal_EatRatio", "Bal_HideRatio_True", "Bal_TimeWarm", "Bal_LateDeath_Thermal"):
            vals[k] = ser.mean("Episode/" + k, lo, hi)
        res = {}
        for k, (op, thr) in P3_CRITERIA.items():
            v = vals[k]
            ok = v is not None and (v >= thr if op == ">=" else v <= thr)
            res[k] = {"value": v, "op": op, "threshold": thr, "pass": bool(ok)}
        # pooled cross-checks (ratio of pooled shares; late-death cause pooled over late deaths)
        pool = lambda sh, n: _pooled(ser, lo, hi, sh, n)
        eh, ef = pool("Bal_EatShare_Hungry", "Bal_N_Hungry"), pool("Bal_EatShare_Fed", "Bal_N_Fed")
        hh, hl = pool("Bal_BushShare_InjHi_True", "Bal_N_InjHi_True"), pool("Bal_BushShare_InjLo_True", "Bal_N_InjLo_True")
        lds = np.array([r.get("Episode/Bal_LateDeathShare", np.nan) for r in ser.rows])
        res["_pooled"] = {"EatRatio": eh / ef if eh is not None and ef else None,
                          "HideRatio_True": hh / hl if hh is not None and hl else None,
                          "LateDeath_Thermal": ser.mean("Episode/Bal_LateDeath_Thermal", lo, hi, weight=np.nan_to_num(lds))}
        return res

    if ser.last - ser.start >= LEVEL_WINDOW:
        c = crit(ser.last - LEVEL_WINDOW, ser.last)
        d["p3_criteria"] = c
        all_rows = all(v["pass"] for k, v in c.items() if not k.startswith("_"))
        # time to competence + collapse check (3.6)
        comp = None
        for e in ser.e:
            if e - ser.start >= LEVEL_WINDOW:
                cc = crit(e - LEVEL_WINDOW, e)
                if all(v["pass"] for k, v in cc.items() if not k.startswith("_")):
                    comp = (float(e), cc["survival"]["value"])
                    break
        collapse = None
        if comp:
            later = [(e, v) for e, v in ser.trailing(LEVEL_WINDOW) if e > comp[0]]
            low = min(later, key=lambda x: x[1]) if later else None
            collapse = {"competent_at_ep": comp[0] - ser.start, "competent_window_S": comp[1],
                        "min_trailing_after": low[1] if low else None,
                        "collapsed": bool(low and low[1] < P3_COLLAPSE_FRAC * comp[1])}
        d["p3_competence"] = collapse
        d["p3_pass"] = {"all_rows_last_window": all_rows,
                        "no_collapse": bool(collapse and not collapse["collapsed"]),
                        "pass": bool(all_rows and collapse and not collapse["collapsed"]),
                        "provisional": not d["finished"]}
    else:
        d["p3_criteria"] = d["p3_competence"] = d["p3_pass"] = None


def _pooled(ser, lo, hi, share, count):
    num = den = 0.0
    for e, r in zip(ser.e, ser.rows):
        if lo < e <= hi and "Episode/" + share in r and "Episode/" + count in r:
            num += r["Episode/" + share] * r["Episode/" + count]
            den += r["Episode/" + count]
    return num / den if den > 0 else None


def analyse_sequence(d, rows, args, meta):
    import yaml
    sched = yaml.safe_load(open(_abs(arg(args, "--continual-schedule"))))["continual"]
    bounds = [float(b) for b in sched["episode_boundaries"]]
    names = [re.sub(r"^\d+_", "", os.path.splitext(f)[0])
             for f in sorted(os.listdir(_abs(arg(args, "--configs-dir")))) if f.endswith(".yaml")]
    if len(names) != len(bounds):
        raise ValueError(f"run {d['run']}: {len(names)} stage files vs {len(bounds)} boundaries")
    d["budget_counter"] = bounds[-1]
    d["eta_h"] = None if d["finished"] else _eta(d, bounds[-1])
    home = d["home"]["level_last10pct"] if d["home"] else None
    its = {}
    for si, it in meta["iterations"]:
        its.setdefault(si, []).append(it)
    stages, first_R, prev_end = [], {}, home
    lo = d["start_counter"]
    for k, (name, hi) in enumerate(zip(names, bounds)):
        srows = [r for r in rows if lo < r["Episode/Number"] <= hi + 4000 and int(r.get("stage/index", -1)) == k]
        st = {"stage": k, "world": name, "from": lo, "to": hi, "length": hi - lo,
              "visit": sum(1 for s in stages if s["world"] == name) + 1}
        mism = [r["Episode/Number"] for r in rows if lo < r["Episode/Number"] <= hi and int(r.get("stage/index", k)) != k]
        st["stage_index_mismatch_rows"] = len(mism)
        if not srows:
            st["status"] = "not reached"
            stages.append(st)
            lo = hi
            continue
        ser = Series(srows, lo)
        done = ser.last >= hi - 4000
        st["status"] = "complete" if done else f"in progress ({ser.last - lo:,.0f} / {hi - lo:,.0f})"
        st["iterations"] = (max(its[k]) - min(its[k])) if its.get(k) else None
        st["level_last200k"] = last_level(ser)
        st["bites_last200k"] = last_level(ser, "Episode/FoodEaten")
        st["prev_stage_end_level"] = prev_end
        if st["visit"] == 1:
            R = st["level_last200k"]
            if done and R is not None:
                first_R[name] = R
            st["R_X"], st["R_X_provisional"] = R, not done
        else:
            st["R_X"], st["R_X_provisional"] = first_R.get(name), name not in first_R
        R = st["R_X"]
        st["S_first20k"] = first_window(ser)
        st["dip"] = dip(ser, R)
        _SERIES[(d["run"], k)] = (ser, st["length"] if done else None)
        st["dip_vs_prev_end"] = dip(ser, prev_end)
        st["recovery_to_0.9R"] = recovery(ser, R, st["length"] if done else None)
        st["plateau"] = plateau(ser)
        if st["visit"] > 1 and st["level_last200k"] is not None and R is not None:
            first = next(s for s in stages if s["world"] == name and s["visit"] == 1)
            r1, r2 = first.get("recovery_to_0.9R") or {}, st["recovery_to_0.9R"] or {}
            st["return"] = {"level_minus_R": st["level_last200k"] - R,
                            "dip_change": (st["dip"] - first["dip"]) if st["dip"] is not None and first.get("dip") is not None else None,
                            "recovery_ep_change": (r2.get("ep") - r1.get("ep")) if r1.get("ep") is not None and r2.get("ep") is not None else None,
                            "recovery_steps_change": (r2.get("env_steps") - r1.get("env_steps")) if r1.get("env_steps") is not None and r2.get("env_steps") is not None else None,
                            "provisional": not done}
        prev_end = st["level_last200k"]
        stages.append(st)
        lo = hi
    d["stages"] = stages


# --------------------------------------------------------------------------- stage lengths ---
def stage_lengths(runs: list[dict]) -> dict:
    groups = {}
    for d in runs:
        if d.get("kind") != "world":
            continue
        cell = re.sub(r"_(t1none|t16quad)_s\d+(_r\d+)?$", "", d["tag"])
        groups.setdefault(cell, {})[d["agent"]] = d
    out = {}
    for cell, g in groups.items():
        Ts = {a: (x["plateau"] or {}).get("T_ep") for a, x in g.items()}
        stat = {a: (x["plateau"] or {}).get("status") for a, x in g.items()}
        if None in Ts.values() or not g:
            out[cell] = {"L_X": None, "T": Ts, "note": "needs >= 200k episodes"}
            continue
        single = set(g) != {"ordinary", "modulated"}
        if any(s == "not plateaued" for s in stat.values()):
            L, note = L_MAX, "not plateaued -> 3 M cap (3.3 fallback)"
        else:
            raw = min(L_MAX, max(L_MIN, L_MULT * max(Ts.values())))
            L, note = math.ceil(raw / L_ROUND) * L_ROUND, ""
        prov = any(not x["finished"] for x in g.values())
        if single:   # e.g. ordinary-only scouts: L_X from the one agent, verdict per agent
            note = (note + "; " if note else "") + f"single agent ({', '.join(g)}) - not the two-agent rule"
        out[cell] = {"L_X": L, "T": Ts, "T_status": stat, "provisional": prov, "single_agent": single,
                     "per_agent_survivable": {a: (x.get("survivable") or {}).get("pass") for a, x in g.items()},
                     "per_agent_line": {a: (x.get("survivable") or {}).get("survival_line") for a, x in g.items()},
                     "note": note or ("provisional (runs still training)" if prov else "final"),
                     "too_easy": all(x.get("frac_of_home") is not None and x["frac_of_home"] >= TOO_EASY_FRAC
                                     and x.get("dip_vs_home") is not None and x["dip_vs_home"] < TOO_EASY_DIP
                                     for x in g.values()),
                     "survivable_both": (not single) and all((x.get("survivable") or {}).get("pass") for x in g.values()),
                     "survivable_one_only": (not single) and sum(bool((x.get("survivable") or {}).get("pass")) for x in g.values()) == 1}
        if prov and single:
            out[cell]["note"] += "; provisional (run still training)"
    return out


# ------------------------------------------------------- common-reference companion (Rev 2a) ---
def pair_key(tag: str) -> str:
    """Sequence/world + seed, with the agent token and a relaunch suffix removed:
    rppo_cw_p3_t16quad_s42 -> rppo_cw_p3_s42; rppo_cw_scout_fog_scout_b_t1none_s42_r2 -> ..._fog_scout_b_s42."""
    return re.sub(r"_(t1none|t16quad)(?=_s\d+$)", "", re.sub(r"_r\d+$", "", tag))


def _sign(diff):
    """modulated-minus-ordinary difference; negative favours the modulator (dip, recovery)."""
    if diff is None:
        return "pending"
    return "modulated" if diff < 0 else "ordinary" if diff > 0 else "tie"


def _rec_sign(r_ord, r_mod, unit, prog_ord, prog_mod):
    """Sign of a recovery difference in `unit` ('ep' | 'env_steps'), handling censoring. A run that has
    not recovered yet still loses to one that recovered in less than it has trained so far."""
    if r_ord is None or r_mod is None:
        return "pending", None
    vo, vm = r_ord.get(unit), r_mod.get(unit)
    if vo is not None and vm is not None:
        return _sign(vm - vo), vm - vo
    if vo is None and vm is None:
        final = r_ord.get("censor_at") is not None and r_mod.get("censor_at") is not None
        return ("both censored" if final else "pending"), None
    if vm is not None:          # ordinary censored
        return ("modulated" if r_ord.get("censor_at") is not None or prog_ord[unit] >= vm else "pending"), None
    return ("ordinary" if r_mod.get("censor_at") is not None or prog_mod[unit] >= vo else "pending"), None


def _vote(signs: dict, ref_pairs, unit_pairs) -> dict:
    """ref_pairs: (own, common) reading keys that must agree (7.11); unit_pairs: (episodes, env steps) keys
    that must agree (7.9). A vote counts only when every reading has the same sign."""
    vals = list(signs.values())
    if "pending" in vals:
        v, why = "pending", "a reading is not available yet"
    elif "both censored" in vals:
        v, why = "excluded", "7.3: never recovered by either agent"
    elif all(x == "modulated" for x in vals):
        v, why = "favourable", "all readings favour the modulator"
    elif all(x == "ordinary" for x in vals):
        v, why = "unfavourable", "all readings favour the ordinary agent"
    else:
        # A tie (equal values; recovery in episodes is resolved only to the 4,000-episode logging
        # interval) is not a favourable sign, so the vote is not counted; it is named as a tie rather
        # than as a 7.9 / 7.11 disagreement, which are checked between untied readings only.
        why = []
        split = lambda pairs: any(signs[a] != signs[b] and "tie" not in (signs[a], signs[b]) for a, b in pairs)
        if split(ref_pairs):
            why.append("7.11: own vs common reference disagree")
        if split(unit_pairs):
            why.append("7.9: episodes vs environment steps disagree")
        if "tie" in vals:
            why.append("tie: " + ", ".join(k for k, x in signs.items() if x == "tie"))
        v, why = "not counted", "; ".join(why) or "readings disagree"
    return {"vote": v, "reason": why}


def _switch(ser_o, ser_m, x_o, x_m, R_o, R_m, rec_o, rec_m) -> dict:
    """One switch of one pair. x_* = the run/stage dict carrying S_first20k and the own dip."""
    (so, co), (sm, cm) = ser_o, ser_m
    Rc = None if R_o is None or R_m is None else min(R_o, R_m)
    out = {"R_ord": R_o, "R_mod": R_m, "R_common": Rc,
           "S_first20k": {"ordinary": x_o.get("S_first20k"), "modulated": x_m.get("S_first20k")}}
    dc = {}
    for a, ser, x in (("ordinary", so, x_o), ("modulated", sm, x_m)):
        s0 = x.get("S_first20k")
        dc[a] = None if Rc is None or s0 is None else {"steps": Rc - s0, "frac": 1 - s0 / Rc}
    out["dip_common"] = dc
    rc = {"ordinary": recovery(so, Rc, co), "modulated": recovery(sm, Rc, cm)}
    out["recovery_common"] = rc
    out["recovery_own"] = {"ordinary": rec_o, "modulated": rec_m}
    own_dip = {"ordinary": x_o.get("_own_dip"), "modulated": x_m.get("_own_dip")}
    out["dip_own"] = own_dip
    # --- readings: modulated - ordinary, negative favours the modulator ---
    d_own = None if None in own_dip.values() else own_dip["modulated"] - own_dip["ordinary"]
    d_com = None if None in dc.values() else dc["modulated"]["steps"] - dc["ordinary"]["steps"]
    dip_r = {"own": {"diff_frac": d_own, "sign": _sign(d_own)},
             "common": {"diff_steps": d_com, "sign": _sign(d_com)}}
    prog = lambda ser: {"ep": ser.last - ser.start, "env_steps": float(ser.cum_steps[-1]) if len(ser.cum_steps) else 0.0}
    po, pm = prog(so), prog(sm)
    rec_r = {}
    for ref, (ro, rm) in (("own", (rec_o, rec_m)), ("common", (rc["ordinary"], rc["modulated"]))):
        for unit, lab in (("ep", "ep"), ("env_steps", "steps")):
            sg, diff = _rec_sign(ro, rm, unit, po, pm)
            rec_r[f"{ref}_{lab}"] = {"diff": diff, "sign": sg}
    out["dip_readings"], out["rec_readings"] = dip_r, rec_r
    out["H_dip"] = _vote({k: v["sign"] for k, v in dip_r.items()}, [("own", "common")], [])
    out["H_rec"] = _vote({k: v["sign"] for k, v in rec_r.items()},
                         [("own_ep", "common_ep"), ("own_steps", "common_steps")],
                         [("own_ep", "own_steps"), ("common_ep", "common_steps")])
    return out


def common_reference(runs: list[dict]) -> list[dict]:
    """5.1 Revision 2a: pair ordinary + modulated runs of the same sequence / world and seed, and read
    every switch against the shared reference R_common = min(R_ord, R_mod) next to each own reference."""
    groups = {}
    for d in runs:
        if d.get("kind") not in ("world", "sequence") or d["agent"] not in ("ordinary", "modulated"):
            continue
        g = groups.setdefault((d["kind"], pair_key(d["tag"])), {})
        if d["agent"] in g:
            raise ValueError(f"pair {pair_key(d['tag'])}: two {d['agent']} runs ({g[d['agent']]['run']}, {d['run']})")
        g[d["agent"]] = d
    out = []
    for (kind, key), g in sorted(groups.items()):
        if set(g) != {"ordinary", "modulated"}:
            continue      # single-agent scout: no pair, nothing to compare
        o, m = g["ordinary"], g["modulated"]
        role = ("vote" if kind == "sequence" and o["job_type"] == m["job_type"] == "prod"
                else "descriptive (pilot; not a vote)")
        pr = {"pair": key, "kind": kind, "role": role, "runs": {"ordinary": o["run"], "modulated": m["run"]},
              "switches": []}
        if kind == "world":
            if (o["run"], None) not in _SERIES or (m["run"], None) not in _SERIES:
                continue
            o["_own_dip"], m["_own_dip"] = o.get("dip_vs_R"), m.get("dip_vs_R")
            sw = _switch(_SERIES[(o["run"], None)], _SERIES[(m["run"], None)], o, m, o["R_X"], m["R_X"],
                         o["recovery_to_0.9R"], m["recovery_to_0.9R"])
            sw.update({"switch": "loaded -> " + re.sub(r"^rppo_cw_|_s\d+$", "", key), "stage": None, "visit": 1,
                       "loaded_from": {"ordinary": (o.get("home") or {}).get("tag"),
                                       "modulated": (m.get("home") or {}).get("tag")},
                       "provisional": not (o["finished"] and m["finished"])})
            o.pop("_own_dip"), m.pop("_own_dip")
            pr["switches"].append(sw)
        else:
            so, sm = o["stages"], m["stages"]
            if [(s["world"], s["to"]) for s in so] != [(s["world"], s["to"]) for s in sm]:
                raise ValueError(f"pair {key}: the two runs have different schedules")
            for a, b in zip(so, sm):
                k = a["stage"]
                if (o["run"], k) not in _SERIES or (m["run"], k) not in _SERIES:
                    continue
                a["_own_dip"], b["_own_dip"] = a.get("dip"), b.get("dip")
                sw = _switch(_SERIES[(o["run"], k)], _SERIES[(m["run"], k)], a, b, a["R_X"], b["R_X"],
                             a["recovery_to_0.9R"], b["recovery_to_0.9R"])
                a.pop("_own_dip"), b.pop("_own_dip")
                prev = so[k - 1]["world"] if k > 0 else "start"
                sw.update({"switch": f"{prev} -> {a['world']}", "stage": k, "visit": a["visit"],
                           "provisional": bool(a["R_X_provisional"] or b["R_X_provisional"]
                                               or a["status"] != "complete" or b["status"] != "complete")})
                pr["switches"].append(sw)
        out.append(pr)
    return out


# ------------------------------------------------------------------------------------ render --
def f(x, n=1, pct=False):
    if x is None:
        return "-"
    return f"{100 * x:+.1f}%" if pct else f"{x:,.{n}f}"


def k_(x):
    return "-" if x is None else f"{x / 1e3:,.0f}k"


def render_common(pairs) -> str:
    out = ["COMMON-REFERENCE COMPANION (5.1 Rev 2a) - per switch: own reference R_X of each agent vs shared "
           "R_common = min(R_ord, R_mod)",
           "  S20k = mean survival over the first 20k episodes after the switch; dip own = 1 - S20k/R_own; dip common ="
           " R_common - S20k (steps)",
           "  recovery = episodes (k) / env steps (M) until the 20k running mean reaches 0.9 x reference; "
           "votes: H-dip needs own+common agreement, H-rec all four (7.9 / 7.11)"]
    if not pairs:
        out.append("  (no ordinary + modulated pairs in this selection)")
    for pr in pairs:
        out.append(f"  pair {pr['pair']} ({pr['kind']}; runs ord {pr['runs']['ordinary']} / mod {pr['runs']['modulated']}; {pr['role']})")
        for sw in pr["switches"]:
            def rec(r):
                if not r:
                    return "-"
                if r.get("censored"):
                    return "cens." + ("" if r.get("censor_at") else "(open)")
                return f"{k_(r['ep'])}/{r['env_steps'] / 1e6:.1f}M"
            S, dc, do = sw["S_first20k"], sw["dip_common"], sw["dip_own"]
            out.append(f"    {sw['switch']:<24} v{sw['visit']}{' (provisional)' if sw['provisional'] else ''}  "
                       f"R ord {f(sw['R_ord'])} mod {f(sw['R_mod'])} common {f(sw['R_common'])}  S20k ord {f(S['ordinary'])} mod {f(S['modulated'])}")
            out.append(f"      dip own    ord {f(do['ordinary'], pct=True)} mod {f(do['modulated'], pct=True)}   "
                       f"dip common ord {f((dc['ordinary'] or {}).get('steps'))} ({f((dc['ordinary'] or {}).get('frac'), pct=True)}) "
                       f"mod {f((dc['modulated'] or {}).get('steps'))} ({f((dc['modulated'] or {}).get('frac'), pct=True)})")
            ro, rc = sw["recovery_own"], sw["recovery_common"]
            out.append(f"      recovery own ord {rec(ro['ordinary'])} mod {rec(ro['modulated'])}   "
                       f"common (to {f(sw['R_common'] and RECOVERY_FRAC * sw['R_common'])}) ord {rec(rc['ordinary'])} mod {rec(rc['modulated'])}")
            ds = " ".join(f"{k}={v['sign']}" for k, v in sw["dip_readings"].items())
            rs = " ".join(f"{k}={v['sign']}" for k, v in sw["rec_readings"].items())
            out.append(f"      H-dip: {sw['H_dip']['vote'].upper()} ({sw['H_dip']['reason']}) [{ds}]")
            out.append(f"      H-rec: {sw['H_rec']['vote'].upper()} ({sw['H_rec']['reason']}) [{rs}]")
    return "\n".join(out)


def render(runs, L, homes, pairs) -> str:
    out = ["HOME REFERENCE (pre-trained runs; level = last 10 % of training, as factorial 7.2 / design 3.4)"]
    for h in homes.values():
        out.append(f"  {h['tag']:<34} wandb {os.path.basename(h['wandb_dir'])[-8:]}  level {h['level_last10pct']:.2f}"
                   f"  (doc {h['doc_value']}, match {h.get('doc_match', 'n/a')})  last-200k {h['level_last200k']:.2f}"
                   f"  -> survivable line {SURVIVABLE_FRAC * h['level_last10pct']:.1f}")
    out.append("")
    hdr = (f"{'run':>5} {'tag':<42} {'done':>6} {'eta_h':>5} {'S_200k':>6} {'best':>6} {'T(ep)':>6} {'T(Msteps)':>9} "
           f"{'plateau':<13} {'dip':>7} {'rec(ep)':>7} {'rec(Mst)':>8} {'bites':>6} {'%home':>6} {'surv':>5}  deaths inj/starv/therm/cap")
    out.append("PILOT 1 - one world from the Home agent (dip = first 20k vs Home level; recovery = to 0.9 x current trailing-200k)")
    out.append(hdr)
    for d in runs:
        if d.get("kind") != "world":
            continue
        p = d["plateau"] or {}
        r = d["recovery_to_0.9R"] or {}
        sv = d["survivable"] or {}
        rec_ep = "cens." if r.get("censored") else k_(r.get("ep"))
        rec_st = "-" if r.get("env_steps") is None else f"{r['env_steps'] / 1e6:.2f}"
        out.append(f"{d['run']:>5} {d['tag']:<42} {k_(d['episodes_done']):>6} {f(d['eta_h'], 1):>5} {f(d['S_trailing200k']):>6} "
                   f"{f(p.get('best')):>6} {k_(p.get('T_ep')):>6} {f(p.get('T_env_steps', None) and p['T_env_steps'] / 1e6, 2):>9} "
                   f"{(p.get('status') or '-') + ('^' if p.get('in_last_500k') and not d['finished'] else ''):<13} "
                   f"{f(d['dip_vs_home'], pct=True):>7} {rec_ep:>7} {rec_st:>8} "
                   f"{f(d['bites_trailing200k']):>6} {f(d.get('frac_of_home'), 2):>6} "
                   f"{('-' if not sv else ('PASS' if sv['pass'] else 'FAIL')) + ('*' if sv and sv['provisional'] else ''):>5}  "
                   + "/".join(f(d["deaths_trailing200k"][c], 2) for c in ("Injury", "Starvation", "Thermal", "MaxSteps")))
    if not any(d.get("kind") == "world" for d in runs):
        out.append("  (no single-world runs in this selection)")
    out.append("  (* = provisional, run still training; ^ = T lies in the last 500k of the data so far, i.e. the 3.3")
    out.append("   'not plateaued' test would fire if the run ended now; dip > 0 means worse than Home; deaths = share of")
    out.append("   episodes ending by injury / starvation / cold-heat / reaching the 500-step cap, last 200k)")
    out.append("")
    out.append("PILOT 1 - proposed stage length L_X = min(3M, max(1M, 1.5 x max(T_ord, T_mod))), ceil 100k")
    for cell, x in L.items():
        T = x["T"]
        out.append(f"  {cell.removeprefix('rppo_cw_'):<28} T_ord {k_(T.get('ordinary')):>6}  T_mod {k_(T.get('modulated')):>6}  L_X {k_(x['L_X']):>6}  "
                   f"[{x['note']}]" + ("  TOO-EASY FLAG" if x.get("too_easy") else "")
                   + ("  SURVIVABLE (" + ", ".join(f"{a} vs {f(x['per_agent_line'][a])}: " + ("PASS" if v else "FAIL")
                                                   for a, v in x["per_agent_survivable"].items()) + ")"
                      if x.get("single_agent") else
                      "  SURVIVABLE: both" if x.get("survivable_both") else
                      "  SURVIVABLE: ONE AGENT ONLY" if x.get("survivable_one_only") else
                      "  SURVIVABLE: neither" if "survivable_both" in x else ""))
    out.append("")
    out.append("PILOT 2 - sequences (level = last 200k of stage; R_X = first visit's level; dip vs R_X and vs previous stage end)")
    for d in runs:
        if d.get("kind") != "sequence":
            continue
        out.append(f"  run {d['run']} {d['tag']}  done {k_(d['episodes_done'])}  eta {f(d['eta_h'], 1)} h")
        out.append(f"    {'st':>2} {'world':<8} {'v':>1} {'status':<28} {'level':>6} {'R_X':>6} {'prevEnd':>7} {'dip':>7} {'dipPrev':>7} "
                   f"{'rec(ep)':>7} {'rec(Mst)':>8} {'bites':>6} {'iters':>6} {'return':>7}")
        for s in d["stages"]:
            if s["status"] == "not reached":
                out.append(f"    {s['stage']:>2} {s['world']:<8} {s['visit']:>1} not reached")
                continue
            r = s["recovery_to_0.9R"] or {}
            rt = s.get("return") or {}
            out.append(f"    {s['stage']:>2} {s['world']:<8} {s['visit']:>1} {s['status']:<28} {f(s['level_last200k']):>6} "
                       f"{f(s['R_X']) + ('*' if s['R_X_provisional'] and s['R_X'] is not None else ''):>6} {f(s['prev_stage_end_level']):>7} "
                       f"{f(s['dip'], pct=True):>7} {f(s['dip_vs_prev_end'], pct=True):>7} "
                       f"{'cens.' if r.get('censored') else k_(r.get('ep')):>7} {f(r.get('env_steps') and r['env_steps'] / 1e6, 2):>8} "
                       f"{f(s['bites_last200k']):>6} {f(s.get('iterations'), 0):>6} {f(rt.get('level_minus_R')):>7}")
    if not any(d.get("kind") == "sequence" for d in runs):
        out.append("  (no sequence runs in this selection)")
    out.append("")
    out.append("PILOT 3 - from scratch, pass criterion on the last 200k (value / threshold / pass)")
    for d in runs:
        if d.get("kind") != "scratch":
            continue
        c = d["p3_criteria"]
        out.append(f"  run {d['run']} {d['tag']}  done {k_(d['episodes_done'])}  eta {f(d['eta_h'], 1)} h")
        if not c:
            out.append("    (< 200k episodes)")
            continue
        for key, v in c.items():
            if key.startswith("_"):
                continue
            out.append(f"    {key:<22} {f(v['value'], 3):>9} {v['op']} {v['threshold']:<6} {'pass' if v['pass'] else 'FAIL'}")
        pl = c["_pooled"]
        out.append(f"    pooled cross-check: EatRatio {f(pl['EatRatio'], 2)}  HideRatio_True {f(pl['HideRatio_True'], 2)}  "
                   f"LateDeath_Thermal {f(pl['LateDeath_Thermal'], 3)}")
        comp = d["p3_competence"]
        out.append(f"    competence: {('first competent 200k window ends at ' + k_(comp['competent_at_ep']) + ', S ' + f(comp['competent_window_S']) + ', min trailing after ' + f(comp['min_trailing_after']) + (' COLLAPSED' if comp['collapsed'] else ' no collapse')) if comp else 'no window meets all rows yet'}")
        pp = d["p3_pass"]
        out.append(f"    PILOT 3 VERDICT: {'PASS' if pp['pass'] else 'FAIL'}{' (provisional)' if pp['provisional'] else ''}")
    if not any(d.get("kind") == "scratch" for d in runs):
        out.append("  (no from-scratch runs in this selection)")
    out.append("")
    out.append(render_common(pairs))
    other = [d for d in runs if d.get("kind") not in ("world", "sequence", "scratch")]
    for d in other:
        out.append(f"  run {d['run']} {d['tag']}: {d.get('kind')}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--design-doc", required=True, help="CONTINUAL_WORLDS.md (manifest + pre-registered rules)")
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--runs", nargs="*", help="restrict to these manifest run ids, e.g. 13 39-r2 "
                    "(a bare number also selects its latest relaunch)")
    a = ap.parse_args()
    text = open(_abs(a.design_doc)).read()
    check_doc(text)
    doc_home = parse_home_numbers(text)
    man = parse_manifest(text)
    if a.runs:
        want = set(a.runs)
        man = [m for m in man if m["run"] in want or str(m["base"]) in want]
        found = {m["run"] for m in man} | {str(m["base"]) for m in man}
        if want - found:
            raise ValueError(f"--runs not in the manifest (or superseded by a relaunch): {sorted(want - found)}")
    runs = [read_run(m, doc_home) for m in man]
    L = stage_lengths(runs)
    pairs = common_reference(runs)
    print(render(runs, L, _HOME_CACHE, pairs))
    os.makedirs(os.path.dirname(_abs(a.json_out)), exist_ok=True)
    json.dump({"design_doc": a.design_doc, "home": _HOME_CACHE, "runs": runs, "stage_lengths": L,
               "common_reference": pairs},
              open(_abs(a.json_out), "w"), indent=1, default=float)
    print(f"\nwrote {a.json_out}")


if __name__ == "__main__":
    sys.exit(main())
