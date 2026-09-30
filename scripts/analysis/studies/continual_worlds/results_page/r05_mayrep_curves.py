"""FIGURE r05 — May replication: survival over training for all six runs, the 500-step cap, and the share of
episodes that reached the cap.

Sources: results/analysis/continual_worlds/mayrep_readout.json (runs M1-M6, their stage boundaries, and the
per-stage cap share `mayrep.ceiling_check.per_run` = share of the last 200,000 episodes of the stage that
ended at the 500-step limit); episode rows from the six local WandB binaries through the read-out's own
scan() / Series. Curves: 20,000-episode running mean restarted at every stage switch. The cap-share curve uses
the logged `Episode/Term_MaxSteps` (share of episodes in the logging window that ended at the limit), the key
the ceiling check reads.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import _common as C

house = C.house; house.apply()
STEM = "r05_mayrep_curves"
D = C.load(C.MAYREP)
runs = D["runs"]
assert len(runs) == 6 and all(r["finished"] for r in runs)
CAPC = D["mayrep"]["ceiling_check"]["per_run"]
LS = {42: "-", 43: (0, (5, 2)), 44: (0, (1.5, 1.5))}

fig = plt.figure(figsize=(9.9, 9.4))
gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 0.8], hspace=0.42, left=0.1, right=0.98, top=0.95, bottom=0.11)
axA, axB, axC = (fig.add_subplot(gs[i]) for i in range(3))
rec = []
for r in runs:
    rr = C.rows(r["wandb_dir"])
    used = 0
    for st in r["stages"]:
        assert st["status"] == "complete", (r["run"], st["stage"])
        ser = C.stage_series(r, st["stage"], rr)
        used += len(ser.e)
        x, y = C.running(ser)
        xc, yc = C.running(ser, key="Episode/Term_MaxSteps")
        kw = dict(color=C.AGENT_COL[r["agent"]], lw=1.1, ls=LS[r["seed"]], alpha=0.9)
        axA.plot((x + st["from"]) / 1e6, y, **kw)
        axB.plot((x + st["from"]) / 1e6, y, **kw)
        axC.plot((xc + st["from"]) / 1e6, 100 * yc, **kw)
    rec.append(dict(what=f"run {r['run']} ({r['agent']}, seed {r['seed']}): logged rows drawn", used=used, total=len(rr),
                    note="rows with a full logging window in the five stages; running mean starts 20,000 episodes after each switch"))
st0 = runs[0]["stages"]
for ax in (axA, axB, axC):
    for st in st0:
        if st["world"] == "passive":
            ax.axvspan(st["from"] / 1e6, st["to"] / 1e6, color=house.BG_SOFT, lw=0, zorder=0)
    ax.set_xlim(0, st0[-1]["to"] / 1e6)
    ax.set_xticks(np.arange(0, 5.5, 0.5)); ax.tick_params(axis="x", pad=7)
    C.assert_ticks_dont_collide(ax, "x")
NAMES = ["1 hunting,\nfrom scratch", "2 harmless", "3 hunting,\nreturn 1", "4 harmless", "5 hunting,\nreturn 2"]
for st, nm in zip(st0, NAMES):
    axA.text((st["from"] + st["to"]) / 2e6, 30, nm, ha="center", va="bottom", fontsize=C.SMALLEST_PT, color=house.INK)
for ax in (axA, axB):
    ax.axhline(500, color=C.GREY, lw=2.2, zorder=1)
axA.set_ylim(0, 520); axA.set_yticks([0, 100, 200, 300, 400, 500])
axA.set_title("(a) survival, full scale", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=6)
axB.set_ylim(420, 505); axB.set_yticks([420, 440, 460, 480, 500])
axB.set_title("(b) the same curves, zoomed to 420–505 steps", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=6)
for ax in (axA, axB):
    ax.set_ylabel("survival (steps per episode)", fontsize=C.SMALLEST_PT + 1)
axC.axhline(80, color=C.GREY, lw=1.0, zorder=1)
axC.set_ylim(0, 100); axC.set_yticks([0, 20, 40, 60, 80, 100])
axC.set_ylabel("episodes at the cap (%)", fontsize=C.SMALLEST_PT + 1)
axC.set_title("(c) share of episodes that lasted the full 500 steps", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=6)
axC.set_xlabel("episodes since the start of training (millions)", fontsize=C.SMALLEST_PT + 1)
h = [Line2D([], [], color=C.ORD, lw=2, label="ordinary agent"), Line2D([], [], color=C.MOD, lw=2, label="modulated agent"),
     Line2D([], [], color=house.INK, lw=1.1, ls=LS[42], label="seed 42"),
     Line2D([], [], color=house.INK, lw=1.1, ls=LS[43], label="seed 43"),
     Line2D([], [], color=house.INK, lw=1.1, ls=LS[44], label="seed 44"),
     Line2D([], [], color=C.GREY, lw=2.2, label="500-step cap"),
     Line2D([], [], color=C.GREY, lw=1.0, label="(c) 80 % ceiling label"),
     Patch(color=house.BG_SOFT, label="harmless stage")]
fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, fontsize=C.SMALLEST_PT + 0.5,
           bbox_to_anchor=(0.5, 0.0), handlelength=2.2, columnspacing=1.4)

# ---- numbers ---------------------------------------------------------------------------------------
cap = {k: [CAPC[r["run"]][str(k)]["cap_frac_last200k"] for r in runs] for k in range(1, 6)}
hunt = cap[1] + cap[3] + cap[5]; harm = cap[2] + cap[4]
assert all(CAPC[r["run"]][str(k)]["ceiling_limited"] for r in runs for k in range(1, 6))
M = D["mayrep"]; MC = M["may_comparison"]
s1 = MC["reference_200k"]["S1_ord_mean"]
ret_ord = M["H_ret"]["3"]["mean_ord"]
C.record_numbers(STEM, {
    "cap_hunt_min": C.fmt(100 * min(hunt), 0), "cap_hunt_max": C.fmt(100 * max(hunt), 0),
    "cap_harm_min": C.fmt(100 * min(harm), 0), "cap_harm_max": C.fmt(100 * max(harm), 0),
    "n_stage_runs": str(sum(len(v) for v in cap.values())),
    "ret_ord": C.fmt(ret_ord), "room": C.fmt(500 - ret_ord, 0),
    "s1_ord": C.fmt(s1), "s1_ord_int": C.fmt(s1, 0),
    "may_need_3": C.fmt(MC["may"]["norm_adv"]["3"] * s1, 0), "may_need_5": C.fmt(MC["may"]["norm_adv"]["5"] * s1, 0)})
C.record_kind(STEM, "training")
C.record_samples(STEM, rec)
C.save(fig, STEM)
