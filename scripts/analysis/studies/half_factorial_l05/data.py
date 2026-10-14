#!/usr/bin/env python3
"""data.py - test-scene results of the level-05 half-factorial screen, one series per run.

Design: docs/experiments/active/hypervigilance/LOOKALIKE_HALF_FACTORIAL_L05.md. Eight training worlds
(world 1 = the lookalike world, worlds 2-8 change four setting groups A-D at "+"), each with an ordinary
and a modulated agent at seed 42, all tested in world 1's frozen scenes (user, 2026-10-13: "world 1's
scenes first"). World 1's seed-43 pair is kept as a seed-to-seed reference, never as a ninth world.

A run stopped and resumed under the same WandB run writes one result folder per session
(<label>, <label>_resumed, <label>_resumed2). series() merges them: rows are joined on the checkpoint
step, and a step present in two folders keeps the later session's row (none overlap in practice: the
resumed session starts at the checkpoint the earlier one stopped at, which only the earlier one tested).

Readout (c), the hypervigilance pattern (LOOKALIKE_ANIMALS_CLOSE_POUNCE.md, "What would count as a clue"):
  injury effect   = bush dwell(injured) - bush dwell(unhurt), per animal condition
  interaction     = injury effect with the wandering rabbit - injury effect with no animal
  rabbit (unhurt) = bush dwell(unhurt, rabbit) - bush dwell(unhurt, no animal)
each formed per checkpoint, summarised by the mean of the newest 20 checkpoints with a 95 % t-interval
on the effective sample size 20(1-r)/(1+r), r = lag-1 autocorrelation (no correction when r <= 0).
"""
from __future__ import annotations

import atexit
import functools
import glob
import os

import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
AV = os.path.join(ROOT, "results", "eval", "avoidance")
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "basicq2_waves"))
import window_profile as WP  # noqa: E402

WORLDS = list(range(1, 9))
AGENTS = ("ordinary", "modulated")
# design table "The eight worlds": the groups at their new value in each world (D = A x B x C)
NEW = {1: "", 2: "AD", 3: "BD", 4: "AB", 5: "CD", 6: "AC", 7: "BC", 8: "ABCD"}
GROUPS = {"A": "predator threat", "B": "food economy", "C": "hazard concealment", "D": "hazard load"}
GROUP_PLAIN = {"A": "one predator, 2-3 cell reach", "B": "fewer, bigger food items",
               "C": "rocks and traps invisible", "D": "fewer hazards, heavier traps"}
# interaction pairs are aliased in a half factorial: each column estimates the sum of two two-way terms
PAIRS = {"AB+CD": ("A", "B"), "AC+BD": ("A", "C"), "AD+BC": ("A", "D")}
SETS = ("grid", "gridchase", "neutral", "own")   # own = cold level-05 air, healing on only
INJ = [f"{i:02d}" for i in range(0, 100, 10)]
NEWEST = 20
SIGMA_C = 2.67   # registry spread of the injury-driven test measure, upper end (design, pass rule item 1)


def sign(world, group):
    return 1 if group in NEW[world] else -1


def folders(world, agent, heal, scene_set, seed=42):
    """Every result folder of one run (one per training session), oldest first."""
    if world == 1:
        base = "metrics_history_rppo_lookalike" + ("_noheal" if heal == "off" else "")
        return [os.path.join(AV, base, scene_set, f"lookalike_{agent}_s{seed}")]
    base = "metrics_history_rppo_lookalike_hf" + ("_noheal" if heal == "off" else "")
    lab = f"hf_w{world}_{agent}_s{seed}"
    fs = sorted(glob.glob(os.path.join(AV, base, scene_set, lab + "*")),
                key=lambda p: (len(os.path.basename(p)), p))   # <label>, <label>_resumed, <label>_resumed2
    return [f for f in fs if os.path.basename(f) == lab or os.path.basename(f).startswith(lab + "_resumed")]


# Optional on-disk cache ($HF_CACHE, a pickle): the test CSVs are ~1,000 small files on the NAS, slow to read
# when it is busy; every figure process would otherwise re-read them. Written at exit, read at import. Delete
# the file to force a fresh read after new test results land.
_CACHE_PATH = os.environ.get("HF_CACHE")
_DISK = {}
if _CACHE_PATH and os.path.exists(_CACHE_PATH):
    _DISK = pd.read_pickle(_CACHE_PATH)
_N_DISK = len(_DISK)


def _save_cache():
    if _CACHE_PATH and len(_DISK) > _N_DISK:
        pd.to_pickle(_DISK, _CACHE_PATH)


atexit.register(_save_cache)


@functools.lru_cache(maxsize=None)
def table(world, agent, heal, scene_set, scene, inj, seed=42):
    """All columns of one test, merged over the run's folders, indexed by checkpoint step."""
    key = (world, agent, heal, scene_set, scene, inj, seed)
    if key not in _DISK:
        _DISK[key] = _read_table(*key)
    return _DISK[key]


def _read_table(world, agent, heal, scene_set, scene, inj, seed):
    parts = []
    for k, f in enumerate(folders(world, agent, heal, scene_set, seed)):
        p = os.path.join(f, f"avoid_{scene}_inj{inj}.csv")
        if os.path.exists(p):
            d = pd.read_csv(p)
            d["_session"] = k
            parts.append(d)
    if not parts:
        raise SystemExit(f"missing test result: world {world} {agent} s{seed} healing {heal} "
                         f"{scene_set}/{scene} injury {inj}")
    d = pd.concat(parts).sort_values(["step", "_session"]).drop_duplicates("step", keep="last")
    return d.set_index("step").drop(columns="_session")


def dwell(world, agent, heal, scene_set, scene, inj, seed=42):
    """Bush dwell in percent (share of the 100 test steps on the bush) per checkpoint."""
    return table(world, agent, heal, scene_set, scene, inj, seed)["bush_hiding"].astype(float) * 100.0


def n_episodes(world, agent, heal, scene_set, seed=42):
    d = table(world, agent, heal, scene_set, "none", "00", seed)
    return int(d["n_episodes"].iloc[0]) if "n_episodes" in d.columns else 30


def contrast(world, agent, heal, kind, inj="70", seed=42):
    """Per-checkpoint contrast (percentage points of bush dwell) in the injury-grid scenes."""
    g = lambda sc, i: dwell(world, agent, heal, "grid", sc, i, seed)
    if kind == "interaction":
        v = (g("rabbitwander", inj) - g("rabbitwander", "00")) - (g("none", inj) - g("none", "00"))
    elif kind == "rabbit_unhurt":
        v = g("rabbitwander", "00") - g("none", "00")
    elif kind == "injury_none":
        v = g("none", inj) - g("none", "00")
    elif kind == "injury_rabbit":
        v = g("rabbitwander", inj) - g("rabbitwander", "00")
    else:
        raise ValueError(kind)
    return v.dropna().sort_index()


def newest(v, n=NEWEST):
    """Mean of the newest n checkpoints, 95 % t-interval on the lag-1-corrected effective sample size
    (the project's window_profile, the same estimator as the lookalike pilot and the smell studies)."""
    p = WP.window_profile(v.to_numpy(float), windows=[min(n, len(v))]).iloc[0]
    return {"mean": float(p["mean"]), "lo": float(p["lo"]), "hi": float(p["hi"]), "se": float(p["se"]),
            "r1": float(p["r1"]), "neff": float(p["n_eff"]), "n": int(p["window"]),
            "first_step": int(v.index[-n:][0]), "last_step": int(v.index[-1])}


def whole_training(v):
    """Checkpoint-wise view (project rule): share positive overall and over the second half, largest jump."""
    x = v.to_numpy(float)
    half = v[v.index >= v.index.max() / 2].to_numpy(float)
    return {"n_ckpt": len(x), "share_pos": float((x > 0).mean()), "share_pos_2nd_half": float((half > 0).mean()),
            "max_jump": float(np.abs(np.diff(x)).max()) if len(x) > 1 else 0.0}


def at_step(v, millions):
    """The contrast at the tested checkpoint nearest a training step (in millions), and that step."""
    j = int(np.argmin(np.abs(v.index.to_numpy(float) - millions * 1e6)))
    return float(v.iloc[j]), int(v.index[j])


def run_row(w, a, heal, inj, seed):
    """Readout (c) and its checks for one run."""
    it = contrast(w, a, heal, "interaction", inj, seed)
    ru = contrast(w, a, heal, "rabbit_unhurt", inj, seed)
    ni, nr = newest(it), newest(ru)
    wt = whole_training(it)
    row = {"world": w, "agent": a, "seed": seed, "new": NEW[w] or "-", "heal": heal, "inj": inj,
           "inter": ni["mean"], "inter_lo": ni["lo"], "inter_hi": ni["hi"], "inter_se": ni["se"],
           "inter_neff": ni["neff"], "rabbit": nr["mean"], "rabbit_lo": nr["lo"], "rabbit_hi": nr["hi"],
           "inj_none": newest(contrast(w, a, heal, "injury_none", inj, seed))["mean"],
           "inj_rabbit": newest(contrast(w, a, heal, "injury_rabbit", inj, seed))["mean"],
           **wt, "first_step": ni["first_step"], "last_step": ni["last_step"],
           "episodes": n_episodes(w, a, heal, "grid", seed)}
    for m in (6, 8, 10):
        row[f"inter_{m}M"], row[f"step_{m}M"] = at_step(it, m)
    row["signature"] = bool(row["inter_lo"] > 0 and row["inter"] > 1.4 and abs(row["rabbit"]) < abs(row["inter"]))
    return row


def run_table(heal, inj="70"):
    """One row per run (16 screen runs + world 1's seed-43 pair): readout (c) and its checks."""
    return pd.DataFrame([run_row(w, a, heal, inj, seed) for w in WORLDS for a in AGENTS
                         for seed in ((42, 43) if w == 1 else (42,))])


# Replication seeds of worlds 2-8 (design, "Seed 43 and 44 replication"). A run enters the page only when it has
# finished training and every one of its seven test folders holds the final checkpoint; until then it is listed
# with its training state. Read straight from disk (never from the cache) so a half-written test is not frozen.
EXTRA_SEEDS = (43, 44)
FOLDER_SETS = [("on", st) for st in SETS] + [("off", st) for st in SETS if st != "own"]
TRAIN_ROOT = os.path.join(ROOT, "results", "JAX_RecurrentPPO")
AGENT_TAG = {"ordinary": "t1none", "modulated": "t16quad"}


def newest_checkpoint(world, agent, seed):
    best = 0
    for d in glob.glob(os.path.join(TRAIN_ROOT, f"*_rppo_lookalike_hf_l05_w{world}_{AGENT_TAG[agent]}_s{seed}")):
        md = os.path.join(d, "models")
        best = max([best] + [int(c) for c in (os.listdir(md) if os.path.isdir(md) else []) if c.isdigit()])
    return best


def tested_complete(world, agent, seed):
    for heal, st in FOLDER_SETS:
        fs = folders(world, agent, heal, st, seed)
        ref = folders(world, agent, heal, st, 42)
        if not fs or not os.path.isdir(fs[-1]) or not ref:
            return False
        want = {f for f in os.listdir(ref[0]) if f.endswith(".csv")}
        have = {f for f in os.listdir(fs[-1]) if f.endswith(".csv")}
        if not want <= have:
            return False
        for f in want:
            if pd.read_csv(os.path.join(fs[-1], f), usecols=["step"])["step"].max() < 9_990_000:
                return False
    return True


@functools.lru_cache(maxsize=None)
def seed_status(world, agent, seed):
    """'tested' (finished and every test folder complete), 'testing', 'training' (with steps) or 'queued'."""
    ck = newest_checkpoint(world, agent, seed)
    if ck >= 9_990_000:
        return ("tested" if tested_complete(world, agent, seed) else "testing"), ck
    return ("training" if ck > 0 else "queued"), ck


def tested_seeds(world, agent):
    return [s for s in EXTRA_SEEDS if world > 1 and seed_status(world, agent, s)[0] == "tested"]


def seed_table(heal="off", inj="70"):
    """Seed 42 and every tested replication seed, worlds 2-8, plus world 1's seed pair as the reference."""
    rows = []
    for w in WORLDS:
        for a in AGENTS:
            for seed in ((42, 43) if w == 1 else (42, *tested_seeds(w, a))):
                rows.append(run_row(w, a, heal, inj, seed))
    return pd.DataFrame(rows)


def group_effects(rt):
    """The pre-registered group contrast for readout (c) (design, pass rule): per agent, mean of the 4 '+' worlds
    minus the 4 '-' worlds; pooled = mean over the two agents; bar = 2 x SD_contrast with
    SD_contrast = sqrt(sigma^2/4 + sum(SE_i^2)/64) over the 16 screen runs; the sign must also hold at
    the 6, 8 and 10 M checkpoints."""
    s = rt[rt.seed == 42]
    sd = float(np.sqrt(SIGMA_C ** 2 / 4 + (s["inter_se"] ** 2).sum() / 64))
    bar = 2 * sd
    out = []
    terms = [(g, (g,)) for g in GROUPS] + [(k, v) for k, v in PAIRS.items()]
    for name, gs in terms:
        sg = lambda w: int(np.prod([sign(w, g) for g in gs]))
        rec = {"term": name, "bar": bar, "sd": sd}
        for col, key in (("inter", "effect"), ("inter_6M", "e6"), ("inter_8M", "e8"), ("inter_10M", "e10")):
            per = {}
            for a in AGENTS:
                x = s[s.agent == a].set_index("world")[col]
                per[a] = float(np.mean([x[w] for w in WORLDS if sg(w) > 0]) - np.mean([x[w] for w in WORLDS if sg(w) < 0]))
            rec[key] = float(np.mean(list(per.values())))
            for a in AGENTS:
                rec[f"{key}_{a}"] = per[a]
        same_sign = all(np.sign(rec[k]) == np.sign(rec["effect"]) for k in ("e6", "e8", "e10"))
        rec["same_sign_6_8_10"] = bool(same_sign)
        rec["clears_bar"] = bool(abs(rec["effect"]) > bar)
        rec["agent_dependent"] = any(abs(rec[f"effect_{a}"]) > bar and np.sign(rec[f"effect_{a}"]) != np.sign(rec["effect"])
                                     for a in AGENTS)
        # world 1's scenes are a cross-test for worlds 2-8 (design, "Decisions on the scene questions", item 3):
        # a secondary result that cannot make a group pass, so no "worth replicating" verdict is issued here
        rec["verdict"] = "clears the bar" if rec["clears_bar"] and same_sign else "does not clear the bar"
        out.append(rec)
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    for heal in ("off", "on"):
        for inj in ("70", "10"):
            rt = run_table(heal, inj)
            print(f"\n=== healing {heal}, injury {inj}")
            print(rt[["world", "agent", "seed", "new", "inter", "inter_lo", "inter_hi", "rabbit", "inj_none", "inj_rabbit",
                      "share_pos", "share_pos_2nd_half", "n_ckpt", "signature"]].round(2).to_string(index=False))
            print(group_effects(rt)[["term", "effect", "effect_ordinary", "effect_modulated", "e6", "e8", "e10",
                                     "bar", "same_sign_6_8_10", "verdict"]].round(2).to_string(index=False))
