"""Figures of the rebalance-planner study (all from the ideal planner, not a trained agent).

R1 decision_balance  For each world (rows), the share of training start states on open ground whose
                     best choice is to hide in a bush (blue), go out to eat (green) or something else
                     (grey). x: share of start states (%). Dotted line: the pre-registered 20 % bar;
                     a world offers a real choice when both blue and green reach it.
R2 choice_maps       Best choice at open ground, food energy (x, 0-200) by injury (y, 0-100), body
                     temperature fixed at -2.5 deg (the middle of the start range), map without a warm
                     bush (59 % of episodes); pale = best and second-best within 0.5 return units.
R3 survival_causes   Outcome of 4,000 starts followed for 500 steps under the ideal policy (x: share of
                     starts, %): survived, or died of predator / trap / rock injury, starvation,
                     over-eating, cold. Pooled over the two maps.
R4 time_shares       Where the ideal policy spends its steps (x: share of all agent-steps, %): in a bush,
                     travelling, eating, warming on a fire ring, other time in the open.
R5 main_effects      Group main effects (x: mean of the four "+" worlds minus the four "-" worlds, in
                     percentage points) for the hide share, the go-out-to-eat share and survival.
R6 hazard_mapping    Left: predator lethal-encounter hazard per step outside a bush (deaths per 1,000
                     steps; y) by sight (detection range, x) for pounce 2 and 3, from 6.7 M level-05
                     episodes with one predator. Right: mean injury per travel step by source (x), per world.

R7 hungry_states     EXPLORATORY, not pre-registered: R1 restricted to start states with food energy below
                     the setpoint (< 100), where eating can help at all. x: share of those states (%).
R8 lever_sweep       EXPLORATORY, not pre-registered: world 8 (left) and world 4 (right) with one lever changed
                     at a time (rows); x: share of training start states on open ground (%) whose best
                     choice is hide / go out to eat / other (same scale in both panels). The bush-healing rows
                     are planner-only, for understanding only (training bush healing stays fixed).

  python figures.py
"""
import json, os, sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C
import rp

house = C.house; house.apply()
R = C.results(); W = R["worlds"]; MAP = rp.load_mappings()
ROWS = [t for t in C.ORDER if t in W]
LAB = {t: C.world_label(t, W[t]) for t in ROWS}
y = np.arange(len(ROWS))[::-1].astype(float)
N_START = 4000
_GN, _GT = np.linspace(0, 200, 51), np.linspace(-15, 15, 61)
_NT = int(((_GT >= -10 - 1e-9) & (_GT <= 5 + 1e-9)).sum())
N_STARTS, N_HUNGRY = 51 * 26 * _NT, int((_GN < 100).sum()) * 26 * _NT     # planner grid 51 x 26 x 61


def finish(fig, stem, kind, samples):
    C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
    C.record_kind(stem, kind); C.record_samples(stem, samples)
    house.save(fig, os.path.join(C.FIG, stem), column_px=C.COLUMN_PX)
    plt.close(fig)


def start_state_rows(note):
    n = json.load(open(os.path.join(C.FIG, "worlds", "level05.json")))["per_map"]["warm0"]["decision_open"]
    return [dict(what=f"{LAB[t]}: training start states x 2 maps", used=2 * n["n"], total=2 * n["n_start"], note=note)
            for t in ROWS]


# ---- R1 ------------------------------------------------------------------------------------------
def dots(stem, rows, labels, key, xlabel, right, note, kind="planner"):
    yy = np.arange(len(rows))[::-1].astype(float)
    fig, ax = plt.subplots(figsize=(8.6, 0.42 * len(rows) + 1.6))
    for d, mk in (("hide", "o"), ("forage", "s"), ("other", "D")):
        ax.plot([100 * W[t][key][d] for t in rows], yy, mk, ls="none", ms=7.5,
                color=C.DECISION_COLOURS[d], mec=house.INK if d == "other" else C.DECISION_COLOURS[d], mew=0.6,
                label=C.DECISION_LABEL[d], zorder=3)
    for t, y0 in zip(rows, yy):
        ax.plot([0, 100], [y0, y0], color=house.TICK_LINE, lw=0.6, zorder=1)
        txt, strong = right(t)
        ax.text(101.5, y0, txt, va="center", fontsize=9.5, color=house.INK if strong else house.TEXT_LIGHT)
    ax.axvline(20, color=house.INK, lw=0.9, ls=":")
    ax.set_yticks(yy); ax.set_yticklabels([labels[t] for t in rows])
    ax.set_xlim(0, 122); ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel(xlabel); ax.grid(axis="y", visible=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.legend(handles=ax.get_legend_handles_labels()[0] + [Line2D([], [], color=house.INK, lw=0.9, ls=":",
               label="20 % mark (descriptive only here)")], loc="lower center", ncol=2, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, 0.0))
    finish(fig, stem, kind, note)


def r7():
    both = lambda t: (W[t]["exploratory_decision_open_hungry"]["hide"] >= 0.2
                      and W[t]["exploratory_decision_open_hungry"]["forage"] >= 0.2)
    dots("r7_hungry_states", ROWS, LAB, "exploratory_decision_open_hungry",
         "EXPLORATORY: share of hungry start states (food < 100) on open ground (%)",
         lambda t: (f"eat best in {100 * W[t]['exploratory_decision_open_hungry']['forage']:.0f} %", t == "level05"),
         [dict(what=f"{LAB[t]}: hungry start states x 2 maps", used=2 * N_HUNGRY, total=2 * N_STARTS,
               note="start states with food energy below 100 only (EXPLORATORY, not pre-registered); open ground; ties kept")
          for t in ROWS])


def r8():
    levers = ["", "_pred0.5", "_pred2", "_trip4", "_trip6", "_trip8", "_heal12.5", "_heal5"]
    names = {"": "as designed (trip to food 5)", "_pred0.5": "predator hit odds x0.5", "_pred2": "predator hit odds x2",
             "_trip4": "trip to food 4", "_trip6": "trip to food 6", "_trip8": "trip to food 8",
             "_heal12.5": "bush healing 12.5 (planner only)", "_heal5": "bush healing 5 (planner only)"}
    yy = np.arange(len(levers))[::-1].astype(float)
    fig, ax = plt.subplots(1, 2, figsize=(9.6, 4.9), sharey=True)
    samples = []
    for j, base in enumerate(("w8", "w4")):
        for d, mk in (("hide", "o"), ("forage", "s"), ("other", "D")):
            ax[j].plot([100 * W[base + l]["decision_open"][d] for l in levers], yy, mk, ls="none", ms=7,
                       color=C.DECISION_COLOURS[d], mec=house.INK if d == "other" else C.DECISION_COLOURS[d],
                       mew=0.6, label=C.DECISION_LABEL[d], zorder=3)
        for l, y0 in zip(levers, yy):
            ax[j].plot([0, 100], [y0, y0], color=house.TICK_LINE, lw=0.6, zorder=1)
            dd = W[base + l]["decision_open"]
            if dd["hide"] >= 0.2 and dd["forage"] >= 0.2:
                ax[j].text(99, y0, "both at least 20 %", ha="right", va="center", fontsize=9.5, color=house.INK)
            samples.append(dict(what=f"from world {base[1]}: {names[l]} (start states x 2 maps)", used=2 * N_STARTS,
                                total=2 * N_STARTS, note="EXPLORATORY single-lever sweep, not pre-registered; bush "
                                "healing is planner-only, for understanding only"))
        ax[j].axvline(20, color=house.INK, lw=0.9, ls=":")
        ax[j].set_xlim(0, 100); ax[j].set_xticks([0, 20, 40, 60, 80, 100]); ax[j].grid(axis="y", visible=False)
        ax[j].set_title(f"one lever changed from world {base[1]}", loc="left", fontsize=10.5)
        ax[j].set_xlabel("share of start states (%)")
    ax[0].set_yticks(yy); ax[0].set_yticklabels([names[l] for l in levers])
    fig.tight_layout(rect=(0, 0.12, 1, 1), w_pad=1.2)
    fig.legend(handles=ax[0].get_legend_handles_labels()[0] + [Line2D([], [], color=house.INK, lw=0.9, ls=":",
               label="20 % mark")], loc="lower center", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
    finish(fig, "r8_lever_sweep", "planner", samples)


def r1():
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for d, mk in (("hide", "o"), ("forage", "s"), ("other", "D")):
        ax.plot([100 * W[t]["decision_open"][d] for t in ROWS], y, mk, ls="none", ms=7.5,
                color=C.DECISION_COLOURS[d], mec=house.INK if d == "other" else C.DECISION_COLOURS[d], mew=0.6,
                label=C.DECISION_LABEL[d], zorder=3)
    for t, yy in zip(ROWS, y):
        ax.plot([0, 100], [yy, yy], color=house.TICK_LINE, lw=0.6, zorder=1)
        ax.text(101.5, yy, "real choice" if W[t]["real_choice"] else "one-sided", va="center", fontsize=9.5,
                color=house.INK if W[t]["real_choice"] else house.TEXT_LIGHT)
    ax.axvline(20, color=house.INK, lw=0.9, ls=":")
    ax.set_yticks(y); ax.set_yticklabels([LAB[t] for t in ROWS])
    ax.set_xlim(0, 118); ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("share of training start states on open ground (%)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.legend(handles=ax.get_legend_handles_labels()[0] + [Line2D([], [], color=house.INK, lw=0.9, ls=":",
               label="20 % bar (pre-registered)")], loc="lower center", ncol=2, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, 0.0))
    finish(fig, "r1_decision_balance", "planner", start_state_rows(
        "every grid state with body temperature -10..+5 (the start range), agent on open ground; ties kept (margin 0)"))


# ---- R2 ------------------------------------------------------------------------------------------
def r2():
    T0 = -2.5
    fig, axs = plt.subplots(3, 3, figsize=(9.6, 8.4), sharex=True, sharey=True)
    cmap = [np.array(to_rgb(C.DECISION_COLOURS[d])) for d in rp.DECISIONS]
    samples = []
    for ax, t in zip(axs.ravel(), ROWS):
        z = np.load(os.path.join(C.FIG, "worlds", f"{t}.npz"))
        g = z["grid"]; GN, GI, GT = np.linspace(0, 200, g[0]), np.linspace(0, 100, g[1]), np.linspace(-15, 15, g[2])
        code = z["code_warm0"].reshape(*g); tie = z["tie_warm0"].reshape(*g)
        k = int(np.argmin(np.abs(GT - T0)))
        img = np.stack([cmap[c] for c in code[:, :, k].T.ravel()]).reshape(len(GI), len(GN), 3)
        img = np.where(tie[:, :, k].T[..., None], 1 - 0.45 * (1 - img), img)
        ax.imshow(img, origin="lower", aspect="auto", extent=(GN[0], GN[-1], GI[0], GI[-1]), interpolation="nearest")
        ax.set_title(LAB[t], loc="left", fontsize=10); ax.grid(False)
        ax.set_xticks([0, 100, 200]); ax.set_yticks([0, 50, 100])
        samples.append(dict(what=LAB[t], used=int(len(GN) * len(GI)), total=int(code.size),
                            note=f"one temperature slice ({GT[k]:+.1f} deg) of all grid states; map without a warm bush; open ground"))
    fig.supxlabel("food energy (0-200; 100 = setpoint)", y=0.065, fontsize=11)
    fig.supylabel("injury (0-100; 100 = death)", x=0.005, fontsize=11)
    fig.tight_layout(h_pad=1.0, w_pad=0.6, rect=(0.02, 0.07, 1, 1))
    pale = tuple(1 - 0.45 * (1 - np.array(to_rgb(C.DECISION_COLOURS["hide"]))))
    fig.legend(handles=[Patch(color=C.DECISION_COLOURS[d], label=C.DECISION_LABEL[d]) for d in rp.DECISIONS]
               + [Patch(color=pale, label="pale: near-tie (within 0.5)")], loc="lower center", ncol=2,
               frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
    finish(fig, "r2_choice_maps", "planner", samples)


# ---- R3 / R4 stacked bars --------------------------------------------------------------------------
def stacked(stem, parts, colours, labels, getter, xlabel, note):
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    left = np.zeros(len(ROWS))
    for p, col, lab in zip(parts, colours, labels):
        v = np.array([100 * getter(W[t], p) for t in ROWS])
        ax.barh(y, v, left=left, color=col, height=0.66, label=lab, edgecolor=house.PAPER, lw=0.6)
        for yy, l0, vv in zip(y, left, v):
            if vv >= 7:
                ax.text(l0 + vv / 2, yy, f"{vv:.0f}", ha="center", va="center", fontsize=9,
                        color="white" if col not in ("#b8bcc4", "#d9dcd8", "#e6e1d3", "#e9bccb", "#c96f8f") else house.INK)
        left += v
    ax.set_yticks(y); ax.set_yticklabels([LAB[t] for t in ROWS]); ax.set_xlim(0, 100)
    ax.set_xlabel(xlabel); ax.grid(axis="y", visible=False)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    fig.legend(loc="lower center", ncol=4, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
    finish(fig, stem, "planner", [dict(what=f"{LAB[t]}: rollouts x 2 maps", used=2 * N_START, total=2 * N_START, note=note)
                                   for t in ROWS])


def r3():
    parts = ["survived"] + [c for c in rp.DEATHS if any(W[t]["death_share_of_starts"][c] > 0 for t in ROWS)]
    get = lambda w, p: w["survival"] if p == "survived" else w["death_share_of_starts"][p]
    stacked("r3_survival_causes", parts, [C.DEATH_COLOURS[p] for p in parts], [C.DEATH_LABEL[p] for p in parts],
            get, "share of starts (%)", "random training-style starts on open ground, 500 steps, pooled 0.59 / 0.41 over the two maps")


def r4():
    stacked("r4_time_shares", rp.TIME_KEYS, [C.TIME_COLOURS[k] for k in rp.TIME_KEYS],
            ["in a bush", "travelling", "eating", "warming on a fire ring", "other, in the open"],
            lambda w, p: w["time_share"][p], "share of all agent-steps (%)",
            "all steps lived by the rollouts (shares of agent-steps); a trip's arrival step into a bush counts as bush")


# ---- R5 ------------------------------------------------------------------------------------------
def r5():
    E = R["main_effects"]
    mets = [("hide share (open ground)", "hide share", house.BLUE, "o"),
            ("forage share (open ground)", "go-out-to-eat share", house.GREEN, "s"),
            ("survival at 500 steps", "survival", C.DEATH_COLOURS["survived"], "D")]
    groups = ["A", "B", "C", "D"]
    gl = {"A": "A  predator setting\n(lower model hazard)", "B": "B  food economy\n(fewer, bigger items)",
          "C": "C  hazards invisible", "D": "D  hazard load\n(fewer, harder traps)"}
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    yy = np.arange(len(groups))[::-1].astype(float)
    for j, (k, lab, col, mk) in enumerate(mets):
        ax.barh(yy + (1 - j) * 0.26, [100 * E[k][g] for g in groups], height=0.24, color=col, label=lab,
                edgecolor=house.INK_2 if k.startswith("survival") else col, lw=0.6)
    ax.axvline(0, color=house.INK, lw=0.8)
    ax.set_yticks(yy); ax.set_yticklabels([gl[g] for g in groups])
    ax.set_xlabel("main effect: mean of '+' worlds minus mean of '-' worlds (percentage points)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.legend(loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
    finish(fig, "r5_main_effects", "planner", [dict(what="half-factorial worlds", used=8, total=9,
           note="level 05 reference and trip-4 sensitivity worlds excluded; each world = 2 maps x (all start states, 4,000 rollouts)")])


# ---- R6 ------------------------------------------------------------------------------------------
def r6():
    lam = MAP["lam_by_sight_pounce"]
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 4.6), gridspec_kw=dict(width_ratios=[1, 1.25]))
    for r in (2, 3):
        st = C.POUNCE_STYLE[r]; xs = list(range(1, 8))
        ax[0].plot(xs, [1000 * lam[f"{d},{r}"]["lam_pred"] for d in xs], color=st["color"], ls=st["ls"], lw=1.8,
                   label=f"pounce reach {r}")
    ax[0].set_xlabel("predator sight (detection range, cells)")
    ax[0].set_ylabel("injury deaths per 1,000 steps outside a bush")
    ax[0].set_xticks(range(1, 8)); ax[0].set_ylim(0, None)
    ax[0].legend(frameon=False, fontsize=9.5, loc="upper left", handlelength=2.6)
    src_col = C.DEATH_COLOURS
    left = np.zeros(len(ROWS))
    for s in rp.SOURCES:
        v = []
        for t in ROWS:
            h = MAP["worlds"][t]["hazard"]["move"][s]
            v.append(h["p"] * sum(q * x for q, x in h["bins"]))
        v = np.array(v)
        ax[1].barh(y, v, left=left, color=src_col[s], height=0.66, label=C.DEATH_LABEL[s], edgecolor=house.PAPER, lw=0.6)
        left += v
    ax[1].set_yticks(y); ax[1].set_yticklabels([LAB[t] for t in ROWS])
    ax[1].set_xlabel("mean injury per travel step outside a bush"); ax[1].grid(axis="y", visible=False)
    ax[1].legend(frameon=False, fontsize=9.5, loc="upper right")   # top rows (level 05 - world 4) end below 1.0
    fig.tight_layout(w_pad=1.2)
    p = MAP["parquet"]
    finish(fig, "r6_hazard_mapping", "recordings", [
        dict(what="level-05 episodes with exactly one predator (left)", used=p["episodes"], total=p["episodes"],
             note=f"{p['injury_deaths']:,} injury deaths over {p['steps']:,} steps; steps outside a bush = 0.74 x steps"),
        dict(what="worlds (right)", used=len(ROWS), total=len(ROWS), note="planner inputs from mappings.json")])


if __name__ == "__main__":
    for f in (r1, r2, r3, r4, r5, r6, r7, r8):
        f(); print("done", f.__name__)
