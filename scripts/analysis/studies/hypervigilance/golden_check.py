#!/usr/bin/env python3
"""golden_check.py - reproduce already-published numbers before any new reading is believed.

Plan: docs/develop/active/behavior/HYPERVIGILANCE_ANALYSIS_TOOLING.md, A4 and section 8, split into
two tiers by Revision 2 (N2):

  --tier sweep --base <commit>     (the store sweeps; minutes to an hour)
      G1  collect_arm_data on three sensor-ladder arms   vs results/_golden_prerefactor_20260904/
      G2  collect_arm_data on two Wave cells + rabbit_avoidance on one
                                                       vs results/analysis/basicq2_integrated/
      G3  hiding_drivers (current code) on the a01 store vs the SAME script at <base> run on the same
          store (the Aug-25 aggregate predates its own schema, so it cannot be the reference -- R1);
          aimed_response on the a01 store (input to the published-value check)
      Every file comparison is `core/golden.py` (unchanged; REPRODUCED required); the three G3
      CSV/JSON products must be byte-identical (`cmp`). Writes _golden_sweep_pass.json with the
      sha256 of the SWEEP sources; candidate outputs are cached in _golden_scratch/sweep_<hash12>/.
  --tier assembly                  (seconds)
      Re-derives every published value of A4 THROUGH readings.py's own functions from that cache,
      at printed precision, and writes _golden_assembly_pass.json (sha256 of readings.py and
      make_population.py + the sweep stamp's sha256). readings.py requires both stamps.

Any failure: no stamp, non-zero exit. Nothing here filters keys or widens a golden.py tolerance.
The one opt-in is the assembly tier's `--printed-rounding via-producer-2dp` (see printed_match):
it exists because two published 1-dp figures were rounded from a 2-dp intermediate that sits
exactly on a half-way point (a01 14.95 -> "14.9"; clue page +0.25 -> "+0.3"). It is off by
default, and the stamp names the mode and every check that needed it.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings as RD            # noqa: E402

ROOT = RD.ROOT
SCRATCH = os.path.join(RD.HV_ROOT, "_golden_scratch")
PY = sys.executable
GOLDEN_PY = os.path.join(ROOT, "scripts", "analysis", "core", "golden.py")
GOLDEN_DIR = os.path.join(ROOT, "results", "_golden_prerefactor_20260904")
A01_RUN = "results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106"
A01_ROOT = "results/trajectories"
A01_AUG25 = os.path.join(ROOT, "results", "analysis", "hiding_drivers",
                         "20260810-185749_rppo_restprem_a01_n106")
G1_ARMS = ["A_baseline", "B_olf_only", "V4_blur05"]
G2_CELLS = ["w2_lvl05_control", "w1_lvl06_modulated"]
G2_RABBIT_CELL = "w2_lvl05_control"
BQ2 = os.path.join(ROOT, "results", "analysis", "basicq2_integrated")
BLIND = [os.path.join(ROOT, "results", "analysis", "nmn_olf_gae_grid", "ladderstyle", f)
         for f in ("t1none.json", "t16quad_ALL.json")]

#: A4 published values at printed precision (a01 doc Finding 2; clue page Figure A3 caption)
A01_UNIVARIATE = {"rab_smell_predatorness": 1.6, "pred_smell_predatorness": 1.7}
A01_EXTREMES = {  # (bottom, top) for hides %, food/step, starved %, killed %, survived steps
    "rabbit": {"hides_pct": (14.9, 22.6), "food_per_step": (0.227, 0.212),
               "starved_pct": (27.6, 38.5), "killed_pct": (45.0, 38.2),
               "survived_steps": (193.3, 175.6)},
    "predator": {"hides_pct": (29.7, 35.0), "food_per_step": (0.197, 0.183),
                 "starved_pct": (24.6, 40.7), "killed_pct": (71.6, 52.9),
                 "survived_steps": (88.9, 115.4)}}
A01_AIMED = {"difference_pp": (8.0, 6.4, 23.1), "rabbit_near_share": (26.7, 49.8),
             "time_near_rabbit": (13.0, 14.3)}
CLUE_HIDE_S_SPAN = (-1.9, 0.3)


def golden(gold: str, cand: str) -> dict:
    p = subprocess.run([PY, GOLDEN_PY, gold, cand], cwd=ROOT, capture_output=True, text=True)
    line = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:]
    return {"gold": os.path.relpath(gold, ROOT), "cand": os.path.relpath(cand, ROOT),
            "ok": p.returncode == 0 and line.startswith("REPRODUCED"), "verdict": line,
            "detail": p.stdout.strip().splitlines()[:-1][:10]}


def cmp_bytes(a: str, b: str) -> dict:
    ok = subprocess.run(["cmp", "-s", a, b]).returncode == 0
    return {"gold": os.path.relpath(a, ROOT), "cand": os.path.relpath(b, ROOT), "ok": ok,
            "verdict": "byte-identical" if ok else "DIFFERS"}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, log, env=None) -> float:
    t0 = time.time()
    with open(log, "w") as f:
        subprocess.run(cmd, cwd=ROOT, env=env or dict(os.environ), check=True, stdout=f,
                       stderr=subprocess.STDOUT)
    return round(time.time() - t0, 1)


def ladder_env(path: str) -> dict:
    return RD.child_env(path, SCRATCH)


# ------------------------------------------------------------------------------ sweep tier ----
def sweep_tier(base: str, reuse_reference: bool, jobs: int) -> int:
    hashes = RD.source_hashes(RD.SWEEP_SOURCES)
    comb = RD.combined_hash(hashes)
    cache = os.path.join(SCRATCH, f"sweep_{comb[:12]}")
    if os.path.exists(cache):
        raise SystemExit(f"{cache} exists: this exact sweep code was already checked there; remove it "
                         f"to re-run (never reused silently)")
    os.makedirs(cache)
    refd = os.path.join(SCRATCH, "g3_reference")
    os.makedirs(refd, exist_ok=True)
    base_src = subprocess.run(["git", "show", f"{base}:scripts/analysis/hiding_drivers.py"],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout
    base_py = os.path.join(refd, "hiding_drivers_base.py")
    timings, checks = {}, []
    if os.path.exists(os.path.join(refd, "aggregate.npz")):
        if not reuse_reference:
            raise SystemExit(f"{refd}/aggregate.npz exists; pass --reuse-reference to use it")
        if open(base_py).read() != base_src:
            raise SystemExit(f"{base_py} is not {base}:scripts/analysis/hiding_drivers.py")
        ref_note = {"reused": True}
    else:
        open(base_py, "w").write(base_src)
        timings["g3_reference"] = run([PY, base_py, "--run", A01_RUN, "--store-root", A01_ROOT,
                                       "--out", refd, "--cache", os.path.join(refd, "aggregate.npz")],
                                      os.path.join(refd, "run.log"))
        ref_note = {"reused": False}
    ref_note.update({f: RD.sha256(os.path.join(refd, f)) for f in
                     ("aggregate.npz", "univariate.csv", "multivariate.csv", "summary.json",
                      "hiding_drivers_base.py")})

    g3c, g3a = os.path.join(cache, "g3_candidate"), os.path.join(cache, "g3_aimed")
    g1, g2 = os.path.join(cache, "g1"), os.path.join(cache, "g2")
    for d in (g3c, g3a, g1, g2):
        os.makedirs(d)
    man = json.load(open(os.path.join(BQ2, "_manifest.json")))
    tasks = {
        "g3_candidate": ([PY, os.path.join(RD.A_DIR, "hiding_drivers.py"), "--run", A01_RUN,
                          "--store-root", A01_ROOT, "--out", g3c,
                          "--cache", os.path.join(g3c, "aggregate.npz")], None, g3c),
        "g3_aimed": ([PY, os.path.join(RD.A_DIR, "aimed_response.py"), "--run", A01_RUN,
                      "--store-root", A01_ROOT, "--out", os.path.join(g3a, "aimed_response.json")],
                     None, g3a),
        "g2_rabbit": ([PY, os.path.join(RD.A_DIR, "rabbit_avoidance.py"), "--run",
                       man[G2_RABBIT_CELL]["run"], "--store-root",
                       *sorted({s.rsplit("/", 4)[0] for s in man[G2_RABBIT_CELL]["stores"]}),
                       "--out", os.path.join(g2, f"rabbit_avoidance_{G2_RABBIT_CELL}.json")], None, g2),
    }
    for arm in G1_ARMS:
        tasks[f"g1_{arm}"] = ([PY, os.path.join(RD.A_DIR, "studies", "sensor_ladder",
                                                "collect_arm_data.py"), "--arms", arm],
                              ladder_env(g1), g1)
    for cellname in G2_CELLS:
        cm = os.path.join(g2, f"_cell_{cellname}.json")
        json.dump({cellname: man[cellname]}, open(cm, "w"), indent=1)
        tasks[f"g2_{cellname}"] = ([PY, os.path.join(RD.A_DIR, "studies", "sensor_ladder",
                                                     "collect_arm_data.py"), "--manifest", cm],
                                   ladder_env(g2), g2)

    def go(item):
        name, (cmd, env, d) = item
        return name, run(cmd, os.path.join(d, f"_{name}.log"), env)

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for name, secs in ex.map(go, tasks.items()):
            timings[name] = secs
            print(f"  {name}: {secs:.0f}s", flush=True)

    # --- comparisons (golden.py unchanged; nothing filtered)
    checks.append({"gate": "G3", **golden(os.path.join(refd, "aggregate.npz"),
                                          os.path.join(g3c, "aggregate.npz"))})
    for f in ("univariate.csv", "multivariate.csv", "summary.json"):
        checks.append({"gate": "G3", **cmp_bytes(os.path.join(refd, f), os.path.join(g3c, f))})
    npz_md5 = {}
    for line in open(os.path.join(GOLDEN_DIR, "_GOLDEN_NPZ_MD5.txt")):
        if line.strip():
            h, p = line.split(None, 1)
            npz_md5[os.path.normpath(p.strip())] = h
    for arm in G1_ARMS:
        checks.append({"gate": "G1", **golden(
            os.path.join(GOLDEN_DIR, "results", "analysis", "ladder", f"{arm}.json"),
            os.path.join(g1, f"{arm}.json"))})
        live = os.path.join("results", "analysis", "ladder", f"{arm}_episodes.npz")
        want = npz_md5.get(os.path.normpath(live))
        got = md5(os.path.join(ROOT, live)) if want else None
        if want is None or got != want:
            checks.append({"gate": "G1", "gold": live, "cand": None, "ok": False,
                           "verdict": f"golden npz md5 {want} != on-disk {got}: the in-place golden "
                                      f"array is not the one recorded"})
        else:
            checks.append({"gate": "G1", **golden(os.path.join(ROOT, live),
                                                  os.path.join(g1, f"{arm}_episodes.npz"))})
    for cellname in G2_CELLS:
        for suffix in (".json", "_episodes.npz"):
            checks.append({"gate": "G2", **golden(os.path.join(BQ2, "ladderstyle", cellname + suffix),
                                                  os.path.join(g2, cellname + suffix))})
    checks.append({"gate": "G2", **golden(
        os.path.join(BQ2, "rabbit_avoidance", f"{G2_RABBIT_CELL}.json"),
        os.path.join(g2, f"rabbit_avoidance_{G2_RABBIT_CELL}.json"))})
    ref_keys = len(np.load(os.path.join(refd, "aggregate.npz")).files)
    ok = all(c["ok"] for c in checks)
    for c in checks:
        print(f"  [{c['gate']}] {'PASS' if c['ok'] else 'FAIL'}  {c['cand'] or c['gold']}: {c['verdict']}")
    doc = {"tier": "sweep", "date": _dt.datetime.now().isoformat(timespec="seconds"),
           "base": base, **RD.git_state(), "sources": hashes, "combined": comb,
           "cache": os.path.relpath(cache, ROOT), "g3_reference": ref_note,
           "g3_reference_aggregate_keys": ref_keys, "timings_seconds": timings,
           "checks": checks, "passed": ok}
    RD.dump(doc, os.path.join(cache, "_sweep_report.json"))
    if not ok:
        print("SWEEP TIER FAILED -- no stamp written")
        return 1
    RD.dump(doc, RD.SWEEP_STAMP)
    print(f"sweep tier PASSED -> {RD.SWEEP_STAMP}")
    return 0


# --------------------------------------------------------------------------- assembly tier ----
def printed_match(got, want, nd, mode):
    """Does a raw value reproduce a published figure printed with `nd` decimals?

    'as-specified' (default, the plan's A4 wording): round(raw, nd) == published.
    'via-producer-2dp' (explicit opt-in, recorded in the stamp): the two archived producers wrote
    TWO decimals first -- supplementary/curves.py stores `(100*dw).round(2)`, a4_hypervigilance.py
    prints `:+.2f` -- and the page then printed one. A published 1-dp figure is accepted if it
    certifies the producer's 2-dp value within its closed half-interval. Used only where direct
    rounding fails, and every such check is listed in the stamp as needing it.
    """
    if round(got, nd) == want:
        return "direct"
    if mode == "via-producer-2dp" and nd == 1 and abs(round(got, 2) - want) <= 0.05 + 1e-9:
        return "via producer 2-dp output"
    return None


def assembly_tier(mode: str = "as-specified") -> int:
    if not os.path.exists(RD.SWEEP_STAMP):
        raise SystemExit("no sweep stamp: run --tier sweep first")
    sw = json.load(open(RD.SWEEP_STAMP))
    if sw["sources"] != RD.source_hashes(RD.SWEEP_SOURCES):
        raise SystemExit("sweep sources changed since the sweep tier passed: re-run --tier sweep")
    cache = os.path.join(ROOT, sw["cache"])
    if not os.path.isdir(cache):
        raise SystemExit(f"sweep cache {cache} is missing")
    checks = []

    def check(gate, what, got, want, nd=None):
        """Exact check (nd None) or a printed-precision check of raw values against published ones."""
        if nd is None:
            checks.append({"gate": gate, "what": what, "got": got, "want": want, "ok": bool(got == want),
                           "rule": "exact"})
            return
        got = tuple(float(g) for g in (got if isinstance(got, tuple) else (got,)))
        want_t = want if isinstance(want, tuple) else (want,)
        rules = [printed_match(g, w, nd, mode) for g, w in zip(got, want_t)]
        ok = all(r is not None for r in rules)
        rule = "direct" if all(r == "direct" for r in rules) else (
            "via producer 2-dp output" if ok else "FAIL")
        checks.append({"gate": gate, "what": what, "raw": list(got),
                       "got": tuple(round(g, nd) for g in got), "want": want_t, "ok": ok,
                       "rule": rule})

    # --- G2: hiding_shift identical on candidate and reference; published span of 14 hide_s
    for cellname in G2_CELLS:
        cand = json.load(open(os.path.join(cache, "g2", f"{cellname}.json")))["grids"]
        ref = json.load(open(os.path.join(BQ2, "ladderstyle", f"{cellname}.json")))["grids"]
        for g in ("rd", "rdc", "pd"):
            check("G2", f"{cellname} hiding_shift({g})", RD.hiding_shift(cand, g),
                  RD.hiding_shift(ref, g))
    files = sorted(f for f in os.listdir(os.path.join(BQ2, "ladderstyle"))
                   if f.endswith(".json") and ("lvl04" in f or "lvl05" in f or "lvl06" in f))
    hs = [RD.hiding_shift(json.load(open(os.path.join(BQ2, "ladderstyle", f)))["grids"], "rd")
          for f in files] + [RD.hiding_shift(json.load(open(p))["grids"], "rd") for p in BLIND]
    check("G2", f"number of published hide_s cells", len(hs), 14)
    check("G2", "published hide_s span (min, max) at 1 dp",
          (np.nanmin(hs), np.nanmax(hs)), CLUE_HIDE_S_SPAN, nd=1)

    # --- G3: univariate scent effects (candidate and the Aug-25 CSV), extreme rows, aimed split
    import yaml
    spec = RD.ENV.scent_spec(yaml.safe_load(open(os.path.join(ROOT, A01_RUN, "models", "config.yaml"))))
    g3c = os.path.join(cache, "g3_candidate")
    for src, d in (("candidate", g3c), ("Aug-25 published", A01_AUG25)):
        u = RD.s2_univariate(os.path.join(d, "univariate.csv"), os.path.join(d, "multivariate.csv"), spec)
        for term, want in A01_UNIVARIATE.items():
            check("G3", f"{src} univariate {term} pp/SD", u[term]["dpp_per_sd"], want, nd=1)
    D = dict(np.load(os.path.join(g3c, "aggregate.npz"), allow_pickle=True))
    ex = RD.s2_extremes(D, spec)
    for who, cols in A01_EXTREMES.items():
        rows = ex[who]["a01_fixed_bins"]
        for col, (lo, hi) in cols.items():
            nd = 3 if col == "food_per_step" else 1
            check("G3", f"{who} extreme rows {col}", (rows["bottom"][col], rows["top"][col]),
                  (lo, hi), nd=nd)
    aimed = RD.s3_summary(json.load(open(os.path.join(cache, "g3_aimed", "aimed_response.json"))))
    sr = aimed["same_row"]
    check("G3", "aimed split difference (nothing, predator, rabbit near) pp",
          tuple(sr["difference_pp"][s] for s in ("nothing near", "predator near", "rabbit near")),
          A01_AIMED["difference_pp"], nd=1)
    check("G3", "rabbit-near hiding rabbit-like -> predator-like %",
          (sr["bush_share_pct"]["rabbit-like"]["rabbit near"],
           sr["bush_share_pct"]["predator-like"]["rabbit near"]), A01_AIMED["rabbit_near_share"], nd=1)
    check("G3", "time near rabbit predator-like vs rabbit-like %",
          (sr["time_share_pct"]["predator-like"]["rabbit near"],
           sr["time_share_pct"]["rabbit-like"]["rabbit near"]), A01_AIMED["time_near_rabbit"], nd=1)
    ok = all(c["ok"] for c in checks)
    for c in checks:
        print(f"  [{c['gate']}] {'PASS' if c['ok'] else 'FAIL'}  {c['what']}: got {c['got']} "
              f"want {c['want']}  [{c['rule']}]" + (f" raw {c['raw']}" if c.get('rule') not in
                                                   ('direct', 'exact') else ""))
    hashes = RD.source_hashes(RD.ASSEMBLY_SOURCES)
    doc = {"tier": "assembly", "date": _dt.datetime.now().isoformat(timespec="seconds"),
           **RD.git_state(), "sources": hashes, "combined": RD.combined_hash(hashes),
           "sweep_stamp_sha256": RD.sha256(RD.SWEEP_STAMP), "sweep_cache": sw["cache"],
           "printed_rounding_mode": mode,
           "checks_needing_the_2dp_rule": [c["what"] for c in checks
                                            if c.get("rule") == "via producer 2-dp output"],
           "checks": checks, "passed": ok,
           "g3_extreme_rows_all": ex, "g3_aimed_same_row": sr, "g3_aimed_prev_row": aimed["prev_row"]}
    RD.dump(doc, os.path.join(cache, "_assembly_report.json"))
    if not ok:
        print("ASSEMBLY TIER FAILED -- no stamp written")
        return 1
    RD.dump(doc, RD.ASSEMBLY_STAMP)
    print(f"assembly tier PASSED -> {RD.ASSEMBLY_STAMP}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", choices=["sweep", "assembly"], required=True)
    ap.add_argument("--base", help="the commit the implementation started from (sweep tier)")
    ap.add_argument("--reuse-reference", action="store_true")
    ap.add_argument("--jobs", type=int, default=1, help="sweeps run concurrently (sweep tier)")
    ap.add_argument("--printed-rounding", choices=["as-specified", "via-producer-2dp"],
                    default="as-specified", help="assembly tier: see printed_match(); the choice "
                                                 "and every check that needed it go into the stamp")
    a = ap.parse_args()
    RD.guard_out_root(SCRATCH + os.sep + "x", RD.HV_ROOT)
    if a.tier == "sweep":
        if not a.base:
            raise SystemExit("--base <commit> is required for the sweep tier")
        sys.exit(sweep_tier(a.base, a.reuse_reference, a.jobs))
    sys.exit(assembly_tier(a.printed_rounding))


if __name__ == "__main__":
    main()
