"""Build a probe set: a fixed sample of stored episodes, their exact inputs, and the targets.

Plain-language purpose: to compare what two agents compute, both must be shown the SAME
inputs. A probe set takes the first `n_per_store` episodes of each listed trajectory store,
keeps every observation of those episodes (the network needs the whole episode to rebuild
its memory), and picks `rows_per_episode` time steps per episode at which layer activity will
be kept and at which the quantities to decode (hunger, injury, predator distance, remaining
survival time) are read.

The load-bearing property (plan finding 4): everything is gathered from ONE read of each
shard through ONE row-index array. Observations, the next action and every target are taken
with the same index object, so they cannot be misaligned by a re-read or a re-sort.

Row convention (src/utils/trajectory_store.py): row t holds the state at t and the action
that ARRIVED at t; an episode of length T has T + 1 rows (t = 0..T). Decision rows are
t = 0..T-1: the observation of row t is what the policy saw when it chose the action stored
in row t + 1. So `action_next[t] = action[t + 1]` exists for every decision row (row T, the
terminal state, supplies it for t = T - 1), and `action_cur[t] = action[t]` is -1 at t = 0.

Group count (plan re-review R8): stores collected with the same `seed_base` share their
`episode_seed` values, so a pooled probe has as many independent groups as distinct seeds,
not as many as episodes. The build prints that number and refuses a probe whose held-out
fold would fall below gate G6's minimum.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes §4.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

STEP_COLS = ("episode_seed", "t", "action", "satiation", "injury_level",
             "agent_row", "agent_col", "animal_row", "animal_col", "obs_noised")
EP_COLS = ("episode_seed", "episode_index", "length", "termination_reason", "animal_active")
TRUNCATED_REASON = 1          # termination_reason 1 = max_steps reached (trajectory_store)


@dataclass
class Probe:
    probe_id: str
    stores: list                 # store dirs (str)
    store_meta: list             # per store: checkpoint_path, D, breakdown, n taken, blocks
    # per episode (E,)
    ep_store: np.ndarray
    ep_seed: np.ndarray
    ep_T: np.ndarray
    ep_truncated: np.ndarray
    ep_offset: np.ndarray        # start of the episode's decision rows in the *_all arrays
    # every decision row of every probe episode, (store, episode, t) order (N,)
    obs_all: np.ndarray          # (N, D) float32, obs_noised — the network's own input
    action_next_all: np.ndarray  # (N,) int
    action_cur_all: np.ndarray   # (N,) int, -1 at t = 0
    t_all: np.ndarray
    # THE row index: positions into the *_all arrays of the sampled rows (sorted)
    rows: np.ndarray
    targets: dict                # name -> (n_rows,) at the sampled rows
    row_sha256: str = ""
    counts: dict = field(default_factory=dict)

    @property
    def row_store(self):
        return self.ep_store[self.row_episode]

    @property
    def row_episode(self):
        return np.searchsorted(self.ep_offset, self.rows, side="right") - 1

    @property
    def row_t(self):
        return self.t_all[self.rows]

    @property
    def row_seed(self):
        return self.ep_seed[self.row_episode]


def _read_store(store: Path, n: int):
    """First `n` episodes (by episode_index) of one store, from block 0 upward; ONE read of
    each shard."""
    import pyarrow.parquet as pq
    from src.utils.trajectory_store import (_list_column_to_2d, completed_blocks,
                                            read_manifest, shard_names)
    man = read_manifest(store)
    if int(man["schema_version"]) != 1:
        raise ValueError(f"{store}: schema_version {man['schema_version']} != 1")
    D, A = int(man["dims"]["D"]), int(man["dims"]["A"])
    blocks = sorted(completed_blocks(store))
    if not blocks or blocks[0] != 0:
        raise ValueError(f"{store}: block 0 is not complete")
    eps, steps, used = [], [], []
    have = 0
    for b in blocks:
        if have >= n:
            break
        if used and b != used[-1] + 1:
            raise ValueError(f"{store}: blocks are not contiguous from 0 ({used} then {b})")
        e_name, s_name = shard_names(b)
        et = pq.read_table(store / e_name, columns=list(EP_COLS))
        st = pq.read_table(store / s_name, columns=list(STEP_COLS))
        eps.append(et); steps.append((st, _list_column_to_2d)); used.append(b)
        have += et.num_rows
    if have < n:
        raise ValueError(f"{store}: only {have} complete episodes, probe needs {n}")

    ep = {}
    for c in ("episode_seed", "episode_index", "length", "termination_reason"):
        ep[c] = np.concatenate([t.column(c).to_numpy() for t in eps])
    ep["animal_active"] = np.concatenate(
        [_list_column_to_2d(t, "animal_active", A).astype(bool) for t in eps])
    s = {}
    for c in ("episode_seed", "t", "action", "satiation", "injury_level", "agent_row", "agent_col"):
        s[c] = np.concatenate([t.column(c).to_numpy(zero_copy_only=False) for t, _ in steps])
    for c, w in (("animal_row", A), ("animal_col", A), ("obs_noised", D)):
        s[c] = np.concatenate([f(t, c, w) for t, f in steps])
    order = np.argsort(ep["episode_index"], kind="stable")
    if not np.array_equal(ep["episode_index"][order], np.arange(len(order))):
        raise ValueError(f"{store}: episode_index of blocks {used} is not 0..{len(order)-1}")
    keep = order[:n]
    return man, used, {k: v[keep] for k, v in ep.items()}, s


def build(probe_id: str, stores: list, n_per_store: int, rows_per_episode: int, seed: int,
          *, test_frac: float, min_test_groups: int) -> Probe:
    """Build the probe. `test_frac` and `min_test_groups` are gate G6 / split constants
    passed in by the driver from the pinned rules' `parameters:`; this module holds none."""
    rng = np.random.default_rng(int(seed))
    n_per_store, rows_per_episode = int(n_per_store), int(rows_per_episode)
    if n_per_store < 1 or rows_per_episode < 1:
        raise ValueError("n_per_store and rows_per_episode must be >= 1")

    ep_store, ep_seed, ep_T, ep_trunc = [], [], [], []
    obs_l, an_l, ac_l, t_l = [], [], [], []
    tgt_l = {k: [] for k in ("satiation", "injury_level", "nearest_predator_manhattan",
                             "predator_valid")}
    store_meta, breakdowns = [], []
    for sid, store in enumerate(stores):
        store = Path(store)
        man, used, ep, s = _read_store(store, n_per_store)
        breakdowns.append((dict(sorted(man["observation_breakdown"].items())), int(man["dims"]["D"])))
        pred = np.array([c == "predator" for c in man["animal_classes"]], bool)
        # rows grouped by episode with t increasing by one: check, never assume
        seed_col, t_col = s["episode_seed"], s["t"].astype(np.int64)
        starts = np.flatnonzero(np.r_[True, seed_col[1:] != seed_col[:-1]])
        ends = np.r_[starts[1:], seed_col.size]
        first = {int(seed_col[a]): (a, b) for a, b in zip(starts, ends)}
        if len(first) != len(starts):
            raise ValueError(f"{store}: an episode's rows are not contiguous")
        for e in range(n_per_store):
            sd, T = int(ep["episode_seed"][e]), int(ep["length"][e])
            if sd not in first:
                raise ValueError(f"{store}: episode_seed {sd} has no step rows")
            a, b = first[sd]
            if b - a != T + 1:
                raise ValueError(f"{store}: seed {sd} has {b - a} rows, expected T+1 = {T + 1}")
            if not np.array_equal(t_col[a:b], np.arange(T + 1)):
                raise ValueError(f"{store}: seed {sd}: t is not 0..T contiguous")
            if int(s["action"][a]) != -1:
                raise ValueError(f"{store}: seed {sd}: row 0 action is not -1")
            dec = slice(a, a + T)                          # decision rows t = 0..T-1
            obs_l.append(s["obs_noised"][dec].astype(np.float32))
            an_l.append(s["action"][a + 1:a + T + 1].astype(np.int64))
            ac_l.append(s["action"][dec].astype(np.int64))
            t_l.append(t_col[dec])
            tgt_l["satiation"].append(s["satiation"][dec].astype(np.float64))
            tgt_l["injury_level"].append(s["injury_level"][dec].astype(np.float64))
            valid_slot = pred & ep["animal_active"][e]
            if valid_slot.any():
                d = (np.abs(s["animal_row"][dec][:, valid_slot] - s["agent_row"][dec, None])
                     + np.abs(s["animal_col"][dec][:, valid_slot] - s["agent_col"][dec, None]))
                tgt_l["nearest_predator_manhattan"].append(d.min(axis=1).astype(np.float64))
                tgt_l["predator_valid"].append(np.ones(T, bool))
            else:
                tgt_l["nearest_predator_manhattan"].append(np.full(T, np.nan))
                tgt_l["predator_valid"].append(np.zeros(T, bool))
            ep_store.append(sid); ep_seed.append(sd); ep_T.append(T)
            ep_trunc.append(int(ep["termination_reason"][e]) == TRUNCATED_REASON)
        store_meta.append({"store": str(store), "checkpoint_path": man["checkpoint_path"],
                           "run_path": man["run_path"], "D": int(man["dims"]["D"]),
                           "episodes_taken": n_per_store, "blocks_read": used,
                           "animal_classes": man["animal_classes"],
                           "policy_mode": man["policy_mode"], "obs_precision": man["obs_precision"],
                           # Revision 4 (R4-1): the collection's matmul mode and card. None marks
                           # a store collected before Revision 4 (the field is absent); it is
                           # never filled with a default.
                           "matmul_precision": man.get("matmul_precision"),
                           "compute_device_kind": man.get("compute_device_kind")})
    if len({json.dumps(b, sort_keys=True) for b in breakdowns}) != 1:
        raise ValueError(f"probe {probe_id}: stores differ in observation breakdown {breakdowns}")

    ep_T = np.asarray(ep_T, np.int64)
    ep_offset = np.r_[0, np.cumsum(ep_T)[:-1]].astype(np.int64)
    obs_all = np.concatenate(obs_l)
    t_all = np.concatenate(t_l)
    # --- THE row index: rows_per_episode distinct decision rows per episode, seeded ---
    rows = []
    for off, T in zip(ep_offset, ep_T):
        k = min(rows_per_episode, int(T))
        rows.append(off + np.sort(rng.choice(int(T), size=k, replace=False)))
    rows = np.concatenate(rows).astype(np.int64)
    if np.any(np.diff(rows) <= 0):
        raise AssertionError("row index is not strictly increasing")

    full = {k: np.concatenate(v) for k, v in tgt_l.items()}
    ep_seed_a, ep_store_a = np.asarray(ep_seed, np.int64), np.asarray(ep_store, np.int64)
    ep_trunc_a = np.asarray(ep_trunc, bool)
    row_ep = np.searchsorted(ep_offset, rows, side="right") - 1
    targets = {k: v[rows] for k, v in full.items()}
    targets["steps_remaining"] = (ep_T[row_ep] - t_all[rows]).astype(np.float64)
    targets["truncated"] = ep_trunc_a[row_ep]

    probe = Probe(probe_id=probe_id, stores=[str(s) for s in stores], store_meta=store_meta,
                  ep_store=ep_store_a, ep_seed=ep_seed_a, ep_T=ep_T, ep_truncated=ep_trunc_a,
                  ep_offset=ep_offset, obs_all=obs_all,
                  action_next_all=np.concatenate(an_l), action_cur_all=np.concatenate(ac_l),
                  t_all=t_all, rows=rows, targets=targets)
    probe.row_sha256 = row_index_sha256(probe)

    n_groups = int(np.unique(ep_seed_a).size)
    per_store = {str(s): int((ep_store_a == i).sum()) for i, s in enumerate(stores)}
    counts = {
        "episodes_per_store": per_store, "episodes": int(ep_T.size),
        "distinct_episode_seed_groups": n_groups,
        "decision_rows_total": int(ep_T.sum()), "rows_kept": int(rows.size),
        "rows_per_episode": rows_per_episode,
        "predator_valid_rows_kept": int(targets["predator_valid"].sum()),
        "truncated_episodes": int(ep_trunc_a.sum()),
        "groups_with_a_death_ended_episode": int(np.unique(ep_seed_a[~ep_trunc_a]).size),
        "g6_test_frac": test_frac, "g6_min_test_groups": min_test_groups,
        "expected_test_groups": n_groups * test_frac,
    }
    probe.counts = counts
    print(f"[probe_set] {probe_id}: episodes per store {per_store}; distinct episode_seed "
          f"groups = {n_groups}; expected held-out groups = {n_groups * test_frac:.1f} "
          f"(gate G6 minimum {min_test_groups})", flush=True)
    if n_groups * test_frac < min_test_groups:
        raise ValueError(
            f"probe {probe_id}: {n_groups} distinct episode_seed groups x test_frac {test_frac} "
            f"= {n_groups * test_frac:.1f} held-out groups, below gate G6's minimum "
            f"{min_test_groups}. Raise n_per_store (a manifest value set by experiment-designer).")
    return probe


def row_index_sha256(probe: Probe) -> str:
    """sha256 over (store_id, episode_seed, t) of the sampled rows."""
    h = hashlib.sha256()
    for a in (probe.row_store, probe.row_seed, probe.row_t):
        h.update(np.ascontiguousarray(np.asarray(a, np.int64)).tobytes())
    return h.hexdigest()


def save(probe: Probe, out_dir) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    npz = out_dir / f"probe_{probe.probe_id}.npz"
    arrays = {"ep_store": probe.ep_store, "ep_seed": probe.ep_seed, "ep_T": probe.ep_T,
              "ep_truncated": probe.ep_truncated, "ep_offset": probe.ep_offset,
              "obs_all": probe.obs_all, "action_next_all": probe.action_next_all,
              "action_cur_all": probe.action_cur_all, "t_all": probe.t_all, "rows": probe.rows}
    arrays.update({f"target__{k}": v for k, v in probe.targets.items()})
    tmp = npz.with_name(npz.name + ".tmp.npz")
    np.savez(tmp, **arrays)
    os.replace(tmp, npz)
    js = out_dir / f"probe_{probe.probe_id}.json"
    js.write_text(json.dumps({"probe_id": probe.probe_id, "stores": probe.stores,
                              "store_meta": probe.store_meta, "counts": probe.counts,
                              "n_groups": probe.counts["distinct_episode_seed_groups"],
                              "row_index_sha256": probe.row_sha256}, indent=1))
    return npz, js


def load(out_dir, probe_id: str) -> Probe:
    out_dir = Path(out_dir)
    meta = json.loads((out_dir / f"probe_{probe_id}.json").read_text())
    z = np.load(out_dir / f"probe_{probe_id}.npz")
    targets = {k[len("target__"):]: z[k] for k in z.files if k.startswith("target__")}
    p = Probe(probe_id=probe_id, stores=meta["stores"], store_meta=meta["store_meta"],
              ep_store=z["ep_store"], ep_seed=z["ep_seed"], ep_T=z["ep_T"],
              ep_truncated=z["ep_truncated"], ep_offset=z["ep_offset"], obs_all=z["obs_all"],
              action_next_all=z["action_next_all"], action_cur_all=z["action_cur_all"],
              t_all=z["t_all"], rows=z["rows"], targets=targets, counts=meta["counts"])
    p.row_sha256 = row_index_sha256(p)
    for sm in p.store_meta:
        if "matmul_precision" not in sm or "compute_device_kind" not in sm:
            raise ValueError(f"probe {probe_id}: built before Revision 4 (its store_meta lacks "
                             f"matmul_precision / compute_device_kind); rebuild it")
    if p.row_sha256 != meta["row_index_sha256"]:
        raise ValueError(f"probe {probe_id}: row index sha256 {p.row_sha256} != recorded "
                         f"{meta['row_index_sha256']}")
    return p
