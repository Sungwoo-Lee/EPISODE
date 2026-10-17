"""Tests for the Figure 5 re-collection per-episode extraction and safe archive prune
(scripts/analysis/studies/half_factorial_l05/{extract_episodes,prune_archives}.py; plan-review
findings C1, C2, M3 in docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md).

Builds a synthetic sweep output folder (real archives packed by src/utils/episode_bundle.py, CSV
rows from cell_measures.cell_row, rows tables, provenance, run folders with models/ steps) under a
fake data root, plus decoy archives in an old frozen-scene folder that must never be touched.
"""
import csv
import gzip
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

_REPO = Path(__file__).resolve().parents[2]
_HF = _REPO / "scripts" / "analysis" / "studies" / "half_factorial_l05"
sys.path.insert(0, str(_HF))
import extract_episodes as XE  # noqa: E402
import prune_archives as PA  # noqa: E402

XE._setup_path()
import src.utils.episode_bundle as EB  # noqa: E402
from cell_measures import cell_row, HEAD  # noqa: E402

SET = "healoff_food_sampled"
CONDS = ["avoid_none_inj00", "avoid_pred_inj20"]
N_EP = 100
OUT_REL = f"results/eval/avoidance/metrics_history_rppo_lookalike_hf_random_layout/{SET}"
PROBE_REL = f"configs/environment/experiment/behavior_probes/random_layout/{SET}"
# run A: one folder; run B: two session folders with a near-duplicate step (600030 / 600080)
RUNS = {
    "runA": [("20261001-000000_rppo_A", [200000, 400000, 600000, 800000])],
    "runB": [("20261001-000000_rppo_B", [200010, 400020, 600030]),
             ("20261002-000000_rppo_B", [600080, 800040, 1000050])],
}
LABELS = [("runA", "20261001-000000_rppo_A"), ("runB", "20261001-000000_rppo_B"),
          ("runB_resumed", "20261002-000000_rppo_B")]
MAX_CK = 3


def _episode(i, seed, rng):
    T = int(rng.integers(5, 30))
    bush = [int(rng.integers(0, 10)), int(rng.integers(0, 10))]
    pos = [int(rng.integers(0, 10)), int(rng.integers(0, 10))]
    snaps = []
    for t in range(T):
        if rng.random() < 0.5:
            pos = [min(9, max(0, pos[0] + int(rng.integers(-1, 2)))), pos[1]]
        if rng.random() < 0.3:
            pos = list(bush)
        snaps.append({"agent_pos": np.array(pos), "obs_pos": np.array([bush]),
                      "animal_pos": np.array([[3, 3]]), "injury_level": np.float32(20 - t * 0.1)})
    return {"version": 1, "episode_index": i, "seed": seed, "snapshots": snaps}


def _make_cell(stage, step, seeds, rng):
    rec = stage / "run" / str(step) / "recordings" / str(step)
    rec.mkdir(parents=True)
    eps = []
    for i, s in enumerate(seeds):
        ep = _episode(i, s, rng)
        eps.append(ep)
        with gzip.open(rec / f"episode_{i:06d}.rec.gz", "wb") as fh:
            pickle.dump(ep, fh)
    return eps


@pytest.fixture
def world(tmp_path):
    root = tmp_path / "data"
    probe = root / PROBE_REL
    probe.mkdir(parents=True)
    for c in CONDS:
        shutil.copy(_REPO / PROBE_REL / f"{c}.yaml", probe / f"{c}.yaml")
    for _run, folders in RUNS.items():
        for name, steps in folders:
            for s in steps:
                (root / "results/JAX_RecurrentPPO" / name / "models" / str(s)).mkdir(parents=True)
    spec = {"name": "t", "algo": "rppo", "output_dir": OUT_REL, "probe": PROBE_REL,
            "conditions": CONDS, "episodes": N_EP, "max_checkpoints": MAX_CK, "nodes": [101],
            "runs": [{"label": l, "path": f"results/JAX_RecurrentPPO/{n}"} for l, n in LABELS]}
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    seeds = XE.expected_seeds(probe, CONDS, N_EP)
    out = root / OUT_REL
    scratch = out / "_scratch"
    rows_dir = scratch / "_rows" / "L1"
    rows_dir.mkdir(parents=True)
    rng = np.random.default_rng(0)
    rows = []
    for label, folder in LABELS:
        steps = [s for f, ss in sum(RUNS.values(), []) if f == folder for s in ss][-MAX_CK:]
        for c in CONDS:
            by_step = {}
            for s in steps:
                stage = tmp_path / "stage" / label / c / str(s)
                eps = _make_cell(stage, s, seeds[c], rng)
                z = scratch / label / c / f"{s}.zip"
                z.parent.mkdir(parents=True, exist_ok=True)
                EB.pack(stage, z)
                row = cell_row(s, eps)
                by_step[s] = row
                rows.append([label, c] + row + [N_EP, np.__version__, f"{label}/{c}/{s}.zip"])
            (out / label).mkdir(parents=True, exist_ok=True)
            with open(out / label / f"{c}.csv", "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(HEAD); w.writerows(by_step[s] for s in sorted(by_step))
    with open(rows_dir / "rows_101.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run_label", "cond"] + HEAD + ["n_episodes", "numpy_version", "bundle"])
        w.writerows(rows)
    for d in ("_logs/L1", "_run_markers"):
        (scratch / d).mkdir(parents=True)
        (scratch / d / "keep.txt").write_text("x")
    (out / "_provenance" / "L1" / "scenes").mkdir(parents=True)
    for c in CONDS:
        shutil.copy(probe / f"{c}.yaml", out / "_provenance" / "L1" / "scenes" / f"{c}.yaml")
    # an archive that is not an expected cell (older step of runA) -- must be kept
    # (merged: it has its CSV row, so it is extracted, but prune must not list it)
    extra_stage = tmp_path / "stage_extra"
    eps = _make_cell(extra_stage, 200000, seeds[CONDS[0]], rng)
    EB.pack(extra_stage, scratch / "runA" / CONDS[0] / "200000.zip")
    with open(out / "runA" / f"{CONDS[0]}.csv", "a", newline="") as fh:
        csv.writer(fh).writerow(cell_row(200000, eps))
    # decoys: old frozen-scene archives sharing the folder-name prefix
    decoys = [root / "results/eval/avoidance/metrics_history_rppo_lookalike_hf/grid/_scratch/runA/avoid_none_inj00/600000.zip",
              root / "results/eval/avoidance/metrics_history_rppo_lookalike_hf_noheal/grid/_scratch/runA/avoid_none_inj00/600000.zip"]
    for d in decoys:
        d.parent.mkdir(parents=True)
        d.write_bytes(b"decoy")
    return dict(root=root, spec=spec_path, out=out, scratch=scratch, seeds=seeds, decoys=decoys,
                n_cells=len(LABELS) * len(CONDS) * MAX_CK)


def _extract(w):
    return XE.main([str(w["spec"]), "--data-root", str(w["root"]), "--workers", "2"])


def _prune(w, *extra):
    return PA.main([str(w["spec"]), "--data-root", str(w["root"]), *extra])


def _zips(w):
    return sorted(p for p in w["scratch"].glob("*/*/*.zip"))


# ------------------------------------------------------------------------------------ tests ----
def test_slots_merge_near_duplicates():
    assert PA.slots([200000, 400000, 600030, 600080, 800040]) == [[200000], [400000], [600030, 600080], [800040]]


def test_extract_writes_checked_table_and_is_incremental(world):
    import pandas as pd
    assert _extract(world) == 0
    t = pd.read_parquet(world["out"] / XE.TABLE_REL)
    assert len(t) == (world["n_cells"] + 1) * N_EP  # + the merged extra archive
    for (lab, c, s), g in t.groupby(["run_label", "cond", "step"], observed=True):
        assert list(g["seed"]) == list(world["seeds"][c])
        csvrow = XE.read_csv_rows(world["out"] / lab / f"{c}.csv")[s]
        assert abs(g["bush_hiding"].mean() - float(csvrow[HEAD.index("bush_hiding")])) < 5e-5
    assert set(t["run"]) == {"runA", "runB"}
    mtime = (world["out"] / XE.TABLE_REL).stat().st_mtime_ns
    assert _extract(world) == 0  # nothing new: table not rewritten
    assert (world["out"] / XE.TABLE_REL).stat().st_mtime_ns == mtime


def test_extract_fails_loudly_on_csv_mismatch(world):
    f = world["out"] / "runA" / f"{CONDS[0]}.csv"
    rows = list(csv.reader(open(f)))
    rows[1][HEAD.index("bush_hiding")] = "0.9999"
    csv.writer(open(f, "w", newline="")).writerows(rows)
    assert _extract(world) == 1
    import pandas as pd
    t = pd.read_parquet(world["out"] / XE.TABLE_REL)
    assert "runA" not in set(t["run_label"])  # the failing label is not written


def test_prune_dry_run_deletes_nothing(world):
    assert _extract(world) == 0
    before = _zips(world)
    assert _prune(world) == 0
    assert _zips(world) == before
    lists = list((world["out"] / "_prune").glob("*_dryrun.tsv"))
    assert len(lists) == 1 and len(open(lists[0]).read().splitlines()) == 1 + world["n_cells"]


@pytest.mark.parametrize("breakage", ["rows_row", "archive", "table_rows", "csv_row", "short_rows"])
def test_prune_aborts_whole_batch_on_incomplete_cell(world, breakage):
    assert _extract(world) == 0
    victim = ("runB_resumed", CONDS[1], 800040)
    if breakage == "rows_row":
        f = world["scratch"] / "_rows/L1/rows_101.csv"
        rows = [r for r in csv.reader(open(f)) if not (r[0] == victim[0] and r[1] == victim[1] and r[2] == str(victim[2]))]
        csv.writer(open(f, "w", newline="")).writerows(rows)
    elif breakage == "short_rows":
        f = world["scratch"] / "_rows/L1/rows_101.csv"
        rows = list(csv.reader(open(f)))
        i = HEAD.index("survival_steps") + 3
        for r in rows[1:]:
            if r[0] == victim[0] and r[1] == victim[1] and r[2] == str(victim[2]):
                r[i] = "99"  # n_episodes
        csv.writer(open(f, "w", newline="")).writerows(rows)
    elif breakage == "archive":
        (world["scratch"] / victim[0] / victim[1] / f"{victim[2]}.zip").unlink()
    elif breakage == "csv_row":
        f = world["out"] / victim[0] / f"{victim[1]}.csv"
        rows = [r for r in csv.reader(open(f)) if r[0] != str(victim[2])]
        csv.writer(open(f, "w", newline="")).writerows(rows)
    elif breakage == "table_rows":
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        p = world["out"] / XE.TABLE_REL
        t = pq.read_table(p)
        drop = pc.and_(pc.and_(pc.equal(t["run_label"].cast("string"), victim[0]),
                               pc.equal(t["cond"].cast("string"), victim[1])),
                       pc.and_(pc.equal(t["step"], victim[2]), pc.equal(t["episode_index"], 7)))
        pq.write_table(t.filter(pc.invert(drop)), p)
    before = _zips(world)
    assert _prune(world, "--delete") == 1
    assert _zips(world) == before
    assert not list((world["out"] / "_prune").glob("*_deleted.tsv"))


def test_prune_delete_removes_only_listed_archives(world):
    assert _extract(world) == 0
    extra = world["scratch"] / "runA" / CONDS[0] / "200000.zip"
    assert _prune(world, "--delete") == 0
    left = _zips(world)
    assert left == [extra]  # the unlisted archive is kept
    for d in world["decoys"]:
        assert d.read_bytes() == b"decoy"
    for keep in ("_rows/L1/rows_101.csv", "_logs/L1/keep.txt", "_run_markers/keep.txt"):
        assert (world["scratch"] / keep).exists()
    assert (world["out"] / "_provenance/L1/scenes").is_dir()
    assert (world["out"] / XE.TABLE_REL).exists()
    log = list((world["out"] / "_prune").glob("*_deleted.tsv"))[0]
    rows = list(csv.DictReader(open(log), delimiter="\t"))
    assert len(rows) == world["n_cells"]
    assert all(len(r["sha256"]) == 64 and int(r["bytes"]) > 0 for r in rows)
    assert all(r["path"].startswith(OUT_REL + "/_scratch/") and r["path"].endswith(".zip") for r in rows)
    # a second pass accepts the already-pruned cells through the log; extract skips them too
    assert _prune(world) == 0
    assert _extract(world) == 0


def test_prune_refuses_other_output_folders(world, tmp_path):
    spec = yaml.safe_load(open(world["spec"]))
    spec["output_dir"] = "results/eval/avoidance/metrics_history_rppo_lookalike_hf/grid"
    (world["root"] / spec["output_dir"]).mkdir(parents=True, exist_ok=True)
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(spec))
    assert PA.main([str(p), "--data-root", str(world["root"]), "--delete"]) == 1
    for d in world["decoys"]:
        assert d.read_bytes() == b"decoy"


def test_assert_deletable_guards(world):
    sc = world["scratch"]
    labels, conds = {l for l, _ in LABELS}, set(CONDS)
    ok = sc / "runA" / CONDS[0] / "800000.zip"
    assert PA.assert_deletable(ok, sc, labels, conds) == ok.resolve()
    for bad in (sc / "_rows/L1/rows_101.csv", sc / "_logs/L1/keep.txt", world["decoys"][0],
                sc / "runA" / CONDS[0]):
        with pytest.raises(PA.Abort):
            PA.assert_deletable(bad, sc, labels, conds)
