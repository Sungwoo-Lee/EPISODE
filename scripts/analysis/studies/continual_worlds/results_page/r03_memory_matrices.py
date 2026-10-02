"""FIGURE r03 — What each checkpoint still knows: frozen stage-end checkpoints played in all seven worlds,
both agents, and the modulated-minus-ordinary difference.

Source: results/analysis/continual_worlds/forgetting_{p1,p2,p3}_{t1none,t16quad}.json (the forgetting
matrices of CONTINUAL_WORLDS.md 5.3 / 10.5): per checkpoint row x world, mean survival over 2,000 test
episodes (seeds 0-1999, identical in every cell), its standard error and the share of episodes at the
500-step cap. Greedy (most-likely-action) play, as the matrices were run. The forgetting votes and their
entries are read from tmp/20260929_cw_main_verdict.json only for the prose numbers recorded below.

Difference cells are marked when they are beyond evaluation noise: |diff| > 1.96 x sqrt(se_ord^2 + se_mod^2)
(two independent 2,000-episode means). This is the cell-level evaluation noise, not the between-agent
yardstick of the registered forgetting vote (non-overlapping 95 % intervals of two forgetting values).
"""
import os, sys, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import _common as C

house = C.house; house.apply()
STEM = "r03_memory_matrices"
WORLDS = ["forage", "danger_scout_a", "fog_scout_b", "winter", "famine", "home", "nursery"]
V = C.load(C.VERDICT)

M, SE, CAP, ROWS = {}, {}, {}, {}
n_cells = 0
for s in ("P1", "P2", "P3"):
    for a in ("ordinary", "modulated"):
        F = C.forgetting(s, a)
        assert F["episodes_per_cell"] == 2000
        labels = [r["label"] for r in F["rows"]]
        ROWS.setdefault(s, labels)
        assert ROWS[s] == labels, (s, a)
        assert sorted(w["world"] for w in F["worlds"]) == sorted(WORLDS), (s, a)
        m = np.full((len(labels), len(WORLDS)), np.nan); e = m.copy(); c = m.copy()
        for cell in F["cells"]:
            assert cell["eval_policy_mode"] == "deterministic" and cell["n"] == 2000
            i, j = labels.index(cell["row"]), WORLDS.index(cell["world"])
            m[i, j], e[i, j], c[i, j] = cell["mean"], cell["se"], cell["frac_at_max_steps"]
            n_cells += 1
        assert not np.isnan(m).any(), (s, a)
        M[s, a], SE[s, a], CAP[s, a] = m, e, c
# the branch-point row is the same two checkpoints in all three sequences
for a in ("ordinary", "modulated"):
    for s in ("P1", "P2"):
        assert np.allclose(M[s, a][0], M["P3", a][0], atol=0.1), (s, a, M[s, a][0], M["P3", a][0])

seq_cmap = LinearSegmentedColormap.from_list("greys", ["#fbfbfa", "#b9bdc2", "#3a3f46"])   # grey: blue and orange are the agents
div = LinearSegmentedColormap.from_list("ordmod", [C.ORD, "#ffffff", C.MOD])
DLIM = 120


def _lum(rgb):
    """WCAG relative luminance of an sRGB colour (0-1 floats)."""
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb[:3]]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ink_on(rgba):
    """Cell text colour with the better contrast against the cell: white or ink (format gate, 2026-09-30)."""
    from matplotlib.colors import to_rgb
    L = _lum(rgba); Li = _lum(to_rgb(house.INK))
    return "white" if (1.05) / (L + 0.05) > (L + 0.05) / (Li + 0.05) else house.INK

fig = plt.figure(figsize=(9.9, 11.0))
gs = fig.add_gridspec(3, 3, hspace=0.95, wspace=0.08, left=0.17, right=0.995, top=0.9, bottom=0.14)
n_beyond, n_diff = 0, 0
for r, s in enumerate(("P1", "P2", "P3")):
    seqw = set(C.SEQ[s][1].split(" ↔ "))
    for c_, key in enumerate(("ordinary", "modulated", "diff")):
        ax = fig.add_subplot(gs[r, c_])
        if key == "diff":
            d = M[s, "modulated"] - M[s, "ordinary"]
            noise = 1.96 * np.sqrt(SE[s, "modulated"] ** 2 + SE[s, "ordinary"] ** 2)
            ax.imshow(np.clip(d, -DLIM, DLIM), cmap=div, vmin=-DLIM, vmax=DLIM, aspect="auto")
            for i in range(d.shape[0]):
                for j in range(d.shape[1]):
                    bn = abs(d[i, j]) > noise[i, j]
                    n_beyond += bn; n_diff += 1
                    txt = "0" if round(d[i, j]) == 0 else C.fmt(d[i, j], 0, sign=True)   # never "-0" / "+0"
                    ax.text(j, i, txt + ("*" if bn else ""), ha="center", va="center", fontsize=C.SMALLEST_PT,
                            color=ink_on(div((np.clip(d[i, j], -DLIM, DLIM) + DLIM) / (2 * DLIM))),
                            fontweight="semibold" if bn else "normal")
            ttl = "modulated − ordinary"
        else:
            m = M[s, key]
            ax.imshow(m, cmap=seq_cmap, vmin=0, vmax=500, aspect="auto")
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=C.SMALLEST_PT,
                            color=ink_on(seq_cmap(m[i, j] / 500)))
            ttl = C.AGENT_LABEL[key]
        if c_ == 0:
            p = ax.get_position()
            fig.text(0.01, p.y1 + 0.043, f"{s}  {C.SEQ[s][1]}", fontsize=house.FS_BODY, fontweight="semibold",
                     color=house.INK, va="bottom")
        ax.set_title(ttl, fontsize=C.SMALLEST_PT + 1.5, loc="left", pad=5,
                     color=C.AGENT_COL.get(key, house.INK))
        ax.grid(False)
        ax.set_xticks(range(len(WORLDS)))
        ax.set_xticklabels([C.WORLD[w] for w in WORLDS], rotation=90, ha="right", va="center", fontsize=C.SMALLEST_PT,
                           rotation_mode="anchor")
        for t, w in zip(ax.get_xticklabels(), WORLDS):
            if C.WORLD[w] in seqw or w == "forage":
                t.set_fontweight("bold"); t.set_color(house.INK)
        ax.set_yticks(range(len(ROWS[s])))
        if c_ == 0:
            ax.set_yticklabels(["branch point" if l == "start" else f"end st. {int(l.split('_')[1])} {C.WORLD[l.split('_', 2)[2]]}"
                                for l in ROWS[s]], fontsize=C.SMALLEST_PT)
        else:
            ax.set_yticklabels([])
fig.text(0.01, 0.99, "cells: mean survival (steps per episode) of the frozen checkpoint in that world;\n"
         "* = difference beyond evaluation noise;  bold world names = worlds of that sequence",
         fontsize=C.SMALLEST_PT + 0.5, color=house.INK)
# colour keys
cax1 = fig.add_axes([0.20, 0.035, 0.30, 0.014]); cax2 = fig.add_axes([0.62, 0.035, 0.30, 0.014])
import matplotlib as mpl
cb1 = fig.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(0, 500), cmap=seq_cmap), cax=cax1, orientation="horizontal")
cb2 = fig.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(-DLIM, DLIM), cmap=div), cax=cax2, orientation="horizontal")
cb1.set_label("survival, steps per episode (cap 500)", fontsize=C.SMALLEST_PT + 0.5)
cb2.set_label(f"difference, steps (clipped at ±{DLIM})", fontsize=C.SMALLEST_PT + 0.5)
for cb in (cb1, cb2):
    cb.ax.tick_params(labelsize=C.SMALLEST_PT); cb.outline.set_visible(False)

# ---- numbers for the prose -------------------------------------------------------------------------
fe = {s: V["forget"][s]["entries"] for s in ("P1", "P2", "P3")}
ab = [e["diff"] for s in fe for e in fe[s] if not e["is_forage"]]
p3w = next(e for e in fe["P3"] if e["is_forage"] and e["at"] == "end_02_winter")
p1rev = next(e for e in fe["P1"] if e["is_forage"] and e["at"] == "end_04_danger_scout_a")
fg_bn = [e for s in fe for e in fe[s] if e["is_forage"] and e["beyond_noise"]]
assert all(e["diff"] < 0 for e in fg_bn)
i_w = ROWS["P3"].index("end_02_winter"); j_f, j_h, j_w = WORLDS.index("forage"), WORLDS.index("home"), WORLDS.index("winter")
C.record_numbers(STEM, {
    "p3_forage_forgot_ord": C.fmt(p3w["ord"]["F"]), "p3_forage_forgot_mod": C.fmt(p3w["mod"]["F"]),
    "p3_forage_gap_greedy": C.fmt(M["P3", "modulated"][i_w, j_f] - M["P3", "ordinary"][i_w, j_f], sign=True),
    "p1_reversal": C.fmt(p1rev["diff"], sign=True),
    "ab_min": C.fmt(min(ab), sign=True), "ab_max": C.fmt(max(ab), sign=True),
    "n_forage_beyond": str(len(fg_bn)),
    "forage_cap_start": C.fmt(100 * CAP["P3", "ordinary"][0, j_f]),
    "forage_start_ord": C.fmt(M["P3", "ordinary"][0, j_f]), "forage_start_mod": C.fmt(M["P3", "modulated"][0, j_f]),
    "home_after_winter_ord": C.fmt(M["P3", "ordinary"][i_w, j_h]), "home_after_winter_mod": C.fmt(M["P3", "modulated"][i_w, j_h]),
    "winter_after_winter_ord": C.fmt(M["P3", "ordinary"][i_w, j_w]), "winter_after_winter_mod": C.fmt(M["P3", "modulated"][i_w, j_w]),
    "n_cells": f"{n_cells}"})
C.record_kind(STEM, "evaluation")
C.record_samples(STEM, [
    dict(what="matrix cells (checkpoint by world, per agent)", used=n_cells, total=n_cells,
         note="5 checkpoints x 7 worlds x 2 agents x 3 sequences; 2,000 test episodes each, most-likely action"),
    dict(what="difference cells beyond evaluation noise", used=int(n_beyond), total=n_diff,
         note="marked with a star; cell-level noise only, not the registered forgetting vote"),
    dict(what="worlds shown", used=len(WORLDS), total=len(WORLDS),
         note="every world the matrices were run in: the five planned worlds that passed their pilots plus the two scouted replacements")])
C.save(fig, STEM)
