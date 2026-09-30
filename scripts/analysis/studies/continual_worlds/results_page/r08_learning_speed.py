"""FIGURE r08 — May replication, stage 1 (learning from scratch in the hunting world): survival against
training EPISODES and against training ENVIRONMENT STEPS, both agents, three seeds each. EXPLORATORY: this
reading (hint E2 of MAY_DOUBLE_RETURN_REPLICATION.md 10.7) was chosen after the data were seen.

Why both axes (plan-reviewer finding A3 on the May verdict): an agent that survives longer uses more
environment steps -- and so gets more training updates -- per episode, so at equal episode counts the
longer-surviving agent has trained more. The environment-step axis is the standard one in RL.

Sources: runs and stage-1 boundaries from results/analysis/continual_worlds/mayrep_readout.json; the
episode-axis areas `exploratory_post_data.auc_first100k / auc_first300k` of stage 1 from the same file
(per run, stages[0]); episode rows from the local WandB binaries through the read-out's own scan() / Series,
whose `cum_steps` (sum of episodes x survival from the stage start) gives the environment-step axis. The
step-axis means reproduce the reviewer's scratch computation: the episode-weighted mean survival over every
logged row whose cumulative environment steps are at most the target.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
STEM = "r08_learning_speed"
D = C.load(C.MAYREP)
runs = D["runs"]
LS = {42: "-", 43: (0, (5, 2)), 44: (0, (1.5, 1.5))}
EP_MAX, ST_MAX = 600_000, 150e6

fig = plt.figure(figsize=(9.9, 5.4))
axA = fig.add_axes([0.08, 0.27, 0.41, 0.63])
axB = fig.add_axes([0.575, 0.27, 0.41, 0.63])
per = {}
rec = []
for r in runs:
    st = r["stages"][0]
    assert st["stage"] == 0 and st["world"] == "active" and st["from"] == 0
    ser = C.stage_series(r, 0)
    x, y = C.running(ser)
    steps_at = np.array([ser.steps_to(ser.start + e) for e in x])
    kw = dict(color=C.AGENT_COL[r["agent"]], ls=LS[r["seed"]], lw=1.4)
    m = x <= EP_MAX
    axA.plot(x[m] / 1e3, y[m], **kw)
    m2 = steps_at <= ST_MAX
    axB.plot(steps_at[m2] / 1e6, y[m2], **kw)

    def mean_first_steps(target):
        k = ser.cum_steps <= target
        return float((ser.w[k] * ser.s[k]).sum() / ser.w[k].sum())

    def level_at_steps(target):
        idx = int(np.argmax(ser.cum_steps >= target)); e = float(ser.e[idx])
        return ser.S(e - 20_000, e)
    ex = st["exploratory_post_data"]
    per[r["run"]] = dict(agent=r["agent"], seed=r["seed"], a100k=ex["auc_first100k"], a300k=ex["auc_first300k"],
                         s10M=mean_first_steps(10e6), s30M=mean_first_steps(30e6),
                         lvl200k=ser.S(200_000 - 20_000, 200_000), lvl30M=level_at_steps(30e6), lvl60M=level_at_steps(60e6),
                         steps100k=ser.steps_to(100_000) / 1e6)
    rec.append(dict(what=f"run {r['run']} ({r['agent']}, seed {r['seed']}): stage-1 rows",
                    used=int(m.sum()), total=len(ser.e),
                    note="left panel: rows up to 600,000 episodes; right panel: rows up to 150 million environment steps"))
for ax, xl, t in ((axA, "training episodes (thousands)", "(a) against episodes"),
                  (axB, "training environment steps (millions)", "(b) against environment steps")):
    ax.set_ylim(0, 500); ax.set_yticks([0, 100, 200, 300, 400, 500])
    ax.axhline(500, color=C.GREY, lw=2.2, zorder=1)
    ax.set_xlabel(xl, fontsize=C.SMALLEST_PT + 1)
    ax.set_title(t, fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
    ax.tick_params(axis="x", pad=7)
axA.set_xlim(0, EP_MAX / 1e3); axB.set_xlim(0, ST_MAX / 1e6)
axA.axvline(100, color=C.GREY, lw=1.2, ls="-."); axB.axvline(10, color=C.GREY, lw=1.2, ls="-.")
axA.set_ylabel("survival (steps per episode)", fontsize=C.SMALLEST_PT + 1)
axB.set_yticklabels([])
for ax in (axA, axB):
    C.assert_ticks_dont_collide(ax, "x")
h = [Line2D([], [], color=C.ORD, lw=2, label="ordinary agent"), Line2D([], [], color=C.MOD, lw=2, label="modulated agent"),
     Line2D([], [], color=house.INK, lw=1.4, ls=LS[42], label="seed 42"),
     Line2D([], [], color=house.INK, lw=1.4, ls=LS[43], label="seed 43"),
     Line2D([], [], color=house.INK, lw=1.4, ls=LS[44], label="seed 44"),
     Line2D([], [], color=C.GREY, lw=2.2, label="500-step cap"),
     Line2D([], [], color=C.GREY, lw=1.2, ls="-.", label="end of the early window (100k episodes / 10M steps)")]
fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=C.SMALLEST_PT + 0.3,
           bbox_to_anchor=(0.5, 0.0), handlelength=2.0, columnspacing=1.2)

# ---- numbers ---------------------------------------------------------------------------------------
def mean_by(agent, k):
    return float(np.mean([v[k] for v in per.values() if v["agent"] == agent]))
def pairs_pos(k):
    seeds = sorted({v["seed"] for v in per.values()})
    g = lambda a, s: next(v[k] for v in per.values() if v["agent"] == a and v["seed"] == s)
    return sum(g("modulated", s) > g("ordinary", s) for s in seeds)
diff = {k: mean_by("modulated", k) - mean_by("ordinary", k) for k in ("a100k", "a300k", "s10M", "s30M", "lvl200k", "lvl30M", "lvl60M")}
# the episode-axis numbers must match the read-out's own aggregate
EX = D["mayrep"]["exploratory_post_data"]
pair_d = [next(st for st in p["stages"] if st["stage"] == 0)["auc_first100k"]["diff"] for p in EX["pairs"]]
assert abs(np.mean(pair_d) - diff["a100k"]) < 1e-6, (pair_d, diff["a100k"])
# E1 (death rate per episode in the hunting stages), carried here with the other exploratory hint
DR = EX["death_rate_last200k"]
hunt = [DR[k] for k in ("1", "3", "5")]
assert all(h["n_pairs_neg"] == 3 and h["favours"] == "modulated" for h in hunt)
nums = {f"{k}_diff": C.fmt(v, sign=True) for k, v in diff.items()}
nums.update({f"{k}_pos": str(pairs_pos(k)) for k in diff})
nums.update({"a100k_ord": C.fmt(mean_by("ordinary", "a100k")), "a100k_mod": C.fmt(mean_by("modulated", "a100k")),
             "s10M_ord": C.fmt(mean_by("ordinary", "s10M")), "s10M_mod": C.fmt(mean_by("modulated", "s10M")),
             "ratio_10M_100k": C.fmt(diff["s10M"] / diff["a100k"], 2),
             "steps100k_ord_min": C.fmt(min(v["steps100k"] for v in per.values() if v["agent"] == "ordinary")),
             "steps100k_ord_max": C.fmt(max(v["steps100k"] for v in per.values() if v["agent"] == "ordinary")),
             "steps100k_mod_min": C.fmt(min(v["steps100k"] for v in per.values() if v["agent"] == "modulated")),
             "steps100k_mod_max": C.fmt(max(v["steps100k"] for v in per.values() if v["agent"] == "modulated"))})
nums.update({"dr_min": C.fmt(-100 * max(h["mean_diff"] for h in hunt)), "dr_max": C.fmt(-100 * min(h["mean_diff"] for h in hunt)),
             "dr_ord_min": C.fmt(100 * min(h["mean_ord"] for h in hunt), 0), "dr_ord_max": C.fmt(100 * max(h["mean_ord"] for h in hunt), 0),
             "dr_s1": C.fmt(100 * hunt[0]["mean_diff"], sign=True)})
C.record_numbers(STEM, nums)
C.record_kind(STEM, "exploratory")
C.record_samples(STEM, rec)
C.save(fig, STEM)
