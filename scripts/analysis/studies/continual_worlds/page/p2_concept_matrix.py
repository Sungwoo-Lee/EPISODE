"""FIGURE p2 — The eight concept worlds side by side: what each one sets for every external factor.

Rows: the eight concepts. Columns: twelve external factors. Every cell's text is read from the world's
RESOLVED config, through the trainer's own loader (load_env_config -> load_env_params), never typed.
Cell shade = how much harder than Home that factor is in that world (greys; darker = harder; hatched =
easier than Home; white = as Home). Hardness per cell is the relative change of the range's midpoint
against Home's -- for counts of things (food, bushes, fires, hunters, ambushers, rocks) the midpoint
count PER GRID CELL, since the concept worlds scale counts with area -- signed by the factor's direction (e.g. fewer food items = harder, a larger grid =
harder), clipped to 1; a factor that is zero in Home (regrowth delay, noise) counts 1 when switched on.
It is an ordinal reading aid, not a measured difficulty.

Before drawing, the script asserts every body field (_common.BODY_FIELDS) is identical in all eight
worlds, and that every EnvParams field that differs between worlds is an EXTERNAL field.
"""
import dataclasses, sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
import _common as C

house = C.house; house.apply()
P = C.load_params()
n_body = C.body_fields_identical(P)

EXTERNAL_PREFIX = ("animal_", "obs_", "res_", "noise_", "type_", "thermal_default_temp", "height", "width",
                   "sensor_radius", "visual_blur", "perceptual_noise", "grid_location_type", "hunt_idx",
                   "wander_idx", "static_idx", "predator_indices", "neutral_indices", "num_entities",
                   "max_per_type", "has_", "thermal_bush_min_fire_distance", "obstacle_names", "num_types")
differ = sorted({f.name for f in dataclasses.fields(P[C.REFERENCE]) for c in C.CONCEPTS
                 if not C.same(getattr(P[c], f.name), getattr(P[C.REFERENCE], f.name))})
not_ext = [f for f in differ if not f.startswith(EXTERNAL_PREFIX)]
if not_ext:
    raise SystemExit(f"fields that differ between worlds but are not external: {not_ext}")


def rng(lo, hi):
    lo, hi = float(lo), float(hi)
    f = lambda v: f"{v:g}".replace("-", "−")
    return f(lo) if lo == hi else f"{f(lo)}–{f(hi)}"


def entry_range(p, kind, mask):
    """count range of the (single) entry whose slots match `mask`; (0, 0) if none."""
    eid = np.asarray(getattr(p, f"{kind}_entry_id"))[mask]
    if eid.size == 0:
        return (0, 0)
    e = set(eid.tolist()); assert len(e) == 1, (kind, e)
    e = e.pop()
    return int(np.asarray(getattr(p, f"{kind}_count_low"))[e]), int(np.asarray(getattr(p, f"{kind}_count_high"))[e])


def factors(p):
    rt = np.asarray(p.res_type); food = rt == 0; amb = rt == 1
    fire = np.asarray(p.obs_temp_ratio_high) > 0; bush = np.asarray(p.obs_hides_agent)
    rock = (np.asarray(p.obs_damage)[:, 1] > 0) & ~fire
    hunt = np.asarray(p.animal_classes_int) == 0
    out = {}
    cells = float(p.height) * float(p.width)            # counts are compared as per-cell densities
    out["grid"] = (f"{int(p.height)}×{int(p.width)}", float(p.height) * float(p.width), +1)
    out["smell range"] = (rng(p.sensor_radius, p.sensor_radius), float(p.sensor_radius), -1)
    f = entry_range(p, "res", food); out["food items"] = (rng(*f), np.mean(f) / cells, -1)
    d = np.unique(np.asarray(p.res_reg_delay)[food]); assert d.size == 1
    out["food regrowth"] = ("instant" if d[0] == 0 else f"{int(d[0])} steps", float(d[0]), +1)
    b = entry_range(p, "obs", bush); out["bushes"] = (rng(*b), np.mean(b) / cells, -1)
    fr = entry_range(p, "obs", fire)
    ratio = np.unique(np.asarray(p.obs_temp_ratio_high)[fire])
    out["fires"] = (rng(*fr) + ("" if ratio.size == 1 and ratio[0] == float(np.asarray(P[C.REFERENCE].obs_temp_ratio_high).max())
                                else f"\nratio {ratio.max():g}"), np.mean(fr) / cells, -1)
    t = (float(p.thermal_default_temp_low), float(p.thermal_default_temp_high))
    out["ambient temperature"] = (rng(*t).replace("\u2013", " to ") + "\n°C", np.mean(t), -1)
    h = entry_range(p, "animal", hunt)
    det = (np.asarray(p.animal_detect_low)[hunt], np.asarray(p.animal_detect_high)[hunt])
    out["hunting predators"] = (rng(*h) + (f"\nsee {rng(det[0].min(), det[1].max())} cells" if h[1] else ""),
                                np.mean(h) / cells, +1)
    if h[1]:
        mv = int(np.asarray(p.animal_move_int)[hunt].min())
        st = (np.asarray(p.animal_max_stamina_low)[hunt].min(), np.asarray(p.animal_max_stamina_high)[hunt].max())
        out["predator speed"] = (("every step" if mv == 1 else f"every {mv}rd step" if mv == 3 else f"every {mv}th step")
                                 + f"\nchase {rng(*st)}", 1.0 / mv * np.mean(st), +1)
    else:
        out["predator speed"] = ("—", None, +1)
    a = entry_range(p, "res", amb); out["ambushers"] = (rng(*a), np.mean(a) / cells, +1)
    r = entry_range(p, "obs", rock); out["rocks"] = (rng(*r), np.mean(r) / cells, +1)
    if bool(p.perceptual_noise_enabled):
        names = list(p.noise_modality_order); sig = np.asarray(p.noise_sigmas)
        word = {"olfaction": "smell", "visual": "sight"}
        names = [str(n).lower() for n in names]
        on = [f"{word.get(n, n)} σ{s:g}" for n, s in zip(names, sig) if s > 0]
        txt = "\n".join(on)
    else:
        txt = "off"
    blur = float(p.visual_blur_radial_scale)
    if blur != float(P[C.REFERENCE].visual_blur_radial_scale):
        txt += f"\nblur {blur / float(P[C.REFERENCE].visual_blur_radial_scale):g}×"
    score = (1.0 if bool(p.perceptual_noise_enabled) else 0.0) + (1.0 if blur != float(P[C.REFERENCE].visual_blur_radial_scale) else 0.0)
    out["sensing noise"] = (txt, score, +1)
    return out


F = {c: factors(P[c]) for c in C.CONCEPTS}
cols = list(F[C.REFERENCE])
ref = F[C.REFERENCE]


def hardness(c, k):
    v, r, sgn = F[c][k][1], ref[k][1], F[c][k][2]
    if v is None or r is None:                     # no hunting predator: easier than any
        return -1.0 if v is None and r is not None else 0.0
    if r == 0:
        return float(np.clip(sgn * (1.0 if v > 0 else 0.0), -1, 1))
    return float(np.clip(sgn * (v - r) / abs(r), -1, 1))


H = np.array([[hardness(c, k) for k in cols] for c in C.CONCEPTS])
HEAD = {"grid": "grid", "smell range": "smell\nrange", "food items": "food\nitems", "food regrowth": "food\nregrowth",
        "bushes": "bushes", "fires": "fires", "ambient temperature": "ambient\ntemp.", "hunting predators": "hunting\npredators",
        "predator speed": "predator\nspeed", "ambushers": "ambushers", "rocks": "rocks", "sensing noise": "sensing\nnoise"}
widths = {"predator speed": 1.45, "hunting predators": 1.4, "ambient temperature": 1.25, "sensing noise": 1.15,
          "grid": 0.85, "smell range": 0.8, "food items": 0.8, "fires": 0.85, "rocks": 0.8, "bushes": 0.8}
W = [widths.get(k, 1.0) for k in cols]
xs = np.concatenate([[0], np.cumsum(W)])
fig, ax = plt.subplots(figsize=(9.9, 6.6))
grey = lambda h: plt.cm.Greys(0.08 + 0.42 * h)      # never darker than mid grey: ink text stays legible
for i, c in enumerate(C.CONCEPTS):
    y = len(C.CONCEPTS) - 1 - i
    for j, k in enumerate(cols):
        h = H[i, j]
        fc = "white" if h <= 0 else grey(h)
        ax.add_patch(Rectangle((xs[j], y), W[j], 1, fc=fc, ec=house.RULE, lw=0.8,
                               hatch="////" if h < 0 else None))
        if h < 0:
            ax.add_patch(Rectangle((xs[j], y), W[j], 1, fc="none", ec=house.RULE, lw=0.8))
        t = F[c][k][0]
        ax.text(xs[j] + W[j] / 2, y + 0.5, t, ha="center", va="center", fontsize=C.SMALLEST_PT,
                color=house.INK, linespacing=1.1,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9) if h < 0 else None)
    if c == C.REFERENCE:
        ax.add_patch(Rectangle((0, y), xs[-1], 1, fc="none", ec=house.INK, lw=1.8))
ax.set_xlim(0, xs[-1]); ax.set_ylim(0, len(C.CONCEPTS))
ax.set_yticks(np.arange(len(C.CONCEPTS)) + 0.5)
ax.set_yticklabels(C.CONCEPTS[::-1], fontsize=11, color=house.INK)
ax.set_xticks((xs[:-1] + xs[1:]) / 2); ax.set_xticklabels([HEAD[k] for k in cols], fontsize=C.SMALLEST_PT, color=house.INK)
ax.xaxis.tick_top(); ax.tick_params(length=0); ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
h = [Patch(fc="white", ec=house.RULE, label="as Home"),
     Patch(fc="white", ec=house.RULE, hatch="////", label="easier than Home"),
     Patch(fc=grey(0.35), ec=house.RULE, label="harder than Home"),
     Patch(fc=grey(1.0), ec=house.RULE, label="much harder (darker = harder)"),
     Patch(fc="none", ec=house.INK, lw=1.8, label="Home: the reference row")]
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, fontsize=C.SMALLEST_PT, bbox_to_anchor=(0.5, 0.0))
assert_ticks = C.assert_ticks_dont_collide(ax, "x")

C.record_kind("p2_concept_matrix", "design")
rows = [dict(what="concept worlds read (resolved configs, trainer's loader)", used=len(C.CONCEPTS), total=len(C.CONCEPTS),
             note="configs/environment/experiment/continual_worlds; every cell's text is read from the loaded parameters"),
        dict(what="body fields asserted identical in all 8 worlds", used=n_body, total=n_body,
             note="food energy, injury, body temperature, interoception and reward fields; the script stops if any differs"),
        dict(what="parameter fields that differ between worlds", used=len(differ), total=len(dataclasses.fields(P[C.REFERENCE])),
             note="every one is an external field (layout, food, animals, obstacles, climate, sensing); asserted"),
        dict(what="cells harder than Home / easier / as Home", used=int((H > 0).sum()), total=H.size,
             note=f"{int((H < 0).sum())} easier and {int((H == 0).sum())} as Home; shade = relative change of the range midpoint (counts per grid cell), clipped")]
C.record_samples("p2_concept_matrix", rows)
for c in C.CONCEPTS:
    print(f"  {c:8s}", " | ".join(F[c][k][0].replace(chr(10), ' ') for k in cols))
C.save(fig, "p2_concept_matrix")
