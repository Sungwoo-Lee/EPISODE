#!/usr/bin/env python3
"""_fig.py - what every Basic Behaviour figure script shares: loading, data accounting, encoding.

Plan: docs/develop/active/behavior/BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), `_fig.py`.

  * `args()`             the common CLI: --population, --out-root, --fig-dir (all mandatory)
  * `load_outputs()`     the population's completed + swept cells: inventory, provenance, episodes
  * `record_samples()`   `<fig_dir>/<stem>.samples.json`: rows {what, used, total, note}, percentage
                         derived, used > total refused (same contract as ladder/_ladder.py)
  * `encode()`           world -> colour, agent -> marker shape, so all six figures read the same way

Figure scripts read caches only (never a parquet shard), call `house.apply()` first, set no style of
their own and save through `house.save(fig, <fig_dir>/<stem>)`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
A_DIR = os.path.join(ROOT, "scripts", "analysis")
for p in (os.path.join(A_DIR, "style"), os.path.join(A_DIR, "studies", "hypervigilance"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import house as H                                                       # noqa: E402

# Plain names for the worlds and agents this project has populations of; anything else is shown by
# its manifest name. These are display labels, not analysis inputs.
WORLD_LABEL = {"hv1ch": "single-channel smell", "hv1chm": "matched-strength smell",
               "hv2ch": "two-channel smell (control)", "a01": "a01 world"}
WORLD_ORDER = ["hv2ch", "hv1ch", "hv1chm"]
# thirst task (THIRST_TASK section 3): map size x smell reach (W = the whole map, 5 or 3 squares)
_REACH = {"W": "smell across the map", "5": "smell 5 squares", "3": "smell 3 squares"}
for _g in (10, 15, 20):
    for _s in ("W", "5", "3"):
        WORLD_LABEL[f"g{_g}s{_s}"] = f"{_g}×{_g} map, {_REACH[_s]}"
        WORLD_ORDER.append(f"g{_g}s{_s}")
AGENT_LABEL = {"t1none": "ordinary agent", "t16quad": "modulated agent", "unmodulated": "ordinary agent"}
AGENT_ORDER = ["t1none", "unmodulated", "t16quad"]
WORLD_SHORT = {"hv1ch": "single-channel", "hv1chm": "matched-strength", "hv2ch": "two-channel (control)",
               **{f"g{g}s{s}": f"{g}×{g}, smell {'map' if s == 'W' else s}" for g in (10, 15, 20)
                  for s in ("W", "5", "3")}}
AGENT_SHORT = {"t1none": "ordinary", "t16quad": "modulated", "unmodulated": "ordinary"}
MARKERS = ["o", "^", "s", "D", "v", "P"]
# Markers reserved for non-run glyphs, so no shape means two things on the page (register F11, third
# amendment): agents use MARKERS; a setting's mean +/- seed-to-seed SD is "_" with an error bar; a
# standardised contrast is a vertical bar "|".
MEAN_MARKER, CONTRAST_MARKER = "_", "|"

# Display names for behaviours: noun phrases, so they fit every sentence frame (register F59 amendment).
# "Bush dwell" is the project's term for time spent in a bush.
TARGET_NOUN = {"bush_dwell": "bush dwell", "eating": "eating", "near_rabbit": "time near a rabbit",
               "near_predator": "time near a predator", "warm_cell": "time on a warm square",
               "pond": "time on the pond (drinking)"}
TARGET_TITLE = {"bush_dwell": "Bush dwell (time in a bush)", "eating": "Eating",
                "near_rabbit": "Time near a rabbit (within 2 squares)",
                "near_predator": "Time near a predator (within 2 squares)",
                "warm_cell": "Time on a warm square", "pond": "Time on the pond (drinking)"}
TARGET_ORDER = ["bush_dwell", "eating", "near_rabbit", "near_predator", "warm_cell", "pond"]

# Every factor shown on a figure goes through this table: no code names on the page.
FACTOR_LABEL = {
    "start_injury": "injury at start", "start_nutrition": "nutrition at start",
    "start_satiation": "satiation at start", "n_predators": "number of predators",
    "n_rabbits": "number of rabbits", "n_campfire": "number of campfires", "n_rocks": "number of rocks",
    "n_bushes": "number of bushes", "n_food": "number of food items",
    "n_ambush_predators": "number of hidden ambush predators", "spawn_dist_to_bush": "start distance to nearest bush",
    "start_body_temp": "body temperature at start", "ambient_temp": "world baseline temperature",
    "pred_detection_range": "predator sight range", "pred_attack_delay": "predator attack delay",
    "pred_attack_range": "predator attack range", "pred_max_stamina": "predator stamina",
    "pred_smell_predatorness": "predator's smell (how predator-like)",
    "spawn_dist_to_predator": "start distance to the predator", "pred_olf_intensity": "predator's odour strength",
    "rab_smell_predatorness": "rabbit's smell (how predator-like)", "rab_olf_intensity": "rabbit's odour strength",
    "frac_time_injured": "share of time injured", "frac_time_inj_severe": "share of time badly injured (50+)",
    "mean_injury": "average injury", "peak_injury": "highest injury", "frac_time_low_nutrition":
    "share of time with nutrition under 50", "mean_nutrition": "average nutrition",
    "total_damage_taken": "total damage taken", "eat_rate": "share of steps eating",
    "rest_rate": "share of steps resting", "episode_length": "episode length",
    "frac_time_predator_near": "share of time a predator is near",
    "frac_time_rabbit_near": "share of time only a rabbit is near",
    "mean_body_temp": "average body temperature", "frac_time_warm_cell": "share of time on a warm square",
    "detect_keenest": "sight range of the keener predator", "detect_least_keen": "sight range of the less keen predator",
    "detect_spread": "difference between the two sight ranges",
    "start_hydration": "hydration at start", "spawn_dist_to_pond": "start distance to the pond",
    "mean_hydration": "average hydration", "frac_time_on_pond": "share of time on the pond"}
QUANTITY_LABEL = {"level": "behaviour level", "start_injury": "injury-at-start slope",
                  "start_nutrition": "nutrition-at-start slope", "smell": "rabbit-smell slope",
                  "smell_x_injury": "rabbit smell × injury at start"}


def flabel(name: str) -> str:
    if name not in FACTOR_LABEL:
        raise SystemExit(f"no display name for factor {name!r}: add it to _fig.FACTOR_LABEL")
    return FACTOR_LABEL[name]
TERM_NAMES = {1: "reached the step limit", 2: "starved", 3: "over-ate",
              4: "injury reached maximum", 5: "body temperature out of range"}
# the two water death causes (core.py codes 6 and 7), shown only for populations with water
TERM_NAMES_WATER = {**TERM_NAMES, 6: "died of thirst", 7: "over-drank"}


def has_water(cells) -> bool:
    """True when any swept cell's world has water (its inventory carries a "water" block)."""
    return any("water" in c["inv"] for c in cells)


def term_names(cells) -> dict:
    return TERM_NAMES_WATER if has_water(cells) else TERM_NAMES


def args(extra=None, argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--fig-dir", required=True, help="the page's figure folder")
    for a, kw in (extra or []):
        ap.add_argument(a, **kw)
    return ap.parse_args(argv)


def wlabel(w):
    return WORLD_LABEL.get(w, w)


def alabel(a):
    return AGENT_LABEL.get(a, a)


def ordered(values, order):
    vs = sorted(set(values))
    return [v for v in order if v in vs] + [v for v in vs if v not in order]


FACTORIAL_RE = re.compile(r"^g(?P<size>\d+)s(?P<reach>[W\d]+)$")
REACH_SHADE = {"W": 0.0, "5": 0.33, "3": 0.55}     # mix toward the page ground: whole map, 5, 3 squares
REACH_NAME = {"W": "smell across the map", "5": "smell reach 5 squares", "3": "smell reach 3 squares"}


def factorial(worlds) -> bool:
    """A map-size x smell-reach world design (the thirst task) with more worlds than palette hues.
    Only such populations get the two-part encoding; every other population is drawn as before."""
    return len(worlds) > len(H.SERIES) and all(FACTORIAL_RE.match(w) for w in worlds)


def _mix(hex_colour, t):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    pr, pg, pb = (int(H.PAPER[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(x + (p - x) * t) for x, p in ((r, pr), (g, pg), (b, pb)))


def encode(cells):
    """{world: colour}, {agent: marker} - fixed for a population, shared by every figure.
    A factorial map-size x smell-reach design: hue = map size, shade = smell reach. Any other design
    with more worlds than hues is refused (colours would repeat)."""
    worlds = ordered([c["world"] for c in cells], WORLD_ORDER)
    agents = ordered([c["agent"] for c in cells], AGENT_ORDER)
    if factorial(worlds):
        sizes = sorted({int(FACTORIAL_RE.match(w)["size"]) for w in worlds})
        if len(sizes) > len(H.SERIES):
            raise SystemExit(f"{len(sizes)} map sizes but {len(H.SERIES)} palette hues")
        col = {w: _mix(H.SERIES[sizes.index(int(FACTORIAL_RE.match(w)["size"]))],
                       REACH_SHADE[FACTORIAL_RE.match(w)["reach"]]) for w in worlds}
    else:
        if len(worlds) > len(H.SERIES):
            raise SystemExit(f"{len(worlds)} worlds but {len(H.SERIES)} palette hues: colours would repeat")
        col = {w: H.SERIES[i % len(H.SERIES)] for i, w in enumerate(worlds)}
    mk = {a: MARKERS[i % len(MARKERS)] for i, a in enumerate(agents)}
    return worlds, agents, col, mk


def legend_ncol(D: dict) -> int:
    """Columns of the shared legend: one row of every entry, as before; four for a factorial design."""
    return 4 if factorial(D["worlds"]) else len(D["worlds"]) + len(D["agents"])


def load_outputs(population: str, out_root: str, need_episodes: bool = False) -> dict:
    """Completed cells of the manifest, with what the sweep wrote for each. Unswept cells are listed
    separately (shown as missing, never silently dropped)."""
    import readings as RD
    M = json.load(open(population))
    pop = RD.load_population(population)
    cells, unswept = [], []
    for c in pop["cells"]:
        d = os.path.join(out_root, c["label"])
        if not os.path.exists(os.path.join(d, "inventory.json")):
            unswept.append(c)
            continue
        e = dict(c)
        e["dir"] = d
        e["inv"] = json.load(open(os.path.join(d, "inventory.json")))
        e["prov"] = json.load(open(os.path.join(d, "_provenance.json")))
        if need_episodes:
            e["ep"] = np.load(os.path.join(d, "episodes.npz"))
        cells.append(e)
    worlds, agents, col, mk = encode(cells)
    key = lambda c: (worlds.index(c["world"]), agents.index(c["agent"]), c["seed"])
    cells.sort(key=key)
    return {"population": M["population"], "cells": cells, "unswept": unswept,
            "not_completed": [c for c in M["cells"] if c["status"] != "completed"],
            "worlds": worlds, "agents": agents, "colour": col, "marker": mk}


def record_samples(fig_dir: str, stem: str, rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        used, total = int(r["used"]), int(r["total"])
        if used > total:
            raise SystemExit(f"{stem}: {r['what']!r} claims {used:,} of {total:,}")
        out.append({"what": r["what"], "used": used, "total": total,
                    "pct": (100.0 * used / total) if total else 0.0, "note": r.get("note", "")})
    os.makedirs(fig_dir, exist_ok=True)
    json.dump(out, open(os.path.join(fig_dir, f"{stem}.samples.json"), "w"), indent=1)
    print(f"data behind {stem}:")
    for r in out:
        print(f"  {r['what'][:60]:60}{r['used']:>12,} of {r['total']:>12,} ({r['pct']:5.1f}%)"
              + (f"  {r['note']}" if r["note"] else ""))
    return out


def run_label(c) -> str:
    return f"{wlabel(c['world'])}, {alabel(c['agent'])}, seed {c['seed']}"


def run_short(c) -> str:
    return f"{WORLD_SHORT.get(c['world'], c['world'])} · {AGENT_SHORT.get(c['agent'], c['agent'])} · seed {c['seed']}"


def group_positions(D: dict, gap: float = 0.6, width: float = 0.5):
    """x position of each run: one group per world x agent cell, seeds jittered inside the group.
    Factorial design: one tick per map size (colour and marker identify the run inside it)."""
    if factorial(D["worlds"]):
        pos, ticks, labels, x = {}, [], [], 0.0
        sizes = sorted({int(FACTORIAL_RE.match(w)["size"]) for w in D["worlds"]})
        for s in sizes:
            start = x
            for w in [w for w in D["worlds"] if int(FACTORIAL_RE.match(w)["size"]) == s]:
                for a in D["agents"]:
                    grp = [c for c in D["cells"] if c["world"] == w and c["agent"] == a]
                    for c in grp:
                        pos[c["label"]] = x
                    if grp:
                        x += 0.32
            ticks.append((start + x - 0.32) / 2)
            labels.append(f"{s}×{s}")
            x += 0.9
        return pos, ticks, labels
    pos, ticks, labels, x = {}, [], [], 0.0
    for w in D["worlds"]:
        for a in D["agents"]:
            grp = [c for c in D["cells"] if c["world"] == w and c["agent"] == a]
            if not grp:
                continue
            offs = np.linspace(-width / 2, width / 2, len(grp)) if len(grp) > 1 else [0.0]
            for c, o in zip(grp, offs):
                pos[c["label"]] = x + o
            ticks.append(x)
            labels.append(f"{WORLD_SHORT.get(w, w)}, {AGENT_SHORT.get(a, a)}")
            x += 1 + gap
    return pos, ticks, labels


def legend_handles(D: dict, extra=()):
    from matplotlib.lines import Line2D
    if factorial(D["worlds"]):
        sizes = sorted({int(FACTORIAL_RE.match(w)["size"]) for w in D["worlds"]})
        hs = [Line2D([], [], ls="", marker="s", ms=9, color=H.SERIES[i], label=f"{s}×{s} map")
              for i, s in enumerate(sizes)]
        reaches = [r for r in REACH_SHADE if any(FACTORIAL_RE.match(w)["reach"] == r for w in D["worlds"])]
        hs += [Line2D([], [], ls="", marker="s", ms=9, color=_mix(H.INK_2, REACH_SHADE[r]),
                      label=f"shade: {REACH_NAME[r]}") for r in reaches]
        hs += [Line2D([], [], ls="", marker=D["marker"][a], ms=8, color=H.INK_2, label=alabel(a))
               for a in D["agents"]]
        for marker, label in extra:
            hs.append(Line2D([], [], ls="", marker=marker, ms=11, mew=2.2, color=H.INK, label=label))
        ncol = legend_ncol(D)
        if len(hs) == 2 * ncol and len(sizes) == len(reaches) == ncol - 1:
            # matplotlib fills legend columns first: interleave so row 1 = map sizes + first agent,
            # row 2 = smell-reach shades + second agent (the three hues stay together)
            row1 = hs[:len(sizes)] + [hs[2 * len(sizes)]]
            row2 = hs[len(sizes):2 * len(sizes)] + [hs[2 * len(sizes) + 1]]
            hs = [h for pair in zip(row1, row2) for h in pair]
        return hs
    hs = [Line2D([], [], ls="", marker="o", ms=8, color=D["colour"][w], label=wlabel(w))
          for w in D["worlds"]]
    hs += [Line2D([], [], ls="", marker=D["marker"][a], ms=8, color=H.INK_2, label=alabel(a))
           for a in D["agents"]]
    for marker, label in extra:
        hs.append(Line2D([], [], ls="", marker=marker, ms=11, mew=2.2, color=H.INK, label=label))
    return hs


def save(fig, fig_dir: str, stem: str):
    return H.save(fig, os.path.join(fig_dir, stem))
