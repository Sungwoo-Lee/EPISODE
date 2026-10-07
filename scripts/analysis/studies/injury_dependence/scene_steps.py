"""Per-step summaries of the injury-grid scene recordings (plan B1, B2) -> one cache per run.

For each run, scene version, scene and starting injury in STARTS, the dwell sweep's own recordings
(`.rec.gz`, 30 episodes per checkpoint) of the newest N checkpoints are read and reduced to:
  bush[t]        share of episodes in the bush at snapshot t (alive episodes only), t = 0..100
  alive[t]       share of episodes still alive at t
  injury[t]      mean true injury at t
  felt[t]        mean felt injury at t (reconstructed from the injury history with the run's own
                 alpha kernel, exactly as the environment builds the interoceptive signal)
  exits          felt injury (0-100) at every bush exit: in the bush at t-1, out at t, no animal
                 within reach at t-1 (Chebyshev <= NEAR_D, the store scans' definition)
  stays          felt injury at every in-bush snapshot that was NOT followed by an exit (same filter),
                 so exits / (exits + stays) per felt-injury bin is the exit rate
  early_ck       per checkpoint: share of steps 1..EARLY spent in the bush (alive steps, all 30 episodes)
                 -- the injured phase, which the whole-episode sweep measure dilutes
Writes results/analysis/injury_dependence/scene_steps/<version>/<label>.npz.

  python scripts/analysis/studies/injury_dependence/scene_steps.py --procs 8 --last 20 [--versions core]

In the no-animal scene nothing is random, so its 30 episodes per checkpoint are identical copies;
there the only variation is across checkpoints.
"""
import argparse, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np, yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_manipulations import RUNS, VERSIONS, R          # noqa: E402
import src.utils.episode_bundle as EB                    # noqa: E402  checkpoint = folder or <step>.zip

EV = os.path.join(ROOT, "results/eval/avoidance")
OUT = os.path.join(ROOT, "results/analysis/injury_dependence/scene_steps")
SCENES = ("avoid_none", "avoid_pred", "avoid_rabbitwander")
STARTS = tuple(range(0, 100, 10))
EARLY = 25        # steps 1..EARLY: the injured phase (healing in cover is fast) and the store scans' window
NEAR_D = 2
T = 101


def kernel_for(run):
    cfg = yaml.safe_load(open(os.path.join(ROOT, R, run, "models", "config.yaml")))
    KL = int(cfg["sensory"]["interoceptive_kernel_length"]); TAU = float(cfg["sensory"]["interoceptive_kernel_tau"])
    k = np.arange(KL, dtype=np.float64); raw = (k / TAU) * np.exp(1.0 - k / TAU)
    return raw / raw.sum()


def felt_series(inj, kernel):
    """Felt injury at each snapshot: buffer of past injury levels (reset row excluded), alpha kernel."""
    f = np.zeros(len(inj))
    for t in range(len(inj)):
        for j in range(1, len(kernel)):
            if t - j >= 1:
                f[t] += kernel[j] * inj[t - j]
    return f


def one(job):
    ver, label, run, last = job
    kernel = kernel_for(run)
    base = os.path.join(EV, f"metrics_history_rppo_injurygrid_{ver}", "_scratch", label)
    out = {}
    for scene in SCENES:
        for s0 in STARTS:
            cdir = os.path.join(base, f"{scene}_inj{s0:02d}")
            cks = sorted(EB.step_names(cdir), key=int)[-last:] if os.path.isdir(cdir) else []
            bush = np.zeros(T); alive = np.zeros(T); inj = np.zeros(T); felt = np.zeros(T)
            exits, stays, n_ep, early_ck = [], [], 0, []
            for ck in cks:
                e_in = e_n = 0
                cell = EB.cell_path(cdir, ck)
                for m in EB.members(cell, f"*/{ck}/recordings/{ck}/episode_*.rec.gz"):   # sorted
                    S = EB.load_recording(cell, m)["snapshots"]; n = len(S); n_ep += 1
                    ag = np.array([s["agent_pos"] for s in S]); bpos = np.asarray(S[0]["obs_pos"][0])
                    ib = np.all(ag == bpos, axis=1)
                    il = np.array([s["injury_level"] for s in S], float); fl = felt_series(il, kernel)
                    bush[:n] += ib; alive[:n] += 1; inj[:n] += il; felt[:n] += fl
                    e_in += ib[1:EARLY + 1].sum(); e_n += len(ib[1:EARLY + 1])
                    if len(S[0]["animal_pos"]):
                        an = np.array([s["animal_pos"][0] for s in S])
                        near = np.max(np.abs(an - ag), axis=1) <= NEAR_D
                    else:
                        near = np.zeros(n, bool)
                    for t in range(1, n):
                        if ib[t - 1] and not near[t - 1]:
                            (exits if not ib[t] else stays).append(fl[t - 1])
                early_ck.append(e_in / max(e_n, 1))
            key = f"{scene}_inj{s0:02d}"
            with np.errstate(invalid="ignore"):
                out[key + "__bush"] = bush / np.maximum(alive, 1)
                out[key + "__injury"] = inj / np.maximum(alive, 1)
                out[key + "__felt"] = felt / np.maximum(alive, 1)
            out[key + "__alive"] = alive / max(n_ep, 1)
            out[key + "__exits"] = np.asarray(exits); out[key + "__stays"] = np.asarray(stays)
            out[key + "__early_ck"] = np.asarray(early_ck)
            out[key + "__n_episodes"] = np.asarray(n_ep); out[key + "__checkpoints"] = np.asarray([int(c) for c in cks])
    os.makedirs(os.path.join(OUT, ver), exist_ok=True)
    np.savez_compressed(os.path.join(OUT, ver, f"{label}.npz"), **out)
    return ver, label, sum(int(out[k]) for k in out if k.endswith("__n_episodes"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, required=True)
    ap.add_argument("--last", type=int, required=True, help="newest N checkpoints per condition")
    ap.add_argument("--versions", nargs="+", default=None, help="only these scene versions (e.g. core)")
    a = ap.parse_args()
    jobs = [(ver, f"{lv}_{arm}", run, a.last) for (lv, arm), run in RUNS.items() for ver in VERSIONS[lv]
            if a.versions is None or ver in a.versions]
    with ProcessPoolExecutor(a.procs) as ex:
        for ver, label, n in ex.map(one, jobs):
            print(f"  {ver:26} {label:16} {n} episodes", flush=True)


if __name__ == "__main__":
    main()
