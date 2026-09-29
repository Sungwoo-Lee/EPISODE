"""Shared plumbing of the Stage 3 drivers (run_similarity, run_decoding).

Plain-language purpose: both drivers read the same things (a manifest, the pinned rules, the
layer activity `run_activations` captured, each run's survival from its WandB log) and must
stamp and guard their outputs the same way. This module holds that common part, so the two
drivers cannot drift apart. It computes no similarity or read-out score and evaluates no rule.

- `load_manifest`: the Stage 2 keys (run_activations.load_manifest) plus the Stage 3 keys.
- `open_rules`: the one loader (rules_pin via decision_rules), the evidence status's policy,
  the committed-rules check for statuses that allow verdict words, and the bootstrap_n floor.
- `Captures`: the output directory of run_activations for the manifest, refused if any
  capture failed a tool check or was taken under other rules.
- `pair_sets`: the rules' pair sets (OO, MM, MO_diff, MO_same, UNTRAINED) from each run's
  saved arm and seed.
- `capture_gates`: gates G1, G2, G3 from the capture reports; `g4_controls`: the G4 inputs.
- `survival_block`: S_k and food bites per run from the local WandB log, gate G5, and the
  survival difference, with every stage and window read from the rules' `parameters:`.
- `stamp`, `guard_no_verdict_words`: every output carries the rules sha, the git sha and the
  evidence status; where the rules allow no verdict word, a written output containing one of
  the rules' verdict words raises before it is written.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §6,
§8, §A1/A3/A4 statistics, §A2 decoding.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NO_VERDICT = "no verdict is drawn"
UNTRAINED = "untrained"          # the capture selector run_activations writes for step 0

# The rules' verdict vocabulary (decision_rules' word constants, reduced to their words). An
# output of a status whose rules forbid verdict words must contain none of them.
VERDICT_WORDS = re.compile(
    r"\b(same|different|differs|undetermined|uninformative|match|matching|mixed|together|"
    r"independently|inherited|blocked|late|early|provisional)\b", re.IGNORECASE)


def _req(d: dict, key: str, where: str = "manifest"):
    if key not in d:
        raise ValueError(f"{where}: mandatory key {key!r} is missing")
    return d[key]


def _abs(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else Path(_ROOT) / p


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", _ROOT, *args], capture_output=True, text=True,
                              timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


# ------------------------------------------------------------------------------ manifest --
def load_manifest(path) -> dict:
    """Every Stage 2 key (run_activations.load_manifest) and the Stage 3 keys, all mandatory:
    bootstrap_n, probe_split {seed, bootstrap_seed}, ridge_alphas and inner_folds
    (representation.ridge_settings), min_rows_per_column, comparisons (auto | list of
    [label, label]) and tool_checks.self_similarity_atol."""
    from scripts.analysis.nmn import representation as rep
    from scripts.analysis.nmn import run_activations as ra
    man = ra.load_manifest(path)
    for k in ("bootstrap_n", "probe_split", "min_rows_per_column", "comparisons"):
        _req(man, k)
    rep.ridge_settings(man)
    for k in ("seed", "bootstrap_seed"):
        _req(man["probe_split"], k, "manifest.probe_split")
    _req(man["tool_checks"], "self_similarity_atol", "manifest.tool_checks")
    c = man["comparisons"]
    if c != "auto" and not (isinstance(c, list) and all(isinstance(p, list) and len(p) == 2
                                                         for p in c)):
        raise ValueError(f"comparisons must be 'auto' or a list of [label, label], got {c!r}")
    return man


def open_rules(man: dict):
    """(pinned, policy): the sha-checked rules, and what the evidence status may say. A status
    that allows verdict words needs the rules committed and clean (decision_rules.enforce_order).
    bootstrap_n is checked against gates.G6.bootstrap_n_min at load."""
    from scripts.analysis.nmn import decision_rules as dr
    pinned = dr.load(man)
    policy = dr.verdict_policy(pinned, man["evidence_status"])
    dr.enforce_order(pinned, policy)
    floor = int(dr.param(pinned.parameters, "gates.G6.bootstrap_n_min"))
    if int(man["bootstrap_n"]) < floor:
        raise ValueError(f"bootstrap_n {man['bootstrap_n']} is below the rules' G6 minimum {floor}")
    return pinned, policy


def stamp(pinned, policy, man_path) -> dict:
    """The fields every output carries."""
    return {"decision_rules": {"file": pinned.path, "sha256": pinned.sha256,
                               "commit": pinned.commit},
            "git_sha": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain", "--", "scripts/analysis/nmn")),
            "evidence_status": policy.status, "label": policy.label,
            "verdict_prefix": policy.prefix, "verdict_words_allowed": policy.allowed,
            "verdict_statement": (NO_VERDICT if not policy.allowed
                                  else "verdict words come only from decision_rules.evaluate_*"),
            "manifest": os.path.relpath(_abs(man_path), _ROOT),
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def guard_no_verdict_words(text: str, policy, where: str) -> None:
    """Refuse to write `text` if the policy allows no verdict word and it contains one."""
    if policy.allowed:
        return
    hits = sorted({m.group(0).lower() for m in VERDICT_WORDS.finditer(text)})
    if hits:
        raise ValueError(f"{where}: evidence status {policy.status!r} allows no verdict word, "
                         f"but the output contains {hits}")


def write_outputs(out: Path, stem: str, doc: dict, csv_rows: list, policy) -> None:
    """Write <stem>.json and <stem>.csv after the verdict-word guard has passed on both."""
    import csv
    import io
    js = json.dumps(doc, indent=1, default=_jsonable)
    buf = io.StringIO()
    if csv_rows:
        w = csv.DictWriter(buf, fieldnames=list(csv_rows[0]))
        w.writeheader()
        w.writerows(csv_rows)
    guard_no_verdict_words(js, policy, f"{stem}.json")
    guard_no_verdict_words(buf.getvalue(), policy, f"{stem}.csv")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}.json").write_text(js)
    (out / f"{stem}.csv").write_text(buf.getvalue())


def _jsonable(x):
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    return str(x)


# ------------------------------------------------------------------------------ captures --
class Captures:
    """The run_activations output directory of a manifest: probes, capture reports and the
    activation files (loaded on demand, checked against the probe's row-index sha256)."""

    def __init__(self, man: dict, pinned):
        from scripts.analysis.nmn import probe_set
        self.out = _abs(man["out_root"]) / man["name"]
        mf = self.out / "manifest.json"
        if not mf.exists():
            raise ValueError(f"{mf}: no run_activations output for this manifest")
        self.meta = json.loads(mf.read_text())
        if self.meta["decision_rules"]["sha256"] != pinned.sha256:
            raise ValueError(f"{mf}: captured under rules sha256 "
                             f"{self.meta['decision_rules']['sha256']}, the manifest pins "
                             f"{pinned.sha256}; re-run run_activations")
        bad = [c["stem"] for c in self.meta["captures"] if c["failures"]]
        if bad:
            raise ValueError(f"captures with failed tool checks: {bad}")
        self.probes = {p["id"]: probe_set.load(self.out / "probes", p["id"]) for p in man["probes"]}
        for pid, p in self.probes.items():
            if p.row_sha256 != self.meta["probes"][pid]["row_index_sha256"]:
                raise ValueError(f"probe {pid}: row index differs from the captured one")
        self.reports = {}
        for c in self.meta["captures"]:
            rep = json.loads((self.out / f"{c['stem']}.json").read_text())
            self.reports[(rep["run_label"], str(rep["selector"]), rep["probe"])] = rep

    def _npz(self, label, selector, probe):
        rep = self.reports[(label, str(selector), probe)]
        z = np.load(self.out / rep["activations_file"])
        if str(z["__probe_row_index_sha256__"]) != self.probes[probe].row_sha256:
            raise ValueError(f"{rep['activations_file']}: captured on another probe")
        return z

    def keys(self, label, selector, probe) -> set:
        return {k for k in self._npz(label, selector, probe).files if not k.startswith("__")}

    def layer(self, label, selector, probe, key) -> np.ndarray:
        """One captured layer (rows x columns, float64); only that array is read."""
        return np.asarray(self._npz(label, selector, probe)[key], np.float64)


def cells(caps: Captures, man: dict) -> list[tuple[str, str]]:
    """(selector, probe) cells every run was captured at, `:prev` selectors excluded (those
    serve only the A4 within-stage drift)."""
    out = []
    for r0 in man["runs"][:1]:
        for sel in r0["checkpoints"]:
            sel = str(sel)
            if sel.endswith(":prev"):
                continue
            for pid in caps.probes:
                if all((r["label"], sel, pid) in caps.reports for r in man["runs"]):
                    out.append((sel, pid))
    return out


def primary_cell(pinned, status: str, all_cells: list) -> tuple[str, str]:
    """The cell the A1/A2/A3 verdicts are read at: the rules' evidence_status.<status>
    `primary_checkpoint` / `primary_probe_world` when the status names them; otherwise the
    manifest must have exactly one cell (the interim and the pilot)."""
    pol = pinned.rules["evidence_status"][status]
    if "primary_checkpoint" in pol:
        c = (str(pol["primary_checkpoint"]), str(pol["primary_probe_world"]))
        if c not in all_cells:
            raise ValueError(f"the rules' primary cell {c} was not captured ({all_cells})")
        return c
    if len(all_cells) != 1:
        raise ValueError(f"status {status!r} names no primary cell and the manifest has "
                         f"{len(all_cells)} cells {all_cells}; the rules must say which")
    return all_cells[0]


def pair_sets(agents: dict, comparisons) -> dict:
    """The rules' pair sets. agents: {name: {"arm": ordinary|modulated, "seed", "untrained"}}.
    OO / MM / MO_diff: trained pairs of different seeds; MO_same: trained ordinary vs modulated
    of one seed; UNTRAINED: untrained networks of different seeds. `comparisons` "auto" keeps
    every such pair; an explicit list keeps only the listed trained pairs (untrained pairs are
    kept)."""
    out = {k: {} for k in ("OO", "MM", "MO_diff", "MO_same", "UNTRAINED")}
    names = list(agents)
    wanted = None if comparisons == "auto" else {frozenset(p) for p in comparisons}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = agents[a], agents[b]
            if A["untrained"] or B["untrained"]:
                if A["untrained"] and B["untrained"] and A["seed"] != B["seed"]:
                    out["UNTRAINED"][f"{a}|{b}"] = (a, b)
                continue
            if wanted is not None and frozenset((a, b)) not in wanted:
                continue
            if A["arm"] == B["arm"]:
                if A["seed"] != B["seed"]:
                    out["OO" if A["arm"] == "ordinary" else "MM"][f"{a}|{b}"] = (a, b)
                continue
            o, m = (a, b) if A["arm"] == "ordinary" else (b, a)
            out["MO_same" if A["seed"] == B["seed"] else "MO_diff"][f"{o}|{m}"] = (o, m)
    return out


# ------------------------------------------------------------------------------- gates ----
def capture_gates(reports: list[dict], P) -> dict:
    """Gates G1 (self-replay), G2 (chain reconstruction) and G3 (alignment) from the capture
    reports of one cell, through decision_rules' gate functions. G1 and G3 apply to every
    capture that generated a store of the probe; G2 to every capture. The chain deviations are
    already normalised by max(1, max|reference|), so they enter G2 with max_abs_ref 0."""
    from scripts.analysis.nmn import decision_rules as dr
    margin = float(dr.param(P, "gates.G1.near_tie_logit_margin"))
    g1, g2, g3, gen = [], [], [], []
    for r in reports:
        dev = {k: {"max_abs_dev": v, "max_abs_ref": 0.0}
               for k, v in r["chain_assertions"]["max_rel_deviation"].items()}
        g2.append(dr.gate_G2(dev, P)[0])
        if r.get("gate_G1_self_agreement") is not None:
            gen.append(r["run_label"])
            g1.append(dr.gate_G1({**r["gate_G1_self_agreement"], "near_tie_logit_margin": margin}, P))
            al = r["alignment_controls"]
            g3.append(dr.gate_G3({"alignment": {**al["step_discontinuous_all"],
                                                "near_tie_logit_margin": margin},
                                  "shift_control_agreement": al["shift_by_one_all_rows_with_t_ge_1"]},
                                 P))
    if not gen:
        raise ValueError("no capture in this cell generated a probe store: G1/G3 not computable")
    return {"G1": all(g1), "G2": all(g2), "G3": all(g3), "generating_captures": gen}


def symlog(x):
    x = np.asarray(x, np.float64)
    return np.sign(x) * np.log(np.abs(x) + 1.0)


def quantity_rows(probe, quantity: str) -> np.ndarray:
    """Positions (into the probe's kept rows) a quantity is scored on: every row, except
    `nearest_predator_manhattan` (rows with an active predator) and the `steps_remaining`
    headline (rows of episodes that ended in death; truncated episodes' remaining time is
    censored). `steps_remaining_all` is the all-episode sensitivity variant."""
    n = probe.rows.size
    if quantity == "nearest_predator_manhattan":
        return np.flatnonzero(probe.targets["predator_valid"])
    if quantity == "steps_remaining":
        return np.flatnonzero(~probe.targets["truncated"])
    if quantity in ("steps_remaining_all", "satiation", "injury_level"):
        return np.arange(n)
    raise ValueError(f"no row rule for quantity {quantity!r}")


def target(probe, quantity: str) -> np.ndarray:
    return np.asarray(probe.targets["steps_remaining" if quantity == "steps_remaining_all"
                                    else quantity], np.float64)


def make_splits(groups, P, seed: int):
    """The probe's split (rules common.split: parameters.common.split.n_repeats repeats, test
    fraction parameters.common.split.test_frac, grouped by episode_seed); one object shared by
    every agent and statistic on the probe."""
    from scripts.analysis.nmn import decision_rules as dr
    from scripts.analysis.nmn import representation as rep
    s = dr.split_settings(P)
    return rep.episode_split(groups, s["n_repeats"], s["test_frac"], seed)


def split_counts(splits, groups, rows=None) -> list[int]:
    """Distinct held-out groups per split repeat among `rows` (all rows when None): the count
    gate G6 reads, per quantity after its exclusions."""
    groups = np.asarray(groups)
    keep = np.ones(groups.size, bool) if rows is None else np.isin(np.arange(groups.size), rows)
    return [int(np.unique(groups[s.test[keep[s.test]]]).size) for s in splits]


def g4_controls(probe, splits, man: dict, quantities) -> dict:
    """The G4 inputs on the probe's raw input (symlog of the observation at the kept rows): the
    held-out R^2 of satiation (a positive control: satiation is an observed channel), and of
    each quantity with its values shuffled across episodes (a negative control: whole episodes'
    values are handed to other episodes, slot by slot). Mean over the split repeats. Also
    whether any group sits in both folds."""
    from scripts.analysis.nmn import representation as rep
    rs = rep.ridge_settings(man)
    groups = probe.row_seed
    X = symlog(probe.obs_all[probe.rows])
    rng = np.random.default_rng(int(man["probe_split"]["seed"]))
    ep = probe.row_episode
    E = probe.ep_T.size
    perm = rng.permutation(E)
    first = np.searchsorted(ep, np.arange(E), side="left")
    n_of = np.bincount(ep, minlength=E)
    slot = np.arange(ep.size) - first[ep]
    src = first[perm[ep]] + np.minimum(slot, n_of[perm[ep]] - 1)

    def mean_r2(y, rows):
        vals, alphas = [], []
        for s in splits:
            tr = np.intersect1d(s.train, rows)
            te = np.intersect1d(s.test, rows)
            m = rep.fit_ridge(X[tr], y[tr], groups[tr], alphas=rs["alphas"],
                              inner_folds=rs["inner_folds"])
            vals.append(rep.heldout_r2(m, X, y, te))
            alphas.append({"alpha": m.alpha, "alpha_at_edge": m.alpha_at_edge})
        return float(np.mean(vals)), vals, alphas

    sat, sat_rep, sat_a = mean_r2(target(probe, "satiation"), np.arange(ep.size))
    shuffled, detail = {}, {}
    for q in quantities:
        rows = quantity_rows(probe, q)
        y = target(probe, q)[src]
        ok = np.isin(src, rows) & np.isin(np.arange(ep.size), rows)
        v, per, a = mean_r2(y, np.flatnonzero(ok))
        shuffled[q], detail[q] = v, {"per_repeat": per, "fits": a, "rows": int(ok.sum())}
    disjoint = all(not np.intersect1d(np.unique(groups[s.train]), s.test_groups).size
                   for s in splits)
    return {"input_satiation_r2": sat, "input_satiation_r2_per_repeat": sat_rep,
            "input_satiation_fits": sat_a, "shuffled_r2": shuffled, "shuffled_detail": detail,
            "groups_disjoint": bool(disjoint),
            "shuffle": "episodes permuted (seed probe_split.seed); kept-row slot j of episode e "
                       "takes slot j of the episode it is paired with"}


def quantities(pinned) -> list:
    """The rules' A2 quantities, in the rules' order."""
    return list(pinned.rules["A2"]["quantities"])


# ----------------------------------------------------------------------------- survival ----
def stage_bounds(scanned: dict, boundaries, k: int) -> tuple[float, float]:
    """(lo, hi) of 0-based stage k, as pilot_readout sets them: lo is the run's start counter
    for stage 0 and the previous boundary otherwise; hi is the schedule boundary k."""
    from scripts.analysis.nmn import wandb_history as wh
    if not 0 <= k < len(boundaries):
        raise ValueError(f"stage/index {k} outside the run's {len(boundaries)} stages")
    lo = wh.start_counter(wh.episode_rows(scanned, None)) if k == 0 else float(boundaries[k - 1])
    return lo, float(boundaries[k])


def survival_block(runs: dict, P, status: str) -> dict:
    """Survival and food bites per run, gate G5, and the survival difference (rules
    common.survival_level, gates.G5_competence, A3 pattern c).

    runs: {label: {"arm", "scanned" (wandb_history.scan), "boundaries" (the run's schedule
    episode_boundaries)}}. The G5 stage is parameters.gates.G5.stage and the A3 stage is
    parameters.A3.survival_stage_by_status.<status> (both 1-based, read through
    decision_rules); the window, the row weighting and the _window_n skip are
    parameters.common.survival.*. G5 exclusions come first: the survival difference is over
    the runs that entered."""
    from scripts.analysis.nmn import decision_rules as dr
    from scripts.analysis.nmn import wandb_history as wh
    s = dr.survival_settings(P)
    k_g5, k_a3 = dr.g5_stage_index(P), dr.survival_stage_index(P, status)
    per_run = {}
    for label, r in runs.items():
        row = {"arm": r["arm"]}
        for tag, k in (("g5", k_g5), ("a3", k_a3)):
            b = stage_bounds(r["scanned"], r["boundaries"], k)
            for key, name in (("Episode/Steps", "S"), ("Episode/FoodEaten", "bites")):
                v, info = wh.stage_level(r["scanned"], k, b, key, s["window_episodes"],
                                         s["min_window_n"], s["row_weight"])
                row[f"{name}_{tag}"] = v
                row[f"{name}_{tag}_info"] = info
        per_run[label] = row
    g5 = dr.gate_G5({lab: {"arm": v["arm"], "S": v["S_g5"], "bites": v["bites_g5"]}
                     for lab, v in per_run.items()}, P)
    ent = g5["entered"]
    surv = dr.survival_difference({a: [per_run[lab]["S_a3"] for lab in ent[a]]
                                   for a in ("ordinary", "modulated")}, P)
    return {"per_run": per_run, "gate_G5": g5, "survival": surv,
            "stage_index": {"G5": k_g5, "A3": k_a3}, "settings": s}


def read_survival(man: dict, roles: dict) -> dict:
    """The `runs` input of survival_block, from each run's local WandB log (folder found by
    the saved tag, exactly one) and its saved models/schedule.yaml."""
    from scripts.analysis.nmn import wandb_history as wh
    out = {}
    for r in man["runs"]:
        run_dir = _abs(r["path"])
        sched = run_dir / "models" / "schedule.yaml"
        if not sched.exists():
            raise ValueError(f"{r['label']}: no models/schedule.yaml; the survival stages of "
                             f"the rules are defined for continual runs")
        bounds = yaml.safe_load(sched.read_text())["continual"]["episode_boundaries"]
        wdir = wh.resolve_by_tag(wh.run_tag(run_dir))
        out[r["label"]] = {"arm": roles[r["label"]]["arm"], "boundaries": bounds,
                           "scanned": wh.scan(wdir, allow_truncated=True),
                           "wandb_dir": os.path.relpath(wdir, _ROOT)}
    return out


def shared_start(man: dict, roles: dict) -> dict:
    """Rules A3.precondition_shared_start, checked now rather than assumed: for every seed with
    an ordinary and a modulated run, `untrained.build` gives identical main-network arrays
    (bitwise) and the modulated network's only extra subtree is `modulator`."""
    from scripts.analysis.nmn import untrained
    by_seed = {}
    for r in man["runs"]:
        by_seed.setdefault(roles[r["label"]]["seed"], {})[roles[r["label"]]["arm"]] = r
    per = {}
    for seed, arms in sorted(by_seed.items()):
        if set(arms) != {"ordinary", "modulated"}:
            continue
        o = untrained.param_arrays(untrained.build(_abs(arms["ordinary"]["path"]))[0])
        m = untrained.param_arrays(untrained.build(_abs(arms["modulated"]["path"]))[0])
        extra = sorted({re.match(r"\['([^']+)'\]", k).group(1) for k in set(m) - set(o)})
        same = all(k in m and np.array_equal(o[k], m[k]) for k in o)
        per[int(seed)] = {"main_arrays": len(o), "identical": bool(same),
                          "extra_subtrees": extra, "only_modulator_extra": extra == ["modulator"]}
    ok = bool(per) and all(v["identical"] and v["only_modulator_extra"] for v in per.values())
    return {"per_seed": per, "holds": ok}
