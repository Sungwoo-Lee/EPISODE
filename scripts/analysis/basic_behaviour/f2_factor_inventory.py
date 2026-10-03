#!/usr/bin/env python3
"""f2_factor_inventory.py - Figure 2: which randomised features of the world each run's analysis
uses, which it drops and why, and which it cannot handle.

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), Figure scripts, F2. Reads inventory.json and
<cell>/<target>/prefit.json (written by fit.py); seconds.

Rows: factors in the registry's order, then any unhandled config marker. Columns: runs. Each cell is
a status word: used / identical to another (dup) / constant / too few episodes (few) / is the outcome
/ univariate only / not in this world (n/a) / unhandled.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

STEM = "f2_factor_inventory"
CODES = ["used", "univariate only", "dup", "constant", "few", "outcome", "n/a", "unhandled"]
SHORT = {"univariate only": "uni", "dup": "dup", "constant": "con", "few": "few", "outcome": "out",
         "unhandled": "unh"}                     # written in the cell; the legend gives the full word


def code_of(reason: str) -> str:
    if reason.startswith("identical to"):
        return "dup"
    if reason.startswith("constant"):
        return "constant"
    if reason.startswith("defined on"):
        return "few"
    if "outcome" in reason:
        return "outcome"
    return "excluded"


def short_run(c):
    return FG.run_short(c)


def main(argv=None):
    a = FG.args([("--target", dict(required=True, choices=sorted(REG.TARGETS)))], argv)
    H = FG.H
    H.apply()
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    D = FG.load_outputs(a.population, a.out_root)
    cells = [c for c in D["cells"] if (c["inv"]["targets"].get(a.target) or {}).get("available")]
    water = FG.has_water(cells)     # world features + pond corners: an HTML table on the page (build_page)
    names, kinds = [], {}
    for c in cells:
        for f in c["inv"]["factors"]:
            if f["name"] not in names:
                names.append(f["name"])
                kinds[f["name"]] = f["block"]
    unh = []
    for c in cells:
        for u in c["inv"]["unhandled"]:
            if u["path"] not in unh:
                unh.append(u["path"])
    rowsn = names + [f"unhandled: {p}" for p in unh]
    M = np.full((len(rowsn), len(cells)), CODES.index("n/a"))
    rows, table = [], {}
    for j, c in enumerate(cells):
        pj = os.path.join(c["dir"], a.target, "prefit.json")
        if not os.path.exists(pj):
            raise SystemExit(f"{c['label']}: no {a.target}/prefit.json -- run fit.py first")
        pf = json.load(open(pj))
        exc = {e["name"]: e["reason"] for e in pf["excluded"]}
        dem = {e["name"]: e["reason"] for e in pf["demoted"]}
        mine = {f["name"] for f in c["inv"]["factors"]}
        for i, n in enumerate(names):
            if n not in mine:
                continue
            code = code_of(exc[n]) if n in exc else ("univariate only" if n in dem else "used")
            M[i, j] = CODES.index(code) if code in CODES else CODES.index("dup")
            if n in exc or n in dem:
                table.setdefault(n, []).append(f"{short_run(c)}: {exc.get(n) or dem.get(n)}")
        for k, p in enumerate(unh):
            if any(u["path"] == p for u in c["inv"]["unhandled"]):
                M[len(names) + k, j] = CODES.index("unhandled")
        rows.append({"what": f"factors used, {FG.run_label(c)}", "used": len(mine) - len(exc),
                     "total": len(mine), "note": (f"{len(exc)} excluded before fitting" if exc else
                                                  "none excluded")})
    for c in D["cells"]:
        if c not in cells:
            rows.append({"what": f"{FG.run_label(c)}", "used": 0, "total": 0,
                         "note": f"{FG.TARGET_NOUN[a.target]} not available in this run"})
    # used / uni / dup / con / few / out / n-a / unh: distinct neutral steps plus one warm tint for
    # "unhandled"; no series hue, since colour means smell world elsewhere on the page
    shades = [H.INK_2, "#9aa0a8", "#c3c7cc", "#dfe1e3", "#e9e3d3", "#d8cfe0", H.PAPER, "#efc9b8"]
    if water:                       # populations with water: distinct steps, "used" clearly the darkest
        shades = ["#2f3640", "#7d8590", "#b4bac2", "#e3e6ea", "#e9e3d3", "#d8cfe0", H.PAPER, "#efc9b8"]
    cmap = ListedColormap(shades)
    h = 0.3 * len(rowsn) + 5.6
    fig, ax = plt.subplots(figsize=(12.0, h))
    ax.imshow(M, cmap=cmap, vmin=-0.5, vmax=len(CODES) - 0.5, aspect="auto", interpolation="nearest")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            code = CODES[M[i, j]]
            if code in ("used", "n/a"):
                continue
            ax.text(j, i, SHORT.get(code, code), ha="center", va="center", fontsize=H.FS_LABEL,
                    color=H.PAPER if code == "univariate only" else H.INK)
    ax.set_yticks(range(len(rowsn)))
    ylab = [(FG.flabel(n) + ("  (during episode)" if kinds.get(n) == "consequence" else ""))
            if not n.startswith("unhandled: ") else "randomised, unmeasured: " + n[11:] for n in rowsn]
    ax.set_yticklabels(ylab, fontsize=H.FS_LABEL)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([short_run(c) for c in cells], rotation=90, fontsize=H.FS_LABEL)
    ax.xaxis.tick_top()
    ax.grid(False)
    if water:                       # white cell borders so neighbouring cells read as separate
        ax.set_xticks(np.arange(-0.5, M.shape[1]), minor=True)
        ax.set_yticks(np.arange(-0.5, M.shape[0]), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.6)
        ax.tick_params(which="minor", length=0)
    ax.set_xlabel("run: smell world · agent type · training seed")
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("feature of the episode")
    from matplotlib.patches import Patch
    full = {"used": "used", "univariate only": "uni = single-factor fits only",
            "dup": "dup = identical to an earlier factor", "constant": "con = constant in this run",
            "few": "few = under 1,000 episodes", "outcome": "out = part of the outcome",
            "n/a": "not in this world", "unhandled": "unh = randomised, no measurement"}
    hs = [Patch(facecolor=shades[CODES.index(k)], edgecolor=H.INK_2, linewidth=0.8, label=full[k]) for k in full]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    FG.record_samples(a.fig_dir, f"{STEM}__{a.target}", rows)
    FG.save(fig, a.fig_dir, f"{STEM}__{a.target}")


if __name__ == "__main__":
    main()
