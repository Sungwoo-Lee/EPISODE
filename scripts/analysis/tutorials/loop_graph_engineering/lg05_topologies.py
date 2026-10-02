#!/usr/bin/env python3
"""FIGURE 5 - five common shapes for wiring agents together.

QUESTION IT ANSWERS. What choices does "designing the graph" actually involve? The simplest one is
the shape. Feng et al. (2026, arXiv:2608.21156) discuss chains, hub-and-spoke coordinators,
hierarchical trees, fully connected groups and dataflow DAGs (directed acyclic graphs, as in
LLMCompiler); the figure draws one small example of each.

WHAT IS IN IT. Five panels. Each dot is one agent (blue); an arrow means "hands work to"; the mesh
uses plain lines because every agent talks to every other in both directions.

HOW IT IS COMPUTED. Nothing is computed. Node positions are placed on simple geometric layouts
(a row, a circle, levels of a tree, a pentagon) on a 10.5 x 3.3 inch canvas.
"""
import math

from matplotlib.patches import Circle

import _diagram as D
import house

R = 0.12            # node radius, inches
SHRINK = 9.5        # points: an arrow stops just outside a node's rim (0.12 in = 8.6 pt)


def nodes(ax, pts):
    fc, ec = D.ROLE["agent"]
    for x, y in pts:
        ax.add_patch(Circle((x, y), R, fc=fc, ec=ec, lw=1.4, zorder=3))


def edges(ax, pts, pairs, directed=True):
    for a, b in pairs:
        if directed:
            D.arrow(ax, pts[a], pts[b], shrink=SHRINK, lw=1.2)
        else:
            D.line(ax, pts[a], pts[b], house.INK_2, lw=1.0)


def ring(cx, cy, r, n, start=90):
    return [(cx + r * math.cos(math.radians(start + 360 * k / n)),
             cy + r * math.sin(math.radians(start + 360 * k / n))) for k in range(n)]


def main():
    fig, ax = D.canvas(10.5, 3.3)
    cxs = [1.05, 3.15, 5.25, 7.35, 9.45]
    y = 2.2
    names = [("Chain", "one after another,\nlike a pipeline"),
             ("Star", "one hub hands out\nevery task"),
             ("Tree", "hubs of hubs:\nsplit, then split again"),
             ("Mesh", "all talk to all,\nas in a debate"),
             ("DAG", "parallel where tasks\nare independent")]

    c = cxs[0]
    pts = [(c - 0.75, y), (c - 0.25, y), (c + 0.25, y), (c + 0.75, y)]
    edges(ax, pts, [(0, 1), (1, 2), (2, 3)]); nodes(ax, pts)

    c = cxs[1]
    pts = [(c, y)] + ring(c, y, 0.62, 5)
    edges(ax, pts, [(0, k) for k in range(1, 6)]); nodes(ax, pts)

    c = cxs[2]
    pts = [(c, 2.85), (c - 0.5, 2.2), (c + 0.5, 2.2),
           (c - 0.75, 1.55), (c - 0.25, 1.55), (c + 0.25, 1.55), (c + 0.75, 1.55)]
    edges(ax, pts, [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]); nodes(ax, pts)

    c = cxs[3]
    pts = ring(c, y, 0.62, 5)
    edges(ax, pts, [(a, b) for a in range(5) for b in range(a + 1, 5)], directed=False); nodes(ax, pts)

    c = cxs[4]
    pts = [(c - 0.8, y), (c - 0.25, 2.7), (c - 0.25, 1.7), (c + 0.3, y), (c + 0.85, y)]
    edges(ax, pts, [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]); nodes(ax, pts)

    for cx, (t, s) in zip(cxs, names):
        D.label(ax, cx, 1.05, t, colour=house.INK, size=house.FS_BODY, weight="semibold")
        D.label(ax, cx, 0.55, s)
    for x in [2.1, 4.2, 6.3, 8.4]:
        D.line(ax, (x, 0.3), (x, 3.1), house.TICK_LINE)

    D.save(fig, "lg05_topologies",
           "Conceptual diagram, not a measurement: 5 of 5 topologies drawn (100%), as invented "
           "examples of 4, 6, 7, 5 and 5 agents. No run, episode or seed is summarised.")


if __name__ == "__main__":
    main()
