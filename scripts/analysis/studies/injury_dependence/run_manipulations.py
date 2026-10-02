"""Batch driver: observation manipulation in the injury-grid scenes, Wave 2 levels 02-06.

Plan: docs/experiments/active/modulator_clues/INJURY_DEPENDENCE_PLAN.md, workstream B (B3, B4).
One call of scripts/analysis/obs_manipulation/run.py --mode live per (run, world version, scene,
manipulation, memory mode), newest 20 checkpoints, 30 episodes, CPU (live mode on GPU diverges from
the dwell sweep at near-tie decisions, so CPU is the only device that reproduces it). Jobs run as
parallel single-threaded processes; a job whose manifest.json exists is skipped, so the driver can
be re-run to resume.

  ladder x {sustained, one_step}   felt injury set 0..0.9, uninjured start (inj00 scenes)
  shift  x {sustained}             felt injury add +0.1..+0.5, start injury 50 (natural rise and heal)

Every job runs the tool's own identity-vs-shadow check. Step-exact parity with the injury-grid
dwell sweep is checked separately, on a sample of jobs, once those sweeps have finished
(`--parity-sample`), because a partly finished sweep has no recordings for some checkpoints.

  python scripts/analysis/studies/injury_dependence/run_manipulations.py --procs 16 [--dry-run]
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PY = "/home/vncuser/miniconda3/envs/grid_world_pain/bin/python"
TOOL = "scripts/analysis/obs_manipulation/run.py"
EX = "scripts/analysis/obs_manipulation/examples"
PROBES = "configs/environment/experiment/behavior_probes/injury_grid"
OUT = "results/analysis/injury_dependence/manip"
EV = "results/eval/avoidance"
R = "results/JAX_RecurrentPPO"
RUNS = {
    ("lvl02", "control"): "20260922-182505_rppo_bq2cover_lvl02_t1none_s42",
    ("lvl02", "modulated"): "20260922-182509_rppo_bq2cover_lvl02_t16quad_s42",
    ("lvl03", "control"): "20260922-182514_rppo_bq2cover_lvl03_t1none_s42",
    ("lvl03", "modulated"): "20260922-182518_rppo_bq2cover_lvl03_t16quad_s42",
    ("lvl04", "control"): "20260922-182522_rppo_bq2cover_lvl04_t1none_s42",
    ("lvl04", "modulated"): "20260922-182527_rppo_bq2cover_lvl04_t16quad_s42",
    ("lvl05", "control"): "20260922-182534_rppo_bq2cover_lvl05_t1none_s42",
    ("lvl05", "modulated"): "20260922-182538_rppo_bq2cover_lvl05_t16quad_s42",
    ("lvl06", "control"): "20260922-182543_rppo_bq2cover_lvl06_t1none_s42",
    ("lvl06", "modulated"): "20260922-182547_rppo_bq2cover_lvl06_t16quad_s42",
}
ARMS = ("neutral", "cool", "fire_by_bush", "fire_away")
VERSIONS = {"lvl02": ["core"], "lvl03": ["core"], "lvl04": ["core"],
            "lvl05": [f"{a}_clean" for a in ARMS],
            "lvl06": [f"{a}_{b}" for a in ARMS for b in ("clean", "noise_matched")]}
SCENES = ("avoid_none", "avoid_pred", "avoid_rabbitwander")
MANIPS = [("ladder", "felt_injury_ladder.yaml", "inj00", "sustained", "steps"),
          ("ladder", "felt_injury_ladder.yaml", "inj00", "one_step", "summary"),
          ("shift", "felt_injury_shift.yaml", "inj50", "sustained", "summary")]


def jobs():
    for (lvl, arm), run in RUNS.items():
        for ver in VERSIONS[lvl]:
            for scene in SCENES:
                for mname, mfile, inj, mem, rec in MANIPS:
                    out = f"{OUT}/{ver}/{scene}_{inj}/{lvl}_{arm}/{mname}_{mem}"
                    cmd = [PY, TOOL, "--mode", "live", "--run", f"{R}/{run}", "--checkpoints", "last:20",
                           "--world", f"{PROBES}/{ver}/{scene}_{inj}.yaml",
                           "--manipulation", f"{EX}/{mfile}", "--memory", mem, "--episodes", "30",
                           "--device", "cpu", "--record", rec, "--out", out]
                    yield out, cmd


CLAIM_FRESH_S = 1800      # a log.txt touched this recently means another driver is running the job


def run_one(job):
    """Run one job unless it is finished or claimed. Several drivers (different nodes) can share the
    job list: a job is claimed atomically with an O_EXCL `claim` file, and a job an older driver
    started before claims existed is recognised by a recently written log.txt."""
    import time
    out, cmd = job
    d = os.path.join(ROOT, out)
    if os.path.exists(os.path.join(d, "manifest.json")):
        return out, "skip"
    os.makedirs(d, exist_ok=True)
    log_p = os.path.join(d, "log.txt")
    if os.path.exists(log_p) and time.time() - os.path.getmtime(log_p) < CLAIM_FRESH_S \
            and not os.path.exists(os.path.join(d, "claim")):
        return out, "busy"
    try:
        fd = os.open(os.path.join(d, "claim"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{os.uname().nodename} {os.getpid()} {time.time():.0f}\n".encode()); os.close(fd)
    except FileExistsError:
        return out, "claimed"
    with open(log_p, "w") as log:
        rc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        os.remove(os.path.join(d, "claim"))          # release, so a re-run can retry it
    return out, "ok" if rc == 0 else f"FAIL rc={rc}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--shards", default=None,
                    help="'i,j/k': run only jobs whose index mod k is in {i, j} (split across nodes)")
    ap.add_argument("--parity-sample", action="store_true",
                    help="re-run the ladder/sustained job of every run on one scene per version with "
                         "--check-against-sweep into a scratch dir; the sweeps must be complete")
    a = ap.parse_args()
    J = list(jobs())
    if a.parity_sample:
        P = []
        for out, cmd in J:
            ver, scene, label, m = out[len(OUT) + 1:].split("/")
            if m == "ladder_sustained" and scene == "avoid_none_inj00":
                pout = out.replace(OUT, OUT + "_parity", 1)
                sweep = f"{EV}/metrics_history_rppo_injurygrid_{ver}/_scratch/{label}/{scene}"
                P.append((pout, cmd[:cmd.index("--out") + 1] + [pout, "--check-against-sweep", sweep]))
        J = P
    if a.shards:
        mine, k = a.shards.split("/")
        mine = {int(x) for x in mine.split(",")}
        J = [j for n, j in enumerate(J) if n % int(k) in mine]
    print(f"{len(J)} jobs")
    if a.dry_run:
        for out, cmd in J[:3]:
            print(" ".join(cmd))
        return 0
    n_fail = 0
    with ThreadPoolExecutor(a.procs) as ex:
        for i, (out, status) in enumerate(ex.map(run_one, J), 1):
            n_fail += status.startswith("FAIL")
            if status in ("busy", "claimed"):
                continue
            print(f"[{i}/{len(J)}] {status:8} {out}", flush=True)
    print(f"done; {n_fail} failed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
