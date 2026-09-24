"""FIGURE G11 — Does the modulator's output follow the felt injury it is given?

WHAT IS PLOTTED. Neuromodulated agent only. In the sustained felt-injury manipulation of Figure G6
(no-animal scene, uninjured start), the modulator's output at each of the places it adjusts the network
is recorded every step. Vertical: the change in its mean gain (the multiplier it applies, averaged over
the units of that layer, over the steps the agent is alive, over 30 episodes and the newest 20
checkpoints) relative to felt injury 0. Horizontal: the felt injury given. One line per place.
Level 06 is split into scenes without and with a fire, the contrast Figures G1-G2 point to. Because
the modulator reads the manipulated input, a response here is expected; its SIZE and SHAPE across
levels is the clue.
"""
import sys, os, glob; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
SITES = [("encoder_unimodal", "encoder, per sense"), ("encoder_multimodal", "encoder, combined"),
         ("rnn", "memory (GRU)"), ("actor", "action head"), ("critic", "value head")]
cols = house.sequential(stops=None)(np.linspace(0.35, 1.0, len(SITES)))   # one hue, light to dark
x = np.array(I.LADDER) * 100


def gain_curves(version):
    files = sorted(glob.glob(os.path.join(I.manip_dir(version, "avoid_none_inj00", f"{lv}_modulated",
                                                      "ladder_sustained"), "steps_*.npz")))
    out = {}
    for f in files:
        z = np.load(f); T = z["T"]; cr = z["cond_rows"]
        valid = np.arange(z["done"].shape[0])[:, None] < T[None, :]
        for s, _ in SITES:
            k = f"gain_{s}"
            if k not in z.files:
                continue
            g = np.array([z[k][:, cr == c][valid[:, cr == c]].mean() for c in range(1, cr.max() + 1)])
            out.setdefault(s, []).append(g - g[0])
    return {s: np.mean(v, 0) for s, v in out.items()}, len(files)


fig, ax = plt.subplots(1, len(I.MANIP_COLS), figsize=(10.0, 4.4), sharey=True)
samples = []
for j, (lv, vers, title) in enumerate(I.MANIP_COLS):
    a = ax[j]; per = []; nck = 0
    for v in vers:
        g, n = gain_curves(v)
        if g:
            per.append(g); nck += n
    for k, (s, sl) in enumerate(SITES):
        ys = [p[s] for p in per if s in p]
        if ys:
            a.plot(x, np.median(ys, 0), "-", color=cols[k], lw=1.7, label=sl if j == 0 else None)
    a.axhline(0, color=house.INK, lw=0.8)
    a.set_title(title, loc="left", fontsize=10, color=house.INK)
    a.set_xlabel("felt injury given"); a.set_xticks([0, 50, 90])
    samples.append(dict(what=title.replace("\n", " "), used=nck, total=len(vers) * I.LAST,
                        note="checkpoint step-recordings (30 episodes x 10 values each)"))
ax[0].set_ylabel("change in mean gain")
fig.tight_layout(w_pad=0.5)
C.legend_below(ax[0], ncol=3, offset=-0.42)
fig.tight_layout(w_pad=0.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g11_modulator_follows", "manipulation")
C.record_samples("g11_modulator_follows", samples)
house.save(fig, os.path.join(C.FIG, "g11_modulator_follows"), column_px=C.COLUMN_PX)
