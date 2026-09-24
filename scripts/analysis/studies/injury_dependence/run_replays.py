"""Batch driver: observation manipulation in REPLAY mode on the training-world stores (plan C3).

For every Wave 2 run with a 1M-episode final-checkpoint store, the first 2,000 recorded episodes are
fed back through the network with felt injury shifted (add +0.1..+0.5) or erased (x0, x0.5), in both
memory modes. GPU (replay parity tolerates only near-tie flips, logged in each manifest). Skips jobs
whose manifest.json exists; runs whose store is missing are reported and skipped.

  python scripts/analysis/studies/injury_dependence/run_replays.py --gpus 0 1
"""
import argparse, os, subprocess, sys, glob
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_manipulations import ROOT, PY, TOOL, EX, R, RUNS

STORE = "results/trajectories_basicq2_w2"
OUT = "results/analysis/injury_dependence/replay"
MANIPS = [("shift", "felt_injury_shift.yaml"), ("erase", "felt_injury_erase.yaml")]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpus", nargs="+", required=True)
    a = ap.parse_args()
    J = []
    for (lvl, arm), run in RUNS.items():
        if not glob.glob(os.path.join(ROOT, STORE, run, "*", "*", "_manifest.json")):
            print(f"  no store yet for {lvl}_{arm}; skipped"); continue
        for m, f in MANIPS:
            for mem in ("sustained", "one_step"):
                out = f"{OUT}/{lvl}_{arm}/{m}_{mem}"
                J.append((out, [PY, TOOL, "--mode", "replay", "--run", f"{R}/{run}", "--store", STORE,
                                "--episodes", "2000", "--memory", mem, "--device", "gpu",
                                "--manipulation", f"{EX}/{f}", "--out", out]))
    queues = {g: J[i::len(a.gpus)] for i, g in enumerate(a.gpus)}

    def worker(g):
        res = []
        for out, cmd in queues[g]:
            if os.path.exists(os.path.join(ROOT, out, "manifest.json")):
                res.append((out, "skip")); continue
            os.makedirs(os.path.join(ROOT, out), exist_ok=True)
            with open(os.path.join(ROOT, out, "log.txt"), "w") as log:
                rc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                    env={**os.environ, "CUDA_VISIBLE_DEVICES": g}).returncode
            res.append((out, "ok" if rc == 0 else f"FAIL rc={rc}")); print(res[-1], flush=True)
        return res
    with ThreadPoolExecutor(len(a.gpus)) as ex:
        allres = [r for rs in ex.map(worker, a.gpus) for r in rs]
    bad = [r for r in allres if r[1].startswith("FAIL")]
    print(f"done: {len(allres)} jobs, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
