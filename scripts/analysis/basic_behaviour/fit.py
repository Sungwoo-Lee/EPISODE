#!/usr/bin/env python3
"""fit.py - per-run models of one behaviour: pre-fit checks (B3), then univariate or multivariate (B4).

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2).

    P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
    nice -n 19 $P scripts/analysis/basic_behaviour/fit.py --population <population.json> \
        --out-root /abs/results/analysis/basic_behaviour/<pop> --kind univariate --target bush_dwell

Reads each cell's `episodes.npz` + `inventory.json` (written by sweep.py), and writes
`<cell>/<target>/{univariate,multivariate}.csv` in the legacy `hiding_drivers.py` format (same
columns, same order, same model labels) plus `<cell>/<target>/prefit.json`, which lists every
exclusion with its reason - nothing is dropped silently.

The model is `hiding_drivers.quasi_binomial_fit`, imported, never copied: the quasi-binomial GLM of
the behaviour's share of chosen steps per episode, effects as percentage points per +1 SD.

Refuses to run unless `results/analysis/basic_behaviour/_golden_pass.json` exists and records the
current sha256 of registry.py, sweep.py, fit.py, core/env.py and hiding_drivers.py (golden_gate.py
writes it). Runs LOCALLY only (statsmodels is missing on the lab nodes).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry as REG                                                  # noqa: E402

ROOT, A_DIR = REG.ROOT, REG.A_DIR
from hiding_drivers import quasi_binomial_fit                           # noqa: E402

BB_ROOT = REG.BB_ROOT                     # under $BB_DATA_ROOT/.../_water_dev when that is set
STAMP = os.path.join(BB_ROOT, "_golden_pass.json")
WATER_STAMP = os.path.join(BB_ROOT, "_water_pass.json")      # BASIC_BEHAVIOUR_WATER Gates
FIT_SOURCES = ["scripts/analysis/basic_behaviour/registry.py",
               "scripts/analysis/basic_behaviour/sweep.py",
               "scripts/analysis/basic_behaviour/fit.py",
               "scripts/analysis/core/env.py", "scripts/analysis/hiding_drivers.py"]

# By-construction identities inside a FIXED recipe carried over from a01. They make the design
# rank-deficient on purpose (the legacy script fits them that way, with a minimum-norm solution), so
# the rank check reports them as a note instead of excluding a column - otherwise the a01 gate would
# fail by construction. Each identity is asserted to hold exactly before it is accepted.
DECLARED_IDENTITIES = {"M5": [("detect_spread", ("detect_keenest", "detect_least_keen"),
                               "detect_spread = detect_keenest - detect_least_keen (fixed a01 recipe)")]}


# -------------------------------------------------------------------------------------- cell ----
class Cell:
    """One swept cell: factor arrays, counts, targets and the inventory, loaded lazily."""

    def __init__(self, out_root: str, label: str):
        self.dir = os.path.join(out_root, label)
        self.label = label
        self.inv = json.load(open(os.path.join(self.dir, "inventory.json")))
        self._z = np.load(os.path.join(self.dir, "episodes.npz"))
        self.arr = {}

    def a(self, key):
        if key not in self.arr:
            self.arr[key] = self._z[key]
        return self.arr[key]

    def factor(self, name):
        return self.a(f"f__{name}")

    @property
    def n(self):
        return int(self.inv["n_episodes"])


def subset_mask(cell: Cell, subset: str) -> np.ndarray:
    if subset == "all":
        return np.ones(cell.n, bool)
    kind, _, arg = subset.partition(":")
    if kind == "one":
        return cell.a(f"cnt__{arg}") == 1
    if kind == "two":
        return cell.a(f"cnt__{arg}") == 2
    if kind == "one_one":
        a, b = arg.split(",")
        return (cell.a(f"cnt__{a}") == 1) & (cell.a(f"cnt__{b}") == 1)
    raise SystemExit(f"unknown subset {subset!r}")


def target_arrays(cell: Cell, target: str):
    t = cell.inv["targets"].get(target)
    if t is None or not t["available"]:
        raise SystemExit(f"{cell.label}: target {target} unavailable: "
                         f"{t['reason'] if t else 'unknown target'}")
    return cell.a(f"y__{target}"), cell.a("n_steps")


# ------------------------------------------------------------------------------------ prefit ----
def prefit(cell: Cell, target: str, factors=None, arrays=None) -> dict:
    """B3 per factor on its own subset, in registry order. Returns included / excluded / demoted."""
    F = factors if factors is not None else cell.inv["factors"]
    get = (lambda n: arrays[n]) if arrays is not None else cell.factor
    inc, exc, demoted = [], [], []
    outcome = set(REG.OUTCOME_CONSEQUENCE.get(target, []))
    for f in F:
        n = f["name"]
        v = get(n)
        sub = subset_mask(cell, f["subset"])
        dfn = sub & np.isfinite(v)
        reason = None
        if dfn.sum() < REG.MIN_EPISODES:
            reason = f"defined on {int(dfn.sum())} episodes (< {REG.MIN_EPISODES})"
        else:
            u = np.unique(v[dfn])
            if len(u) == 1:
                reason = f"constant (= {u[0]:g}) in this run"
            else:
                for g in inc:
                    w = get(g["name"])
                    sh = dfn & subset_mask(cell, g["subset"]) & np.isfinite(w)
                    if sh.sum() >= REG.MIN_EPISODES and np.array_equal(v[sh], w[sh]):
                        reason = f"identical to {g['name']}"
                        break
        if reason is None and n in outcome:
            reason = "is (part of) the outcome being modelled"
        if reason:
            exc.append({"name": n, "reason": reason})
            continue
        f = dict(f)
        if f["role"] == "episode" and f["subset"] == "all" and not np.isfinite(v).all():
            # plan Revision 2, N2: an "all episodes" model must never silently run on a subset
            f["role"] = "episode_univariate_only"
            demoted.append({"name": n, "reason": f"non-finite on {int((~np.isfinite(v)).sum())} "
                            f"episodes; kept univariate-only so M1 / M4 see every episode"})
        inc.append(f)
    return {"target": target, "included": inc, "excluded": exc, "demoted": demoted}


# ------------------------------------------------------------------------------- univariate ----
def univariate(cell: Cell, target: str, pf: dict, arrays=None):
    import pandas as pd
    get = (lambda n: arrays[n]) if arrays is not None else cell.factor
    Y, L = target_arrays(cell, target)
    uni = []
    for f in pf["included"]:
        v = get(f["name"])
        keep = subset_mask(cell, f["subset"])
        blk = f["block"]
        r = quasi_binomial_fit(pd.DataFrame({f["name"]: v}), keep & np.isfinite(v), "univariate",
                               Y, L).iloc[1:]
        uni.append(r.assign(block=blk))
    return pd.concat(uni).sort_values("dpp_per_sd", key=abs, ascending=False)


# ----------------------------------------------------------------------------- multivariate ----
def _display(tag):
    return REG.ENTITY_NAMES.get(tag, {}).get("display", tag)


def recipes(cell: Cell, pf: dict, factors_all=None) -> list[dict]:
    """M1, M2, M3, M5, M4 as data (plan B4), from the included factors."""
    inc = pf["included"]
    names = [f["name"] for f in inc]
    ents = cell.inv["slots"]["entities"]
    c1 = next((e for e in ents if e["cls"] == "predator"), None)
    c2 = next((e for e in ents if e["cls"] != "predator"), None)
    count_of = {}
    for f in inc:
        if f.get("kind") == "count_entity":
            count_of[f["source"].split("[")[1].split("]")[0]] = f["name"]
    episode = [f["name"] for f in inc if f["role"] == "episode"]
    cons = [f["name"] for f in inc if f["block"] == "consequence"]
    trait = lambda e: [f["name"] for f in inc if e and f["role"] == f"class_trait:{e['tag']}"]
    out = [dict(id="M1", label="M1 exogenous, all episodes", cols=episode, subset="all")]
    if c1:
        d1 = _display(c1["tag"])
        m2 = [x for x in episode if x != count_of.get(c1["tag"])] + trait(c1)
        out.append(dict(id="M2", label=f"M2 exogenous + {d1} traits, 1-{d1} episodes", cols=m2,
                        subset=f"one:{c1['tag']}"))
        if c2:
            d2 = _display(c2["tag"])
            t2 = trait(c2)
            all_smell = all(x.endswith(("_smell_predatorness", "_olf_intensity")) for x in t2)
            m3 = [x for x in m2 if x != count_of.get(c2["tag"])] + t2
            out.append(dict(id="M3", label=f"M3 + {d2} {'smell' if all_smell else 'traits'}, "
                            f"1 {d1} + 1 {d2}", cols=m3, subset=f"one_one:{c1['tag']},{c2['tag']}"))
        m5 = cell.inv.get("m5") or {}
        lab5 = f"M5 two-{d1} episodes, keenest vs least-keen"
        if "skip" in m5:
            out.append(dict(id="M5", label=lab5, skip=m5["skip"]))
        else:
            p = m5["prefix"]
            need = [f"{p}_attack_delay", f"{p}_max_stamina"]
            miss = [x for x in need if x not in names]
            if miss:
                out.append(dict(id="M5", label=lab5, skip=f"traits {miss} excluded in this run"))
            else:
                out.append(dict(id="M5", label=lab5, subset=f"two:{c1['tag']}",
                                cols=[x for x in episode if x != count_of.get(c1["tag"])]
                                + ["detect_keenest", "detect_least_keen", "detect_spread"] + need))
    out.append(dict(id="M4", label="M4 exogenous + consequences", cols=episode + cons, subset="all"))
    return out


def _design_checks(X: np.ndarray, cols: list[str], declared: list) -> tuple[list, list]:
    """Within-design constant / duplicate / collinear checks (B3). Returns (keep_idx, exclusions)."""
    exc, keep = [], []
    ident = {d[0]: d for d in declared}
    sd = X.std(0)
    Z = (X - X.mean(0)) / np.where(sd > 0, sd, 1)
    for j, c in enumerate(cols):
        if sd[j] == 0:
            exc.append({"name": c, "reason": f"constant (= {X[0, j]:g}) in this design's episodes"})
            continue
        if c in ident:
            continue                      # handled after the rank check, as a declared identity
        dup = next((cols[k] for k in keep if np.array_equal(X[:, j], X[:, k])), None)
        if dup:
            exc.append({"name": c, "reason": f"identical to {dup}"})
            continue
        if keep:
            r = (Z[:, keep].T @ Z[:, j]) / len(Z)
            k = int(np.argmax(np.abs(r)))
            if abs(r[k]) >= REG.COLLINEAR_R:
                exc.append({"name": c, "reason": f"collinear with {cols[keep[k]]} (r = {r[k]:.4f})"})
                continue
            G = Z[:, keep + [j]].T @ Z[:, keep + [j]] / len(Z)
            ev = np.linalg.eigvalsh(G)
            if ev.min() < 1e-9 * ev.max():
                exc.append({"name": c, "reason": f"collinear with {[cols[x] for x in keep]} "
                            f"(design rank < columns)"})
                continue
        keep.append(j)
    return keep, exc


def multivariate(cell: Cell, target: str, pf: dict, arrays=None):
    """Returns (DataFrame in the legacy format, per-model record for prefit.json)."""
    import pandas as pd
    get = (lambda n: arrays[n]) if arrays is not None else cell.factor
    Y, L = target_arrays(cell, target)
    extra = {}
    if "detect_max" in cell._z.files:
        extra = {"detect_keenest": cell.a("detect_max"), "detect_least_keen": cell.a("detect_min")}
        extra["detect_spread"] = extra["detect_keenest"] - extra["detect_least_keen"]
    col = lambda n: extra[n] if n in extra else get(n)
    fits, rec = [], {}
    for r in recipes(cell, pf):
        if "skip" in r:
            rec[r["id"]] = {"label": r["label"], "skipped": r["skip"]}
            continue
        keep = subset_mask(cell, r["subset"])
        Xd = pd.DataFrame({n: col(n) for n in r["cols"]})
        rows = keep & np.isfinite(Xd.to_numpy()).all(1)
        if rows.sum() < REG.MIN_EPISODES:
            rec[r["id"]] = {"label": r["label"],
                            "skipped": f"{int(rows.sum())} episodes in its subset (< {REG.MIN_EPISODES})"}
            continue
        declared = DECLARED_IDENTITIES.get(r["id"], [])
        kidx, exc = _design_checks(Xd.to_numpy()[rows], list(Xd.columns), declared)
        notes = []
        for name, (a, b), text in declared:
            if name in Xd.columns:
                if not np.array_equal(Xd[name].to_numpy(), Xd[a].to_numpy() - Xd[b].to_numpy(),
                                      equal_nan=True):
                    raise SystemExit(f"{r['id']}: declared identity '{text}' does not hold")
                notes.append(f"{text}: the design is rank-deficient by construction; the three "
                             f"coefficients are the minimum-norm solution, as in the legacy fit")
        keepcols = [c for c in Xd.columns if c not in {e["name"] for e in exc}]
        fits.append(quasi_binomial_fit(Xd[keepcols], keep, r["label"], Y, L))
        rec[r["id"]] = {"label": r["label"], "n": int(fits[-1]["n"].iloc[0]), "columns": keepcols,
                        "excluded": exc, "notes": notes}
    return pd.concat(fits), rec


# ------------------------------------------------------------------------------------ stamp ----
def require_stamp(water: bool = False):
    """The golden stamp on the current sources; with water=True also the water gate's own stamp."""
    import hashlib
    if water:
        if not os.path.exists(WATER_STAMP):
            raise SystemExit(f"water stamp missing: {WATER_STAMP}\n  run golden_gate.py --water first")
        ws = json.load(open(WATER_STAMP))
        bad = [p for p in FIT_SOURCES if ws["sources"].get(p) !=
               hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()]
        if bad:
            raise SystemExit("sources changed since the water gate passed -- re-run golden_gate.py "
                             "--water:\n  " + "\n  ".join(bad))
    if not os.path.exists(STAMP):
        raise SystemExit(f"golden stamp missing: {STAMP}\n  run golden_gate.py first")
    st = json.load(open(STAMP))
    bad = []
    for p in FIT_SOURCES:
        h = hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()
        if st["sources"].get(p) != h:
            bad.append(p)
    if bad:
        raise SystemExit("sources changed since the golden gate passed -- re-run golden_gate.py:\n  "
                         + "\n  ".join(bad))
    return st


def fit_cell(out_root: str, label: str, kind: str, target: str) -> dict:
    cell = Cell(out_root, label)
    pf = prefit(cell, target)
    od = os.path.join(cell.dir, target)
    os.makedirs(od, exist_ok=True)
    pj = os.path.join(od, "prefit.json")
    rec = json.load(open(pj)) if os.path.exists(pj) else {}
    rec.update({"label": label, "target": target, "n_episodes": cell.n,
                "excluded": pf["excluded"], "demoted": pf["demoted"],
                "included": [f["name"] for f in pf["included"]]})
    if kind == "univariate":
        uni = univariate(cell, target, pf)
        uni.to_csv(os.path.join(od, "univariate.csv"), index=False)
        rec["univariate_rows"] = int(len(uni))
    else:
        multi, mrec = multivariate(cell, target, pf)
        multi.to_csv(os.path.join(od, "multivariate.csv"), index=False)
        rec["multivariate"] = mrec
    json.dump(rec, open(pj, "w"), indent=1)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--kind", choices=["univariate", "multivariate"], required=True)
    ap.add_argument("--target", required=True, choices=sorted(REG.TARGETS))
    ap.add_argument("--cells", nargs="*", default=None)
    a = ap.parse_args(argv)
    require_stamp()
    sys.path.insert(0, os.path.join(A_DIR, "studies", "hypervigilance"))
    import readings as RD
    pop = RD.load_population(a.population)
    labels = [c["label"] for c in pop["cells"] if not a.cells or c["label"] in a.cells]
    for lab in labels:
        if not os.path.exists(os.path.join(a.out_root, lab, "episodes.npz")):
            print(f"{lab}: not swept yet -- skipped")
            continue
        inv = json.load(open(os.path.join(a.out_root, lab, "inventory.json")))
        if "water" in inv:
            require_stamp(water=True)       # populations with water also need the water gate
        if a.target not in inv["targets"]:
            print(f"{lab}: {a.target} does not exist in this world -- skipped")
            continue
        if not inv["targets"][a.target]["available"]:
            print(f"{lab}: {a.target} unavailable ({inv['targets'][a.target]['reason']}) -- skipped")
            continue
        rec = fit_cell(a.out_root, lab, a.kind, a.target)
        print(f"{lab}: {a.kind} {a.target}: {len(rec['included'])} factors, "
              f"{len(rec['excluded'])} excluded" + (f", demoted {rec['demoted']}" if rec["demoted"] else ""))


if __name__ == "__main__":
    main()
