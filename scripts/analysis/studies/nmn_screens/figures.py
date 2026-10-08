#!/usr/bin/env python3
"""figures.py - figures of the 'Modulator Capacity and Input Screen' page (level-05 modulator screens).

Two one-seed (42) screens at level 05, tested like the fast-heal replication
(docs/experiments/active/hypervigilance/NMN_CAPACITY_GRID_L05.md, NMN_INPUT_L05.md):
  cap  9 settings: modulator memory size 32/64/128 x neurons sharing one gain 8/16/32
  inp  4 settings: the modulator reads felt injury only (N), fullness + felt injury (I),
       all body signals (IT), the outside world only (X)
Every setting is drawn against the replication's level-05 ordinary agent, seed 42 (same seed, same
world); the current modulated agent (size 16, grouping 1, reads everything), seed 42, is the reference row.

  effects --study S          the three effects of every setting beside the six level-05 references
                             (readout.py; neutral and own scenes)
  dose    --study S [--size H]   bush dwell against starting injury 0..90, rows = settings, four scenes
  train   --study S --cell C     ten injury lines across training, ordinary vs the setting

    $P scripts/analysis/studies/nmn_screens/figures.py --fig-dir <dir> --figure effects|dose|train ...
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readout as RO  # noqa: E402  (STUDY, rows, table, figure; RF = fast_heal_replication figures)

RF, HL, H = RO.RF, RO.HL, RO.H
AV = RO.AV


def _leaf(folder, scene_set, label):
    return f"{AV}/{folder}/l05_{scene_set}/{label}"


def register():
    """INJ_GRID keys: 'ref' = current modulated s42 vs ordinary s42; '<study>_<cell>' = setting vs ordinary s42."""
    rep = "metrics_history_rppo_healrep"
    ordin = {s: _leaf(rep, s, "l05_ordinary_s42") for s in ("grid", "gridchase")}
    HL.INJ_GRID["ref"] = ("current modulated agent, seed 42",
                          {"ordinary": ordin["grid"], "modulated": _leaf(rep, "grid", "l05_modulated_s42")},
                          {"ordinary": ordin["gridchase"], "modulated": _leaf(rep, "gridchase", "l05_modulated_s42")})
    for study, (folder, cells, name) in RO.STUDY.items():
        for c in cells:
            HL.INJ_GRID[f"{study}_{c}"] = (name(c),
                                           {"ordinary": ordin["grid"], "modulated": _leaf(folder, "grid", f"l05_{c}_s42")},
                                           {"ordinary": ordin["gridchase"], "modulated": _leaf(folder, "gridchase", f"l05_{c}_s42")})


def short(study, c):
    return f"size {c[1:c.index('g')]}, group {c[c.index('g') + 1:]}" if study == "cap" else \
        {"N": "reads felt injury only", "I": "reads fullness + felt injury", "IT": "reads all body signals",
         "X": "reads outside world only"}[c]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=["effects", "dose", "train"])
    ap.add_argument("--study", required=True, choices=list(RO.STUDY))
    ap.add_argument("--size", choices=["32", "64", "128"])
    ap.add_argument("--cell")
    a = ap.parse_args(argv)
    H.apply()
    register()
    d = os.path.abspath(a.fig_dir)
    if a.figure == "effects":
        T = RO.table(a.study)
        T.to_csv(os.path.join(d, f"screen_{a.study}_table.csv"), index=False, float_format="%.2f")
        for st in RO.SETS:
            fig, rows = RO.figure(T, st)
            HL.FG.record_samples(d, f"screen_{a.study}__{st}", rows)
            HL.FG.save(fig, d, f"screen_{a.study}__{st}")
        return
    if a.figure == "dose":
        cells = [c for c in RO.STUDY[a.study][1] if a.size is None or c.startswith(f"h{a.size}g")]
        keys = ["ref"] + [f"{a.study}_{c}" for c in cells]
        labels = ["current (16, group 1)" if a.study == "cap" else "current (reads all)"] + [short(a.study, c) for c in cells]
        fig, rows = HL.fig_injdose_seeds(keys, labels=labels)
        stem = f"screen_dose__{a.study}" + (f"_h{a.size}" if a.size else "")
    else:
        fig, rows = HL.fig_injtrain(f"{a.study}_{a.cell}")
        stem = f"screen_train__{a.study}_{a.cell}"
    HL.FG.record_samples(d, stem, rows)
    HL.FG.save(fig, d, stem)


if __name__ == "__main__":
    main()
