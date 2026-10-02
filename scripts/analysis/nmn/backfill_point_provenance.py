"""Back-fill code provenance into B2 wake-up point files written before run_wakeup stamped it.

Plain-language purpose: the first GPU wake-up sweep (code f3291b93) wrote one JSON per grid
point carrying only the rules sha256, the settings, x, the seconds and a time stamp; the code
sha, the dirty flag, the evidence status and the device lived only in each run's `_done.json`.
A point file separated from its `_done.json` then had no provenance. run_wakeup now writes
those fields into every point record (run_wakeup.PROVENANCE_KEYS); this script copies them
from each run's `_done.json` into the point files that lack them. Metadata only: `measures`,
`settings`, `x`, `seconds` and the rules sha256 are never changed (checked after every write).

Refuses to run unless EVERY run of the manifest has its `_done.json`: a worker writes that file
only after its run's last point, so a run without it may still be being written. Run only after
the sweep has ended (both worker logs show `exit 0`).

Usage:
  python scripts/analysis/nmn/backfill_point_provenance.py --manifest M            # dry run
  python scripts/analysis/nmn/backfill_point_provenance.py --manifest M --write
  (M = docs/experiments/active/modulator_clues/algorithmic_null_wakeup.yaml)

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md (code review of
Stage 4, item 1).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.analysis.nmn import run_wakeup as rw   # noqa: E402

UNCHANGED = ("label", "x", "rules_sha256", "settings", "measures", "seconds", "generated_utc")


def plan_backfill(out: Path, labels: list) -> list:
    """[(point file, provenance to add)] for every point file lacking provenance. Raises if a
    run has no `_done.json`, if a point's rules sha256 differs from its `_done.json`, or if a
    point already carries provenance that disagrees with it."""
    missing = [l for l in labels if not (out / "points" / l / "_done.json").is_file()]
    if missing:
        raise RuntimeError(f"no _done.json for {missing}: the sweep may still be writing these "
                           f"runs; back-fill only after it has ended")
    todo = []
    for label in labels:
        d = out / "points" / label
        done = json.loads((d / "_done.json").read_text())
        prov = {k: done[k] for k in rw.PROVENANCE_KEYS}
        rules = done["decision_rules"]["sha256"]
        for pf in sorted(d.glob("*.json"), key=lambda p: p.name):
            if pf.name == "_done.json":
                continue
            rec = json.loads(pf.read_text())
            if rec["rules_sha256"] != rules:
                raise ValueError(f"{pf}: rules sha256 differs from {label}/_done.json")
            have = {k: rec[k] for k in rw.PROVENANCE_KEYS if k in rec}
            if any(have[k] != prov[k] for k in have):
                raise ValueError(f"{pf}: carries provenance {have} that differs from "
                                 f"_done.json {prov}")
            if set(have) != set(prov):
                todo.append((pf, prov))
    return todo


def apply_backfill(todo: list, source: str) -> int:
    """Add the provenance fields (and where they came from) to each file, atomically; every
    other field is checked unchanged after the write."""
    for pf, prov in todo:
        rec = json.loads(pf.read_text())
        new = {**rec, **prov, "provenance_backfilled": source}
        tmp = pf.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(new))
        os.replace(tmp, pf)
        back = json.loads(pf.read_text())
        if any(back.get(k) != rec.get(k) for k in UNCHANGED):
            raise AssertionError(f"{pf}: a non-provenance field changed during the back-fill")
    return len(todo)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--write", action="store_true", help="write (default: dry run)")
    args = ap.parse_args(argv)
    man = rw.load_manifest(rw._abs(args.manifest))
    out = rw._abs(man["out_root"]) / man["name"]
    todo = plan_backfill(out, [r["label"] for r in man["runs"]])
    print(f"[backfill] {len(todo)} point files lack provenance under {out}")
    if args.write and todo:
        src = ("copied from the run's _done.json by backfill_point_provenance.py at "
               + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        print(f"[backfill] wrote {apply_backfill(todo, src)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
