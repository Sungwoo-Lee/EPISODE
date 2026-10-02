"""FIGURE p3 — One example start of an episode in each of the eight concept worlds, drawn as a map.

Each map is ONE real environment reset (core.jax_reset on the world's resolved parameters, loaded by
the trainer's own loader), at a fixed key (SEED below), the same key for every world. Drawn: food,
bushes, fires with the ground-temperature field as a grey background (warmer = darker), rocks, hunting
predators, ambushers (drawn, but marked hidden: the agent cannot see them), and the agent's start.
Rabbits (harmless) are not drawn. Every panel uses the SAME cell size, so a 20 x 20 world is drawn
twice as wide as a 10 x 10 one. Because the key is shared, the five 15 x 15 worlds draw their
positions from the same random stream: where their counts agree the objects sit on the same cells, so
the maps differ where the configs differ. One reset shows one draw of the counts; the ranges are in Figure 2.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
import _common as C

house = C.house; house.apply()
SEED = 7
P = C.load_params()
C.body_fields_identical(P)
import jax
from src.environment import core


def reset(p):
    s = jax.jit(core.jax_reset)(p, jax.random.PRNGKey(SEED))
    g = lambda k: np.asarray(getattr(s, k))
    rt = np.asarray(p.res_type); fire = np.asarray(p.obs_temp_ratio_high) > 0
    bush = np.asarray(p.obs_hides_agent); rock = (np.asarray(p.obs_damage)[:, 1] > 0) & ~fire
    hunt = np.asarray(p.animal_classes_int) == 0
    rp, ra, op, oa, ap, aa = g("res_pos"), g("res_active"), g("obs_pos"), g("obs_active"), g("animal_pos"), g("animal_active")
    return dict(agent=g("agent_pos").reshape(-1, 2)[:1], food=rp[ra & (rt == 0)], ambusher=rp[ra & (rt == 1)],
                fire=op[oa & fire], bush=op[oa & bush], rock=op[oa & rock], hunter=ap[aa & hunt],
                field=g("thermal_field"), G=(int(p.height), int(p.width)),
                ambient=(float(p.thermal_default_temp_low) + float(p.thermal_default_temp_high)) / 2)


R = {c: reset(P[c]) for c in C.CONCEPTS}
Gmax = max(r["G"][1] for r in R.values())
Hmax = max(r["G"][0] for r in R.values())
MARK = {"food": dict(marker="o", ms=5.2, mfc=house.INK, mec=house.INK, label="food"),
        "fire": dict(marker="*", ms=9.5, mfc=house.INK, mec=house.INK, label="fire"),
        "rock": dict(marker="D", ms=4.2, mfc=house.INK_2, mec=house.INK_2, label="rock (hurts)"),
        "hunter": dict(marker="^", ms=7.0, mfc=house.INK, mec="white", label="hunting predator"),
        "ambusher": dict(marker="x", ms=5.0, mfc="none", mec=house.INK_2, mew=1.3, label="ambusher (hidden from the agent)"),
        "agent": dict(marker="o", ms=8.5, mfc="white", mec=house.INK, mew=2.0, label="agent start")}

# layout: 4 panels per row, each slot sized for the largest grid; every panel has the same cell size
FW, ncol = 9.8, 4
slot_w = FW / ncol; cell = (slot_w - 0.25) / Gmax
nrow = int(np.ceil(len(C.CONCEPTS) / ncol))
row_h = [max(R[c]["G"][0] for c in C.CONCEPTS[r * ncol:(r + 1) * ncol]) * cell + 0.45 for r in range(nrow)]
FH = sum(row_h) + 0.62
fig = plt.figure(figsize=(FW, FH))
TMAX = 10.0      # the grey background saturates at this ground temperature (degrees C)
for i, c in enumerate(C.CONCEPTS):
    r = R[c]; H, W = r["G"]
    col, row = i % ncol, i // ncol
    x0 = col * slot_w + 0.12; ytop = FH - sum(row_h[:row]) - 0.38
    ax = fig.add_axes([x0 / FW, (ytop - H * cell) / FH, W * cell / FW, H * cell / FH])
    f = np.clip((r["field"] - r["ambient"]) / (TMAX - r["ambient"]), 0, 1)
    ax.imshow(f, cmap="Greys", vmin=0, vmax=2.2, origin="upper", extent=(-0.5, W - 0.5, H - 0.5, -0.5),
              interpolation="nearest")
    for (y, x) in r["bush"]:
        ax.add_patch(Rectangle((x - 0.42, y - 0.42), 0.84, 0.84, fc="white", ec=house.INK_2, lw=0.9, hatch="....", zorder=2))
    for k in ("rock", "food", "ambusher", "fire", "hunter", "agent"):
        pts = r[k]
        if len(pts):
            st = {kk: v for kk, v in MARK[k].items() if kk != "label"}
            ax.plot(pts[:, 1], pts[:, 0], ls="none", zorder=3, **st)
    ax.set_xlim(-0.5, W - 0.5); ax.set_ylim(H - 0.5, -0.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(house.INK_2); s.set_linewidth(0.8)
    fig.text(x0 / FW, (ytop + 0.07) / FH, f"{c}  ·  {H} × {W}", ha="left", va="bottom", fontsize=11,
             weight="semibold", color=house.INK)
handles = [Patch(fc="white", ec=house.INK_2, hatch="....", label="bush (cover)")] + \
          [Line2D([], [], ls="none", **MARK[k]) for k in ("food", "fire", "rock", "hunter", "ambusher", "agent")] + \
          [Patch(fc=plt.cm.Greys(0.35), ec="none", label=f"warm ground (grey saturates at {TMAX:g} °C)")]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=C.SMALLEST_PT,
           bbox_to_anchor=(0.5, 0.0))

C.record_kind("p3_concept_layouts", "design")
tot = {k: sum(len(r[k]) for r in R.values()) for k in ("food", "bush", "fire", "rock", "hunter", "ambusher")}
rows = [dict(what="environment resets drawn (one per concept world)", used=len(C.CONCEPTS), total=len(C.CONCEPTS),
             note=f"core.jax_reset with PRNG key {SEED}, the same key in every world; one draw of each world's counts"),
        dict(what="grid cells drawn across the 8 maps", used=int(sum(r['G'][0] * r['G'][1] for r in R.values())),
             total=int(sum(r['G'][0] * r['G'][1] for r in R.values())), note="every cell of every map"),
        dict(what="objects placed on these resets", used=int(sum(tot.values())), total=int(sum(tot.values())),
             note=", ".join(f"{v} {k}" for k, v in tot.items()) + "; rabbits (harmless) are placed but not drawn")]
C.record_samples("p3_concept_layouts", rows)
for c, r in R.items():
    print(f"  {c:8s} G={r['G']} " + " ".join(f"{k}={len(r[k])}" for k in ("food", "bush", "fire", "rock", "hunter", "ambusher")))
# the maps are image panels with titles set above them in figure coordinates, on purpose
C.save(fig, "p3_concept_layouts", check_text=False)
