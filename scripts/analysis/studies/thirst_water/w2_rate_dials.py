"""FIGURE 2 — The two water dials: drain per step and gain per step on the pond.

Left: steps from the setpoint to thirst death, 100 / drain, over drain 0.3-2.0; the target band
150-200 (decision 8) shaded; the hunger clock (100) and the measured cold band (86-99) for reference.
Right: at drain 0.625, steps on the pond to refill from 25 and from 50 to the setpoint, and to
over-drink from the setpoint, as the gain per step varies; the plan's own target bands shaded.
Exact arithmetic, the planned rule W' = clip(W - drain + gain*on_pond, 0, 200).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import watersim as S

house = C.house; house.apply()
Wt = S.Water()
d = np.linspace(0.3, 2.0, 341)
g = np.linspace(1.0, 21.0, 401)
net = g - Wt.drain

fig, ax = plt.subplots(1, 2, figsize=(10.2, 4.2))
a = ax[0]
a.axhspan(150, 200, color=house.BLUE, alpha=0.10, lw=0)
a.text(1.95, 188, "target 150-200", ha="right", fontsize=10, color=house.BLUE)
a.plot(d, 100 / d, color=house.BLUE, lw=2.2)
a.axhline(100, color=house.GREEN, lw=1.2, ls="--"); a.text(1.95, 103, "hunger 100", ha="right", fontsize=10, color=house.GREEN)
a.axhspan(86, 99, color="#5b6bbf", alpha=0.18, lw=0); a.text(1.95, 74, "cold 86-99", ha="right", fontsize=10, color="#5b6bbf")
a.scatter([Wt.drain], [100 / Wt.drain], color=house.INK, zorder=5, s=26)
a.annotate("planned: 0.625 -> 160", (Wt.drain, 160), xytext=(0.78, 232), fontsize=10.5, color=house.INK,
           arrowprops=dict(arrowstyle="-", color=house.INK, lw=0.8))
a.set_ylim(0, 340); a.set_xlim(0.3, 2.0)
a.set_xlabel("drain per step away from water"); a.set_ylabel("steps from setpoint to thirst death")

b = ax[1]
b.axhspan(10, 20, color=house.BLUE, alpha=0.10, lw=0)
b.axhspan(15, 25, color=house.ORANGE, alpha=0.10, lw=0)
b.text(20.8, 11.0, "refill target 10-20", ha="right", fontsize=10, color=house.BLUE)
b.text(20.8, 22.5, "over-drink target 15-25", ha="right", fontsize=10, color=house.ORANGE)
b.plot(g, 75 / net, color=house.BLUE, lw=2.0, label="refill 25 -> 100")
b.plot(g, 50 / net, color="#7fb2e5", lw=2.0, label="refill 50 -> 100")
b.plot(g, 100 / net, color=house.ORANGE, lw=2.0, ls="--", label="over-drink from 100")
b.axvline(Wt.gain, color=house.INK, lw=0.9, ls=":")
b.text(Wt.gain + 0.3, 57, "planned 5.625", fontsize=10, color=house.INK, va="top")
b.set_ylim(0, 60); b.set_xlim(1, 21)
b.set_xlabel("gain per step standing on the pond"); b.set_ylabel("steps on the pond")
b.legend(loc="upper right", fontsize=10.5)
fig.tight_layout(w_pad=2.2)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("w2_rate_dials", "calculation")
C.record_samples("w2_rate_dials", [
    dict(what="drain values evaluated", used=len(d), total=len(d), note="a regular grid 0.3-2.0; exact arithmetic"),
    dict(what="gain values evaluated", used=len(g), total=len(g), note="a regular grid 1-21 at drain 0.625; exact arithmetic")])
house.save(fig, os.path.join(C.FIG, "w2_rate_dials"), column_px=C.COLUMN_PX)
