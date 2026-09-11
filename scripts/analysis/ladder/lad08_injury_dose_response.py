"""FIGURE 8 - Does waking up wounded make the agent hide? (the causal test)

QUESTION. Everywhere else in this report, a wounded agent is a suspicious comparison: it got hurt
by doing something, so its later behaviour is contaminated by whatever it was doing. This
environment removes that problem. `body.random_start_injury` is true, so at the start of every
episode the agent is handed a wound drawn uniformly from 0 to 100 that it did nothing to earn.
Behaviour that tracks THAT number is caused by the wound.

WHY IT MATTERS FOR THE SENSOR LADDER. The agent cannot see its own wound - `injury_observable` is
false. The only route from an injury level to behaviour is the interoceptive nociceptor, which
convolves a twelve-slot buffer of injury LEVELS with an alpha kernel. So this figure asks whether
that internal channel changes behaviour, and whether the answer depends on what the agent can
sense of the outside world.

HOW IT IS COMPUTED. Episodes are split into four equal quarters of starting wound (0-25, 25-50,
50-75, 75-100). Bush hiding is pooled over the first 25 steps of each episode only - the wound
recovers over time, so a whole-episode average would dilute the assigned dose with whatever the
agent's own behaviour produced later. The t=0 row is excluded.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _ladder as L, _plot as PL

D = L.load_all(); arms = L.ARM_ORDER; col = PL.arm_colors()
x = np.arange(4)
curves = {a: L.rate(D[a]["grids"]["dw_early"], D[a]["grids"]["dwt_early"]) for a in arms}
slope = {a: curves[a][3] - curves[a][0] for a in arms}
GRP = {a: L.resolves_identity(D[a]["sensory"]) for a in arms}
# Name the arms a reader will actually look for: the one line that goes DOWN, the highest line in
# each family, and the reference agent the rest of the page is written against. Everything else
# stays thin. Asserted rather than hardcoded blind, so the figure cannot keep naming "the highest"
# arm after the data stops making it the highest.
SPOT = ("A_baseline", "B_olf_only", "V4_blur05", "V5_sharp")
_top = lambda want: max((a for a in arms if GRP[a] == want), key=lambda a: curves[a][-1])
assert _top(False) == "B_olf_only", f"highest non-resolving arm is now {_top(False)}, not B_olf_only"
assert _top(True) == "V5_sharp", f"highest identity-resolving arm is now {_top(True)}, not V5_sharp"
assert min(slope, key=slope.get) == "A_baseline"

fig, ax = plt.subplots(1, 2, figsize=(12.4, 5.5),
                       gridspec_kw={"width_ratios": [1.1, 1]})
# Colour by ARM, with the identical colour in the right panel, instead of by the two-family split
# used elsewhere on the page. The right panel names all fourteen arms down its y-axis, so it IS
# this panel's key; a legend repeating fourteen names beside a four-point plot would be larger
# than the plot. The named arms stay thicker and carry their name at the end of the line.
ends = []
for a in arms:
    yv = curves[a]
    if a in SPOT:
        ax[0].plot(x, yv, lw=2.7, color=col[a], marker="o", ms=5.2, zorder=3)
        ends.append((x[-1], yv[-1], f" {a}", col[a]))
    else:
        ax[0].plot(x, yv, lw=1.5, color=col[a], alpha=0.9, zorder=2)
PL.stagger_end_labels(ax[0], ends)
ax[0].set_xlim(-0.25, 3.9)
ax[0].set_xticks(x); ax[0].set_xticklabels(L.INJ_NAMES)
ax[0].set_xlabel("initial injury level  (0-100, in four equal quarters)")
ax[0].set_ylabel("bush hiding over the episode's first 25 steps\n(% of those steps spent in a bush)")
ax[0].set_title("Bush hiding against the initial injury level\n"
                "One line per arm, in the same colour that arm has in the right panel, which "
                "names all fourteen.\nThe four the text discusses are drawn thicker and named "
                "at the end of their line.",
                fontsize=9, color=PL.MUTED, loc="left", pad=8)

y = np.arange(len(arms))
v = np.array([slope[a] for a in arms])
ax[1].barh(y, v, color=[col[a] for a in arms], height=0.72, edgecolor="none")
ax[1].axvline(0, color=PL.INK, lw=1)
ax[1].set_yticks(y); ax[1].set_yticklabels(PL.arm_ylabels(arms), fontsize=8)
ax[1].set_ylabel("sensor-ladder arm  (poorest senses at the bottom)")
ax[1].set_xlabel("a DIFFERENCE, in percentage points:\n"
                 "bush hiding in the highest initial-injury quarter MINUS the lowest")
ax[1].grid(axis="y", visible=False)
for i, q in enumerate(v):
    ax[1].text(q + np.sign(q) * 0.06, y[i], f"{q:+.2f}", va="center",
               ha="left" if q >= 0 else "right", fontsize=7.6, color=PL.INK)
m = max(abs(v)) * 1.55
ax[1].set_xlim(-m, m)
POP = L.population()
_used = sum(int(np.asarray(D[a]["grids"]["dwt_early"], float).sum()) for a in arms)
L.record_samples("lad08_injury_dose_response", [
    dict(what="step rows in the 25-step window", used=_used, total=POP["steps"],
         note="the first 25 steps of every episode of every arm; episodes shorter than 25 steps "
              "contribute all the steps they have"),
    dict(what="episodes contributing", used=POP["episodes"], total=POP["episodes"],
         note="every episode has a randomised initial injury level, so none is excluded")])

PL.assert_labels_fit(fig, ax)
PL.finish(fig, f"{L.FIG_ROOT}/lad08_injury_dose_response.png")
print(f"{'arm':22}" + "".join(f"{n:>10}" for n in L.INJ_NAMES) + f"{'slope':>10}")
for a in arms:
    print(f"{a:22}" + "".join(f"{q:>10.2f}" for q in curves[a]) + f"{slope[a]:>+10.2f}")
