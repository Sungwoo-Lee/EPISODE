"""The explicit run list of the modulator engagement check -- no discovery by name pattern.

Plain-language purpose: the check compares, pair by pair, how strongly a modulated agent's
modulator responds to felt injury with how much its injury-driven hiding exceeds its ordinary
partner's. Every tool in this folder takes its runs from the table below, written out folder by
folder, because the shared run-discovery regex (`scripts/analysis/nmn/ckpt_io._RUN_RE`) does not
match the `healrep_*` names, and widening it would also catch the two dead level-06 seed-42
folders of 2026-10-05 16:01 (`..._160128_..._t1none_s42`, `..._160249_..._t16quad_s42`), which
hold no checkpoints.

Each pair also names the eval-sweep spec and labels that produced its behaviour outcomes. The test
scenes the engagement measures use (probe directory, episode count) are read from that spec, so
engagement and behaviour are measured in the same scenes by construction.

The modulator-input study's four seed-42 level-05 runs (group `nmninp`, keys `nmninp_<V>_s42`,
V in N, I, IT, X) are listed here too, for the internal-measures screen
(docs/experiments/active/modulator_clues/MODULATOR_INPUT_INTERNALS.md). Each has a modulator but
no ordinary twin of its own: its `ordinary` field names the descriptive partner (the replication's
level-05 seed-42 ordinary agent), whose sweep label lives in a different spec, so its label here is
None and `spec_scene` returns only the modulated label. Their reference modulated agent is pair
`l05_s42`.

Plan: docs/experiments/active/modulator_clues/MODULATOR_ENGAGEMENT_CHECK.md (Revision 1a).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUNS_DIR = "results/JAX_RecurrentPPO"
DEAD_FOLDERS = ("20261005-160128_rppo_healrep_l06_t1none_s42",
                "20261005-160249_rppo_healrep_l06_t16quad_s42")


@dataclass(frozen=True)
class Pair:
    key: str          # e.g. "l04_s42"
    group: str        # "main" | "oos_fix" | "oos_orig"
    level: str        # demeaning stratum: l04 l05 l06 (main); l05fix, lvl04, lvl05 (out of sample)
    seed: int
    ordinary: str     # run folder under results/JAX_RecurrentPPO
    modulated: str
    spec: str         # eval-sweep spec that produced this pair's outcomes (main scene set)
    labels: tuple     # (ordinary label, modulated label) in that spec
    own_spec: str | None = None   # own-scene sweep spec (sensitivity row), if any

    @property
    def run_dirs(self):
        return {a: os.path.join(ROOT, RUNS_DIR, f) for a, f in
                (("ordinary", self.ordinary), ("modulated", self.modulated))}


_HR = "configs/eval_sweeps/healrep"
_MAIN = {  # level -> (main-set spec, own-scene spec, {seed: (ordinary folder, modulated folder)})
    "l04": (f"{_HR}/healrep_l04_core_rppo.yaml", None, {
        42: ("20261005-160115_rppo_healrep_l04_t1none_s42", "20261005-160228_rppo_healrep_l04_t16quad_s42"),
        43: ("20261005-160117_rppo_healrep_l04_t1none_s43", "20261005-160231_rppo_healrep_l04_t16quad_s43"),
        44: ("20261005-160119_rppo_healrep_l04_t1none_s44", "20261005-160235_rppo_healrep_l04_t16quad_s44")}),
    "l05": (f"{_HR}/healrep_l05_neutral_rppo.yaml", f"{_HR}/healrep_l05_own_rppo.yaml", {
        42: ("20261005-160124_rppo_healrep_l05_t1none_s42", "20261005-160241_rppo_healrep_l05_t16quad_s42"),
        43: ("20261005-160125_rppo_healrep_l05_t1none_s43", "20261005-160244_rppo_healrep_l05_t16quad_s43"),
        44: ("20261005-160126_rppo_healrep_l05_t1none_s44", "20261005-160248_rppo_healrep_l05_t16quad_s44")}),
    "l06": (f"{_HR}/healrep_l06_neutral_rppo.yaml", f"{_HR}/healrep_l06_own_rppo.yaml", {
        # seed 42: the 17:03 relaunch; the 16:01 folders are dead (DEAD_FOLDERS)
        42: ("20261005-170252_rppo_healrep_l06_t1none_s42", "20261005-170314_rppo_healrep_l06_t16quad_s42"),
        43: ("20261005-160131_rppo_healrep_l06_t1none_s43", "20261005-160255_rppo_healrep_l06_t16quad_s43"),
        44: ("20261005-160134_rppo_healrep_l06_t1none_s44", "20261005-160258_rppo_healrep_l06_t16quad_s44")}),
}
_FIX = {
    42: ("20261006-074127_rppo_healrep_l05fix_t1none_s42", "20261006-074133_rppo_healrep_l05fix_t16quad_s42"),
    43: ("20261006-074127_rppo_healrep_l05fix_t1none_s43", "20261006-074134_rppo_healrep_l05fix_t16quad_s43"),
    44: ("20261006-074127_rppo_healrep_l05fix_t1none_s44", "20261006-074134_rppo_healrep_l05fix_t16quad_s44"),
}


_INP = "configs/eval_sweeps/nmninp"
#: variant -> (run folder, what the modulator reads). Input-study stage 1, seed 42, level 05.
NMNINP = {
    "N": ("20261007-111854_rppo_nmninp_l05_N_s42", ("Interoceptive Nociception",)),
    "I": ("20261007-111909_rppo_nmninp_l05_I_s42", ("Satiation", "Interoceptive Nociception")),
    "IT": ("20261007-111922_rppo_nmninp_l05_IT_s42",
           ("Satiation", "Body Temperature", "Interoceptive Nociception")),
    "X": ("20261007-111937_rppo_nmninp_l05_X_s42",
          ("Extero Nociception", "Thermoception", "Olfaction", "Collision", "Visual")),
}


def _build():
    out = []
    for lv, (spec, own, seeds) in _MAIN.items():
        for s, (o, m) in seeds.items():
            out.append(Pair(f"{lv}_s{s}", "main", lv, s, o, m, spec,
                            (f"{lv}_ordinary_s{s}", f"{lv}_modulated_s{s}"), own))
    for s, (o, m) in _FIX.items():
        out.append(Pair(f"l05fix_s{s}", "oos_fix", "l05fix", s, o, m,
                        f"{_HR}/healrep_l05fix_neutral_rppo.yaml",
                        (f"l05fix_ordinary_s{s}", f"l05fix_modulated_s{s}"),
                        f"{_HR}/healrep_l05fix_own_rppo.yaml"))
    # the two 22-Sep originals, selected because they showed the effect -> reported apart
    out.append(Pair("orig_lvl04_s42", "oos_orig", "lvl04", 42,
                    "20260922-182522_rppo_bq2cover_lvl04_t1none_s42",
                    "20260922-182527_rppo_bq2cover_lvl04_t16quad_s42",
                    "configs/eval_sweeps/basicq2_wave2_blocking_bush_rppo.yaml",
                    ("lvl04_control", "lvl04_modulated")))
    out.append(Pair("orig_lvl05_s42", "oos_orig", "lvl05", 42,
                    "20260922-182534_rppo_bq2cover_lvl05_t1none_s42",
                    "20260922-182538_rppo_bq2cover_lvl05_t16quad_s42",
                    "configs/eval_sweeps/thermal_probes/thermalprobe_neutral_clean_rppo.yaml",
                    ("lvl05_control", "lvl05_modulated")))
    # modulator-input study (seed 42, level 05); partner = the l05_s42 ordinary agent
    partner = _MAIN["l05"][2][42][0]
    for v, (folder, _reads) in NMNINP.items():
        out.append(Pair(f"nmninp_{v}_s42", "nmninp", f"l05inp_{v}", 42, partner, folder,
                        f"{_INP}/nmninp_l05_neutral_stage1_rppo.yaml", (None, f"l05_{v}_s42")))
    return tuple(out)


PAIRS = _build()
GROUPS = {"main": ("main",), "oos": ("oos_fix", "oos_orig"), "all": ("main", "oos_fix", "oos_orig"),
          "nmninp": ("nmninp",)}


def select(which):
    """`which`: 'main' | 'oos' | 'all' | comma-separated pair keys."""
    if which in GROUPS:
        return [p for p in PAIRS if p.group in GROUPS[which]]
    keys = which.split(",")
    by = {p.key: p for p in PAIRS}
    bad = [k for k in keys if k not in by]
    if bad:
        raise ValueError(f"unknown pair key(s) {bad}; valid: {sorted(by)}")
    return [by[k] for k in keys]


def load_spec(path):
    return yaml.safe_load(open(os.path.join(ROOT, path)))


def spec_scene(pair, own=False):
    """(probe dir, episodes, output_dir, {agent: sweep label}) of the pair's sweep spec, after
    checking that the spec's run paths for those labels are exactly this pair's folders."""
    path = pair.own_spec if own else pair.spec
    if path is None:
        raise ValueError(f"{pair.key}: no own-scene spec")
    sp = load_spec(path)
    for k in ("probe", "episodes", "output_dir", "runs"):
        if k not in sp:
            raise ValueError(f"{path}: mandatory key {k!r} missing")
    by_label = {r["label"]: r["path"].rstrip("/") for r in sp["runs"]}
    labels = {a: lab for a, lab in zip(("ordinary", "modulated"), pair.labels) if lab is not None}
    for agent, lab in labels.items():
        want = getattr(pair, agent)
        got = by_label.get(lab)
        # a spec path is a folder name or a glob on the run tag (the nmninp specs); a glob
        # must resolve to exactly this one folder
        if got is not None and any(c in got for c in "*?["):
            import glob
            hits = [os.path.basename(h) for h in glob.glob(os.path.join(ROOT, got))]
            got = hits[0] if len(hits) == 1 else f"<glob {got!r}: {len(hits)} matches>"
        elif got is not None:
            got = os.path.basename(got)
        if got != want:
            raise ValueError(f"{path}: label {lab!r} points at {got!r}, expected {want!r}")
    return sp["probe"], int(sp["episodes"]), sp["output_dir"], labels


def validate(pairs=PAIRS):
    """Fatal checks on the explicit list: folders exist and hold checkpoints, the modulated run
    has a FiLM modulator and the ordinary one has none, the top-level seed matches, no dead
    folder is used, and there is exactly one pair per (level, seed)."""
    from scripts.analysis.nmn import ckpt_io
    seen = set()
    for p in pairs:
        if (p.level, p.seed) in seen:
            raise ValueError(f"two pairs for level {p.level} seed {p.seed}")
        seen.add((p.level, p.seed))
        for agent, d in p.run_dirs.items():
            if os.path.basename(d) in DEAD_FOLDERS:
                raise ValueError(f"{p.key}: {d} is a dead folder (no checkpoints)")
            models = os.path.join(d, "models")
            if not ckpt_io.list_steps(models):
                raise ValueError(f"{p.key}: {models} holds no checkpoints")
            cfg = yaml.safe_load(open(os.path.join(models, "config.yaml")))
            mod = (cfg.get("agent") or {}).get("modulation") or {}
            has = mod.get("type") not in (None, "none")
            if has != (agent == "modulated"):
                raise ValueError(f"{p.key}: {agent} run {d} has modulation type {mod.get('type')!r}")
            if int(cfg["seed"]) != p.seed:   # top-level seed (Known Bugs: nested training.seed is stale)
                raise ValueError(f"{p.key}: {d} has top-level seed {cfg['seed']}, expected {p.seed}")
        spec_scene(p)
        if p.own_spec:
            spec_scene(p, own=True)
    return True
