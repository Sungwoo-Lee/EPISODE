"""Shared trajectory reader for the level-04 behaviour figures.

WHY THE RECORDINGS AND NOT THE SUMMARY CSVs. The probe sweep already writes a `bush_hiding`
column -- the share of the episode spent on a bush. That statistic cannot tell a PARKED agent from
a RESPONSIVE one: it reports 80% for an agent that never leaves a bush and 58% for one that enters
when a predator arrives, and reads as "the first one hides more". Every quantity here is therefore
computed from the step-by-step recordings, where standing on a bush WITH a predator two cells away
is a different event from standing on one in an empty world.

Computed once and cached to JSON, because six figures read the same numbers and each pass reads
thirty episodes per condition per arm off the NAS.
"""
import json, os, posixpath, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import src.utils.episode_bundle as EB   # noqa: E402  a checkpoint is a folder or its <step>.zip archive
SCRATCH = os.path.join(ROOT, "results/eval/avoidance/metrics_history_rppo_basicq2_wave2/_scratch")
CACHE = os.path.join(ROOT, "results/analysis/basicq2_w1/traj_level04.json")
FIG_ROOT = os.path.join(ROOT, "docs/experiments/active/basic_levels_q2_default/figures")

#: Ordered from an empty world to a real predator. The ORDER carries the argument in T1/T2 --
#: a flat profile across it means hiding is unconditional; a rising one means it is a response.
CONDS = [("avoid_none_inj00",                 "no animal"),
         ("avoid_rabbitwander_inj00",         "rabbit,\nwandering"),
         ("avoid_rabbitwander_predsmell_inj00","rabbit, wandering\n+ predator smell"),
         ("avoid_rabbit_inj00",               "rabbit,\nchasing"),
         ("avoid_pred_inj00",                 "predator")]
INJ_PAIR = [("avoid_none_inj00", "uninjured"), ("avoid_none_inj70", "injured")]
ARMS = ["control", "modulated"]
NEAR = 2            # Chebyshev cells; matches the probe predators' attack_range lower bound


def _episodes(arm, cond):
    base = os.path.join(SCRATCH, f"lvl04_{arm}", cond)
    if not os.path.isdir(base): return None, []
    cks = sorted(EB.step_names(base), key=int)
    if not cks: return None, []
    cell = EB.cell_path(base, cks[-1])
    recs = EB.members(cell, "*/*/recordings/*/episode_*.rec.gz")
    g = sorted({posixpath.dirname(r) for r in recs})        # recordings/<ck> folders holding episodes
    if not g: return cks[-1], []
    out = [EB.load_recording(cell, r) for r in recs if posixpath.dirname(r) == g[0]]
    return cks[-1], out


def _one(arm, cond):
    ck, eps = _episodes(arm, cond)
    if not eps: return None
    on_n = on_f = n_n = n_f = on_all = n_all = 0
    lens, inj0, injN = [], [], []
    for d in eps:
        sn = d["snapshots"]; lens.append(len(sn))
        inj0.append(float(sn[0]["injury_level"])); injN.append(float(sn[-1]["injury_level"]))
        for s in sn:
            a = np.asarray(s["agent_pos"], float)
            bush = np.asarray(s["obs_pos"], float)
            an = np.asarray(s["animal_pos"], float)
            if bush.size == 0: continue
            on = bool((np.abs(bush - a).sum(1) == 0).any())
            on_all += on; n_all += 1
            if an.size:
                if np.abs(an - a).max(1).min() <= NEAR: n_n += 1; on_n += on
                else:                                   n_f += 1; on_f += on
    f = lambda num, den: (100.0 * num / den) if den else None
    return dict(checkpoint=int(ck), episodes=len(eps), steps=n_all,
                hide=f(on_all, n_all), near=f(on_n, n_n), far=f(on_f, n_f),
                exposure=f(n_n, n_n + n_f) if (n_n + n_f) else None,
                length=float(np.mean(lens)),
                injury_change=float(np.mean(injN) - np.mean(inj0)))


def load(rebuild=False):
    if os.path.exists(CACHE) and not rebuild:
        return json.load(open(CACHE))
    out = {}
    for cond, _ in CONDS + INJ_PAIR:
        for arm in ARMS:
            r = _one(arm, cond)
            if r: out[f"{arm}|{cond}"] = r
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(out, open(CACHE, "w"), indent=1)
    return out


def record_samples(stem, rows):
    """Write `<stem>.data.txt` -- used/available, EMITTED by the script (guide 11b)."""
    os.makedirs(FIG_ROOT, exist_ok=True)
    with open(os.path.join(FIG_ROOT, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            fh.write(f"{r['what']}|{r['used']}|{r['total']}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")
