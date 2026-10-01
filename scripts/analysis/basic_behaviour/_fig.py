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
AGENT_LABEL = {"t1none": "ordinary agent", "t16quad": "modulated agent", "unmodulated": "ordinary agent"}
AGENT_ORDER = ["t1none", "unmodulated", "t16quad"]
WORLD_SHORT = {"hv1ch": "single-ch.", "hv1chm": "matched", "hv2ch": "two-ch. (control)"}
AGENT_SHORT = {"t1none": "ordinary", "t16quad": "modulated", "unmodulated": "ordinary"}
MARKERS = ["o", "^", "s", "D", "v", "P"]
TERM_NAMES = {1: "reached the step limit", 2: "starved", 3: "over-ate",
              4: "injury reached maximum", 5: "body temperature out of range"}


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


def encode(cells):
    """{world: colour}, {agent: marker} - fixed for a population, shared by every figure."""
    worlds = ordered([c["world"] for c in cells], WORLD_ORDER)
    agents = ordered([c["agent"] for c in cells], AGENT_ORDER)
    col = {w: H.SERIES[i % len(H.SERIES)] for i, w in enumerate(worlds)}
    mk = {a: MARKERS[i % len(MARKERS)] for i, a in enumerate(agents)}
    return worlds, agents, col, mk


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


def group_positions(D: dict, gap: float = 0.6, width: float = 0.5):
    """x position of each run: one group per world x agent cell, seeds jittered inside the group."""
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


def legend_handles(D: dict):
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], ls="", marker="o", ms=8, color=D["colour"][w], label=wlabel(w))
          for w in D["worlds"]]
    hs += [Line2D([], [], ls="", marker=D["marker"][a], ms=8, color=H.INK_2, label=alabel(a))
           for a in D["agents"]]
    return hs


def save(fig, fig_dir: str, stem: str):
    return H.save(fig, os.path.join(fig_dir, stem))
