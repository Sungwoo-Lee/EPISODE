#!/usr/bin/env python3
"""golden_gate.py - the new pipeline must reproduce the hiding page before any new number is trusted.

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), A5, S0.

    P=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
    nice -n 19 $P scripts/analysis/basic_behaviour/golden_gate.py

GATE 1 (a01, the unchanged path). A one-cell a01 population is built with the fixed
`make_population.py` command, swept, and fitted (bush_dwell, univariate + multivariate) into
`_golden_scratch/<sources-hash12>/`. The reference CSVs - produced by the base-commit
`hiding_drivers.py` on the same store - are first verified against the sha256s the hypervigilance
gate recorded, then compared with `cmp`-style byte equality. Pre-fit must exclude nothing on a01 and
the config audit must find nothing unhandled.

GATE 2 (one hv1ch store, the new-world paths). The frozen `hiding_drivers.py` (unchanged, run by
subprocess) and the new sweep + fits run on the same store; then: every per-episode array the two
share is np.array_equal (n_rocks excepted: the legacy code counts campfires as rocks); every legacy
univariate line not about rocks appears verbatim; eating / near-predator / near-rabbit successes
equal the legacy counts; the intensity terms are excluded as duplicates; and (Revision 2) the recipe
engine run with campfires + rocks recombined reproduces every legacy multivariate line verbatim.

THERMAL REPLAY (S0.3, S0.4, S0.5b, S0.5c). On the same hv1ch store: the body-temperature index is not
its alphabetical position and every start value lies in the configured range; for 20 episodes the
environment's own reset is replayed and the field at the agent's square equals the obs_true
reconstruction at every step (1e-4); the recovered baseline temperature equals the replayed draw
(1e-4); M1 sees every episode.

Pass of everything -> results/analysis/basic_behaviour/_golden_pass.json (source sha256s, reference
sha256s, HEAD, sweep seconds, every check). Any failure -> no stamp, non-zero exit, the first 40
differing lines / arrays printed. Runs LOCALLY only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry as REG                                                   # noqa: E402
import sweep as SW                                                       # noqa: E402
import fit as FT                                                         # noqa: E402

ROOT = REG.ROOT
PY = sys.executable
BB = SW.BB_ROOT
A01_RUN = "results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106"
A01_STORE_ROOT = "results/trajectories"
HV1CH_RUN = "results/JAX_RecurrentPPO/20261001-002402_rppo_hv1ch_t1none_s42"
HV_STORE_ROOT = "results/trajectories_hvsmell"
HV_REF_DIR = os.path.join(ROOT, "results/analysis/hypervigilance/_golden_scratch/g3_reference")
HV_STAMP = os.path.join(ROOT, "results/analysis/hypervigilance/_golden_sweep_pass.json")
REF_DIR = os.path.join(BB, "_golden_reference", "a01")
REF_FILES = ("univariate.csv", "multivariate.csv", "summary.json")
STAMP_SOURCES = FT.FIT_SOURCES + ["scripts/analysis/basic_behaviour/golden_gate.py"]
LEGACY_ORDER = ["start_injury", "start_nutrition", "n_predators", "n_rabbits", "n_bushes", "n_rocks",
                "n_food", "n_ambush_predators", "spawn_dist_to_bush",
                "pred_detection_range", "pred_attack_delay", "pred_attack_range", "pred_max_stamina",
                "pred_smell_predatorness", "spawn_dist_to_predator", "pred_olf_intensity",
                "rab_smell_predatorness", "rab_olf_intensity"] + REG.CONSEQUENCES


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


class Gate:
    def __init__(self):
        self.checks = []

    def check(self, name, ok, detail=""):
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""), flush=True)
        return ok

    @property
    def ok(self):
        return all(c["ok"] for c in self.checks)


# ----------------------------------------------------------------------------- references ----
def copy_references(g: Gate) -> dict:
    """Copy the hv gate's a01 reference into this pipeline's tree once, with sha256s (plan L2)."""
    want = json.load(open(HV_STAMP))["g3_reference"]
    os.makedirs(REF_DIR, exist_ok=True)
    rec_p = os.path.join(REF_DIR, "sha256.json")
    if not os.path.exists(rec_p):
        for f in REF_FILES:
            src = os.path.join(HV_REF_DIR, f)
            if sha(src) != want[f]:
                raise SystemExit(f"hv reference {src} sha256 {sha(src)} != recorded {want[f]}; "
                                 f"never regenerated silently")
            shutil.copy2(src, os.path.join(REF_DIR, f))
        json.dump({f: want[f] for f in REF_FILES} | {"copied_from": os.path.relpath(HV_REF_DIR, ROOT),
                   "copied_at": _dt.datetime.now().isoformat(timespec="seconds")},
                  open(rec_p, "w"), indent=1)
    rec = json.load(open(rec_p))
    for f in REF_FILES:
        got = sha(os.path.join(REF_DIR, f))
        g.check(f"reference {f} sha256", got == rec[f] == want[f], got[:12])
    return {f: rec[f] for f in REF_FILES}


def population(scratch, name, args) -> str:
    out = os.path.join(scratch, name, "population.json")
    if not os.path.exists(out):
        cmd = [PY, os.path.join(ROOT, "scripts/analysis/studies/hypervigilance/make_population.py"),
               "--population", name, *args, "--out", out]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"make_population failed: {r.stdout}{r.stderr}")
        print("  " + r.stdout.strip())
    return out


def sweep_one(pop_p, out_root):
    import readings as RD
    c = RD.load_population(pop_p)["cells"][0]
    RD.require_yardstick_for([c])
    have = os.path.exists(os.path.join(out_root, c["label"], "_provenance.json"))
    pv = SW.sweep_cell(c, out_root, reuse=have)
    return c, pv


def diff_lines(a, b, n=40):
    la, lb = open(a).read().splitlines(), open(b).read().splitlines()
    out = []
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "<missing>"
        y = lb[i] if i < len(lb) else "<missing>"
        if x != y:
            out.append(f"line {i + 1}:\n    ref {x}\n    new {y}")
        if len(out) >= n:
            break
    return out


# --------------------------------------------------------------------------------- gate 1 ----
def gate1(g: Gate, scratch: str) -> dict:
    print("\n=== Gate 1: a01, byte identity ===")
    pop = population(scratch, "bb_golden_a01",
                     ["--runs", A01_RUN, "--world", "a01", "--agent", "unmodulated",
                      "--store-root", A01_STORE_ROOT])
    out_root = os.path.join(scratch, "a01")
    c, pv = sweep_one(pop, out_root)
    cell = FT.Cell(out_root, c["label"])
    pf = FT.prefit(cell, "bush_dwell")
    od = os.path.join(scratch, "a01_fit")
    os.makedirs(od, exist_ok=True)
    FT.univariate(cell, "bush_dwell", pf).to_csv(os.path.join(od, "univariate.csv"), index=False)
    multi, mrec = FT.multivariate(cell, "bush_dwell", pf)
    multi.to_csv(os.path.join(od, "multivariate.csv"), index=False)
    for f in ("univariate.csv", "multivariate.csv"):
        a, b = os.path.join(REF_DIR, f), os.path.join(od, f)
        same = open(a, "rb").read() == open(b, "rb").read()
        g.check(f"a01 {f} byte-identical", same, "" if same else "\n" + "\n".join(diff_lines(a, b)))
    mexc = {k: v.get("excluded", []) for k, v in mrec.items()}
    g.check("a01 pre-fit excludes nothing (S0.7)",
            not pf["excluded"] and not pf["demoted"] and not any(mexc.values()),
            json.dumps({"univariate": pf["excluded"], "multivariate": mexc}))
    notes = {k: v.get("notes") for k, v in mrec.items() if v.get("notes")}
    inv = cell.inv
    g.check("a01 audit: zero unhandled markers", not inv["unhandled"], json.dumps(inv["unhandled"]))
    names = [f["name"] for f in inv["factors"]]
    leg = [n for n in LEGACY_ORDER if n in names]
    g.check("a01 factor names and order are the legacy ones", names == leg and
            len(names) == len(LEGACY_ORDER), f"{names}")
    ref = json.load(open(os.path.join(REF_DIR, "summary.json")))
    dwell = float(100 * cell.a("bush_steps").sum() / cell.a("n_steps").sum())
    g.check("a01 pooled bush share == reference overall_dwell (S0.10)", dwell == ref["overall_dwell"],
            f"{dwell!r} vs {ref['overall_dwell']!r}")
    return {"cell": c["label"], "sweep_seconds": pv.get("seconds"), "m5_notes": notes,
            "inventory_unhandled": inv["unhandled"]}


# --------------------------------------------------------------------------------- gate 2 ----
def legacy_hv1ch() -> str:
    hd = sha(os.path.join(ROOT, "scripts/analysis/hiding_drivers.py"))
    d = os.path.join(BB, "_golden_scratch", f"legacy_hv1ch_{hd[:12]}")
    meta_p = os.path.join(d, "_legacy_run.json")
    done = all(os.path.exists(os.path.join(d, f)) for f in ("aggregate.npz", "univariate.csv",
                                                            "multivariate.csv"))
    if done and os.path.exists(meta_p):
        m = json.load(open(meta_p))
        ok = (m["run"] == HV1CH_RUN and m["hiding_drivers_sha256"] == hd
              and open(os.path.join(d, "exit_code")).read().strip() == "0")
        if ok:
            print(f"  legacy hv1ch outputs reused ({os.path.relpath(d, ROOT)})")
            return d
        raise SystemExit(f"{d}: legacy outputs from another run or script -- remove them")
    os.makedirs(d, exist_ok=True)
    json.dump({"run": HV1CH_RUN, "store_root": [HV_STORE_ROOT], "hiding_drivers_sha256": hd,
               "started": _dt.datetime.now().isoformat(timespec="seconds")}, open(meta_p, "w"))
    t0 = time.time()
    r = subprocess.run([PY, "scripts/analysis/hiding_drivers.py", "--run", HV1CH_RUN, "--store-root",
                        HV_STORE_ROOT, "--out", os.path.relpath(d, ROOT)], cwd=ROOT,
                       capture_output=True, text=True)
    open(os.path.join(d, "run.log"), "w").write(r.stdout + r.stderr)
    open(os.path.join(d, "exit_code"), "w").write(str(r.returncode))
    open(os.path.join(d, "seconds"), "w").write(str(round(time.time() - t0)))
    if r.returncode:
        raise SystemExit(f"frozen hiding_drivers.py failed on hv1ch: {r.stderr[-2000:]}")
    return d


def gate2(g: Gate, scratch: str) -> dict:
    print("\n=== Gate 2: hv1ch, frozen script vs new pipeline ===")
    leg = legacy_hv1ch()
    pop = population(scratch, "bb_golden_hv1ch",
                     ["--runs", HV1CH_RUN, "--world", "hv1ch", "--store-root", HV_STORE_ROOT])
    out_root = os.path.join(scratch, "hv1ch")
    c, pv = sweep_one(pop, out_root)
    cell = FT.Cell(out_root, c["label"])
    inv = cell.inv
    L = dict(np.load(os.path.join(leg, "aggregate.npz"), allow_pickle=True))
    tags = {e["tag"] for e in inv["slots"]["entities"]}
    if tags != {"pred", "rabbit"}:
        raise SystemExit(f"gate 2 expects one 'pred' and one 'rabbit' declaration, got {tags}")
    ch = inv["scent"]["channels"]
    name_map = {"n_pred": "cnt__pred", "n_rab": "cnt__rabbit", "n_bush": "cnt__obs__bush",
                "n_food": "cnt__res__food", "n_ambush": "cnt__res__hiding_predator",
                "pred_detect": "f__pred_detection_range", "pred_delay": "f__pred_attack_delay",
                "pred_range": "f__pred_attack_range", "pred_stamina": "f__pred_max_stamina",
                "pred_predatorness": "smell__pred", "rab_predatorness": "smell__rabbit",
                "pred_olf_ch1": f"smellch__pred__{ch[0]}", "rab_olf_ch1": f"smellch__rabbit__{ch[0]}",
                "pred_olf_intensity": "f__pred_olf_intensity",
                "rab_olf_intensity": "f__rab_olf_intensity",
                "pred_detect_max": "detect_max", "pred_detect_min": "detect_min"}
    skipped = {"n_rock": "legacy counts campfires as rocks (the defect this pipeline fixes)",
               "IBb": "same-row bush cross-table (A6; the new tables use row t-1)",
               "NBb": "same-row bush cross-table (A6; the new tables use row t-1)",
               "pred_olf_ch2": "single-channel layout: legacy fills NaN, no second channel",
               "rab_olf_ch2": "single-channel layout: legacy fills NaN, no second channel"}
    bad, compared = [], []
    for k, v in L.items():
        if k in skipped:
            continue
        nk = name_map.get(k, k)
        if nk not in cell._z.files:
            bad.append(f"{k}: no counterpart {nk}")
            continue
        w = cell.a(nk)
        eq = np.array_equal(v, w, equal_nan=True) if v.dtype.kind == "f" else np.array_equal(v, w)
        compared.append(k)
        if not eq:
            bad.append(f"{k} vs {nk}: differ (max |d| = "
                       f"{np.nanmax(np.abs(v.astype(float) - w.astype(float))):.3g})")
    g.check(f"hv1ch per-episode arrays equal ({len(compared)} compared; skipped {sorted(skipped)})",
            not bad, "; ".join(bad[:40]))
    pf = FT.prefit(cell, "bush_dwell")
    od = os.path.join(scratch, "hv1ch_fit")
    os.makedirs(od, exist_ok=True)
    uni = FT.univariate(cell, "bush_dwell", pf)
    uni.to_csv(os.path.join(od, "univariate.csv"), index=False)
    new_lines = set(open(os.path.join(od, "univariate.csv")).read().splitlines())
    leg_lines = open(os.path.join(leg, "univariate.csv")).read().splitlines()
    rocks = [l for l in leg_lines[1:] if l.split(",")[1] == "n_rocks"]
    miss = [l for l in leg_lines if l not in new_lines and l not in rocks]
    g.check(f"hv1ch legacy univariate lines verbatim ({len(leg_lines) - 1 - len(rocks)} rows; "
            f"n_rocks row excluded)", not miss, "\n" + "\n".join(miss[:40]))
    g.check("eating successes == legacy n_ate", np.array_equal(cell.a("y__eating"), L["n_ate"]))
    g.check("near_predator successes == legacy n_pred_near",
            np.array_equal(cell.a("y__near_predator"), L["n_pred_near"]))
    g.check("near_rabbit successes - both-near == legacy n_rab_near",
            np.array_equal(cell.a("y__near_rabbit") - cell.a("n_both_near"), L["n_rab_near"]))
    exc = {e["name"]: e["reason"] for e in pf["excluded"]}
    g.check("intensity terms excluded as duplicates (S0.8, hv1ch)",
            exc.get("pred_olf_intensity") == "identical to pred_smell_predatorness"
            and exc.get("rab_olf_intensity") == "identical to rab_smell_predatorness"
            and not any(l.split(",")[1].endswith("_olf_intensity") for l in leg_lines[1:]), json.dumps(exc))
    # Revision 2 extension: the recipe engine with campfires + rocks recombined -> legacy lines
    by = {f["name"]: f for f in inv["factors"]}
    nonhide = [o["name"] for o in inv["slots"]["obstacles"] if not o["hides"]]
    rock_sum = sum(cell.a(f"cnt__obs__{n}") for n in nonhide)
    arrays = {n: cell.factor(n) for n in by}
    arrays["n_rocks"] = rock_sum
    F_leg = []
    for n in LEGACY_ORDER:
        if n == "n_rocks":
            F_leg.append(dict(by.get("n_rocks", by[f"n_{nonhide[0]}"]), name="n_rocks"))
        elif n in by:
            F_leg.append(by[n])
    pf_leg = FT.prefit(cell, "bush_dwell", factors=F_leg, arrays=arrays)
    multi_leg, _ = FT.multivariate(cell, "bush_dwell", pf_leg, arrays=arrays)
    multi_leg.to_csv(os.path.join(od, "multivariate_legacy_set.csv"), index=False)
    ml = set(open(os.path.join(od, "multivariate_legacy_set.csv")).read().splitlines())
    lm = open(os.path.join(leg, "multivariate.csv")).read().splitlines()
    miss = [l for l in lm if l not in ml]
    g.check(f"hv1ch legacy multivariate lines verbatim with campfires + rocks recombined "
            f"({len(lm) - 1} rows)", not miss, "\n" + "\n".join(miss[:40]))
    multi, mrec = FT.multivariate(cell, "bush_dwell", pf)
    multi.to_csv(os.path.join(od, "multivariate.csv"), index=False)
    return {"cell": c["label"], "out_root": out_root, "sweep_seconds": pv.get("seconds"),
            "legacy_seconds": open(os.path.join(leg, "seconds")).read().strip()
            if os.path.exists(os.path.join(leg, "seconds")) else None,
            "multivariate": mrec, "prefit_excluded": pf["excluded"], "prefit_demoted": pf["demoted"],
            "unhandled": inv["unhandled"]}


# -------------------------------------------------------------------------- thermal replay ----
def thermal_replay(g: Gate, out_root: str, label: str, mrec: dict, n_eps: int = 20) -> dict:
    print("\n=== Thermal replay (S0.3, S0.4, S0.5b, S0.5c) ===")
    import yaml
    import jax
    import pyarrow.parquet as pq
    from src.environment.core import jax_reset, _THERMAL_FIELD_KEY
    cell = FT.Cell(out_root, label)
    inv = cell.inv
    ob = inv["obs_indices"]
    g.check("S0.3 body-temperature index differs from its alphabetical position (the trap is real)",
            ob["body_temp"] != ob["alphabetical_body_temp"],
            f"order index {ob['body_temp']}, alphabetical {ob['alphabetical_body_temp']}")
    cfg = yaml.safe_load(open(os.path.join(ROOT, HV1CH_RUN, "models", "config.yaml")))
    lo, hi = cfg["thermal"]["start_body_temp_low"], cfg["thermal"]["start_body_temp_high"]
    bt0 = cell.a("bt0")
    g.check(f"S0.3 every start body temperature in [{lo}, {hi}] with non-zero variance",
            bool((bt0 >= lo).all() and (bt0 <= hi).all() and bt0.var() > 0),
            f"min {bt0.min():.4f} max {bt0.max():.4f} var {bt0.var():.3f}")
    params = REG.rebuild_params(cfg)
    import readings as RD
    pop = RD.load_population(os.path.join(os.path.dirname(out_root), "bb_golden_hv1ch", "population.json"))
    store = os.path.join(ROOT, pop["cells"][0]["stores"][0])
    f0 = sorted(f for f in os.listdir(store) if f.startswith("steps_"))[0]
    tb = pq.read_table(os.path.join(store, f0), columns=["episode_seed", "t", "agent_row", "agent_col",
                                                          "obs_true"])
    sd = tb.column("episode_seed").to_numpy()
    uniq = np.unique(sd)
    pick = uniq[np.linspace(0, len(uniq) - 1, n_eps).astype(int)]
    OT = REG.ENV.listcol(tb.column("obs_true"), ob["D"])
    ar, ac = tb.column("agent_row").to_numpy(), tb.column("agent_col").to_numpy()
    t = tb.column("t").to_numpy()
    keys = jax.vmap(jax.random.PRNGKey)(np.asarray(pick, dtype=np.int64))
    states = jax.vmap(jax_reset, in_axes=(None, 0))(params, keys)
    fields = np.asarray(states.thermal_field)
    apos = np.asarray(states.agent_pos)

    def draw(k):
        _, _, _, _, pk = jax.random.split(k, 5)
        kd = jax.random.split(jax.random.fold_in(pk, _THERMAL_FIELD_KEY), 4)[0]
        return jax.random.uniform(kd, (), minval=params.thermal_default_temp_low,
                                  maxval=max(params.thermal_default_temp_high,
                                             params.thermal_default_temp_low))
    base = np.asarray(jax.vmap(draw)(keys))
    seeds = cell.a("seed")
    amb = cell.a("ambient")
    den = cell.a("ambient_den")
    worst_f, worst_b, rows_n, bad_pos = 0.0, 0.0, 0, []
    dens = []
    for i, s in enumerate(pick):
        rr = np.flatnonzero(sd == s)
        if not (ar[rr[t[rr] == 0][0]] == apos[i][0] and ac[rr[t[rr] == 0][0]] == apos[i][1]):
            bad_pos.append(int(s))
        rec = OT[rr, ob["thermo_own_cell"]].astype(np.float64) + OT[rr, ob["body_temp"]].astype(np.float64)
        fld = fields[i][ar[rr], ac[rr]].astype(np.float64)
        worst_f = max(worst_f, float(np.abs(rec - fld).max()))
        rows_n += len(rr)
        j = int(np.flatnonzero(seeds == s)[0])
        worst_b = max(worst_b, float(abs(amb[j] - base[i])))
        dens.append(float(den[j]))
    g.check(f"S0.4 replayed reset is the same episode (t=0 agent square), {n_eps} episodes",
            not bad_pos, f"mismatch seeds {bad_pos}")
    g.check(f"S0.4 field at the agent's square == obs_true reconstruction ({rows_n} steps, <= 1e-4)",
            worst_f <= 1e-4, f"max |diff| {worst_f:.3g}")
    g.check("S0.5b recovered ambient_temp == replayed baseline draw (<= 1e-4)", worst_b <= 1e-4,
            f"max |diff| {worst_b:.3g}; denominators 1 - 11*B in [{min(dens):.3f}, {max(dens):.3f}]")
    share = float(np.isfinite(amb).mean())
    g.check("S0.5b ambient_temp defined on every episode", share == 1.0, f"share {share:.6f}")
    m1n = mrec.get("M1", {}).get("n")
    g.check("S0.5c M1 sees every episode on the thermal world", m1n == cell.n, f"M1 n {m1n} of {cell.n}")
    return {"episodes": [int(x) for x in pick], "max_field_diff": worst_f, "max_baseline_diff": worst_b,
            "ambient_defined_share": share, "min_abs_denominator_all": float(np.abs(den).min())}


# ----------------------------------------------------------------------------------- main ----
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-gate1", action="store_true", help="development only; never stamps")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.join(REG.A_DIR, "studies", "hypervigilance"))
    srcs = {p: sha(os.path.join(ROOT, p)) for p in STAMP_SOURCES}
    h12 = hashlib.sha256(json.dumps(srcs, sort_keys=True).encode()).hexdigest()[:12]
    scratch = os.path.join(BB, "_golden_scratch", h12)
    os.makedirs(scratch, exist_ok=True)
    print(f"sources hash {h12}; scratch {os.path.relpath(scratch, ROOT)}")
    g = Gate()
    refs = copy_references(g)
    r1 = None if a.skip_gate1 else gate1(g, scratch)
    r2 = gate2(g, scratch)
    r3 = thermal_replay(g, r2["out_root"], r2["cell"], r2["multivariate"])
    result = {"date": _dt.datetime.now().isoformat(timespec="seconds"), "head": SW.git_head(),
              "sources": srcs, "combined": h12, "references": refs, "gate1": r1,
              "gate2": {k: v for k, v in r2.items() if k != "out_root"}, "thermal": r3,
              "checks": g.checks}
    json.dump(result, open(os.path.join(scratch, "_gate_result.json"), "w"), indent=1, default=str)
    if not g.ok or a.skip_gate1:
        bad = [c["check"] for c in g.checks if not c["ok"]]
        print(f"\nGOLDEN GATE {'NOT RUN IN FULL' if a.skip_gate1 else 'FAILED'}: {bad}; no stamp written")
        sys.exit(1)
    json.dump(result, open(FT.STAMP, "w"), indent=1, default=str)
    print(f"\nGOLDEN GATE PASSED -> {os.path.relpath(FT.STAMP, ROOT)}")


if __name__ == "__main__":
    main()
