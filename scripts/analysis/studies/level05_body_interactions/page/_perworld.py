"""Shared layout for the per-world figures (4 and 5): rule matrix | both agents | modulator minus
ordinary. Kept separate from _common so a change here cannot touch Figures 1-3."""
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house


def draw(values, gap_label, value_label, xlim_val, xlim_gap, legend=True):
    """values: {world: (ordinary, modulated)}. Returns fig, axes."""
    worlds = C.WORLDS
    y = np.arange(len(worlds))[::-1].astype(float)
    fig, ax = plt.subplots(1, 3, figsize=(9.8, 7.0), sharey=True,
                           gridspec_kw=dict(width_ratios=[1.1, 1.5, 1.0]))
    C.draw_rule_matrix(ax[0], worlds, y)
    for w, yy in zip(worlds, y):
        o, m = values[w]
        ax[1].plot([o, m], [yy, yy], color=C.GREY, lw=1.2, zorder=2)
        for ag, v in (("ordinary", o), ("modulated", m)):
            st = C.AGENT[ag]
            ax[1].plot([v], [yy], st["marker"], mfc=st["mfc"], mec=st["mec"], mew=1.3, ms=6.5, zorder=3,
                       label=st["label"] if w == worlds[0] else None)
        ax[2].plot([0, m - o], [yy, yy], color=house.INK, lw=1.4, solid_capstyle="butt")
        ax[2].plot([m - o], [yy], "D", color=house.INK, ms=5.5)
    ax[2].axvline(0, color=C.GREY, lw=0.8)
    ax[1].set_xlim(*xlim_val); ax[2].set_xlim(*xlim_gap)
    ax[1].set_xlabel(value_label); ax[2].set_xlabel(gap_label)
    for a in ax[1:]:
        a.grid(axis="y", visible=False); a.grid(axis="x", visible=True)
    ax[0].set_ylim(-0.7, len(worlds) - 0.3)
    fig.tight_layout(w_pad=0.8, rect=(0, 0.06 if legend else 0, 1, 1))
    if legend:
        h, l = ax[1].get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0),
                   fontsize=C.SMALLEST_PT)
    return fig, ax
