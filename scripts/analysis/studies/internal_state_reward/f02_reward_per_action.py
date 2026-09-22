"""FIGURE 2 — what one action is worth, at every fullness.

QUESTION. Reward here is not a score for eating; it is the DROP in homeostatic drive that an
action produces. So the same action is worth different amounts depending on where the body
already is, and after 2026-09-22 the same action can be worth a positive or a negative amount.

WHY IT MATTERS. This is the figure that shows over-eating being punished without any special
case for it. Nothing in the code says "do not eat when full" — eating when full simply moves the
body away from its target, which raises the drive, which is a negative reward by definition.

HOW IT IS COMPUTED. Both curves call the live `calculate_drive` twice, once at the current
fullness and once at the fullness the action leads to, and plot the difference. The nutrition
each action moves is read from the resolved `EnvParams`, never typed: eating is
`food_nutrition_gain - eating_nutrition_cost - metabolic_cost`, resting is `-metabolic_cost`.
Injury is held at zero and thermal is off, so fullness is the only live axis. The endpoints are
clipped into `[0, max_nutrition]` exactly as `update_body` clips them.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C
import house

STEM = "f02_reward_per_action"
p = C.params_for("10x10")
d_eat  = float(p.food_nutrition_gain) - float(p.eating_nutrition_cost) - float(p.metabolic_cost)
d_rest = -float(p.metabolic_cost)

n = np.arange(0, p.max_nutrition + 1, 1.0)
def reward(delta):
    after = np.clip(n + delta, 0.0, p.max_nutrition)
    return (C.drive(C.satiation_of(n, p), 0.0, p)
            - C.drive(C.satiation_of(after, p), 0.0, p))

r_eat, r_rest = reward(d_eat), reward(d_rest)

# PAGE-WIDE COLOUR CONTRACT (register F11): on this page blue means "the world as it now
# stands" and orange means "the world before the change" (figures 1, 4, 5). This figure's
# categories are ACTIONS, which is a different thing, so it takes two hues that appear in no
# other figure and in no chrome on the page.
EAT, REST = "#17807a", "#9a7d19"
house.apply(series=[EAT, REST])
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.axhline(0, color=house.INK_2, lw=1.0)
ax.axvline(p.setpoint, color=house.INK_2, lw=1.0, ls=(0, (4, 3)))
ax.plot(n, r_eat,  lw=2.6, color=EAT,  label=f"eat one food  (fullness {d_eat:+.0f})")
ax.plot(n, r_rest, lw=2.6, color=REST, label=f"rest one step  (fullness {d_rest:+.0f})")
ax.set_xlabel("the agent's fullness (nutrition) BEFORE the action, in nutrition points")
ax.set_ylabel("reward for that one action,\nin satiation units of drive removed")
ax.set_xlim(-5, 205)
house.legend_below(ax, ncol=2)

C.record_samples(STEM, [
    dict(what="fullness values evaluated", used=len(n), total=len(n),
         note="every whole nutrition point in the reachable range 0-200; the drive at each is "
              "read from the live calculate_drive, and the nutrition each action moves is read "
              "from the resolved EnvParams rather than typed"),
    dict(what="episodes used", used=0, total=0,
         note="none - this figure is the reward RULE evaluated across the state space, not a "
              "measurement of what an agent did. An independent full jax_step measurement of the "
              "eat action gave -4.0 at the target and +4.0 at fullness 50, matching this curve")])
house.save(fig, os.path.join(C.FIG_ROOT, STEM))
for x in (50, 100, 150):
    k = int(x)
    print(f"  at fullness {x}: eat {r_eat[k]:+.2f}   rest {r_rest[k]:+.2f}")
