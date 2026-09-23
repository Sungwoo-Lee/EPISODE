"""FIGURE C1 — How much of the modulator's output actually moves with the body, site by site?

WHAT IS MEASURED. At each place it acts, the modulator emits a gain for every channel -- a number
that feature is multiplied by. Replaying a trained agent on a fixed set of 128 episodes, the variation
in those gains splits in two: variation ACROSS CHANNELS (channel 7 always amplified, channel 30 always
damped -- a learned constant, no different in effect from a fixed weight) and variation ACROSS TIME
within a channel (the same channel scaled differently as the body's state changes). Only the second
can make behaviour depend on internal state. Each cell shows that second part as a share of the total.

HOW THE CHECKPOINTS ENTER. Every Wave-1/2 cell is replayed at the same five late checkpoints as its
behaviour; the cell shows the median and, beneath it, the range across those five (one run). The
blind world's value comes from an earlier replay at its final checkpoint only: its saved config no
longer loads under the current config schema, so it cannot be re-replayed at other checkpoints.

WHAT CLUE IT OFFERS. Whether the environment updates made the modulator track the body more -- and at
which site. A share that rises where the world demands more state dependence would say the modulator
responds to the task; a share that stays flat would say something about the architecture or training.
"""
import sys, os, csv, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
SITES = [("encoder_unimodal", "encoder, one sense"), ("encoder_multimodal", "encoder, senses combined"),
         ("rnn", "memory (recurrent core)"), ("actor", "actor (chooses)"), ("critic", "critic (evaluates)")]
rows = list(csv.DictReader(open(os.path.join(C.INT, "mod_distribution/distributions.csv"))))
blind = {r["site"]: float(r["gamma_rho"]) for r in csv.DictReader(open(os.path.join(
    C.A, "nmn_representation/mod_distribution_olf/distributions.csv")))
    if r["grid"] == "olfgae" and r["arm"] == "t16quad" and r["input_slice"] == "ALL"}
by = collections.defaultdict(list)
for r in rows:
    w = "w1" if r["grid"] == "basicq2" else "w2"
    by[(w, int(r["level"]), r["site"])].append(100 * float(r["gamma_rho"]))
COLS = C.COLUMNS
M = np.full((len(SITES), len(COLS)), np.nan); LO = M.copy(); HI = M.copy()
for j, (world, lvl) in enumerate(COLS):
    for i, (site, _) in enumerate(SITES):
        if world == "blind":
            M[i, j] = 100 * blind[site]
        elif by.get((world, lvl, site)):
            v = np.asarray(by[(world, lvl, site)]); M[i, j] = np.median(v); LO[i, j] = v.min(); HI[i, j] = v.max()
fig, ax = plt.subplots(figsize=(10.0, 4.9))
im = ax.imshow(M, cmap=house.sequential(), vmin=0, vmax=40, aspect="auto")
for i in range(len(SITES)):
    for j in range(len(COLS)):
        if np.isnan(M[i, j]):
            ax.text(j, i, "—", ha="center", va="center", fontsize=10, color=house.TEXT_LIGHT); continue
        dark = M[i, j] > 24
        txt = f"{M[i, j]:.0f}%" + ("" if np.isnan(LO[i, j]) else f"\n{LO[i, j]:.0f}–{HI[i, j]:.0f}")
        ax.text(j, i, txt, ha="center", va="center", fontsize=10 if np.isnan(LO[i, j]) else 9.6,
                color="white" if dark else house.INK)
ax.set_xticks(range(len(COLS))); ax.set_xticklabels([C.col_label(*c) for c in COLS], fontsize=10)
ax.set_yticks(range(len(SITES))); ax.set_yticklabels([s for _, s in SITES], fontsize=10)
ax.axvline(0.5, color="white", lw=3)
ax.grid(False)
ax.xaxis.tick_top()
fig.suptitle("Share of each site's gain variation that changes over time (%). Small line: range across 5 late checkpoints (one run).",
             fontsize=10, color=house.INK_2, x=0.005, ha="left", y=0.02, va="bottom")
fig.tight_layout(rect=(0, 0.05, 1, 1))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("c1_gain_tracking", "observational")
C.record_samples("c1_gain_tracking", [
    dict(what="modulated runs", used=9, total=9, note="blind, Wave 1 levels 02-06, Wave 2 levels 04-06"),
    dict(what="checkpoints per Wave-1/2 cell", used=5, total=5,
         note="the same late checkpoints as the behaviour; Wave 1 levels 02/03 at matched training length"),
    dict(what="checkpoints for the blind cell", used=1, total=5,
         note="final only: the blind run's saved config no longer loads, so it cannot be re-replayed"),
    dict(what="episodes replayed", used=128, total=128, note="one fixed set, shared by every run and checkpoint")])
house.save(fig, os.path.join(C.FIG, "c1_gain_tracking"), column_px=C.COLUMN_PX)
for i, (s, _) in enumerate(SITES): print(f"  {s:20}", " ".join(f"{v:5.1f}" for v in M[i]))
