"""FIGURE C1 — Do the trained agents change how much they hide when the danger level changes?
(context-exploration study, Part 1; recordings of the two trained level-05 agents, 1,000,000 episodes each.)

One row per comparison; x = gap in the share of steps spent in cover (percentage points), dot = gap,
bar = 95 % bootstrap interval over episodes. Two agents (ordinary t1none: filled circle; modulator
t16quad: open square). Dotted lines at the pre-registered adaptation bar of +/- 5 points.

Rows, top to bottom:
  hidden danger — many (9-12) minus few (2-5) ambushers, matched on body state and time in episode;
                  the same with time replaced by steps since the last hit (sensitivity);
  sensed danger — 1 and 2 hunting predators minus none, matched on body state and time, then also
                  matched on the recorded animal-smell reading.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
SRC = os.path.join(C.ROOT, "results/analysis/context_exploration/part1_hidden_context.json")
d = json.load(open(SRC))
AG = {"ordinary": ("o", house.INK, "ordinary agent"), "modulator": ("s", "white", "modulator agent")}
BAR = 5.0   # pre-registered minimum gap (STUDY_PLAN Part 1)


def rows_for(a):
    h, g = a["hidden_axis"], a["sensed_threat_axis"]["gaps"]
    return [("many vs few ambushers\n(matched on body, time)", h["matched_body_time"]["cover"]),
            ("many vs few ambushers\n(matched on body, time since hit)", h["sensitivity_since_last_hit"]["cover"]),
            ("1 vs 0 predators\n(matched on body, time)", g["1_minus_0"]["matched_body_time"]["cover"]),
            ("1 vs 0 predators\n(also matched on smell)", g["1_minus_0"]["matched_body_time_smell"]["cover"]),
            ("2 vs 0 predators\n(matched on body, time)", g["2_minus_0"]["matched_body_time"]["cover"]),
            ("2 vs 0 predators\n(also matched on smell)", g["2_minus_0"]["matched_body_time_smell"]["cover"])]


labels = [r[0] for r in rows_for(d["per_agent"]["ordinary"])]
n = len(labels); y = np.arange(n)[::-1].astype(float)
fig, ax = plt.subplots(figsize=(10.0, 5.2))
ax.axvspan(-BAR, BAR, color=house.BG_SOFT, zorder=0, lw=0)
for x in (-BAR, BAR):
    ax.axvline(x, color=house.INK, lw=0.9, ls=":")
ax.axvline(0, color="#8a8f99", lw=0.8)
for j, (ag, (mk, fc, lab)) in enumerate(AG.items()):
    off = 0.14 if j == 0 else -0.14
    for i, (_, v) in enumerate(rows_for(d["per_agent"][ag])):
        lo, hi = v["ci95"]
        ax.plot([lo, hi], [y[i] + off] * 2, color=house.INK, lw=1.6, solid_capstyle="butt")
        ax.plot([v["gap_points"]], [y[i] + off], mk, mfc=fc, mec=house.INK, mew=1.3, ms=6.5,
                label=lab if i == 0 else None)
ax.axhline(3.5, color=house.RULE, lw=0.9)
ax.text(-3.0, 5.5, "hidden danger (not sensed)", fontsize=9.5, color=house.TEXT_LIGHT, va="center")
ax.text(-3.0, 3.35, "sensed danger", fontsize=9.5, color=house.TEXT_LIGHT, va="top")
ax.text(BAR + 0.3, -0.52, "adaptation bar\n(±5 points)", fontsize=9.5, color=house.INK, va="bottom")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.5)
ax.set_ylim(-0.6, n - 0.2); ax.set_xlim(-3.5, 25)
ax.set_xlabel("more time in cover when the danger is higher (percentage points)")
ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
fig.tight_layout(rect=(0, 0.07, 1, 1))
h_, l_ = ax.get_legend_handles_labels()
fig.legend(h_, l_, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)

C.record_kind("c1_hidden_context", "recordings")
rows = []
for ag in AG:
    a = d["per_agent"][ag]; band = a["ambusher_band_episodes"]
    rows.append(dict(what=f"{ag} agent: episodes in the few / many ambusher bands", used=band["low_2to5"] + band["high_9to12"],
                     total=a["episodes"], note=f"{band['excluded_6to8']:,} episodes with 6-8 ambushers left out by design"))
    cv = a["hidden_axis"]["coverage"]
    rows.append(dict(what=f"{ag} agent: steps in matched cells (ambusher rows)", used=cv["steps_in_counted_cells"],
                     total=cv["steps_total"], note=f"{cv['cells_counted']} of {cv['cells_total']} body/time cells had >= {d['min_steps_per_cell']} steps in both bands"))
    cs = a["sensed_threat_axis"]["gaps"]["2_minus_0"]["coverage_smell"]
    rows.append(dict(what=f"{ag} agent: steps in matched cells (2 vs 0 predators, smell-matched)", used=cs["steps_in_counted_cells"],
                     total=cs["steps_total"], note=f"{cs['cells_counted']} of {cs['cells_total']} body/time/smell cells counted"))
C.record_samples("c1_hidden_context", rows)
house.save(fig, os.path.join(C.FIG, "c1_hidden_context"), column_px=C.COLUMN_PX)
