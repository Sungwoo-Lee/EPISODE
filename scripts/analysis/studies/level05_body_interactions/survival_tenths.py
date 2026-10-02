#!/usr/bin/env python3
"""survival_tenths.py -- survival and starvation share per tenth of training, per run (LEVEL05 §7.5).

Plain language: for every run named in an analysis manifest's `wandb_ids`, how long did episodes last
(survival steps) in each tenth of training, and what share ended in starvation? Survival only; reward is
never read. Reads the LOCAL WandB binaries through `pilot_pick.py` (same folder: `read_history`,
`weighted` = `Episode/_window_n`-weighted mean over `Episode/Number` in a range, `wandb_dir_for`).
A run that has not reached its episode budget is still read (`allow_truncated`) and marked incomplete.

Usage: PY survival_tenths.py MANIFEST OUT_JSON
  e.g. MANIFEST docs/experiments/active/level05_body_interactions/analysis_manifest.yaml,
       OUT_JSON results/analysis/level05_body_interactions/survival_tenths.json
"""
import argparse
import importlib.util
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]      # scripts/analysis/studies/<study>/ -> repo root (three levels deep)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest"); ap.add_argument("out_json")
    a = ap.parse_args()
    sp = importlib.util.spec_from_file_location("pp", HERE / "pilot_pick.py")
    PP = importlib.util.module_from_spec(sp); sp.loader.exec_module(PP)
    mp = Path(a.manifest)
    man = yaml.safe_load((mp if mp.is_absolute() else ROOT / mp).read_text())
    out = {}
    for lab, wid in man["wandb_ids"].items():
        try:
            rows, cfg = PP.read_history(PP.wandb_dir_for({"id": lab, "wandb_id": wid}), allow_truncated=True)
        except Exception as e:
            out[lab] = {"error": str(e)}; continue
        N = int(cfg["episodes"]); reached = max(r["Number"] for r in rows)
        tenths = [PP.weighted(rows, i * N / 10, (i + 1) * N / 10, "Steps")[0] for i in range(10)]
        starve = [PP.weighted(rows, i * N / 10, (i + 1) * N / 10, "starve")[0] for i in range(10)]
        out[lab] = {"wandb_id": wid, "episodes": N, "reached": reached, "complete": reached >= N,
                    "S_tenths": tenths, "starve_tenths": starve}
        print(lab, "complete" if reached >= N else f"PARTIAL {reached:.0f}",
              [round(x) if x == x else None for x in tenths], flush=True)
    op = Path(a.out_json); op = op if op.is_absolute() else ROOT / op
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1))
    print(f"[survival_tenths] wrote {op}")


if __name__ == "__main__":
    main()
