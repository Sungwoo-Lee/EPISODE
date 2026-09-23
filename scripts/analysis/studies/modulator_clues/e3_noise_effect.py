"""FIGURE E3 — What does injury-gated smell noise do? Level 06 against level 05.

THE DESIGN THIS USES. Level 06 is level 05 plus one thing: the agent's sense of smell becomes noisier
as it is injured (smell is how it identifies a predator). The project's hypothesis for that level is
that an agent which can no longer trust its threat cue when hurt should fall back on caution --
over-react to ambiguous cues. A modulator that reads the body's state is the obvious mechanism for
switching strategy with injury, so if it matters anywhere, it should show here.

WHAT IS PLOTTED. For each wave and each agent, level 06's value MINUS level 05's, on four injury-
related measures computed elsewhere on this page: the causal injury span and hunger span (Figure A5),
the wound's shift in response to a nearby predator, and the criterion shift -- how much more the wound
raises the response to a harmless rabbit than to a predator (Figure A4). All four use randomly
assigned starting injury.

WHAT IT CANNOT SEPARATE. Levels 05 and 06 are different training runs. Their difference is the smell
noise PLUS whatever two runs with different random seeds would differ by anyway, which one seed per
cell cannot measure. Read a small difference as nothing; read a consistent sign across both waves and
both agents as a lead.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ladder"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house
from _ladder import proximity_effect

house.apply()


def measures(world, lvl, arm):
    d = C.ladder(world, lvl, arm); z = C.npz(world, lvl, arm)
    g = d["grids"]; f = lambda k, b: proximity_effect(g[f"{k}_bush"], g[f"{k}_tot"], b)
    pre = f("pd", (3,)) - f("pd", (0,)); rab = f("rd", (3,)) - f("rd", (0,))
    inj, hun, _ = C.spans(z, world)
    return {"injury span": inj, "hunger span": hun, "wound's predator shift": pre, "criterion shift": rab - pre}


NAMES = ["injury span", "hunger span", "wound's predator shift", "criterion shift"]
LATE = "state span, 5 checkpoints"


def late_span(world, lvl, arm):
    """Causal state span at each late checkpoint (four 100k stores + the final 1M), in order."""
    s = [C.causal_metric(d, "state_span") for d in C.late(world, lvl, arm)]
    f = C.context_final(world, lvl, arm)
    return s + ([C.causal_metric(f, "state_span")] if f else [])
fig, ax = plt.subplots(1, 2, figsize=(10.0, 5.4), sharey=True)
out = {}
for p, world in enumerate(("w1", "w2")):
    y = np.arange(len(NAMES))[::-1] + 1
    for k, (arm, lab, col) in enumerate(C.ARMS):
        a, b = late_span(world, 6, arm), late_span(world, 5, arm)
        if len(a) == len(b) and a:
            d = np.array(a) - np.array(b); yy = 0 + (0.5 - k) * 0.36
            ax[p].plot([d.min(), d.max()], [yy, yy], color=col, lw=3, alpha=0.45, solid_capstyle="round")
            ax[p].plot([np.median(d)], [yy], "o", ms=7, color=col)
            out[(world, arm, "late")] = (np.median(d), d.min(), d.max())
    for k, (arm, lab, col) in enumerate(C.ARMS):
        d6, d5 = measures(world, 6, arm), measures(world, 5, arm)
        v = [d6[n] - d5[n] for n in NAMES]; out[(world, arm)] = v
        ax[p].barh(y + (0.5 - k) * 0.36, v, height=0.34, color=col, label=lab)
    ax[p].axvline(0, color=house.INK, lw=1); ax[p].grid(axis="y", visible=False)
    ax[p].set_title(C.WORLD_NAME[world], fontsize=10.5, color=house.INK, loc="left", pad=8)
    ax[p].set_xlabel("level 06 − level 05 (pp)")
ax[0].set_yticks(list(np.arange(len(NAMES))[::-1] + 1) + [0]); ax[0].set_yticklabels(NAMES + [LATE], fontsize=10)
C.legend_below(ax[0], ncol=2, offset=-0.22)
fig.tight_layout(w_pad=1.6)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("e3_noise_effect", "between_runs")
C.record_samples("e3_noise_effect", [
    dict(what="training runs", used=8, total=8, note="levels 05 and 06 × two agents × two waves, one seed each"),
    dict(what="episodes per run", used=1000000, total=1000000, note="final-checkpoint store; randomly assigned starting injury"),
    dict(what="measures", used=4, total=4, note="injury span, hunger span, wound's predator shift, criterion shift"),
    dict(what="late checkpoints in the bottom row", used=5, total=5,
         note="four 100k stores plus the final 1M store per run, paired in order between levels 06 and 05"),
    dict(what="seed-to-seed spread", used=0, total=1,
         note="not estimable: each level is a different single run, so the difference mixes noise effect and seed")])
house.save(fig, os.path.join(C.FIG, "e3_noise_effect"), column_px=C.COLUMN_PX)
for k, v in out.items(): print(" ", k, [f"{x:+.2f}" for x in v])
