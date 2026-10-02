#!/usr/bin/env python3
"""pilot_pick.py - survival-based strength pick from short calibration pilots.

Implements the stage-1 pick rule of
docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md §2.3 (Revisions 1-2)
and the §2.4 collapse check, for ANY set of runs described by a manifest YAML (see
docs/experiments/active/level05_body_interactions/pilot_pick_manifest.yaml for the format).

Data source: the LOCAL WandB binary `wandb/run-*-<id>/run-<id>.wandb` (never the web API). Each
`Episode/*` history row is a rolling-window mean whose sample count is `Episode/_window_n`.

Read-out per run (exactly as §2.3 words it):
  S      = `_window_n`-weighted mean of `Episode/Steps` over rows whose `Episode/Number` lies in
           (N - f*N, N], N = the run's configured `episodes`, f = readout_fraction (0.10).
           The lower bound is exclusive: the row stamped at 1.8 M summarises episodes before 1.8 M.
  starve = the same weighted mean of `Episode/Term_Starvation` (fraction of episodes ending by
           starvation). Reward is never read.
Reference: S_base = mean S of the `role: base` runs, n = their sample SD (ddof=1),
           starve_base = their mean starvation share.
Definitions:
  noticeable (non-negligible):  S_base - S >= min(max(k*n, a*S_base), c*S_base)
  survivable:                   S >= s*S_base  and  starve <= starve_base + r
Pick per factor (strengths listed weak -> strong in the manifest):
  weakest_noticeable   -> first strength that is noticeable AND survivable.
                          If no strength is noticeable: strongest survivable, flagged.
  strongest_survivable -> last survivable strength (noticeable recorded, not required).
  Either rule: if the weakest strength is not survivable -> STOP (no pick, report to user).
  A case the doc does not cover (some strength noticeable, none noticeable-and-survivable, weakest
  survivable) -> UNRESOLVED (no pick, report to user). Never silently resolved.
Group (form) choice: among a group's factors, keep the one whose pick is noticeable; if several,
  keep `preferred_form`; if none, keep `fallback` and flag.
Also flagged: non-monotone survival with strength; NaN; collapse-like strengths (§2.4 thresholds);
  cap binding (2n > c*S_base -> "noise-limited").

Completeness: by default every run must have logged Episode/Number == N and (if `log:` given) the
log must contain "Training complete". `--allow-partial` instead reads the last f of the episodes
reached SO FAR and marks every number PARTIAL - for tooling tests only, never for the pick.

Usage:
  python scripts/analysis/studies/level05_body_interactions/pilot_pick.py MANIFEST.yaml \
      [--allow-partial] [--md-out FILE] [--json-out FILE]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import numpy as np
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))

STEPS, NUM, WN, STARVE = "Episode/Steps", "Episode/Number", "Episode/_window_n", "Episode/Term_Starvation"


# ---------------------------------------------------------------------------------------- I/O --
def _abs(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def wandb_dir_for(run: dict) -> str:
    wid = run.get("wandb_id")
    if not wid:
        raise ValueError(f"{run['id']}: manifest row has no wandb_id")
    hits = sorted(glob.glob(os.path.join(ROOT, "wandb", f"run-*-{wid}")))
    if len(hits) != 1:
        raise ValueError(f"{run['id']}: expected exactly one wandb/run-*-{wid}, found {hits}")
    return hits[0]


def read_history(wdir: str, allow_truncated: bool) -> tuple[list[dict], dict]:
    """From the local .wandb binary: (episode rows {Number, Steps, n, starve}, run config dict).

    The config comes from the binary's own run/config records, because `files/config.yaml` is
    only written when a run finishes."""
    from wandb.proto import wandb_internal_pb2 as pb
    from wandb.sdk.internal import datastore

    files = glob.glob(os.path.join(wdir, "run-*.wandb"))
    if len(files) != 1:
        raise ValueError(f"{wdir}: expected one run-*.wandb, found {files}")
    ds = datastore.DataStore()
    ds.open_for_scan(files[0])
    rows, cfg = [], {}
    while True:
        try:
            data = ds.scan_data()
        except Exception as e:  # a run still being written can end mid-record
            if allow_truncated:
                break
            raise RuntimeError(f"{files[0]}: unreadable record ({e})") from e
        if data is None:
            break
        rec = pb.Record()
        rec.ParseFromString(data)
        rtype = rec.WhichOneof("record_type")
        if rtype in ("run", "config"):
            upd = rec.run.config.update if rtype == "run" else rec.config.update
            for it in upd:
                cfg[it.key or "/".join(it.nested_key)] = json.loads(it.value_json)
            continue
        if rtype != "history":
            continue
        item = {(it.key or "/".join(it.nested_key)): it.value_json for it in rec.history.item}
        if NUM not in item or STEPS not in item:
            continue
        for k in (WN, STARVE):
            if k not in item:
                raise ValueError(f"{wdir}: episode row at {item[NUM]} lacks {k}")
        rows.append({"Number": float(item[NUM]), "Steps": float(item[STEPS]),
                     "n": float(item[WN]), "starve": float(item[STARVE])})
    if not rows:
        raise ValueError(f"{wdir}: no Episode rows found")
    return rows, cfg


def run_meta(wdir: str, cfg: dict) -> dict:
    for k in ("episodes", "tag"):
        if k not in cfg:
            raise ValueError(f"{wdir}: WandB run config has no {k!r}")
    args = json.load(open(os.path.join(wdir, "files", "wandb-metadata.json"))).get("args", [])
    return {"episodes": int(cfg["episodes"]), "tag": cfg["tag"],
            "config": args[args.index("--config") + 1] if "--config" in args else None}


# ------------------------------------------------------------------------------------ read-out --
def weighted(rows, lo, hi, key):
    sel = [r for r in rows if lo < r["Number"] <= hi]
    if not sel:
        return float("nan"), 0
    w = np.array([r["n"] for r in sel])
    v = np.array([r[key] for r in sel])
    return float((w * v).sum() / w.sum()), len(sel)


def readout(run: dict, frac: float, allow_partial: bool) -> dict:
    wdir = wandb_dir_for(run)
    rows, cfg = read_history(wdir, allow_truncated=allow_partial)
    meta = run_meta(wdir, cfg)
    for k in ("tag", "config"):
        if run.get(k) and meta[k] != run[k]:
            raise ValueError(f"{run['id']}: manifest {k}={run[k]!r} but WandB has {meta[k]!r}")
    if run.get("run_dir") and not os.path.isdir(_abs(run["run_dir"])):
        raise ValueError(f"{run['id']}: run_dir {run['run_dir']} does not exist")
    N = meta["episodes"]
    reached = max(r["Number"] for r in rows)
    log_done = None
    if run.get("log"):
        with open(_abs(run["log"]), "rb") as fh:
            fh.seek(max(0, os.path.getsize(_abs(run["log"])) - 20000))
            log_done = b"Training complete" in fh.read()
    complete = reached >= N and log_done is not False
    if not complete and not allow_partial:
        raise RuntimeError(f"{run['id']}: incomplete (reached {reached:.0f}/{N}, "
                           f"'Training complete' in log: {log_done}); use --allow-partial for tests only")
    end = N if complete else reached
    lo = end - frac * end
    S, nrows = weighted(rows, lo, end, "Steps")
    starve, _ = weighted(rows, lo, end, "starve")
    # temporal evolution: weighted S and starvation in 10 equal blocks of what has been logged
    blocks = []
    for b in range(10):
        blo, bhi = end * b / 10, end * (b + 1) / 10
        blocks.append((weighted(rows, blo, bhi, "Steps")[0], weighted(rows, blo, bhi, "starve")[0]))
    return {"id": run["id"], "role": run["role"], "factor": run.get("factor"), "strength": run.get("strength"),
            "note": run.get("note"), "wandb_id": run["wandb_id"], "episodes_cfg": N, "reached": reached,
            "complete": complete, "window": [lo, end], "rows_in_window": nrows, "S": S, "starve": starve,
            "blocks": blocks}


# ---------------------------------------------------------------------------------- pick rule --
def apply_rule(man: dict, res: dict) -> dict:
    th = man["thresholds"]
    base = [r for r in res.values() if r["role"] == "base"]
    if len(base) < 2:
        raise ValueError(f"need >= 2 base runs for a noise estimate, have {len(base)}")
    Sb = float(np.mean([r["S"] for r in base]))
    n = float(np.std([r["S"] for r in base], ddof=1))
    stb = float(np.mean([r["starve"] for r in base]))
    raw = max(th["noticeable_noise_mult"] * n, th["noticeable_floor_frac"] * Sb)
    cap = th["noticeable_cap_frac"] * Sb
    thr = min(raw, cap)
    ref = {"S_base": Sb, "n": n, "starve_base": stb, "threshold": thr, "threshold_uncapped": raw,
           "cap": cap, "cap_binds": th["noticeable_noise_mult"] * n > cap,
           "survivable_S_min": th["survivable_frac"] * Sb,
           "starve_max": stb + th["starvation_rise_max"]}

    for r in res.values():
        if r["role"] == "base":
            continue
        r["pct_base"] = 100 * r["S"] / Sb
        r["nan"] = not math.isfinite(r["S"]) or not math.isfinite(r["starve"])
        r["noticeable"] = (not r["nan"]) and (Sb - r["S"] >= thr)
        r["survivable"] = (not r["nan"]) and r["S"] >= ref["survivable_S_min"] and r["starve"] <= ref["starve_max"]
        r["collapse_like"] = (not r["nan"]) and (r["S"] < th["collapse_frac"] * Sb
                                                  or r["starve"] > th["collapse_starve_abs"]
                                                  or r["starve"] > stb + th["collapse_starve_rise"])

    factors = {}
    for fname, fdef in man["factors"].items():
        rs = [res[x["id"]] for x in man["runs"] if x.get("factor") == fname and x["id"] in res]
        out = {"label": fdef["label"], "rule": fdef["rule"], "runs": [r["id"] for r in rs],
               "pick": None, "pick_noticeable": None, "status": "ok", "flags": []}
        if not rs:
            out["status"] = "no runs"; factors[fname] = out; continue
        Ss = [r["S"] for r in rs]
        if any(b > a for a, b in zip(Ss, Ss[1:])):
            out["flags"].append("survival does not fall steadily with strength (reported; rule applied as written)")
        if any(r["nan"] for r in rs):
            out["flags"].append("NaN read-out in " + ", ".join(r["id"] for r in rs if r["nan"]))
        for r in rs:
            if r["collapse_like"]:
                out["flags"].append(f"{r['id']} ({r['strength']}) is collapse-like by the §2.4 thresholds")
        if not rs[0]["survivable"]:
            out["status"] = "STOP: even the weakest strength is not survivable - report to user"
        elif fdef["rule"] == "strongest_survivable":
            p = [r for r in rs if r["survivable"]][-1]
            out["pick"], out["pick_noticeable"] = p["id"], p["noticeable"]
        elif fdef["rule"] == "weakest_noticeable":
            ok = [r for r in rs if r["noticeable"] and r["survivable"]]
            if ok:
                out["pick"], out["pick_noticeable"] = ok[0]["id"], True
            elif not any(r["noticeable"] for r in rs):
                p = [r for r in rs if r["survivable"]][-1]
                out["pick"], out["pick_noticeable"] = p["id"], False
                out["flags"].append("no measurable survival effect at the tested strengths (strongest survivable picked)")
            else:
                out["status"] = ("UNRESOLVED: some strength is noticeable but none is noticeable and survivable; "
                                 "the doc's edge cases do not cover this - report to user")
        else:
            raise ValueError(f"unknown rule {fdef['rule']!r}")
        if out["pick"] and res[out["pick"]].get("note"):
            out["flags"].append(f"{out['pick']}: {res[out['pick']]['note']}")
        factors[fname] = out

    groups = {}
    for gname, gdef in (man.get("groups") or {}).items():
        members = {f: d for f, d in man["factors"].items() if d.get("group") == gname}
        yes = [f for f in members if factors[f]["pick"] and factors[f]["pick_noticeable"]]
        if len(yes) == 1:
            keep, why = yes[0], "only form with a non-negligible pick"
        elif len(yes) > 1:
            keep = [f for f in yes if members[f]["form"] == gdef["preferred_form"]][0]
            why = f"both forms non-negligible -> preferred form ({gdef['preferred_form']})"
        else:
            keep, why = gdef["fallback"]["factor"], f"neither form non-negligible -> fallback {gdef['fallback']} (flagged)"
        groups[gname] = {"keep_factor": keep, "why": why,
                         "pick": factors[keep]["pick"] if len(yes) else
                         next(r["id"] for r in res.values() if r.get("factor") == gdef["fallback"]["factor"]
                              and r.get("strength") == gdef["fallback"]["strength"])}
    return {"reference": ref, "factors": factors, "groups": groups}


# ----------------------------------------------------------------------------------- report --
def render(man, res, out, partial) -> str:
    ref = out["reference"]
    L = []
    if partial or not all(r["complete"] for r in res.values()):
        L.append("> **PARTIAL DATA - tooling test only; not a pick.** Each S is over the last "
                 f"{int(man['readout_fraction']*100)} % of the episodes reached so far.\n")
    L.append("**Reference (unchanged level 05).**\n")
    L.append("| Run | Episodes read | S (survival steps) | Starvation share |")
    L.append("|---|---|---|---|")
    for r in res.values():
        if r["role"] == "base":
            L.append(f"| {r['id']} | {r['window'][0]:,.0f}-{r['window'][1]:,.0f} | {r['S']:.1f} | {r['starve']:.3f} |")
    L.append("")
    L.append(f"S_base = **{ref['S_base']:.1f}** steps; seed noise n (SD of the base S values) = {ref['n']:.1f}; "
             f"starve_base = {ref['starve_base']:.3f}.  ")
    L.append(f"Noticeable threshold = min(max(2n = {2*ref['n']:.1f}, 5 % = {0.05*ref['S_base']:.1f}), "
             f"cap 15 % = {ref['cap']:.1f}) = **{ref['threshold']:.1f}** steps "
             f"(cap binds: {'**yes - noise-limited**' if ref['cap_binds'] else 'no'}).  ")
    L.append(f"Survivable: S >= {ref['survivable_S_min']:.1f} and starvation share <= {ref['starve_max']:.3f}.\n")
    for fname, f in out["factors"].items():
        L.append(f"**{fname} - {f['label']}** (rule: {f['rule'].replace('_', ' ')})\n")
        L.append("| Run | Strength | S | % of S_base | Starvation share | Noticeable? | Survivable? | Picked |")
        L.append("|---|---|---|---|---|---|---|---|")
        for rid in f["runs"]:
            r = res[rid]
            L.append(f"| {rid} | {r['strength']} | {r['S']:.1f} | {r['pct_base']:.1f} % | {r['starve']:.3f} | "
                     f"{'yes' if r['noticeable'] else 'no'} | {'yes' if r['survivable'] else 'no'} | "
                     f"{'**PICK**' if f['pick'] == rid else ''} |")
        L.append("")
        if f["status"] != "ok":
            L.append(f"- **{f['status']}**")
        for fl in f["flags"]:
            L.append(f"- Flag: {fl}")
        L.append("")
    for g, d in out["groups"].items():
        L.append(f"**{g} form choice:** keep **{d['keep_factor']}** ({d['why']}); strength run {d['pick']}.\n")
    L.append("**Temporal evolution** - weighted S per tenth of the episodes read (first -> last tenth):\n")
    L.append("| Run | " + " | ".join(f"{10*i+10}%" for i in range(10)) + " |")
    L.append("|---|" + "---|" * 10)
    for r in res.values():
        L.append(f"| {r['id']} | " + " | ".join(f"{s:.0f}" for s, _ in r["blocks"]) + " |")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--md-out")
    ap.add_argument("--json-out")
    a = ap.parse_args()
    man = yaml.safe_load(open(_abs(a.manifest)))
    ids = [r["id"] for r in man["runs"]]
    if len(set(ids)) != len(ids) or len({r["wandb_id"] for r in man["runs"]}) != len(ids):
        raise ValueError("duplicate run id or wandb_id in manifest")
    res = {r["id"]: readout(r, man["readout_fraction"], a.allow_partial) for r in man["runs"]}
    out = apply_rule(man, res)
    md = render(man, res, out, a.allow_partial)
    print(md)
    if a.md_out:
        open(a.md_out, "w").write(md)
    if a.json_out:
        json.dump({"runs": res, **out}, open(a.json_out, "w"), indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
