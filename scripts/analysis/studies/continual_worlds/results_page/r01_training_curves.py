"""FIGURE r01 — Survival over training in the three main sequences, both agents, switches marked.

Question: what did the two agents' survival actually do across the four world switches of each sequence?

Data: the six main sequence runs (P1, P2, P3 x ordinary / modulated), located through
results/analysis/continual_worlds/pilot_readout.json (runs of the three 'vote' pairs), their stage
boundaries from the same file, and their episode rows from the local WandB binaries read through the
read-out's own scan() / Series (so the curve and the read-out's numbers share one code path).

Curve: the 20,000-episode running mean of survival (steps alive per episode), restarted at every switch
exactly as the registered dip / recovery measures are (a window never straddles two worlds). Episode
rows are weighted by the episodes they cover, as in the read-out. Reward is never read.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
STEM = "r01_training_curves"
P = C.main_pairs()

fig = plt.figure(figsize=(9.9, 7.4))
gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.16, left=0.08, right=0.985, top=0.93, bottom=0.14)
axes = {"P1": fig.add_subplot(gs[0, 0]), "P2": fig.add_subplot(gs[0, 1]), "P3": fig.add_subplot(gs[1, :])}
YMAX = 280
rec, n_rows_used, n_rows_all = [], 0, 0
branch = {}
for s, ax in axes.items():
    lens = []
    for a in ("ordinary", "modulated"):
        run = P[s][a]
        rr = C.rows(run["wandb_dir"])
        n_rows_all += len(rr)
        b0 = run["stages"][1]["from"]          # the branch point = start of the first alternating stage
        branch.setdefault(s, b0)
        assert abs(b0 - branch[s]) < 1, (s, b0)
        used = 0
        for st in run["stages"]:
            if st.get("status") != "complete":
                assert st["stage"] == 0 and st.get("status") == "not reached", (run["tag"], st)
                continue            # stage 0 = Forage, trained before the branch; not part of these runs
            ser = C.stage_series(run, st["stage"], rr)
            x, y = C.running(ser)
            used += len(ser.e)
            ax.plot((x + st["from"] - b0) / 1e6, y, color=C.AGENT_COL[a], lw=1.25,
                    alpha=0.95 if a == "modulated" else 0.9, zorder=3 if a == "ordinary" else 2)
            assert y.max() < YMAX, (s, a, y.max())
        n_rows_used += used
        rec.append(dict(what=f"{s} {C.AGENT_LABEL[a]}: logged rows drawn", used=used, total=len(rr),
                        note="rows with a full 5,000-episode logging window inside stages 1 to 4; "
                             "the running mean starts 20,000 episodes after each switch"))
    run = P[s]["ordinary"]
    for i, st in enumerate(run["stages"][1:]):
        x0, x1 = (st["from"] - branch[s]) / 1e6, (st["to"] - branch[s]) / 1e6
        if i % 2 == 1:
            ax.axvspan(x0, x1, color=house.BG_SOFT, lw=0, zorder=0)
        if i:
            ax.axvline(x0, color=C.GREY, lw=0.9, ls=(0, (3, 2)), zorder=1)
        lab = C.WORLD[st["world"]] + ("\nreturn" if st["visit"] == 2 else "\nfirst visit")
        ax.text((x0 + x1) / 2, YMAX * 0.985, lab, ha="center", va="top", fontsize=C.SMALLEST_PT, color=house.INK)
        lens.append(x1)
    ax.set_xlim(0, max(lens))
    ax.set_ylim(0, YMAX)
    ax.set_yticks([0, 50, 100, 150, 200])
    ax.set_xticks(range(0, int(round(max(lens))) + 1))
    ax.tick_params(axis="x", pad=7)          # keeps the x '0' clear of the y '0' at the corner
    ax.set_title(f"{s}  {C.SEQ[s][1]}", fontsize=house.FS_BODY, loc="left", pad=6)
    ax.set_xlabel("episodes since the branch point (millions)", fontsize=C.SMALLEST_PT + 1)
    C.assert_ticks_dont_collide(ax, "x")
for s in ("P1", "P3"):
    axes[s].set_ylabel("survival (steps per episode)", fontsize=C.SMALLEST_PT + 1)
axes["P2"].set_yticklabels([])
h = [Line2D([], [], color=C.ORD, lw=2, label="ordinary agent"),
     Line2D([], [], color=C.MOD, lw=2, label="modulated agent"),
     Line2D([], [], color=C.GREY, lw=0.9, ls=(0, (3, 2)), label="world switch")]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=C.SMALLEST_PT + 0.5,
           bbox_to_anchor=(0.5, 0.0), handlelength=2.0)

C.record_kind(STEM, "training")
C.record_samples(STEM, rec)
SH = C.load(C.SHARED)
assert SH["seeds"] == [42, 42] and not SH["differing_main_arrays"]
C.record_numbers(STEM, {"rows_used": f"{n_rows_used:,}", "rows_all": f"{n_rows_all:,}",
                        "shared_same": str(SH["identical_main_arrays"]), "shared_of": str(SH["main_arrays_ordinary"])})
C.save(fig, STEM)
