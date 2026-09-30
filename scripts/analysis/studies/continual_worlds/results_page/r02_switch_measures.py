"""FIGURE r02 — Every switch of the three main sequences: drop, recovery and return, modulated minus
ordinary, read against each agent's own level and against one shared level, with the registered votes.

Sources (read, never recomputed):
  tmp/20260929_cw_main_verdict.json  per-switch readings as scored in CONTINUAL_WORLDS.md 10.3-10.4:
      S20_ord / S20_mod (first 20,000 episodes after the switch), dip_own_diff_pp, dip_common_diff_steps,
      rec_own_ep / rec_common_ep, the 5.5 noise yardstick `yard.thr`, the H-dip and H-rec votes
      (`rec_vote_literal` = the registered same-logged-row tie rule), and each return's diff / yardstick / vote.
  results/analysis/continual_worlds/pilot_readout.json  the read-out after the tie-rule fix: its H-dip and
      H-rec votes are asserted equal to the verdict file's, so the two sources cannot disagree silently.

Sign convention on every panel: RIGHT of zero favours the modulated agent.
  (a) first-20k survival, modulated minus ordinary (= minus the shared-level dip difference), steps;
  (b) own-level dip, ordinary's percent drop minus modulated's, percentage points;
  (c) recovery to 90 % of the level, ordinary's episodes minus modulated's (thousands; shared and own);
  (d) return, modulated's gain over its own first visit minus ordinary's, steps.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import _common as C

house = C.house; house.apply()
STEM = "r02_switch_measures"
V = C.load(C.VERDICT)
P = C.main_pairs()

VOTE = {"favourable": "mod.", "unfavourable": "ord.", "not counted": "—", "not counted (tie)": "tie"}

rows = []                                  # one per switch, in sequence / stage order
for s in ("P1", "P2", "P3"):
    ro_sw = P[s]["pair"]["switches"]
    assert len(V["switches"][s]) == len(ro_sw) == 4, s
    for sw, ro in zip(V["switches"][s], ro_sw):
        assert sw["switch"] == ro["switch"] and sw["stage"] == ro["stage"], (s, sw["switch"], ro["switch"])
        # the read-out (after the tie-rule fix) and the analyzer's scoring must give the same votes
        assert ro["H_dip"]["vote"] == sw["dip_vote"], (s, sw["switch"], ro["H_dip"], sw["dip_vote"])
        rv = "not counted (tie)" if ro["H_rec"]["vote"] == "not counted" and "tie" in ro["H_rec"]["reason"] else ro["H_rec"]["vote"]
        assert rv == sw["rec_vote_literal"] or (ro["H_rec"]["vote"] == "not counted" and sw["rec_vote_literal"].startswith("not counted")), \
            (s, sw["switch"], ro["H_rec"], sw["rec_vote_literal"])
        a, b = sw["switch"].split(" -> ")
        rows.append(dict(seq=s, sw=sw, label=f"{s}  {C.WORLD[a]} → {C.WORLD[b]}" + ("" if sw["visit"] == 1 else " (return)")))
n = len(rows)

fig = plt.figure(figsize=(9.9, 9.6))
H = 9.6
top, rowh = 0.93, 0.34 / H * 1.0            # figure-fraction height per row
y0 = top - n * rowh
L = 0.215
axA = fig.add_axes([L, y0, 0.20, n * rowh])
axB = fig.add_axes([L + 0.225, y0, 0.16, n * rowh])
axC = fig.add_axes([L + 0.41, y0, 0.20, n * rowh])
axV = fig.add_axes([L + 0.635, y0, 0.15, n * rowh])
ys = np.arange(n)[::-1]                      # first switch at the top
beyond = 0
for i, (y, r) in enumerate(zip(ys, rows)):
    sw = r["sw"]
    thr = sw["yard"]["thr"]
    d = -sw["dip_common_diff_steps"]
    axA.plot([-thr, thr], [y, y], color=C.BAND, lw=7, solid_capstyle="butt", zorder=1)
    bn = sw["dip_beyond_noise"]
    beyond += bn
    axA.plot([d], [y], "o", ms=6.5, color=house.INK if bn else house.INK, mfc=house.INK if bn else house.PAPER,
             mew=1.4, zorder=3)
    axB.plot([-sw["dip_own_diff_pp"]], [y], "o", ms=6.5, mfc=house.PAPER, mec=house.INK, mew=1.4, zorder=3)
    ro, rm = sw["rec_common_ep"]
    oo, om = sw["rec_own_ep"]
    for (u, v), mk in (((ro, rm), "o"), ((oo, om), "v")):
        dx = (u - v) / 1e3
        shown = min(dx, 145)
        axC.plot([shown], [y], mk, ms=6, color=house.INK,
                 mfc=C.GREY if mk == "o" else house.PAPER, mew=1.3, zorder=3)
        if dx > 145:
            axC.text(141, y - 0.2, f"{dx:.0f} →", ha="right", va="top", fontsize=C.SMALLEST_PT, color=house.INK)
    axV.text(0.02, y, VOTE[sw["dip_vote"]] + ("*" if bn else ""), ha="left", va="center",
             fontsize=C.SMALLEST_PT + 0.5, color=house.INK, transform=axV.get_yaxis_transform())
    axV.text(0.55, y, VOTE[sw["rec_vote_literal"]], ha="left", va="center",
             fontsize=C.SMALLEST_PT + 0.5, color=house.INK, transform=axV.get_yaxis_transform())
for ax, lim, xl, t in ((axA, 32, "steps", "(a) first 20k episodes"),
                       (axB, 25, "percentage points", "(b) own-level drop"),
                       (axC, 150, "thousand episodes sooner", "(c) recovery")):
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(-lim if ax is not axC else -30, lim)
    ax.axvline(0, color=house.INK_2 if hasattr(house, "INK_2") else C.GREY, lw=0.9, zorder=2)
    ax.grid(axis="x", visible=True); ax.grid(axis="y", visible=False)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["label"] for r in rows] if ax is axA else [], fontsize=C.SMALLEST_PT)
    ax.set_xlabel(xl, fontsize=C.SMALLEST_PT + 1)
    ax.set_title(t, fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
    for yy in (3.5, 7.5):
        ax.axhline(yy, color=house.RULE, lw=0.7)
    C.assert_ticks_dont_collide(ax, "x")
axC.set_xticks([0, 50, 100, 150]); axA.set_xticks([-30, -15, 0, 15, 30]); axB.set_xticks([-20, 0, 20])
axV.set_ylim(-0.6, n - 0.4); axV.axis("off")
axV.set_title("(votes)  drop  rec.", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)
for yy in (3.5, 7.5):
    axV.axhline(yy, color=house.RULE, lw=0.7, xmax=0.9)

# ---- returns ---------------------------------------------------------------------------------------
ret = [r for r in rows if "return" in r["sw"]]
m = len(ret)
axR = fig.add_axes([L, 0.16, 0.20 + 0.225 + 0.16, m * rowh])
yr = np.arange(m)[::-1]
axV2 = fig.add_axes([L + 0.635, 0.16, 0.15, m * rowh])
ret_bn = 0
for y, r in zip(yr, ret):
    R = r["sw"]["return"]
    axR.plot([-R["yard"]["thr"], R["yard"]["thr"]], [y, y], color=C.BAND, lw=7, solid_capstyle="butt", zorder=1)
    axR.plot([R["diff"]], [y], "o", ms=6.5, color=house.INK, mfc=house.INK if R["beyond_noise"] else house.PAPER,
             mew=1.4, zorder=3)
    ret_bn += R["beyond_noise"]
    axV2.text(0.02, y, VOTE[R["vote"]] + ("*" if R["beyond_noise"] else ""), ha="left", va="center",
              fontsize=C.SMALLEST_PT + 0.5, color=house.INK, transform=axV2.get_yaxis_transform())
axR.set_ylim(-0.6, m - 0.4); axR.set_xlim(-32, 32)
axR.axvline(0, color=C.GREY, lw=0.9, zorder=2)
axR.grid(axis="x", visible=True); axR.grid(axis="y", visible=False)
axR.set_yticks(yr)
axR.set_yticklabels([f"{r['seq']}  return to {C.WORLD[r['sw']['switch'].split(' -> ')[1]]}" for r in ret],
                    fontsize=C.SMALLEST_PT)
axR.set_xlabel("steps: modulated's gain over its first visit minus ordinary's", fontsize=C.SMALLEST_PT + 1)
axR.set_title("(d) return: level at the end of the second visit, relative to the first", fontsize=C.SMALLEST_PT + 1.5,
              loc="left", pad=8)
axR.set_xticks([-30, -15, 0, 15, 30])
C.assert_ticks_dont_collide(axR, "x")
axV2.set_ylim(-0.6, m - 0.4); axV2.axis("off")
axV2.set_title("(vote)", fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=8)

h = [Line2D([], [], marker="o", ms=6.5, color=house.INK, mfc=house.PAPER, ls="none", label="difference inside noise"),
     Line2D([], [], marker="o", ms=6.5, color=house.INK, ls="none", label="beyond noise (also * on the vote)"),
     Line2D([], [], marker="v", ms=6, color=house.INK, mfc=house.PAPER, ls="none", label="(c) own level"),
     Line2D([], [], marker="o", ms=6, color=house.INK, mfc=C.GREY, ls="none", label="(c) shared level (no yardstick)"),
     Patch(color=C.BAND, label="noise yardstick, ± per row")]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=C.SMALLEST_PT + 0.5,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.4, columnspacing=1.2)
fig.text(0.02, 0.985, "right of zero = favours the modulated agent;  votes: mod. = favours modulated, "
         "ord. = favours ordinary, tie / — = not counted", fontsize=C.SMALLEST_PT + 0.5, color=house.INK)

# ---- numbers for the prose -------------------------------------------------------------------------
w1 = next(r["sw"] for r in rows if r["seq"] == "P3" and r["sw"]["stage"] == 1)
p2r = next(r["sw"]["return"] for r in ret if r["seq"] == "P2" and r["sw"]["return"]["beyond_noise"])
diffs = [r["sw"]["return"]["diff"] for r in ret]
st3 = P["P3"]["ordinary"]["stages"][3], P["P3"]["modulated"]["stages"][3]
assert st3[0]["world"] == "winter" and st3[0]["visit"] == 2
C.record_numbers(STEM, {
    "winter_dip": C.fmt(-w1["dip_common_diff_steps"]), "winter_thr": C.fmt(w1["yard"]["thr"]),
    "winter_margin": C.fmt(-w1["dip_common_diff_steps"] - w1["yard"]["thr"]),
    "p2_ret": C.fmt(p2r["diff"]), "p2_ret_thr": C.fmt(p2r["yard"]["thr"]),
    "ret_min": C.fmt(min(diffs), sign=True), "ret_max": C.fmt(max(diffs), sign=True),
    "winter_ret_ord": C.fmt(st3[0]["level_last200k"]), "winter_ret_mod": C.fmt(st3[1]["level_last200k"]),
    "n_dip_beyond": str(beyond), "n_ret_beyond": str(ret_bn),
    "n_read": str(n + m), "n_beyond": str(beyond + ret_bn),
    "yard_floor": C.fmt(rows[0]["sw"]["yard"]["b"])})
assert len({r["sw"]["yard"]["b"] for r in rows}) == 1

C.record_kind(STEM, "training")
C.record_samples(STEM, [
    dict(what="switches (drop and recovery)", used=n, total=n,
         note="every switch of the three sequences; first 20,000 episodes after each switch"),
    dict(what="returns", used=m, total=m, note="each second visit; last 200,000 episodes of the visit"),
    dict(what="drop votes counted", used=sum(r["sw"]["dip_vote"] != "not counted" for r in rows), total=n,
         note="not counted when the own-level and shared-level readings disagree"),
    dict(what="recovery votes counted", used=sum(not r["sw"]["rec_vote_literal"].startswith("not counted") for r in rows),
         total=n, note="a tie when both agents recover in the same logged row, usually the first one")])
C.save(fig, STEM)
