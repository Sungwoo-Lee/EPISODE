"""FIGURE S1 — What each body rule does on its own (simulator, no agent).

Six panels, level-05 values:
  (a) B2  healing per rest step in a bush against body temperature, for three strengths
  (b) B5  healing per rest step in a bush against food energy, for three floors
  (c) B4  steps from 0 deg to freezing on cold ground against injury, for three gains
  (d) B3  food energy left after resting in a bush to heal a 70-point wound from food 100, against
          the cost per point healed (B5 off / on)
  (e) A1  food energy burned per step against body temperature, for three coupling rates
  (f) B1  starting body temperatures (the range) and what a first step onto a fire does from each
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, bodysim as B

house = C.house; house.apply()
P0 = B.Body()
fig, ax = plt.subplots(2, 3, figsize=(10.0, 6.6))
ax = ax.ravel()
greys = house.sequential(stops=["#c9ccd3", "#8a8f99", house.INK])

# (a) B2
T = np.linspace(-15, 15, 121)
for k, s in enumerate((0.0, 1 / 30, 1 / 15)):
    P = P0.with_(heal_cold_s=s, heal_warm_s=s)
    h = B.step(np.full_like(T, 100.0), np.full_like(T, 90.0), T, True, False, True, -30.0, P)["healed"]
    ax[0].plot(T, h, color=greys(0.35 + 0.3 * k), lw=1.8, label=["off", "1/30 per deg", "1/15 per deg"][k])
ax[0].set_title("(a) B2: healing vs body temperature", loc="left", fontsize=10.5)
ax[0].set_xlabel("body temperature (deg)"); ax[0].set_ylabel("healed per rest step")
ax[0].legend(frameon=False, fontsize=9.5)

# (b) B5
N = np.linspace(0, 200, 201)
for k, (f, lo) in enumerate(((1.0, 0.0), (0.5, 20.0), (0.0, 0.0))):
    P = P0.with_(b5=f < 1.0, b5_floor=f if f < 1 else 0.0, b5_low=lo, b5_high=100.0)
    h = B.step(N, np.full_like(N, 90.0), 0.0, True, False, True, 8.8, P)["healed"]
    ax[1].plot(N, h, color=greys(0.35 + 0.3 * k), lw=1.8, label=["off", "floor 0.5", "floor 0"][k])
ax[1].set_title("(b) B5: healing vs food energy", loc="left", fontsize=10.5)
ax[1].set_xlabel("food energy (0-200)"); ax[1].set_ylabel("healed per rest step")
ax[1].legend(frameon=False, fontsize=9.5)

# (c) B4 steps to freezing from 0 deg on cold ground, injury held (no healing)
Ivals = np.linspace(0, 100, 21)
for k, g in enumerate((0.0, 1.0, 2.0)):
    P = P0.with_(inj_gain=g, inj_mode="cooling_only")
    Tb = np.zeros_like(Ivals); alive = np.ones_like(Ivals, bool); steps = np.zeros_like(Ivals)
    for t in range(400):
        s = B.step(np.full_like(Ivals, 100.0), Ivals, Tb, False, False, False, -30.0, P)
        newly = alive & s["thermal_death"]; steps[newly] = t + 1; alive &= ~s["thermal_death"]; Tb = s["T"]
    ax[2].plot(Ivals, np.where(steps > 0, steps, np.nan), color=greys(0.35 + 0.3 * k), lw=1.8,
               label=["off", "gain 1", "gain 2"][k])
ax[2].set_title("(c) B4: time to freeze vs injury", loc="left", fontsize=10.5)
ax[2].set_xlabel("injury (0-100)"); ax[2].set_ylabel("steps from 0 deg to freezing")
ax[2].set_ylim(bottom=0); ax[2].legend(frameon=False, fontsize=9.5)

# (d) B3 food left after healing 70 in a warm bush (body stays warm) from food 100
costs = np.linspace(0, 2, 41)
for k, b5 in enumerate((False, True)):
    left = []
    for c in costs:
        P = P0.with_(heal_cost=c, shortfall="partial", b5=b5, b5_floor=0.2, b5_low=20.0, b5_high=100.0)
        n, i, tb = 100.0, 70.0, 5.8
        for t in range(300):
            s = B.step(n, i, tb, True, False, True, 8.8, P); n, i, tb = float(s["N"]), float(s["I"]), float(s["T"])
            if i <= 0 or s["dead"]:
                break
        left.append(n if not s["dead"] else 0.0)
    ax[3].plot(costs, left, color=house.INK if b5 else "#8a8f99", lw=1.8, label=["B5 off", "B5 on (floor 0.2)"][k])
ax[3].set_title("(d) B3: food left after a 70-point heal", loc="left", fontsize=10.5)
ax[3].set_xlabel("food energy per point healed"); ax[3].set_ylabel("food energy left (from 100)")
ax[3].set_xticks([0.5, 1.0, 1.5, 2.0]); ax[3].legend(frameon=False, fontsize=9.5)

# (e) A1
for k, r in enumerate((0.0, 1.0, 2.0)):
    P = P0.with_(coupling=r > 0, coupling_rate=r if r > 0 else 1.0)
    s = B.step(np.full_like(T, 100.0), 0.0, T, False, False, False, -30.0, P)
    ax[4].plot(T, 100.0 - s["N"], color=greys(0.35 + 0.3 * k), lw=1.8, label=["off", "rate 1", "rate 2"][k])
ax[4].set_title("(e) A1: food burned per step", loc="left", fontsize=10.5)
ax[4].set_xlabel("body temperature (deg)"); ax[4].set_ylabel("food energy burned per step")
ax[4].legend(frameon=False, fontsize=9.5)

# (f) B1 start range and first step onto a fire (hottest fire cell 79.73)
Ts = np.linspace(-12, 12, 97)
first = B.step(100.0, 0.0, Ts, False, False, False, 79.73, P0)["T"]
ax[5].plot(Ts, first, color=house.INK, lw=1.8)
ax[5].axvspan(-10, 5, color=house.BLUE, alpha=0.15, lw=0)
ax[5].axhline(15, color=house.RED, lw=1.0, ls="--")
ax[5].text(-11.5, 15.6, "death line +15", fontsize=9.5, color=house.RED)
ax[5].text(-9.6, 1.5, "level-05 start range", fontsize=9.5, color=house.INK)
ax[5].set_title("(f) B1: first step onto a fire", loc="left", fontsize=10.5)
ax[5].set_xlabel("starting body temperature (deg)"); ax[5].set_ylabel("temperature after the step")
for a, xl, yl in zip(ax, [(-15, 15), (0, 200), (0, 100), (0, 2), (-15, 15), (-12, 12)],
                     [(0, 5.5), (0, 5.5), (0, 100), (0, 100), (0.9, 1.7), (-6, 20)]):
    a.set_xlim(*xl); a.set_ylim(*yl)
fig.tight_layout(h_pad=1.6, w_pad=2.2)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("s1_single_rules", "simulation")
C.record_samples("s1_single_rules", [
    dict(what="body states per curve", used=121, total=121, note="a regular grid; the simulator is deterministic"),
    dict(what="simulator steps checked against the real environment", used=4000, total=4000,
         note="today's rules; max difference 2e-5 (validation_current_rules.json)")])
house.save(fig, os.path.join(C.FIG, "s1_single_rules"), column_px=C.COLUMN_PX)
