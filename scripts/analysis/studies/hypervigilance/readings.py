#!/usr/bin/env python3
"""readings.py - every pre-registered hypervigilance reading, per run, over a population manifest.

Plan: docs/develop/active/behavior/HYPERVIGILANCE_ANALYSIS_TOOLING.md (Revision 2).
Study: docs/experiments/active/hypervigilance/SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md, section 5.

Run-agnostic. It reads a population manifest written by `make_population.py` (one entry per cell,
with a `status` column; only `completed` cells are read), runs the four existing store sweeps on
each cell by subprocess, and assembles one `readings.json` per cell with P1, P2, P2d, survival and
S1-S6, every NaN carrying a reason, and data-accounting rows emitted by code.

    --stage check     saved config + first episodes shard only (seconds): seed, odour layout vs
                      world, non-emitting channels exactly 0, per-class empirical odour means
    --stage sweep     hiding_drivers.py, collect_arm_data.py --manifest, rabbit_avoidance.py,
                      aimed_response.py -> <out-root>/<label>/ (one cell at a time, serially)
    --stage assemble  <out-root>/<label>/readings.json, then the cross-run sextile assertion
    --stage all       the three in order

GUARDS (each refuses rather than warns):
  * --out-root must be an ABSOLUTE path under results/analysis/hypervigilance/; the child env sets
    LADDER_OUT_ROOT explicitly, never the live sensor-ladder root (plan R7);
  * both golden stamps (sweep tier + assembly tier, plan Revision 2 N2) must exist and match the
    current sources, except for the `a01` population the gate itself reads;
  * an hv-study population (worlds hv1ch / hv1chm / hv2ch) is not swept or assembled until the
    cmp10m seed-noise yardstick has been frozen (study section 5.3: frozen before any hv run is read);
  * outputs already on disk are refused unless --reuse-cache, and then only if their recorded run,
    stores and sweep-source hashes equal the requested ones (the stale-cache trap).

Run from anywhere with the project interpreter; paths in the manifest are repo-relative.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
A_DIR = os.path.join(ROOT, "scripts", "analysis")
sys.path.insert(0, os.path.join(A_DIR, "core"))
sys.path.insert(0, os.path.join(A_DIR, "ladder"))
sys.path.insert(0, A_DIR)

import env as ENV                                    # noqa: E402
from _ladder import proximity_effect                 # noqa: E402
from hiding_drivers import quasi_binomial_fit        # noqa: E402

EARLY = 25                                  # first 25 chosen steps (study S1; collect_arm_data.EARLY)
INJ_Q_EDGES = [25.0, 50.0, 75.0]            # start-injury quarters (_ladder.INJ_EDGES)
MIN_WLS_EPISODES = 30
TERM_STARVED, TERM_KILLED = 2, 4            # core.py termination codes (_ladder.TERM_NAMES)
A01_FIXED_BINS = (-0.2, 0.6)                # a01 curves.py: bottom < -0.2, top >= 0.6
HV_ROOT = os.path.join(ROOT, "results", "analysis", "hypervigilance")
LIVE_LADDER_ROOT = os.path.join(ROOT, "results", "analysis", "ladder")
YARDSTICK = os.path.join(HV_ROOT, "cmp10m", "yardstick.json")
SWEEP_STAMP = os.path.join(HV_ROOT, "_golden_sweep_pass.json")
ASSEMBLY_STAMP = os.path.join(HV_ROOT, "_golden_assembly_pass.json")

SWEEP_SOURCES = ["scripts/analysis/core/env.py", "scripts/analysis/core/scan.py",
                 "scripts/analysis/core/store.py", "scripts/analysis/hiding_drivers.py",
                 "scripts/analysis/studies/sensor_ladder/collect_arm_data.py",
                 "scripts/analysis/ladder/_ladder.py", "scripts/analysis/rabbit_avoidance.py",
                 "scripts/analysis/aimed_response.py"]
ASSEMBLY_SOURCES = ["scripts/analysis/studies/hypervigilance/readings.py",
                    "scripts/analysis/studies/hypervigilance/make_population.py"]

WORLD_LAYOUT = {"hv2ch": "difference", "basicq2": "difference", "cmp10m": "difference",
                "a01": "difference", "l05body": "difference", "hv1ch": "single", "hv1chm": "sum"}
HV_WORLDS = ("hv1ch", "hv1chm", "hv2ch")
HV_TAG_RE = re.compile(
    r"^\d{8}-\d{6}_(?P<tag>rppo_(?P<world>hv1ch|hv1chm|hv2ch)_(?P<agent>t1none|t16quad)_s(?P<seed>\d+))"
    r"(?P<relaunch>_r\d+)?$")
SEED_RE = re.compile(r"_s(?P<seed>\d+)(_r\d+)?$")


# --------------------------------------------------------------------------- provenance ----
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_hashes(rel_paths) -> dict:
    return {p: sha256(os.path.join(ROOT, p)) for p in rel_paths}


def combined_hash(hashes: dict) -> str:
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def git_state() -> dict:
    def run(*a):
        return subprocess.run(["git", "--no-optional-locks", *a], cwd=ROOT, capture_output=True, text=True,
                              timeout=120).stdout.strip()
    try:
        head = run("rev-parse", "HEAD")
        dirty = bool(run("status", "--porcelain", "--", "scripts/analysis"))
    except Exception as e:                                         # noqa: BLE001
        head, dirty = f"unavailable ({e!r})", None
    return {"head": head, "scripts_analysis_dirty": dirty}


def require_stamps(root: str = HV_ROOT) -> dict:
    """Both golden tiers must have passed on exactly the current sources (plan Revision 2, N2)."""
    sweep_p = os.path.join(root, "_golden_sweep_pass.json")
    asm_p = os.path.join(root, "_golden_assembly_pass.json")
    for p in (sweep_p, asm_p):
        if not os.path.exists(p):
            raise SystemExit(f"golden stamp missing: {p}\n  run golden_check.py (--tier sweep, then "
                             f"--tier assembly) before reading any population")
    sw, asm = json.load(open(sweep_p)), json.load(open(asm_p))
    stale = [p for p, h in source_hashes(SWEEP_SOURCES).items() if sw["sources"].get(p) != h]
    stale += [p for p, h in source_hashes(ASSEMBLY_SOURCES).items() if asm["sources"].get(p) != h]
    if asm.get("sweep_stamp_sha256") != sha256(sweep_p):
        stale.append("_golden_sweep_pass.json (the assembly tier passed against another sweep stamp)")
    if stale:
        raise SystemExit("these analysis sources changed since the golden check passed -- re-run "
                         "golden_check.py:\n  " + "\n  ".join(stale))
    return {"sweep": sw["combined"], "assembly": asm["combined"]}


# --------------------------------------------------------------------------------- guards ----
def guard_out_root(path: str, parent: str = HV_ROOT) -> str:
    """The output root must be an absolute path strictly under `parent` (plan R7)."""
    if not os.path.isabs(path):
        raise SystemExit(f"--out-root must be an absolute path, got {path!r}")
    out = os.path.realpath(path)
    par = os.path.realpath(parent)
    if not out.startswith(par + os.sep):
        raise SystemExit(f"--out-root {out} is not under {par}")
    live = os.path.realpath(LIVE_LADDER_ROOT)
    if out == live or out.startswith(live + os.sep):
        raise SystemExit(f"--out-root {out} is the live sensor-ladder root")
    return out


def child_env(ladder_out: str, out_root: str) -> dict:
    """os.environ with LADDER_OUT_ROOT set explicitly and asserted safe."""
    lo = os.path.realpath(ladder_out)
    if not os.path.isabs(ladder_out) or not lo.startswith(os.path.realpath(out_root) + os.sep):
        raise SystemExit(f"LADDER_OUT_ROOT {ladder_out!r} is not an absolute path under {out_root}")
    if lo == os.path.realpath(LIVE_LADDER_ROOT):
        raise SystemExit("LADDER_OUT_ROOT resolves to the live sensor-ladder root")
    env = dict(os.environ)
    env["LADDER_OUT_ROOT"] = lo
    return env


def require_yardstick_for(cells) -> None:
    if any(c["world"] in HV_WORLDS for c in cells) and not os.path.exists(YARDSTICK):
        raise SystemExit(f"{YARDSTICK} does not exist: the cmp10m seed-noise yardstick must be frozen "
                         f"before any hv-study run is read (study section 5.3). Run verdict.py "
                         f"--yardstick first.")


# ------------------------------------------------------------------------------- manifest ----
def cell_key(c) -> tuple:
    return (c["world"], c["agent"], c["seed"], c.get("level"), c.get("wave"))


def validate_cell(c) -> None:
    """Tag cross-check: the run directory's own name must agree with the manifest entry."""
    base = os.path.basename(c["run"].rstrip("/"))
    m = HV_TAG_RE.match(base)
    if m:
        got = (m["world"], m["agent"], int(m["seed"]))
        if got != (c["world"], c["agent"], int(c["seed"])):
            raise SystemExit(f"{c['label']}: run dir {base} says world/agent/seed {got}, the manifest "
                             f"says {(c['world'], c['agent'], c['seed'])}")
    elif c["world"] in ("hv1ch", "hv1chm"):
        raise SystemExit(f"{c['label']}: world {c['world']} but run dir {base} is not an hv tag")
    s = SEED_RE.search(base)
    if s and int(s["seed"]) != int(c["seed"]):
        raise SystemExit(f"{c['label']}: run dir {base} carries seed {s['seed']}, manifest {c['seed']}")


def load_population(path: str) -> dict:
    """Read a population manifest; return it with only `completed` cells in `cells`."""
    M = json.load(open(path))
    done = [c for c in M["cells"] if c["status"] == "completed"]
    seen = {}
    for c in done:
        k = cell_key(c)
        if k in seen:
            raise SystemExit(f"two completed cells for {k}: {seen[k]} and {c['label']} -- the manifest "
                             f"must mark one of them failed")
        seen[k] = c["label"]
        validate_cell(c)
        if not os.path.exists(os.path.join(ROOT, c["run"], "models", "config.yaml")):
            raise SystemExit(f"{c['label']}: {c['run']}/models/config.yaml does not exist")
        if not c.get("stores"):
            raise SystemExit(f"{c['label']}: completed but no store")
        for st in c["stores"]:
            if not os.path.isdir(os.path.join(ROOT, st)):
                raise SystemExit(f"{c['label']}: store {st} does not exist")
    labels = [c["label"] for c in done]
    if len(set(labels)) != len(labels):
        raise SystemExit("duplicate labels among completed cells")
    return {**M, "cells": done, "n_not_completed": len(M["cells"]) - len(done)}


def load_cfg(c) -> dict:
    import yaml
    return yaml.safe_load(open(os.path.join(ROOT, c["run"], "models", "config.yaml")))


# ---------------------------------------------------------------------------------- check ----
def check_cell(c) -> dict:
    """Ground-truth checks from the saved config and the store's first episodes shard."""
    import glob
    import pyarrow.parquet as pq
    cfg = load_cfg(c)
    if int(cfg["seed"]) != int(c["seed"]):
        raise SystemExit(f"{c['label']}: saved config seed {cfg['seed']} != manifest seed {c['seed']}")
    spec = ENV.scent_spec(cfg)
    want = WORLD_LAYOUT[c["world"]]
    if spec.layout != want:
        raise SystemExit(f"{c['label']}: world {c['world']} expects layout {want}, config gives "
                         f"{spec.layout}")
    lay = ENV.slot_layout(cfg)
    na = lay["n_animal"]
    f0 = sorted(glob.glob(os.path.join(ROOT, c["stores"][0], "episodes_*.parquet")))
    if not f0:
        raise SystemExit(f"{c['label']}: no episodes shard in {c['stores'][0]}")
    tb = pq.read_table(f0[0], columns=["animal_active", "animal_property_sampled"])
    act = ENV.listcol(tb.column("animal_active"), na).astype(bool)
    col = tb.column("animal_property_sampled")
    flat = np.concatenate([ch.flatten().to_numpy(zero_copy_only=False) for ch in col.chunks])
    prop = flat.reshape(len(act), na, -1).astype(np.float64)
    other = [ch for ch in range(prop.shape[2]) if ch not in spec.channels]
    live = prop[act]                                               # (active animals, channels)
    nonzero = int(np.count_nonzero(live[:, other])) if other else 0
    if nonzero:
        raise SystemExit(f"{c['label']}: {nonzero} non-zero values on non-emitting channels {other} "
                         f"for active animals -- the store is not from the world the config says")
    means = {}
    for name, slots in (("predator", lay["pred"]), ("rabbit", lay["neutral"])):
        m = act[:, slots]
        v = prop[:, slots][m]
        means[name] = {"n": int(m.sum()), "channel_means": v[:, list(spec.channels)].mean(0).tolist()
                       if len(v) else None,
                       "total_mean": float(spec.intensity(v).mean()) if len(v) else None}
    return {"label": c["label"], "layout": spec.layout, "channels": list(spec.channels),
            "non_emitting_channels_zero": True, "shard": os.path.relpath(f0[0], ROOT),
            "empirical_means": means}


# ---------------------------------------------------------------------------------- sweep ----
def cell_dir(out_root, c):
    return os.path.join(out_root, c["label"])


def expected_outputs(out_root, c) -> dict:
    d = cell_dir(out_root, c)
    return {"glm": os.path.join(d, "glm", "aggregate.npz"),
            "ladder": os.path.join(d, "ladderstyle", f"{c['label']}.json"),
            "rabbit": os.path.join(d, "rabbit_avoidance.json"),
            "aimed": os.path.join(d, "aimed_response.json")}


def validate_cache(out_root, c) -> list[str]:
    """Which existing outputs belong to exactly this cell and this code; raise on any mismatch."""
    d, exp = cell_dir(out_root, c), expected_outputs(out_root, c)
    prov_p = os.path.join(d, "_sweep_provenance.json")
    present = [k for k, p in exp.items() if os.path.exists(p)]
    if not present:
        return []
    if not os.path.exists(prov_p):
        raise SystemExit(f"{c['label']}: outputs exist without _sweep_provenance.json -- stale cache")
    prov = json.load(open(prov_p))
    if prov["run"] != c["run"] or prov["stores"] != c["stores"]:
        raise SystemExit(f"{c['label']}: cached outputs were built from {prov['run']} / {prov['stores']}")
    cur = source_hashes(SWEEP_SOURCES)
    for k in present:
        if prov.get("sweeps", {}).get(k, {}).get("sources") != cur:
            raise SystemExit(f"{c['label']}: cached {k} output was built by other sweep code")
    for k in ("ladder", "rabbit", "aimed"):
        if k in present:
            j = json.load(open(exp[k]))
            if j["run"] != c["run"] or j["stores"] != c["stores"]:
                raise SystemExit(f"{c['label']}: {exp[k]} records run/stores {j['run']}/{j['stores']}")
    if "glm" in present and "ladder" in present:
        a = np.load(exp["glm"])["seed"]
        b = np.load(exp["ladder"].replace(".json", "_episodes.npz"))["seed"]
        if not np.array_equal(a, b):
            raise SystemExit(f"{c['label']}: aggregate.npz and _episodes.npz hold different episodes")
    return present


def sweep_cell(c, out_root: str, reuse: bool) -> dict:
    d = cell_dir(out_root, c)
    os.makedirs(d, exist_ok=True)
    present = validate_cache(out_root, c)
    if present and not reuse:
        raise SystemExit(f"{c['label']}: outputs already exist ({present}); pass --reuse-cache to keep "
                         f"them (they are validated) or remove {d}")
    prov_p = os.path.join(d, "_sweep_provenance.json")
    prov = json.load(open(prov_p)) if os.path.exists(prov_p) else {
        "run": c["run"], "stores": c["stores"], "checkpoint": c.get("checkpoint"),
        "store_root": c.get("store_root"), "sweeps": {}}
    roots = c["store_root"]
    ck = ["--checkpoint", str(c["checkpoint"])] if c.get("checkpoint") is not None else []
    py = sys.executable
    lad = os.path.join(d, "ladderstyle")
    cellman = os.path.join(d, "_cell_manifest.json")
    json.dump({c["label"]: {"run": c["run"], "stores": c["stores"]}}, open(cellman, "w"), indent=1)
    jobs = {
        "glm": [py, os.path.join(A_DIR, "hiding_drivers.py"), "--run", c["run"], "--store-root",
                *roots, *ck, "--out", os.path.join(d, "glm"),
                "--cache", os.path.join(d, "glm", "aggregate.npz")],
        "ladder": [py, os.path.join(A_DIR, "studies", "sensor_ladder", "collect_arm_data.py"),
                   "--manifest", cellman],
        "rabbit": [py, os.path.join(A_DIR, "rabbit_avoidance.py"), "--run", c["run"],
                   "--store-root", *roots, *ck, "--out", os.path.join(d, "rabbit_avoidance.json")],
        "aimed": [py, os.path.join(A_DIR, "aimed_response.py"), "--run", c["run"], "--store-root",
                  *roots, *ck, "--out", os.path.join(d, "aimed_response.json")],
    }
    env = child_env(lad, out_root)
    for k, cmd in jobs.items():
        if k in present:
            print(f"  {c['label']}: {k} cached and validated", flush=True)
            continue
        t0 = time.time()
        log = open(os.path.join(d, f"_{k}.log"), "w")
        subprocess.run(cmd, cwd=ROOT, env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
        dt = time.time() - t0
        prov["sweeps"][k] = {"seconds": round(dt, 1), "sources": source_hashes(SWEEP_SOURCES),
                             "finished": _dt.datetime.now().isoformat(timespec="seconds"),
                             **git_state()}
        json.dump(prov, open(prov_p, "w"), indent=1)
        print(f"  {c['label']}: {k} done in {dt:.0f}s", flush=True)
    validate_cache(out_root, c)
    # the stores each sweep resolved must be exactly the manifest's
    for k in ("ladder", "rabbit", "aimed"):
        j = json.load(open(expected_outputs(out_root, c)[k]))
        assert j["stores"] == c["stores"], (k, j["stores"], c["stores"])
    return prov


# ------------------------------------------------------------------------------- readings ----
def val(x, reason: str | None = None) -> dict:
    """A scalar reading; a NaN is never silent (study section 5.7)."""
    x = None if x is None else float(x)
    if x is None or not np.isfinite(x):
        return {"value": None, "reason": reason or "not computable"}
    return {"value": x, "reason": None}


def proximity(g: dict, name: str, inj=None) -> float:
    return proximity_effect(g[f"{name}_bush"], g[f"{name}_tot"], inj)


def hiding_shift(g: dict, name: str) -> float:
    """a4_hypervigilance.hiding_shift, re-stated (that module draws a figure at import)."""
    return proximity(g, name, (3,)) - proximity(g, name, (0,))


def wls(x, y, w, z=None) -> tuple:
    """Weighted least-squares slope of y on x (optionally with covariate z); (slope, se, n)."""
    cols = [np.ones_like(x), x] + ([z] if z is not None else [])
    X = np.column_stack(cols)
    n, p = X.shape
    if n < MIN_WLS_EPISODES or np.sum(w) <= 0:
        return np.nan, np.nan, n
    XtW = X.T * w
    XtWX = XtW @ X
    beta = np.linalg.solve(XtWX, XtW @ y)
    r = y - X @ beta
    s2 = float(np.sum(w * r * r) / max(n - p, 1))          # weights as relative precisions
    cov = s2 * np.linalg.inv(XtWX)
    return float(beta[1]), float(np.sqrt(cov[1, 1])), n


def s1_quarter_contrast(share_pp, llr, w, inj0, z=None) -> dict:
    """Study S1 (i), the primary estimator: WLS slope (pp per nat) in the top and bottom
    start-injury quarters; contrast = top - bottom."""
    q = np.digitize(inj0, INJ_Q_EDGES)
    out = {}
    for name, qi in (("q0", 0), ("q3", 3)):
        m = (q == qi) & (w > 0) & np.isfinite(llr) & np.isfinite(share_pp)
        if z is not None:
            m &= np.isfinite(z)
        b, se, n = wls(llr[m], share_pp[m], w[m], None if z is None else z[m])
        out[name] = {"slope_pp_per_nat": val(b, f"fewer than {MIN_WLS_EPISODES} episodes"),
                     "se": se if np.isfinite(se) else None, "episodes": int(n)}
    b0, b3 = out["q0"]["slope_pp_per_nat"]["value"], out["q3"]["slope_pp_per_nat"]["value"]
    if b0 is None or b3 is None:
        out["contrast"] = val(np.nan, "a start-injury quarter has too few episodes")
        out["contrast_se"] = None
    else:
        out["contrast"] = val(b3 - b0)
        out["contrast_se"] = float(np.hypot(out["q0"]["se"], out["q3"]["se"]))
    return out


def s1_glm(Y, Lst, llr, D, keep, z=None) -> dict:
    """Study S1 (ii), descriptive: quasi-binomial GLM with scent x start-injury product term."""
    import pandas as pd
    X = {"llr": llr, "start_injury": D["inj0"], "llr_x_injury": llr * D["inj0"],
         "start_nutrition": D["nut0"], "n_bushes": D["n_bush"], "n_rocks": D["n_rock"],
         "n_food": D["n_food"], "n_ambush_predators": D["n_ambush"],
         "spawn_dist_to_bush": D["d_bush0"]}
    if z is not None:
        X["rab_olf_ch2"] = z
    keep = keep & (Lst > 0)
    if keep.sum() < 100:
        return {"product_pp_per_nat_per_100_injury": val(np.nan, "fewer than 100 episodes")}
    f = quasi_binomial_fit(pd.DataFrame(X), keep, "S1 GLM", Y, Lst)
    r = f[f.term == "llr_x_injury"].iloc[0]
    s = r.dpp_per_unit / r.coef if r.coef != 0 else np.nan
    return {"n": int(r.n), "coef": float(r.coef), "p": float(r.p),
            "product_pp_per_nat_per_100_injury": val(r.dpp_per_unit * 100),
            "product_se": float(r.se * s * 100), "overdispersion": float(r.overdispersion)}


def extreme_rows(stat, keep, D, cuts, llr_fn) -> dict:
    """Bottom (stat < cuts[0]) vs top (stat >= cuts[1]) rows of the a01 extreme-row table."""
    rows = {}
    for name, m in (("bottom", keep & (stat < cuts[0])), ("top", keep & (stat >= cuts[1]))):
        ns = D["n_steps"][m]
        if m.sum() == 0:
            rows[name] = {"episodes": 0}
            continue
        rows[name] = {"episodes": int(m.sum()),
                      "hides_pct": float(100 * D["bush_steps"][m].sum() / ns.sum()),
                      "food_per_step": float(D["n_ate"][m].sum() / ns.sum()),
                      "starved_pct": float(100 * np.mean(D["term"][m] == TERM_STARVED)),
                      "killed_pct": float(100 * np.mean(D["term"][m] == TERM_KILLED)),
                      "survived_steps": float(ns.mean()),
                      "mean_evidence_nats": float(np.mean(llr_fn(stat[m])))}
    return rows


def s2_extremes(D, spec) -> dict:
    """Study S2 extreme rows: within-world sextiles (primary) and a01 fixed bins (control only)."""
    out = {}
    for who, stat_key, n_key in (("rabbit", "rab_predatorness", "n_rab"),
                                 ("predator", "pred_predatorness", "n_pred")):
        stat = D[stat_key]
        keep = (D[n_key] == 1) & np.isfinite(stat)
        q = np.quantile(stat[keep], [1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6])
        o = {"episodes": int(keep.sum()), "sextile_cuts": q.tolist(),
             "sextiles": extreme_rows(stat, keep, D, (q[0], q[4]), spec.llr)}
        if spec.layout == "difference":
            o["a01_fixed_bins"] = {"cuts": list(A01_FIXED_BINS),
                                   **extreme_rows(stat, keep, D, A01_FIXED_BINS, spec.llr)}
        out[who] = o
    return out


def s2_univariate(uni_csv: str, multi_csv: str, spec) -> dict:
    import pandas as pd
    u = pd.read_csv(uni_csv)
    m = pd.read_csv(multi_csv)
    out = {}
    for term in ("rab_smell_predatorness", "pred_smell_predatorness"):
        r = u[u.term == term]
        if len(r) != 1:
            out[term] = {"reason": "term absent from univariate.csv"}
            continue
        r = r.iloc[0]
        out[term] = {"n": int(r.n), "dpp_per_unit": float(r.dpp_per_unit),
                     "dpp_per_nat": val(r.dpp_per_unit / spec.llr_scale,
                                        "deterministic smell: k undefined"),
                     "dpp_per_sd": float(r.dpp_per_sd), "p": float(r.p)}
    m3 = m[m.model.str.startswith("M3")]
    out["M3"] = {t: {"dpp_per_unit": float(r.dpp_per_unit), "dpp_per_sd": float(r.dpp_per_sd),
                     "p": float(r.p), "n": int(r.n)}
                 for t, r in m3.set_index("term").iterrows()
                 if t in ("rab_smell_predatorness", "pred_smell_predatorness",
                          "rab_olf_intensity", "pred_olf_intensity")}
    return out


def s2_matched(D, spec) -> dict:
    """Control only: rabbit channel 1 with channel 2 as covariate, on exactly-one-rabbit episodes."""
    import pandas as pd
    keep = (D["n_rab"] == 1)
    f = quasi_binomial_fit(pd.DataFrame({"rab_olf_ch1": D["rab_olf_ch1"],
                                         "rab_olf_ch2": D["rab_olf_ch2"]}),
                           keep, "S2 matched", D["bush_steps"], D["n_steps"])
    r = f[f.term == "rab_olf_ch1"].iloc[0]
    _, k1 = spec.channel_scale(spec.channels[0])
    return {"n": int(r.n), "ch1_dpp_per_unit": float(r.dpp_per_unit),
            "ch1_dpp_per_nat": float(r.dpp_per_unit / k1), "ch1_dpp_per_sd": float(r.dpp_per_sd),
            "p": float(r.p), "k_channel1": k1}


def s3_summary(aimed: dict) -> dict:
    out = {"primary": aimed["primary"], "group_episodes": aimed["group_episodes"],
           "thresholds": aimed["thresholds"]}
    for key in ("prev_row", "same_row"):
        r = aimed[key]
        out[key] = {"difference_pp": dict(zip(aimed["states"], r["difference_pp"])),
                    "bush_share_pct": {g: dict(zip(aimed["states"], row))
                                       for g, row in zip(aimed["groups"], r["bush_share_pct"])},
                    "time_share_pct": {g: dict(zip(aimed["states"], row))
                                       for g, row in zip(aimed["groups"], r["time_share_pct"])},
                    "steps": r["steps"]}
    return out


def join_episodes(ep: dict, agg: dict) -> None:
    if not np.array_equal(ep["seed"], agg["seed"]):
        raise SystemExit("the ladder _episodes.npz and hiding_drivers aggregate.npz hold different "
                         "episode seeds -- they are not the same population")


def s1_block(ep, D, spec, llr, keep, z=None, flag=None) -> dict:
    share = 100 * ep["bush_early"] / np.maximum(ep["steps_early"], 1)
    w = ep["steps_early"].astype(np.float64)
    blk = {"statistic_equals_intensity": flag,
           "episodes": int(keep.sum()),
           "primary": s1_quarter_contrast(share[keep], llr[keep], w[keep], ep["inj0"][keep],
                                          None if z is None else z[keep]),
           "glm": s1_glm(ep["bush_early"], ep["steps_early"], llr, D, keep, z)}
    return blk


def s1_all(ep, D, spec) -> dict:
    join_episodes(ep, D)
    if ep["steps_early"].max() > EARLY:
        raise SystemExit(f"steps_early exceeds EARLY={EARLY}: the ladder sweep's window changed")
    nopred = (ep["n_pred"] == 0) & (ep["n_rab"] == 1)
    onepred = (ep["n_pred"] == 1) & (ep["n_rab"] == 1)
    llr = spec.llr(D["rab_predatorness"])
    out = {"window_steps": EARLY,
           "plain": {**s1_block(ep, D, spec, llr, nopred, flag=spec.statistic_equals_intensity),
                     "sensitivity_one_predator": s1_block(ep, D, spec, llr, onepred,
                                                          flag=spec.statistic_equals_intensity)}}
    if spec.layout == "difference":
        mid1, k1 = spec.channel_scale(spec.channels[0])
        llr1 = k1 * (D["rab_olf_ch1"] - mid1)
        z = D["rab_olf_ch2"]
        out["matched_control"] = {
            **s1_block(ep, D, spec, llr1, nopred, z=z, flag=True),
            "scale": {"channel": spec.channels[0], "midpoint": mid1, "nats_per_unit": k1},
            "sensitivity_one_predator": s1_block(ep, D, spec, llr1, onepred, z=z, flag=True)}
        out["tested"] = "matched_control"
    else:
        out["tested"] = "plain"
    return out


def assemble_cell(c, out_root: str) -> dict:
    d = cell_dir(out_root, c)
    exp = expected_outputs(out_root, c)
    for k, p in exp.items():
        if not os.path.exists(p):
            raise SystemExit(f"{c['label']}: {p} missing -- run --stage sweep first")
    validate_cache(out_root, c)
    cfg = load_cfg(c)
    spec = ENV.scent_spec(cfg)
    lad = json.load(open(exp["ladder"]))
    sens = json.load(open(exp["ladder"].replace(".json", "_sensitivity.json")))
    rab = json.load(open(exp["rabbit"]))
    aimed = json.load(open(exp["aimed"]))
    ep = dict(np.load(exp["ladder"].replace(".json", "_episodes.npz")))
    D = dict(np.load(exp["glm"], allow_pickle=True))
    g, gs = lad["grids"], sens["grids"]
    low = "bin below 1000 steps"
    P1 = proximity(g, "rd")
    S4 = proximity(g, "pd")
    killed = lad["term_pct"].get("killed by predator", 0.0)
    R = {
        "label": c["label"], "run": c["run"], "stores": c["stores"],
        "checkpoint": c.get("checkpoint"), "world": c["world"], "agent": c["agent"],
        "seed": c["seed"], "level": c.get("level"), "wave": c.get("wave"),
        "scent": {**spec.as_dict()},
        "survival": {"mean_steps": val(lad["mean_survival"]), "term_pct": lad["term_pct"]},
        "P1": val(P1, low), "P2": val(hiding_shift(g, "rd"), low),
        "P2d": val(rab["start"]["near_share_shift"], "injury quarter below 5000 steps"),
        "S1": s1_all(ep, D, spec),
        "S2": {"univariate": s2_univariate(os.path.join(d, "glm", "univariate.csv"),
                                           os.path.join(d, "glm", "multivariate.csv"), spec),
               "extremes": s2_extremes(D, spec),
               **({"matched_control": s2_matched(D, spec)} if spec.layout == "difference" else {})},
        "S3": s3_summary(aimed),
        "S4": {"predator_proximity_effect": val(S4, low), "killed_by_predator_pct": val(killed),
               "confusion_index": val(P1 / S4 if np.isfinite(S4) and S4 != 0 else np.nan,
                                      "predator proximity effect zero or not computable")},
        "S5": {"hiding_shift_current": val(hiding_shift(g, "rdc"), low),
               "distance_shift_current": val(rab["current"]["near_share_shift"],
                                             "injury quarter below 5000 steps")},
        "S6": {"rabbit_on_cell_steps": gs["rab_on_cell"], "rabbit_episode_steps": gs["rab_steps"],
               "rabbit_on_cell_share_pct": val(100 * np.sum(gs["rab_on_cell"]) /
                                               max(np.sum(gs["rab_steps"]), 1)),
               "P1_without_distance0": val(proximity(gs, "rd_no0"), low),
               "P2_without_distance0": val(hiding_shift(gs, "rd_no0"), low),
               "P1_predator_free": val(proximity(gs, "rdpf"), low),
               "P2_predator_free": val(hiding_shift(gs, "rdpf"), low),
               "P2_current_predator_free": val(hiding_shift(gs, "rdcpf"), low)},
    }
    n = int(lad["n_episodes"])
    has_r = int(np.sum(ep["n_rab"] > 0))
    acc = [
        {"what": "episodes in the store", "used": n, "total": n, "pct": 100.0,
         "reason": "final-checkpoint 1M store" if c.get("checkpoint") else "store"},
        {"what": "P1/P2/S5/S6: episodes with >= 1 rabbit", "used": has_r, "total": n,
         "pct": 100 * has_r / n, "reason": "the rabbit proximity grids need a rabbit"},
        {"what": "S1: episodes with no predator and exactly one rabbit",
         "used": R["S1"]["plain"]["episodes"], "total": n,
         "pct": 100 * R["S1"]["plain"]["episodes"] / n,
         "reason": "any hiding driven by that rabbit's scent is a pure false alarm"},
        {"what": "S1 sensitivity: one predator and one rabbit",
         "used": R["S1"]["plain"]["sensitivity_one_predator"]["episodes"], "total": n,
         "pct": 100 * R["S1"]["plain"]["sensitivity_one_predator"]["episodes"] / n,
         "reason": "sensitivity reading"},
        {"what": "S2 rabbit table: exactly one rabbit",
         "used": R["S2"]["extremes"]["rabbit"]["episodes"], "total": n,
         "pct": 100 * R["S2"]["extremes"]["rabbit"]["episodes"] / n,
         "reason": "the scent of the only rabbit is unambiguous"},
        {"what": "S2 predator table: exactly one predator",
         "used": R["S2"]["extremes"]["predator"]["episodes"], "total": n,
         "pct": 100 * R["S2"]["extremes"]["predator"]["episodes"] / n,
         "reason": "the scent of the only predator is unambiguous"},
        *[{**a, "what": "S3: " + a["what"]} for a in aimed["accounting"]],
        {"what": "P2d: predator-free early steps in rabbit episodes (start quarters)",
         "used": int(np.sum(rab["start"]["n"])), "total": None, "pct": None,
         "reason": "first 25 steps, no predator within 2 squares, rabbit present"},
    ]
    R["accounting"] = acc
    R["code"] = {**git_state(), "sources": source_hashes(SWEEP_SOURCES + ASSEMBLY_SOURCES)}
    R["assembled"] = _dt.datetime.now().isoformat(timespec="seconds")
    return R


def sextile_key(r) -> tuple:
    return (r["world"], r.get("level"), r.get("wave"))


def assert_sextiles(readings: list[dict]) -> dict:
    """Study S2: cut points are identical for every run of a world -- asserted, not assumed."""
    ref = {}
    for r in readings:
        k = sextile_key(r)
        cuts = {w: r["S2"]["extremes"][w]["sextile_cuts"] for w in ("rabbit", "predator")}
        if k not in ref:
            ref[k] = (r["label"], cuts)
        elif ref[k][1] != cuts:
            raise SystemExit(f"sextile cut points differ between {ref[k][0]} and {r['label']} in "
                             f"world {k}: {ref[k][1]} vs {cuts} -- refusing the population")
    return {str(k): v[1] for k, v in ref.items()}


def dump(obj, path):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1, default=float)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--labels", nargs="*", default=None)
    ap.add_argument("--stage", choices=["check", "sweep", "assemble", "all"], required=True)
    ap.add_argument("--reuse-cache", action="store_true")
    ap.add_argument("--out-root", required=True)
    a = ap.parse_args()
    out_root = guard_out_root(a.out_root)
    M = load_population(a.manifest)
    cells = M["cells"]
    if a.labels:
        miss = set(a.labels) - {c["label"] for c in cells}
        if miss:
            raise SystemExit(f"not completed cells of this manifest: {sorted(miss)}")
        cells = [c for c in cells if c["label"] in a.labels]
    if M["population"] != "a01":
        require_stamps()
    if a.stage in ("sweep", "assemble", "all"):
        require_yardstick_for(cells)
    os.makedirs(out_root, exist_ok=True)
    print(f"population {M['population']}: {len(cells)} completed cell(s) selected "
          f"({M['n_not_completed']} not completed in the manifest)")
    if a.stage in ("check", "sweep", "all"):
        res = [check_cell(c) for c in cells]
        for r in res:
            print(f"  check {r['label']}: layout {r['layout']} channels {r['channels']} means "
                  f"{ {k: v['total_mean'] for k, v in r['empirical_means'].items()} }")
        if a.stage == "check":
            dump(res, os.path.join(out_root, "_check.json" if not a.labels else
                                   f"_check_{'_'.join(a.labels)[:80]}.json"))
            return
    if a.stage in ("sweep", "all"):
        for c in cells:
            t0 = time.time()
            sweep_cell(c, out_root, a.reuse_cache)
            print(f"{c['label']}: swept in {time.time() - t0:.0f}s", flush=True)
    if a.stage in ("assemble", "all"):
        new = {c["label"]: assemble_cell(c, out_root) for c in cells}
        others = []
        for c in M["cells"]:
            p = os.path.join(cell_dir(out_root, c), "readings.json")
            if c["label"] not in new and os.path.exists(p):
                others.append(json.load(open(p)))
        cuts = assert_sextiles(list(new.values()) + others)
        for lab, r in new.items():
            dump(r, os.path.join(cell_dir(out_root, {"label": lab}), "readings.json"))
            print(f"{lab}: P1 {r['P1']['value']}  P2 {r['P2']['value']}  P2d {r['P2d']['value']}  "
                  f"survival {r['survival']['mean_steps']['value']:.1f}")
        dump({"population": M["population"], "manifest": os.path.relpath(a.manifest, ROOT),
              "manifest_sha256": sha256(a.manifest),
              "cells_with_readings": sorted(set(new) | {o["label"] for o in others}),
              "sextile_cuts": cuts, "status": "ok",
              "written": _dt.datetime.now().isoformat(timespec="seconds")},
             os.path.join(out_root, "_assembly.json"))


if __name__ == "__main__":
    main()
