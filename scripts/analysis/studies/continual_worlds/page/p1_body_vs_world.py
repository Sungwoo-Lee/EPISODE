"""FIGURE p1 — What stays fixed (the body) and what changes between the continual worlds (the outside
world). A schematic: two blocks of setting groups, each group with the number of level-05 settings it
holds, read from the balance-settings inventory (BALANCE_SETTINGS_INVENTORY.md, sections A-H). Each
inventory row is assigned to exactly one group by ROW_GROUP below; a row the table does not know stops
the script (the inventory changed, so the assignment must be looked at again).

The two boundary items -- food energy per bite and the bush healing multiplier -- look like properties of
the world (what food is worth, what a bush does) but are body-side keys; the design keeps them fixed.
They are marked on the fixed side, and the script asserts from the resolved configs (the trainer's loader)
that every body field, those two included, is identical in all eight worlds.
"""
import re, sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import _common as C

house = C.house; house.apply()

FIXED = ["food energy", "injury", "body temperature", "interoception", "reward"]
CHANGES = ["layout", "food supply", "danger", "climate", "sensing"]
# inventory row key (first cell, stripped) -> group; None = not an environment setting of either side
ROW_GROUP = {
    "body.with_nutrition / with_satiation / with_injury": "food energy",
    "body.metabolic_cost": "food energy", "body.food_nutrition_gain": "food energy",
    "body.eating_nutrition_cost": "food energy", "body.eating_reward_penalty": "food energy",
    "body.max_nutrition / max_satiation": "food energy", "body.satiation_setpoint": "food energy",
    "body.nutrition_to_satiation_scaling_factor": "food energy", "body.overeating_death": "food energy",
    "body.random_start_nutrition, start range": "food energy",
    "body.random_start_injury, start range": "injury", "body.max_injury": "injury",
    "environment.eat_action_enabled / rest_action_enabled": "food energy",
    "thermal.k_metabolic": "body temperature", "thermal.metabolic_coupling / rate (A1)": "body temperature",
    "resources.food count": "food supply", "resources.food spawn_area": "food supply",
    "resources.food max_consumption": "food supply", "resources.food regeneration_delay": "food supply",
    "thermal.food_min_fire_distance": "food supply", "food smell / sensor radius": "sensing",
    "entities.pred count": "danger", "entities.pred damage": "danger", "entities.pred attack_delay": "danger",
    "entities.pred attack_range / success": "danger", "entities.pred detection / stamina": "danger",
    "entities.rabbit": "danger", "resources.hiding_predator (ambushers)": "danger", "obstacles.rock": "danger",
    "body.injury_smoothing_duration": "injury", "body.recovery_base_rate": "injury",
    "body.recovery_in_bush_multiplier": "injury", "Rest requirement": "injury",
    "B2–B5 (healing and warmth, healing costs food, injury chills, healing and hunger)": "injury",
    "campfire count": "climate", "campfire temperature": "climate", "thermal.default_temp": "climate",
    "thermal.k_exchange / k_loss": "body temperature", "thermal.warming / cooling scale": "body temperature",
    "thermal.min/max_temperature, setpoint": "body temperature", "thermal.min_fire_separation": "climate",
    "thermal.bush_min_fire_distance": "climate", "random start body temp (B1)": "body temperature",
    "No cell settles the body at 0": None, "Agent can step onto a fire": None,
    "bush count": "layout", "hides_agent / blocks_animals": "layout",
    "use_homeostatic_reward": "reward", "drive": "reward", "temperature axis scale": "reward",
    "death_penalty": "reward", "agent.gamma": None, "return mode / entropy": None,
    "max_steps": "reward", "random_start_pos": "layout",
    "satiation observed": "interoception", "injury_observable": "interoception",
    "felt injury (alpha kernel, τ 3, length 12, buffer starts at 0)": "interoception",
    "contact pain": "sensing", "body_temp_observable": "interoception", "vision": "sensing", "smell": "sensing",
}
BOUNDARY = {"body.food_nutrition_gain": "food energy", "body.recovery_in_bush_multiplier": "injury"}
# plain-word examples printed under each group heading (labels, not values)
EXAMPLES = {
    "food energy": "hunger drain per step, overeating death",
    "injury": "healing only when resting, hits spread over time",
    "body temperature": "warming / cooling rates, death at {tlo:g} / {thi:+g}",
    "interoception": "what the agent feels of its own body",
    "reward": "drive reduction, death penalty, {steps}-step episode",
    "layout": "grid size, bushes, where things are placed",
    "food supply": "how many food items, regrowth delay",
    "danger": "hunters, ambushers, rocks",
    "climate": "cold of open ground, number of fires",
    "sensing": "smell range, blur and noise on sight and smell",
}

# ---- parse the inventory -------------------------------------------------------------------------
rows, sect = [], None
for line in open(C.INVENTORY):
    m = re.match(r"^## ([A-Z])\. ", line)
    if m:
        sect = m.group(1) if m.group(1) in "ABCDEFGH" else None
        continue
    if line.startswith("## "):
        sect = None
    if sect and line.startswith("| ") and not line.startswith("| Key"):
        key = line.split("|")[1].strip()
        rows.append((sect, key))
assert rows, "no inventory rows parsed"
unknown = [k for _, k in rows if k not in ROW_GROUP]
if unknown:
    raise SystemExit(f"inventory rows with no group assignment (inventory changed?): {unknown}")
count = {g: sum(1 for _, k in rows if ROW_GROUP[k] == g) for g in FIXED + CHANGES}
excluded = [k for _, k in rows if ROW_GROUP[k] is None]
for k in BOUNDARY:
    assert k in dict((kk, s) for s, kk in rows), f"boundary row {k} missing from inventory"

# ---- the configs: the body is identical in all eight worlds ---------------------------------------
P = C.load_params()
n_body = C.body_fields_identical(P)
for f in ("food_nutrition_gain", "recovery_in_bush_multiplier"):
    assert f in sum(C.BODY_FIELDS.values(), [])
R = P[C.REFERENCE]
EXAMPLES = {g: e.format(tlo=float(R.min_temperature), thi=float(R.max_temperature), steps=int(R.max_steps)).replace("-1", "\u22121") for g, e in EXAMPLES.items()}
gain = float(P[C.REFERENCE].food_nutrition_gain); bush = float(P[C.REFERENCE].recovery_in_bush_multiplier)

# ---- draw ----------------------------------------------------------------------------------------
fig = plt.figure(figsize=(9.6, 6.0))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 62.5); ax.axis("off")
cols = {"fixed": (2, 47), "changes": (53, 98)}
ax.text(24.5, 60.2, "fixed in every world — the body", ha="center", va="center", fontsize=13,
        weight="semibold", color=house.INK)
ax.text(75.5, 60.2, "changes between worlds — the outside", ha="center", va="center", fontsize=13,
        weight="semibold", color=house.INK)
top, h, gap = 56.5, 9.0, 1.3
for side, groups, fill, edge in (("fixed", FIXED, house.BG_SOFT, house.INK_2),
                                 ("changes", CHANGES, "white", house.RULE)):
    x0, x1 = cols[side]
    for i, g in enumerate(groups):
        y1 = top - i * (h + gap); y0 = y1 - h
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, h, boxstyle="round,pad=0,rounding_size=0.8",
                                    fc=fill, ec=edge, lw=1.1 if side == "fixed" else 1.0,
                                    ls="-" if side == "fixed" else (0, (4, 2))))
        ax.text(x0 + 1.6, y1 - 2.5, g, ha="left", va="center", fontsize=12, weight="semibold", color=house.INK)
        ax.text(x1 - 1.6, y1 - 2.5, f"{count[g]} settings", ha="right", va="center", fontsize=C.SMALLEST_PT,
                color=house.INK_2)
        ax.text(x0 + 1.6, y1 - 5.1, EXAMPLES[g], ha="left", va="center", fontsize=C.SMALLEST_PT, color=house.INK_2)
        if side == "fixed" and g in BOUNDARY.values():
            txt = (f"boundary item, kept fixed: food energy per bite = {gain:g}" if g == "food energy"
                   else f"boundary item, kept fixed: bush healing ×{bush:g}")
            ax.plot([x0 + 2.2], [y1 - 7.4], marker="D", ms=5.5, color=C.ACCENT, mec=C.ACCENT)
            ax.text(x0 + 3.6, y1 - 7.4, txt, ha="left", va="center", fontsize=C.SMALLEST_PT, color=C.ACCENT,
                    weight="semibold")
# arrow between the blocks: the body is the reference across the switches
ax.annotate("", xy=(52.4, 30), xytext=(47.6, 30),
            arrowprops=dict(arrowstyle="<->", color=house.INK_2, lw=1.2))
ax.text(50, 2.2, f"solid boxes: identical in all {len(C.CONCEPTS)} worlds (asserted on {n_body} body fields of the resolved configs)"
        "   ·   dashed boxes: set per world", ha="center", va="center", fontsize=C.SMALLEST_PT, color=house.INK_2)

C.record_kind("p1_body_vs_world", "design")
tot = len(rows)
data = [dict(what=f"inventory settings on the fixed side ({', '.join(FIXED)})", used=sum(count[g] for g in FIXED),
             total=tot, note="level-05 balance-settings inventory, sections A-H; one row per setting"),
        dict(what=f"inventory settings on the changing side ({', '.join(CHANGES)})",
             used=sum(count[g] for g in CHANGES), total=tot,
             note="the design may change any of these; which ones each world changes is Figure 2"),
        dict(what="inventory rows left out of both sides", used=len(excluded), total=tot,
             note="not environment settings: " + "; ".join(excluded)),
        dict(what="body fields compared across the 8 resolved world configs", used=n_body, total=n_body,
             note="load_env_config -> load_env_params (the trainer's path); every one identical in all 8 worlds, "
                  "including the two boundary items")]
C.record_samples("p1_body_vs_world", data)
print("  counts:", count, "excluded:", excluded)
# a diagram: the axes are only a coordinate system, and text sits at its edges by design
C.save(fig, "p1_body_vs_world", check_text=False)
