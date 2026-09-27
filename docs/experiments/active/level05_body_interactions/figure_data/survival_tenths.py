import importlib.util, json, sys, yaml
from pathlib import Path
R = Path("/media/nas01/projects/Interoceptive-AI/grid_world_pain")
sp = importlib.util.spec_from_file_location("pp", R / "scripts/analysis/studies/level05_body_interactions/pilot_pick.py")
PP = importlib.util.module_from_spec(sp); sp.loader.exec_module(PP)
man = yaml.safe_load((R / "docs/experiments/active/level05_body_interactions/analysis_manifest.yaml").read_text())
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
    print(lab, "complete" if reached >= N else f"PARTIAL {reached:.0f}", [round(x) if x == x else None for x in tenths], flush=True)
(R / "results/analysis/level05_body_interactions/survival_tenths.json").write_text(json.dumps(out, indent=1))
